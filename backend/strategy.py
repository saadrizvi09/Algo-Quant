import yfinance as yf
import pandas as pd
import numpy as np
from hmmlearn.hmm import GaussianHMM
from datetime import datetime
import joblib
import os

def fetch_data(ticker, start_date, end_date):
    # FIXED: Added auto_adjust=True to clean up data splits/dividends automatically
    df = yf.download(ticker, start=start_date, end=end_date, progress=False, auto_adjust=True)
    
    if df.empty: return None
    
    # FIXED: More robust MultiIndex handling
    if isinstance(df.columns, pd.MultiIndex):
        # Check if the first level contains 'Close' (standard format is Price, Ticker)
        if 'Close' in df.columns.get_level_values(0):
            df.columns = df.columns.get_level_values(0)
        else:
            # Fallback for (Ticker, Price) format
            df.columns = df.columns.get_level_values(1)
            
    return df.dropna()

def generate_trade_log(df):
    """
    Scans the backtest dataframe to identify individual trade cycles.
    """
    trades = []
    in_trade = False
    entry_date = None
    entry_price = 0
    trade_returns = []
    
    for date, row in df.iterrows():
        pos = row['Position']
        close_price = row['Close']
        
        # Check for Entry
        if pos > 0 and not in_trade:
            in_trade = True
            entry_date = date
            entry_price = close_price
            # We initialize with 0 return on the entry day because PnL comes from the NEXT day
            trade_returns = [] 
            
        # Check for adjustments while in trade
        elif pos > 0 and in_trade:
            trade_returns.append(row['Strategy_Returns'])
            
        # Check for Exit
        elif pos == 0 and in_trade:
            in_trade = False
            exit_date = date
            exit_price = close_price
            
            # Calculate compounded return
            cum_trade_ret = np.prod([1 + r for r in trade_returns]) - 1
            
            trades.append({
                'entry_date': entry_date,
                'exit_date': exit_date,
                'entry_price': entry_price,
                'exit_price': exit_price,
                'duration_days': len(trade_returns),
                'trade_pnl': cum_trade_ret,
                'trade_pnl_percent': cum_trade_ret * 100
            })
            trade_returns = []

    # Handle Open Trade
    if in_trade:
        cum_trade_ret = np.prod([1 + r for r in trade_returns]) - 1
        trades.append({
            'entry_date': entry_date,
            'exit_date': df.index[-1],
            'entry_price': entry_price,
            'exit_price': df.iloc[-1]['Close'],
            'duration_days': len(trade_returns),
            'trade_pnl': cum_trade_ret,
            'trade_pnl_percent': cum_trade_ret * 100
        })

    return trades

def train_models_and_backtest(ticker, start_date, end_date, short_window, long_window, n_states):
    # 1. Fetch Data
    train_start = pd.Timestamp(start_date) - pd.DateOffset(years=2) 
    df = fetch_data(ticker, train_start, end_date)
    
    if df is None or len(df) < 200:
        return {"error": "Not enough data"}

    # Feature Engineering
    df['Log_Returns'] = np.log(df['Close'] / df['Close'].shift(1))
    df['Volatility'] = df['Log_Returns'].rolling(window=10).std()
    df['EMA_Short'] = df['Close'].ewm(span=short_window).mean()
    df['EMA_Long'] = df['Close'].ewm(span=long_window).mean()
    df = df.dropna()

    # Split Data
    test_mask = df.index >= pd.Timestamp(start_date)
    train_df = df[~test_mask].copy()
    test_df = df[test_mask].copy()

    if test_df.empty: return {"error": "No data in selected date range"}

    # 2. Train HMM
    X_train = train_df[['Log_Returns', 'Volatility']].values * 100
    hmm_model = GaussianHMM(n_components=n_states, covariance_type="full", n_iter=100, random_state=42)
    hmm_model.fit(X_train)
    
    # Identify "High Volatility" state
    state_vars = [hmm_model.means_[i][1] for i in range(n_states)]
    high_vol_state = np.argmax(state_vars)
    
    # Save the trained model for live trading
    model_data = {
        'model': hmm_model,
        'high_vol_state': high_vol_state,
        'n_states': n_states,
        'trained_at': datetime.now().isoformat()
    }
    model_path = os.path.join(os.path.dirname(__file__), 'hmm_model.pkl')
    joblib.dump(model_data, model_path)
    print(f"✅ HMM Model trained and saved to {model_path}")
    print(f"   High volatility state: {high_vol_state}")

    # 3. Backtest
    X_test = test_df[['Log_Returns', 'Volatility']].values * 100
    test_df['Regime'] = hmm_model.predict(X_test)
    
    # Signals
    test_df['Signal'] = np.where(test_df['EMA_Short'] > test_df['EMA_Long'], 1, 0)
    
    # Strategy Position
    test_df['Position'] = np.where(
        (test_df['Signal'] == 1) & (test_df['Regime'] != high_vol_state), 
        1.0, 
        0.0
    )
    
    # Returns Calculation
    test_df['Simple_Returns'] = test_df['Close'].pct_change()
    
    # FIXED: Use a temporary shifted column for returns, but keep 'Position' clean for the log
    test_df['Position_Shifted'] = test_df['Position'].shift(1)
    test_df['Strategy_Returns'] = test_df['Position_Shifted'] * test_df['Simple_Returns']
    
    # --- CUMULATIVE CURVES ---
    test_df['Strategy_Equity'] = (1 + test_df['Strategy_Returns'].fillna(0)).cumprod()
    test_df['BuyHold_Equity'] = (1 + test_df['Simple_Returns'].fillna(0)).cumprod()

    # 4. Generate Trade Log
    # FIXED: Passed the original test_df with unshifted Position
    trades_list = generate_trade_log(test_df)
    
    trades_data = []
    for trade in trades_list:
        trades_data.append({
            'entry_date': trade['entry_date'].strftime('%Y-%m-%d'),
            'exit_date': trade['exit_date'].strftime('%Y-%m-%d'),
            'entry_price': float(trade['entry_price']),
            'exit_price': float(trade['exit_price']),
            'duration_days': int(trade['duration_days']),
            'trade_pnl': float(trade['trade_pnl']),
            'trade_pnl_percent': float(trade['trade_pnl_percent']),
            'regime': int(test_df.loc[trade['entry_date'], 'Regime']) if trade['entry_date'] in test_df.index else 0
        })

    # 5. JSON Response - Chart Data
    chart_data = []
    for date, row in test_df.iterrows():
        chart_data.append({
            'date': date.strftime('%Y-%m-%d'),
            'strategy': float(row['Strategy_Equity']),
            'buy_hold': float(row['BuyHold_Equity']),
            'regime': int(row['Regime'])
        })

    # 6. Calculate Advanced Metrics
    strat_total = test_df['Strategy_Equity'].iloc[-1] - 1
    bh_total = test_df['BuyHold_Equity'].iloc[-1] - 1
    
    strategy_returns = test_df['Strategy_Returns'].dropna()
    sharpe = (strategy_returns.mean() / strategy_returns.std()) * np.sqrt(252) if strategy_returns.std() != 0 else 0
    
    # Max Drawdown
    rolling_max_strategy = test_df['Strategy_Equity'].cummax()
    drawdown_strategy = (test_df['Strategy_Equity'] - rolling_max_strategy) / rolling_max_strategy
    max_drawdown_strategy = drawdown_strategy.min()
    
    rolling_max_bh = test_df['BuyHold_Equity'].cummax()
    drawdown_bh = (test_df['BuyHold_Equity'] - rolling_max_bh) / rolling_max_bh
    max_drawdown_bh = drawdown_bh.min()
    
    # FIXED: Win Rate Calculation (Consistency Check)
    closed_trades = [t for t in trades_list if t['exit_date'] != test_df.index[-1]]
    winning_closed_trades = [t for t in closed_trades if t['trade_pnl'] > 0]
    
    win_rate = (len(winning_closed_trades) / len(closed_trades) * 100) if closed_trades else 0
    
    # Sortino Ratio
    negative_returns = strategy_returns[strategy_returns < 0]
    downside_std = negative_returns.std() if len(negative_returns) > 0 else 0
    sortino = (strategy_returns.mean() / downside_std) * np.sqrt(252) if downside_std != 0 else 0
    
    # Profit Factor (All trades including open ones)
    winning_trades = [t for t in trades_list if t['trade_pnl'] > 0]
    losing_trades = [t for t in trades_list if t['trade_pnl'] < 0]
    
    total_wins = sum([t['trade_pnl'] for t in winning_trades]) if winning_trades else 0
    total_losses = abs(sum([t['trade_pnl'] for t in losing_trades])) if losing_trades else 0
    profit_factor = total_wins / total_losses if total_losses != 0 else (float('inf') if total_wins > 0 else 0)
    
    # Risk Reward
    avg_win = (total_wins / len(winning_trades)) if winning_trades else 0
    avg_loss = (total_losses / len(losing_trades)) if losing_trades else 0
    risk_reward = avg_win / avg_loss if avg_loss != 0 else 0
    
    recovery_factor = abs(strat_total / max_drawdown_strategy) if max_drawdown_strategy != 0 else 0

    return {
        "metrics": {
            "strategy_return": f"{strat_total:.2%}",
            "buy_hold_return": f"{bh_total:.2%}",
            "final_value": f"${test_df['Strategy_Equity'].iloc[-1] * 10000:.2f}",
            "sharpe_ratio": f"{sharpe:.2f}",
            "sortino_ratio": f"{sortino:.2f}",
            "max_drawdown": f"{max_drawdown_strategy:.2%}",
            "max_drawdown_bh": f"{max_drawdown_bh:.2%}",
            "profit_factor": f"{profit_factor:.2f}" if profit_factor != float('inf') else "∞",
            "risk_reward": f"{risk_reward:.2f}",
            "recovery_factor": f"{recovery_factor:.2f}",
            "win_rate": f"{win_rate:.1f}%",
            "total_trades": len(trades_data)
        },
        "chart_data": chart_data,
        "trades": trades_data
    }