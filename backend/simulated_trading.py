"""
HMM-SVR Trading Bot with Simulated Exchange
Long-term trading strategy using HMM regime detection and SVR volatility prediction.
Checks for trading signals every 3 hours - designed for position trading, not high-frequency.
"""
from datetime import datetime, timedelta
from typing import Optional
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
import simulated_exchange
from models import TradingSession, Trade
from sqlmodel import Session, select
from database import engine
import uuid
from strategy_handlers import HMMSVRStrategyHandler

# Active trading sessions
simulated_sessions = {}


class SimulatedTradingSession:
    """
    HMM-SVR Trading Bot Session
    Long-only strategy using regime detection - checks every 3 hours
    """
    
    def __init__(self, session_id: str, user_email: str, symbol: str, 
                 trade_amount: float, duration_minutes: int):
        self.session_id = session_id
        self.user_email = user_email
        self.strategy = "hmm_svr"  # Only strategy supported
        self.symbol = symbol  # e.g., "BTCUSDT"
        self.trade_amount = trade_amount
        self.duration_minutes = duration_minutes
        
        # Parse trading pair (e.g., BTCUSDT -> BTC, USDT)
        if symbol.endswith("USDT"):
            self.base_asset = symbol[:-4]
            self.quote_asset = "USDT"
        else:
            self.base_asset = symbol
            self.quote_asset = "USDT"
        
        # Session state
        self.is_running = True
        self.start_time = datetime.now()
        self.end_time = self.start_time + timedelta(minutes=duration_minutes)
        self.total_pnl = 0.0
        self.trades_count = 0
        self.position = None  # None or 'LONG' (no SHORT for long-term strategy)
        self.entry_price = None
        
        print(f"[HMM-SVR Bot] {symbol} -> {self.base_asset}/{self.quote_asset}")
        
        # Auto-train model if not exists
        self._ensure_model_trained()
        
        # Initialize HMM-SVR strategy handler
        try:
            self.handler = HMMSVRStrategyHandler(symbol=self.base_asset)
            print(f"[HMM-SVR Bot] ✅ Strategy initialized")
        except Exception as e:
            print(f"[HMM-SVR Bot] ❌ Init failed: {e}")
            raise
        
        # Scheduler - checks every 3 hours
        self.scheduler = BackgroundScheduler()
        self.scheduler.add_job(
            func=self._trading_loop,
            trigger=IntervalTrigger(hours=3),
            id=f"hmm_svr_{session_id}",
            name=f"HMM-SVR Bot - {symbol}",
            replace_existing=True
        )
        
        print(f"[HMM-SVR Bot] Session created | Duration: {duration_minutes}min | Amount: ${trade_amount}")
    
    def _ensure_model_trained(self):
        """Check if model exists, train if not"""
        try:
            from model_manager import load_model, train_and_save_model
            
            # Check if model exists
            model_data = load_model(self.base_asset)
            
            if model_data is None:
                print(f"[HMM-SVR Bot] 🔄 No model found for {self.base_asset}, training now...")
                print(f"[HMM-SVR Bot] ⏳ Training on historical data (this may take 30-60 seconds)...")
                
                # Train model
                result = train_and_save_model(self.base_asset, n_states=3)
                
                if result and 'error' not in result:
                    print(f"[HMM-SVR Bot] ✅ Model trained successfully for {self.base_asset}")
                else:
                    error_msg = result.get('error', 'Unknown error') if result else 'Training failed'
                    print(f"[HMM-SVR Bot] ⚠️ Model training failed: {error_msg}")
            else:
                print(f"[HMM-SVR Bot] ✅ Model already trained for {self.base_asset}")
                
        except Exception as e:
            print(f"[HMM-SVR Bot] ⚠️ Error checking/training model: {e}")
    
    def start(self):
        """Start the trading bot"""
        self.scheduler.start()
        self._trading_loop()  # First check immediately
        print(f"[HMM-SVR Bot] ✅ Started - next check in 3 hours")
    
    def stop(self, close_positions: bool = False):
        """Stop the trading bot"""
        self.is_running = False
        self.scheduler.shutdown(wait=False)
        
        if close_positions and self.position:
            self._close_position()
        
        print(f"[HMM-SVR Bot] ⏹️ Stopped | Trades: {self.trades_count} | P&L: ${self.total_pnl:.2f}")
    
    def _trading_loop(self):
        """Main check - runs every 3 hours"""
        try:
            if not self.is_running:
                return
            
            if datetime.now() >= self.end_time:
                print(f"[HMM-SVR Bot] Session expired")
                _cleanup_expired_session(self.session_id)
                return
            
            # Get current price
            price = simulated_exchange.get_current_price(self.base_asset, self.quote_asset)
            if price is None:
                print(f"[HMM-SVR Bot] ❌ Could not fetch {self.symbol} price")
                return
            
            # Get signal from HMM-SVR model
            signal = self.handler.get_signal(price)
            
            # Log check
            elapsed_hours = (datetime.now() - self.start_time).total_seconds() / 3600
            position_str = self.position or 'NONE'
            print(f"[HMM-SVR Bot] ⏰ Check | {elapsed_hours:.1f}h | ${price:,.2f} | {signal} | Pos: {position_str}")
            
            # Execute based on signal (long-only strategy)
            if signal == "BUY" and self.position is None:
                self._open_long_position(price)
            elif signal == "SELL" and self.position == "LONG":
                self._close_position(price)
            
        except Exception as e:
            print(f"[HMM-SVR Bot] ❌ Error: {e}")
    
    def _open_long_position(self, price: float):
        """Open a LONG position (BUY)"""
        quantity = self.trade_amount / price
        
        success, trade_info = simulated_exchange.execute_buy(
            symbol=self.base_asset,
            quote_symbol=self.quote_asset,
            amount_to_buy=quantity,
            user_email=self.user_email
        )
        
        if success:
            self.position = "LONG"
            self.entry_price = price
            self._save_trade_to_db(trade_info)
            print(f"[HMM-SVR Bot] 📈 LONG opened: {quantity:.8f} {self.base_asset} @ ${price:,.2f}")
        else:
            print(f"[HMM-SVR Bot] ❌ Failed to open position")
    
    def _close_position(self, current_price: float = None):
        """Close LONG position by selling"""
        if not self.position:
            return
        
        if current_price is None:
            current_price = simulated_exchange.get_current_price(self.base_asset, self.quote_asset)
            if current_price is None:
                return
        
        # Sell all holdings to close position
        balance = simulated_exchange.get_balance(self.base_asset, self.user_email)
        if balance > 0.00001:
            success, trade_info = simulated_exchange.execute_sell(
                symbol=self.base_asset,
                quote_symbol=self.quote_asset,
                amount_to_sell=balance,
                user_email=self.user_email
            )
            if success:
                pnl = (current_price - self.entry_price) * balance
                self.total_pnl += pnl
                self._save_trade_to_db(trade_info, pnl=pnl)
                print(f"[HMM-SVR Bot] ✅ LONG closed | P&L: ${pnl:.2f}")
            else:
                print(f"[HMM-SVR Bot] ❌ Failed to close position")
        
        self.position = None
        self.entry_price = None
    
    def _save_trade_to_db(self, trade_info: dict, pnl: Optional[float] = None):
        """Save trade to database"""
        try:
            with Session(engine) as session:
                trade = Trade(
                    session_id=self.session_id,
                    user_email=self.user_email,
                    symbol=trade_info['symbol'],
                    side=trade_info['side'],
                    price=trade_info['price'],
                    quantity=trade_info['quantity'],
                    total=trade_info.get('total', trade_info.get('cost', 0)),
                    pnl=pnl,
                    executed_at=datetime.now()
                )
                session.add(trade)
                session.commit()
                
                # Only increment after successful DB save
                self.trades_count += 1
                
        except Exception as e:
            print(f"[SimTrading] Error saving trade: {e}")
    
    def get_status(self) -> dict:
        """Get current session status"""
        return {
            'session_id': self.session_id,
            'strategy': self.strategy,
            'symbol': self.symbol,
            'is_running': self.is_running,
            'position': self.position,
            'entry_price': self.entry_price,
            'trades_count': self.trades_count,
            'total_pnl': self.total_pnl,
            'start_time': self.start_time.isoformat(),
            'end_time': self.end_time.isoformat(),
            'time_remaining': max(0, (self.end_time - datetime.now()).total_seconds())
        }


def start_simulated_trading(user_email: str, symbol: str,
                           trade_amount: float, duration_minutes: int, **kwargs) -> dict:
    """
    Start HMM-SVR trading bot session
    
    Args:
        user_email: User identifier
        symbol: Trading pair (e.g., "BTCUSDT")
        trade_amount: Amount per trade in USDT
        duration_minutes: How long to run
    
    Returns:
        Session info dictionary
    """
    session_id = str(uuid.uuid4())
    
    # Create and start session
    session = SimulatedTradingSession(
        session_id=session_id,
        user_email=user_email,
        symbol=symbol,
        trade_amount=trade_amount,
        duration_minutes=duration_minutes
    )
    
    session.start()
    simulated_sessions[session_id] = session
    print(f"[HMM-SVR Bot] ✅ Session {session_id} active")
    
    # Save to database
    try:
        with Session(engine) as db_session:
            db_trading_session = TradingSession(
                session_id=session_id,
                user_email=user_email,
                strategy="hmm_svr",
                symbol=symbol,
                trade_amount=trade_amount,
                duration_minutes=duration_minutes,
                start_time=datetime.now(),
                is_running=True
            )
            db_session.add(db_trading_session)
            db_session.commit()
    except Exception as e:
        print(f"[HMM-SVR Bot] DB error: {e}")
    
    return {
        'session_id': session_id,
        'message': f'HMM-SVR trading bot started for {symbol}',
        'status': session.get_status()
    }


def _cleanup_expired_session(session_id: str):
    """Clean up expired session"""
    if session_id in simulated_sessions:
        session = simulated_sessions[session_id]
        session.stop(close_positions=False)
        
        # Update database
        try:
            with Session(engine) as db_session:
                stmt = select(TradingSession).where(TradingSession.session_id == session_id)
                db_trading_session = db_session.exec(stmt).first()
                if db_trading_session:
                    db_trading_session.is_running = False
                    db_trading_session.end_time = datetime.now()
                    db_trading_session.total_pnl = session.total_pnl
                    db_trading_session.trades_count = session.trades_count
                    db_session.add(db_trading_session)
                    db_session.commit()
        except Exception as e:
            print(f"[HMM-SVR Bot] DB error: {e}")
        
        del simulated_sessions[session_id]
        print(f"[HMM-SVR Bot] Session expired")


def stop_simulated_trading(session_id: str, close_positions: bool = False) -> dict:
    """Stop trading bot session"""
    if session_id not in simulated_sessions:
        return {'error': 'Session not found'}
    
    session = simulated_sessions[session_id]
    session.stop(close_positions=close_positions)
    
    # Update database
    try:
        with Session(engine) as db_session:
            stmt = select(TradingSession).where(TradingSession.session_id == session_id)
            db_trading_session = db_session.exec(stmt).first()
            if db_trading_session:
                db_trading_session.is_running = False
                db_trading_session.end_time = datetime.now()
                db_trading_session.total_pnl = session.total_pnl
                db_trading_session.trades_count = session.trades_count
                db_session.add(db_trading_session)
                db_session.commit()
    except Exception as e:
        print(f"[HMM-SVR Bot] DB error: {e}")
    
    del simulated_sessions[session_id]
    
    return {
        'session_id': session_id,
        'message': 'Bot stopped',
        'total_pnl': session.total_pnl,
        'trades_count': session.trades_count
    }


def get_simulated_session_status(session_id: str) -> dict:
    """Get bot session status"""
    if session_id not in simulated_sessions:
        return {'error': 'Session not found'}
    
    return simulated_sessions[session_id].get_status()
