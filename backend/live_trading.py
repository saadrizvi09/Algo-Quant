"""
Live Trading Module for Binance Testnet
Handles real trading operations using paper money on Binance Testnet Vision
"""
import os
import time
import threading
from datetime import datetime
from typing import Optional, Dict, List
from binance.client import Client
from binance.enums import *
import pandas as pd
import numpy as np
from dotenv import load_dotenv
from sqlmodel import Session, select
from database import engine
from models import Trade, TradingSession

load_dotenv()

# Binance Testnet Configuration
TESTNET_API_KEY = os.getenv("BINANCE_API_KEY", "")
TESTNET_API_SECRET = os.getenv("BINANCE_SECRET_KEY", "")

# Storage for active trading sessions (in-memory for real-time tracking)
active_sessions: Dict[str, "LiveTradingSessionRunner"] = {}


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


class LiveTradingSessionRunner:
    """Manages a live trading session with a specific strategy"""
    
    def __init__(self, session_id: str, user_email: str, strategy: str, 
                 symbol: str, trade_amount: float, duration_minutes: int):
        self.session_id = session_id
        self.user_email = user_email
        self.strategy = strategy
        self.symbol = symbol
        self.trade_amount = trade_amount
        self.duration_minutes = duration_minutes
        self.start_time = datetime.now()
        self.is_running = False
        self.position = 0
        self.trades: List[dict] = []
        self.pnl = 0.0
        self.client = get_testnet_client()
        self._thread: Optional[threading.Thread] = None
        
    def start(self):
        """Start the trading session in a background thread"""
        self.is_running = True
        save_session_to_db(
            self.session_id, self.user_email, self.strategy,
            self.symbol, self.trade_amount, self.duration_minutes
        )
        self._thread = threading.Thread(target=self._run_strategy, daemon=True)
        self._thread.start()
        
    def stop(self):
        """Stop the trading session"""
        self.is_running = False
        if self.position > 0:
            self._close_position()
        update_session_in_db(
            self.session_id, False, self.pnl, len(self.trades)
        )
            
    def _run_strategy(self):
        """Main strategy loop"""
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
        if self.position > 0:
            self._close_position()
        
        update_session_in_db(
            self.session_id, False, self.pnl, len(self.trades)
        )
            
    def _get_signal(self) -> int:
        """Get trading signal based on selected strategy"""
        try:
            klines = self.client.get_klines(
                symbol=self.symbol, 
                interval=Client.KLINE_INTERVAL_1MINUTE,
                limit=50
            )
            
            closes = [float(k[4]) for k in klines]
            df = pd.DataFrame({'close': closes})
            
            if self.strategy == "hmm":
                return self._hmm_signal(df)
            elif self.strategy == "ema_crossover":
                return self._ema_crossover_signal(df)
            elif self.strategy == "rsi":
                return self._rsi_signal(df)
            elif self.strategy == "macd":
                return self._macd_signal(df)
            elif self.strategy == "bollinger":
                return self._bollinger_signal(df)
            else:
                return self._ema_crossover_signal(df)
                
        except Exception as e:
            print(f"Signal error: {e}")
            return -1
            
    def _hmm_signal(self, df: pd.DataFrame) -> int:
        """HMM-based signal (simplified for live trading)"""
        df['ema_short'] = df['close'].ewm(span=12).mean()
        df['ema_long'] = df['close'].ewm(span=26).mean()
        df['volatility'] = df['close'].pct_change().rolling(10).std()
        
        current_vol = df['volatility'].iloc[-1]
        avg_vol = df['volatility'].mean()
        
        high_vol = current_vol > avg_vol * 1.5
        
        if high_vol:
            return 0
        elif df['ema_short'].iloc[-1] > df['ema_long'].iloc[-1]:
            return 1
        else:
            return 0
            
    def _ema_crossover_signal(self, df: pd.DataFrame) -> int:
        """Simple EMA crossover strategy"""
        df['ema_short'] = df['close'].ewm(span=9).mean()
        df['ema_long'] = df['close'].ewm(span=21).mean()
        
        if df['ema_short'].iloc[-1] > df['ema_long'].iloc[-1]:
            return 1
        return 0
        
    def _rsi_signal(self, df: pd.DataFrame) -> int:
        """RSI-based strategy"""
        delta = df['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        
        current_rsi = rsi.iloc[-1]
        if current_rsi < 30:
            return 1
        elif current_rsi > 70:
            return 0
        return -1
        
    def _macd_signal(self, df: pd.DataFrame) -> int:
        """MACD strategy"""
        ema_12 = df['close'].ewm(span=12).mean()
        ema_26 = df['close'].ewm(span=26).mean()
        macd = ema_12 - ema_26
        signal = macd.ewm(span=9).mean()
        
        if macd.iloc[-1] > signal.iloc[-1]:
            return 1
        return 0
        
    def _bollinger_signal(self, df: pd.DataFrame) -> int:
        """Bollinger Bands strategy"""
        df['sma'] = df['close'].rolling(20).mean()
        df['std'] = df['close'].rolling(20).std()
        df['upper'] = df['sma'] + 2 * df['std']
        df['lower'] = df['sma'] - 2 * df['std']
        
        current_price = df['close'].iloc[-1]
        if current_price < df['lower'].iloc[-1]:
            return 1
        elif current_price > df['upper'].iloc[-1]:
            return 0
        return -1
        
    def _open_position(self):
        """Open a long position"""
        try:
            price = get_current_price(self.symbol)
            if price:
                quantity = self.trade_amount / price
                quantity = round(quantity, 5)
                
                order = place_market_order(self.symbol, 'BUY', quantity)
                if 'error' not in order:
                    self.position = 1
                    order_id = str(order.get('orderId', ''))
                    
                    self.trades.append({
                        'type': 'BUY',
                        'price': price,
                        'quantity': quantity,
                        'time': datetime.now().isoformat(),
                        'order_id': order_id
                    })
                    
                    save_trade_to_db(
                        self.session_id, self.user_email, self.symbol,
                        'BUY', price, quantity, None, order_id
                    )
        except Exception as e:
            print(f"Open position error: {e}")
            
    def _close_position(self):
        """Close the current position"""
        try:
            if self.trades:
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
                        
                        self.trades.append({
                            'type': 'SELL',
                            'price': price,
                            'quantity': quantity,
                            'time': datetime.now().isoformat(),
                            'pnl': pnl,
                            'order_id': order_id
                        })
                        
                        save_trade_to_db(
                            self.session_id, self.user_email, self.symbol,
                            'SELL', price, quantity, pnl, order_id
                        )
                        
                        update_session_in_db(
                            self.session_id, True, self.pnl, len(self.trades)
                        )
        except Exception as e:
            print(f"Close position error: {e}")
            
    def get_status(self) -> dict:
        """Get current session status"""
        elapsed = (datetime.now() - self.start_time).total_seconds() / 60
        remaining = max(0, self.duration_minutes - elapsed)
        
        return {
            'session_id': self.session_id,
            'strategy': self.strategy,
            'symbol': self.symbol,
            'trade_amount': self.trade_amount,
            'is_running': self.is_running,
            'position': 'LONG' if self.position == 1 else 'FLAT',
            'trades_count': len(self.trades),
            'pnl': self.pnl,
            'elapsed_minutes': round(elapsed, 1),
            'remaining_minutes': round(remaining, 1),
            'trades': self.trades[-10:]
        }


def start_live_trading(user_email: str, strategy: str, symbol: str, 
                       trade_amount: float, duration_minutes: int,
                       duration_unit: str = "minutes") -> dict:
    """Start a new live trading session"""
    session_id = f"{user_email}_{datetime.now().strftime('%Y%m%d%H%M%S')}"
    
    # Check if user already has an active session
    for sid, session in active_sessions.items():
        if session.user_email == user_email and session.is_running:
            return {"error": "You already have an active trading session"}
    
    session = LiveTradingSessionRunner(
        session_id=session_id,
        user_email=user_email,
        strategy=strategy,
        symbol=symbol,
        trade_amount=trade_amount,
        duration_minutes=duration_minutes
    )
    
    active_sessions[session_id] = session
    session.start()
    
    return {
        "success": True,
        "session_id": session_id,
        "message": f"Trading session started with {strategy} strategy on {symbol}"
    }


def stop_live_trading(session_id: str) -> dict:
    """Stop an active trading session"""
    # First check if it's in active memory
    if session_id in active_sessions:
        session = active_sessions[session_id]
        session.stop()
        
        return {
            "success": True,
            "message": "Trading session stopped",
            "final_pnl": session.pnl,
            "total_trades": len(session.trades)
        }
    
    # If not in memory, try to stop in database directly
    try:
        with Session(engine) as db_session:
            statement = select(TradingSession).where(
                TradingSession.session_id == session_id
            )
            trading_session = db_session.exec(statement).first()
            if trading_session:
                trading_session.is_running = False
                trading_session.end_time = datetime.now()
                db_session.add(trading_session)
                db_session.commit()
                return {
                    "success": True,
                    "message": "Trading session stopped (was not active in memory)",
                    "final_pnl": trading_session.total_pnl,
                    "total_trades": trading_session.trades_count
                }
    except Exception as e:
        print(f"Error stopping session: {e}")
    
    return {"error": "Session not found"}


def get_session_status(session_id: str) -> dict:
    """Get status of a trading session"""
    if session_id in active_sessions:
        return active_sessions[session_id].get_status()
    return {"error": "Session not found"}


def get_user_sessions(user_email: str) -> List[dict]:
    """Get all sessions for a user"""
    return get_user_sessions_from_db(user_email)


# Available strategies for frontend
AVAILABLE_STRATEGIES = [
    {
        "id": "hmm",
        "name": "HMM Regime Filter",
        "description": "Uses Hidden Markov Models to detect market regimes and filters trades during high volatility",
        "risk_level": "Medium",
        "requires_symbol": True
    },
    {
        "id": "ema_crossover",
        "name": "EMA Crossover",
        "description": "Classic 9/21 EMA crossover strategy for trend following",
        "risk_level": "Medium",
        "requires_symbol": True
    },
    {
        "id": "rsi",
        "name": "RSI Mean Reversion",
        "description": "Trades overbought/oversold conditions using RSI indicator",
        "risk_level": "Medium-High",
        "requires_symbol": True
    },
    {
        "id": "macd",
        "name": "MACD Momentum",
        "description": "MACD line and signal crossover for momentum trading",
        "risk_level": "Medium",
        "requires_symbol": True
    },
    {
        "id": "bollinger",
        "name": "Bollinger Bounce",
        "description": "Mean reversion strategy using Bollinger Bands",
        "risk_level": "Medium-High",
        "requires_symbol": True
    },
    {
        "id": "pairs",
        "name": "Pairs Trading (Test)",
        "description": "ETH/BTC mean reversion using Z-Score. High frequency testing strategy.",
        "risk_level": "Medium",
        "requires_symbol": False
    }
]
