"""
HMM-SVR Strategy Handler
Long-term trading strategy using regime detection and volatility prediction.
Checks every 3 hours - designed for position trading.
"""
import pandas as pd
from collections import deque
from datetime import datetime, timedelta


class HMMSVRStrategyHandler:
    """
    HMM-SVR Strategy Handler for long-term trading.
    Uses pre-trained models for regime detection and volatility prediction.
    Position sizing: 0x (no position), 1x (normal), or 3x (high conviction).
    """
    
    # Fixed EMA windows (standard values for trend detection)
    SHORT_WINDOW = 12
    LONG_WINDOW = 26
    
    def __init__(self, symbol: str):
        self.symbol = symbol
        
        # Buffer for historical prices (400 days for feature calculation)
        self.price_buffer = deque(maxlen=400)
        self.last_position_size = 0.0
        
        # Pre-load historical data for immediate signal generation
        self._preload_historical_data()
        
        print(f"[HMM-SVR] Initialized for {symbol} | {len(self.price_buffer)} historical prices")
    
    def _preload_historical_data(self):
        """Pre-load historical price data from Yahoo Finance."""
        try:
            import yfinance as yf
            
            # Map symbol to Yahoo Finance ticker
            symbol_map = {
                "BTC": "BTC-USD",
                "BTCUSDT": "BTC-USD",
                "ETH": "ETH-USD",
                "ETHUSDT": "ETH-USD",
                "BNB": "BNB-USD",
                "BNBUSDT": "BNB-USD",
                "SOL": "SOL-USD",
                "SOLUSDT": "SOL-USD",
                "LINK": "LINK-USD",
                "LINKUSDT": "LINK-USD"
            }
            
            ticker_symbol = symbol_map.get(self.symbol.upper(), f"{self.symbol.replace('USDT', '')}-USD")
            
            # Fetch 450 days of daily data
            ticker = yf.Ticker(ticker_symbol)
            end_date = datetime.now()
            start_date = end_date - timedelta(days=450)
            hist = ticker.history(start=start_date, end=end_date, interval="1d")
            
            if hist.empty:
                print(f"[HMM-SVR] ⚠️ No historical data for {ticker_symbol}")
                return
            
            # Load last 400 prices into buffer
            prices = hist['Close'].dropna().values
            for price in prices[-400:]:
                self.price_buffer.append(float(price))
            
            print(f"[HMM-SVR] ✅ Loaded {len(self.price_buffer)} prices")
            
        except Exception as e:
            print(f"[HMM-SVR] ⚠️ Error loading historical data: {e}")
    
    def get_signal(self, price: float) -> str:
        """
        Generate trading signal using HMM-SVR model.
        
        Returns:
            "BUY" - open/increase position
            "SELL" - close position
            "HOLD" - maintain current state
        """
        # Add current price to buffer
        self.price_buffer.append(float(price))
        
        # Need at least 100 data points
        if len(self.price_buffer) < 100:
            return "HOLD"
        
        try:
            # Convert buffer to DataFrame for model
            df = pd.DataFrame({'Close': list(self.price_buffer)})
            
            # Get signal from model_manager
            from model_manager import calculate_signal_and_position
            
            result = calculate_signal_and_position(
                symbol=self.symbol,
                recent_data=df,
                short_window=self.SHORT_WINDOW,
                long_window=self.LONG_WINDOW
            )
            
            if result is None or 'error' in result:
                print(f"[HMM-SVR] Error: {result}")
                return "HOLD"
            
            # Extract results
            target_position = result.get('target_position_size', 0.0)
            regime = result.get('regime_label', 'Unknown')
            ema_signal = result.get('ema_signal', 0)
            
            ema_str = 'Bullish' if ema_signal else 'Bearish'
            print(f"[HMM-SVR] Regime: {regime} | Target: {target_position}x | Trend: {ema_str}")
            
            # Determine action based on position change
            if target_position > self.last_position_size:
                signal = "BUY"
            elif target_position < self.last_position_size:
                signal = "SELL"
            else:
                signal = "HOLD"
            
            self.last_position_size = target_position
            return signal
            
        except Exception as e:
            print(f"[HMM-SVR] Error generating signal: {e}")
            return "HOLD"
