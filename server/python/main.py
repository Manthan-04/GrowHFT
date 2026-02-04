"""
FastAPI Backend for HFT Trading System
Main application entry point
"""
import os
import asyncio
from datetime import datetime
from typing import List, Optional
from contextlib import asynccontextmanager

from fastapi import FastAPI, Depends, HTTPException, BackgroundTasks
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

# Global trading engine instance
trading_engine: Optional[TradingEngine] = None
engine_task: Optional[asyncio.Task] = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan - startup and shutdown"""
    # Startup
    print("Starting HFT Trading API...")
    init_db()
    yield
    # Shutdown
    global trading_engine, engine_task
    if trading_engine:
        trading_engine.stop()
    if engine_task:
        engine_task.cancel()
    print("HFT Trading API stopped")


app = FastAPI(
    title="HFT Trading API",
    description="High Frequency Trading API for Indian Stock Market (NSE/BSE)",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============ Health Check ============

@app.get("/")
async def root():
    """API root - health check"""
    return {
        "status": "running",
        "service": "HFT Trading API",
        "version": "1.0.0",
        "timestamp": datetime.utcnow().isoformat()
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "timestamp": datetime.utcnow().isoformat()}


# ============ User Endpoints ============

@app.get("/api/users/{user_id}", response_model=UserResponse)
async def get_user(user_id: str, db: Session = Depends(get_db)):
    """Get user by ID"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@app.post("/api/users", response_model=UserResponse)
async def create_user(user_data: UserCreate, db: Session = Depends(get_db)):
    """Create a new user"""
    existing = db.query(User).filter(User.id == user_data.id).first()
    if existing:
        return existing
    
    user = User(
        id=user_data.id,
        email=user_data.email,
        first_name=user_data.first_name,
        last_name=user_data.last_name
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@app.patch("/api/users/{user_id}", response_model=UserResponse)
async def update_user(user_id: str, update: UserUpdate, db: Session = Depends(get_db)):
    """Update user configuration (API keys, capital)"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    update_data = update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(user, key, value)
    
    user.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(user)
    return user


# ============ Strategy Endpoints ============

@app.get("/api/strategies", response_model=List[StrategyResponse])
async def get_strategies(db: Session = Depends(get_db)):
    """Get all trading strategies"""
    return db.query(Strategy).all()


@app.get("/api/strategies/{strategy_id}", response_model=StrategyResponse)
async def get_strategy_by_id(strategy_id: int, db: Session = Depends(get_db)):
    """Get strategy by ID"""
    strategy = db.query(Strategy).filter(Strategy.id == strategy_id).first()
    if not strategy:
        raise HTTPException(status_code=404, detail="Strategy not found")
    return strategy


@app.post("/api/strategies", response_model=StrategyResponse)
async def create_strategy(strategy: StrategyCreate, db: Session = Depends(get_db)):
    """Create a new strategy"""
    db_strategy = Strategy(**strategy.model_dump())
    db.add(db_strategy)
    db.commit()
    db.refresh(db_strategy)
    return db_strategy


@app.patch("/api/strategies/{strategy_id}", response_model=StrategyResponse)
async def update_strategy(strategy_id: int, update: StrategyUpdate, db: Session = Depends(get_db)):
    """Update a strategy"""
    strategy = db.query(Strategy).filter(Strategy.id == strategy_id).first()
    if not strategy:
        raise HTTPException(status_code=404, detail="Strategy not found")
    
    update_data = update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(strategy, key, value)
    
    db.commit()
    db.refresh(strategy)
    return strategy


@app.delete("/api/strategies/{strategy_id}")
async def delete_strategy(strategy_id: int, db: Session = Depends(get_db)):
    """Delete a strategy"""
    strategy = db.query(Strategy).filter(Strategy.id == strategy_id).first()
    if not strategy:
        raise HTTPException(status_code=404, detail="Strategy not found")
    
    db.delete(strategy)
    db.commit()
    return {"message": "Strategy deleted"}


# ============ Trade Endpoints ============

@app.get("/api/trades", response_model=List[TradeResponse])
async def get_trades(
    user_id: Optional[str] = None,
    symbol: Optional[str] = None,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """Get trades with optional filters"""
    query = db.query(Trade)
    
    if user_id:
        query = query.filter(Trade.user_id == user_id)
    if symbol:
        query = query.filter(Trade.symbol == symbol)
    
    return query.order_by(Trade.timestamp.desc()).limit(limit).all()


@app.get("/api/trades/{trade_id}", response_model=TradeResponse)
async def get_trade(trade_id: int, db: Session = Depends(get_db)):
    """Get trade by ID"""
    trade = db.query(Trade).filter(Trade.id == trade_id).first()
    if not trade:
        raise HTTPException(status_code=404, detail="Trade not found")
    return trade


@app.post("/api/trades", response_model=TradeResponse)
async def create_trade(trade: TradeCreate, db: Session = Depends(get_db)):
    """Record a new trade"""
    db_trade = Trade(**trade.model_dump())
    db.add(db_trade)
    db.commit()
    db.refresh(db_trade)
    return db_trade


# ============ Trading Engine Endpoints ============

@app.get("/api/engine/status", response_model=EngineStatus)
async def get_engine_status():
    """Get current trading engine status"""
    global trading_engine
    
    if not trading_engine:
        return EngineStatus(
            is_running=False,
            is_market_hours=False,
            active_strategies=[],
            open_positions=0,
            daily_trades=0,
            daily_pnl=0.0,
            current_capital=0.0
        )
    
    return EngineStatus(
        is_running=trading_engine.is_running,
        is_market_hours=trading_engine.is_market_hours(),
        active_strategies=trading_engine.active_strategies,
        open_positions=len(trading_engine.money_manager.positions),
        daily_trades=trading_engine.money_manager.daily_trades,
        daily_pnl=trading_engine.money_manager.daily_pnl,
        current_capital=trading_engine.money_manager.current_capital
    )


@app.post("/api/engine/start")
async def start_engine(
    user_id: str,
    config: EngineConfig = None,
    background_tasks: BackgroundTasks = None,
    db: Session = Depends(get_db)
):
    """Start the trading engine"""
    global trading_engine, engine_task
    
    if trading_engine and trading_engine.is_running:
        raise HTTPException(status_code=400, detail="Engine already running")
    
    # Get user credentials
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    api_key = user.groww_api_key or ""
    api_secret = user.groww_api_secret or ""
    initial_capital = config.initial_capital if config else user.initial_capital
    
    # Create and start engine
    trading_engine = TradingEngine(
        user_id=user_id,
        api_key=api_key,
        api_secret=api_secret,
        initial_capital=initial_capital
    )
    
    if config and config.symbols:
        trading_engine.symbols = config.symbols
    
    # Connect to database
    trading_engine.connect_database()
    trading_engine.connect_groww()
    trading_engine.load_active_strategies()
    
    # Start trading loop in background
    async def run_engine():
        await trading_engine.run_trading_loop()
    
    engine_task = asyncio.create_task(run_engine())
    
    return {"message": "Trading engine started", "user_id": user_id}


@app.post("/api/engine/stop")
async def stop_engine():
    """Stop the trading engine"""
    global trading_engine, engine_task
    
    if not trading_engine or not trading_engine.is_running:
        raise HTTPException(status_code=400, detail="Engine not running")
    
    trading_engine.stop()
    
    if engine_task:
        engine_task.cancel()
        engine_task = None
    
    return {"message": "Trading engine stopped"}


@app.get("/api/engine/signals/{symbol}", response_model=SignalResponse)
async def get_signal(symbol: str):
    """Get current trading signal for a symbol"""
    global trading_engine
    
    if not trading_engine:
        # Create temporary engine for signal generation
        temp_engine = TradingEngine(
            user_id="temp",
            api_key="",
            api_secret="",
            initial_capital=100000.0
        )
        data = temp_engine.fetch_market_data(symbol)
    else:
        data = trading_engine.fetch_market_data(symbol)
    
    if data is None or len(data) < 50:
        raise HTTPException(status_code=400, detail="Insufficient market data")
    
    from indicators import calculate_atr
    
    strategy_engine = MultiStrategyEngine()
    signal, strategy_signals = strategy_engine.get_combined_signal(data)
    
    current_price = float(data['close'].iloc[-1])
    atr = calculate_atr(data['high'], data['low'], data['close'])
    current_atr = float(atr.iloc[-1]) if not atr.iloc[-1] != atr.iloc[-1] else current_price * 0.02
    
    # Calculate position sizing
    risk_amount = 100000 * 0.02
    quantity = int(risk_amount / (current_atr * 2)) if current_atr > 0 else 1
    
    stop_loss = current_price - (current_atr * 2) if signal == 1 else current_price + (current_atr * 2)
    take_profit = current_price + (current_atr * 4) if signal == 1 else current_price - (current_atr * 4)
    
    # Calculate confidence (how many strategies agree)
    agreeing = sum(1 for s in strategy_signals.values() if s == signal and signal != 0)
    confidence = agreeing / len(strategy_signals) if strategy_signals else 0
    
    return SignalResponse(
        symbol=symbol,
        signal=signal,
        strategy_signals=strategy_signals,
        confidence=confidence,
        current_price=current_price,
        suggested_quantity=max(1, quantity),
        stop_loss=stop_loss,
        take_profit=take_profit
    )


@app.get("/api/engine/metrics", response_model=RiskMetrics)
async def get_risk_metrics():
    """Get current risk metrics"""
    global trading_engine
    
    if not trading_engine:
        return RiskMetrics(
            total_capital=0.0,
            available_capital=0.0,
            daily_pnl=0.0,
            daily_trades=0,
            max_drawdown=0.0,
            win_rate=0.0,
            profit_factor=0.0,
            sharpe_ratio=0.0
        )
    
    metrics = trading_engine.money_manager.get_risk_metrics()
    return RiskMetrics(
        total_capital=metrics.total_capital,
        available_capital=metrics.available_capital,
        daily_pnl=metrics.daily_pnl,
        daily_trades=metrics.daily_trades,
        max_drawdown=metrics.max_drawdown,
        win_rate=metrics.win_rate,
        profit_factor=metrics.profit_factor,
        sharpe_ratio=metrics.sharpe_ratio
    )


# ============ Market Data Endpoints ============

@app.get("/api/symbols")
async def get_default_symbols():
    """Get default trading symbols"""
    return {"symbols": DEFAULT_SYMBOLS}


@app.get("/api/market/{symbol}")
async def get_market_data(symbol: str, interval: str = "5m", limit: int = 100):
    """Get market data for a symbol"""
    global trading_engine
    
    if trading_engine:
        data = trading_engine.fetch_market_data(symbol, interval, limit)
    else:
        temp_engine = TradingEngine(
            user_id="temp",
            api_key="",
            api_secret="",
            initial_capital=100000.0
        )
        data = temp_engine.fetch_market_data(symbol, interval, limit)
    
    if data is None:
        raise HTTPException(status_code=400, detail="Failed to fetch market data")
    
    candles = []
    for idx, row in data.iterrows():
        candles.append({
            "timestamp": idx.isoformat(),
            "open": float(row['open']),
            "high": float(row['high']),
            "low": float(row['low']),
            "close": float(row['close']),
            "volume": int(row['volume'])
        })
    
    current_price = float(data['close'].iloc[-1])
    prev_close = float(data['close'].iloc[-2]) if len(data) > 1 else current_price
    change_percent = ((current_price - prev_close) / prev_close) * 100
    
    return {
        "symbol": symbol,
        "candles": candles,
        "current_price": current_price,
        "change_percent": round(change_percent, 2)
    }


# ============ Backtest Endpoints ============

@app.post("/api/backtest", response_model=BacktestResult)
async def run_backtest(request: BacktestRequest):
    """Run a backtest for a strategy"""
    # This is a simplified backtest - in production you'd want more sophisticated logic
    from strategies import get_strategy as get_strat
    from indicators import calculate_atr
    import pandas as pd
    
    temp_engine = TradingEngine(
        user_id="backtest",
        api_key="",
        api_secret="",
        initial_capital=request.initial_capital
    )
    
    data = temp_engine.fetch_market_data(request.symbol, limit=500)
    if data is None:
        raise HTTPException(status_code=400, detail="Failed to fetch market data")
    
    try:
        strategy = get_strat(request.strategy, request.parameters)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    
    trades = []
    position = None
    capital = request.initial_capital
    
    for i in range(50, len(data)):
        window = data.iloc[:i+1]
        signal = strategy.generate_signal(window)
        current_price = float(window['close'].iloc[-1])
        
        if position is None and signal == 1:
            # Open long position
            quantity = int((capital * 0.02) / current_price)
            if quantity > 0:
                position = {
                    "entry_price": current_price,
                    "quantity": quantity,
                    "side": "BUY",
                    "entry_idx": i
                }
        elif position is None and signal == -1:
            # Open short position
            quantity = int((capital * 0.02) / current_price)
            if quantity > 0:
                position = {
                    "entry_price": current_price,
                    "quantity": quantity,
                    "side": "SELL",
                    "entry_idx": i
                }
        elif position is not None:
            # Check for exit
            if (position["side"] == "BUY" and signal == -1) or \
               (position["side"] == "SELL" and signal == 1):
                # Close position
                if position["side"] == "BUY":
                    pnl = (current_price - position["entry_price"]) * position["quantity"]
                else:
                    pnl = (position["entry_price"] - current_price) * position["quantity"]
                
                capital += pnl
                trades.append({
                    "entry_price": position["entry_price"],
                    "exit_price": current_price,
                    "quantity": position["quantity"],
                    "side": position["side"],
                    "pnl": pnl
                })
                position = None
    
    # Calculate metrics
    if len(trades) == 0:
        return BacktestResult(
            total_trades=0,
            winning_trades=0,
            losing_trades=0,
            win_rate=0.0,
            total_pnl=0.0,
            max_drawdown=0.0,
            sharpe_ratio=0.0,
            profit_factor=0.0,
            trades=[]
        )
    
    winning = [t for t in trades if t["pnl"] > 0]
    losing = [t for t in trades if t["pnl"] < 0]
    
    gross_profit = sum(t["pnl"] for t in winning)
    gross_loss = abs(sum(t["pnl"] for t in losing))
    
    return BacktestResult(
        total_trades=len(trades),
        winning_trades=len(winning),
        losing_trades=len(losing),
        win_rate=(len(winning) / len(trades)) * 100 if trades else 0.0,
        total_pnl=capital - request.initial_capital,
        max_drawdown=0.0,  # Simplified
        sharpe_ratio=0.0,  # Simplified
        profit_factor=gross_profit / gross_loss if gross_loss > 0 else float('inf'),
        trades=trades
    )


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 5000))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=True)
