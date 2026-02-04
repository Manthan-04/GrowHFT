# HFT Trading API - Python Backend

## Overview
A professional-grade algorithmic trading API for the Indian Stock Market (NSE/BSE) using the Groww trading platform. Built entirely in Python with FastAPI.

## Architecture

```
server/python/
├── main.py            # FastAPI application entry point
├── database.py        # SQLAlchemy models and database connection
├── schemas.py         # Pydantic request/response schemas
├── engine.py          # Trading engine with async execution
├── strategies.py      # 7 trading strategy implementations
├── indicators.py      # Technical indicators using TA-Lib
├── money_management.py # Risk management and position sizing
├── config.py          # Configuration parameters
└── requirements.txt   # Python dependencies
```

## Running the Application

```bash
cd server/python
python main.py
```

The API runs on port 5000.

## API Endpoints

### Health
- `GET /` - API status
- `GET /health` - Health check

### Users
- `GET /api/users/{user_id}` - Get user
- `POST /api/users` - Create user
- `PATCH /api/users/{user_id}` - Update user config

### Strategies
- `GET /api/strategies` - List all strategies
- `GET /api/strategies/{id}` - Get strategy
- `POST /api/strategies` - Create strategy
- `PATCH /api/strategies/{id}` - Update strategy
- `DELETE /api/strategies/{id}` - Delete strategy

### Trades
- `GET /api/trades` - List trades
- `GET /api/trades/{id}` - Get trade
- `POST /api/trades` - Record trade

### Trading Engine
- `GET /api/engine/status` - Engine status
- `POST /api/engine/start` - Start trading
- `POST /api/engine/stop` - Stop trading
- `GET /api/engine/signals/{symbol}` - Get trading signal
- `GET /api/engine/metrics` - Risk metrics

### Market Data
- `GET /api/symbols` - Default symbols
- `GET /api/market/{symbol}` - Market data

### Backtest
- `POST /api/backtest` - Run strategy backtest

## Trading Strategies

1. Moving Average Crossover
2. RSI Mean Reversion
3. MACD Strategy
4. Bollinger Bands
5. VWAP Strategy
6. SuperTrend
7. Stochastic RSI

## Database

Uses PostgreSQL with SQLAlchemy ORM.

Tables: users, strategies, trades, trading_sessions
