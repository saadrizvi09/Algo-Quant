"""
Strategy Handlers for Real-Time Trading
Converts backtesting strategies into stateful, real-time signal generators
"""
import numpy as np
import pandas as pd
from collections import deque
import os
import joblib
from typing import Optional


class BaseStrategyHandler:
    """Base class for all strategy handlers"""
    
    def __init__(self, **params):
        self.params = params
        print(f"[StrategyHandler] Initialized {self.__class__.__name__} with params: {params}")

    def get_signal(self, price: float) -> str:
        """
        Process a single price tick and return trading signal
        
        Returns:
            "BUY", "SELL", or "HOLD"
        """
        raise NotImplementedError


class HMMStrategyHandler(BaseStrategyHandler):
    """
    HMM Regime Filter Strategy Handler
    Uses Hidden Markov Model to detect market regimes and filters trades
    """
    
    def __init__(self, short_window=12, long_window=26, **params):
        super().__init__(**params)
        self.short_window = short_window
        self.long_window = long_window
        
        # Use deque for efficient rolling window of prices
        self.prices = deque(maxlen=long_window + 50)
        self.log_returns = deque(maxlen=long_window + 50)
        self.volatility = deque(maxlen=long_window + 50)
        
        # Load pre-trained HMM model
        self.model = None
        self.high_vol_state = None
        self._load_model()
        
        print(f"[HMMHandler] Initialized with windows: short={short_window}, long={long_window}")
        if self.model is None:
            print(f"[HMMHandler] ⚠️  WARNING: No trained model found. Using simple MA crossover strategy.")
    
    def _load_model(self):
        """Load the pre-trained HMM model from disk"""
        model_path = os.path.join(os.path.dirname(__file__), 'hmm_model.pkl')
        
        if os.path.exists(model_path):
            try:
                model_data = joblib.load(model_path)
                self.model = model_data['model']
                self.high_vol_state = model_data['high_vol_state']
                print(f"[HMMHandler] ✅ Loaded pre-trained HMM model from {model_path}")
                print(f"[HMMHandler] High volatility state: {self.high_vol_state}")
            except Exception as e:
                print(f"[HMMHandler] ❌ Error loading model: {e}")
                self.model = None
        else:
            print(f"[HMMHandler] ℹ️  Model file not found at {model_path}")
            print(f"[HMMHandler] Run backtest with model saving to generate hmm_model.pkl")
    
    def get_signal(self, price: float) -> str:
        """
        Generate trading signal based on current price
        
        Logic:
        1. Maintain rolling window of prices
        2. Calculate log returns and volatility
        3. If model loaded: Use HMM regime prediction + EMA crossover
        4. If no model: Fall back to simple EMA crossover
        """
        # Add price to rolling window
        self.prices.append(price)
        
        # Calculate log return
        if len(self.prices) >= 2:
            log_ret = np.log(self.prices[-1] / self.prices[-2])
            self.log_returns.append(log_ret)
        
        # Calculate rolling volatility
        if len(self.log_returns) >= 10:
            recent_returns = list(self.log_returns)[-10:]
            vol = np.std(recent_returns)
            self.volatility.append(vol)
        
        # Wait until we have enough data
        if len(self.prices) < self.long_window:
            return "HOLD"
        
        # Convert to pandas for easy calculation
        price_series = pd.Series(list(self.prices))
        
        # Calculate EMAs
        ema_short = price_series.ewm(span=self.short_window).mean().iloc[-1]
        ema_long = price_series.ewm(span=self.long_window).mean().iloc[-1]
        
        # Generate base signal (EMA crossover)
        base_signal = "BUY" if ema_short > ema_long else "SELL"
        
        # If model is loaded, use regime filter
        if self.model is not None and len(self.log_returns) >= 10 and len(self.volatility) >= 1:
            try:
                # Prepare features (same as training)
                current_return = self.log_returns[-1] * 100  # Scale to match training
                current_vol = self.volatility[-1] * 100
                
                features = np.array([[current_return, current_vol]])
                
                # Predict current regime
                current_regime = self.model.predict(features)[0]
                
                # Filter signal based on regime
                # Only take BUY signals when NOT in high volatility regime
                if current_regime == self.high_vol_state:
                    # High volatility - avoid trading
                    return "HOLD"
                else:
                    # Low/medium volatility - use EMA signal
                    return base_signal
                    
            except Exception as e:
                print(f"[HMMHandler] Error in regime prediction: {e}")
                return base_signal
        
        # Fallback: Simple EMA crossover
        return base_signal


class PairsStrategyHandler(BaseStrategyHandler):
    """
    Pairs Trading Strategy Handler
    Trades the spread between ETH and BTC using Z-score mean reversion
    
    Logic:
    - Tracks ETH/BTC ratio
    - Calculates Z-score (deviation from mean)
    - BUY when Z-score < -threshold (ratio is low, expect reversion up)
    - SELL when Z-score > +threshold (ratio is high, expect reversion down)
    - CLOSE when Z-score crosses zero (mean reversion complete)
    """
    
    def __init__(self, window=60, threshold=2.0, **params):
        super().__init__(**params)
        self.window = window
        self.threshold = threshold  # Z-score threshold
        
        # Track the ETH/BTC ratio
        self.ratio_history = deque(maxlen=window + 10)
        
        # Track position state
        self.position = None  # None, 'LONG', 'SHORT'
        self.entry_ratio = None
        
        print(f"[PairsHandler] Initialized with window={window}, threshold={threshold}")
    
    def update_ratio(self, eth_price: float, btc_price: float):
        """
        Update the ETH/BTC ratio
        Call this method to feed price data for both assets
        """
        if btc_price > 0:
            ratio = eth_price / btc_price
            self.ratio_history.append(ratio)
    
    def get_signal(self) -> str:
        """
        Generate signal based on ETH/BTC ratio Z-score
        Note: This method doesn't take a price parameter because it uses
        the ratio data fed via update_ratio()
        
        Returns:
            "BUY" - Open long on ratio (expect ratio to increase)
            "SELL" - Close position or open short (expect ratio to decrease)
            "HOLD" - Do nothing
        """
        if len(self.ratio_history) < self.window:
            return "HOLD"
        
        try:
            # Calculate Z-score of current ratio
            ratio_array = np.array(list(self.ratio_history))
            mean_ratio = np.mean(ratio_array[-self.window:])
            std_ratio = np.std(ratio_array[-self.window:])
            
            if std_ratio == 0 or np.isnan(std_ratio):
                return "HOLD"
            
            current_ratio = ratio_array[-1]
            z_score = (current_ratio - mean_ratio) / std_ratio
            
            # Entry Logic
            if self.position is None:
                # Ratio is too LOW (Z < -threshold) → Expect reversion UP → BUY (go LONG on ratio)
                if z_score < -self.threshold:
                    self.position = "LONG"
                    self.entry_ratio = current_ratio
                    print(f"[PairsHandler] 📊 Z-Score: {z_score:.2f} | Opening LONG (ratio undervalued)")
                    return "BUY"
                
                # Ratio is too HIGH (Z > +threshold) → Expect reversion DOWN → Don't buy
                # In a real pairs strategy, you'd short here, but for simplicity we just avoid
                elif z_score > self.threshold:
                    # For simulated trading with single asset, we treat this as SELL signal
                    # (meaning: don't hold ETH, ratio will decrease)
                    return "HOLD"  # Or "SELL" if you want to close any existing position
            
            # Exit Logic (Mean Reversion)
            elif self.position == "LONG":
                # Close LONG when Z-score crosses back to zero (mean reversion)
                if z_score >= 0:
                    pnl_pct = (current_ratio - self.entry_ratio) / self.entry_ratio * 100
                    print(f"[PairsHandler] 📊 Z-Score: {z_score:.2f} | Closing LONG (mean reversion) | P&L: {pnl_pct:.2f}%")
                    self.position = None
                    self.entry_ratio = None
                    return "SELL"
                
                # Or close if Z-score goes too high (stop loss)
                elif z_score > self.threshold * 1.5:
                    print(f"[PairsHandler] ⚠️  Z-Score: {z_score:.2f} | Stop loss triggered")
                    self.position = None
                    self.entry_ratio = None
                    return "SELL"
            
            # Log current state
            if len(self.ratio_history) % 6 == 0:  # Log every 6th update (every minute if 10s interval)
                print(f"[PairsHandler] Z-Score: {z_score:.2f} | Ratio: {current_ratio:.6f} | Position: {self.position or 'NONE'}")
            
            return "HOLD"
            
        except Exception as e:
            print(f"[PairsHandler] ❌ Error calculating signal: {e}")
            return "HOLD"
    
    def get_current_zscore(self) -> Optional[float]:
        """Get the current Z-score for monitoring"""
        if len(self.ratio_history) < self.window:
            return None
        
        try:
            ratio_array = np.array(list(self.ratio_history))
            mean_ratio = np.mean(ratio_array[-self.window:])
            std_ratio = np.std(ratio_array[-self.window:])
            
            if std_ratio == 0 or np.isnan(std_ratio):
                return None
            
            current_ratio = ratio_array[-1]
            z_score = (current_ratio - mean_ratio) / std_ratio
            
            if np.isnan(z_score) or np.isinf(z_score):
                return None
                
            return z_score
        except Exception as e:
            print(f"[PairsHandler] Error calculating Z-score: {e}")
            return None


def create_strategy_handler(strategy: str, **params) -> BaseStrategyHandler:
    """
    Factory function to create appropriate strategy handler
    
    Args:
        strategy: Strategy name or ID (e.g., "HMM Regime Filter", "hmm", "Pairs Strategy", "pairs")
        **params: Strategy-specific parameters
    
    Returns:
        Instance of appropriate strategy handler
    """
    # Normalize strategy name (accept both ID and full name)
    strategy_lower = strategy.lower()
    
    if strategy_lower in ["hmm", "hmm regime filter"]:
        return HMMStrategyHandler(**params)
    elif strategy_lower in ["pairs", "pairs strategy", "pairs trading (eth/btc)"]:
        return PairsStrategyHandler(**params)
    else:
        raise ValueError(f"Unknown strategy: {strategy}")
