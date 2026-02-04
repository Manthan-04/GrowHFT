"""
Pydantic Schemas for API Request/Response Validation
"""
from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


# ============ User Schemas ============

class UserBase(BaseModel):
    email: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None


class UserCreate(UserBase):
    id: str


class UserUpdate(BaseModel):
    groww_api_key: Optional[str] = None
    groww_api_secret: Optional[str] = None
    initial_capital: Optional[float] = None


class UserResponse(UserBase):
    id: str
    profile_image_url: Optional[str] = None
    initial_capital: float = 100000.0
    created_at: datetime
    
    class Config:
        from_attributes = True


# ============ Strategy Schemas ============

class StrategyBase(BaseModel):
    name: str
    description: Optional[str] = None
    is_active: bool = False
    parameters: Dict[str, Any] = {}


class StrategyCreate(StrategyBase):
    pass


class StrategyUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None
    parameters: Optional[Dict[str, Any]] = None


class StrategyResponse(StrategyBase):
    id: int
    created_at: datetime
    
    class Config:
        from_attributes = True


# ============ Trade Schemas ============

class TradeBase(BaseModel):
    symbol: str
    side: str  # 'BUY' or 'SELL'
    quantity: int
    price: str
    status: str


class TradeCreate(TradeBase):
    user_id: str
    strategy_id: Optional[int] = None


class TradeUpdate(BaseModel):
    status: Optional[str] = None
    pnl: Optional[str] = None
    exit_price: Optional[str] = None
    exit_timestamp: Optional[datetime] = None
    exit_reason: Optional[str] = None


class TradeResponse(TradeBase):
    id: int
    user_id: str
    strategy_id: Optional[int] = None
    timestamp: datetime
    pnl: Optional[str] = None
    exit_price: Optional[str] = None
    exit_reason: Optional[str] = None
    
    class Config:
        from_attributes = True


# ============ Trading Engine Schemas ============

class EngineStatus(BaseModel):
    is_running: bool
    is_market_hours: bool
    active_strategies: List[str]
    open_positions: int
    daily_trades: int
    daily_pnl: float
    current_capital: float


class EngineConfig(BaseModel):
    symbols: List[str] = []
    initial_capital: float = 100000.0
    max_position_size_percent: float = 2.0
    max_daily_loss_percent: float = 5.0
    stop_loss_percent: float = 1.5
    take_profit_percent: float = 3.0


class SignalResponse(BaseModel):
    symbol: str
    signal: int  # 1 (BUY), -1 (SELL), 0 (HOLD)
    strategy_signals: Dict[str, int]
    confidence: float
    current_price: float
    suggested_quantity: int
    stop_loss: float
    take_profit: float


class BacktestRequest(BaseModel):
    symbol: str
    strategy: str
    start_date: str
    end_date: str
    initial_capital: float = 100000.0
    parameters: Dict[str, Any] = {}


class BacktestResult(BaseModel):
    total_trades: int
    winning_trades: int
    losing_trades: int
    win_rate: float
    total_pnl: float
    max_drawdown: float
    sharpe_ratio: float
    profit_factor: float
    trades: List[Dict[str, Any]]


# ============ Risk Metrics ============

class RiskMetrics(BaseModel):
    total_capital: float
    available_capital: float
    daily_pnl: float
    daily_trades: int
    max_drawdown: float
    win_rate: float
    profit_factor: float
    sharpe_ratio: float


# ============ Market Data ============

class CandleData(BaseModel):
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: int


class MarketDataResponse(BaseModel):
    symbol: str
    candles: List[CandleData]
    current_price: float
    change_percent: float
