---
title: AlgoQuant Backend API
emoji: 🚀
colorFrom: blue
colorTo: green
sdk: docker
pinned: false
license: mit
---

# AlgoQuant Backend API 🚀

Production-grade FastAPI backend for algorithmic cryptocurrency trading with AI-powered strategies.

## Features

- 🤖 **HMM-SVR Walk-Forward Strategy** - Zero lookahead bias backtesting
- 📊 **Pairs Trading** - Statistical arbitrage (ETH/BTC)
- 💼 **Paper Trading** - Simulated trading with $10,000 starting capital
- 🔒 **Secure Auth** - JWT authentication with bcrypt
- ⚡ **Real-Time Data** - Binance Testnet + Yahoo Finance

## API Documentation

Once deployed, access the interactive API docs at:
- **Swagger UI:** `https://your-space-name.hf.space/docs`
- **ReDoc:** `https://your-space-name.hf.space/redoc`

## Endpoints

### Authentication
- `POST /signup` - Create new user account
- `POST /login` - Get JWT access token

### Trading
- `POST /backtest` - Run strategy backtesting
- `POST /start-live-trading` - Start simulated trading session
- `POST /stop-live-trading/{session_id}` - Stop trading session
- `GET /portfolio` - Get user portfolio balance
- `GET /trading-sessions` - List all trading sessions
- `GET /trades` - Get trade history

### Data
- `GET /price/{ticker}` - Get current price for ticker
- `GET /dashboard` - Get dashboard metrics

## Environment Variables

Required for production:
```bash
DATABASE_URL=postgresql://user:password@host:5432/dbname
SECRET_KEY=your-secret-key-here
```

## Tech Stack

- **FastAPI** - Modern async web framework
- **PostgreSQL** - Production database
- **SQLModel** - SQL ORM with type safety
- **scikit-learn** - Machine learning
- **hmmlearn** - Hidden Markov Models
- **yfinance** - Free market data

## Local Development

```bash
# Install dependencies
pip install -r requirements.txt

# Train HMM model
python train_hmm_model.py

# Run server
uvicorn main:app --reload --port 8000
```

## License

MIT License - See LICENSE for details

---

**Built with 🧠 for quantitative traders**

*Part of the AlgoQuant AI-Powered Trading Platform*
