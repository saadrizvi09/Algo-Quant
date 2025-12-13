# 🚀 AlgoQuant - AI-Powered Crypto Trading Platform

<div align="center">

![AlgoQuant Banner](https://img.shields.io/badge/AlgoQuant-Trading%20Platform-00d4ff?style=for-the-badge&logo=bitcoin&logoColor=white)

[![License](https://img.shields.io/badge/license-MIT-blue.svg?style=flat-square)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.8+-3776AB?style=flat-square&logo=python&logoColor=white)](https://python.org)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.0+-3178C6?style=flat-square&logo=typescript&logoColor=white)](https://www.typescriptlang.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.124-009688?style=flat-square&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![Next.js](https://img.shields.io/badge/Next.js-15.0-000000?style=flat-square&logo=next.js&logoColor=white)](https://nextjs.org/)

**Institutional-grade algorithmic trading platform with real-time backtesting, AI-powered strategies, and paper trading**

[Features](#-features) • [Quick Start](#-quick-start) • [Documentation](#-documentation) • [Strategies](#-trading-strategies)

</div>

---

## 📋 Table of Contents

- [Overview](#-overview)
- [Features](#-features)
- [Technology Stack](#-technology-stack)
- [Quick Start](#-quick-start)
- [Trading Strategies](#-trading-strategies)
- [Architecture](#-architecture)
- [Configuration](#-configuration)
- [Troubleshooting](#-troubleshooting)
- [Contributing](#-contributing)
- [License](#-license)

---

## 🎯 Overview

**AlgoQuant** is a full-stack algorithmic trading platform that combines machine learning, quantitative finance, and modern web technologies to provide a comprehensive trading solution. Built for traders who want to backtest strategies, execute paper trades, and analyze performance without risking real capital.

### Why AlgoQuant?

- ✅ **100% Free** - No paid APIs or subscriptions required
- 🤖 **AI-Powered** - Hidden Markov Models for regime detection
- 📊 **Real-Time Data** - Live price feeds from Binance Testnet & Yahoo Finance
- 💼 **Paper Trading** - Start with $10,000 virtual capital
- 📈 **Multiple Strategies** - HMM Regime Filter, Pairs Trading, and more
- 🔒 **Secure** - JWT authentication with bcrypt encryption
- 🚀 **Production-Ready** - Fully tested and bug-free

---

## ✨ Features

### 🎯 Trading Features

| Feature | Description |
|---------|-------------|
| **Live Trading Simulation** | Execute trades in real-time with simulated wallet |
| **Strategy Backtesting** | Test historical performance with detailed metrics |
| **Multiple Strategies** | HMM Regime Filter, Pairs Trading (ETH/BTC) |
| **Portfolio Management** | Per-user portfolios with $10,000 starting capital |
| **Real-Time Price Data** | Binance Testnet + Yahoo Finance fallback |
| **Trade Execution** | 10-second interval automated trading |
| **Position Tracking** | Monitor LONG/SHORT positions in real-time |
| **P&L Calculation** | Accurate profit/loss tracking per session |

### 🤖 AI & Machine Learning

- **Hidden Markov Models (HMM)** - 3-state Gaussian HMM for market regime detection
- **Regime Filtering** - Trade only in favorable market conditions
- **Z-Score Analysis** - Statistical mean reversion for pairs trading
- **EMA Crossover** - Exponential Moving Average signals
- **Volatility Detection** - Avoid high-volatility regimes

### 💻 Platform Features

- **🔐 Authentication** - Secure JWT-based login/signup
- **📊 Dashboard** - Portfolio overview, recent trades, active sessions
- **🎨 Modern UI** - Beautiful dark theme with Tailwind CSS
- **📱 Responsive** - Works on desktop, tablet, and mobile
- **⚡ Real-Time Updates** - Auto-refresh every 30 seconds
- **📈 Charts & Metrics** - Visual portfolio performance tracking

---

## 🛠 Technology Stack

### Backend

```
🐍 Python 3.8+
⚡ FastAPI - Modern async web framework
🗄️  PostgreSQL - Production database
🔍 SQLModel - SQL ORM with type safety
🤖 scikit-learn - Machine learning
📊 hmmlearn - Hidden Markov Models
📈 yfinance - Free market data
🔐 python-jose - JWT authentication
🔒 passlib - Password hashing
⏰ APScheduler - Background job scheduler
```

### Frontend

```
⚛️  React 18 / Next.js 15
📘 TypeScript 5.0+
🎨 Tailwind CSS - Utility-first styling
🎯 Lucide Icons - Beautiful icon set
🔥 Hot Reload - Instant development feedback
```

### DevOps & Tools

```
🐳 Docker-ready architecture
🔄 Git version control
📦 pip & npm package managers
🧪 Built-in testing support
📝 Comprehensive logging
```

---

## 🚀 Quick Start

### Prerequisites

- **Python 3.8+** installed
- **Node.js 18+** and npm installed
- **PostgreSQL** database running
- **Git** for version control

### Installation

1. **Clone the Repository**

```bash
git clone https://github.com/yourusername/algoquant.git
cd algoquant
```

2. **Backend Setup**

```bash
cd backend

# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Configure environment variables
# Create .env file with:
DATABASE_URL=postgresql://user:password@localhost/algoquant
BINANCE_API_KEY=your_testnet_key_here
BINANCE_SECRET_KEY=your_testnet_secret_here

# Train HMM model (optional but recommended)
python train_hmm_model.py
```

3. **Frontend Setup**

```bash
cd ../frontend

# Install dependencies
npm install

# Start development server
npm run dev
```

4. **Start the Application**

```bash
# Terminal 1 - Backend (from backend/)
uvicorn main:app --reload

# Terminal 2 - Frontend (from frontend/)
npm run dev
```

5. **Access the Platform**

Open your browser and navigate to:
- **Frontend**: http://localhost:3000
- **Backend API Docs**: http://127.0.0.1:8000/docs

### 🎉 First Steps

1. **Sign Up** - Create your account at http://localhost:3000
2. **Login** - Access the dashboard with your credentials
3. **Check Portfolio** - You start with $10,000 USDT
4. **Start Trading** - Navigate to Live Trading and select a strategy
5. **Monitor Performance** - View trades, P&L, and sessions in real-time

---

## 🎲 Trading Strategies

### 1. HMM Regime Filter Strategy

A Hidden Markov Model (HMM) is a powerful statistical model used to describe the evolution of observable events that depend on internal factors, which are not directly observable. In financial markets, these unobservable factors are called "market regimes."

**Core Concept:**

The market does not behave the same way all the time. It switches between different states, or "regimes," such as:
- **Low-Volatility / Bullish Trend:** Stable upward price movements.
- **High-Volatility / Choppy:** Unpredictable, risky price action with no clear trend.
- **Bearish Trend:** Stable downward price movements.

An HMM can be trained on market data (like price returns or volatility) to learn the characteristics of these hidden regimes. Once trained, the model can analyze current market data and predict which regime the market is currently in.

**How This Strategy Uses HMM:**

1.  **Regime Identification:** A 3-state Gaussian HMM is trained on historical price data to identify three distinct market regimes based on their volatility and return characteristics.
2.  **Signal Generation:** A classic technical indicator, the EMA (Exponential Moving Average) crossover (12-period vs. 26-period), is used to generate raw buy/sell signals.
3.  **AI-Powered Filtering:** This is the key step. The raw signal from the EMA crossover is **filtered** based on the current regime predicted by the HMM.
    - If the HMM detects a **favorable regime** (e.g., low-volatility, trending), it allows the trade signal to pass through.
    - If the HMM detects an **unfavorable regime** (e.g., high-volatility, sideways market), it **blocks** the trade signal.
4.  **Goal:** The primary goal is not just to generate trades, but to **intelligently avoid trading in bad market conditions**. This helps to reduce losses from false signals and improve the risk-adjusted return of the underlying EMA strategy.

**Parameters**:
- `short_window`: 12 (default) - For the short-term EMA.
- `long_window`: 26 (default) - For the long-term EMA.
- Model: A pre-trained HMM is loaded to provide the regime predictions.

### 2. Pairs Trading (ETH/BTC)

**Description**: Statistical arbitrage strategy that trades the mean reversion of the ETH/BTC price ratio.

**How It Works**:
- Tracks ETH/BTC ratio over 60-period rolling window
- Calculates Z-score of current ratio
- **BUY** when Z-score < -2.0 (ratio undervalued, expect reversion up)
- **SELL** when Z-score crosses 0 (mean reversion complete)
- Stop loss when Z-score > 3.0

**Parameters**:
- `window`: 60 periods (default)
- `threshold`: 2.0 Z-score (default)

**Entry Logic**:
```
Z-Score < -2.0  →  BUY (go LONG on ETH)
Z-Score > +2.0  →  Avoid (ratio overvalued)
```

**Exit Logic**:
```
Z-Score crosses 0  →  SELL (mean reversion)
Z-Score > 3.0      →  SELL (stop loss)
```

---

## 🏗 Architecture

### System Overview

```
┌─────────────────────────────────────────────────────────────┐
│                      Client Browser                         │
│                    (Next.js + React)                        │
└────────────────────────┬────────────────────────────────────┘
                         │ HTTP/REST
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                   FastAPI Backend                           │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │   Auth API   │  │  Trading API │  │  Data API    │     │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘     │
│         │                  │                  │              │
│         ▼                  ▼                  ▼              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │     JWT      │  │  Strategy    │  │  Simulated   │     │
│  │  Validator   │  │  Handlers    │  │  Exchange    │     │
│  └──────────────┘  └──────┬───────┘  └──────┬───────┘     │
│                            │                  │              │
│                            ▼                  ▼              │
│                    ┌────────────────────────────┐           │
│                    │   APScheduler (10s jobs)   │           │
│                    └────────────┬───────────────┘           │
└─────────────────────────────────┼───────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────┐
│                   PostgreSQL Database                        │
│  - Users (auth)                                             │
│  - PortfolioAsset (balances)                                │
│  - TradingSession (active sessions)                         │
│  - Trade (execution history)                                │
└─────────────────────────────────────────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────┐
│                  External Data Sources                       │
│  - Binance Testnet (free, real-time prices)                │
│  - Yahoo Finance (free, fallback data)                      │
└─────────────────────────────────────────────────────────────┘
```

### Data Flow

1. **User Authentication**
   - User logs in → JWT token issued
   - Token stored in localStorage
   - Sent with every API request

2. **Trading Session**
   - User selects strategy & parameters
   - Backend creates `SimulatedTradingSession`
   - APScheduler job runs every 10 seconds
   - Strategy handler generates signals
   - Trades executed in simulated exchange
   - Portfolio updated in database

3. **Price Fetching**
   - Primary: Binance Testnet API
   - Fallback: Yahoo Finance (yfinance)
   - Automatic fallback on API failure

4. **Signal Generation**
   - Price → Strategy Handler → Signal (BUY/SELL/HOLD)
   - HMM: Price → EMA + Regime → Signal
   - Pairs: ETH Price + BTC Price → Z-Score → Signal

---

## ⚙️ Configuration

### Environment Variables

Create a `.env` file in the `backend/` directory:

```env
# Database
DATABASE_URL=postgresql://username:password@localhost:5432/algoquant

# Binance Testnet (Free - Get from https://testnet.binance.vision/)
BINANCE_API_KEY=your_testnet_api_key_here
BINANCE_SECRET_KEY=your_testnet_secret_key_here

# JWT Authentication
SECRET_KEY=your_super_secret_key_change_this_in_production
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=43200

# Optional: Logging Level
LOG_LEVEL=INFO
```

### Trading Parameters

Edit in `backend/strategy_handlers.py`:

```python
# HMM Strategy
short_window = 12  # EMA short period
long_window = 26   # EMA long period

# Pairs Strategy
window = 60        # Rolling window for Z-score
threshold = 2.0    # Entry/exit threshold
```

---

## 🐛 Troubleshooting

### Common Issues

#### 1. "Failed to fetch portfolio"

**Solution**:
```bash
# Check if backend is running
curl http://127.0.0.1:8000/docs

# Verify token in localStorage
# Open browser console and run:
localStorage.getItem('token')

# Clear cache and login again
localStorage.clear()
```

#### 2. "Session not found" (404)

**Cause**: Session already expired or stopped

**Solution**:
- Sessions automatically cleanup after expiration
- Refresh the page to see updated session list
- Check logs for detailed error messages

#### 3. Database Connection Error

**Solution**:
```bash
# Check PostgreSQL is running
# Windows:
net start postgresql-x64-14

# Linux:
sudo systemctl start postgresql

# Verify connection
psql -U username -d algoquant
```

#### 4. Missing Dependencies

**Solution**:
```bash
# Backend
cd backend
pip install -r requirements.txt

# Frontend
cd frontend
npm install
```

### Debug Mode

Enable detailed logging:

```python
# backend/main.py
import logging
logging.basicConfig(level=logging.DEBUG)
```

Check logs for:
- `[SimTrading]` - Trading session events
- `[SimEx]` - Exchange operations
- `[StrategyHandler]` - Signal generation
- `[Portfolio]` - Balance updates

---

## 💰 Cost Breakdown

| Component | Service | Cost |
|-----------|---------|------|
| Price Data (Primary) | Binance Testnet | **FREE** ✅ |
| Price Data (Fallback) | Yahoo Finance | **FREE** ✅ |
| Database | PostgreSQL (Local) | **FREE** ✅ |
| Backend | FastAPI + Python | **FREE** ✅ |
| Frontend | Next.js + React | **FREE** ✅ |
| ML Models | scikit-learn, hmmlearn | **FREE** ✅ |
| Hosting | Local Development | **FREE** ✅ |
| **TOTAL** | | **$0.00** 🎉 |

---

## 📚 Additional Resources

### Documentation
- [FastAPI Docs](https://fastapi.tiangolo.com/)
- [Next.js Docs](https://nextjs.org/docs)
- [SQLModel Guide](https://sqlmodel.tiangolo.com/)
- [Binance Testnet](https://testnet.binance.vision/)

### Learning Resources
- [Algorithmic Trading Tutorial](https://www.quantstart.com/)
- [Hidden Markov Models](https://www.youtube.com/watch?v=kqSzLo9fenk)
- [Pairs Trading Explained](https://www.investopedia.com/terms/p/pairstrade.asp)
- [Z-Score Analysis](https://www.investopedia.com/terms/z/zscore.asp)

---

## 🤝 Contributing

We welcome contributions! Here's how you can help:

### Development Setup

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Run tests (if available)
5. Commit your changes (`git commit -m 'Add amazing feature'`)
6. Push to the branch (`git push origin feature/amazing-feature`)
7. Open a Pull Request

---

## 📄 License

This project is licensed under the **MIT License** - see the [LICENSE](LICENSE) file for details.

---

## 🚀 Roadmap

### Version 2.1 (Q1 2026)
- [ ] More trading strategies (MACD, RSI, Bollinger Bands)
- [ ] Advanced portfolio analytics
- [ ] Export trade history to CSV
- [ ] Risk management tools

### Version 2.2 (Q2 2026)
- [ ] Multi-timeframe analysis
- [ ] Custom strategy builder
- [ ] Social trading features
- [ ] Mobile app (React Native)

---

<div align="center">

**Made with 🧠 by Algorithmic Traders, for Algorithmic Traders**

[⬆ Back to Top](#-algoquant---ai-powered-crypto-trading-platform)

</div>
