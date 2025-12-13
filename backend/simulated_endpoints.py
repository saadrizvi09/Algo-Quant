"""
Additional simulated trading endpoints for trades and sessions
"""


def get_simulated_trades_endpoint(limit: int, current_user: str):
    """Get recent simulated trades for the current user"""
    from models import Trade
    from database import engine
    from sqlmodel import Session, select
    
    with Session(engine) as session:
        statement = (
            select(Trade)
            .where(Trade.user_email == current_user)
            .order_by(Trade.executed_at.desc())
            .limit(limit)
        )
        trades = session.exec(statement).all()
        
        trades_list = [
            {
                "symbol": trade.symbol,
                "side": trade.side,
                "price": trade.price,
                "quantity": trade.quantity,
                "total": trade.total,
                "time": trade.executed_at.isoformat()
            }
            for trade in trades
        ]
        
        return {"trades": trades_list}


def get_simulated_sessions_endpoint(current_user: str):
    """Get all simulated trading sessions for the current user"""
    from models import TradingSession
    from database import engine
    from sqlmodel import Session, select
    from datetime import datetime
    from simulated_trading import simulated_sessions
    
    with Session(engine) as session:
        statement = (
            select(TradingSession)
            .where(TradingSession.user_email == current_user)
            .order_by(TradingSession.start_time.desc())
        )
        sessions = session.exec(statement).all()
        
        sessions_list = []
        for s in sessions:
            # Check if session is actually running in memory
            is_actually_running = s.session_id in simulated_sessions
            
            # If DB says running but not in memory, it expired/crashed
            if s.is_running and not is_actually_running:
                # Update DB to reflect reality
                s.is_running = False
                if s.end_time is None:
                    s.end_time = datetime.now()
                session.add(s)
            
            # Calculate elapsed and remaining time
            now = datetime.now()
            elapsed = (now - s.start_time).total_seconds() / 60  # minutes
            
            # Calculate total duration based on duration_unit
            if s.duration_unit == "days":
                total_duration = s.duration_minutes * 24 * 60
            else:
                total_duration = s.duration_minutes
            
            remaining = max(0, total_duration - elapsed)
            
            sessions_list.append({
                "session_id": s.session_id,
                "strategy": s.strategy,
                "symbol": s.symbol,
                "trade_amount": s.trade_amount,
                "is_running": is_actually_running,  # Use real status from memory
                "position": "NONE",  # Default position
                "trades_count": s.trades_count,
                "pnl": s.total_pnl,
                "elapsed_minutes": elapsed,
                "remaining_minutes": remaining
            })
        
        session.commit()  # Commit any DB updates
        
        return {"sessions": sessions_list}
