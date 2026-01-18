"""
Configuration for the HFT Trading Engine
"""
import os
from dotenv import load_dotenv

load_dotenv()

# Database Configuration
DATABASE_URL = os.getenv("DATABASE_URL")

# Trading Configuration
MAX_POSITION_SIZE_PERCENT = 2.0  # Maximum 2% of capital per trade
MAX_DAILY_LOSS_PERCENT = 5.0    # Stop trading if daily loss exceeds 5%
MAX_TRADES_PER_DAY = 50         # Maximum trades per day per symbol

# Risk Management
STOP_LOSS_PERCENT = 1.5         # Default stop loss percentage
TAKE_PROFIT_PERCENT = 3.0       # Default take profit percentage
TRAILING_STOP_PERCENT = 1.0     # Trailing stop percentage

# Technical Indicator Defaults
RSI_PERIOD = 14
RSI_OVERBOUGHT = 70
RSI_OVERSOLD = 30

MACD_FAST = 12
MACD_SLOW = 26
MACD_SIGNAL = 9

BOLLINGER_PERIOD = 20
BOLLINGER_STD = 2

SMA_SHORT = 20
SMA_LONG = 50
EMA_SHORT = 12
EMA_LONG = 26

# Market Hours (IST)
MARKET_OPEN_HOUR = 9
MARKET_OPEN_MINUTE = 15
MARKET_CLOSE_HOUR = 15
MARKET_CLOSE_MINUTE = 30

# Symbols to Trade (Indian Stock Market - NSE)
DEFAULT_SYMBOLS = [
    "RELIANCE",
    "TCS",
    "HDFCBANK",
    "INFY",
    "ICICIBANK",
    "HINDUNILVR",
    "SBIN",
    "BHARTIARTL",
    "KOTAKBANK",
    "ITC"
]
