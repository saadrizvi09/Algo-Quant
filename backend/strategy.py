import yfinance as yf
import pandas as pd
import numpy as np
from hmmlearn.hmm import GaussianHMM
from sklearn.svm import SVR
from sklearn.preprocessing import StandardScaler
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
    Includes leverage information.
    """
    trades = []
    in_trade = False
    entry_date = None
    entry_price = 0
    trade_returns = []
    avg_leverage = []
    
    for date, row in df.iterrows():
        pos = row['Final_Position']
        close_price = row['Close']
        lev = row['Position_Size']
        
        # Check for Entry
        if pos > 0 and not in_trade:
            in_trade = True
            entry_date = date
            entry_price = close_price
            trade_returns = [row['Strategy_Returns']]
            avg_leverage = [lev]
            
        # Check for adjustments while in trade
        elif pos > 0 and in_trade:
            trade_returns.append(row['Strategy_Returns'])
            avg_leverage.append(lev)
            
        # Check for Exit
        elif pos == 0 and in_trade:
            in_trade = False
            exit_date = date
            exit_price = close_price
            
            # Calculate compounded return
            cum_trade_ret = np.prod([1 + r for r in trade_returns]) - 1
            mean_lev = np.mean(avg_leverage)
            
            trades.append({
                'entry_date': entry_date,
                'exit_date': exit_date,
                'entry_price': entry_price,
                'exit_price': exit_price,
                'duration_days': len(trade_returns),
                'avg_leverage': mean_lev,
                'trade_pnl': cum_trade_ret,
                'trade_pnl_percent': cum_trade_ret * 100
            })
            trade_returns = []
            avg_leverage = []

    # Handle Open Trade
    if in_trade:
        cum_trade_ret = np.prod([1 + r for r in trade_returns]) - 1
        mean_lev = np.mean(avg_leverage)
        trades.append({
            'entry_date': entry_date,
            'exit_date': df.index[-1],
            'entry_price': entry_price,
            'exit_price': df.iloc[-1]['Close'],
            'duration_days': len(trade_returns),
            'avg_leverage': mean_lev,
            'trade_pnl': cum_trade_ret,
            'trade_pnl_percent': cum_trade_ret * 100
        })

    return trades


def train_hmm_model(train_df, n_states=3):
    """
    Trains HMM on historical data and sorts states by volatility.
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
        avg_vol = X_train[hidden_states == i, 1].mean()
        state_vol.append((i, avg_vol))
    
    # Sort states by volatility: State 0 = Lowest, State N-1 = Highest
    state_vol.sort(key=lambda x: x[1])
    mapping = {old: new for new, (old, _) in enumerate(state_vol)}
    
    return model, mapping


def train_svr_model(train_df):
    """
    Trains SVR to predict next day's volatility.
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

def train_models_and_backtest(ticker, start_date, end_date, short_window, long_window, n_states):
    """
    HMM-SVR Honest Leverage Strategy (Walk-Forward):
    Uses strict walk-forward simulation to eliminate lookahead bias.
    Each prediction uses only data available up to that point in time.
    """
    # 1. Fetch Data (extended training period)
    train_start = pd.Timestamp(start_date) - pd.DateOffset(years=4) 
    df = fetch_data(ticker, train_start, end_date)
    
    if df is None or len(df) < 200:
        return {"error": "Not enough data"}

    # Feature Engineering
    df['Log_Returns'] = np.log(df['Close'] / df['Close'].shift(1))
    df['Volatility'] = df['Log_Returns'].rolling(window=10).std()
    
    # Downside volatility (std of negative returns only)
    df['Downside_Returns'] = df['Log_Returns'].apply(lambda x: x if x < 0 else 0)
    df['Downside_Vol'] = df['Downside_Returns'].rolling(10).std()
    
    # SVR target: next day's volatility
    df['Target_Next_Vol'] = df['Volatility'].shift(-1)
    df = df.dropna()

    # Split Data
    train_df = df[df.index < pd.Timestamp(start_date)].copy()
    test_df = df[df.index >= pd.Timestamp(start_date)].copy()

    if len(train_df) < 365 or len(test_df) < 10: 
        return {"error": "Data split error. Adjust dates."}

    print(f"✅ Training on {len(train_df)} days, Testing on {len(test_df)} days")

    # 2. Train HMM (sorted by volatility)
    print("🔄 Training HMM on historical data...")
    hmm_model, state_mapping = train_hmm_model(train_df, n_states=n_states)
    
    # Predict regimes on train and remap
    X_train = train_df[['Log_Returns', 'Volatility']].values * 100
    train_regimes = hmm_model.predict(X_train)
    train_df['Regime'] = [state_mapping[s] for s in train_regimes]
    
    # Calculate average training volatility for risk ratio
    avg_train_vol = train_df['Volatility'].mean()
    
    # 3. Train SVR
    print("🔄 Training SVR for volatility prediction...")
    svr_model, svr_scaler = train_svr_model(train_df)
    
    # Save models for live trading
    model_data = {
        'hmm_model': hmm_model,
        'svr_model': svr_model,
        'svr_scaler': svr_scaler,
        'state_mapping': state_mapping,
        'avg_train_vol': avg_train_vol,
        'n_states': n_states,
        'trained_at': datetime.now().isoformat()
    }
    model_path = os.path.join(os.path.dirname(__file__), 'hmm_model.pkl')
    joblib.dump(model_data, model_path)
    print(f"✅ HMM-SVR Model saved to {model_path}")
    print(f"   States: 0=Low Vol, {n_states-1}=High Vol (Crash)")
    print(f"   Avg training volatility: {avg_train_vol:.6f}")
    
    # --- HONEST WALK-FORWARD BACKTEST ---
    print("\n🔄 Running Walk-Forward Simulation (No Lookahead Bias)...")
    
    # Prepare containers for honest predictions
    honest_regimes = []
    honest_predicted_vols = []
    honest_ema_short = []
    honest_ema_long = []
    
    # Concatenate for sliding window access
    all_data = pd.concat([train_df, test_df])
    start_idx = len(train_df)
    total_steps = len(test_df)
    lookback_window = 252  # 1 year lookback for regime detection
    
    # Walk forward one day at a time
    for i in range(total_steps):
        # Progress indicator
        if i % 50 == 0 and i > 0:
            print(f"   Processing day {i}/{total_steps}...")
        
        # Current position in full dataset
        curr_pointer = start_idx + i
        window_start = max(0, curr_pointer - lookback_window)
        
        # Slice history up to current day (inclusive)
        history_slice = all_data.iloc[window_start : curr_pointer + 1]
        
        # A. Honest Regime Detection (uses only history)
        X_slice = history_slice[['Log_Returns', 'Volatility']].values * 100
        try:
            hidden_states_slice = hmm_model.predict(X_slice)
            current_state_raw = hidden_states_slice[-1]
            current_state = state_mapping.get(current_state_raw, current_state_raw)
        except:
            current_state = 1  # Fallback to neutral
        
        honest_regimes.append(current_state)
        
        # B. Honest Volatility Prediction (uses today's data to predict tomorrow)
        row = test_df.iloc[i]
        svr_features = np.array([[
            row['Log_Returns'], 
            row['Volatility'], 
            row['Downside_Vol'], 
            current_state
        ]])
        
        svr_feat_scaled = svr_scaler.transform(svr_features)
        pred_vol = svr_model.predict(svr_feat_scaled)[0]
        honest_predicted_vols.append(pred_vol)
        
        # C. Honest EMA Calculation (uses only history)
        ema_short_val = history_slice['Close'].ewm(span=short_window).mean().iloc[-1]
        ema_long_val = history_slice['Close'].ewm(span=long_window).mean().iloc[-1]
        honest_ema_short.append(ema_short_val)
        honest_ema_long.append(ema_long_val)
    
    print(f"✅ Walk-forward simulation complete!")
    
    # Assign honest predictions to test dataframe
    test_df['Regime'] = honest_regimes
    test_df['Predicted_Vol'] = honest_predicted_vols
    test_df['EMA_Short'] = honest_ema_short
    test_df['EMA_Long'] = honest_ema_long
    
    # 4. Generate trading signals (EMA crossover)
    test_df['Signal'] = np.where(test_df['EMA_Short'] > test_df['EMA_Long'], 1, 0)
    test_df['Risk_Ratio'] = test_df['Predicted_Vol'] / avg_train_vol
    
    # 5. Calculate leverage based on regime and risk
    test_df['Position_Size'] = 1.0  # Default
    
    # Boost: 3x in certainty (low vol + low risk)
    cond_safe = (test_df['Regime'] == 0)
    cond_low_risk = (test_df['Risk_Ratio'] < 0.5)
    test_df.loc[cond_safe & cond_low_risk, 'Position_Size'] = 3.0
    
    # Cut: 0x in crash regime
    cond_crash = (test_df['Regime'] == (n_states - 1))
    test_df.loc[cond_crash, 'Position_Size'] = 0.0
    
    # 6. Calculate final position (signal today decides position tomorrow)
    test_df['Final_Position'] = (test_df['Signal'] * test_df['Position_Size']).shift(1)
    
    # 7. Returns Calculation
    test_df['Simple_Returns'] = test_df['Close'].pct_change()
    test_df['Strategy_Returns'] = test_df['Final_Position'] * test_df['Simple_Returns']
    
    # --- CUMULATIVE CURVES ---
    test_df['Strategy_Equity'] = (1 + test_df['Strategy_Returns'].fillna(0)).cumprod()
    test_df['BuyHold_Equity'] = (1 + test_df['Simple_Returns'].fillna(0)).cumprod()
    test_df.dropna(inplace=True)

    # 8. Generate Trade Log with leverage info
    trades_list = generate_trade_log(test_df)
    
    trades_data = []
    for trade in trades_list:
        trades_data.append({
            'entry_date': trade['entry_date'].strftime('%Y-%m-%d'),
            'exit_date': trade['exit_date'].strftime('%Y-%m-%d'),
            'entry_price': float(trade['entry_price']),
            'exit_price': float(trade['exit_price']),
            'duration_days': int(trade['duration_days']),
            'avg_leverage': float(trade['avg_leverage']),
            'trade_pnl': float(trade['trade_pnl']),
            'trade_pnl_percent': float(trade['trade_pnl_percent']),
            'regime': int(test_df.loc[trade['entry_date'], 'Regime']) if trade['entry_date'] in test_df.index else 0
        })

    # 9. JSON Response - Chart Data
    chart_data = []
    for date, row in test_df.iterrows():
        chart_data.append({
            'date': date.strftime('%Y-%m-%d'),
            'strategy': float(row['Strategy_Equity']),
            'buy_hold': float(row['BuyHold_Equity']),
            'regime': int(row['Regime']),
            'leverage': float(row['Position_Size'])
        })

    # 10. Calculate Advanced Metrics
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
    
    # Win Rate Calculation
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
    
    # Average leverage used
    avg_leverage_used = test_df[test_df['Final_Position'] > 0]['Position_Size'].mean() if (test_df['Final_Position'] > 0).any() else 0

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
            "avg_leverage": f"{avg_leverage_used:.2f}x",
            "total_trades": len(trades_data)
        },
        "chart_data": chart_data,
        "trades": trades_data
    }