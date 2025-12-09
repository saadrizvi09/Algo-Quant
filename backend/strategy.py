import yfinance as yf
import pandas as pd
import numpy as np
from hmmlearn.hmm import GaussianHMM
from datetime import datetime

def fetch_data(ticker, start_date, end_date):
    df = yf.download(ticker, start=start_date, end=end_date, progress=False)
    if df.empty: return None
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    return df.dropna()

def generate_trade_log(df):
    """
    Scans the backtest dataframe to identify individual trade cycles.
    A 'Trade' is defined as a period where Position > 0.
    """
    trades = []
    in_trade = False
    entry_date = None
    entry_price = 0
    trade_returns = []
    
    # We iterate through the dataframe
    for date, row in df.iterrows():
        pos = row['Position']
        close_price = row['Close']
        
        # Check for Entry (Position goes from 0 to > 0)
        if pos > 0 and not in_trade:
            in_trade = True
            entry_date = date
            entry_price = close_price
            trade_returns = [row['Strategy_Returns']]
            
        # Check for adjustments while in trade
        elif pos > 0 and in_trade:
            trade_returns.append(row['Strategy_Returns'])
            
        # Check for Exit (Position goes to 0 while we were in a trade)
        elif pos == 0 and in_trade:
            in_trade = False
            exit_date = date
            exit_price = close_price
            
            # Calculate compounded return for this specific trade period
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

    # Handle case where trade is still open at end of data
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
    # 1. Fetch Data (Get extra history for training)
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

    # 3. Backtest
    X_test = test_df[['Log_Returns', 'Volatility']].values * 100
    test_df['Regime'] = hmm_model.predict(X_test)
    
    # Signals
    test_df['Signal'] = np.where(test_df['EMA_Short'] > test_df['EMA_Long'], 1, 0)
    
    # Strategy Position: Block trades if High Volatility Regime
    test_df['Position'] = np.where(
        (test_df['Signal'] == 1) & (test_df['Regime'] != high_vol_state), 
        1.0, 
        0.0
    )
    
    # Returns Calculation
    test_df['Simple_Returns'] = test_df['Close'].pct_change()
    test_df['Strategy_Returns'] = test_df['Position'].shift(1) * test_df['Simple_Returns']
    
    # --- CUMULATIVE CURVES (Normalized to 1.0 start) ---
    test_df['Strategy_Equity'] = (1 + test_df['Strategy_Returns'].fillna(0)).cumprod()
    test_df['BuyHold_Equity'] = (1 + test_df['Simple_Returns'].fillna(0)).cumprod()

    # 4. Generate Trade Log
    test_df['Position'] = test_df['Position'].shift(1).fillna(0)  # Align position for trade detection
    trades_list = generate_trade_log(test_df)
    
    # Convert trades to JSON-serializable format
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
            "date": date.strftime('%Y-%m-%d'),
            "strategy": float(row['Strategy_Equity']),
            "buy_hold": float(row['BuyHold_Equity']),
            "regime": int(row['Regime'])
        })

    # 6. Calculate Advanced Metrics
    strat_total = test_df['Strategy_Equity'].iloc[-1] - 1
    bh_total = test_df['BuyHold_Equity'].iloc[-1] - 1
    
    # Sharpe Ratio
    strategy_returns = test_df['Strategy_Returns'].dropna()
    sharpe = (strategy_returns.mean() / strategy_returns.std()) * np.sqrt(252) if strategy_returns.std() != 0 else 0
    
    # Max Drawdown
    rolling_max = test_df['Strategy_Equity'].cummax()
    drawdown = (test_df['Strategy_Equity'] - rolling_max) / rolling_max
    max_drawdown = drawdown.min()
    
    # Win Rate
    winning_trades = [t for t in trades_list if t['trade_pnl'] > 0]
    closed_trades = [t for t in trades_list if t['exit_date'] != test_df.index[-1]]
    win_rate = (len(winning_trades) / len(closed_trades) * 100) if closed_trades else 0

    return {
        "metrics": {
            "strategy_return": f"{strat_total:.2%}",
            "buy_hold_return": f"{bh_total:.2%}",
            "final_value": f"${test_df['Strategy_Equity'].iloc[-1] * 10000:.2f}",
            "sharpe_ratio": f"{sharpe:.2f}",
            "max_drawdown": f"{max_drawdown:.2%}",
            "win_rate": f"{win_rate:.1f}%",
            "total_trades": len(trades_data)
        },
        "chart_data": chart_data,
        "trades": trades_data
    }