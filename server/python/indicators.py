"""
Technical Indicators for Trading Strategies
Uses TA-Lib for efficient calculations
"""
import numpy as np
import pandas as pd
import talib

def calculate_sma(prices: pd.Series, period: int) -> pd.Series:
    """Simple Moving Average"""
    return talib.SMA(prices, timeperiod=period)

def calculate_ema(prices: pd.Series, period: int) -> pd.Series:
    """Exponential Moving Average"""
    return talib.EMA(prices, timeperiod=period)

def calculate_rsi(prices: pd.Series, period: int = 14) -> pd.Series:
    """Relative Strength Index"""
    return talib.RSI(prices, timeperiod=period)

def calculate_macd(prices: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9):
    """MACD - Moving Average Convergence Divergence"""
    macd, macd_signal, macd_hist = talib.MACD(prices, fastperiod=fast, slowperiod=slow, signalperiod=signal)
    return macd, macd_signal, macd_hist

def calculate_bollinger_bands(prices: pd.Series, period: int = 20, std_dev: float = 2.0):
    """Bollinger Bands"""
    upper, middle, lower = talib.BBANDS(prices, timeperiod=period, nbdevup=std_dev, nbdevdn=std_dev)
    return upper, middle, lower

def calculate_atr(high: pd.Series, low: pd.Series, close: pd.Series, period: int = 14) -> pd.Series:
    """Average True Range - for volatility and position sizing"""
    return talib.ATR(high, low, close, timeperiod=period)

def calculate_adx(high: pd.Series, low: pd.Series, close: pd.Series, period: int = 14) -> pd.Series:
    """Average Directional Index - trend strength"""
    return talib.ADX(high, low, close, timeperiod=period)

def calculate_stochastic(high: pd.Series, low: pd.Series, close: pd.Series, 
                         fastk_period: int = 14, slowk_period: int = 3, slowd_period: int = 3):
    """Stochastic Oscillator"""
    slowk, slowd = talib.STOCH(high, low, close, 
                               fastk_period=fastk_period, 
                               slowk_period=slowk_period, 
                               slowd_period=slowd_period)
    return slowk, slowd

def calculate_vwap(high: pd.Series, low: pd.Series, close: pd.Series, volume: pd.Series) -> pd.Series:
    """Volume Weighted Average Price"""
    typical_price = (high + low + close) / 3
    vwap = (typical_price * volume).cumsum() / volume.cumsum()
    return vwap

def calculate_supertrend(high: pd.Series, low: pd.Series, close: pd.Series, 
                         period: int = 10, multiplier: float = 3.0):
    """SuperTrend Indicator"""
    atr = calculate_atr(high, low, close, period)
    
    hl2 = (high + low) / 2
    upper_band = hl2 + (multiplier * atr)
    lower_band = hl2 - (multiplier * atr)
    
    supertrend = pd.Series(index=close.index, dtype=float)
    direction = pd.Series(index=close.index, dtype=int)
    
    for i in range(period, len(close)):
        if close.iloc[i] > upper_band.iloc[i-1]:
            direction.iloc[i] = 1
        elif close.iloc[i] < lower_band.iloc[i-1]:
            direction.iloc[i] = -1
        else:
            direction.iloc[i] = direction.iloc[i-1] if i > period else 1
            
        if direction.iloc[i] == 1:
            supertrend.iloc[i] = lower_band.iloc[i]
        else:
            supertrend.iloc[i] = upper_band.iloc[i]
    
    return supertrend, direction

def calculate_momentum(prices: pd.Series, period: int = 10) -> pd.Series:
    """Momentum indicator"""
    return talib.MOM(prices, timeperiod=period)

def calculate_williams_r(high: pd.Series, low: pd.Series, close: pd.Series, period: int = 14) -> pd.Series:
    """Williams %R"""
    return talib.WILLR(high, low, close, timeperiod=period)

def detect_candlestick_patterns(open_prices: pd.Series, high: pd.Series, 
                                  low: pd.Series, close: pd.Series) -> dict:
    """Detect common candlestick patterns"""
    patterns = {
        'doji': talib.CDLDOJI(open_prices, high, low, close),
        'hammer': talib.CDLHAMMER(open_prices, high, low, close),
        'engulfing': talib.CDLENGULFING(open_prices, high, low, close),
        'morning_star': talib.CDLMORNINGSTAR(open_prices, high, low, close),
        'evening_star': talib.CDLEVENINGSTAR(open_prices, high, low, close),
        'three_white_soldiers': talib.CDL3WHITESOLDIERS(open_prices, high, low, close),
        'three_black_crows': talib.CDL3BLACKCROWS(open_prices, high, low, close),
    }
    return patterns
