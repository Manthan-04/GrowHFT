import os
import time
import json
import psycopg2
import talib
import numpy as np
from datetime import datetime
import threading
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Database Connection
def get_db_connection():
    return psycopg2.connect(os.environ['DATABASE_URL'])

# Mock Groww API Wrapper (replace with actual growwapi when keys available)
class TradingBot:
    def __init__(self):
        self.conn = get_db_connection()
        self.is_running = True
        print("Trading Bot Initialized")

    def fetch_active_strategies(self):
        cur = self.conn.cursor()
        cur.execute("SELECT id, name, parameters FROM strategies WHERE is_active = TRUE")
        strategies = cur.fetchall()
        cur.close()
        return strategies

    def log_trade(self, strategy_id, symbol, side, qty, price, status, pnl=0):
        cur = self.conn.cursor()
        cur.execute(
            """
            INSERT INTO trades (user_id, symbol, side, quantity, price, status, strategy_id, pnl, timestamp)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, NOW())
            RETURNING id
            """,
            (1, symbol, side, qty, price, status, strategy_id, pnl) # Hardcoded user_id 1 for demo
        )
        self.conn.commit()
        trade_id = cur.fetchone()[0]
        cur.close()
        print(f"Trade Logged: {side} {qty} {symbol} @ {price} (ID: {trade_id})")

    def run_strategy(self, strategy):
        s_id, s_name, s_params = strategy
        print(f"Running Strategy: {s_name}")
        
        # === SIMULATION LOGIC ===
        # In a real scenario, we would fetch live data here
        # groww.get_live_data(symbol)
        
        symbol = "RELIANCE"
        current_price = 2500 + np.random.randn() * 10
        
        # Mock Indicator Calculation
        # close_prices = np.random.random(100) * 100 + 2400
        # rsi = talib.RSI(close_prices, timeperiod=14)[-1]
        
        # Simple Random Logic for Demo
        action = None
        if np.random.random() > 0.8:
            action = "BUY"
        elif np.random.random() > 0.8:
            action = "SELL"
            
        if action:
            self.log_trade(
                strategy_id=s_id,
                symbol=symbol,
                side=action,
                qty=10,
                price=round(current_price, 2),
                status="EXECUTED",
                pnl=round(np.random.randn() * 50, 2)
            )

    def loop(self):
        while self.is_running:
            try:
                strategies = self.fetch_active_strategies()
                if not strategies:
                    print("No active strategies. Waiting...")
                
                for strategy in strategies:
                    self.run_strategy(strategy)
                
                time.sleep(5) # Poll every 5 seconds
            except Exception as e:
                print(f"Error in loop: {e}")
                time.sleep(5)

if __name__ == "__main__":
    bot = TradingBot()
    bot.loop()
