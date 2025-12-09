from fastapi import FastAPI, HTTPException, Depends, status, Header
from contextlib import asynccontextmanager
from typing import Optional, Annotated
from datetime import datetime, timedelta

# SQLModel & Database Imports
from sqlmodel import Session, select
from database import create_db_and_tables, engine
from models import User 

# Security Imports
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from passlib.context import CryptContext
from jose import JWTError, jwt

# Import your strategy logic
from strategy import train_models_and_backtest
from pairs_strategy import simulate_pairs_backtest
from live_trading import (
    get_account_balance,
    get_portfolio_value,
    get_recent_trades,
    get_recent_trades_from_db,
    get_current_price,
    start_live_trading,
    stop_live_trading,
    get_session_status,
    get_user_sessions,
    AVAILABLE_STRATEGIES
) 

# --- 1. LIFESPAN (Create Tables on Startup) ---
@asynccontextmanager
async def lifespan(app: FastAPI):
    create_db_and_tables()
    yield

app = FastAPI(lifespan=lifespan)

# --- CONFIGURATION ---
SECRET_KEY = "algoquant_super_secret_key" # Use os.getenv("SECRET_KEY")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 43200  # 30 days (30 * 24 * 60)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# --- CORS ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Pydantic Models (For Request Body) ---
class UserCreate(BaseModel):
    email: str
    password: str
    name: Optional[str] = None

class UserLogin(BaseModel):
    email: str
    password: str

class BacktestRequest(BaseModel):
    ticker: str
    start_date: str
    end_date: str
    strategy: str = "hmm"  # "hmm" or "pairs"
    # Strategy-specific parameters
    short_window: int = 12  # For HMM strategy
    long_window: int = 26   # For HMM strategy
    n_states: int = 3       # For HMM strategy
    window: int = 30        # For pairs strategy
    threshold: float = 1.0  # For pairs strategy

class Token(BaseModel):
    access_token: str
    token_type: str

class LiveTradingRequest(BaseModel):
    strategy: str
    symbol: str
    trade_amount: float
    duration: int
    duration_unit: str = "minutes"  # "minutes" or "days"
    # Strategy-specific parameters
    short_window: int = 12  # For HMM strategy
    long_window: int = 26   # For HMM strategy
    window: int = 60        # For pairs strategy
    threshold: float = 1.0  # For pairs strategy
    interval: str = '5m'    # Time interval: '1m', '5m', '15m', '1h'

# --- DATABASE DEPENDENCY ---
def get_session():
    with Session(engine) as session:
        yield session

# --- AUTH HELPERS ---
def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now() + expires_delta
    else:
        expire = datetime.now() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

# --- THE GUARD (Protect Routes) ---
async def get_current_user(authorization: str = Header(None)):
    if not authorization:
        raise HTTPException(status_code=401, detail="Missing Token")
    try:
        token = authorization.split(" ")[1]
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise HTTPException(status_code=401, detail="Invalid Token")
        return email
    except (JWTError, IndexError):
        raise HTTPException(status_code=401, detail="Could not validate credentials")

# --- ROUTES ---

@app.post("/api/signup", response_model=Token)
def signup(user_data: UserCreate, session: Session = Depends(get_session)):
    try:
        # 1. Check if user exists in DB
        statement = select(User).where(User.email == user_data.email)
        existing_user = session.exec(statement).first()
        
        if existing_user:
            raise HTTPException(status_code=400, detail="Email already registered")
        
        # 2. Hash Password & Create User Object
        hashed_pwd = get_password_hash(user_data.password)
        new_user = User(
            email=user_data.email, 
            name=user_data.name, 
            hashed_password=hashed_pwd
        )
        
        # 3. Save to DB
        session.add(new_user)
        session.commit()
        session.refresh(new_user)
        
        # 4. Auto-login (Return Token immediately)
        access_token = create_access_token(data={"sub": new_user.email})
        return {"access_token": access_token, "token_type": "bearer"}
    
    except HTTPException:
        raise
    except Exception as e:
        session.rollback()
        print(f"Signup error: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error during signup")

@app.post("/api/login", response_model=Token)
def login(user_data: UserLogin, session: Session = Depends(get_session)):
    try:
        # 1. Validate input
        if not user_data.email or not user_data.password:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email and password are required"
            )
        
        # 2. Select User from DB
        statement = select(User).where(User.email == user_data.email)
        user = session.exec(statement).first()
        
        # 3. Verify
        if not user or not verify_password(user_data.password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password",
            )
        
        # 4. Issue Token (30 days expiration)
        access_token = create_access_token(data={"sub": user.email})
        return {"access_token": access_token, "token_type": "bearer"}
    
    except HTTPException:
        raise
    except Exception as e:
        print(f"Login error: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error during login")

@app.post("/api/backtest")
def run_backtest(
    req: BacktestRequest, 
    current_user: str = Depends(get_current_user)
):
    print(f"User {current_user} is running {req.strategy} backtest...")
    
    if req.strategy == "pairs":
        # Run Pairs Trading Strategy
        result = simulate_pairs_backtest(
            req.start_date, req.end_date,
            initial_capital=10000,
            window=req.window,
            threshold=req.threshold
        )
    else:
        # Run HMM Strategy
        result = train_models_and_backtest(
            req.ticker, req.start_date, req.end_date, 
            short_window=req.short_window,
            long_window=req.long_window,
            n_states=req.n_states
        )
    return result


@app.get("/api/backtest/strategies")
def get_backtest_strategies(current_user: str = Depends(get_current_user)):
    """Get available backtest strategies"""
    return {
        "strategies": [
            {
                "id": "hmm",
                "name": "HMM Regime Filter",
                "description": "Hidden Markov Model that detects market regimes and filters trades during high volatility",
                "requires_ticker": True
            },
            {
                "id": "pairs",
                "name": "Pairs Trading (Test)",
                "description": "ETH/BTC mean reversion using Z-Score. High frequency strategy for testing.",
                "requires_ticker": False
            }
        ]
    }


# --- LIVE TRADING ROUTES ---

@app.get("/api/live/strategies")
def list_strategies(current_user: str = Depends(get_current_user)):
    """Get list of available trading strategies"""
    return {"strategies": AVAILABLE_STRATEGIES}


@app.get("/api/live/portfolio")
def get_portfolio(current_user: str = Depends(get_current_user)):
    """Get current portfolio value and holdings"""
    portfolio = get_portfolio_value()
    if "error" in portfolio:
        raise HTTPException(status_code=500, detail=portfolio["error"])
    return portfolio


@app.get("/api/live/balance")
def get_balance(current_user: str = Depends(get_current_user)):
    """Get account balances"""
    balances = get_account_balance()
    if isinstance(balances, dict) and "error" in balances:
        raise HTTPException(status_code=500, detail=balances["error"])
    return {"balances": balances}


@app.get("/api/live/trades")
def get_trades(symbol: Optional[str] = None, limit: int = 20, 
               current_user: str = Depends(get_current_user)):
    """Get recent trades from database for current user"""
    trades = get_recent_trades_from_db(current_user, limit)
    return {"trades": trades}


@app.get("/api/live/price/{symbol}")
def get_price(symbol: str, current_user: str = Depends(get_current_user)):
    """Get current price for a symbol"""
    price = get_current_price(symbol)
    if price is None:
        raise HTTPException(status_code=404, detail="Symbol not found")
    return {"symbol": symbol, "price": price}


@app.post("/api/live/start")
def start_trading(req: LiveTradingRequest, current_user: str = Depends(get_current_user)):
    """Start a live trading session"""
    # Convert days to minutes if needed
    duration_minutes = req.duration
    if req.duration_unit == "days":
        duration_minutes = req.duration * 24 * 60
    
    result = start_live_trading(
        user_email=current_user,
        strategy=req.strategy,
        symbol=req.symbol,
        trade_amount=req.trade_amount,
        duration_minutes=duration_minutes,
        duration_unit=req.duration_unit,
        short_window=req.short_window,
        long_window=req.long_window,
        window=req.window,
        threshold=req.threshold,
        interval=req.interval
    )
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return result


@app.post("/api/live/stop/{session_id}")
def stop_trading(session_id: str, current_user: str = Depends(get_current_user)):
    """Stop an active trading session"""
    result = stop_live_trading(session_id)
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    return result


@app.get("/api/live/session/{session_id}")
def get_session(session_id: str, current_user: str = Depends(get_current_user)):
    """Get status of a trading session"""
    status = get_session_status(session_id)
    if "error" in status:
        raise HTTPException(status_code=404, detail=status["error"])
    return status


@app.get("/api/live/sessions")
def get_sessions(current_user: str = Depends(get_current_user)):
    """Get all trading sessions for the current user"""
    sessions = get_user_sessions(current_user)
    return {"sessions": sessions}