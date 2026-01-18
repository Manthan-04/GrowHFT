"""
Famous Trading Strategies Implementation
Each strategy returns a signal: 1 (BUY), -1 (SELL), 0 (HOLD)
"""
import pandas as pd
import numpy as np
from typing import Tuple, Optional
from indicators import (
    calculate_sma, calculate_ema, calculate_rsi, calculate_macd,
    calculate_bollinger_bands, calculate_atr, calculate_adx,
    calculate_stochastic, calculate_vwap, calculate_supertrend,
    calculate_momentum, detect_candlestick_patterns
)
from config import *


class BaseStrategy:
    """Base class for all trading strategies"""
    
    def __init__(self, name: str):
        self.name = name
        self.positions = {}
        
    def generate_signal(self, data: pd.DataFrame) -> int:
        """Override in subclass. Returns 1 (BUY), -1 (SELL), 0 (HOLD)"""
        raise NotImplementedError
    
    def calculate_position_size(self, capital: float, price: float, atr: float) -> int:
        """Calculate position size based on ATR volatility"""
        risk_amount = capital * (MAX_POSITION_SIZE_PERCENT / 100)
        position_value = risk_amount / (atr * 2) if atr > 0 else risk_amount / price
        shares = int(position_value / price)
        return max(1, shares)


class MovingAverageCrossover(BaseStrategy):
    """
    Golden Cross / Death Cross Strategy
    - BUY when short MA crosses above long MA
    - SELL when short MA crosses below long MA
    """
    
    def __init__(self, short_period: int = 20, long_period: int = 50, use_ema: bool = False):
        super().__init__("Moving Average Crossover")
        self.short_period = short_period
        self.long_period = long_period
        self.use_ema = use_ema
        
    def generate_signal(self, data: pd.DataFrame) -> int:
        close = data['close']
        
        if self.use_ema:
            short_ma = calculate_ema(close, self.short_period)
            long_ma = calculate_ema(close, self.long_period)
        else:
            short_ma = calculate_sma(close, self.short_period)
            long_ma = calculate_sma(close, self.long_period)
        
        if len(short_ma) < 2 or pd.isna(short_ma.iloc[-1]) or pd.isna(long_ma.iloc[-1]):
            return 0
            
        # Golden Cross - short crosses above long
        if short_ma.iloc[-2] <= long_ma.iloc[-2] and short_ma.iloc[-1] > long_ma.iloc[-1]:
            return 1
        # Death Cross - short crosses below long
        elif short_ma.iloc[-2] >= long_ma.iloc[-2] and short_ma.iloc[-1] < long_ma.iloc[-1]:
            return -1
            
        return 0


class RSIMeanReversion(BaseStrategy):
    """
    RSI Mean Reversion Strategy
    - BUY when RSI < oversold level (default 30)
    - SELL when RSI > overbought level (default 70)
    """
    
    def __init__(self, period: int = 14, overbought: int = 70, oversold: int = 30):
        super().__init__("RSI Mean Reversion")
        self.period = period
        self.overbought = overbought
        self.oversold = oversold
        
    def generate_signal(self, data: pd.DataFrame) -> int:
        close = data['close']
        rsi = calculate_rsi(close, self.period)
        
        if pd.isna(rsi.iloc[-1]):
            return 0
            
        current_rsi = rsi.iloc[-1]
        prev_rsi = rsi.iloc[-2] if len(rsi) > 1 else current_rsi
        
        # Oversold - potential buy
        if current_rsi < self.oversold and prev_rsi >= self.oversold:
            return 1
        # Overbought - potential sell
        elif current_rsi > self.overbought and prev_rsi <= self.overbought:
            return -1
            
        return 0


class BollingerBandStrategy(BaseStrategy):
    """
    Bollinger Bands Mean Reversion
    - BUY when price touches lower band
    - SELL when price touches upper band
    """
    
    def __init__(self, period: int = 20, std_dev: float = 2.0):
        super().__init__("Bollinger Bands")
        self.period = period
        self.std_dev = std_dev
        
    def generate_signal(self, data: pd.DataFrame) -> int:
        close = data['close']
        upper, middle, lower = calculate_bollinger_bands(close, self.period, self.std_dev)
        
        if pd.isna(upper.iloc[-1]) or pd.isna(lower.iloc[-1]):
            return 0
            
        current_price = close.iloc[-1]
        prev_price = close.iloc[-2] if len(close) > 1 else current_price
        
        # Price crosses below lower band - BUY
        if prev_price >= lower.iloc[-2] and current_price < lower.iloc[-1]:
            return 1
        # Price crosses above upper band - SELL
        elif prev_price <= upper.iloc[-2] and current_price > upper.iloc[-1]:
            return -1
            
        return 0


class MACDStrategy(BaseStrategy):
    """
    MACD Crossover Strategy
    - BUY when MACD crosses above signal line
    - SELL when MACD crosses below signal line
    """
    
    def __init__(self, fast: int = 12, slow: int = 26, signal: int = 9):
        super().__init__("MACD")
        self.fast = fast
        self.slow = slow
        self.signal = signal
        
    def generate_signal(self, data: pd.DataFrame) -> int:
        close = data['close']
        macd, macd_signal, macd_hist = calculate_macd(close, self.fast, self.slow, self.signal)
        
        if pd.isna(macd.iloc[-1]) or pd.isna(macd_signal.iloc[-1]):
            return 0
            
        # MACD crosses above signal - BUY
        if macd.iloc[-2] <= macd_signal.iloc[-2] and macd.iloc[-1] > macd_signal.iloc[-1]:
            return 1
        # MACD crosses below signal - SELL
        elif macd.iloc[-2] >= macd_signal.iloc[-2] and macd.iloc[-1] < macd_signal.iloc[-1]:
            return -1
            
        return 0


class VWAPStrategy(BaseStrategy):
    """
    VWAP Strategy for Intraday Trading
    - BUY when price crosses above VWAP with volume confirmation
    - SELL when price crosses below VWAP
    """
    
    def __init__(self, volume_threshold: float = 1.5):
        super().__init__("VWAP")
        self.volume_threshold = volume_threshold
        
    def generate_signal(self, data: pd.DataFrame) -> int:
        if 'volume' not in data.columns:
            return 0
            
        vwap = calculate_vwap(data['high'], data['low'], data['close'], data['volume'])
        
        if pd.isna(vwap.iloc[-1]):
            return 0
            
        close = data['close']
        volume = data['volume']
        avg_volume = volume.rolling(20).mean()
        
        current_price = close.iloc[-1]
        prev_price = close.iloc[-2] if len(close) > 1 else current_price
        current_vwap = vwap.iloc[-1]
        prev_vwap = vwap.iloc[-2] if len(vwap) > 1 else current_vwap
        
        # Volume confirmation
        volume_confirmed = volume.iloc[-1] > (avg_volume.iloc[-1] * self.volume_threshold)
        
        # Price crosses above VWAP with volume
        if prev_price <= prev_vwap and current_price > current_vwap and volume_confirmed:
            return 1
        # Price crosses below VWAP
        elif prev_price >= prev_vwap and current_price < current_vwap:
            return -1
            
        return 0


class SuperTrendStrategy(BaseStrategy):
    """
    SuperTrend Strategy - Trend Following
    - BUY when price is above SuperTrend and direction changes to bullish
    - SELL when price is below SuperTrend and direction changes to bearish
    """
    
    def __init__(self, period: int = 10, multiplier: float = 3.0):
        super().__init__("SuperTrend")
        self.period = period
        self.multiplier = multiplier
        
    def generate_signal(self, data: pd.DataFrame) -> int:
        supertrend, direction = calculate_supertrend(
            data['high'], data['low'], data['close'], 
            self.period, self.multiplier
        )
        
        if pd.isna(direction.iloc[-1]):
            return 0
            
        # Direction changes to bullish - BUY
        if direction.iloc[-2] == -1 and direction.iloc[-1] == 1:
            return 1
        # Direction changes to bearish - SELL
        elif direction.iloc[-2] == 1 and direction.iloc[-1] == -1:
            return -1
            
        return 0


class StochasticRSIStrategy(BaseStrategy):
    """
    Combined Stochastic + RSI Strategy
    More reliable signals by combining two oscillators
    """
    
    def __init__(self, rsi_period: int = 14, stoch_period: int = 14):
        super().__init__("Stochastic RSI")
        self.rsi_period = rsi_period
        self.stoch_period = stoch_period
        
    def generate_signal(self, data: pd.DataFrame) -> int:
        close = data['close']
        rsi = calculate_rsi(close, self.rsi_period)
        slowk, slowd = calculate_stochastic(
            data['high'], data['low'], data['close'], 
            self.stoch_period
        )
        
        if pd.isna(rsi.iloc[-1]) or pd.isna(slowk.iloc[-1]):
            return 0
        
        # Both oversold - strong BUY signal
        if rsi.iloc[-1] < 30 and slowk.iloc[-1] < 20:
            return 1
        # Both overbought - strong SELL signal
        elif rsi.iloc[-1] > 70 and slowk.iloc[-1] > 80:
            return -1
            
        return 0


class MultiStrategyEngine:
    """
    Combines multiple strategies with weighted voting
    """
    
    def __init__(self):
        self.strategies = {
            'ma_crossover': (MovingAverageCrossover(SMA_SHORT, SMA_LONG), 1.0),
            'ema_crossover': (MovingAverageCrossover(EMA_SHORT, EMA_LONG, use_ema=True), 1.0),
            'rsi': (RSIMeanReversion(RSI_PERIOD, RSI_OVERBOUGHT, RSI_OVERSOLD), 0.8),
            'bollinger': (BollingerBandStrategy(BOLLINGER_PERIOD, BOLLINGER_STD), 0.7),
            'macd': (MACDStrategy(MACD_FAST, MACD_SLOW, MACD_SIGNAL), 1.0),
            'vwap': (VWAPStrategy(), 0.9),
            'supertrend': (SuperTrendStrategy(), 1.2),
            'stoch_rsi': (StochasticRSIStrategy(), 0.8),
        }
        
    def get_combined_signal(self, data: pd.DataFrame, active_strategies: list = None) -> Tuple[int, dict]:
        """
        Get weighted signal from all active strategies
        Returns: (signal, details_dict)
        """
        if active_strategies is None:
            active_strategies = list(self.strategies.keys())
            
        signals = {}
        weighted_sum = 0.0
        total_weight = 0.0
        
        for name in active_strategies:
            if name in self.strategies:
                strategy, weight = self.strategies[name]
                try:
                    signal = strategy.generate_signal(data)
                    signals[name] = signal
                    weighted_sum += signal * weight
                    total_weight += weight
                except Exception as e:
                    signals[name] = 0
                    
        # Normalize the weighted sum
        if total_weight > 0:
            normalized_signal = weighted_sum / total_weight
        else:
            normalized_signal = 0
            
        # Convert to discrete signal
        if normalized_signal > 0.3:
            final_signal = 1
        elif normalized_signal < -0.3:
            final_signal = -1
        else:
            final_signal = 0
            
        return final_signal, signals


# Strategy factory
def get_strategy(name: str, params: dict = None) -> BaseStrategy:
    """Factory function to get strategy by name"""
    params = params or {}
    
    strategies = {
        'ma_crossover': lambda: MovingAverageCrossover(
            params.get('shortWindow', SMA_SHORT),
            params.get('longWindow', SMA_LONG),
            params.get('useEma', False)
        ),
        'rsi': lambda: RSIMeanReversion(
            params.get('rsiPeriod', RSI_PERIOD),
            params.get('overbought', RSI_OVERBOUGHT),
            params.get('oversold', RSI_OVERSOLD)
        ),
        'bollinger': lambda: BollingerBandStrategy(
            params.get('period', BOLLINGER_PERIOD),
            params.get('stdDev', BOLLINGER_STD)
        ),
        'macd': lambda: MACDStrategy(
            params.get('fast', MACD_FAST),
            params.get('slow', MACD_SLOW),
            params.get('signal', MACD_SIGNAL)
        ),
        'vwap': lambda: VWAPStrategy(
            params.get('volumeThreshold', 1.5)
        ),
        'supertrend': lambda: SuperTrendStrategy(
            params.get('period', 10),
            params.get('multiplier', 3.0)
        ),
        'stoch_rsi': lambda: StochasticRSIStrategy(
            params.get('rsiPeriod', RSI_PERIOD),
            params.get('stochPeriod', 14)
        ),
    }
    
    if name in strategies:
        return strategies[name]()
    
    raise ValueError(f"Unknown strategy: {name}")
