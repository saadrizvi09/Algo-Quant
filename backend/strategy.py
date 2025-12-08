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
    test_df['Position'] = np.where((test_df['Signal'] == 1) & (test_df['Regime'] != high_vol_state), 1.0, 0.0)
    
    # Returns Calculation
    test_df['Simple_Returns'] = test_df['Close'].pct_change()
    test_df['Strategy_Returns'] = test_df['Position'].shift(1) * test_df['Simple_Returns']
    
    # --- CUMULATIVE CURVES (Normalized to 1.0 start) ---
    test_df['Strategy_Equity'] = (1 + test_df['Strategy_Returns'].fillna(0)).cumprod()
    test_df['BuyHold_Equity'] = (1 + test_df['Simple_Returns'].fillna(0)).cumprod()

    # 4. JSON Response
    chart_data = []
    for date, row in test_df.iterrows():
        chart_data.append({
            "date": date.strftime('%Y-%m-%d'),
            "strategy": row['Strategy_Equity'],
            "buy_hold": row['BuyHold_Equity'],
            "regime": int(row['Regime'])
        })

    # Metrics
    strat_total = test_df['Strategy_Equity'].iloc[-1] - 1
    bh_total = test_df['BuyHold_Equity'].iloc[-1] - 1

    return {
        "metrics": {
            "strategy_return": f"{strat_total:.2%}",
            "buy_hold_return": f"{bh_total:.2%}",
            "final_value": f"${test_df['Strategy_Equity'].iloc[-1] * 10000:.2f}"
        },
        "chart_data": chart_data
    }