# models.py
from typing import Optional
from datetime import datetime
from sqlmodel import Field, SQLModel

class User(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    email: str = Field(index=True, unique=True) 
    name: Optional[str] = None
    hashed_password: str


class TradingSession(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    session_id: str = Field(index=True, unique=True)
    user_email: str = Field(index=True)
    strategy: str
    symbol: str
    trade_amount: float
    duration_minutes: int
    duration_unit: str = "minutes"  # "minutes" or "days"
    start_time: datetime = Field(default_factory=datetime.now)
    end_time: Optional[datetime] = None
    is_running: bool = True
    total_pnl: float = 0.0
    trades_count: int = 0


class Trade(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    session_id: str = Field(index=True)
    user_email: str = Field(index=True)
    symbol: str
    side: str  # BUY or SELL
    price: float
    quantity: float
    total: float
    pnl: Optional[float] = None
    order_id: Optional[str] = None
    executed_at: datetime = Field(default_factory=datetime.now)


class PortfolioAsset(SQLModel, table=True):
    """Internal simulated wallet for paper trading"""
    symbol: str = Field(primary_key=True)  # e.g., 'USDT', 'BTC', 'ETH'
    user_email: str = Field(primary_key=True, index=True)  # Support multi-user portfolios
    balance: float = Field(default=0.0)
    avg_cost_basis: float = Field(default=0.0)  # Average buy price per unit
    total_invested: float = Field(default=0.0)  # Total USDT invested in this asset