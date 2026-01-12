"""
Live Trading Module for Binance Testnet
Handles real trading operations using paper money on Binance Testnet Vision
"""
import os
import time
import threading
from datetime import datetime, timedelta
from typing import Optional, Dict, List
from binance.client import Client
from binance.enums import *
import pandas as pd
import numpy as np
import yfinance as yf
from hmmlearn.hmm import GaussianHMM
from dotenv import load_dotenv
from sqlmodel import Session, select
from database import engine
from models import Trade, TradingSession

load_dotenv()

# Binance Testnet Configuration
TESTNET_API_KEY = os.getenv("BINANCE_API_KEY", "")
TESTNET_API_SECRET = os.getenv("BINANCE_SECRET_KEY", "")

# Storage for active trading sessions (in-memory for real-time tracking)
active_sessions: Dict[str, "BaseTradingSessionRunner"] = {}

# Portfolio cache to prevent API rate limits
_portfolio_cache = {'data': None, 'timestamp': None}
_CACHE_DURATION = 30  # seconds


def get_testnet_client():
    """Create Binance testnet client with timestamp sync"""
    try:
        # Create client without timestamp initially to sync time
        client = Client(TESTNET_API_KEY, TESTNET_API_SECRET, testnet=True)
        
        # Sync time with Binance server to avoid timestamp issues
        try:
            server_time = client.get_server_time()
            time_offset = server_time['serverTime'] - int(time.time() * 1000)
            # Adjust for any offset (subtract 1 second for safety)
            client.timestamp_offset = time_offset - 1000
        except Exception as e:
            print(f"[Warning] Could not sync time with Binance: {e}")
            # Set a small negative offset as fallback
            client.timestamp_offset = -1000
        
        return client
    except Exception as e:
        print(f"[Error] Failed to create Binance client: {e}")
        # Return basic client as fallback
        client = Client(TESTNET_API_KEY, TESTNET_API_SECRET, testnet=True)
        client.timestamp_offset = -1000
        return client


def get_account_balance():
    """Get current testnet account balance"""
    try:
        client = get_testnet_client()
        account = client.get_account()
        balances = []
        for balance in account['balances']:
            free = float(balance['free'])
            locked = float(balance['locked'])
            if free > 0 or locked > 0:
                balances.append({
                    'asset': balance['asset'],
                    'free': free,
                    'locked': locked,
                    'total': free + locked
                })
        return balances
    except Exception as e:
        return {"error": str(e)}


def get_portfolio_value():
    """Get total portfolio value in USDT (with caching and SAFE batch price fetch)"""
    global _portfolio_cache
    
    # Check cache first
    if _portfolio_cache['data'] is not None and _portfolio_cache['timestamp'] is not None:
        elapsed = (datetime.now() - _portfolio_cache['timestamp']).total_seconds()
        if elapsed < _CACHE_DURATION:
            return _portfolio_cache['data']
    
    try:
        client = get_testnet_client()
        account = client.get_account()
        
        # Assets that are stablecoins or don't have USDT pairs on testnet
        skip_assets = {'USDT', 'BUSD', 'USDC', 'DAI', 'TUSD', 'PAX', 'TRY', 'ZAR', 'UAH', 'BRL', 'EUR', 'GBP', 'AUD', 'NGN', 'RUB', 'UAH', 'BIDR', 'IDRT', 'VAI'}
        
        # First pass: identify symbols to fetch (ONLY what user actually holds)
        symbols_to_fetch = []
        for balance in account['balances']:
            free = float(balance.get('free', 0))
            locked = float(balance.get('locked', 0))
            total = free + locked
            if total > 0.001:
                asset = balance.get('asset', 'UNKNOWN')
                if asset not in skip_assets and asset != 'USDT':
                    symbols_to_fetch.append(f"{asset}USDT")
        
        # Batch fetch ONLY needed prices (API weight: 2 per symbol - very safe!)
        price_map = {}
        for symbol in symbols_to_fetch:
            try:
                ticker = client.get_symbol_ticker(symbol=symbol)
                price_map[symbol] = float(ticker['price'])
            except Exception as e:
                # Silently skip invalid symbols
                pass
        
        total_usdt = 0.0
        holdings = []
        
        # Second pass: calculate values using pre-fetched prices
        for balance in account['balances']:
            try:
                free = float(balance.get('free', 0))
                locked = float(balance.get('locked', 0))
                total = free + locked
                
                if total > 0.001:  # Ignore dust
                    asset = balance.get('asset', 'UNKNOWN')
                    
                    if asset == 'USDT':
                        value_usdt = total
                        if value_usdt > 0.01:
                            holdings.append({
                                'asset': asset,
                                'quantity': total,
                                'value_usdt': value_usdt
                            })
                            total_usdt += value_usdt
                    elif asset not in skip_assets:
                        # Use pre-fetched price from batch call
                        trading_pair = f"{asset}USDT"
                        price = price_map.get(trading_pair, 0.0)
                        
                        if price > 0:
                            value_usdt = total * price
                            if value_usdt > 0.01:
                                holdings.append({
                                    'asset': asset,
                                    'quantity': total,
                                    'value_usdt': value_usdt
                                })
                                total_usdt += value_usdt
            except Exception as balance_error:
                print(f"[Portfolio] Error processing balance: {balance_error}")
                continue
        
        result = {
            'total_value_usdt': round(total_usdt, 2),
            'holdings': holdings
        }
        
        # Update cache
        _portfolio_cache['data'] = result
        _portfolio_cache['timestamp'] = datetime.now()
        
        return result
    except Exception as e:
        print(f"[Portfolio] Error getting portfolio value: {e}")
        import traceback
        traceback.print_exc()
        default = {"error": str(e)}
        # Cache the error result too
        _portfolio_cache['data'] = default
        _portfolio_cache['timestamp'] = datetime.now()
        return default


def get_recent_trades_from_db(user_email: str, limit: int = 20) -> List[dict]:
    """Get recent trades from database - only bot trades (excludes manual trades)"""
    try:
        with Session(engine) as session:
            # Filter out manual trades by excluding session_ids starting with "manual_"
            statement = select(Trade).where(
                Trade.user_email == user_email,
                ~Trade.session_id.startswith("manual_")
            ).order_by(Trade.executed_at.desc()).limit(limit)
            trades = session.exec(statement).all()
            
            result = []
            for t in trades:
                trade_dict = {
                    'symbol': t.symbol,
                    'side': t.side,
                    'price': t.price,
                    'quantity': t.quantity,
                    'total': t.total,
                    'pnl': t.pnl,
                    'time': t.executed_at.isoformat()
                }
                
                # Calculate pnl_percent for SELL trades
                if t.side == "SELL" and t.pnl is not None and t.total > 0:
                    # PnL percent = (pnl / cost_basis) * 100
                    cost_basis = t.total - t.pnl
                    if cost_basis > 0:
                        trade_dict['pnl_percent'] = (t.pnl / cost_basis) * 100
                
                result.append(trade_dict)
            
            return result
    except Exception as e:
        print(f"Error getting bot trades: {e}")
        return []


def get_recent_trades(symbol: Optional[str] = None, limit: int = 20):
    """Get recent trades from the testnet account"""
    try:
        client = get_testnet_client()
        if symbol:
            trades = client.get_my_trades(symbol=symbol, limit=limit)
        else:
            all_trades = []
            symbols = ['BTCUSDT', 'ETHUSDT', 'BNBUSDT', 'SOLUSDT']
            for sym in symbols:
                try:
                    trades = client.get_my_trades(symbol=sym, limit=5)
                    all_trades.extend(trades)
                except:
                    pass
            trades = sorted(all_trades, key=lambda x: x['time'], reverse=True)[:limit]
        
        formatted_trades = []
        for trade in trades:
            formatted_trades.append({
                'symbol': trade['symbol'],
                'side': 'BUY' if trade['isBuyer'] else 'SELL',
                'price': float(trade['price']),
                'quantity': float(trade['qty']),
                'total': float(trade['quoteQty']),
                'commission': float(trade['commission']),
                'time': datetime.fromtimestamp(trade['time'] / 1000).isoformat()
            })
        
        return formatted_trades
    except Exception as e:
        return {"error": str(e)}


def get_current_price(symbol: str):
    """Get current price for a symbol"""
    try:
        client = get_testnet_client()
        ticker = client.get_symbol_ticker(symbol=symbol)
        return float(ticker['price'])
    except Exception as e:
        return None


def get_symbol_filters(symbol: str):
    """Get trading filters for a symbol (LOT_SIZE, MIN_NOTIONAL, etc.)"""
    try:
        client = get_testnet_client()
        info = client.get_symbol_info(symbol)
        
        filters = {}
        for f in info.get('filters', []):
            if f['filterType'] == 'LOT_SIZE':
                filters['min_qty'] = float(f['minQty'])
                filters['max_qty'] = float(f['maxQty'])
                filters['step_size'] = float(f['stepSize'])
            elif f['filterType'] == 'MIN_NOTIONAL':
                filters['min_notional'] = float(f.get('minNotional', f.get('notional', 0)))
        
        return filters
    except Exception as e:
        print(f"[Filters] Could not get filters for {symbol}: {e}")
        return None

def adjust_quantity(symbol: str, quantity: float):
    """Adjust quantity to meet exchange requirements"""
    filters = get_symbol_filters(symbol)
    
    if not filters:
        # Fallback to default precision
        if 'BTC' in symbol and symbol.endswith('BTC'):
            return round(quantity, 3)
        elif 'USDT' in symbol:
            return round(quantity, 3)
        return quantity
    
    min_qty = filters.get('min_qty', 0)
    step_size = filters.get('step_size', 0.00001)
    
    # Adjust to step size
    adjusted = round(quantity / step_size) * step_size
    
    # Ensure minimum quantity
    if adjusted < min_qty:
        adjusted = min_qty
    
    # Round to appropriate precision
    precision = len(str(step_size).rstrip('0').split('.')[-1]) if '.' in str(step_size) else 0
    adjusted = round(adjusted, precision)
    
    print(f"[Quantity] Original: {quantity}, Adjusted: {adjusted} (min: {min_qty}, step: {step_size})")
    return adjusted

def place_market_order(symbol: str, side: str, quantity: float):
    """Place a market order on testnet"""
    try:
        client = get_testnet_client()
        
        # Adjust quantity to meet exchange requirements
        quantity = adjust_quantity(symbol, quantity)
        
        print(f"[Order] Placing {side} order: {symbol} qty={quantity}")
        
        order = client.create_order(
            symbol=symbol,
            side=SIDE_BUY if side.upper() == 'BUY' else SIDE_SELL,
            type=ORDER_TYPE_MARKET,
            quantity=quantity
        )
        print(f"[Order] Success: Order ID {order.get('orderId', 'N/A')}")
        return order
    except Exception as e:
        error_msg = str(e)
        print(f"[Order] Failed: {error_msg}")
        return {"error": error_msg}


def save_trade_to_db(session_id: str, user_email: str, symbol: str, 
                      side: str, price: float, quantity: float, 
                      pnl: Optional[float] = None, order_id: Optional[str] = None):
    """Save a trade to the database"""
    try:
        with Session(engine) as db_session:
            trade = Trade(
                session_id=session_id,
                user_email=user_email,
                symbol=symbol,
                side=side,
                price=price,
                quantity=quantity,
                total=price * quantity,
                pnl=pnl,
                order_id=order_id,
                executed_at=datetime.now()
            )
            db_session.add(trade)
            db_session.commit()
    except Exception as e:
        print(f"Error saving trade: {e}")


def save_session_to_db(session_id: str, user_email: str, strategy: str,
                        symbol: str, trade_amount: float, duration_minutes: int):
    """Save a trading session to the database"""
    try:
        with Session(engine) as db_session:
            trading_session = TradingSession(
                session_id=session_id,
                user_email=user_email,
                strategy=strategy,
                symbol=symbol,
                trade_amount=trade_amount,
                duration_minutes=duration_minutes,
                start_time=datetime.now(),
                is_running=True
            )
            db_session.add(trading_session)
            db_session.commit()
    except Exception as e:
        print(f"Error saving session: {e}")


def update_session_in_db(session_id: str, is_running: bool, 
                          total_pnl: float, trades_count: int):
    """Update a trading session in the database"""
    try:
        with Session(engine) as db_session:
            statement = select(TradingSession).where(
                TradingSession.session_id == session_id
            )
            trading_session = db_session.exec(statement).first()
            if trading_session:
                trading_session.is_running = is_running
                trading_session.total_pnl = total_pnl
                trading_session.trades_count = trades_count
                if not is_running:
                    trading_session.end_time = datetime.now()
                db_session.add(trading_session)
                db_session.commit()
    except Exception as e:
        print(f"Error updating session: {e}")


def get_user_sessions_from_db(user_email: str) -> List[dict]:
    """Get all sessions for a user from database"""
    try:
        with Session(engine) as db_session:
            statement = select(TradingSession).where(
                TradingSession.user_email == user_email
            ).order_by(TradingSession.start_time.desc()).limit(20)
            sessions = db_session.exec(statement).all()
            
            result = []
            for s in sessions:
                # Check if session is in active_sessions for real-time data
                if s.session_id in active_sessions:
                    runner = active_sessions[s.session_id]
                    result.append(runner.get_status())
                else:
                    # Calculate elapsed time from database
                    elapsed = (datetime.now() - s.start_time).total_seconds() / 60
                    remaining = max(0, s.duration_minutes - elapsed)
                    
                    # Auto-mark as stopped if time is up and not in active runners
                    if s.is_running and remaining <= 0:
                        s.is_running = False
                        s.end_time = datetime.now()
                        db_session.add(s)
                        db_session.commit()
                    
                    result.append({
                        'session_id': s.session_id,
                        'strategy': s.strategy,
                        'symbol': s.symbol,
                        'trade_amount': s.trade_amount,
                        'is_running': s.is_running,
                        'position': 'FLAT',
                        'trades_count': s.trades_count,
                        'pnl': s.total_pnl,
                        'elapsed_minutes': round(elapsed, 1),
                        'remaining_minutes': round(remaining, 1),
                        'trades': []
                    })
            return result
    except Exception as e:
        print(f"Error getting sessions: {e}")
        return []


class BaseTradingSessionRunner:
    """Base class for managing a live trading session."""
    
    def __init__(self, session_id: str, user_email: str, strategy: str, 
                 symbols: List[str], trade_amount: float, duration_minutes: int):
        self.session_id = session_id
        self.user_email = user_email
        self.strategy = strategy
        self.symbols = symbols
        self.trade_amount = trade_amount
        self.duration_minutes = duration_minutes
        self.start_time = datetime.now()
        self.is_running = False
        self.trades: List[dict] = []
        self.pnl = 0.0
        self.client = get_testnet_client()
        self._thread: Optional[threading.Thread] = None

    def start(self):
        self.is_running = True
        save_session_to_db(
            self.session_id, self.user_email, self.strategy,
            ",".join(self.symbols), self.trade_amount, self.duration_minutes
        )
        self._thread = threading.Thread(target=self._run_strategy, daemon=True)
        self._thread.start()
        
    def stop(self):
        self.is_running = False
        self._on_stop()
        update_session_in_db(
            self.session_id, False, self.pnl, len(self.trades)
        )
            
    def _run_strategy(self):
        raise NotImplementedError

    def _on_stop(self):
        pass

    def get_status(self) -> dict:
        raise NotImplementedError

class MediumFrequencySessionRunner(BaseTradingSessionRunner):
    """
    Medium-Frequency HMM-SVR Strategy Runner.
    
    Uses pre-trained HMM-SVR models (loaded from disk) to make trading decisions
    every 3 hours based on:
    - Regime detection (Safe/Normal/Crash)
    - Volatility prediction
    - EMA crossover signals
    - Dynamic position sizing (0x, 1x, or 3x)
    """
    
    # Trading interval: 3 hours in seconds
    TRADE_INTERVAL_SECONDS = 3 * 60 * 60  # 3 hours
    
    def __init__(self, session_id: str, user_email: str, symbol: str, 
                 trade_amount: float, duration_minutes: int,
                 short_window: int = 12, long_window: int = 26):
        super().__init__(session_id, user_email, "hmm_svr", [symbol], trade_amount, duration_minutes)
        self.symbol = symbol
        self.short_window = short_window
        self.long_window = long_window
        
        # Position tracking
        self.current_position_qty = 0.0  # Actual quantity held
        self.target_position_size = 0.0  # Target multiplier (0, 1, or 3)
        self.entry_price = 0.0
        self.last_signal_info = {}
        
        # Ensure model is loaded
        from model_manager import load_model, is_model_trained
        if not is_model_trained(symbol):
            raise Exception(f"No trained model found for {symbol}. Train it first using /api/models/train/{symbol}")
        
        model_data = load_model(symbol)
        if model_data is None:
            raise Exception(f"Failed to load model for {symbol}")
        
        print(f"[MediumFreq] Initialized for {symbol} with model trained on {model_data.get('train_days', 0)} days")

    def _on_stop(self):
        """Close any open position when session stops."""
        if self.current_position_qty > 0:
            print(f"[MediumFreq] Closing position on stop: {self.current_position_qty} {self.symbol}")
            self._adjust_position(0)

    def _run_strategy(self):
        """
        Main strategy loop - runs every 3 hours.
        """
        end_time = self.start_time.timestamp() + (self.duration_minutes * 60)
        
        # Run immediately on start
        self._execute_trading_cycle()
        
        while self.is_running and time.time() < end_time:
            try:
                # Sleep in smaller intervals to allow for graceful shutdown
                sleep_remaining = self.TRADE_INTERVAL_SECONDS
                while sleep_remaining > 0 and self.is_running and time.time() < end_time:
                    sleep_chunk = min(60, sleep_remaining)  # Sleep 1 minute at a time
                    time.sleep(sleep_chunk)
                    sleep_remaining -= sleep_chunk
                
                if self.is_running and time.time() < end_time:
                    self._execute_trading_cycle()
                    
            except Exception as e:
                print(f"[MediumFreq] Strategy error: {e}")
                import traceback
                traceback.print_exc()
                time.sleep(60)  # Wait before retrying
        
        self.is_running = False
        self._on_stop()
        update_session_in_db(self.session_id, False, self.pnl, len(self.trades))
        print(f"[MediumFreq] Session ended. Total PnL: ${self.pnl:.2f}")

    def _execute_trading_cycle(self):
        """
        Execute one trading cycle:
        1. Fetch recent data
        2. Generate signal using pre-trained model
        3. Calculate target position
        4. Adjust position if needed
        """
        print(f"\n{'='*60}")
        print(f"[MediumFreq] Trading cycle at {datetime.now().isoformat()}")
        print(f"{'='*60}")
        
        try:
            # 1. Fetch recent daily data (400 days for proper feature calculation)
            recent_data = self._fetch_recent_data(days=400)
            if recent_data is None or len(recent_data) < 100:
                print("[MediumFreq] Insufficient data, skipping cycle")
                return
            
            # 2. Generate signal using model_manager
            from model_manager import calculate_signal_and_position
            signal_result = calculate_signal_and_position(
                symbol=self.symbol,
                recent_data=recent_data,
                short_window=self.short_window,
                long_window=self.long_window
            )
            
            if signal_result is None or 'error' in signal_result:
                print(f"[MediumFreq] Signal error: {signal_result}")
                return
            
            self.last_signal_info = signal_result
            
            # 3. Calculate target position in USDT terms
            target_multiplier = signal_result['target_position']  # 0, 1, or 3
            ema_signal = signal_result['ema_signal']
            current_price = signal_result['close_price']
            
            print(f"[MediumFreq] Signal Analysis:")
            print(f"  - Regime: {signal_result['regime_label']} (state {signal_result['regime']})")
            print(f"  - Predicted Vol: {signal_result['predicted_vol']:.6f}")
            print(f"  - Risk Ratio: {signal_result['risk_ratio']:.2f}")
            print(f"  - EMA Signal: {'BULLISH' if ema_signal == 1 else 'BEARISH'}")
            print(f"  - Position Multiplier: {target_multiplier}x")
            print(f"  - Reasoning: {signal_result['reasoning']}")
            
            # 4. Calculate target quantity in asset terms
            target_usdt_value = self.trade_amount * target_multiplier
            target_quantity = target_usdt_value / current_price if current_price > 0 else 0
            
            # 5. Get current position from exchange
            current_qty = self._get_current_position()
            
            print(f"\n[MediumFreq] Position Status:")
            print(f"  - Current Position: {current_qty:.8f} {self.symbol.replace('USDT', '')}")
            print(f"  - Target Position: {target_quantity:.8f} ({target_multiplier}x = ${target_usdt_value:.2f})")
            
            # 6. Calculate and execute trade delta
            trade_delta = target_quantity - current_qty
            
            if abs(trade_delta * current_price) > 10:  # Minimum $10 trade
                self._adjust_position(target_quantity)
            else:
                print(f"[MediumFreq] Trade delta too small (${abs(trade_delta * current_price):.2f}), no action")
            
            self.target_position_size = target_multiplier
            
        except Exception as e:
            print(f"[MediumFreq] Error in trading cycle: {e}")
            import traceback
            traceback.print_exc()

    def _fetch_recent_data(self, days: int = 400) -> Optional[pd.DataFrame]:
        """
        Fetch recent daily data from Binance for signal generation.
        """
        try:
            # Use public client (no API keys needed for klines)
            client = Client()
            
            klines = client.get_historical_klines(
                symbol=self.symbol,
                interval=Client.KLINE_INTERVAL_1DAY,
                limit=days
            )
            
            if not klines or len(klines) < 100:
                print(f"[MediumFreq] Insufficient klines returned: {len(klines) if klines else 0}")
                return None
            
            df = pd.DataFrame(klines, columns=[
                'timestamp', 'Open', 'High', 'Low', 'Close', 'Volume',
                'close_time', 'quote_volume', 'trades', 'taker_buy_base',
                'taker_buy_quote', 'ignore'
            ])
            
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            df.set_index('timestamp', inplace=True)
            df['Close'] = df['Close'].astype(float)
            df['Open'] = df['Open'].astype(float)
            df['High'] = df['High'].astype(float)
            df['Low'] = df['Low'].astype(float)
            
            print(f"[MediumFreq] Fetched {len(df)} days of data, latest close: ${df['Close'].iloc[-1]:.2f}")
            return df[['Open', 'High', 'Low', 'Close', 'Volume']]
            
        except Exception as e:
            print(f"[MediumFreq] Error fetching data: {e}")
            return None

    def _get_current_position(self) -> float:
        """Get current quantity of the asset held."""
        try:
            account = self.client.get_account()
            asset = self.symbol.replace('USDT', '')
            
            for balance in account['balances']:
                if balance['asset'] == asset:
                    qty = float(balance['free']) + float(balance['locked'])
                    return qty
            return 0.0
        except Exception as e:
            print(f"[MediumFreq] Error getting position: {e}")
            return self.current_position_qty  # Fallback to tracked quantity

    def _adjust_position(self, target_qty: float):
        """
        Adjust position to match target quantity.
        Handles both increasing and decreasing positions.
        """
        current_qty = self._get_current_position()
        delta = target_qty - current_qty
        price = get_current_price(self.symbol)
        
        if price is None:
            print(f"[MediumFreq] Cannot get price for {self.symbol}")
            return
        
        if abs(delta) < 0.00001:  # Negligible difference
            print(f"[MediumFreq] Position already at target")
            return
        
        if delta > 0:
            # Need to buy
            side = 'BUY'
            quantity = delta
        else:
            # Need to sell
            side = 'SELL'
            quantity = abs(delta)
        
        print(f"[MediumFreq] Placing {side} order: {quantity:.8f} @ ${price:.2f} (${quantity * price:.2f})")
        
        order = place_market_order(self.symbol, side, quantity)
        
        if 'error' not in order:
            order_id = str(order.get('orderId', ''))
            pnl = None
            
            # Calculate PnL for sells
            if side == 'SELL' and self.entry_price > 0:
                pnl = (price - self.entry_price) * quantity
                self.pnl += pnl
                print(f"[MediumFreq] Trade PnL: ${pnl:.2f}")
            
            # Update entry price tracking
            if side == 'BUY':
                if self.current_position_qty == 0:
                    self.entry_price = price
                else:
                    # Average entry price
                    total_cost = (self.entry_price * self.current_position_qty) + (price * quantity)
                    self.entry_price = total_cost / (self.current_position_qty + quantity)
            
            self.current_position_qty = target_qty
            
            self.trades.append({
                'type': side,
                'price': price,
                'quantity': quantity,
                'time': datetime.now().isoformat(),
                'pnl': pnl,
                'order_id': order_id,
                'target_multiplier': self.target_position_size,
                'regime': self.last_signal_info.get('regime_label', 'Unknown')
            })
            
            save_trade_to_db(
                self.session_id, self.user_email, self.symbol,
                side, price, quantity, pnl, order_id
            )
            
            update_session_in_db(self.session_id, True, self.pnl, len(self.trades))
            print(f"[MediumFreq] ✅ Order executed successfully")
        else:
            print(f"[MediumFreq] ❌ Order failed: {order['error']}")

    def get_status(self) -> dict:
        elapsed = (datetime.now() - self.start_time).total_seconds() / 60
        remaining = max(0, self.duration_minutes - elapsed)
        
        # Calculate next trade time
        time_since_start = (datetime.now() - self.start_time).total_seconds()
        cycles_completed = int(time_since_start / self.TRADE_INTERVAL_SECONDS)
        next_trade_in = self.TRADE_INTERVAL_SECONDS - (time_since_start % self.TRADE_INTERVAL_SECONDS)
        
        pos_str = "FLAT"
        if self.current_position_qty > 0:
            pos_str = f"LONG {self.target_position_size}x"
        
        return {
            'session_id': self.session_id,
            'strategy': 'hmm_svr',
            'strategy_name': 'HMM-SVR Medium Frequency',
            'symbol': self.symbol,
            'trade_amount': self.trade_amount,
            'is_running': self.is_running,
            'position': pos_str,
            'position_qty': self.current_position_qty,
            'target_multiplier': self.target_position_size,
            'trades_count': len(self.trades),
            'pnl': round(self.pnl, 2),
            'elapsed_minutes': round(elapsed, 1),
            'remaining_minutes': round(remaining, 1),
            'next_trade_in_minutes': round(next_trade_in / 60, 1),
            'trade_interval_hours': 3,
            'last_signal': self.last_signal_info,
            'trades': self.trades[-10:]
        }


def start_live_trading(user_email: str, strategy: str, symbol: str, 
                       trade_amount: float, duration_minutes: int,
                       duration_unit: str = "minutes",
                       short_window: int = 12, long_window: int = 26,
                       interval: str = '5m') -> dict:
    """Factory function to start a new live trading session."""
    session_id = f"{user_email}_{datetime.now().strftime('%Y%m%d%H%M%S')}"
    
    for sid, session in active_sessions.items():
        if session.user_email == user_email and session.is_running:
            return {"error": "You already have an active trading session"}
    
    if not symbol:
        return {"error": "Symbol is required"}
    
    if strategy != "hmm_svr":
        return {"error": f"Unsupported strategy '{strategy}'. Only 'hmm_svr' is available."}
    
    try:
        # Medium-frequency strategy using pre-trained models
        session = MediumFrequencySessionRunner(
            session_id=session_id, user_email=user_email,
            symbol=symbol, trade_amount=trade_amount, duration_minutes=duration_minutes,
            short_window=short_window, long_window=long_window
        )
    except Exception as e:
        return {"error": f"Failed to start session: {e}"}

    active_sessions[session_id] = session
    session.start()
    
    return {
        "success": True, "session_id": session_id,
        "message": f"Trading session started with {strategy} on {symbol}"
    }


def stop_live_trading(session_id: str) -> dict:
    """Stop an active trading session."""
    if session_id in active_sessions:
        session = active_sessions[session_id]
        session.stop()
        del active_sessions[session_id]
        return {"success": True, "message": "Trading session stopped.", "final_pnl": session.pnl}
    
    # Fallback for sessions not in memory
    try:
        with Session(engine) as db_session:
            statement = select(TradingSession).where(TradingSession.session_id == session_id, TradingSession.is_running == True)
            trading_session = db_session.exec(statement).first()
            if trading_session:
                trading_session.is_running = False
                trading_session.end_time = datetime.now()
                db_session.add(trading_session)
                db_session.commit()
                return {"success": True, "message": "Trading session stopped (was not active in memory)."}
    except Exception as e:
        print(f"Error stopping session in DB: {e}")
    
    return {"error": "Session not found or already stopped"}


def get_session_status(session_id: str) -> dict:
    """Get status of a trading session."""
    if session_id in active_sessions:
        return active_sessions[session_id].get_status()
    
    # If not active, pull final from DB
    try:
        with Session(engine) as db_session:
            statement = select(TradingSession).where(TradingSession.session_id == session_id)
            s = db_session.exec(statement).first()
            if s:
                elapsed = ((s.end_time or datetime.now()) - s.start_time).total_seconds() / 60
                return {'session_id': s.session_id, 'strategy': s.strategy, 'symbol': s.symbol, 'trade_amount': s.trade_amount,
                        'is_running': s.is_running, 'position': 'FLAT', 'trades_count': s.trades_count, 'pnl': s.total_pnl, 
                        'elapsed_minutes': round(elapsed, 1), 'remaining_minutes': 0, 'trades': []}
    except Exception as e:
        print(f"Error getting session status from DB: {e}")

    return {"error": "Session not found"}


def get_user_sessions(user_email: str) -> List[dict]:
    """Get all sessions for a user."""
    return get_user_sessions_from_db(user_email)


# Available strategies for frontend
AVAILABLE_STRATEGIES = [
    {
        "id": "hmm_svr",
        "name": "HMM-SVR Medium Frequency",
        "description": "Uses pre-trained HMM-SVR models for regime detection and volatility prediction. Trades every 3 hours with dynamic position sizing (0x-3x leverage based on market regime).",
        "risk_level": "Medium",
        "requires_symbol": True,
        "requires_model": True,
        "trade_interval": "3 hours"
    }
]
