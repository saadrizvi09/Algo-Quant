"""
Live Trading with Simulated Exchange
Runs trading strategies using internal database wallet instead of real exchange
"""
import time
import threading
from datetime import datetime, timedelta
from typing import Optional
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
import simulated_exchange
from models import TradingSession, Trade
from sqlmodel import Session, select
from database import engine
import uuid
from strategy_handlers import create_strategy_handler

# Active simulated trading sessions
simulated_sessions = {}


class SimulatedTradingSession:
    """Manages a live trading session using simulated exchange"""
    
    def __init__(self, session_id: str, user_email: str, strategy: str, 
                 symbol: str, trade_amount: float, duration_minutes: int,
                 **strategy_params):
        self.session_id = session_id
        self.user_email = user_email
        self.strategy = strategy
        self.symbol = symbol  # e.g., "BTCUSDT"
        self.trade_amount = trade_amount
        self.duration_minutes = duration_minutes
        self.strategy_params = strategy_params
        
        # Extract base and quote from symbol
        # For Pairs Strategy, we'll use ETH as the traded asset
        if strategy.lower() == "pairs" or strategy == "Pairs Strategy":
            self.base_asset = "ETH"
            self.quote_asset = "USDT"
        else:
            # Parse trading pair correctly (e.g., BTCUSDT -> BTC, USDT)
            if symbol.endswith("USDT"):
                self.base_asset = symbol[:-4]  # Remove "USDT" suffix
                self.quote_asset = "USDT"
            elif symbol.endswith("BTC"):
                self.base_asset = symbol[:-3]  # Remove "BTC" suffix
                self.quote_asset = "BTC"
            else:
                # Default fallback
                self.base_asset = symbol
                self.quote_asset = "USDT"
        
        # Session state
        self.is_running = True
        self.start_time = datetime.now()
        self.end_time = self.start_time + timedelta(minutes=duration_minutes)
        self.total_pnl = 0.0
        self.trades_count = 0
        self.position = None  # None, 'LONG', or 'SHORT'
        self.entry_price = None
        
        print(f"[SimTrading] Parsed symbol: {symbol} -> base={self.base_asset}, quote={self.quote_asset}")
        
        # Initialize strategy handler with symbol for pre-loading data
        try:
            # Pass base_asset as symbol for HMM strategy to pre-load correct data
            handler_params = {**strategy_params, 'symbol': self.base_asset}
            self.handler = create_strategy_handler(strategy, **handler_params)
            print(f"[SimTrading] ✅ Strategy handler initialized: {strategy}")
        except Exception as e:
            print(f"[SimTrading] ❌ Failed to initialize strategy handler: {e}")
            raise
        
        # Scheduler for 30-second intervals (more suitable for production)
        self.scheduler = BackgroundScheduler()
        self.scheduler.add_job(
            func=self._trading_loop,
            trigger=IntervalTrigger(seconds=30),  # 30 seconds instead of 10
            id=f"simulated_{session_id}",
            name=f"Simulated {strategy} - {symbol}",
            replace_existing=True
        )
        
        print(f"[SimTrading] Session {session_id} created: {strategy} on {symbol}")
        print(f"  Duration: {duration_minutes} min | Trade Amount: {trade_amount} {self.quote_asset}")
    
    def start(self):
        """Start the trading session"""
        self.scheduler.start()
        print(f"[SimTrading] ✅ Session {self.session_id} started (10s intervals)")
    
    def stop(self, close_positions: bool = False):
        """Stop the trading session
        
        Args:
            close_positions: If True, close any open positions. 
                           If False (default), leave positions open.
        """
        self.is_running = False
        self.scheduler.shutdown(wait=False)
        
        # Only close positions if explicitly requested
        if close_positions and self.position:
            self._close_position()
        
        print(f"[SimTrading] ⏹️  Session {self.session_id} stopped")
        print(f"  Total Trades: {self.trades_count} | Total P&L: {self.total_pnl:.2f} {self.quote_asset}")
        if self.position:
            print(f"  ⚠️  Position '{self.position}' left open (as requested)")
    
    def _trading_loop(self):
        """Main trading loop - executes every 10 seconds"""
        try:
            # Check if session was stopped
            if not self.is_running:
                print(f"[SimTrading] Session {self.session_id} stopped, exiting loop")
                return
            
            # Check if session should end
            if datetime.now() >= self.end_time:
                print(f"[SimTrading] Session {self.session_id} duration expired")
                # Trigger proper cleanup through the stop function
                _cleanup_expired_session(self.session_id)
                return
            
            # Special handling for Pairs Trading strategy
            if self.strategy.lower() == "pairs" or self.strategy == "Pairs Strategy":
                # Fetch both ETH and BTC prices
                eth_price = simulated_exchange.get_current_price("ETH", "USDT")
                btc_price = simulated_exchange.get_current_price("BTC", "USDT")
                
                if eth_price is None or btc_price is None:
                    print(f"[SimTrading] ❌ Could not fetch ETH/BTC prices")
                    return
                
                # Update the pairs handler with both prices
                self.handler.update_ratio(eth_price, btc_price)
                
                # Get signal from handler (no price parameter for pairs)
                signal = self.handler.get_signal()
                
                # For pairs trading, we trade ETH based on the ETH/BTC ratio
                price = eth_price  # Use ETH price for position sizing
                
                # Detailed logging
                elapsed = (datetime.now() - self.start_time).total_seconds() / 60
                z_score = self.handler.get_current_zscore()
                ratio = eth_price / btc_price
                print(f"[SimTrading] 🔄 Loop #{self.trades_count} | {elapsed:.1f}min elapsed")
                print(f"  ETH: ${eth_price:.2f} | BTC: ${btc_price:.2f} | Ratio: {ratio:.6f}")
                print(f"  Z-Score: {z_score:.2f if z_score else 'N/A'} | Signal: '{signal}' | Position: '{self.position or 'NONE'}'")
            else:
                # Standard single-asset trading (HMM, etc.)
                price = simulated_exchange.get_current_price(self.base_asset, self.quote_asset)
                if price is None:
                    print(f"[SimTrading] ❌ Could not fetch price for {self.symbol}")
                    return
                
                # Get signal from strategy handler
                signal = self.handler.get_signal(price)
                
                # Detailed logging for debugging
                elapsed = (datetime.now() - self.start_time).total_seconds() / 60
                print(f"[SimTrading] 🔄 Loop #{self.trades_count} | {elapsed:.1f}min elapsed")
                print(f"  Price: {price:.2f} | Signal: '{signal}' | Position: '{self.position or 'NONE'}'")
            
            # Execute trades based on signal (same logic for all strategies)
            if signal == "BUY" and self.position != "LONG":
                print(f"  ➡️  Action: Opening LONG position")
                self._open_long_position(price)
            elif signal == "SELL" and self.position is not None:
                # Close any position on SELL signal
                print(f"  ➡️  Action: Closing position (SELL signal)")
                self._close_position(price)
            elif signal == "HOLD":
                print(f"  ➡️  Action: HOLD (no trade)")
            
        except Exception as e:
            print(f"[SimTrading] ❌ FATAL ERROR in trading loop: {e}")
            import traceback
            traceback.print_exc()
    
    def _get_strategy_signal(self, current_price: float) -> str:
        """
        Generate trading signal based on strategy
        Delegates to strategy handler
        
        Returns:
            "BUY", "SELL", or "HOLD"
        """
        return self.handler.get_signal(current_price)
    
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
            print(f"[SimTrading] 📈 LONG opened: {quantity:.8f} {self.base_asset} @ {price:.2f}")
        else:
            print(f"[SimTrading] ❌ Failed to open LONG position")
    
    def _open_short_position(self, price: float):
        """Open a SHORT position (SELL)"""
        # Check if we have the asset to sell
        balance = simulated_exchange.get_balance(self.base_asset, self.user_email)
        quantity = min(balance, self.trade_amount / price)
        
        if quantity < 0.00001:
            print(f"[SimTrading] Cannot SHORT: No {self.base_asset} to sell")
            return
        
        success, trade_info = simulated_exchange.execute_sell(
            symbol=self.base_asset,
            quote_symbol=self.quote_asset,
            amount_to_sell=quantity,
            user_email=self.user_email
        )
        
        if success:
            self.position = "SHORT"
            self.entry_price = price
            self._save_trade_to_db(trade_info)
            print(f"[SimTrading] 📉 SHORT opened: {quantity:.8f} {self.base_asset} @ {price:.2f}")
        else:
            print(f"[SimTrading] ❌ Failed to open SHORT position")
    
    def _close_position(self, current_price: float = None):
        """Close current position"""
        if not self.position:
            return
        
        if current_price is None:
            current_price = simulated_exchange.get_current_price(self.base_asset, self.quote_asset)
            if current_price is None:
                return
        
        if self.position == "LONG":
            # Close LONG by selling
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
                    print(f"[SimTrading] ✅ LONG closed | P&L: {pnl:.2f} {self.quote_asset}")
                else:
                    print(f"[SimTrading] ❌ Failed to close LONG position")
        
        elif self.position == "SHORT":
            # Close SHORT by buying back
            quantity = self.trade_amount / current_price
            success, trade_info = simulated_exchange.execute_buy(
                symbol=self.base_asset,
                quote_symbol=self.quote_asset,
                amount_to_buy=quantity,
                user_email=self.user_email
            )
            if success:
                pnl = (self.entry_price - current_price) * quantity
                self.total_pnl += pnl
                self._save_trade_to_db(trade_info, pnl=pnl)
                print(f"[SimTrading] ✅ SHORT closed | P&L: {pnl:.2f} {self.quote_asset}")
            else:
                print(f"[SimTrading] ❌ Failed to close SHORT position")
        
        self.position = None
        self.entry_price = None
    
    def _save_trade_to_db(self, trade_info: dict, pnl: Optional[float] = None):
        """Save trade to database and increment trade counter"""
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


def start_simulated_trading(user_email: str, strategy: str, symbol: str,
                           trade_amount: float, duration_minutes: int,
                           **strategy_params) -> dict:
    """
    Start a simulated trading session using internal database wallet
    
    Args:
        user_email: User identifier
        strategy: Strategy name
        symbol: Trading pair (e.g., "BTCUSDT")
        trade_amount: Amount per trade in quote currency
        duration_minutes: How long to run
        **strategy_params: Additional strategy parameters
    
    Returns:
        Session info dictionary
    """
    session_id = str(uuid.uuid4())
    
    # Create and start session
    session = SimulatedTradingSession(
        session_id=session_id,
        user_email=user_email,
        strategy=strategy,
        symbol=symbol,
        trade_amount=trade_amount,
        duration_minutes=duration_minutes,
        **strategy_params
    )
    
    session.start()
    simulated_sessions[session_id] = session
    print(f"[SimTrading] ✅ Session {session_id} added to active sessions")
    print(f"[SimTrading] Active sessions count: {len(simulated_sessions)}")
    
    # Save to database
    try:
        with Session(engine) as db_session:
            db_trading_session = TradingSession(
                session_id=session_id,
                user_email=user_email,
                strategy=strategy,
                symbol=symbol,
                trade_amount=trade_amount,
                duration_minutes=duration_minutes,
                start_time=datetime.now(),
                is_running=True
            )
            db_session.add(db_trading_session)
            db_session.commit()
    except Exception as e:
        print(f"[SimTrading] Error saving session to DB: {e}")
    
    return {
        'session_id': session_id,
        'message': f'Simulated trading session started for {symbol}',
        'status': session.get_status()
    }


def _cleanup_expired_session(session_id: str):
    """Internal helper to clean up expired sessions (keeps positions open)"""
    if session_id in simulated_sessions:
        session = simulated_sessions[session_id]
        # Don't close positions when session expires naturally
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
            print(f"[SimTrading] Error updating expired session in DB: {e}")
        
        # Remove from active sessions
        del simulated_sessions[session_id]
        print(f"[SimTrading] Session {session_id} expired and cleaned up (positions kept open)")


def stop_simulated_trading(session_id: str, close_positions: bool = False) -> dict:
    """Stop a simulated trading session
    
    Args:
        session_id: The session to stop
        close_positions: If True, close any open positions before stopping.
                        If False (default), leave positions open.
    """
    print(f"[SimTrading] Stop request for session: {session_id}")
    print(f"[SimTrading] Active sessions: {list(simulated_sessions.keys())}")
    print(f"[SimTrading] Session in dict: {session_id in simulated_sessions}")
    
    if session_id not in simulated_sessions:
        print(f"[SimTrading] ❌ Session {session_id} not found in active sessions")
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
        print(f"[SimTrading] Error updating session in DB: {e}")
    
    del simulated_sessions[session_id]
    
    return {
        'session_id': session_id,
        'message': 'Session stopped',
        'total_pnl': session.total_pnl,
        'trades_count': session.trades_count,
        'positions_closed': close_positions
    }


def get_simulated_session_status(session_id: str) -> dict:
    """Get status of a simulated trading session"""
    if session_id not in simulated_sessions:
        return {'error': 'Session not found'}
    
    return simulated_sessions[session_id].get_status()
