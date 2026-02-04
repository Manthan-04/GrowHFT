# HFT Trading API

A professional-grade **High Frequency Trading API** for the **Indian Stock Market (NSE/BSE)** using the Groww trading platform. Built entirely in Python with FastAPI.

![Python](https://img.shields.io/badge/Python-3.11+-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-0.109+-green)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16+-blue)
![License](https://img.shields.io/badge/License-MIT-yellow)

---

## Features

- **7 Professional Trading Strategies** - Battle-tested algorithms
- **Multi-Strategy Voting System** - Reduces false signals
- **Async Execution** - Non-blocking order execution
- **Professional Money Management** - ATR-based position sizing
- **RESTful API** - Full CRUD operations for strategies and trades
- **Real-time Signals** - Get trading signals for any symbol
- **Backtesting** - Test strategies on historical data

---

## Project Structure

```
server/python/
├── main.py              # FastAPI application entry point
├── database.py          # SQLAlchemy models and connection
├── schemas.py           # Pydantic request/response schemas
├── engine.py            # Trading engine with async execution
├── strategies.py        # 7 trading strategy implementations
├── indicators.py        # Technical indicators (TA-Lib equivalent)
├── money_management.py  # Risk management and position sizing
├── config.py            # Configuration parameters
└── requirements.txt     # Python dependencies
```

---

## Trading Strategies

| # | Strategy | Description | Best For |
|---|----------|-------------|----------|
| 1 | **Moving Average Crossover** | Golden Cross/Death Cross trading | Trending markets |
| 2 | **RSI Mean Reversion** | Buy oversold, sell overbought | Range-bound markets |
| 3 | **MACD Strategy** | MACD/Signal line crossovers | Momentum trading |
| 4 | **Bollinger Bands** | Mean reversion at bands | Volatile markets |
| 5 | **VWAP Strategy** | Price crossing VWAP | Intraday trading |
| 6 | **SuperTrend** | ATR-based trend following | Strong trends |
| 7 | **Stochastic RSI** | Combined oscillator signals | Confirmation |

### Multi-Strategy Voting

The engine combines signals from all active strategies using weighted voting:

```python
# Signal weights
Moving Average: 1.0
RSI: 0.8
MACD: 1.0
Bollinger: 0.7
VWAP: 0.9
SuperTrend: 1.2
Stochastic RSI: 0.8

# Trade executed only if weighted signal > 0.3
```

---

## Money Management

| Parameter | Value | Description |
|-----------|-------|-------------|
| Max Position Size | 2% | Maximum capital per trade |
| Daily Loss Limit | 5% | Stop trading if exceeded |
| Stop Loss | 2× ATR | Dynamic based on volatility |
| Take Profit | 4× ATR | 2:1 reward-to-risk ratio |
| Trailing Stop | 1% | Locks in profits |

---

## API Endpoints

### Health
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | API status |
| GET | `/health` | Health check |

### Users
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/users/{user_id}` | Get user |
| POST | `/api/users` | Create user |
| PATCH | `/api/users/{user_id}` | Update config (API keys) |

### Strategies
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/strategies` | List all strategies |
| GET | `/api/strategies/{id}` | Get strategy by ID |
| POST | `/api/strategies` | Create new strategy |
| PATCH | `/api/strategies/{id}` | Update strategy |
| DELETE | `/api/strategies/{id}` | Delete strategy |

### Trades
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/trades` | List trades (with filters) |
| GET | `/api/trades/{id}` | Get trade by ID |
| POST | `/api/trades` | Record new trade |

### Trading Engine
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/engine/status` | Get engine status |
| POST | `/api/engine/start` | Start trading engine |
| POST | `/api/engine/stop` | Stop trading engine |
| GET | `/api/engine/signals/{symbol}` | Get trading signal |
| GET | `/api/engine/metrics` | Get risk metrics |

### Market Data
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/symbols` | Get default symbols |
| GET | `/api/market/{symbol}` | Get market data |

### Backtest
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/backtest` | Run strategy backtest |

---

## Installation

### Prerequisites
- Python 3.11+
- PostgreSQL 14+
- Groww Trading Account (optional)

### Setup

```bash
# Navigate to Python directory
cd server/python

# Install dependencies
pip install -r requirements.txt

# Run the server
python main.py
```

The API will be available at `http://localhost:5000`

---

## Configuration

### Environment Variables

```env
DATABASE_URL=postgresql://user:pass@host:5432/dbname
PORT=5000
GROWW_API_KEY=your-api-key (optional)
GROWW_API_SECRET=your-api-secret (optional)
```

### Trading Configuration (`config.py`)

```python
# Risk Management
MAX_POSITION_SIZE_PERCENT = 2.0
MAX_DAILY_LOSS_PERCENT = 5.0
MAX_TRADES_PER_DAY = 50

# Technical Indicators
RSI_PERIOD = 14
MACD_FAST = 12
MACD_SLOW = 26
BOLLINGER_PERIOD = 20

# Market Hours (IST)
MARKET_OPEN = 9:15 AM
MARKET_CLOSE = 3:30 PM
```

### Default Symbols (NSE)

```python
RELIANCE, TCS, HDFCBANK, INFY, ICICIBANK,
HINDUNILVR, SBIN, BHARTIARTL, KOTAKBANK, ITC
```

---

## Database Schema

### Users
```sql
id VARCHAR PRIMARY KEY,
email VARCHAR,
first_name VARCHAR,
last_name VARCHAR,
groww_api_key VARCHAR,
groww_api_secret VARCHAR,
initial_capital FLOAT
```

### Strategies
```sql
id SERIAL PRIMARY KEY,
name VARCHAR NOT NULL,
description TEXT,
is_active BOOLEAN,
parameters JSONB
```

### Trades
```sql
id SERIAL PRIMARY KEY,
user_id VARCHAR REFERENCES users(id),
symbol VARCHAR NOT NULL,
side VARCHAR NOT NULL,
quantity INTEGER NOT NULL,
price VARCHAR NOT NULL,
status VARCHAR NOT NULL,
pnl VARCHAR,
strategy_id INTEGER REFERENCES strategies(id)
```

---

## Usage Examples

### Get Trading Signal

```bash
curl http://localhost:5000/api/engine/signals/RELIANCE
```

Response:
```json
{
  "symbol": "RELIANCE",
  "signal": 1,
  "strategy_signals": {
    "ma_crossover": 1,
    "rsi": 0,
    "macd": 1,
    "supertrend": 1
  },
  "confidence": 0.75,
  "current_price": 2450.50,
  "suggested_quantity": 8,
  "stop_loss": 2400.00,
  "take_profit": 2550.00
}
```

### Start Trading Engine

```bash
curl -X POST "http://localhost:5000/api/engine/start?user_id=user123"
```

### Run Backtest

```bash
curl -X POST http://localhost:5000/api/backtest \
  -H "Content-Type: application/json" \
  -d '{
    "symbol": "RELIANCE",
    "strategy": "ma_crossover",
    "start_date": "2024-01-01",
    "end_date": "2024-12-31",
    "initial_capital": 100000
  }'
```

---

## Simulation Mode

If Groww API credentials are not provided, the engine runs in **simulation mode** with generated market data - perfect for testing strategies without real money.

---

## Risk Disclaimer

**IMPORTANT: Trading involves substantial risk of loss.**

- Past performance is not indicative of future results
- Only trade with money you can afford to lose
- This software is for educational purposes
- Test thoroughly in simulation mode first
- Consult a financial advisor before live trading

---

## License

MIT License - See [LICENSE](LICENSE) for details.

---

*Built for the Indian Trading Community*
