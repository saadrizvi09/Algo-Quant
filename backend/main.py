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

# Import model manager for HMM-SVR models
from model_manager import (
    load_all_models,
    train_and_save_model,
    load_model,
    is_model_trained,
    get_model_info,
    get_cached_models
)

# --- 1. LIFESPAN (Create Tables on Startup) ---
@asynccontextmanager
async def lifespan(app: FastAPI):
    create_db_and_tables()
    # Load all pre-trained HMM-SVR models from disk into memory
    print("\n🚀 Starting AlgoQuant API...")
    loaded_models = load_all_models()
    if loaded_models:
        print(f"✅ Loaded {len(loaded_models)} HMM-SVR models: {list(loaded_models.keys())}")
    else:
        print("ℹ️  No pre-trained models found. Train models using /api/models/train/{symbol}")
    yield

app = FastAPI(lifespan=lifespan)

# --- CONFIGURATION ---
import os
SECRET_KEY = os.getenv("SECRET_KEY", "algoquant_super_secret_key")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 43200  # 30 days (30 * 24 * 60)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# --- CORS ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "https://algo-quant-pi.vercel.app"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Health Check Endpoint ---
@app.get("/")
async def root():
    return {"status": "healthy", "message": "AlgoQuant API is running"}

@app.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.utcnow().isoformat()}

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
    strategy: str = "hmm_svr"
    # Strategy-specific parameters
    short_window: int = 12
    long_window: int = 26
    n_states: int = 3

class Token(BaseModel):
    access_token: str
    token_type: str

class SimulatedTradingRequest(BaseModel):
    symbol: str
    trade_amount: float
    duration: int
    duration_unit: str = "minutes"  # "minutes" or "days"

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
        "strategies": []
    }


# --- MODEL MANAGEMENT ROUTES (HMM-SVR) ---

@app.post("/api/models/train/{symbol}")
def train_model(symbol: str, current_user: str = Depends(get_current_user)):
    """
    Train and save HMM-SVR model for a specific symbol.
    This trains on 4 years of historical data and saves the model to disk.
    The model will be automatically loaded on next startup.
    
    Example: POST /api/models/train/BTCUSDT
    """
    print(f"[API] User {current_user} requested model training for {symbol}")
    
    # Validate symbol format
    symbol = symbol.upper()
    if not symbol.endswith('USDT'):
        raise HTTPException(
            status_code=400, 
            detail="Symbol must end with USDT (e.g., BTCUSDT, ETHUSDT)"
        )
    
    result = train_and_save_model(symbol, n_states=3)
    
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    
    return {
        "success": True,
        "message": f"Model trained and saved for {symbol}",
        "details": result
    }


@app.get("/api/models/status/{symbol}")
def get_model_status(symbol: str, current_user: str = Depends(get_current_user)):
    """
    Check if a model exists and get its metadata for a symbol.
    """
    symbol = symbol.upper()
    
    if not is_model_trained(symbol):
        return {
            "trained": False,
            "symbol": symbol,
            "message": f"No model found for {symbol}. Train it using POST /api/models/train/{symbol}"
        }
    
    info = get_model_info(symbol)
    return {
        "trained": True,
        "symbol": symbol,
        "info": info
    }


@app.get("/api/models")
def list_models(current_user: str = Depends(get_current_user)):
    """
    List all available trained models and their status.
    """
    cached = get_cached_models()
    
    # Also check for models on disk that aren't loaded yet
    import os
    from model_manager import MODEL_DIR
    
    disk_models = []
    if os.path.exists(MODEL_DIR):
        for filename in os.listdir(MODEL_DIR):
            if filename.endswith('_hmm_svr.pkl'):
                symbol = filename.replace('_hmm_svr.pkl', '').upper()
                disk_models.append(symbol)
    
    return {
        "loaded_models": cached,
        "available_on_disk": disk_models,
        "total_count": len(set(list(cached.keys()) + disk_models))
    }


@app.post("/api/models/reload")
def reload_models(current_user: str = Depends(get_current_user)):
    """
    Reload all models from disk into memory.
    Useful if models were trained externally or after a restart.
    """
    result = load_all_models()
    return {
        "success": True,
        "loaded_models": list(result.keys()),
        "count": sum(result.values())
    }


# --- SIMULATED TRADING ROUTES ---

@app.get("/api/simulated/trades")
def get_simulated_trades(
    limit: int = 50,
    current_user: str = Depends(get_current_user)
):
    """Get recent simulated trades for the current user"""
    from simulated_endpoints import get_simulated_trades_endpoint
    return get_simulated_trades_endpoint(limit, current_user)


@app.get("/api/simulated/sessions")
def get_simulated_sessions(current_user: str = Depends(get_current_user)):
    """Get all simulated trading sessions for the current user"""
    from simulated_endpoints import get_simulated_sessions_endpoint
    return get_simulated_sessions_endpoint(current_user)


@app.get("/api/simulated/portfolio")
def get_simulated_portfolio(current_user: str = Depends(get_current_user)):
    """Get the internal simulated portfolio (database-driven wallet)"""
    from simulated_exchange import get_portfolio_summary
    from database import initialize_portfolio_if_empty
    
    # Initialize portfolio with 10k USDT if this is a new user
    initialize_portfolio_if_empty(user_email=current_user)
    
    portfolio = get_portfolio_summary(user_email=current_user)
    return portfolio


@app.post("/api/simulated/start")
def start_simulated_session(req: SimulatedTradingRequest, current_user: str = Depends(get_current_user)):
    """Start HMM-SVR trading bot session"""
    from simulated_trading import start_simulated_trading
    from database import initialize_portfolio_if_empty
    
    # Initialize portfolio with 10k USDT if this is a new user
    initialize_portfolio_if_empty(user_email=current_user)
    
    duration_minutes = req.duration
    if req.duration_unit == "days":
        duration_minutes = req.duration * 24 * 60
    
    result = start_simulated_trading(
        user_email=current_user,
        symbol=req.symbol,
        trade_amount=req.trade_amount,
        duration_minutes=duration_minutes
    )
    
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return result


@app.post("/api/simulated/stop/{session_id}")
def stop_simulated_session(session_id: str, current_user: str = Depends(get_current_user)):
    """Stop trading bot session"""
    from simulated_trading import stop_simulated_trading
    
    result = stop_simulated_trading(session_id)
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    return result


@app.get("/api/simulated/session/{session_id}")
def get_simulated_session(session_id: str, current_user: str = Depends(get_current_user)):
    """Get bot session status"""
    from simulated_trading import get_simulated_session_status
    
    status = get_simulated_session_status(session_id)
    if "error" in status:
        raise HTTPException(status_code=404, detail=status["error"])
    return status


# --- MANUAL TRADING ROUTES (Market Page) ---

class ManualBuyRequest(BaseModel):
    symbol: str  # e.g., 'BTC', 'ETH'
    usdt_amount: float  # Amount in USDT to spend

class ManualSellRequest(BaseModel):
    symbol: str  # e.g., 'BTC', 'ETH'
    quantity: float  # Amount of asset to sell

class ManualSellPercentRequest(BaseModel):
    symbol: str  # e.g., 'BTC', 'ETH'
    percentage: float  # Percentage of holdings to sell (0-100)


@app.post("/api/market/buy")
def manual_buy(req: ManualBuyRequest, current_user: str = Depends(get_current_user)):
    """
    Execute a manual buy order from the Market page.
    This is independent from automated trading bot strategies.
    Updates portfolio and creates trade log entry.
    """
    from manual_trading import execute_manual_buy
    from database import initialize_portfolio_if_empty
    
    # Ensure user has portfolio initialized
    initialize_portfolio_if_empty(user_email=current_user)
    
    # Validate input
    if req.usdt_amount <= 0:
        raise HTTPException(status_code=400, detail="Amount must be positive")
    
    if req.usdt_amount < 1:
        raise HTTPException(status_code=400, detail="Minimum buy amount is 1 USDT")
    
    success, trade_info, error = execute_manual_buy(
        symbol=req.symbol,
        usdt_amount=req.usdt_amount,
        user_email=current_user
    )
    
    if not success:
        raise HTTPException(status_code=400, detail=error)
    
    return {
        "success": True,
        "message": f"Successfully bought {trade_info['quantity']:.8f} {req.symbol}",
        "trade": trade_info
    }


@app.post("/api/market/sell")
def manual_sell(req: ManualSellRequest, current_user: str = Depends(get_current_user)):
    """
    Execute a manual sell order from the Market page.
    This is independent from automated trading bot strategies.
    Updates portfolio and creates trade log entry.
    """
    from manual_trading import execute_manual_sell
    from database import initialize_portfolio_if_empty
    
    # Ensure user has portfolio initialized
    initialize_portfolio_if_empty(user_email=current_user)
    
    # Validate input
    if req.quantity <= 0:
        raise HTTPException(status_code=400, detail="Quantity must be positive")
    
    success, trade_info, error = execute_manual_sell(
        symbol=req.symbol,
        quantity=req.quantity,
        user_email=current_user
    )
    
    if not success:
        raise HTTPException(status_code=400, detail=error)
    
    return {
        "success": True,
        "message": f"Successfully sold {trade_info['quantity']:.8f} {req.symbol}",
        "trade": trade_info
    }


@app.post("/api/market/sell-percent")
def manual_sell_percent(req: ManualSellPercentRequest, current_user: str = Depends(get_current_user)):
    """
    Sell a percentage of holdings for a specific asset.
    Useful for quick "Sell 25%", "Sell 50%", "Sell All" actions.
    """
    from manual_trading import execute_manual_sell, get_user_balance
    from database import initialize_portfolio_if_empty
    
    # Ensure user has portfolio initialized
    initialize_portfolio_if_empty(user_email=current_user)
    
    # Validate percentage
    if req.percentage <= 0 or req.percentage > 100:
        raise HTTPException(status_code=400, detail="Percentage must be between 0 and 100")
    
    # Get current balance
    balance = get_user_balance(req.symbol.upper(), current_user)
    if balance <= 0:
        raise HTTPException(status_code=400, detail=f"No {req.symbol} holdings to sell")
    
    # Calculate quantity to sell
    quantity_to_sell = balance * (req.percentage / 100)
    
    success, trade_info, error = execute_manual_sell(
        symbol=req.symbol,
        quantity=quantity_to_sell,
        user_email=current_user
    )
    
    if not success:
        raise HTTPException(status_code=400, detail=error)
    
    return {
        "success": True,
        "message": f"Successfully sold {req.percentage}% ({trade_info['quantity']:.8f}) {req.symbol}",
        "trade": trade_info
    }


@app.get("/api/market/trades")
def get_manual_trades(limit: int = 50, current_user: str = Depends(get_current_user)):
    """Get manual trade history for the current user"""
    from manual_trading import get_manual_trade_history
    
    trades = get_manual_trade_history(current_user, limit)
    return {"trades": trades}


@app.get("/api/market/prices")
def get_market_prices(current_user: str = Depends(get_current_user)):
    """
    Get current prices for all supported assets.
    Useful for initial page load before WebSocket connects.
    """
    from manual_trading import get_prices_for_assets
    
    prices = get_prices_for_assets()
    return {"prices": prices}


@app.get("/api/market/assets")
def get_supported_assets(current_user: str = Depends(get_current_user)):
    """Get list of supported assets for manual trading"""
    from manual_trading import SUPPORTED_ASSETS
    
    assets = [
        {"symbol": "BTC", "name": "Bitcoin", "logo": "₿", "color": "#F7931A"},
        {"symbol": "ETH", "name": "Ethereum", "logo": "Ξ", "color": "#627EEA"},
        {"symbol": "SOL", "name": "Solana", "logo": "◎", "color": "#14F195"},
        {"symbol": "LINK", "name": "Chainlink", "logo": "⬡", "color": "#2A5ADA"},
        {"symbol": "DOGE", "name": "Dogecoin", "logo": "Ð", "color": "#C2A633"},
        {"symbol": "BNB", "name": "BNB", "logo": "⬡", "color": "#F3BA2F"},
    ]
    
    return {"assets": [a for a in assets if a["symbol"] in SUPPORTED_ASSETS]}


@app.get("/api/market/cost-basis/{symbol}")
def get_cost_basis(symbol: str, current_user: str = Depends(get_current_user)):
    """
    Get the average cost basis and investment info for a specific asset.
    Used to show estimated PnL before selling.
    """
    from manual_trading import get_asset_cost_basis, get_current_price_from_binance, TRADING_FEE
    
    cost_info = get_asset_cost_basis(symbol.upper(), current_user)
    
    # Get current price to calculate unrealized PnL
    current_price = get_current_price_from_binance(symbol.upper(), "USDT")
    
    if current_price and cost_info['balance'] > 0:
        current_value = current_price * cost_info['balance']
        fee_estimate = current_value * TRADING_FEE
        net_value = current_value - fee_estimate
        unrealized_pnl = net_value - cost_info['total_invested']
        unrealized_pnl_percent = ((net_value / cost_info['total_invested']) - 1) * 100 if cost_info['total_invested'] > 0 else 0.0
    else:
        current_value = 0.0
        unrealized_pnl = 0.0
        unrealized_pnl_percent = 0.0
    
    return {
        "symbol": symbol.upper(),
        "balance": cost_info['balance'],
        "avg_cost_basis": cost_info['avg_cost_basis'],
        "total_invested": cost_info['total_invested'],
        "current_price": current_price,
        "current_value": current_value,
        "unrealized_pnl": unrealized_pnl,
        "unrealized_pnl_percent": unrealized_pnl_percent
    }