"""
High Frequency Trading Engine
Main execution loop that connects everything together
"""
import asyncio
import os
import sys
import json
import logging
from datetime import datetime, time
from typing import Optional, Dict, List
import pandas as pd
import psycopg2
from psycopg2.extras import RealDictCursor

# Import our modules
from config import *
from strategies import MultiStrategyEngine, get_strategy
from money_management import MoneyManager, RiskMetrics
from indicators import calculate_atr

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class TradingEngine:
    """
    Main HFT Engine that:
    1. Fetches market data from Groww API
    2. Runs multiple trading strategies
    3. Executes trades with proper risk management
    4. Records everything to database
    """
    
    def __init__(self, user_id: str, api_key: str, api_secret: str, initial_capital: float = 100000.0):
        self.user_id = user_id
        self.api_key = api_key
        self.api_secret = api_secret
        self.money_manager = MoneyManager(initial_capital)
        self.strategy_engine = MultiStrategyEngine()
        self.is_running = False
        self.groww_client = None
        self.db_conn = None
        self.active_strategies: List[str] = []
        self.symbols: List[str] = DEFAULT_SYMBOLS
        
    def connect_database(self):
        """Connect to PostgreSQL database"""
        try:
            self.db_conn = psycopg2.connect(DATABASE_URL)
            logger.info("Connected to database")
        except Exception as e:
            logger.error(f"Database connection failed: {e}")
            raise
            
    def connect_groww(self):
        """Initialize Groww API client"""
        try:
            from growwapi import GrowwAPI
            
            # Get access token
            access_token = GrowwAPI.get_access_token(
                api_key=self.api_key,
                secret=self.api_secret
            )
            
            self.groww_client = GrowwAPI(access_token)
            logger.info("Connected to Groww API")
        except Exception as e:
            logger.error(f"Groww connection failed: {e}")
            # In demo mode, we'll use simulated data
            self.groww_client = None
            logger.warning("Running in SIMULATION mode")
            
    def is_market_hours(self) -> bool:
        """Check if within Indian market trading hours"""
        now = datetime.now()
        market_open = time(MARKET_OPEN_HOUR, MARKET_OPEN_MINUTE)
        market_close = time(MARKET_CLOSE_HOUR, MARKET_CLOSE_MINUTE)
        
        current_time = now.time()
        
        # Check if weekday (0=Monday, 4=Friday)
        if now.weekday() > 4:
            return False
            
        return market_open <= current_time <= market_close
        
    def fetch_market_data(self, symbol: str, interval: str = "5m", limit: int = 100) -> Optional[pd.DataFrame]:
        """Fetch OHLCV data for a symbol"""
        try:
            if self.groww_client is None:
                # Return simulated data for testing
                return self._generate_simulated_data(symbol, limit)
                
            # Fetch historical candles from Groww
            candles = self.groww_client.get_historical_candles(
                exchange=self.groww_client.EXCHANGE_NSE,
                segment=self.groww_client.SEGMENT_CASH,
                trading_symbol=symbol,
                interval=interval
            )
            
            df = pd.DataFrame(candles)
            df.columns = ['timestamp', 'open', 'high', 'low', 'close', 'volume']
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            df.set_index('timestamp', inplace=True)
            
            return df
            
        except Exception as e:
            logger.error(f"Error fetching data for {symbol}: {e}")
            return None
            
    def _generate_simulated_data(self, symbol: str, limit: int) -> pd.DataFrame:
        """Generate simulated market data for testing"""
        import numpy as np
        
        dates = pd.date_range(end=datetime.now(), periods=limit, freq='5T')
        base_price = 1000 + hash(symbol) % 5000
        
        # Generate random walk prices
        returns = np.random.normal(0, 0.001, limit)
        prices = base_price * np.exp(np.cumsum(returns))
        
        df = pd.DataFrame({
            'open': prices * (1 + np.random.uniform(-0.005, 0.005, limit)),
            'high': prices * (1 + np.random.uniform(0, 0.01, limit)),
            'low': prices * (1 - np.random.uniform(0, 0.01, limit)),
            'close': prices,
            'volume': np.random.randint(1000, 100000, limit)
        }, index=dates)
        
        return df
        
    def execute_trade(self, symbol: str, side: str, quantity: int, price: float) -> bool:
        """Execute a trade via Groww API"""
        try:
            if self.groww_client is None:
                logger.info(f"SIMULATED {side} {quantity} shares of {symbol} @ {price:.2f}")
                return True
                
            response = self.groww_client.place_order(
                trading_symbol=symbol,
                quantity=quantity,
                validity=self.groww_client.VALIDITY_DAY,
                exchange=self.groww_client.EXCHANGE_NSE,
                segment=self.groww_client.SEGMENT_CASH,
                product=self.groww_client.PRODUCT_MIS,  # Intraday
                order_type=self.groww_client.ORDER_TYPE_MARKET,
                transaction_type=self.groww_client.TRANSACTION_TYPE_BUY if side == 'BUY' else self.groww_client.TRANSACTION_TYPE_SELL,
            )
            
            logger.info(f"Order placed: {response}")
            return True
            
        except Exception as e:
            logger.error(f"Trade execution failed: {e}")
            return False
            
    def record_trade(self, symbol: str, side: str, quantity: int, price: float, 
                     status: str, strategy_id: Optional[int] = None, pnl: Optional[float] = None):
        """Record trade to database"""
        try:
            if self.db_conn is None:
                return
                
            cursor = self.db_conn.cursor()
            cursor.execute("""
                INSERT INTO trades (user_id, symbol, side, quantity, price, status, strategy_id, pnl)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """, (self.user_id, symbol, side, quantity, str(price), status, strategy_id, str(pnl) if pnl else None))
            
            self.db_conn.commit()
            cursor.close()
            
        except Exception as e:
            logger.error(f"Failed to record trade: {e}")
            
    def load_active_strategies(self):
        """Load active strategies from database"""
        try:
            if self.db_conn is None:
                self.active_strategies = ['ma_crossover', 'rsi', 'macd', 'supertrend']
                return
                
            cursor = self.db_conn.cursor(cursor_factory=RealDictCursor)
            cursor.execute("SELECT * FROM strategies WHERE is_active = true")
            strategies = cursor.fetchall()
            cursor.close()
            
            self.active_strategies = []
            for s in strategies:
                name = s['name'].lower().replace(' ', '_')
                # Map common names
                if 'moving average' in name or 'ma' in name:
                    self.active_strategies.append('ma_crossover')
                elif 'rsi' in name:
                    self.active_strategies.append('rsi')
                elif 'macd' in name:
                    self.active_strategies.append('macd')
                elif 'bollinger' in name:
                    self.active_strategies.append('bollinger')
                elif 'vwap' in name:
                    self.active_strategies.append('vwap')
                elif 'supertrend' in name:
                    self.active_strategies.append('supertrend')
                    
            logger.info(f"Loaded strategies: {self.active_strategies}")
            
        except Exception as e:
            logger.error(f"Failed to load strategies: {e}")
            self.active_strategies = ['ma_crossover', 'rsi', 'macd']
            
    async def process_symbol(self, symbol: str):
        """Process trading logic for a single symbol"""
        # Fetch market data
        data = self.fetch_market_data(symbol)
        if data is None or len(data) < 50:
            return
            
        # Calculate ATR for position sizing
        atr = calculate_atr(data['high'], data['low'], data['close'])
        current_atr = atr.iloc[-1] if not pd.isna(atr.iloc[-1]) else data['close'].iloc[-1] * 0.02
        current_price = data['close'].iloc[-1]
        
        # Check for exit conditions first
        if symbol in self.money_manager.positions:
            should_exit, reason = self.money_manager.should_exit(symbol, current_price)
            if should_exit:
                pnl = self.money_manager.close_position(symbol, current_price, reason)
                side = 'SELL' if self.money_manager.positions.get(symbol, None) and \
                       self.money_manager.positions[symbol].side == 'BUY' else 'BUY'
                
                if self.execute_trade(symbol, side, 1, current_price):  # Quantity from position
                    self.record_trade(symbol, side, 1, current_price, 'EXECUTED', pnl=pnl)
                    logger.info(f"Closed {symbol} position: {reason}, PnL: {pnl:.2f}")
                return
                
        # Check if we can open new positions
        can_trade, reason = self.money_manager.can_trade()
        if not can_trade:
            logger.warning(f"Trading blocked: {reason}")
            return
            
        # Skip if already in position
        if symbol in self.money_manager.positions:
            return
            
        # Get combined signal from strategies
        signal, strategy_signals = self.strategy_engine.get_combined_signal(data, self.active_strategies)
        
        if signal == 0:
            return
            
        # Calculate position size
        quantity = self.money_manager.calculate_position_size(symbol, current_price, current_atr)
        
        if signal == 1:  # BUY
            if self.execute_trade(symbol, 'BUY', quantity, current_price):
                self.money_manager.open_position(symbol, 'BUY', quantity, current_price, current_atr)
                self.record_trade(symbol, 'BUY', quantity, current_price, 'EXECUTED')
                logger.info(f"BUY {quantity} {symbol} @ {current_price:.2f} | Signals: {strategy_signals}")
                
        elif signal == -1:  # SELL
            if self.execute_trade(symbol, 'SELL', quantity, current_price):
                self.money_manager.open_position(symbol, 'SELL', quantity, current_price, current_atr)
                self.record_trade(symbol, 'SELL', quantity, current_price, 'EXECUTED')
                logger.info(f"SELL {quantity} {symbol} @ {current_price:.2f} | Signals: {strategy_signals}")
                
    async def run_trading_loop(self):
        """Main async trading loop"""
        logger.info("Starting trading engine...")
        self.is_running = True
        
        while self.is_running:
            try:
                # Check market hours
                if not self.is_market_hours():
                    logger.info("Outside market hours. Waiting...")
                    await asyncio.sleep(60)
                    continue
                    
                # Reload strategies periodically
                self.load_active_strategies()
                
                # Process all symbols in parallel
                tasks = [self.process_symbol(symbol) for symbol in self.symbols]
                await asyncio.gather(*tasks)
                
                # Log risk metrics
                metrics = self.money_manager.get_risk_metrics()
                logger.info(f"Capital: {metrics.available_capital:.2f} | Daily PnL: {metrics.daily_pnl:.2f} | Win Rate: {metrics.win_rate:.1f}%")
                
                # Wait before next iteration (5 seconds for HFT)
                await asyncio.sleep(5)
                
            except Exception as e:
                logger.error(f"Error in trading loop: {e}")
                await asyncio.sleep(10)
                
    def start(self):
        """Start the trading engine"""
        try:
            self.connect_database()
            self.connect_groww()
            self.load_active_strategies()
            
            # Run async loop
            asyncio.run(self.run_trading_loop())
            
        except KeyboardInterrupt:
            logger.info("Shutting down...")
            self.stop()
        except Exception as e:
            logger.error(f"Engine error: {e}")
            self.stop()
            
    def stop(self):
        """Stop the trading engine"""
        self.is_running = False
        
        # Close all positions
        for symbol in list(self.money_manager.positions.keys()):
            data = self.fetch_market_data(symbol)
            if data is not None:
                current_price = data['close'].iloc[-1]
                self.money_manager.close_position(symbol, current_price, "ENGINE_STOP")
                
        if self.db_conn:
            self.db_conn.close()
            
        logger.info("Trading engine stopped")


def main():
    """Entry point for the trading engine"""
    # Get credentials from environment or command line
    user_id = os.getenv("TRADING_USER_ID", "demo_user")
    api_key = os.getenv("GROWW_API_KEY", "")
    api_secret = os.getenv("GROWW_API_SECRET", "")
    initial_capital = float(os.getenv("INITIAL_CAPITAL", "100000"))
    
    engine = TradingEngine(
        user_id=user_id,
        api_key=api_key,
        api_secret=api_secret,
        initial_capital=initial_capital
    )
    
    engine.start()


if __name__ == "__main__":
    main()
