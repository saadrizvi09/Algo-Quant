"""
Model Manager for HMM-SVR Trading Models
Handles training, saving, loading, and prediction for live trading.
Models are persisted to disk for Hugging Face Spaces cold start handling.
"""
import os
import joblib
import numpy as np
import pandas as pd
import yfinance as yf
from datetime import datetime, timedelta
from typing import Optional, Dict, Tuple, Any
from hmmlearn.hmm import GaussianHMM
from sklearn.svm import SVR
from sklearn.preprocessing import StandardScaler
from binance.client import Client
from dotenv import load_dotenv

load_dotenv()

# Directory for storing trained models
MODEL_DIR = os.path.join(os.path.dirname(__file__), 'models')
os.makedirs(MODEL_DIR, exist_ok=True)

# Global cache for loaded models (survives until Space sleeps)
_model_cache: Dict[str, Dict[str, Any]] = {}


def get_model_path(symbol: str) -> str:
    """Get the file path for a symbol's model."""
    # Normalize symbol (e.g., BTCUSDT -> btcusdt)
    return os.path.join(MODEL_DIR, f'{symbol.lower()}_hmm_svr.pkl')


def is_model_trained(symbol: str) -> bool:
    """Check if a model exists for the given symbol."""
    return os.path.exists(get_model_path(symbol))


def get_model_info(symbol: str) -> Optional[Dict]:
    """Get metadata about a trained model."""
    model_path = get_model_path(symbol)
    if not os.path.exists(model_path):
        return None
    
    try:
        model_data = joblib.load(model_path)
        return {
            'symbol': symbol,
            'trained_at': model_data.get('trained_at', 'Unknown'),
            'n_states': model_data.get('n_states', 3),
            'avg_train_vol': model_data.get('avg_train_vol', 0),
            'train_days': model_data.get('train_days', 0),
        }
    except Exception as e:
        print(f"[ModelManager] Error reading model info for {symbol}: {e}")
        return None


def fetch_training_data_yfinance(ticker: str, years: int = 4) -> Optional[pd.DataFrame]:
    """
    Fetch historical daily data from Yahoo Finance for training.
    Converts Binance symbols (e.g., BTCUSDT) to Yahoo format (BTC-USD).
    """
    # Convert Binance symbol to Yahoo Finance format
    yahoo_ticker = ticker.replace('USDT', '-USD').replace('BUSD', '-USD')
    
    end_date = datetime.now()
    start_date = end_date - timedelta(days=years * 365)
    
    print(f"[ModelManager] Fetching {years} years of data for {yahoo_ticker}...")
    
    try:
        df = yf.download(yahoo_ticker, start=start_date, end=end_date, progress=False, auto_adjust=True)
        
        if df.empty:
            print(f"[ModelManager] No data returned for {yahoo_ticker}")
            return None
        
        # Handle MultiIndex columns from yfinance
        if isinstance(df.columns, pd.MultiIndex):
            if 'Close' in df.columns.get_level_values(0):
                df.columns = df.columns.get_level_values(0)
            else:
                df.columns = df.columns.get_level_values(1)
        
        print(f"[ModelManager] Fetched {len(df)} days of data")
        return df.dropna()
    except Exception as e:
        print(f"[ModelManager] Error fetching data: {e}")
        return None


def fetch_training_data_binance(symbol: str, days: int = 1460) -> Optional[pd.DataFrame]:
    """
    Fetch historical daily data from Binance for training.
    Falls back to this if yfinance fails.
    """
    try:
        client = Client()  # No API keys needed for public data
        
        # Calculate start time
        end_time = datetime.now()
        start_time = end_time - timedelta(days=days)
        
        print(f"[ModelManager] Fetching {days} days of Binance data for {symbol}...")
        
        klines = client.get_historical_klines(
            symbol=symbol,
            interval=Client.KLINE_INTERVAL_1DAY,
            start_str=start_time.strftime('%Y-%m-%d'),
            end_str=end_time.strftime('%Y-%m-%d')
        )
        
        if not klines:
            print(f"[ModelManager] No Binance data returned for {symbol}")
            return None
        
        df = pd.DataFrame(klines, columns=[
            'timestamp', 'Open', 'High', 'Low', 'Close', 'Volume',
            'close_time', 'quote_volume', 'trades', 'taker_buy_base',
            'taker_buy_quote', 'ignore'
        ])
        
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
        df.set_index('timestamp', inplace=True)
        df['Close'] = df['Close'].astype(float)
        df['Open'] = df['Open'].astype(float)
        df['High'] = df['High'].astype(float)
        df['Low'] = df['Low'].astype(float)
        df['Volume'] = df['Volume'].astype(float)
        
        print(f"[ModelManager] Fetched {len(df)} days from Binance")
        return df[['Open', 'High', 'Low', 'Close', 'Volume']].dropna()
    except Exception as e:
        print(f"[ModelManager] Error fetching Binance data: {e}")
        return None


def engineer_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Apply feature engineering as defined in strategy.py.
    """
    df = df.copy()
    
    # Log returns
    df['Log_Returns'] = np.log(df['Close'] / df['Close'].shift(1))
    
    # Rolling volatility (10-day)
    df['Volatility'] = df['Log_Returns'].rolling(window=10).std()
    
    # Downside volatility (std of negative returns only)
    df['Downside_Returns'] = df['Log_Returns'].apply(lambda x: x if x < 0 else 0)
    df['Downside_Vol'] = df['Downside_Returns'].rolling(10).std()
    
    # Target for SVR: next day's volatility
    df['Target_Next_Vol'] = df['Volatility'].shift(-1)
    
    return df.dropna()


def train_hmm_model(train_df: pd.DataFrame, n_states: int = 3) -> Tuple[GaussianHMM, Dict[int, int]]:
    """
    Train HMM on historical data and sort states by volatility.
    State 0 = Lowest Volatility (Safe)
    State N-1 = Highest Volatility (Crash)
    """
    X_train = train_df[['Log_Returns', 'Volatility']].values * 100
    
    model = GaussianHMM(n_components=n_states, covariance_type="full", n_iter=100, random_state=42)
    model.fit(X_train)
    
    # Calculate average volatility per state
    hidden_states = model.predict(X_train)
    state_vol = []
    for i in range(n_states):
        mask = hidden_states == i
        if mask.sum() > 0:
            avg_vol = X_train[mask, 1].mean()
        else:
            avg_vol = 0
        state_vol.append((i, avg_vol))
    
    # Sort states by volatility: State 0 = Lowest, State N-1 = Highest
    state_vol.sort(key=lambda x: x[1])
    mapping = {old: new for new, (old, _) in enumerate(state_vol)}
    
    return model, mapping


def train_svr_model(train_df: pd.DataFrame) -> Tuple[SVR, StandardScaler]:
    """
    Train SVR to predict next day's volatility.
    """
    feature_cols = ['Log_Returns', 'Volatility', 'Downside_Vol', 'Regime']
    target_col = 'Target_Next_Vol'
    
    X = train_df[feature_cols].values
    y = train_df[target_col].values
    
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)
    
    model = SVR(kernel='rbf', C=100, gamma=0.1, epsilon=0.01)
    model.fit(X_scaled, y)
    
    return model, scaler


def train_and_save_model(symbol: str, n_states: int = 3) -> Dict[str, Any]:
    """
    Train HMM-SVR models for a symbol and save to disk.
    Returns training results and metadata.
    """
    print(f"\n{'='*60}")
    print(f"[ModelManager] Training HMM-SVR model for {symbol}")
    print(f"{'='*60}")
    
    # Try Yahoo Finance first, then Binance
    df = fetch_training_data_yfinance(symbol)
    if df is None or len(df) < 250:
        print("[ModelManager] Falling back to Binance data...")
        df = fetch_training_data_binance(symbol)
    
    if df is None or len(df) < 250:
        return {"error": f"Insufficient data for {symbol}. Need at least 250 days, got {len(df) if df is not None else 0}."}
    
    # Engineer features
    df = engineer_features(df)
    
    if len(df) < 200:
        return {"error": f"Insufficient data after feature engineering for {symbol}. Got {len(df)} days."}
    
    print(f"[ModelManager] Training on {len(df)} days of data...")
    
    # Train HMM
    print("[ModelManager] Training HMM model...")
    hmm_model, state_mapping = train_hmm_model(df, n_states=n_states)
    
    # Apply regime labels to training data
    X_train = df[['Log_Returns', 'Volatility']].values * 100
    raw_states = hmm_model.predict(X_train)
    df['Regime'] = [state_mapping[s] for s in raw_states]
    
    # Calculate average training volatility for risk ratio
    avg_train_vol = df['Volatility'].mean()
    
    # Train SVR
    print("[ModelManager] Training SVR model...")
    svr_model, svr_scaler = train_svr_model(df)
    
    # Prepare model data for saving
    model_data = {
        'hmm_model': hmm_model,
        'svr_model': svr_model,
        'svr_scaler': svr_scaler,
        'state_mapping': state_mapping,
        'avg_train_vol': avg_train_vol,
        'n_states': n_states,
        'train_days': len(df),
        'trained_at': datetime.now().isoformat(),
        'symbol': symbol
    }
    
    # Save to disk
    model_path = get_model_path(symbol)
    joblib.dump(model_data, model_path)
    
    # Update cache
    _model_cache[symbol.upper()] = model_data
    
    print(f"[ModelManager] ✅ Model saved to {model_path}")
    print(f"[ModelManager] States: 0=Low Vol (Safe), {n_states-1}=High Vol (Crash)")
    print(f"[ModelManager] Avg training volatility: {avg_train_vol:.6f}")
    
    return {
        "success": True,
        "symbol": symbol,
        "trained_at": model_data['trained_at'],
        "train_days": len(df),
        "avg_train_vol": avg_train_vol,
        "n_states": n_states,
        "model_path": model_path
    }


def load_model(symbol: str) -> Optional[Dict[str, Any]]:
    """
    Load a trained model from disk into memory.
    Returns None if model doesn't exist.
    """
    symbol_upper = symbol.upper()
    
    # Check cache first
    if symbol_upper in _model_cache:
        print(f"[ModelManager] Using cached model for {symbol}")
        return _model_cache[symbol_upper]
    
    # Load from disk
    model_path = get_model_path(symbol)
    if not os.path.exists(model_path):
        print(f"[ModelManager] No model found for {symbol} at {model_path}")
        return None
    
    try:
        print(f"[ModelManager] Loading model from {model_path}...")
        model_data = joblib.load(model_path)
        _model_cache[symbol_upper] = model_data
        print(f"[ModelManager] ✅ Model loaded for {symbol}")
        return model_data
    except Exception as e:
        print(f"[ModelManager] Error loading model: {e}")
        return None


def load_all_models() -> Dict[str, bool]:
    """
    Load all available models from disk into cache.
    Called on application startup.
    """
    print("\n[ModelManager] Loading all models from disk...")
    results = {}
    
    if not os.path.exists(MODEL_DIR):
        print("[ModelManager] No models directory found")
        return results
    
    for filename in os.listdir(MODEL_DIR):
        if filename.endswith('_hmm_svr.pkl'):
            symbol = filename.replace('_hmm_svr.pkl', '').upper()
            model = load_model(symbol)
            results[symbol] = model is not None
    
    print(f"[ModelManager] Loaded {sum(results.values())} models: {list(results.keys())}")
    return results


def predict_regime_and_volatility(
    symbol: str,
    recent_data: pd.DataFrame
) -> Optional[Dict[str, Any]]:
    """
    Use trained model to predict current regime and next volatility.
    
    Args:
        symbol: Trading symbol (e.g., BTCUSDT)
        recent_data: DataFrame with recent price data (needs Close column)
    
    Returns:
        Dict with regime, predicted_vol, risk_ratio, etc.
    """
    model_data = load_model(symbol)
    if model_data is None:
        return {"error": f"No model found for {symbol}. Train it first."}
    
    hmm_model = model_data['hmm_model']
    svr_model = model_data['svr_model']
    svr_scaler = model_data['svr_scaler']
    state_mapping = model_data['state_mapping']
    avg_train_vol = model_data['avg_train_vol']
    n_states = model_data['n_states']
    
    # Engineer features on recent data
    df = engineer_features(recent_data)
    
    if len(df) < 20:
        return {"error": "Insufficient recent data for prediction"}
    
    # Predict regime using HMM on recent window
    lookback = min(252, len(df))  # Use up to 1 year of data
    recent_window = df.iloc[-lookback:]
    
    X_hmm = recent_window[['Log_Returns', 'Volatility']].values * 100
    hidden_states = hmm_model.predict(X_hmm)
    current_state_raw = hidden_states[-1]
    current_regime = state_mapping.get(current_state_raw, current_state_raw)
    
    # Get latest row for SVR prediction
    latest = df.iloc[-1]
    
    # Predict next volatility using SVR
    svr_features = np.array([[
        latest['Log_Returns'],
        latest['Volatility'],
        latest['Downside_Vol'],
        current_regime
    ]])
    svr_features_scaled = svr_scaler.transform(svr_features)
    predicted_vol = svr_model.predict(svr_features_scaled)[0]
    
    # Calculate risk ratio
    risk_ratio = predicted_vol / avg_train_vol if avg_train_vol > 0 else 1.0
    
    return {
        'regime': int(current_regime),
        'regime_label': 'Safe' if current_regime == 0 else ('Crash' if current_regime == n_states - 1 else 'Normal'),
        'predicted_vol': float(predicted_vol),
        'current_vol': float(latest['Volatility']),
        'risk_ratio': float(risk_ratio),
        'avg_train_vol': float(avg_train_vol),
        'n_states': n_states,
        'log_return': float(latest['Log_Returns']),
        'close_price': float(latest['Close'])
    }


def calculate_signal_and_position(
    symbol: str,
    recent_data: pd.DataFrame,
    short_window: int = 12,
    long_window: int = 26
) -> Optional[Dict[str, Any]]:
    """
   
    
    Returns:
        Dict with signal, target_position_size, regime info, etc.
    """
    # Get regime and volatility prediction
    prediction = predict_regime_and_volatility(symbol, recent_data)
    if prediction is None or 'error' in prediction:
        return prediction
    
    model_data = load_model(symbol)
    n_states = model_data['n_states']
    
    # Calculate EMAs on recent data
    df = recent_data.copy()
    df['EMA_Short'] = df['Close'].ewm(span=short_window).mean()
    df['EMA_Long'] = df['Close'].ewm(span=long_window).mean()
    
    latest = df.iloc[-1]
    
    # EMA Crossover Signal (1 = bullish, 0 = bearish)
    ema_signal = 1 if latest['EMA_Short'] > latest['EMA_Long'] else 0
    
    # Determine position size based on regime and risk
    regime = prediction['regime']
    risk_ratio = prediction['risk_ratio']
    
    # Default position size
    position_size = 1.0
    
    # Boost: 3x in safe regime with low risk
    if regime == 0 and risk_ratio < 0.5:
        position_size = 3.0
    
    # Cut: 0x in crash regime (highest volatility state)
    if regime == n_states - 1:
        position_size = 0.0
    
    # Target position = Signal * Position Size
    # Signal of 0 means no position regardless of size
    target_position = ema_signal * position_size
    
    return {
        'ema_signal': ema_signal,
        'ema_short': float(latest['EMA_Short']),
        'ema_long': float(latest['EMA_Long']),
        'regime': regime,
        'regime_label': prediction['regime_label'],
        'predicted_vol': prediction['predicted_vol'],
        'risk_ratio': risk_ratio,
        'position_size_multiplier': position_size,
        'target_position': target_position,  # 0, 1, or 3
        'close_price': float(latest['Close']),
        'reasoning': _get_signal_reasoning(ema_signal, regime, risk_ratio, position_size, n_states)
    }


def _get_signal_reasoning(ema_signal: int, regime: int, risk_ratio: float, 
                          position_size: float, n_states: int) -> str:
    """Generate human-readable reasoning for the signal."""
    reasons = []
    
    # EMA reasoning
    if ema_signal == 1:
        reasons.append("EMA crossover bullish (short > long)")
    else:
        reasons.append("EMA crossover bearish (short < long)")
    
    # Regime reasoning
    if regime == 0:
        reasons.append("Safe regime detected (low volatility)")
    elif regime == n_states - 1:
        reasons.append("⚠️ Crash regime detected (high volatility)")
    else:
        reasons.append(f"Normal regime ({regime})")
    
    # Risk reasoning
    if risk_ratio < 0.5:
        reasons.append(f"Low risk (ratio: {risk_ratio:.2f})")
    elif risk_ratio > 1.5:
        reasons.append(f"High risk (ratio: {risk_ratio:.2f})")
    else:
        reasons.append(f"Moderate risk (ratio: {risk_ratio:.2f})")
    
    # Position reasoning
    if position_size == 3.0:
        reasons.append("→ Leveraging 3x (safe + low risk)")
    elif position_size == 0.0:
        reasons.append("→ Position cut to 0 (crash regime)")
    else:
        reasons.append("→ Standard 1x position")
    
    return " | ".join(reasons)


def get_cached_models() -> Dict[str, Dict]:
    """Get info about all cached models."""
    return {
        symbol: {
            'trained_at': data.get('trained_at', 'Unknown'),
            'n_states': data.get('n_states', 3),
            'avg_train_vol': data.get('avg_train_vol', 0),
            'train_days': data.get('train_days', 0)
        }
        for symbol, data in _model_cache.items()
    }
