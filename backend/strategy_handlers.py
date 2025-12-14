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
    HMM-SVR Honest Leverage Strategy Handler (Walk-Forward)
    Uses strict walk-forward approach: only uses data available up to current moment.
    Applies dynamic leverage (0x, 1x, 3x) based on regime and predicted risk.
    """
    
    def __init__(self, short_window=12, long_window=26, **params):
        super().__init__(**params)
        self.short_window = short_window
        self.long_window = long_window
        
        # Use deque for efficient rolling window (252 days = 1 year)
        self.lookback_window = 252
        self.prices = deque(maxlen=self.lookback_window)
        self.log_returns = deque(maxlen=self.lookback_window)
        self.volatility = deque(maxlen=self.lookback_window)
        self.downside_vol = deque(maxlen=self.lookback_window)
        
        # Load pre-trained HMM-SVR model
        self.hmm_model = None
        self.svr_model = None
        self.svr_scaler = None
        self.state_mapping = None
        self.avg_train_vol = None
        self.n_states = 3
        self._load_model()
        
        print(f"[HMMHandler] Initialized HMM-SVR Honest Strategy")
        print(f"[HMMHandler] Windows: EMA={short_window}/{long_window}, Lookback={self.lookback_window}")
        if self.hmm_model is None:
            print(f"[HMMHandler] ⚠️  WARNING: No trained model. Using simple MA crossover.")
    
    def _load_model(self):
        """Load the pre-trained HMM-SVR hybrid model from disk"""
        model_path = os.path.join(os.path.dirname(__file__), 'hmm_model.pkl')
        
        if os.path.exists(model_path):
            try:
                model_data = joblib.load(model_path)
                self.hmm_model = model_data['hmm_model']
                self.svr_model = model_data['svr_model']
                self.svr_scaler = model_data['svr_scaler']
                self.state_mapping = model_data['state_mapping']
                self.avg_train_vol = model_data['avg_train_vol']
                self.n_states = model_data['n_states']
                print(f"[HMMHandler] ✅ Loaded HMM-SVR model from {model_path}")
                print(f"[HMMHandler] States: 0=Low Vol, {self.n_states-1}=High Vol")
                print(f"[HMMHandler] Avg training vol: {self.avg_train_vol:.6f}")
            except Exception as e:
                print(f"[HMMHandler] ❌ Error loading model: {e}")
                self.hmm_model = None
        else:
            print(f"[HMMHandler] ℹ️  Model file not found at {model_path}")
            print(f"[HMMHandler] Run backtest to generate hmm_model.pkl")
    
    def get_signal(self, price: float) -> str:
        """
        Generate trading signal with leverage (Walk-Forward Honest Approach)
        
        Logic:
        1. Maintain rolling window of historical prices (252 days)
        2. Calculate features using ONLY historical data
        3. Use HMM to predict current regime (using full history sequence)
        4. Use SVR to predict next-day volatility (using today's features)
        5. Calculate leverage: 0x (crash), 1x (normal), 3x (certainty)
        6. Return signal (HOLD forced in crash regime)
        
        Returns: "BUY", "SELL", or "HOLD"
        """
        # Add price to rolling window
        self.prices.append(price)
        
        # Calculate log return
        if len(self.prices) >= 2:
            log_ret = np.log(self.prices[-1] / self.prices[-2])
            self.log_returns.append(log_ret)
        
        # Calculate rolling volatility (10-period to match training)
        if len(self.log_returns) >= 10:
            recent_returns = list(self.log_returns)[-10:]
            vol = np.std(recent_returns)
            self.volatility.append(vol)
            
            # Calculate downside volatility (negative returns only)
            negative_returns = [r for r in recent_returns if r < 0]
            dside_vol = np.std(negative_returns) if len(negative_returns) > 0 else 0
            self.downside_vol.append(dside_vol)
        
        # Wait until we have enough data
        if len(self.prices) < max(self.long_window, 30):
            return "HOLD"
        
        # Convert to pandas for EMA calculation
        price_series = pd.Series(list(self.prices))
        
        # Calculate EMAs using ONLY historical data (honest approach)
        ema_short = price_series.ewm(span=self.short_window).mean().iloc[-1]
        ema_long = price_series.ewm(span=self.long_window).mean().iloc[-1]
        
        # Generate base signal (EMA crossover)
        base_signal = "BUY" if ema_short > ema_long else "SELL"
        
        # If model loaded, use honest HMM-SVR prediction
        if (self.hmm_model is not None and self.svr_model is not None and 
            len(self.log_returns) >= 30 and len(self.volatility) >= 10):
            try:
                # A. Honest Regime Detection (using full historical sequence)
                # Prepare features for ALL history in window
                returns_array = np.array(list(self.log_returns))
                vol_array = np.array(list(self.volatility))
                
                # Pad if needed to match lengths
                min_len = min(len(returns_array), len(vol_array))
                X_history = np.column_stack([
                    returns_array[-min_len:] * 100,
                    vol_array[-min_len:] * 100
                ])
                
                # Predict sequence and get CURRENT regime
                hidden_states = self.hmm_model.predict(X_history)
                current_state_raw = hidden_states[-1]
                current_regime = self.state_mapping[current_state_raw]
                
                # B. Honest Volatility Prediction (using today's features)
                svr_features = np.array([[
                    self.log_returns[-1],
                    self.volatility[-1],
                    self.downside_vol[-1],
                    current_regime
                ]])
                
                # Scale and predict
                svr_features_scaled = self.svr_scaler.transform(svr_features)
                predicted_vol = self.svr_model.predict(svr_features_scaled)[0]
                risk_ratio = predicted_vol / self.avg_train_vol
                
                # C. Calculate Leverage
                if current_regime == self.n_states - 1:  # Crash regime
                    leverage = 0.0
                    signal = "HOLD"  # Force exit
                elif current_regime == 0 and risk_ratio < 0.5:  # Certainty
                    leverage = 3.0
                    signal = base_signal
                else:  # Normal
                    leverage = 1.0
                    signal = base_signal
                
                # Store for external access
                self.current_leverage = leverage
                self.current_regime = current_regime
                self.current_risk_ratio = risk_ratio
                
                print(f"[HMMHandler] Regime={current_regime}, Risk={risk_ratio:.3f}, Lev={leverage}x, Signal={signal}")
                return signal
                    
            except Exception as e:
                print(f"[HMMHandler] Error in prediction: {e}")
                self.current_leverage = 1.0
                return base_signal
        
        # Fallback: Simple EMA crossover with 1x leverage
        self.current_leverage = 1.0
        return base_signal
    
    def get_leverage(self) -> float:
        """Return current leverage multiplier (0x, 1x, or 3x)"""
        return getattr(self, 'current_leverage', 1.0)
    
    def get_regime(self) -> Optional[int]:
        """Return current market regime (0=Low Vol, 1=Neutral, 2=High Vol)"""
        return getattr(self, 'current_regime', None)
    
    def get_risk_ratio(self) -> Optional[float]:
        """Return current risk ratio (predicted_vol / avg_train_vol)"""
        return getattr(self, 'current_risk_ratio', None)


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
