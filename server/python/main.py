"""
FastAPI Backend for HFT Trading System
Main application entry point.

The engine auto-starts in the background when the server boots.
It continuously scans the market and generates signals on its own.
"""
import os
import asyncio
from datetime import datetime
from typing import List, Optional
from contextlib import asynccontextmanager

from fastapi import FastAPI, Depends, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from dotenv import load_dotenv

from database import get_db, init_db, User, Strategy, Trade, TradingSession
from schemas import (
    UserResponse, UserCreate, UserUpdate,
    StrategyResponse, StrategyCreate, StrategyUpdate,
    TradeResponse, TradeCreate,
    EngineStatus, EngineConfig, SignalResponse, RiskMetrics,
    BacktestRequest, BacktestResult
)
from engine import TradingEngine
from strategies import MultiStrategyEngine, get_strategy
from config import DEFAULT_SYMBOLS

load_dotenv()

# ---------------------------------------------------------------------------
# Global state
# ---------------------------------------------------------------------------
trading_engine: Optional[TradingEngine] = None
engine_task: Optional[asyncio.Task] = None


async def _auto_start_engine():
    """
    Called at server startup.
    Creates an engine in SIMULATION mode (no API keys needed)
    so the market scanner runs automatically from boot.
    """
    global trading_engine, engine_task

    user_id = os.getenv("TRADING_USER_ID", "auto_scanner")
    api_key = os.getenv("GROWW_API_KEY", "")
    api_secret = os.getenv("GROWW_API_SECRET", "")
    capital = float(os.getenv("INITIAL_CAPITAL", "100000"))

    trading_engine = TradingEngine(
        user_id=user_id,
        api_key=api_key,
        api_secret=api_secret,
        initial_capital=capital,
    )
    trading_engine.connect_database()
    trading_engine.connect_groww()
    trading_engine.load_active_strategies()

    engine_task = asyncio.create_task(trading_engine.run_trading_loop())
    print("Engine auto-started in background")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup / Shutdown hooks."""
    print("Starting HFT Trading API...")
    init_db()
    await _auto_start_engine()
    yield
    global trading_engine, engine_task
    if trading_engine:
        trading_engine.stop()
    if engine_task:
        engine_task.cancel()
    print("HFT Trading API stopped")


app = FastAPI(
    title="HFT Trading API",
    description="High Frequency Trading API for Indian Stock Market (NSE/BSE). "
                "The engine auto-starts and continuously scans the market.",
    version="2.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ======================================================================
# HEALTH
# ======================================================================

@app.get("/")
async def root():
    return {
        "status": "running",
        "service": "HFT Trading API",
        "version": "2.0.0",
        "engine_running": trading_engine.is_running if trading_engine else False,
        "docs": "/docs",
        "timestamp": datetime.utcnow().isoformat(),
    }


@app.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.utcnow().isoformat()}


# ======================================================================
# USERS
# ======================================================================

@app.get("/api/users/{user_id}", response_model=UserResponse)
async def get_user(user_id: str, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@app.post("/api/users", response_model=UserResponse)
async def create_user(user_data: UserCreate, db: Session = Depends(get_db)):
    existing = db.query(User).filter(User.id == user_data.id).first()
    if existing:
        return existing
    user = User(
        id=user_data.id,
        email=user_data.email,
        first_name=user_data.first_name,
        last_name=user_data.last_name,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@app.patch("/api/users/{user_id}", response_model=UserResponse)
async def update_user(user_id: str, update: UserUpdate, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    for key, value in update.model_dump(exclude_unset=True).items():
        setattr(user, key, value)
    user.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(user)
    return user


# ======================================================================
# STRATEGIES
# ======================================================================

@app.get("/api/strategies", response_model=List[StrategyResponse])
async def get_strategies(db: Session = Depends(get_db)):
    return db.query(Strategy).all()


@app.get("/api/strategies/{strategy_id}", response_model=StrategyResponse)
async def get_strategy_by_id(strategy_id: int, db: Session = Depends(get_db)):
    strategy = db.query(Strategy).filter(Strategy.id == strategy_id).first()
    if not strategy:
        raise HTTPException(status_code=404, detail="Strategy not found")
    return strategy


@app.post("/api/strategies", response_model=StrategyResponse)
async def create_strategy(strategy: StrategyCreate, db: Session = Depends(get_db)):
    db_strategy = Strategy(**strategy.model_dump())
    db.add(db_strategy)
    db.commit()
    db.refresh(db_strategy)
    return db_strategy


@app.patch("/api/strategies/{strategy_id}", response_model=StrategyResponse)
async def update_strategy(strategy_id: int, update: StrategyUpdate, db: Session = Depends(get_db)):
    strategy = db.query(Strategy).filter(Strategy.id == strategy_id).first()
    if not strategy:
        raise HTTPException(status_code=404, detail="Strategy not found")
    for key, value in update.model_dump(exclude_unset=True).items():
        setattr(strategy, key, value)
    db.commit()
    db.refresh(strategy)
    return strategy


@app.delete("/api/strategies/{strategy_id}")
async def delete_strategy(strategy_id: int, db: Session = Depends(get_db)):
    strategy = db.query(Strategy).filter(Strategy.id == strategy_id).first()
    if not strategy:
        raise HTTPException(status_code=404, detail="Strategy not found")
    db.delete(strategy)
    db.commit()
    return {"message": "Strategy deleted"}


# ======================================================================
# TRADES
# ======================================================================

@app.get("/api/trades", response_model=List[TradeResponse])
async def get_trades(
    user_id: Optional[str] = None,
    symbol: Optional[str] = None,
    limit: int = 100,
    db: Session = Depends(get_db),
):
    query = db.query(Trade)
    if user_id:
        query = query.filter(Trade.user_id == user_id)
    if symbol:
        query = query.filter(Trade.symbol == symbol)
    return query.order_by(Trade.timestamp.desc()).limit(limit).all()


@app.get("/api/trades/{trade_id}", response_model=TradeResponse)
async def get_trade(trade_id: int, db: Session = Depends(get_db)):
    trade = db.query(Trade).filter(Trade.id == trade_id).first()
    if not trade:
        raise HTTPException(status_code=404, detail="Trade not found")
    return trade


@app.post("/api/trades", response_model=TradeResponse)
async def create_trade(trade: TradeCreate, db: Session = Depends(get_db)):
    db_trade = Trade(**trade.model_dump())
    db.add(db_trade)
    db.commit()
    db.refresh(db_trade)
    return db_trade


# ======================================================================
# ENGINE — control & monitoring
# ======================================================================

@app.get("/api/engine/status")
async def get_engine_status():
    """Full snapshot of the running engine."""
    if not trading_engine:
        return {"is_running": False, "message": "Engine not initialised"}
    return trading_engine.get_status_dict()


@app.post("/api/engine/start")
async def start_engine(
    user_id: str = Query(..., description="User ID whose credentials to use"),
    config: Optional[EngineConfig] = None,
    db: Session = Depends(get_db),
):
    """(Re)start the engine with a specific user's credentials."""
    global trading_engine, engine_task

    if trading_engine and trading_engine.is_running:
        trading_engine.stop()
        if engine_task:
            engine_task.cancel()

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    trading_engine = TradingEngine(
        user_id=user_id,
        api_key=user.groww_api_key or "",
        api_secret=user.groww_api_secret or "",
        initial_capital=config.initial_capital if config else user.initial_capital,
    )
    if config and config.symbols:
        trading_engine.symbols = config.symbols

    trading_engine.connect_database()
    trading_engine.connect_groww()
    trading_engine.load_active_strategies()

    engine_task = asyncio.create_task(trading_engine.run_trading_loop())
    return {"message": "Engine (re)started", "user_id": user_id,
            "mode": "LIVE" if trading_engine.groww_client else "SIMULATION"}


@app.post("/api/engine/stop")
async def stop_engine():
    """Stop the background engine loop."""
    global trading_engine, engine_task
    if not trading_engine or not trading_engine.is_running:
        raise HTTPException(status_code=400, detail="Engine not running")
    trading_engine.stop()
    if engine_task:
        engine_task.cancel()
        engine_task = None
    return {"message": "Engine stopped"}


# ======================================================================
# AUTO-GENERATED SIGNALS — populated by the background loop
# ======================================================================

@app.get("/api/engine/signals")
async def get_auto_signals(
    symbol: Optional[str] = None,
    limit: int = Query(50, ge=1, le=500),
):
    """
    Returns the signals that the engine generated AUTOMATICALLY
    during its background scans.  No manual trigger needed.
    """
    if not trading_engine:
        return {"signals": [], "message": "Engine not running"}
    return {"signals": trading_engine.get_signal_log(symbol=symbol, limit=limit)}


@app.get("/api/engine/signals/{symbol}")
async def get_signal_for_symbol(symbol: str):
    """Get the latest auto-generated signal for a specific symbol."""
    if not trading_engine:
        raise HTTPException(status_code=400, detail="Engine not running")

    logs = trading_engine.get_signal_log(symbol=symbol, limit=1)
    if not logs:
        return {"symbol": symbol, "message": "No signal yet — engine may still be scanning"}
    return logs[-1]


@app.get("/api/engine/metrics")
async def get_risk_metrics():
    """Current risk & portfolio metrics from the running engine."""
    if not trading_engine:
        return RiskMetrics(
            total_capital=0, available_capital=0, daily_pnl=0,
            daily_trades=0, max_drawdown=0, win_rate=0,
            profit_factor=0, sharpe_ratio=0,
        )
    m = trading_engine.money_manager.get_risk_metrics()
    return RiskMetrics(
        total_capital=m.total_capital, available_capital=m.available_capital,
        daily_pnl=m.daily_pnl, daily_trades=m.daily_trades,
        max_drawdown=m.max_drawdown, win_rate=m.win_rate,
        profit_factor=m.profit_factor, sharpe_ratio=m.sharpe_ratio,
    )


# ======================================================================
# MARKET DATA (on-demand)
# ======================================================================

@app.get("/api/symbols")
async def get_default_symbols():
    return {"symbols": DEFAULT_SYMBOLS}


@app.get("/api/market/{symbol}")
async def get_market_data(symbol: str, interval: str = "5m", limit: int = 100):
    engine = trading_engine or TradingEngine("temp", "", "", 100000)
    data = engine.fetch_market_data(symbol, interval, limit)
    if data is None:
        raise HTTPException(status_code=400, detail="Failed to fetch market data")

    candles = [
        {"timestamp": idx.isoformat(), "open": float(r['open']), "high": float(r['high']),
         "low": float(r['low']), "close": float(r['close']), "volume": int(r['volume'])}
        for idx, r in data.iterrows()
    ]
    price = float(data['close'].iloc[-1])
    prev = float(data['close'].iloc[-2]) if len(data) > 1 else price
    return {"symbol": symbol, "candles": candles, "current_price": price,
            "change_percent": round(((price - prev) / prev) * 100, 2)}


# ======================================================================
# BACKTEST
# ======================================================================

@app.post("/api/backtest", response_model=BacktestResult)
async def run_backtest(request: BacktestRequest):
    from strategies import get_strategy as get_strat
    temp = TradingEngine("backtest", "", "", request.initial_capital)
    data = temp.fetch_market_data(request.symbol, limit=500)
    if data is None:
        raise HTTPException(status_code=400, detail="Failed to fetch market data")

    try:
        strategy = get_strat(request.strategy, request.parameters)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    trades, position, capital = [], None, request.initial_capital

    for i in range(50, len(data)):
        window = data.iloc[:i + 1]
        sig = strategy.generate_signal(window)
        price = float(window['close'].iloc[-1])

        if position is None and sig != 0:
            qty = int((capital * 0.02) / price)
            if qty > 0:
                position = {"entry_price": price, "quantity": qty,
                            "side": "BUY" if sig == 1 else "SELL", "entry_idx": i}
        elif position is not None:
            exit_signal = (position["side"] == "BUY" and sig == -1) or \
                          (position["side"] == "SELL" and sig == 1)
            if exit_signal:
                pnl = ((price - position["entry_price"]) if position["side"] == "BUY"
                       else (position["entry_price"] - price)) * position["quantity"]
                capital += pnl
                trades.append({**position, "exit_price": price, "pnl": pnl})
                position = None

    if not trades:
        return BacktestResult(total_trades=0, winning_trades=0, losing_trades=0,
                              win_rate=0, total_pnl=0, max_drawdown=0,
                              sharpe_ratio=0, profit_factor=0, trades=[])

    wins = [t for t in trades if t["pnl"] > 0]
    losses = [t for t in trades if t["pnl"] < 0]
    gp = sum(t["pnl"] for t in wins)
    gl = abs(sum(t["pnl"] for t in losses))

    return BacktestResult(
        total_trades=len(trades), winning_trades=len(wins), losing_trades=len(losses),
        win_rate=(len(wins) / len(trades)) * 100, total_pnl=capital - request.initial_capital,
        max_drawdown=0, sharpe_ratio=0,
        profit_factor=gp / gl if gl > 0 else float('inf'), trades=trades,
    )


# ======================================================================
# ENTRY POINT
# ======================================================================

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 5000))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=True)
