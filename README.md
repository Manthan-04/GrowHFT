<<<<<<< HEAD
# GrowHFT
High Frequency trading platform.
=======
# 🚀 High Frequency Trading (HFT) Dashboard

A professional-grade algorithmic trading system for the **Indian Stock Market (NSE/BSE)** using the Groww trading platform. Features a modern React dashboard for real-time monitoring and a Python trading engine implementing world-famous trading strategies.

![Trading Dashboard](https://img.shields.io/badge/Status-Production%20Ready-green)
![Python](https://img.shields.io/badge/Python-3.11+-blue)
![TypeScript](https://img.shields.io/badge/TypeScript-5.0+-blue)
![License](https://img.shields.io/badge/License-MIT-yellow)

---

## 📋 Table of Contents

- [Features](#-features)
- [Architecture](#-architecture)
- [Trading Strategies](#-trading-strategies)
- [Money Management](#-money-management)
- [Technical Indicators](#-technical-indicators)
- [Installation](#-installation)
- [Configuration](#-configuration)
- [API Reference](#-api-reference)
- [Database Schema](#-database-schema)
- [Usage](#-usage)
- [Risk Disclaimer](#-risk-disclaimer)

---

## ✨ Features

### Core Capabilities
- **7 Professional Trading Strategies** - Battle-tested algorithms used by institutional traders
- **Multi-Strategy Voting System** - Reduces false signals by requiring strategy consensus
- **Real-time Dashboard** - Monitor trades, P&L, and strategy performance live
- **Professional Money Management** - ATR-based position sizing, stop-loss, take-profit
- **Multi-User Support** - Secure authentication with individual API key management
- **Parallel Stock Trading** - Trade 10+ stocks simultaneously
- **Async Execution** - Non-blocking order execution for speed

### Dashboard Features
- 📊 Real-time P&L tracking
- 📈 Strategy performance metrics
- 📉 Trade history with detailed analytics
- ⚙️ Strategy configuration interface
- 🔐 Secure API key management
- 🌙 Professional dark theme

---

## 🏗 Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        FRONTEND (React)                         │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐             │
│  │  Dashboard  │  │  Strategies │  │   Trades    │             │
│  └─────────────┘  └─────────────┘  └─────────────┘             │
└────────────────────────────┬────────────────────────────────────┘
                             │ REST API
┌────────────────────────────┴────────────────────────────────────┐
│                     BACKEND (Node.js/Express)                    │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐             │
│  │   Routes    │  │   Storage   │  │    Auth     │             │
│  └─────────────┘  └─────────────┘  └─────────────┘             │
└────────────────────────────┬────────────────────────────────────┘
                             │
┌────────────────────────────┴────────────────────────────────────┐
│                    TRADING ENGINE (Python)                       │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐             │
│  │ Strategies  │  │  Indicators │  │Money Manager│             │
│  └─────────────┘  └─────────────┘  └─────────────┘             │
│                          │                                       │
│                    ┌─────┴─────┐                                │
│                    │ Groww API │                                │
│                    └───────────┘                                │
└─────────────────────────────────────────────────────────────────┘
                             │
┌────────────────────────────┴────────────────────────────────────┐
│                      DATABASE (PostgreSQL)                       │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐             │
│  │    Users    │  │  Strategies │  │   Trades    │             │
│  └─────────────┘  └─────────────┘  └─────────────┘             │
└─────────────────────────────────────────────────────────────────┘
```

### Technology Stack

| Layer | Technology | Purpose |
|-------|------------|---------|
| Frontend | React 18, TypeScript, TailwindCSS, Shadcn/UI | User interface |
| Backend | Node.js, Express, Drizzle ORM | API & data management |
| Trading Engine | Python 3.11, TA-Lib, Pandas, NumPy | Strategy execution |
| Database | PostgreSQL | Persistent storage |
| Authentication | Replit Auth (OpenID Connect) | User management |
| Trading API | Groww API | Market data & order execution |

---

## 📈 Trading Strategies

### 1. Moving Average Crossover (Golden Cross / Death Cross)

The most popular trend-following strategy used by institutions worldwide.

```
Signal Logic:
├── BUY:  Short MA crosses ABOVE Long MA (Golden Cross)
└── SELL: Short MA crosses BELOW Long MA (Death Cross)

Default Parameters:
├── Short Window: 20 periods
├── Long Window: 50 periods
└── Type: SMA (can switch to EMA)
```

**Best For:** Trending markets, swing trading
**Win Rate:** 45-55% with proper risk management

---

### 2. RSI Mean Reversion

Classic oscillator strategy exploiting overbought/oversold conditions.

```
Signal Logic:
├── BUY:  RSI crosses below 30 (oversold)
└── SELL: RSI crosses above 70 (overbought)

Default Parameters:
├── RSI Period: 14
├── Overbought Level: 70
└── Oversold Level: 30
```

**Best For:** Range-bound markets, mean reversion
**Win Rate:** 50-60% in ranging conditions

---

### 3. MACD Strategy

Momentum indicator combining trend and oscillator characteristics.

```
Signal Logic:
├── BUY:  MACD line crosses ABOVE Signal line
└── SELL: MACD line crosses BELOW Signal line

Default Parameters:
├── Fast EMA: 12 periods
├── Slow EMA: 26 periods
└── Signal Line: 9 periods
```

**Best For:** Momentum trading, trend confirmation
**Win Rate:** 40-50% (high reward-to-risk ratio)

---

### 4. Bollinger Bands

Volatility-based mean reversion strategy.

```
Signal Logic:
├── BUY:  Price touches/crosses lower band
└── SELL: Price touches/crosses upper band

Default Parameters:
├── Period: 20
└── Standard Deviation: 2.0
```

**Best For:** Volatile markets, breakout confirmation
**Win Rate:** 55-65% in ranging markets

---

### 5. VWAP Strategy

Institutional favorite for intraday trading.

```
Signal Logic:
├── BUY:  Price crosses ABOVE VWAP + Volume confirmation
└── SELL: Price crosses BELOW VWAP

Default Parameters:
└── Volume Threshold: 1.5x average
```

**Best For:** Intraday trading, institutional flow
**Win Rate:** 50-55% with volume filter

---

### 6. SuperTrend

ATR-based trend-following indicator.

```
Signal Logic:
├── BUY:  SuperTrend direction changes to bullish
└── SELL: SuperTrend direction changes to bearish

Default Parameters:
├── ATR Period: 10
└── Multiplier: 3.0
```

**Best For:** Strong trending markets
**Win Rate:** 40-45% (high reward trades)

---

### 7. Stochastic RSI

Combined oscillator for stronger confirmation signals.

```
Signal Logic:
├── BUY:  Both RSI < 30 AND Stochastic < 20
└── SELL: Both RSI > 70 AND Stochastic > 80

Default Parameters:
├── RSI Period: 14
└── Stochastic Period: 14
```

**Best For:** Confirmation signals, reducing false positives
**Win Rate:** 55-60% (higher accuracy)

---

### Multi-Strategy Voting System

The engine combines signals from all active strategies using weighted voting:

```python
Strategy Weights:
├── Moving Average Crossover: 1.0
├── EMA Crossover: 1.0
├── RSI Mean Reversion: 0.8
├── Bollinger Bands: 0.7
├── MACD: 1.0
├── VWAP: 0.9
├── SuperTrend: 1.2
└── Stochastic RSI: 0.8

Signal Threshold: 0.3 (30% agreement required)
```

This approach significantly reduces false signals by requiring multiple strategy confirmation.

---

## 💰 Money Management

### Position Sizing (ATR-Based)

```python
Position Size = Risk Amount / (ATR × 2)

Where:
├── Risk Amount = Capital × 2% (max risk per trade)
└── ATR = 14-period Average True Range
```

### Risk Controls

| Parameter | Value | Description |
|-----------|-------|-------------|
| Max Position Size | 2% | Maximum capital per trade |
| Daily Loss Limit | 5% | Stop trading if exceeded |
| Max Trades/Day | 50 | Per symbol limit |
| Stop Loss | 2× ATR | Dynamic based on volatility |
| Take Profit | 4× ATR | 2:1 reward-to-risk ratio |
| Trailing Stop | 1% | Locks in profits |

### Kelly Criterion

Optimal position sizing based on historical performance:

```python
Kelly Fraction = (Win Rate × Avg Win - Loss Rate × Avg Loss) / Avg Win

# We use Half-Kelly for safety
Position Size = Kelly Fraction / 2
```

---

## 📊 Technical Indicators

All indicators are calculated using **TA-Lib** for maximum efficiency:

| Indicator | Function | Usage |
|-----------|----------|-------|
| SMA | `calculate_sma()` | Trend identification |
| EMA | `calculate_ema()` | Faster trend signals |
| RSI | `calculate_rsi()` | Overbought/oversold |
| MACD | `calculate_macd()` | Momentum |
| Bollinger Bands | `calculate_bollinger_bands()` | Volatility |
| ATR | `calculate_atr()` | Position sizing |
| ADX | `calculate_adx()` | Trend strength |
| Stochastic | `calculate_stochastic()` | Oscillator |
| VWAP | `calculate_vwap()` | Fair value |
| SuperTrend | `calculate_supertrend()` | Trend following |
| Williams %R | `calculate_williams_r()` | Momentum |
| Candlestick Patterns | `detect_candlestick_patterns()` | Pattern recognition |

---

## 🔧 Installation

### Prerequisites

- Node.js 18+
- Python 3.11+
- PostgreSQL 14+
- Groww Trading Account with API access

### Setup

```bash
# Clone the repository
git clone https://github.com/yourusername/hft-trading-dashboard.git
cd hft-trading-dashboard

# Install Node.js dependencies
npm install

# Install Python dependencies
cd server/python
pip install -r requirements.txt

# Setup database
npm run db:push

# Start the application
npm run dev
```

---

## ⚙️ Configuration

### Environment Variables

```env
# Database
DATABASE_URL=postgresql://user:pass@host:5432/dbname

# Session
SESSION_SECRET=your-secret-key

# Trading (Optional - set in dashboard)
GROWW_API_KEY=your-api-key
GROWW_API_SECRET=your-api-secret
INITIAL_CAPITAL=100000
```

### Trading Configuration (`server/python/config.py`)

```python
# Risk Management
MAX_POSITION_SIZE_PERCENT = 2.0    # Max 2% per trade
MAX_DAILY_LOSS_PERCENT = 5.0       # Stop at 5% daily loss
MAX_TRADES_PER_DAY = 50            # Trade limit

# Stop Loss / Take Profit
STOP_LOSS_PERCENT = 1.5
TAKE_PROFIT_PERCENT = 3.0
TRAILING_STOP_PERCENT = 1.0

# Market Hours (IST)
MARKET_OPEN_HOUR = 9
MARKET_OPEN_MINUTE = 15
MARKET_CLOSE_HOUR = 15
MARKET_CLOSE_MINUTE = 30
```

### Default Trading Symbols

```python
DEFAULT_SYMBOLS = [
    "RELIANCE", "TCS", "HDFCBANK", "INFY", "ICICIBANK",
    "HINDUNILVR", "SBIN", "BHARTIARTL", "KOTAKBANK", "ITC"
]
```

---

## 🔌 API Reference

### Strategies

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/strategies` | Get all strategies |
| GET | `/api/strategies/:id` | Get strategy by ID |
| PATCH | `/api/strategies/:id` | Update strategy |

### Trades

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/trades` | Get user's trades |
| POST | `/api/trades` | Record new trade |

### User

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/auth/user` | Get current user |
| PATCH | `/api/user/config` | Update API keys |

---

## 🗄 Database Schema

### Users Table
```sql
CREATE TABLE users (
    id VARCHAR PRIMARY KEY,
    email VARCHAR,
    first_name VARCHAR,
    last_name VARCHAR,
    profile_image_url VARCHAR,
    groww_api_key VARCHAR,
    groww_api_secret VARCHAR,
    created_at TIMESTAMP,
    updated_at TIMESTAMP
);
```

### Strategies Table
```sql
CREATE TABLE strategies (
    id SERIAL PRIMARY KEY,
    name VARCHAR NOT NULL,
    description TEXT,
    is_active BOOLEAN DEFAULT false,
    parameters JSONB,
    created_at TIMESTAMP DEFAULT NOW()
);
```

### Trades Table
```sql
CREATE TABLE trades (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR REFERENCES users(id),
    symbol VARCHAR NOT NULL,
    side VARCHAR NOT NULL,  -- 'BUY' or 'SELL'
    quantity INTEGER NOT NULL,
    price DECIMAL NOT NULL,
    status VARCHAR NOT NULL,
    timestamp TIMESTAMP DEFAULT NOW(),
    strategy_id INTEGER REFERENCES strategies(id),
    pnl DECIMAL
);
```

---

## 🚀 Usage

### Starting the Dashboard

```bash
npm run dev
```

Access at `http://localhost:5000`

### Starting the Trading Engine

```bash
cd server/python
python engine.py
```

The engine will:
1. Connect to the database
2. Authenticate with Groww API
3. Load active strategies
4. Begin trading during market hours (9:15 AM - 3:30 PM IST)

### Simulation Mode

If Groww API credentials are not provided, the engine runs in simulation mode with generated market data - perfect for testing strategies without real money.

---

## ⚠️ Risk Disclaimer

**IMPORTANT: Trading involves substantial risk of loss and is not suitable for all investors.**

- Past performance is not indicative of future results
- Only trade with money you can afford to lose
- This software is provided for educational purposes
- The developers are not responsible for any trading losses
- Always test strategies in simulation mode first
- Consult a financial advisor before live trading

---

## 📄 License

MIT License - See [LICENSE](LICENSE) for details.

---

## 🤝 Contributing

Contributions are welcome! Please read our contributing guidelines before submitting PRs.

---

## 📞 Support

- **Issues**: GitHub Issues
- **Discussions**: GitHub Discussions

---

*Built with ❤️ for the Indian Trading Community*
>>>>>>> 6ed51e6 (Add comprehensive design documentation to the README file)
