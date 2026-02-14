# HFT Trading API

A Python-only High Frequency Trading engine for the **Indian Stock Market (NSE/BSE)** built with FastAPI. The engine **automatically and continuously monitors the market**, generates trading signals, and executes trades — no manual API calls are required to trigger scans.

---

## How It Works — Complete Flow

### The Big Picture

```
┌────────────────────────────────────────────────────────────────────────┐
│                          SERVER STARTS                                 │
│   python main.py                                                       │
│     │                                                                  │
│     ├─► Initialise database (create tables, seed strategies)           │
│     ├─► Auto-start the Trading Engine in a background task             │
│     └─► FastAPI server listens on port 5000                            │
│                                                                        │
│   From this point, the engine runs BY ITSELF:                          │
│                                                                        │
│   ┌────────── BACKGROUND LOOP (every 5 seconds) ──────────┐           │
│   │                                                         │           │
│   │  1. Check if it is NSE market hours (9:15–15:30 IST)   │           │
│   │     └─ If NO → sleep 60 s, then retry                  │           │
│   │                                                         │           │
│   │  2. Reload active strategies from database              │           │
│   │                                                         │           │
│   │  3. For EACH symbol (10 stocks, in parallel):           │           │
│   │     a. Fetch latest OHLCV candles from Groww (or sim)   │           │
│   │     b. Run ALL active strategies on the data            │           │
│   │     c. Combine votes → weighted signal → BUY/SELL/HOLD  │           │
│   │     d. If open position → check stop-loss / trailing /  │           │
│   │        take-profit → close if triggered                 │           │
│   │     e. If no position + BUY or SELL signal →            │           │
│   │        calculate position size → execute trade           │           │
│   │     f. Log signal to in-memory signal log               │           │
│   │     g. Persist trade to PostgreSQL                      │           │
│   │                                                         │           │
│   │  4. Log portfolio metrics (capital, PnL, win rate)      │           │
│   │                                                         │           │
│   │  5. Sleep 5 seconds → loop again                        │           │
│   └─────────────────────────────────────────────────────────┘           │
│                                                                        │
│   MEANWHILE, the API endpoints let you:                                │
│     • GET /api/engine/status     → see if engine is running            │
│     • GET /api/engine/signals    → read auto-generated signals         │
│     • GET /api/engine/metrics    → see portfolio risk metrics          │
│     • GET /api/trades            → see executed trades from DB         │
│     • PATCH /api/strategies/{id} → enable/disable a strategy           │
│     • POST /api/engine/stop      → stop the engine                     │
│     • POST /api/engine/start     → restart with different user/config  │
│                                                                        │
└────────────────────────────────────────────────────────────────────────┘
```

### Step-by-Step Execution Flow

#### Step 1: Server Boot (`main.py`)

When you run `python main.py`, the following happens in order:

1. **Database initialisation** — SQLAlchemy creates the `users`, `strategies`, `trades`, and `trading_sessions` tables if they don't exist. If the strategies table is empty, it seeds 7 default strategies.
2. **Engine auto-start** — A `TradingEngine` instance is created and its `run_trading_loop()` method is launched as an `asyncio.Task`. This runs **in the background**, in parallel with the API server.
3. **API server starts** — Uvicorn begins serving FastAPI on port 5000. You can now call any endpoint.

#### Step 2: The Background Loop (`engine.py → run_trading_loop`)

This is the heart of the system. Once started, it repeats this cycle every 5 seconds:

```
LOOP START
  │
  ├─ Is it a weekday AND between 9:15 AM – 3:30 PM IST?
  │    NO  → sleep 60 seconds, retry
  │    YES → continue
  │
  ├─ Reload active strategies from database
  │    (so you can toggle strategies on/off via API at any time)
  │
  ├─ For EACH of the 10 default symbols (in parallel):
  │    │
  │    ├─ Fetch 100 most recent 5-minute OHLCV candles
  │    │    • From Groww API if credentials are set (LIVE mode)
  │    │    • Generated random-walk data otherwise (SIMULATION mode)
  │    │
  │    ├─ IF there is an open position for this symbol:
  │    │    Check exit conditions:
  │    │    • Price hit stop-loss (2x ATR below entry)?
  │    │    • Price hit trailing stop (1% from peak)?
  │    │    • Price hit take-profit (4x ATR above entry)?
  │    │    → If YES: close the position, record PnL, log the event
  │    │    → If NO: do nothing, keep holding
  │    │
  │    ├─ IF there is NO open position:
  │    │    Run signal generation:
  │    │    • Each active strategy votes: +1 (BUY), -1 (SELL), 0 (HOLD)
  │    │    • Votes are combined with weights (see below)
  │    │    • If weighted average > 0.3  → BUY signal
  │    │    • If weighted average < -0.3 → SELL signal
  │    │    • Otherwise → HOLD
  │    │    
  │    │    If signal is BUY or SELL:
  │    │    • Check daily loss limit (max 5% of capital)
  │    │    • Check daily trade count (max 50)
  │    │    • Calculate position size using ATR
  │    │    • Execute trade on Groww (or simulate)
  │    │    • Save trade to PostgreSQL
  │    │
  │    └─ Log the signal event to in-memory signal log
  │
  ├─ Log portfolio summary to console
  │
  └─ Sleep 5 seconds → LOOP START
```

#### Step 3: Reading Results (API Endpoints)

You **never need to trigger a scan manually**. The engine does it automatically. You just read the results:

- `GET /api/engine/signals` — returns auto-generated signals (default 50, max 500 stored in memory)
- `GET /api/engine/signals/RELIANCE` — latest signal for a specific stock
- `GET /api/engine/status` — is the engine running, how many scans, capital, PnL
- `GET /api/trades` — all executed trades from the database
- `GET /api/engine/metrics` — win rate, drawdown, Sharpe ratio

---

## Signal Generation — How Strategies Vote

When the engine scans a symbol, it runs all active strategies on the price data. Each strategy independently returns a vote:

| Vote | Meaning |
|------|---------|
| +1   | BUY — I think the price will go up |
| -1   | SELL — I think the price will go down |
|  0   | HOLD — No clear signal |

These votes are then combined using a **weighted average**:

```
                              Strategy         Weight
                              ─────────────────────────
                              MA Crossover       1.0
                              EMA Crossover      1.0
                              RSI                0.8
                              Bollinger Bands    0.7
                              MACD               1.0
                              VWAP               0.9
                              SuperTrend         1.2
                              Stochastic RSI     0.8

Weighted Signal = Σ(vote × weight) / Σ(weight)

If Weighted Signal > +0.3  →  Final decision = BUY
If Weighted Signal < -0.3  →  Final decision = SELL
Otherwise                  →  Final decision = HOLD
```

**Example:** If MA Crossover (+1), EMA Crossover (+1), MACD (+1), and SuperTrend (+1) all say BUY, but RSI (0), Bollinger (0), VWAP (0), and Stochastic RSI (0) are neutral:

```
Weighted Signal = (1×1.0 + 1×1.0 + 0×0.8 + 0×0.7 + 1×1.0 + 0×0.9 + 1×1.2 + 0×0.8) / (1.0+1.0+0.8+0.7+1.0+0.9+1.2+0.8)
                = 4.2 / 7.4
                = 0.57  →  > 0.3  →  BUY
```

---

## The 8 Trading Strategies Explained

The engine uses 7 distinct strategy classes (defined in `strategies.py`), but the `MovingAverageCrossover` class is instantiated **twice** — once with SMA and once with EMA — giving 8 independent voters in the multi-strategy engine.

### 1. Moving Average Crossover (SMA variant)

**Code class:** `MovingAverageCrossover` with `use_ema=False`

**How it works:** Calculates two Simple Moving Averages — a fast one (20-period) and a slow one (50-period). When the fast crosses above the slow, it's a buy signal ("Golden Cross"). When it crosses below, it's a sell signal ("Death Cross").

**Why it works:** Moving averages smooth out noise. When the short-term trend overtakes the long-term trend, it suggests momentum is building.

```
BUY:  SMA(20) was below SMA(50) → now crosses above
SELL: SMA(20) was above SMA(50) → now crosses below
```

### 2. EMA Crossover (EMA variant of the same class)

**Code class:** `MovingAverageCrossover` with `use_ema=True`

**How it works:** Same crossover logic as strategy #1, but uses Exponential Moving Averages instead of Simple Moving Averages. EMAs give more weight to recent prices, making them react faster to new trends.

**Why it works:** EMA responds more quickly to price changes than SMA, catching trends earlier — at the cost of more false signals. Running both gives the engine two "views" of trend strength.

```
BUY:  EMA(short) crosses above EMA(long)
SELL: EMA(short) crosses below EMA(long)
```

### 3. RSI Mean Reversion

**How it works:** The Relative Strength Index measures how fast prices are rising vs falling over 14 periods. It ranges from 0 to 100.

**Why it works:** When RSI drops below 30, the stock is "oversold" — it has fallen too much too fast and is likely to bounce. Above 70, it's "overbought" and likely to pull back.

```
BUY:  RSI crosses below 30 (oversold bounce expected)
SELL: RSI crosses above 70 (overbought pullback expected)
```

### 4. MACD Strategy

**How it works:** MACD is the difference between a 12-period EMA and a 26-period EMA. A 9-period EMA of the MACD itself is the "signal line". When MACD crosses above the signal line, it's bullish.

**Why it works:** MACD captures momentum shifts. The crossover happens before price trends become obvious.

```
BUY:  MACD line crosses above signal line
SELL: MACD line crosses below signal line
```

### 5. Bollinger Bands

**How it works:** Draws bands at 2 standard deviations above and below a 20-period moving average. Price touching the lower band suggests the stock is cheap; touching the upper band suggests it's expensive.

**Why it works:** Statistically, prices tend to revert to their mean. When they stretch too far from the average, they snap back.

```
BUY:  Price crosses below the lower band
SELL: Price crosses above the upper band
```

### 6. VWAP Strategy

**How it works:** Volume Weighted Average Price gives the average price weighted by volume for the day. If the price crosses above VWAP with high volume, institutions are buying.

**Why it works:** VWAP is the benchmark that institutional traders use. Price above VWAP means buyers are in control.

```
BUY:  Price crosses above VWAP AND volume > 1.5× average
SELL: Price crosses below VWAP
```

### 7. SuperTrend

**How it works:** Uses ATR (Average True Range) to create dynamic support and resistance levels. When price is above the SuperTrend line, the trend is up. When it crosses below, the trend has reversed.

**Why it works:** ATR adapts to volatility, so the trigger levels automatically widen in volatile markets and tighten in calm markets.

```
BUY:  SuperTrend direction flips from bearish to bullish
SELL: SuperTrend direction flips from bullish to bearish
```

### 8. Stochastic RSI

**How it works:** Combines two popular oscillators. Requires BOTH RSI < 30 AND Stochastic < 20 for a buy, or BOTH RSI > 70 AND Stochastic > 80 for a sell.

**Why it works:** Requiring two independent indicators to agree filters out false signals that either indicator alone would produce.

```
BUY:  RSI < 30 AND Stochastic %K < 20
SELL: RSI > 70 AND Stochastic %K > 80
```

---

## Money Management — How Risk Is Controlled

### Position Sizing

Every trade risks at most **2% of total capital**. The exact number of shares is calculated using volatility:

```
ATR = Average True Range over 14 periods (measures how much price moves per candle)
Risk Amount = Capital × 2%
Stop Distance = ATR × 2
Shares = Risk Amount ÷ Stop Distance
```

**Example:** Capital = ₹1,00,000. ATR = ₹50. Stop Distance = ₹100.
→ Risk Amount = ₹2,000. Shares = 2,000 ÷ 100 = **20 shares**.

### Stop-Loss, Take-Profit, Trailing Stop

For every trade opened, three exit levels are calculated automatically:

| Exit Type | Calculation | Purpose |
|-----------|-------------|---------|
| **Stop-Loss** | Entry ± 2 × ATR | Limits loss if the trade goes wrong |
| **Take-Profit** | Entry ± 4 × ATR | Locks in profit at a 2:1 reward-to-risk ratio |
| **Trailing Stop** | 1% from the highest price reached | Lets winners run, but protects gains |

The engine checks these conditions **every scan cycle** (every 5 seconds) and closes the position automatically if any are hit.

### Daily Loss Limit

If the total daily loss exceeds **5% of starting capital**, the engine stops opening new positions for the rest of the day.

### Kelly Criterion

For advanced users, the system includes a Kelly Criterion calculator that determines the mathematically optimal fraction of capital to risk based on your historical win rate and average win/loss ratio. It uses **Half-Kelly** for safety (halves the theoretical optimal to reduce variance).

---

## Project Structure

```
server/python/
│
├── main.py              ← FastAPI app. Starts server + auto-starts engine.
│                           All API endpoints are defined here.
│
├── engine.py            ← The TradingEngine class. Contains the background
│                           loop that scans the market automatically.
│                           Also holds the in-memory signal log.
│
├── strategies.py        ← All 7 strategy classes + MultiStrategyEngine
│                           that combines them via weighted voting.
│
├── indicators.py        ← Technical indicator calculations:
│                           SMA, EMA, RSI, MACD, Bollinger, ATR, ADX,
│                           Stochastic, VWAP, SuperTrend, Williams %R,
│                           and candlestick pattern detection.
│
├── money_management.py  ← MoneyManager class: position sizing, stop-loss,
│                           take-profit, trailing stop, daily limits.
│                           Also contains KellyCriterion class.
│
├── database.py          ← SQLAlchemy models (User, Strategy, Trade,
│                           TradingSession) + database connection setup
│                           + seed data for default strategies.
│
├── schemas.py           ← Pydantic models for API request/response
│                           validation (UserCreate, TradeResponse, etc.)
│
├── config.py            ← All configurable parameters in one place:
│                           risk limits, indicator periods, market hours,
│                           default symbols.
│
└── requirements.txt     ← Python package dependencies.
```

### How the files connect to each other:

```
main.py
  ├── imports engine.py        → creates TradingEngine, starts background loop
  ├── imports database.py      → SQLAlchemy session for API endpoints
  ├── imports schemas.py       → validates API request/response bodies
  ├── imports strategies.py    → on-demand signal queries
  └── imports config.py        → DEFAULT_SYMBOLS list

engine.py
  ├── imports strategies.py    → MultiStrategyEngine for voting
  ├── imports money_management.py → MoneyManager for sizing & exits
  ├── imports indicators.py    → calculate_atr for volatility
  ├── imports database.py      → SessionLocal, Trade, Strategy models
  └── imports config.py        → market hours, symbols, risk params

strategies.py
  ├── imports indicators.py    → all technical indicator functions
  └── imports config.py        → default indicator periods

money_management.py
  └── imports config.py        → risk limits, stop percentages
```

---

## API Endpoint Reference

### Health & Info

| Method | Endpoint | What it does |
|--------|----------|--------------|
| GET | `/` | Shows API status, engine state, link to docs |
| GET | `/health` | Simple health check |
| GET | `/docs` | Interactive Swagger UI (auto-generated by FastAPI) |

### Engine (Background Scanner)

| Method | Endpoint | What it does |
|--------|----------|--------------|
| GET | `/api/engine/status` | Is engine running? How many scans? Capital? PnL? |
| GET | `/api/engine/signals` | Auto-generated signals (default 50, up to 500 stored in memory; use `?limit=N`) |
| GET | `/api/engine/signals/{symbol}` | Latest signal for one specific stock |
| GET | `/api/engine/metrics` | Win rate, drawdown, Sharpe ratio, profit factor |
| POST | `/api/engine/start?user_id=X` | Restart engine with a specific user's API keys |
| POST | `/api/engine/stop` | Stop the background scanner |

### Strategies

| Method | Endpoint | What it does |
|--------|----------|--------------|
| GET | `/api/strategies` | List all 7 strategies with their on/off status |
| GET | `/api/strategies/{id}` | Get one strategy's details |
| POST | `/api/strategies` | Create a custom strategy |
| PATCH | `/api/strategies/{id}` | Toggle a strategy on/off, change parameters |
| DELETE | `/api/strategies/{id}` | Remove a strategy |

### Trades

| Method | Endpoint | What it does |
|--------|----------|--------------|
| GET | `/api/trades` | List all executed trades (newest first) |
| GET | `/api/trades?symbol=RELIANCE` | Filter trades by symbol |
| GET | `/api/trades/{id}` | Get one trade's details |
| POST | `/api/trades` | Manually record a trade |

### Users

| Method | Endpoint | What it does |
|--------|----------|--------------|
| GET | `/api/users/{id}` | Get user profile |
| POST | `/api/users` | Create a new user |
| PATCH | `/api/users/{id}` | Update Groww API keys, set initial capital |

### Market Data

| Method | Endpoint | What it does |
|--------|----------|--------------|
| GET | `/api/symbols` | List default trading symbols |
| GET | `/api/market/{symbol}` | Get OHLCV candle data for any stock |

### Backtesting

| Method | Endpoint | What it does |
|--------|----------|--------------|
| POST | `/api/backtest` | Test a strategy on historical data |

---

## Database Schema

### users
| Column | Type | Description |
|--------|------|-------------|
| id | VARCHAR (PK) | Unique user identifier |
| email | VARCHAR | User email |
| first_name | VARCHAR | First name |
| last_name | VARCHAR | Last name |
| groww_api_key | VARCHAR | Encrypted Groww API key |
| groww_api_secret | VARCHAR | Encrypted Groww API secret |
| initial_capital | FLOAT | Starting capital (default ₹1,00,000) |
| created_at | TIMESTAMP | Account creation time |

### strategies
| Column | Type | Description |
|--------|------|-------------|
| id | SERIAL (PK) | Auto-increment ID |
| name | VARCHAR | Strategy name (e.g., "MACD Strategy") |
| description | TEXT | What the strategy does |
| is_active | BOOLEAN | Whether the engine uses this strategy |
| parameters | JSONB | Configurable parameters (periods, thresholds) |
| created_at | TIMESTAMP | When it was added |

### trades
| Column | Type | Description |
|--------|------|-------------|
| id | SERIAL (PK) | Auto-increment ID |
| user_id | VARCHAR (FK → users) | Who placed the trade |
| symbol | VARCHAR | Stock symbol (e.g., "RELIANCE") |
| side | VARCHAR | "BUY" or "SELL" |
| quantity | INTEGER | Number of shares |
| price | VARCHAR | Execution price |
| status | VARCHAR | "EXECUTED", "PENDING", "FAILED" |
| timestamp | TIMESTAMP | When the trade happened |
| strategy_id | INTEGER (FK → strategies) | Which strategy triggered it |
| pnl | VARCHAR | Profit/loss (set when position is closed) |

---

## Configuration (`config.py`)

All tunable parameters are in one file:

```python
# Risk Management
MAX_POSITION_SIZE_PERCENT = 2.0    # Max 2% of capital per trade
MAX_DAILY_LOSS_PERCENT = 5.0       # Stop trading after 5% daily loss
MAX_TRADES_PER_DAY = 50            # Per-symbol daily limit

# Exit Rules
STOP_LOSS_PERCENT = 1.5            # Fallback stop-loss
TAKE_PROFIT_PERCENT = 3.0          # Fallback take-profit
TRAILING_STOP_PERCENT = 1.0        # Trailing stop distance

# Indicator Defaults
RSI_PERIOD = 14
MACD_FAST = 12, MACD_SLOW = 26, MACD_SIGNAL = 9
BOLLINGER_PERIOD = 20, BOLLINGER_STD = 2
SMA_SHORT = 20, SMA_LONG = 50

# NSE Market Hours (IST)
MARKET_OPEN  = 09:15
MARKET_CLOSE = 15:30

# Default Symbols
RELIANCE, TCS, HDFCBANK, INFY, ICICIBANK,
HINDUNILVR, SBIN, BHARTIARTL, KOTAKBANK, ITC
```

---

## Running the Application

```bash
cd server/python
python main.py
```

The server starts on port 5000. Open `http://localhost:5000/docs` for the interactive API documentation.

### Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| DATABASE_URL | Yes | (set by Replit) | PostgreSQL connection string |
| PORT | No | 5000 | Server port |
| GROWW_API_KEY | No | "" | Groww API key (empty = simulation) |
| GROWW_API_SECRET | No | "" | Groww API secret |
| INITIAL_CAPITAL | No | 100000 | Starting capital in INR |

### Simulation vs Live Mode

- **No API keys** → Engine runs in **SIMULATION** mode using generated price data. Perfect for testing.
- **With API keys** → Engine connects to Groww and trades with **real market data and real orders**.

---

## Example Usage

### Check engine status
```bash
curl http://localhost:5000/api/engine/status
```

### Read auto-generated signals
```bash
# All recent signals
curl http://localhost:5000/api/engine/signals

# Signals for RELIANCE only
curl http://localhost:5000/api/engine/signals/RELIANCE
```

### Toggle a strategy off
```bash
curl -X PATCH http://localhost:5000/api/strategies/4 \
  -H "Content-Type: application/json" \
  -d '{"is_active": false}'
```

### View executed trades
```bash
curl http://localhost:5000/api/trades
```

### Run a backtest
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

## Risk Disclaimer

**Trading involves substantial risk of loss.** This software is for educational purposes. Test thoroughly in simulation mode before using real money. The developers are not responsible for any trading losses.

---

## License

MIT
