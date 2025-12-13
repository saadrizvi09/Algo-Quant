"""
Pairs Trading Strategy (ETH/BTC Mean Reversion)
Uses Z-Score to detect when the ETH/BTC ratio deviates from its mean
"""
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from binance.client import Client
import os


def fetch_pairs_data(period: str = '7d', interval: str = '1m', use_binance: bool = False) -> pd.DataFrame:
    """
    Fetches ETH/BTC ratio data.
    If use_binance=True, fetches ETHBTC directly from Binance (for recent data).
    Otherwise uses Yahoo Finance (for historical backtests).
    """
    if use_binance:
        try:
            # Fetch from Binance ETHBTC pair
            from binance.client import Client
            from dotenv import load_dotenv
            load_dotenv()
            
            api_key = os.getenv("BINANCE_API_KEY", "")
            api_secret = os.getenv("BINANCE_SECRET_KEY", "")
            client = Client(api_key, api_secret, testnet=True)
            
            # Map interval
            interval_map = {
                '1m': Client.KLINE_INTERVAL_1MINUTE,
                '5m': Client.KLINE_INTERVAL_5MINUTE,
                '15m': Client.KLINE_INTERVAL_15MINUTE,
                '1h': Client.KLINE_INTERVAL_1HOUR,
                '1d': Client.KLINE_INTERVAL_1DAY
            }
            
            binance_interval = interval_map.get(interval, Client.KLINE_INTERVAL_5MINUTE)
            
            # Determine limit based on period
            period_to_limit = {
                '1d': 1440 if interval == '1m' else 288,  # 1 day
                '7d': 2016 if interval == '5m' else 168,   # 7 days
                '30d': 1440,  # 30 days with hourly
                '60d': 1440   # 60 days
            }
            limit = period_to_limit.get(period, 500)
            
            klines = client.get_klines(symbol='ETHBTC', interval=binance_interval, limit=limit)
            
            df = pd.DataFrame({
                'Ratio': [float(k[4]) for k in klines]  # Close price is ETH/BTC ratio
            }, index=pd.to_datetime([k[0] for k in klines], unit='ms'))
            
            return df.dropna()
        except Exception as e:
            print(f"Binance fetch failed: {e}, falling back to Yahoo Finance")
            use_binance = False
    
    # Yahoo Finance fallback (calculate ratio from separate prices)
    try:
        tickers = "BTC-USD ETH-USD"
        data = yf.download(tickers, period=period, interval=interval, group_by='ticker', progress=False)
        
        if data.empty:
            print("No data returned from Yahoo Finance")
            return pd.DataFrame()
        
        df = pd.DataFrame(index=data.index)
        
        # Handle MultiIndex columns (when multiple tickers are downloaded)
        if isinstance(data.columns, pd.MultiIndex):
            df['BTC'] = data['BTC-USD']['Close']
            df['ETH'] = data['ETH-USD']['Close']
        else:
            # Single ticker case or flat structure
            if 'Close' in data.columns:
                # This shouldn't happen with 2 tickers, but handle it
                df['BTC'] = data['Close']
                df['ETH'] = data['Close']
            else:
                print("Unexpected data structure from Yahoo Finance")
                return pd.DataFrame()
        
        df['Ratio'] = df['ETH'] / df['BTC']
        df = df[['Ratio']].dropna()
        return df
        
    except Exception as e:
        print(f"Yahoo Finance download error: {e}")
        return pd.DataFrame()


def calculate_zscore(df: pd.DataFrame, window: int = 60) -> pd.DataFrame:
    """
    Calculates the Z-Score of the ETH/BTC ratio.
    """
    df = df.copy()
    # Ratio column should already exist from fetch_pairs_data
    if 'Ratio' not in df.columns:
        raise ValueError("DataFrame must contain 'Ratio' column")
    
    df['Mean'] = df['Ratio'].rolling(window=window).mean()
    df['Std'] = df['Ratio'].rolling(window=window).std()
    df['Z-Score'] = (df['Ratio'] - df['Mean']) / df['Std']
    return df.dropna()


def simulate_pairs_backtest(start_date: str, end_date: str,
                             initial_capital: float = 10000,
                             window: int = 30,
                             threshold: float = 1.0,
                             fee: float = 0.00075) -> Dict:
    """
    Backtests the pairs trading strategy on historical data.
    """
    start = pd.Timestamp(start_date).tz_localize('UTC')
    end = pd.Timestamp(end_date).tz_localize('UTC')
    days = (end - start).days
    
    if days < 1:
        return {"error": "Date range too short"}
    
    # Determine the period to fetch
    if days <= 7:
        period = '7d'
        interval = '1m'
    elif days <= 60:
        period = '60d'
        interval = '5m'
    else:
        period = f'{min(days, 730)}d'
        interval = '1h'
    
    try:
        raw_df = fetch_pairs_data(period=period, interval=interval)
    except Exception as e:
        return {"error": f"Failed to fetch data: {str(e)}"}
    
    if raw_df.empty:
        return {"error": "No data available for the selected period"}
    
    # Ensure index is timezone-aware for comparison
    if raw_df.index.tz is None:
        raw_df.index = raw_df.index.tz_localize('UTC')
    
    # Filter to date range
    raw_df = raw_df[(raw_df.index >= start) & (raw_df.index <= end)]
    
    if len(raw_df) < window + 10:
        return {"error": "Not enough data points for the selected parameters"}
    
    df = calculate_zscore(raw_df, window)
    
    # Backtest engine
    trades = []
    position = 0  # 0 = Flat, 1 = Long Ratio, -1 = Short Ratio
    entry_price = 0
    entry_time = None
    balance = initial_capital
    equity_curve = []
    
    for index, row in df.iterrows():
        z = row['Z-Score']
        current_ratio = row['Ratio']
        
        # Entry Logic
        if position == 0 and z < -threshold:
            position = 1
            entry_price = current_ratio
            entry_time = index
            trades.append({
                'time': index,
                'type': 'OPEN_LONG',
                'price': current_ratio,
                'z_score': z,
                'pnl': 0
            })
            
        elif position == 0 and z > threshold:
            position = -1
            entry_price = current_ratio
            entry_time = index
            trades.append({
                'time': index,
                'type': 'OPEN_SHORT',
                'price': current_ratio,
                'z_score': z,
                'pnl': 0
            })
        
        # Exit Logic (Mean Reversion)
        elif position == 1 and z >= 0:
            raw_pnl = (current_ratio - entry_price) / entry_price
            net_pnl = raw_pnl - (fee * 2)
            profit_cash = balance * net_pnl
            balance += profit_cash
            position = 0
            
            trades.append({
                'time': index,
                'type': 'CLOSE_LONG',
                'price': current_ratio,
                'z_score': z,
                'pnl': profit_cash,
                'pnl_pct': net_pnl * 100
            })
            
        elif position == -1 and z <= 0:
            raw_pnl = (entry_price - current_ratio) / entry_price
            net_pnl = raw_pnl - (fee * 2)
            profit_cash = balance * net_pnl
            balance += profit_cash
            position = 0
            
            trades.append({
                'time': index,
                'type': 'CLOSE_SHORT',
                'price': current_ratio,
                'z_score': z,
                'pnl': profit_cash,
                'pnl_pct': net_pnl * 100
            })
        
        equity_curve.append({
            'date': index.strftime('%Y-%m-%d %H:%M') if hasattr(index, 'strftime') else str(index),
            'equity': balance,
            'strategy': balance / initial_capital,
            'buy_hold': 1.0,
            'regime': 0
        })
    
    # Calculate metrics
    close_trades = [t for t in trades if 'pnl_pct' in t]
    winning_trades = [t for t in close_trades if t.get('pnl', 0) > 0]
    losing_trades = [t for t in close_trades if t.get('pnl', 0) < 0]
    
    total_return = (balance - initial_capital) / initial_capital
    win_rate = len(winning_trades) / len(close_trades) * 100 if close_trades else 0
    
    # Calculate returns for Sharpe and Sortino
    if len(equity_curve) > 1:
        returns = []
        for i in range(1, len(equity_curve)):
            ret = (equity_curve[i]['equity'] - equity_curve[i-1]['equity']) / equity_curve[i-1]['equity']
            returns.append(ret)
        
        # Sharpe ratio
        sharpe = (np.mean(returns) / np.std(returns)) * np.sqrt(252 * 24) if np.std(returns) > 0 else 0
        
        # Sortino ratio (downside deviation)
        negative_returns = [r for r in returns if r < 0]
        downside_std = np.std(negative_returns) if len(negative_returns) > 0 else 0
        sortino = (np.mean(returns) / downside_std) * np.sqrt(252 * 24) if downside_std > 0 else 0
    else:
        sharpe = 0
        sortino = 0
    
    # Profit Factor
    total_wins = sum([abs(t.get('pnl', 0)) for t in winning_trades]) if winning_trades else 0
    total_losses = sum([abs(t.get('pnl', 0)) for t in losing_trades]) if losing_trades else 0
    profit_factor = total_wins / total_losses if total_losses > 0 else (float('inf') if total_wins > 0 else 0)
    
    # Average Risk:Reward Ratio
    avg_win = (total_wins / len(winning_trades)) if winning_trades else 0
    avg_loss = (total_losses / len(losing_trades)) if losing_trades else 0
    risk_reward = avg_win / avg_loss if avg_loss > 0 else 0
    
    # Max drawdown - Strategy
    peak = initial_capital
    max_dd_strategy = 0
    for point in equity_curve:
        if point['equity'] > peak:
            peak = point['equity']
        dd = (peak - point['equity']) / peak
        if dd > max_dd_strategy:
            max_dd_strategy = dd
    
    # Max drawdown - Buy and Hold (based on ratio price movement)
    ratio_prices = [raw_df.loc[raw_df.index[i], 'Ratio'] if i < len(raw_df) else raw_df['Ratio'].iloc[-1] for i in range(len(equity_curve))]
    if ratio_prices:
        ratio_peak = ratio_prices[0]
        max_dd_bh = 0
        for price in ratio_prices:
            if price > ratio_peak:
                ratio_peak = price
            dd = (ratio_peak - price) / ratio_peak
            if dd > max_dd_bh:
                max_dd_bh = dd
    else:
        max_dd_bh = 0
    
    # Downsample equity curve for chart (max 500 points)
    if len(equity_curve) > 500:
        step = len(equity_curve) // 500
        equity_curve = equity_curve[::step]
    
    # Format trades for response
    formatted_trades = []
    for t in close_trades[-50:]:
        formatted_trades.append({
            'entry_date': t['time'].strftime('%Y-%m-%d %H:%M') if hasattr(t['time'], 'strftime') else str(t['time']),
            'exit_date': t['time'].strftime('%Y-%m-%d %H:%M') if hasattr(t['time'], 'strftime') else str(t['time']),
            'entry_price': float(t['price']),
            'exit_price': float(t['price']),
            'duration_days': 0,
            'trade_pnl': t.get('pnl_pct', 0) / 100,
            'trade_pnl_percent': t.get('pnl_pct', 0),
            'regime': 0,
            'type': t['type'],
            'z_score': round(t['z_score'], 2)
        })
    
    # Recovery Factor (total return / max drawdown)
    recovery_factor = abs(total_return / max_dd_strategy) if max_dd_strategy > 0 else 0
    
    return {
        "metrics": {
            "strategy_return": f"{total_return:.2%}",
            "buy_hold_return": "N/A (Pairs)",
            "final_value": f"${balance:.2f}",
            "sharpe_ratio": f"{sharpe:.2f}",
            "sortino_ratio": f"{sortino:.2f}",
            "max_drawdown": f"{-max_dd_strategy:.2%}",
            "max_drawdown_bh": f"{-max_dd_bh:.2%}",
            "profit_factor": f"{profit_factor:.2f}" if profit_factor != float('inf') else "∞",
            "risk_reward": f"{risk_reward:.2f}",
            "recovery_factor": f"{recovery_factor:.2f}",
            "win_rate": f"{win_rate:.1f}%",
            "total_trades": len(close_trades),
            "trades_per_day": f"{len(close_trades) / max(days, 1):.1f}"
        },
        "chart_data": equity_curve,
        "trades": formatted_trades
    }


class PairsTradingSignal:
    """
    Live signal generator for pairs trading.
    """
    
    def __init__(self, window: int = 30, threshold: float = 1.0):
        self.window = window
        self.threshold = threshold
        self.position = 0
        self.entry_price = 0
        
    def get_signal(self) -> int:
        """
        Get current trading signal based on live data.
        Returns: 1 for long, -1 for short, 0 for flat/hold
        """
        try:
            df = fetch_pairs_data(period='1d', interval='1m')
            if len(df) < self.window + 5:
                return 0
            
            df = calculate_zscore(df, self.window)
            z = df['Z-Score'].iloc[-1]
            
            if self.position == 0:
                if z < -self.threshold:
                    self.position = 1
                    self.entry_price = df['Ratio'].iloc[-1]
                    return 1
                elif z > self.threshold:
                    self.position = -1
                    self.entry_price = df['Ratio'].iloc[-1]
                    return -1
            elif self.position == 1 and z >= 0:
                self.position = 0
                return 0
            elif self.position == -1 and z <= 0:
                self.position = 0
                return 0
                
            return -2  # Hold current position
            
        except Exception as e:
            print(f"Signal error: {e}")
            return 0
    
    def get_current_zscore(self) -> Optional[float]:
        """Get current Z-Score"""
        try:
            df = fetch_pairs_data(period='1d', interval='1m')
            df = calculate_zscore(df, self.window)
            return float(df['Z-Score'].iloc[-1])
        except:
            return None
