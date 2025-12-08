# main.py
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

# --- 1. LIFESPAN (Create Tables on Startup) ---
@asynccontextmanager
async def lifespan(app: FastAPI):
    create_db_and_tables()
    yield

app = FastAPI(lifespan=lifespan)

# --- CONFIGURATION ---
SECRET_KEY = "algoquant_super_secret_key" # Use os.getenv("SECRET_KEY")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# --- CORS ---
app.add_middleware(
    CORSMiddleware,
    # Allow both localhost AND 127.0.0.1 to avoid confusion
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

class Token(BaseModel):
    access_token: str
    token_type: str

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
    expire = datetime.utcnow() + (expires_delta if expires_delta else timedelta(minutes=15))
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

@app.post("/api/login", response_model=Token)
def login(user_data: UserLogin, session: Session = Depends(get_session)):
    # 1. Select User from DB
    statement = select(User).where(User.email == user_data.email)
    user = session.exec(statement).first()
    
    # 2. Verify
    if not user or not verify_password(user_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
        )
    
    # 3. Issue Token
    access_token = create_access_token(data={"sub": user.email})
    return {"access_token": access_token, "token_type": "bearer"}

@app.post("/api/backtest")
def run_backtest(
    req: BacktestRequest, 
    current_user: str = Depends(get_current_user)
):
    print(f"User {current_user} is running backtest...")
    
    # Run Strategy
    result = train_models_and_backtest(
        req.ticker, req.start_date, req.end_date, 
        short_window=12, long_window=26, n_states=3
    )
    return result