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


def get_testnet_client():
    """Create Binance testnet client"""
    client = Client(TESTNET_API_KEY, TESTNET_API_SECRET, testnet=True)
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
    """Get total portfolio value in USDT"""
    try:
        client = get_testnet_client()
        account = client.get_account()
        total_usdt = 0.0
        holdings = []
        
        for balance in account['balances']:
            free = float(balance['free'])
            locked = float(balance['locked'])
            total = free + locked
            
            if total > 0:
                asset = balance['asset']
                if asset == 'USDT':
                    value_usdt = total
                else:
                    try:
                        ticker = client.get_symbol_ticker(symbol=f"{asset}USDT")
                        price = float(ticker['price'])
                        value_usdt = total * price
                    except:
                        value_usdt = 0
                
                if value_usdt > 0.01:
                    holdings.append({
                        'asset': asset,
                        'quantity': total,
                        'value_usdt': value_usdt
                    })
                    total_usdt += value_usdt
        
        return {
            'total_value_usdt': total_usdt,
            'holdings': holdings
        }
    except Exception as e:
        return {"error": str(e)}


def get_recent_trades_from_db(user_email: str, limit: int = 20) -> List[dict]:
    """Get recent trades from database"""
    try:
        with Session(engine) as session:
            statement = select(Trade).where(
                Trade.user_email == user_email
            ).order_by(Trade.executed_at.desc()).limit(limit)
            trades = session.exec(statement).all()
            
            return [{
                'symbol': t.symbol,
                'side': t.side,
                'price': t.price,
                'quantity': t.quantity,
                'total': t.total,
                'pnl': t.pnl,
                'time': t.executed_at.isoformat()
            } for t in trades]
    except Exception as e:
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


def place_market_order(symbol: str, side: str, quantity: float):
    """Place a market order on testnet"""
    try:
        client = get_testnet_client()
        order = client.create_order(
            symbol=symbol,
            side=SIDE_BUY if side.upper() == 'BUY' else SIDE_SELL,
            type=ORDER_TYPE_MARKET,
            quantity=quantity
        )
        return order
    except Exception as e:
        return {"error": str(e)}


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


def _train_hmm_model(ticker: str, n_states: int = 3, train_years: int = 2):
    """
    Trains a GaussianHMM model based on historical data.
    """
    try:
        end_date = datetime.now()
        start_date = end_date - timedelta(days=train_years * 365)
        
        df = yf.download(ticker, start=start_date, end=end_date, progress=False)
        if df.empty or len(df) < 100:
            print("Not enough historical data to train HMM model.")
            return None, None

        # Feature Engineering
        df['Log_Returns'] = np.log(df['Close'] / df['Close'].shift(1))
        df['Volatility'] = df['Log_Returns'].rolling(window=10).std()
        df = df.dropna()

        # Train HMM
        X_train = df[['Log_Returns', 'Volatility']].values * 100
        hmm_model = GaussianHMM(n_components=n_states, covariance_type="full", n_iter=100, random_state=42)
        hmm_model.fit(X_train)
        
        # Identify "High Volatility" state
        state_vars = [hmm_model.means_[i][1] for i in range(n_states)]
        high_vol_state = np.argmax(state_vars)
        
        print(f"HMM model trained for {ticker}. High volatility state identified as: {high_vol_state}")
        return hmm_model, high_vol_state
    except Exception as e:
        print(f"Error training HMM model: {e}")
        return None, None


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
                if s.session_id in active_sessions:
                    runner = active_sessions[s.session_id]
                    result.append(runner.get_status())
                else:
                    elapsed = (datetime.now() - s.start_time).total_seconds() / 60
                    remaining = max(0, s.duration_minutes - elapsed)
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

def _train_hmm_model(ticker: str, n_states: int = 3, train_years: int = 2):
    """Trains a GaussianHMM model based on historical data."""
    try:
        end_date = datetime.now()
        start_date = end_date - timedelta(days=train_years * 365)
        
        df = yf.download(ticker, start=start_date, end=end_date, progress=False)
        if df.empty or len(df) < 100:
            print("Not enough historical data to train HMM model.")
            return None, None

        df['Log_Returns'] = np.log(df['Close'] / df['Close'].shift(1))
        df['Volatility'] = df['Log_Returns'].rolling(window=10).std()
        df = df.dropna()

        X_train = df[['Log_Returns', 'Volatility']].values * 100
        hmm_model = GaussianHMM(n_components=n_states, covariance_type="full", n_iter=100, random_state=42)
        hmm_model.fit(X_train)
        
        state_vars = [hmm_model.means_[i][1] for i in range(n_states)]
        high_vol_state = np.argmax(state_vars)
        
        print(f"HMM model trained for {ticker}. High volatility state identified as: {high_vol_state}")
        return hmm_model, high_vol_state
    except Exception as e:
        print(f"Error training HMM model: {e}")
        return None, None

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

class SingleAssetSessionRunner(BaseTradingSessionRunner):
    """Manages a session for a single-asset strategy like HMM."""
    
    def __init__(self, session_id: str, user_email: str, strategy: str, 
                 symbol: str, trade_amount: float, duration_minutes: int,
                 short_window: int = 12, long_window: int = 26, interval: str = '5m'):
        super().__init__(session_id, user_email, strategy, [symbol], trade_amount, duration_minutes)
        self.position = 0
        self.symbol = symbol
        self.short_window = short_window
        self.long_window = long_window
        self.interval = interval

        self.hmm_model: Optional[GaussianHMM] = None
        self.high_vol_state: Optional[int] = None

        if self.strategy == "hmm":
            self.hmm_model, self.high_vol_state = _train_hmm_model(self.symbol)
            if self.hmm_model is None:
                raise Exception("Failed to initialize HMM strategy: Model training failed.")

    def _on_stop(self):
        if self.position > 0:
            self._close_position()
            
    def _run_strategy(self):
        end_time = self.start_time.timestamp() + (self.duration_minutes * 60)
        while self.is_running and time.time() < end_time:
            try:
                signal = self._get_signal()
                if signal == 1 and self.position == 0:
                    self._open_position()
                elif signal == 0 and self.position == 1:
                    self._close_position()
                time.sleep(60)
            except Exception as e:
                print(f"Strategy error: {e}")
                time.sleep(60)
        self.is_running = False
        self._on_stop()
        update_session_in_db(self.session_id, False, self.pnl, len(self.trades))
            
    def _get_signal(self) -> int:
        try:
            # Map interval string to Binance constant
            interval_map = {
                '1m': Client.KLINE_INTERVAL_1MINUTE,
                '5m': Client.KLINE_INTERVAL_5MINUTE,
                '15m': Client.KLINE_INTERVAL_15MINUTE,
                '1h': Client.KLINE_INTERVAL_1HOUR
            }
            binance_interval = interval_map.get(self.interval, Client.KLINE_INTERVAL_5MINUTE)
            
            klines = self.client.get_klines(symbol=self.symbol, interval=binance_interval, limit=100)
            df = pd.DataFrame({'close': [float(k[4]) for k in klines]})
            df['ema_short'] = df['close'].ewm(span=self.short_window).mean()
            df['ema_long'] = df['close'].ewm(span=self.long_window).mean()
            if self.strategy == "hmm":
                return self._hmm_signal(df)
            else:
                return -1
        except Exception as e:
            print(f"Signal error: {e}")
            return -1
            
    def _hmm_signal(self, df: pd.DataFrame) -> int:
        if self.hmm_model is None or self.high_vol_state is None: return -1
        df['log_returns'] = np.log(df['close'] / df['close'].shift(1))
        df['volatility'] = df['log_returns'].rolling(window=10).std()
        df = df.dropna()
        if df.empty: return -1
        current_features = df[['log_returns', 'volatility']].values * 100
        current_regime = self.hmm_model.predict(current_features)[-1]
        is_high_vol = (current_regime == self.high_vol_state)
        ema_crossover_bullish = (df['ema_short'].iloc[-1] > df['ema_long'].iloc[-1])
        if not is_high_vol and ema_crossover_bullish: return 1
        elif is_high_vol or not ema_crossover_bullish: return 0
        else: return -1
        
    def _open_position(self):
        try:
            price = get_current_price(self.symbol)
            if price:
                quantity = round(self.trade_amount / price, 5)
                order = place_market_order(self.symbol, 'BUY', quantity)
                if 'error' not in order:
                    self.position = 1
                    order_id = str(order.get('orderId', ''))
                    self.trades.append({'type': 'BUY', 'price': price, 'quantity': quantity, 'time': datetime.now().isoformat(), 'order_id': order_id})
                    save_trade_to_db(self.session_id, self.user_email, self.symbol, 'BUY', price, quantity, None, order_id)
        except Exception as e:
            print(f"Open position error: {e}")
            
    def _close_position(self):
        try:
            last_buy = next((t for t in reversed(self.trades) if t['type'] == 'BUY'), None)
            if last_buy:
                price = get_current_price(self.symbol)
                quantity = last_buy['quantity']
                order = place_market_order(self.symbol, 'SELL', quantity)
                if 'error' not in order:
                    self.position = 0
                    pnl = (price - last_buy['price']) * quantity
                    self.pnl += pnl
                    order_id = str(order.get('orderId', ''))
                    self.trades.append({'type': 'SELL', 'price': price, 'quantity': quantity, 'time': datetime.now().isoformat(), 'pnl': pnl, 'order_id': order_id})
                    save_trade_to_db(self.session_id, self.user_email, self.symbol, 'SELL', price, quantity, pnl, order_id)
                    update_session_in_db(self.session_id, True, self.pnl, len(self.trades))
        except Exception as e:
            print(f"Close position error: {e}")
            
    def get_status(self) -> dict:
        elapsed = (datetime.now() - self.start_time).total_seconds() / 60
        remaining = max(0, self.duration_minutes - elapsed)
        return {'session_id': self.session_id, 'strategy': self.strategy, 'symbol': self.symbol, 'trade_amount': self.trade_amount,
                'is_running': self.is_running, 'position': 'LONG' if self.position == 1 else 'FLAT', 'trades_count': len(self.trades),
                'pnl': self.pnl, 'elapsed_minutes': round(elapsed, 1), 'remaining_minutes': round(remaining, 1), 'trades': self.trades[-10:]}

class PairsTradingSessionRunner(BaseTradingSessionRunner):
    """Manages a session for the ETH/BTC pairs trading strategy."""
    
    def __init__(self, session_id: str, user_email: str, trade_amount: float, duration_minutes: int,
                 window: int = 60, threshold: float = 1.0, interval: str = '5m'):
        super().__init__(session_id, user_email, "pairs", ["ETHBTC"], trade_amount, duration_minutes)
        self.position_state = 0 # 0: flat, 1: long ratio, -1: short ratio
        self.z_score = 0
        self.window = window
        self.threshold = threshold
        self.interval = interval
        self.entry_price = 0

    def _on_stop(self):
        if self.position_state != 0:
            self._close_position()

    def _run_strategy(self):
        end_time = self.start_time.timestamp() + (self.duration_minutes * 60)
        while self.is_running and time.time() < end_time:
            try:
                signal = self._get_signal()
                if self.position_state == 0:
                    if signal == 1: self._open_position(1)
                    elif signal == -1: self._open_position(-1)
                elif self.position_state == 1 and signal == 0:
                    self._close_position()
                elif self.position_state == -1 and signal == 0:
                    self._close_position()
                time.sleep(60)
            except Exception as e:
                print(f"Strategy error: {e}")
                time.sleep(60)
        self.is_running = False
        self._on_stop()
        update_session_in_db(self.session_id, False, self.pnl, len(self.trades))

    def _get_signal(self) -> int:
        try:
            # Map interval string to Binance constant
            interval_map = {
                '1m': Client.KLINE_INTERVAL_1MINUTE,
                '5m': Client.KLINE_INTERVAL_5MINUTE,
                '15m': Client.KLINE_INTERVAL_15MINUTE,
                '1h': Client.KLINE_INTERVAL_1HOUR
            }
            binance_interval = interval_map.get(self.interval, Client.KLINE_INTERVAL_5MINUTE)
            
            # Fetch ETHBTC ratio directly from Binance
            ratio_klines = self.client.get_klines(symbol='ETHBTC', interval=binance_interval, limit=self.window + 5)
            
            df = pd.DataFrame(index=pd.to_datetime([k[0] for k in ratio_klines], unit='ms'))
            df['Ratio'] = [float(k[4]) for k in ratio_klines]  # Close price is the ETH/BTC ratio
            df = df.dropna()

            df['Mean'] = df['Ratio'].rolling(window=self.window).mean()
            df['Std'] = df['Ratio'].rolling(window=self.window).std()
            df['Z-Score'] = (df['Ratio'] - df['Mean']) / df['Std']
            df = df.dropna()

            if df.empty: return -2
            self.z_score = df['Z-Score'].iloc[-1]
            current_ratio = df['Ratio'].iloc[-1]

            if self.position_state == 0:
                if self.z_score < -self.threshold:
                    self.entry_price = current_ratio
                    return 1
                elif self.z_score > self.threshold:
                    self.entry_price = current_ratio
                    return -1
            elif self.position_state == 1 and self.z_score >= 0: return 0
            elif self.position_state == -1 and self.z_score <= 0: return 0
            return -2 # Hold
        except Exception as e:
            print(f"Signal error: {e}")
            return -2

    def _open_position(self, direction: int):
        try:
            # Trade ETHBTC pair directly (ratio trading)
            ratio_price = get_current_price("ETHBTC")
            if not ratio_price: return
            
            # Calculate quantity based on BTC amount we want to trade
            # trade_amount is in USDT, convert to BTC first
            btc_price = get_current_price("BTCUSDT")
            if not btc_price: return
            btc_amount = self.trade_amount / btc_price
            
            # Quantity in ETH for the ETHBTC pair
            eth_qty = round(btc_amount / ratio_price, 5)

            if direction == 1: # Long Ratio: Buy ETHBTC
                side = 'BUY'
            else: # Short Ratio: Sell ETHBTC
                side = 'SELL'

            order = place_market_order('ETHBTC', side, eth_qty)

            if 'error' not in order:
                self.position_state = direction
                self.trades.append({
                    'type': f'OPEN_{side}',
                    'price': ratio_price,
                    'quantity': eth_qty,
                    'time': datetime.now().isoformat(),
                    'order_id': str(order.get('orderId', ''))
                })
                save_trade_to_db(self.session_id, self.user_email, 'ETHBTC', side, ratio_price, eth_qty, None, str(order.get('orderId', '')))
        except Exception as e:
            print(f"Pairs open position error: {e}")

    def _close_position(self):
        try:
            # Find the opening trade
            open_trade = next((t for t in reversed(self.trades) if 'OPEN' in t['type']), None)
            if not open_trade: return

            # Close position in opposite direction
            if self.position_state == 1: # Was Long Ratio -> Sell ETHBTC
                side = 'SELL'
            else: # Was Short Ratio -> Buy ETHBTC
                side = 'BUY'
            
            qty = open_trade['quantity']
            order = place_market_order('ETHBTC', side, qty)

            if 'error' not in order:
                # PnL Calculation (ratio-based, matching backtest)
                exit_price = get_current_price('ETHBTC') or open_trade['price']
                
                if self.position_state == 1:  # Long ratio
                    raw_pnl = (exit_price - self.entry_price) / self.entry_price
                else:  # Short ratio
                    raw_pnl = (self.entry_price - exit_price) / self.entry_price
                
                # Convert to USDT PnL (approximate using BTC price)
                btc_price = get_current_price('BTCUSDT') or 1
                trade_pnl = raw_pnl * self.trade_amount
                self.pnl += trade_pnl

                self.position_state = 0
                self.trades.append({
                    'type': f'CLOSE_{side}',
                    'price': exit_price,
                    'quantity': qty,
                    'pnl': trade_pnl,
                    'pnl_pct': raw_pnl * 100,
                    'time': datetime.now().isoformat(),
                    'order_id': str(order.get('orderId', ''))
                })
                save_trade_to_db(self.session_id, self.user_email, 'ETHBTC', side, exit_price, qty, trade_pnl, str(order.get('orderId', '')))
                update_session_in_db(self.session_id, True, self.pnl, len(self.trades))

        except Exception as e:
            print(f"Pairs close position error: {e}")

    def get_status(self) -> dict:
        elapsed = (datetime.now() - self.start_time).total_seconds() / 60
        remaining = max(0, self.duration_minutes - elapsed)
        pos_str = "FLAT"
        if self.position_state == 1: pos_str = "LONG ETH/BTC"
        elif self.position_state == -1: pos_str = "SHORT ETH/BTC"
        
        return {'session_id': self.session_id, 'strategy': self.strategy, 'symbol': ",".join(self.symbols), 'trade_amount': self.trade_amount,
                'is_running': self.is_running, 'position': pos_str, 'trades_count': len(self.trades),
                'pnl': self.pnl, 'elapsed_minutes': round(elapsed, 1), 'remaining_minutes': round(remaining, 1), 
                'z_score': round(self.z_score, 3), 'trades': self.trades[-10:]}


def start_live_trading(user_email: str, strategy: str, symbol: str, 
                       trade_amount: float, duration_minutes: int,
                       duration_unit: str = "minutes",
                       short_window: int = 12, long_window: int = 26,
                       window: int = 60, threshold: float = 1.0,
                       interval: str = '5m') -> dict:
    """Factory function to start a new live trading session."""
    session_id = f"{user_email}_{datetime.now().strftime('%Y%m%d%H%M%S')}"
    
    for sid, session in active_sessions.items():
        if session.user_email == user_email and session.is_running:
            return {"error": "You already have an active trading session"}
    
    try:
        if strategy == "pairs":
            session = PairsTradingSessionRunner(
                session_id=session_id, user_email=user_email,
                trade_amount=trade_amount, duration_minutes=duration_minutes,
                window=window, threshold=threshold, interval=interval
            )
        else: # HMM and other single-asset strategies
            if not symbol:
                return {"error": "Symbol is required for this strategy"}
            session = SingleAssetSessionRunner(
                session_id=session_id, user_email=user_email, strategy=strategy,
                symbol=symbol, trade_amount=trade_amount, duration_minutes=duration_minutes,
                short_window=short_window, long_window=long_window, interval=interval
            )
    except Exception as e:
        return {"error": f"Failed to start session: {e}"}

    active_sessions[session_id] = session
    session.start()
    
    return {
        "success": True, "session_id": session_id,
        "message": f"Trading session started with {strategy} on {symbol or 'ETHBTC'}"
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
        "id": "hmm",
        "name": "HMM Regime Filter",
        "description": "Uses a trained Hidden Markov Model to trade EMA crossovers only in low-volatility regimes.",
        "risk_level": "Medium",
        "requires_symbol": True
    },
    {
        "id": "pairs",
        "name": "Pairs Trading (ETH/BTC)",
        "description": "Trades the mean reversion of the ETH/BTC price ratio using a Z-Score. Assumes ability to long/short both assets.",
        "risk_level": "Medium-High",
        "requires_symbol": False
    }
]
