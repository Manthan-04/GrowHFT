"""
High Frequency Trading Engine
Continuously monitors the market, generates signals, and executes trades automatically.
Once started, it runs as a background loop — no manual API calls needed per tick.
"""
import asyncio
import os
import sys
import json
import logging
from datetime import datetime, time
from typing import Optional, Dict, List
from dataclasses import dataclass, field, asdict
import pandas as pd

from config import *
from strategies import MultiStrategyEngine, get_strategy
from money_management import MoneyManager, RiskMetrics
from indicators import calculate_atr
from database import SessionLocal, Trade, Strategy, User

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@dataclass
class SignalEvent:
    """A signal generated automatically by the engine during scanning."""
    timestamp: str
    symbol: str
    signal: int              # 1=BUY, -1=SELL, 0=HOLD
    signal_label: str        # "BUY", "SELL", "HOLD"
    current_price: float
    strategy_votes: Dict[str, int]
    confidence: float
    suggested_quantity: int
    stop_loss: float
    take_profit: float
    action_taken: str        # "TRADE_EXECUTED", "ALREADY_IN_POSITION", "HOLD", "BLOCKED"


class TradingEngine:
    """
    Autonomous HFT Engine.

    Lifecycle:
        1. POST /api/engine/start  → creates engine, connects DB & Groww, spawns background loop
        2. Background loop (every SCAN_INTERVAL_SECONDS):
           a. Checks market hours
           b. Reloads active strategies from DB
           c. For EACH symbol in parallel:
              - Fetches latest OHLCV candles
              - Runs all active strategies → weighted vote → BUY / SELL / HOLD
              - If there is an open position, checks exit rules (stop-loss, trailing stop, take-profit)
              - If no position and signal is BUY or SELL, calculates position size and executes trade
              - Logs signal to the in-memory signal_log
              - Persists executed trades to PostgreSQL
           d. Logs portfolio metrics
        3. POST /api/engine/stop  → stops the loop, closes all positions
        4. GET /api/engine/signals  → returns the auto-generated signal log (no manual scan needed)
    """

    SCAN_INTERVAL_SECONDS = 5   # How often the engine scans all symbols

    def __init__(self, user_id: str, api_key: str, api_secret: str, initial_capital: float = 100000.0):
        self.user_id = user_id
        self.api_key = api_key
        self.api_secret = api_secret
        self.money_manager = MoneyManager(initial_capital)
        self.strategy_engine = MultiStrategyEngine()
        self.is_running = False
        self.groww_client = None
        self.db_session = None
        self.active_strategies: List[str] = []
        self.symbols: List[str] = DEFAULT_SYMBOLS

        # Auto-generated signal log — populated by the background loop
        self.signal_log: List[SignalEvent] = []
        self.max_signal_log_size = 500       # keep last 500 signals in memory
        self.loop_count = 0                  # number of completed scan cycles
        self.last_scan_time: Optional[str] = None

    # ------------------------------------------------------------------
    # CONNECTIONS
    # ------------------------------------------------------------------

    def connect_database(self):
        """Open a SQLAlchemy session for trade persistence."""
        try:
            self.db_session = SessionLocal()
            logger.info("Connected to database")
        except Exception as e:
            logger.error(f"Database connection failed: {e}")
            raise

    def connect_groww(self):
        """Authenticate with Groww. Falls back to simulation mode if keys are missing."""
        try:
            if not self.api_key or not self.api_secret:
                raise ValueError("No API credentials provided")

            from growwapi import GrowwAPI
            access_token = GrowwAPI.get_access_token(api_key=self.api_key, secret=self.api_secret)
            self.groww_client = GrowwAPI(access_token)
            logger.info("Connected to Groww API — LIVE mode")
        except Exception as e:
            logger.warning(f"Groww connection failed ({e}) — Running in SIMULATION mode")
            self.groww_client = None

    # ------------------------------------------------------------------
    # MARKET DATA
    # ------------------------------------------------------------------

    def is_market_hours(self) -> bool:
        """True if current time is within NSE trading hours on a weekday."""
        now = datetime.now()
        if now.weekday() > 4:
            return False
        current = now.time()
        return time(MARKET_OPEN_HOUR, MARKET_OPEN_MINUTE) <= current <= time(MARKET_CLOSE_HOUR, MARKET_CLOSE_MINUTE)

    def fetch_market_data(self, symbol: str, interval: str = "5m", limit: int = 100) -> Optional[pd.DataFrame]:
        """Fetch OHLCV candles — from Groww in live mode, or generated data in simulation."""
        try:
            if self.groww_client is None:
                return self._generate_simulated_data(symbol, limit)

            candles = self.groww_client.get_historical_candles(
                exchange=self.groww_client.EXCHANGE_NSE,
                segment=self.groww_client.SEGMENT_CASH,
                trading_symbol=symbol,
                interval=interval,
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
        """Random-walk price data used in simulation mode."""
        import numpy as np
        dates = pd.date_range(end=datetime.now(), periods=limit, freq='5min')
        base_price = 1000 + abs(hash(symbol)) % 5000
        returns = np.random.normal(0, 0.001, limit)
        prices = base_price * np.exp(np.cumsum(returns))
        return pd.DataFrame({
            'open':   prices * (1 + np.random.uniform(-0.005, 0.005, limit)),
            'high':   prices * (1 + np.random.uniform(0, 0.01, limit)),
            'low':    prices * (1 - np.random.uniform(0, 0.01, limit)),
            'close':  prices,
            'volume': np.random.randint(1000, 100000, limit),
        }, index=dates)

    # ------------------------------------------------------------------
    # TRADE EXECUTION & PERSISTENCE
    # ------------------------------------------------------------------

    def execute_trade(self, symbol: str, side: str, quantity: int, price: float) -> bool:
        """Place an order on Groww (or simulate it)."""
        try:
            if self.groww_client is None:
                logger.info(f"[SIM] {side} {quantity} x {symbol} @ {price:.2f}")
                return True

            self.groww_client.place_order(
                trading_symbol=symbol,
                quantity=quantity,
                validity=self.groww_client.VALIDITY_DAY,
                exchange=self.groww_client.EXCHANGE_NSE,
                segment=self.groww_client.SEGMENT_CASH,
                product=self.groww_client.PRODUCT_MIS,
                order_type=self.groww_client.ORDER_TYPE_MARKET,
                transaction_type=(
                    self.groww_client.TRANSACTION_TYPE_BUY if side == 'BUY'
                    else self.groww_client.TRANSACTION_TYPE_SELL
                ),
            )
            logger.info(f"[LIVE] {side} {quantity} x {symbol} @ {price:.2f}")
            return True
        except Exception as e:
            logger.error(f"Trade execution failed for {symbol}: {e}")
            return False

    def record_trade(self, symbol: str, side: str, quantity: int, price: float,
                     status: str, strategy_id: Optional[int] = None, pnl: Optional[float] = None):
        """Persist a trade record to PostgreSQL."""
        try:
            if self.db_session is None:
                return
            trade = Trade(
                user_id=self.user_id, symbol=symbol, side=side, quantity=quantity,
                price=str(price), status=status, strategy_id=strategy_id,
                pnl=str(pnl) if pnl is not None else None,
            )
            self.db_session.add(trade)
            self.db_session.commit()
        except Exception as e:
            logger.error(f"Failed to record trade: {e}")
            if self.db_session:
                self.db_session.rollback()

    # ------------------------------------------------------------------
    # STRATEGY LOADING
    # ------------------------------------------------------------------

    def load_active_strategies(self):
        """Read which strategies are enabled from the database."""
        try:
            if self.db_session is None:
                self.active_strategies = ['ma_crossover', 'rsi', 'macd', 'supertrend']
                return

            rows = self.db_session.query(Strategy).filter(Strategy.is_active == True).all()
            self.active_strategies = []
            # Order matters: check specific names before substrings (e.g. "macd" before "ma")
            name_map = [
                ('moving average', 'ma_crossover'),
                ('ema crossover', 'ema_crossover'),
                ('macd', 'macd'),
                ('stochastic', 'stoch_rsi'),
                ('bollinger', 'bollinger'),
                ('supertrend', 'supertrend'),
                ('vwap', 'vwap'),
                ('rsi', 'rsi'),
            ]
            for row in rows:
                lower = row.name.lower()
                for keyword, key in name_map:
                    if keyword in lower:
                        if key not in self.active_strategies:
                            self.active_strategies.append(key)
                        break
            logger.info(f"Active strategies: {self.active_strategies}")
        except Exception as e:
            logger.error(f"Failed to load strategies: {e}")
            self.active_strategies = ['ma_crossover', 'rsi', 'macd']

    # ------------------------------------------------------------------
    # CORE LOOP — runs automatically every SCAN_INTERVAL_SECONDS
    # ------------------------------------------------------------------

    async def process_symbol(self, symbol: str):
        """
        Called by the background loop for EACH symbol every tick.
        Generates a signal, checks exits, opens new positions, and logs everything.
        """
        data = self.fetch_market_data(symbol)
        if data is None or len(data) < 50:
            return

        atr_series = calculate_atr(data['high'], data['low'], data['close'])
        current_atr = float(atr_series.iloc[-1]) if not pd.isna(atr_series.iloc[-1]) else float(data['close'].iloc[-1]) * 0.02
        current_price = float(data['close'].iloc[-1])

        # ---------- EXIT CHECK (runs before new entry) ----------
        if symbol in self.money_manager.positions:
            should_exit, reason = self.money_manager.should_exit(symbol, current_price)
            if should_exit:
                pos = self.money_manager.positions[symbol]
                exit_side = 'SELL' if pos.side == 'BUY' else 'BUY'
                pnl = self.money_manager.close_position(symbol, current_price, reason)
                self.execute_trade(symbol, exit_side, pos.quantity, current_price)
                self.record_trade(symbol, exit_side, pos.quantity, current_price, 'EXECUTED', pnl=pnl)
                self._log_signal(symbol, 0, "HOLD", current_price, {}, 0, 0, 0, 0,
                                 f"POSITION_CLOSED ({reason}), PnL={pnl:.2f}")
                logger.info(f"Closed {symbol}: {reason}, PnL: {pnl:.2f}")
            return   # don't open a new position in the same tick we closed one

        # ---------- SIGNAL GENERATION ----------
        signal, votes = self.strategy_engine.get_combined_signal(data, self.active_strategies)
        signal_label = {1: "BUY", -1: "SELL"}.get(signal, "HOLD")

        quantity = self.money_manager.calculate_position_size(symbol, current_price, current_atr)
        stop_loss = current_price - (current_atr * 2) if signal == 1 else current_price + (current_atr * 2)
        take_profit = current_price + (current_atr * 4) if signal == 1 else current_price - (current_atr * 4)
        agreeing = sum(1 for v in votes.values() if v == signal and signal != 0)
        confidence = agreeing / len(votes) if votes else 0

        # ---------- ENTRY DECISION ----------
        action = "HOLD"
        if signal == 0:
            action = "HOLD"
        else:
            can_trade, block_reason = self.money_manager.can_trade()
            if not can_trade:
                action = f"BLOCKED ({block_reason})"
            elif symbol in self.money_manager.positions:
                action = "ALREADY_IN_POSITION"
            else:
                side = "BUY" if signal == 1 else "SELL"
                if self.execute_trade(symbol, side, quantity, current_price):
                    self.money_manager.open_position(symbol, side, quantity, current_price, current_atr)
                    self.record_trade(symbol, side, quantity, current_price, 'EXECUTED')
                    action = "TRADE_EXECUTED"
                    logger.info(f"{side} {quantity} x {symbol} @ {current_price:.2f} | votes={votes}")
                else:
                    action = "EXECUTION_FAILED"

        self._log_signal(symbol, signal, signal_label, current_price, votes,
                         confidence, quantity, stop_loss, take_profit, action)

    def _log_signal(self, symbol, signal, label, price, votes, confidence,
                    qty, sl, tp, action):
        """Append a signal event to the in-memory log (auto-trimmed)."""
        event = SignalEvent(
            timestamp=datetime.now().isoformat(),
            symbol=symbol,
            signal=signal,
            signal_label=label,
            current_price=round(price, 2),
            strategy_votes=votes,
            confidence=round(confidence, 3),
            suggested_quantity=qty,
            stop_loss=round(sl, 2),
            take_profit=round(tp, 2),
            action_taken=action,
        )
        self.signal_log.append(event)
        if len(self.signal_log) > self.max_signal_log_size:
            self.signal_log = self.signal_log[-self.max_signal_log_size:]

    async def run_trading_loop(self):
        """
        THE MAIN BACKGROUND LOOP.
        Runs continuously once the engine is started.
        Every SCAN_INTERVAL_SECONDS it:
          1. Checks market hours
          2. Reloads strategies
          3. Scans ALL symbols in parallel
          4. Logs portfolio metrics
        You do NOT need to hit any API to trigger this — it runs by itself.
        """
        logger.info("=== Engine loop started — scanning automatically ===")
        self.is_running = True

        while self.is_running:
            try:
                if not self.is_market_hours():
                    logger.info("Outside market hours. Sleeping 60 s...")
                    await asyncio.sleep(60)
                    continue

                self.load_active_strategies()

                tasks = [self.process_symbol(sym) for sym in self.symbols]
                await asyncio.gather(*tasks)

                self.loop_count += 1
                self.last_scan_time = datetime.now().isoformat()

                metrics = self.money_manager.get_risk_metrics()
                logger.info(
                    f"[Scan #{self.loop_count}] Capital: {metrics.available_capital:.2f} | "
                    f"Daily PnL: {metrics.daily_pnl:.2f} | Positions: {len(self.money_manager.positions)} | "
                    f"Win Rate: {metrics.win_rate:.1f}%"
                )

                await asyncio.sleep(self.SCAN_INTERVAL_SECONDS)

            except Exception as e:
                logger.error(f"Error in scan loop: {e}", exc_info=True)
                await asyncio.sleep(10)

    # ------------------------------------------------------------------
    # LIFECYCLE
    # ------------------------------------------------------------------

    def start(self):
        """Blocking start (used when running engine.py directly)."""
        try:
            self.connect_database()
            self.connect_groww()
            self.load_active_strategies()
            asyncio.run(self.run_trading_loop())
        except KeyboardInterrupt:
            logger.info("Keyboard interrupt — shutting down")
            self.stop()
        except Exception as e:
            logger.error(f"Engine error: {e}")
            self.stop()

    def stop(self):
        """Gracefully stop the engine and close all open positions."""
        self.is_running = False
        for symbol in list(self.money_manager.positions.keys()):
            data = self.fetch_market_data(symbol)
            if data is not None:
                price = float(data['close'].iloc[-1])
                self.money_manager.close_position(symbol, price, "ENGINE_STOP")
        if self.db_session:
            self.db_session.close()
        logger.info("=== Engine stopped ===")

    # ------------------------------------------------------------------
    # READ-ONLY HELPERS (used by API endpoints)
    # ------------------------------------------------------------------

    def get_signal_log(self, symbol: Optional[str] = None, limit: int = 50) -> List[dict]:
        """Return recent auto-generated signals, optionally filtered by symbol."""
        logs = self.signal_log
        if symbol:
            logs = [s for s in logs if s.symbol == symbol]
        return [asdict(s) for s in logs[-limit:]]

    def get_status_dict(self) -> dict:
        """Snapshot of engine state for the /status endpoint."""
        return {
            "is_running": self.is_running,
            "is_market_hours": self.is_market_hours(),
            "mode": "LIVE" if self.groww_client else "SIMULATION",
            "active_strategies": self.active_strategies,
            "symbols": self.symbols,
            "open_positions": len(self.money_manager.positions),
            "daily_trades": self.money_manager.daily_trades,
            "daily_pnl": round(self.money_manager.daily_pnl, 2),
            "current_capital": round(self.money_manager.current_capital, 2),
            "scan_count": self.loop_count,
            "last_scan_time": self.last_scan_time,
            "signals_in_memory": len(self.signal_log),
        }


def main():
    """Standalone entry point — run the engine directly without the API server."""
    user_id = os.getenv("TRADING_USER_ID", "demo_user")
    api_key = os.getenv("GROWW_API_KEY", "")
    api_secret = os.getenv("GROWW_API_SECRET", "")
    initial_capital = float(os.getenv("INITIAL_CAPITAL", "100000"))

    engine = TradingEngine(user_id=user_id, api_key=api_key,
                           api_secret=api_secret, initial_capital=initial_capital)
    engine.start()


if __name__ == "__main__":
    main()
