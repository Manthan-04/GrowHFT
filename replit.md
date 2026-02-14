# HFT Trading API - Python Backend

## Overview
A professional-grade algorithmic trading API for the Indian Stock Market (NSE/BSE) using the Groww trading platform. Built entirely in Python with FastAPI. The trading engine **auto-starts on server boot** and continuously scans the market in the background — no manual API calls needed to trigger scans.

## Architecture

```
server/python/
├── main.py              # FastAPI app + auto-starts engine on boot
├── database.py          # SQLAlchemy models and database connection
├── schemas.py           # Pydantic request/response schemas
├── engine.py            # Trading engine with background loop + signal log
├── strategies.py        # 7 trading strategy implementations
├── indicators.py        # Technical indicators (SMA, EMA, RSI, MACD, etc.)
├── money_management.py  # Risk management and position sizing
├── config.py            # Configuration parameters
└── requirements.txt     # Python dependencies
```

## Running the Application

```bash
cd server/python
python main.py
```

The API runs on port 5000. Engine auto-starts in SIMULATION mode (no API keys needed).

## Key Behaviour

- Engine starts automatically when server boots
- Background loop scans all 10 symbols every 5 seconds during NSE market hours (9:15-15:30 IST)
- Signals are stored in an in-memory log (last 500) and readable via GET /api/engine/signals
- Trades are persisted to PostgreSQL
- Without Groww API keys, engine runs in SIMULATION mode with generated price data

## API Endpoints

### Health
- `GET /` - API status + engine state
- `GET /health` - Health check

### Engine (auto-running background scanner)
- `GET /api/engine/status` - Full engine snapshot (running, capital, positions, scan count)
- `GET /api/engine/signals` - Auto-generated signals (no manual trigger needed)
- `GET /api/engine/signals/{symbol}` - Latest signal for one stock
- `GET /api/engine/metrics` - Risk metrics (win rate, drawdown, Sharpe)
- `POST /api/engine/start?user_id=X` - Restart engine with specific user credentials
- `POST /api/engine/stop` - Stop the background loop

### Users
- `GET /api/users/{user_id}` - Get user
- `POST /api/users` - Create user (JSON body: id, email, first_name, last_name)
- `PATCH /api/users/{user_id}` - Update user config (API keys, capital)

### Strategies
- `GET /api/strategies` - List all strategies
- `PATCH /api/strategies/{id}` - Toggle strategy on/off

### Trades
- `GET /api/trades` - List executed trades
- `POST /api/trades` - Record trade manually

### Market Data
- `GET /api/symbols` - Default symbols
- `GET /api/market/{symbol}` - OHLCV candle data

### Backtest
- `POST /api/backtest` - Run strategy backtest

## Trading Strategies

1. Moving Average Crossover (SMA 20/50 crossover)
2. RSI Mean Reversion (RSI 14, oversold <30, overbought >70)
3. MACD Strategy (12/26/9 crossover)
4. Bollinger Bands (20-period, 2 std dev)
5. VWAP Strategy (price vs VWAP with volume confirmation)
6. SuperTrend (ATR-based trend following)
7. Stochastic RSI (dual oscillator confirmation)

## Database

Uses PostgreSQL with SQLAlchemy ORM.

Tables: users, strategies, trades, trading_sessions
