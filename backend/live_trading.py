"""
Live Trading Module - DEPRECATED
All trading functionality has been moved to simulated_trading.py
This file contains minimal stubs for backwards compatibility with main.py imports.
"""
from typing import List
from datetime import datetime
from sqlmodel import Session, select
from database import engine
from models import TradingSession, Trade


def get_account_balance():
    """DEPRECATED: Binance API removed. Use simulated_exchange instead."""
    return {"error": "Live trading with Binance API has been removed. Use /api/simulated endpoints."}


def get_portfolio_value():
    """DEPRECATED: Binance API removed. Use simulated_exchange instead."""
    return {"error": "Live trading with Binance API has been removed. Use /api/simulated endpoints."}


def get_recent_trades(symbol: str = None, limit: int = 20):
    """DEPRECATED: Binance API removed. Use get_recent_trades_from_db instead."""
    return []


def get_recent_trades_from_db(user_email: str, limit: int = 20):
    """Get recent trades from database for a user"""
    try:
        with Session(engine) as session:
            statement = (
                select(Trade)
                .where(Trade.user_email == user_email)
                .order_by(Trade.executed_at.desc())
                .limit(limit)
            )
            trades = session.exec(statement).all()
            
            return [
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
    except Exception as e:
        print(f"Error fetching trades: {e}")
        return []


def get_current_price(symbol: str):
    """DEPRECATED: Binance API removed. Use simulated_exchange instead."""
    return None


def start_live_trading(user_email: str, strategy: str, symbol: str, 
                       trade_amount: float, duration_minutes: int,
                       duration_unit: str = "minutes",
                       short_window: int = 12, long_window: int = 26,
                       interval: str = '5m') -> dict:
    """DEPRECATED: Use /api/simulated/start endpoint instead"""
    return {"error": "Live trading has been removed. Use /api/simulated/start endpoint instead."}


def stop_live_trading(session_id: str) -> dict:
    """DEPRECATED: Use /api/simulated/stop endpoint instead"""
    return {"error": "Live trading has been removed. Use /api/simulated/stop endpoint instead."}


def get_session_status(session_id: str) -> dict:
    """DEPRECATED: Use /api/simulated/sessions endpoint instead"""
    return {"error": "Live trading has been removed. Use /api/simulated/sessions endpoint instead."}


def get_user_sessions(user_email: str) -> List[dict]:
    """Get all sessions for a user from database"""
    try:
        with Session(engine) as session:
            statement = (
                select(TradingSession)
                .where(TradingSession.user_email == user_email)
                .order_by(TradingSession.start_time.desc())
            )
            sessions = session.exec(statement).all()
            
            return [
                {
                    "session_id": s.session_id,
                    "strategy": s.strategy,
                    "symbol": s.symbol,
                    "trade_amount": s.trade_amount,
                    "is_running": s.is_running,
                    "trades_count": s.trades_count,
                    "pnl": s.total_pnl,
                    "start_time": s.start_time.isoformat(),
                    "end_time": s.end_time.isoformat() if s.end_time else None
                }
                for s in sessions
            ]
    except Exception as e:
        print(f"Error fetching sessions: {e}")
        return []


# Available strategies (kept for backwards compatibility)
AVAILABLE_STRATEGIES = [
    {
        "id": "hmm_svr",
        "name": "HMM-SVR Long-Term Bot",
        "description": "Uses pre-trained HMM-SVR models for regime detection and volatility prediction. Checks every 3 hours with dynamic position sizing (0x-3x leverage based on market regime). Uses simulated exchange (database-only).",
        "risk_level": "Medium",
        "requires_symbol": True,
        "requires_model": True,
        "trade_interval": "3 hours"
    }
]
