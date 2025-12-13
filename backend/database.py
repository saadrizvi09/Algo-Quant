# database.py
from sqlmodel import SQLModel, create_engine, Session, select
from dotenv import load_dotenv 
import os

load_dotenv() 

database_url = os.environ.get("DATABASE_URL")

engine = create_engine(
    database_url, 
    echo=True,
    pool_pre_ping=True,
    pool_recycle=300,
    pool_size=5,
    max_overflow=10
)

def create_db_and_tables():
    SQLModel.metadata.create_all(engine)


def initialize_portfolio_if_empty(user_email: str = "default_user"):
    """
    Initialize portfolio with 10,000 USDT only on first run.
    Persistent across restarts - won't reset if portfolio already exists.
    """
    from models import PortfolioAsset
    
    with Session(engine) as session:
        # Check if this user has any portfolio assets
        statement = select(PortfolioAsset).where(PortfolioAsset.user_email == user_email)
        existing_assets = session.exec(statement).all()
        
        if not existing_assets:
            # First run - initialize with starting capital
            print(f"[Portfolio] Initializing new portfolio for {user_email} with 10,000 USDT")
            usdt_asset = PortfolioAsset(
                symbol="USDT",
                balance=10000.0,
                user_email=user_email
            )
            session.add(usdt_asset)
            session.commit()
            print("[Portfolio] ✅ Starting capital deposited: 10,000 USDT")
        else:
            total_assets = len(existing_assets)
            print(f"[Portfolio] Loading existing portfolio for {user_email} ({total_assets} assets)")
            for asset in existing_assets:
                print(f"  - {asset.symbol}: {asset.balance:.8f}")