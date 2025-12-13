"""
Train HMM Model for Live Trading
Run this script once to generate the hmm_model.pkl file
"""
from strategy import train_models_and_backtest

# Train HMM model using recent BTC data
print("Training HMM model for live trading...")
print("=" * 60)

result = train_models_and_backtest(
    ticker="BTC-USD",
    start_date="2024-01-01",  # Backtest period
    end_date="2024-12-14",     # Today
    short_window=12,
    long_window=26,
    n_states=3
)

if "error" in result:
    print(f"❌ Error: {result['error']}")
else:
    print("\n" + "=" * 60)
    print("✅ Model training complete!")
    print("\nBacktest Results:")
    print(f"  Strategy Return: {result['metrics']['strategy_return']}")
    print(f"  Buy & Hold Return: {result['metrics']['buy_hold_return']}")
    print(f"  Sharpe Ratio: {result['metrics']['sharpe_ratio']}")
    print(f"  Max Drawdown: {result['metrics']['max_drawdown']}")
    print(f"  Win Rate: {result['metrics']['win_rate']}")
    print(f"  Total Trades: {result['metrics']['total_trades']}")
    print("\n📁 Model saved to: backend/hmm_model.pkl")
    print("   Ready for live trading!")
