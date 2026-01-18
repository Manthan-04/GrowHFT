# High Frequency Trading Dashboard

## Overview
A professional-grade algorithmic trading system for the Indian stock market (NSE/BSE) using the Groww API. Features a React dashboard for monitoring and a Python trading engine with multiple famous strategies.

## Architecture

### Frontend (React + TypeScript)
- **Dashboard**: Real-time overview of trading performance, P&L, active strategies
- **Strategies Page**: Configure and toggle trading strategies
- **Trades Page**: Historical trade log with detailed analytics
- **Settings**: Groww API credentials configuration

### Backend (Node.js + Express)
- RESTful API for frontend communication
- PostgreSQL database for persistence
- Replit Auth for user authentication

### Trading Engine (Python)
Located in `server/python/`:
- `engine.py` - Main trading loop, connects to Groww API
- `strategies.py` - All trading strategy implementations
- `indicators.py` - Technical indicators using TA-Lib
- `money_management.py` - Risk management and position sizing
- `config.py` - Configuration parameters

## Trading Strategies Implemented

### 1. Moving Average Crossover (Golden Cross/Death Cross)
- **Signal**: BUY when short MA crosses above long MA, SELL when it crosses below
- **Parameters**: shortWindow (20), longWindow (50), useEma (false)
- **Best for**: Trending markets

### 2. RSI Mean Reversion
- **Signal**: BUY when RSI < 30 (oversold), SELL when RSI > 70 (overbought)
- **Parameters**: rsiPeriod (14), overbought (70), oversold (30)
- **Best for**: Range-bound markets

### 3. MACD Strategy
- **Signal**: BUY when MACD crosses above signal line, SELL when it crosses below
- **Parameters**: fast (12), slow (26), signal (9)
- **Best for**: Momentum trading

### 4. Bollinger Bands
- **Signal**: BUY at lower band, SELL at upper band
- **Parameters**: period (20), stdDev (2.0)
- **Best for**: Mean reversion in volatile markets

### 5. VWAP Strategy
- **Signal**: BUY when price crosses above VWAP with volume confirmation
- **Parameters**: volumeThreshold (1.5)
- **Best for**: Intraday trading

### 6. SuperTrend
- **Signal**: Trend-following with ATR-based dynamic support/resistance
- **Parameters**: period (10), multiplier (3.0)
- **Best for**: Strong trending markets

### 7. Stochastic RSI
- **Signal**: Combined oscillator for stronger signals
- **Parameters**: rsiPeriod (14), stochPeriod (14)
- **Best for**: Confirmation signals

## Money Management Features

- **Position Sizing**: ATR-based volatility sizing (max 2% capital per trade)
- **Stop Loss**: Automatic 2x ATR stop loss
- **Take Profit**: 2:1 reward-to-risk ratio
- **Trailing Stop**: 1% trailing stop once in profit
- **Daily Loss Limit**: 5% maximum daily loss
- **Kelly Criterion**: Optimal position sizing based on win rate

## Database Schema

### Users (from Replit Auth)
- id, email, firstName, lastName, growwApiKey, growwApiSecret

### Strategies
- id, name, description, isActive, parameters (JSON), createdAt

### Trades
- id, userId, symbol, side, quantity, price, status, timestamp, strategyId, pnl

## Running the Trading Engine

```bash
cd server/python
python engine.py
```

Environment variables needed:
- `DATABASE_URL` - PostgreSQL connection string
- `GROWW_API_KEY` - Your Groww API key
- `GROWW_API_SECRET` - Your Groww API secret
- `INITIAL_CAPITAL` - Starting capital (default: 100000)

## Default Symbols Traded
RELIANCE, TCS, HDFCBANK, INFY, ICICIBANK, HINDUNILVR, SBIN, BHARTIARTL, KOTAKBANK, ITC

## Market Hours
- NSE Trading: 9:15 AM - 3:30 PM IST
- Engine automatically pauses outside market hours

## User Preferences
- Dark theme by default (fintech standard)
- Real-time data refresh every 5 seconds
