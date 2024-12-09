import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import ccxt
import pandas as pd
from ta.trend import ADXIndicator
from backtesting.lib import crossover
import dontshare as d
import time
from datetime import datetime, timedelta
import logging
from typing import Optional
import signal
import threading

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('trading_bot.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

class TradingConfig:
    adx_period = 28
    adx_low = 26
    adx_high = 46
    risk_reward_ratio = 3
    stop_loss_pct = 0.027
    
    trade_amount_eth = 0.002  
    timeframe = '4h'
    symbol = 'ETH/USD'
    max_slippage = 0.002
    order_timeout = 60  
    
    max_daily_loss_usd = 20
    minimum_usd_balance = 10
    
    min_data_points = 20

class TradeState:
    def __init__(self):
        self.in_trade = False
        self.current_position = None
        self.entry_price = None
        self.stop_loss = None
        self.take_profit = None
        self.daily_loss = 0
        self.daily_trades = 0
        self.last_trade_time = None
        self.last_reset_time = datetime.now()

class TradingBot:
    def __init__(self):
        self.exchange = ccxt.kraken({
            'apiKey': d.kraken_api_key,
            'secret': d.kraken_secret_key,
            'enableRateLimit': True,
        })
        self.trade_state = TradeState()
        self.running = True
        self.is_shutting_down = False
        self.stop_event = threading.Event()

        signal.signal(signal.SIGINT, self.handle_shutdown)
        signal.signal(signal.SIGTERM, self.handle_shutdown)

    def wake_up_api(self, retries=2, delay=5) -> bool:
        for attempt in range(retries):
            try:
                self.exchange.public_get_time()
                logger.info("API woken up successfully")
                return True
            except Exception as e:
                logger.error(f"Failed to wake up API on attempt {attempt + 1}: {e}")
                if attempt < retries - 1:
                    logger.info(f"Retrying in {delay} seconds...")
                    time.sleep(delay)
        logger.error("API wake-up failed after multiple attempts")
        return False

    def handle_shutdown(self, signum, frame):
        if self.is_shutting_down:
            return
        self.is_shutting_down = True
        logger.info("Shutdown signal received. Cleaning up...")
        self.running = False
        self.stop_event.set()
        self.close_all_positions()

    def fetch_data(self) -> Optional[pd.DataFrame]:
        try:
            ohlcv = self.exchange.fetch_ohlcv(
                TradingConfig.symbol,
                timeframe=TradingConfig.timeframe,
                limit=101  
            )

            if not ohlcv or len(ohlcv) < TradingConfig.min_data_points:
                logger.error(f"Invalid data: Insufficient data points ({len(ohlcv) if ohlcv else 0})")
                return None

            df = pd.DataFrame(
                ohlcv,
                columns=['timestamp', 'open', 'high', 'low', 'close', 'volume']
            )

            if df.isnull().any().any():
                logger.error("Invalid data: Missing values detected")
                return None

            invalid_candles = (
                (df['high'] < df['low']) | 
                (df['high'] < df['open']) | 
                (df['high'] < df['close']) |
                (df['low'] > df['open']) | 
                (df['low'] > df['close'])
            )
            if invalid_candles.any():
                logger.error(f"Invalid data: Detected {invalid_candles.sum()} candles with invalid OHLC relationships")
                return None

            df['datetime'] = pd.to_datetime(df['timestamp'], unit='ms')
            df.set_index('datetime', inplace=True)
            return df
        except ccxt.BaseError as e:
            logger.error(f"Exchange error when fetching data: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error fetching data: {str(e)}")
            return None

    def execute_trade(self, side: str, price: float) -> bool:
        if not self.wake_up_api() or side == 'sell' or price <= 0:
            return False

        try:
            balance = self.exchange.fetch_balance()
            usd_balance = float(balance['free'].get('USD', 0))
            if usd_balance < TradingConfig.minimum_usd_balance:
                logger.error(f"Insufficient USD balance: ${usd_balance}")
                return False

            eth_amount = TradingConfig.trade_amount_eth
            stop_loss = price * (1 - TradingConfig.stop_loss_pct)
            take_profit = price * (1 + TradingConfig.stop_loss_pct * TradingConfig.risk_reward_ratio)

            entry_order = self.exchange.create_order(
                symbol=TradingConfig.symbol,
                type='limit',
                side=side,
                amount=eth_amount,
                price=price
            )

            start_time = time.time()
            while time.time() - start_time < TradingConfig.order_timeout:
                order_status = self.exchange.fetch_order(entry_order['id'])
                if order_status['status'] == 'closed':
                    break
                time.sleep(2)

            if order_status['status'] != 'closed':
                self.exchange.cancel_order(entry_order['id'])
                logger.warning("Order cancelled due to timeout")
                return False

            self.trade_state.in_trade = True
            self.trade_state.entry_price = price
            self.trade_state.stop_loss = stop_loss
            self.trade_state.take_profit = take_profit
            self.trade_state.daily_trades += 1
            self.trade_state.last_trade_time = datetime.now()

            logger.info(f"{side.upper()} order executed: Entry ${price:.2f}, SL ${stop_loss:.2f}, TP ${take_profit:.2f}")
            return True

        except Exception as e:
            logger.error(f"Error executing trade: {e}")
            return False

    def run_strategy(self):
        df = self.fetch_data()
        if df is None or len(df) < TradingConfig.min_data_points:
            logger.warning("Insufficient data to run strategy")
            return

        current_price = df['close'].iloc[-1]
        adx = ADXIndicator(df['high'], df['low'], df['close'], TradingConfig.adx_period).adx()
        current_adx = adx.iloc[-1]

        if TradingConfig.adx_low < current_adx < TradingConfig.adx_high:
            if crossover(df['close'], df['high'].shift(2)):
                self.execute_trade('buy', current_price)

    def next_candle_time(self) -> datetime:
        now = datetime.utcnow()
        next_candle = now.replace(minute=0, second=0, microsecond=0) + timedelta(hours=4 - now.hour % 4)
        return next_candle

    def run(self):
        logger.info(f"Bot started on {TradingConfig.symbol}, timeframe {TradingConfig.timeframe}")
        while self.running:
            try:
                next_candle = self.next_candle_time()
                wake_up_time = next_candle - timedelta(minutes=1)
                wait_time = (wake_up_time - datetime.utcnow()).total_seconds()

                logger.info(f"Waiting to wake up API in {wait_time / 60:.2f} minutes...")
                self.stop_event.wait(timeout=wait_time)

                if not self.running:
                    break

                logger.info("Waking up API before candle close...")
                if not self.wake_up_api():
                    continue

                logger.info("Running strategy at candle close...")
                self.run_strategy()
            except Exception as e:
                logger.error(f"Error in main loop: {e}")
                time.sleep(60)

if __name__ == "__main__":
    bot = TradingBot()
    bot.run()
