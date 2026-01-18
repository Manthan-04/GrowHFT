"""
Money Management and Risk Control Module
Implements professional-grade risk management for HFT
"""
import pandas as pd
import numpy as np
from dataclasses import dataclass
from typing import Optional, Tuple
from datetime import datetime, timedelta
from config import *


@dataclass
class Position:
    """Represents an open position"""
    symbol: str
    side: str  # 'BUY' or 'SELL'
    quantity: int
    entry_price: float
    entry_time: datetime
    stop_loss: float
    take_profit: float
    trailing_stop: Optional[float] = None
    highest_price: Optional[float] = None  # For trailing stop
    lowest_price: Optional[float] = None   # For short trailing stop
    

@dataclass
class RiskMetrics:
    """Risk metrics for the trading session"""
    total_capital: float
    available_capital: float
    daily_pnl: float
    daily_trades: int
    max_drawdown: float
    win_rate: float
    profit_factor: float
    sharpe_ratio: float


class MoneyManager:
    """
    Professional Money Management System
    - Position sizing based on volatility (ATR)
    - Fixed percentage risk per trade
    - Daily loss limits
    - Maximum position limits
    """
    
    def __init__(self, initial_capital: float):
        self.initial_capital = initial_capital
        self.current_capital = initial_capital
        self.positions: dict[str, Position] = {}
        self.daily_pnl = 0.0
        self.daily_trades = 0
        self.trade_history = []
        self.equity_curve = [initial_capital]
        self.last_reset_date = datetime.now().date()
        
    def reset_daily_stats(self):
        """Reset daily statistics at market open"""
        today = datetime.now().date()
        if today > self.last_reset_date:
            self.daily_pnl = 0.0
            self.daily_trades = 0
            self.last_reset_date = today
            
    def can_trade(self) -> Tuple[bool, str]:
        """Check if trading is allowed based on risk limits"""
        self.reset_daily_stats()
        
        # Check daily loss limit
        daily_loss_limit = self.initial_capital * (MAX_DAILY_LOSS_PERCENT / 100)
        if self.daily_pnl < -daily_loss_limit:
            return False, f"Daily loss limit reached: {self.daily_pnl:.2f}"
            
        # Check maximum trades per day
        if self.daily_trades >= MAX_TRADES_PER_DAY:
            return False, f"Maximum daily trades reached: {self.daily_trades}"
            
        return True, "Trading allowed"
        
    def calculate_position_size(self, symbol: str, price: float, atr: float) -> int:
        """
        Calculate optimal position size using ATR-based volatility sizing
        Risk = (Entry - Stop Loss) * Shares <= Max Risk Per Trade
        """
        # Maximum risk amount per trade
        risk_amount = self.current_capital * (MAX_POSITION_SIZE_PERCENT / 100)
        
        # Stop loss distance based on ATR
        stop_distance = atr * 2  # 2x ATR for stop loss
        
        if stop_distance <= 0:
            stop_distance = price * (STOP_LOSS_PERCENT / 100)
            
        # Calculate shares such that risk = stop_distance * shares
        if stop_distance > 0:
            shares = int(risk_amount / stop_distance)
        else:
            shares = int(risk_amount / price)
            
        # Ensure minimum 1 share
        shares = max(1, shares)
        
        # Ensure we don't exceed available capital
        max_shares = int(self.current_capital / price)
        shares = min(shares, max_shares)
        
        return shares
        
    def calculate_stop_loss(self, entry_price: float, side: str, atr: float) -> float:
        """Calculate stop loss price"""
        stop_distance = atr * 2
        
        if side == 'BUY':
            return entry_price - stop_distance
        else:  # SELL/SHORT
            return entry_price + stop_distance
            
    def calculate_take_profit(self, entry_price: float, side: str, atr: float) -> float:
        """Calculate take profit price (2:1 reward-to-risk ratio)"""
        profit_distance = atr * 4  # 4x ATR for 2:1 R:R
        
        if side == 'BUY':
            return entry_price + profit_distance
        else:
            return entry_price - profit_distance
            
    def open_position(self, symbol: str, side: str, quantity: int, 
                      price: float, atr: float) -> Position:
        """Open a new position with proper risk management"""
        stop_loss = self.calculate_stop_loss(price, side, atr)
        take_profit = self.calculate_take_profit(price, side, atr)
        
        position = Position(
            symbol=symbol,
            side=side,
            quantity=quantity,
            entry_price=price,
            entry_time=datetime.now(),
            stop_loss=stop_loss,
            take_profit=take_profit,
            trailing_stop=None,
            highest_price=price if side == 'BUY' else None,
            lowest_price=price if side == 'SELL' else None
        )
        
        self.positions[symbol] = position
        self.daily_trades += 1
        
        # Deduct capital
        self.current_capital -= (quantity * price)
        
        return position
        
    def update_trailing_stop(self, symbol: str, current_price: float):
        """Update trailing stop if price moves favorably"""
        if symbol not in self.positions:
            return
            
        position = self.positions[symbol]
        trailing_distance = position.entry_price * (TRAILING_STOP_PERCENT / 100)
        
        if position.side == 'BUY':
            if position.highest_price is None or current_price > position.highest_price:
                position.highest_price = current_price
                new_stop = current_price - trailing_distance
                if position.trailing_stop is None or new_stop > position.trailing_stop:
                    position.trailing_stop = new_stop
        else:  # SELL
            if position.lowest_price is None or current_price < position.lowest_price:
                position.lowest_price = current_price
                new_stop = current_price + trailing_distance
                if position.trailing_stop is None or new_stop < position.trailing_stop:
                    position.trailing_stop = new_stop
                    
    def should_exit(self, symbol: str, current_price: float) -> Tuple[bool, str]:
        """Check if position should be exited"""
        if symbol not in self.positions:
            return False, ""
            
        position = self.positions[symbol]
        self.update_trailing_stop(symbol, current_price)
        
        if position.side == 'BUY':
            # Check stop loss
            if current_price <= position.stop_loss:
                return True, "STOP_LOSS"
            # Check trailing stop
            if position.trailing_stop and current_price <= position.trailing_stop:
                return True, "TRAILING_STOP"
            # Check take profit
            if current_price >= position.take_profit:
                return True, "TAKE_PROFIT"
        else:  # SELL
            if current_price >= position.stop_loss:
                return True, "STOP_LOSS"
            if position.trailing_stop and current_price >= position.trailing_stop:
                return True, "TRAILING_STOP"
            if current_price <= position.take_profit:
                return True, "TAKE_PROFIT"
                
        return False, ""
        
    def close_position(self, symbol: str, exit_price: float, reason: str = "") -> float:
        """Close a position and calculate PnL"""
        if symbol not in self.positions:
            return 0.0
            
        position = self.positions[symbol]
        
        if position.side == 'BUY':
            pnl = (exit_price - position.entry_price) * position.quantity
        else:
            pnl = (position.entry_price - exit_price) * position.quantity
            
        # Update capital
        self.current_capital += (position.quantity * exit_price)
        self.daily_pnl += pnl
        self.equity_curve.append(self.current_capital)
        
        # Record trade
        self.trade_history.append({
            'symbol': symbol,
            'side': position.side,
            'quantity': position.quantity,
            'entry_price': position.entry_price,
            'exit_price': exit_price,
            'pnl': pnl,
            'entry_time': position.entry_time,
            'exit_time': datetime.now(),
            'reason': reason
        })
        
        del self.positions[symbol]
        return pnl
        
    def get_risk_metrics(self) -> RiskMetrics:
        """Calculate current risk metrics"""
        if len(self.trade_history) == 0:
            return RiskMetrics(
                total_capital=self.initial_capital,
                available_capital=self.current_capital,
                daily_pnl=self.daily_pnl,
                daily_trades=self.daily_trades,
                max_drawdown=0.0,
                win_rate=0.0,
                profit_factor=0.0,
                sharpe_ratio=0.0
            )
            
        # Calculate win rate
        wins = [t for t in self.trade_history if t['pnl'] > 0]
        win_rate = len(wins) / len(self.trade_history) * 100
        
        # Calculate profit factor
        gross_profit = sum(t['pnl'] for t in self.trade_history if t['pnl'] > 0)
        gross_loss = abs(sum(t['pnl'] for t in self.trade_history if t['pnl'] < 0))
        profit_factor = gross_profit / gross_loss if gross_loss > 0 else float('inf')
        
        # Calculate max drawdown
        equity = pd.Series(self.equity_curve)
        rolling_max = equity.cummax()
        drawdown = (equity - rolling_max) / rolling_max * 100
        max_drawdown = abs(drawdown.min())
        
        # Calculate Sharpe ratio (simplified daily)
        returns = equity.pct_change().dropna()
        if len(returns) > 0 and returns.std() > 0:
            sharpe_ratio = (returns.mean() / returns.std()) * np.sqrt(252)
        else:
            sharpe_ratio = 0.0
            
        return RiskMetrics(
            total_capital=self.initial_capital,
            available_capital=self.current_capital,
            daily_pnl=self.daily_pnl,
            daily_trades=self.daily_trades,
            max_drawdown=max_drawdown,
            win_rate=win_rate,
            profit_factor=profit_factor,
            sharpe_ratio=sharpe_ratio
        )


class KellyCriterion:
    """
    Kelly Criterion for optimal position sizing
    f* = (bp - q) / b
    where:
    - b = odds received on the bet
    - p = probability of winning
    - q = probability of losing (1 - p)
    """
    
    @staticmethod
    def calculate_kelly_fraction(win_rate: float, avg_win: float, avg_loss: float) -> float:
        """
        Calculate Kelly fraction
        Returns fraction of capital to risk (0 to 1)
        """
        if avg_loss == 0:
            return 0.0
            
        p = win_rate / 100  # Probability of winning
        q = 1 - p  # Probability of losing
        b = avg_win / abs(avg_loss)  # Win/loss ratio
        
        kelly = (b * p - q) / b
        
        # Use half-Kelly for safety
        half_kelly = kelly / 2
        
        # Clamp between 0 and maximum position size
        return max(0, min(half_kelly, MAX_POSITION_SIZE_PERCENT / 100))
        
    @staticmethod
    def calculate_optimal_size(capital: float, win_rate: float, 
                               avg_win: float, avg_loss: float, price: float) -> int:
        """Calculate optimal number of shares using Kelly Criterion"""
        kelly_fraction = KellyCriterion.calculate_kelly_fraction(win_rate, avg_win, avg_loss)
        risk_capital = capital * kelly_fraction
        shares = int(risk_capital / price)
        return max(1, shares)
