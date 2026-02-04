"""
Database Configuration and Models using SQLAlchemy
"""
import os
from datetime import datetime
from typing import Optional
from sqlalchemy import create_engine, Column, Integer, String, Boolean, DateTime, Float, Text, ForeignKey, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


class User(Base):
    """User model for authentication and API key storage"""
    __tablename__ = "users"
    
    id = Column(String, primary_key=True)
    email = Column(String, unique=True, nullable=True)
    first_name = Column(String, nullable=True)
    last_name = Column(String, nullable=True)
    profile_image_url = Column(String, nullable=True)
    groww_api_key = Column(String, nullable=True)
    groww_api_secret = Column(String, nullable=True)
    initial_capital = Column(Float, default=100000.0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    trades = relationship("Trade", back_populates="user")


class Strategy(Base):
    """Trading strategy configuration"""
    __tablename__ = "strategies"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    is_active = Column(Boolean, default=False)
    parameters = Column(JSON, default={})
    created_at = Column(DateTime, default=datetime.utcnow)
    
    trades = relationship("Trade", back_populates="strategy")


class Trade(Base):
    """Trade execution record"""
    __tablename__ = "trades"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    symbol = Column(String, nullable=False)
    side = Column(String, nullable=False)  # 'BUY' or 'SELL'
    quantity = Column(Integer, nullable=False)
    price = Column(String, nullable=False)
    status = Column(String, nullable=False)  # 'PENDING', 'EXECUTED', 'CANCELLED', 'FAILED'
    timestamp = Column(DateTime, default=datetime.utcnow)
    strategy_id = Column(Integer, ForeignKey("strategies.id"), nullable=True)
    pnl = Column(String, nullable=True)
    exit_price = Column(String, nullable=True)
    exit_timestamp = Column(DateTime, nullable=True)
    exit_reason = Column(String, nullable=True)
    
    user = relationship("User", back_populates="trades")
    strategy = relationship("Strategy", back_populates="trades")


class TradingSession(Base):
    """Daily trading session statistics"""
    __tablename__ = "trading_sessions"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    date = Column(DateTime, nullable=False)
    starting_capital = Column(Float, nullable=False)
    ending_capital = Column(Float, nullable=True)
    total_trades = Column(Integer, default=0)
    winning_trades = Column(Integer, default=0)
    losing_trades = Column(Integer, default=0)
    gross_profit = Column(Float, default=0.0)
    gross_loss = Column(Float, default=0.0)
    net_pnl = Column(Float, default=0.0)
    max_drawdown = Column(Float, default=0.0)
    created_at = Column(DateTime, default=datetime.utcnow)


def get_db():
    """Dependency to get database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Initialize database tables"""
    Base.metadata.create_all(bind=engine)
    
    # Seed default strategies if not exist
    db = SessionLocal()
    try:
        existing = db.query(Strategy).count()
        if existing == 0:
            default_strategies = [
                Strategy(
                    name="Moving Average Crossover",
                    description="Golden Cross/Death Cross - Buy when short MA crosses above long MA, sell when it crosses below",
                    is_active=True,
                    parameters={"shortWindow": 20, "longWindow": 50, "useEma": False}
                ),
                Strategy(
                    name="RSI Mean Reversion",
                    description="Buy when RSI < 30 (oversold), Sell when RSI > 70 (overbought)",
                    is_active=True,
                    parameters={"rsiPeriod": 14, "overbought": 70, "oversold": 30}
                ),
                Strategy(
                    name="MACD Strategy",
                    description="Buy when MACD crosses above signal line, sell when it crosses below",
                    is_active=True,
                    parameters={"fast": 12, "slow": 26, "signal": 9}
                ),
                Strategy(
                    name="Bollinger Bands",
                    description="Mean reversion - Buy at lower band, sell at upper band",
                    is_active=False,
                    parameters={"period": 20, "stdDev": 2.0}
                ),
                Strategy(
                    name="VWAP Strategy",
                    description="Intraday momentum - Trade based on price crossing VWAP with volume confirmation",
                    is_active=False,
                    parameters={"volumeThreshold": 1.5}
                ),
                Strategy(
                    name="SuperTrend",
                    description="Trend following strategy with ATR-based dynamic support/resistance",
                    is_active=True,
                    parameters={"period": 10, "multiplier": 3.0}
                ),
                Strategy(
                    name="Stochastic RSI",
                    description="Combined oscillator - Strong signals when both RSI and Stochastic agree",
                    is_active=False,
                    parameters={"rsiPeriod": 14, "stochPeriod": 14}
                ),
            ]
            db.add_all(default_strategies)
            db.commit()
            print("Seeded default strategies")
    finally:
        db.close()
