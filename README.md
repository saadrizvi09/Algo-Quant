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

The market does not behave the same way all the time. It switches between different states, or "regimes." This strategy uses a 3-state Gaussian HMM trained on historical log returns and volatility to identify three distinct market regimes:

1.  **Low-Volatility, Ranging/Consolidating:** The market is stable but has no clear direction. This is often a neutral state.
2.  **Trending (Bullish or Bearish):** The market is moving with a clear directional bias and moderate volatility. These are often the most profitable conditions for trend-following strategies.
3.  **High-Volatility, Choppy:** The market is experiencing erratic, unpredictable price swings. Trading in this regime is extremely risky and often leads to losses from false signals.

**How This Strategy Uses HMM:**

The strategy combines a classic technical indicator with the AI-powered regime detection of the HMM.

1.  **Signal Generation:** A standard EMA (Exponential Moving Average) crossover (12-period vs. 26-period) is used to generate raw buy/sell signals. A bullish crossover is a potential "buy" signal.
2.  **AI-Powered Filtering:** This is the key innovation. The raw signal from the EMA crossover is **filtered** based on the current regime predicted by the HMM.
    - If the HMM detects a **Trending** regime and a bullish crossover occurs, the trade signal is **allowed**.
    - If the HMM detects a **High-Volatility** or **Low-Volatility/Ranging** regime, the trade signal is **blocked**, regardless of the EMA crossover.
3.  **Goal:** The primary goal is to **intelligently avoid trading in unfavorable market conditions**. This helps to filter out noise, reduce losses from false signals, and improve the overall quality and risk-adjusted return of the trading strategy.

**Visualizing the Flow:**
```
                     ┌──────────────────┐
                     │ Raw Price Data   │
                     └────────┬─────────┘
                              │
            ┌─────────────────┴─────────────────┐
            │                                   │
            ▼                                   ▼
┌──────────────────────┐             ┌─────────────────────┐
│   EMA Crossover      │             │   HMM Prediction    │
│ (12 vs 26 periods)   │             │ (Log Returns, Vol)  │
└──────────┬───────────┘             └──────────┬──────────┘
           │                                    │
           │       ┌──────────────────┐         │
           ├───────►   Regime Filter  ◄─────────┤
           │       └──────────────────┘         │
           │                                    │
           ▼                                    ▼
┌──────────────────────┐          ┌───────────────────────────┐
│ "BUY" Signal if EMAs │          │  Current Market Regime:   │
│ cross bullishly      │          │  (Trending, High-Vol, etc)│
└──────────────────────┘          └───────────────────────────┘
                              │
                              ▼
                     ┌──────────────────┐
                     │  Final Decision  │
                     │  (Trade or Wait) │
                     └──────────────────┘
```

**Parameters**:
- `short_window`: 12 (default) - For the short-term EMA.
- `long_window`: 26 (default) - For the long-term EMA.
- `n_states`: 3 (default) - The number of hidden states in the HMM.

### 2. Pairs Trading (ETH/BTC)

**Description**: Statistical arbitrage strategy that trades the mean reversion of the ETH/BTC price ratio.

**How It Works**:
- Tracks ETH/BTC ratio over a 60-period rolling window.
- Calculates the Z-score of the current ratio relative to its rolling mean.
- A Z-score indicates how many standard deviations the current ratio is from its average.
- **Go LONG** the pair (Buy ETH, Sell BTC) when the Z-score is significantly low (e.g., < -1.5), indicating the ratio is undervalued and likely to rise.
- **Go SHORT** the pair (Sell ETH, Buy BTC) when the Z-score is significantly high (e.g., > 1.5), indicating the ratio is overvalued and likely to fall.
- **Exit** the position when the Z-score returns to its mean (Z-score crosses 0), capturing the profit from the mean reversion.

**Parameters**:
- `window`: 60 periods (default)
- `threshold`: 1.5 Z-score (default) for entry.

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
   - HMM: Price → EMA + Regime → Signal
   - Pairs: ETH Price + BTC Price → Z-Score → Signal

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
