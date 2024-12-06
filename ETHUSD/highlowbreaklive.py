import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import ccxt
import pandas as pd
from ta.trend import ADXIndicator
from backtesting.lib import crossover
import dontshare as d
import time
from datetime import datetime
import logging
from typing import Optional
import sys
import signal

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
    # Strategy parameters (matching backtest)
    adx_period = 10
    adx_low = 26
    adx_high = 32
    risk_reward_ratio = 2
    stop_loss_pct = 0.03
    
    # Trading parameters
    trade_amount_eth = 0.002  # Fixed amount of ETH to trade
    timeframe = '4h'
    symbol = 'ETH/USD'
    max_slippage = 0.002  # 0.2% maximum allowed slippage
    order_timeout = 60    # seconds to wait for order to fill
    
    # Risk management
    max_daily_loss_usd = 20
    minimum_usd_balance = 10
    
    # Technical parameters
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

from backtesting.lib import crossover

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
        
        # Set up signal handlers
        signal.signal(signal.SIGINT, self.handle_shutdown)
        signal.signal(signal.SIGTERM, self.handle_shutdown)

    def handle_shutdown(self, signum, frame):
        if self.is_shutting_down:
            return
            
        self.is_shutting_down = True
        logger.info("Shutdown signal received. Cleaning up...")
        self.running = False
        self.close_all_positions()
        sys.exit(0)

    def reset_daily_metrics(self):
        if datetime.now().date() != self.trade_state.last_reset_time.date():
            self.trade_state.daily_loss = 0
            self.trade_state.daily_trades = 0
            self.trade_state.last_reset_time = datetime.now()
            logger.info("Daily metrics reset")

    def fetch_data(self) -> Optional[pd.DataFrame]:
        try:
            # Fetch one extra candle to ensure we have the latest complete one
            ohlcv = self.exchange.fetch_ohlcv(
                TradingConfig.symbol,
                timeframe=TradingConfig.timeframe,
                limit=101  # Fetch 101 instead of 100
            )
            
            # Validate OHLCV data exists
            if not ohlcv or len(ohlcv) < TradingConfig.min_data_points:
                logger.error(f"Invalid data: Insufficient data points ({len(ohlcv) if ohlcv else 0})")
                return None

            df = pd.DataFrame(
                ohlcv,
                columns=['timestamp', 'open', 'high', 'low', 'close', 'volume']
            )
            
            # Check for missing values
            if df.isnull().any().any():
                logger.error("Invalid data: Missing values detected")
                return None
            
            # Validate OHLC relationships
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

            # Validate timestamps are sequential
            df['datetime'] = pd.to_datetime(df['timestamp'], unit='ms')
            df.set_index('datetime', inplace=True)
            return df
        except ccxt.NetworkError as e:
            logger.error(f"Network error when fetching data: {str(e)}")
            return None
        except ccxt.ExchangeError as e:
            logger.error(f"Exchange error when fetching data: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error fetching data: {str(e)}")
            return None

    def close_all_positions(self):
        try:
            # Only close position if we're in a trade that this strategy opened
            if self.trade_state.in_trade:
                self.exchange.create_market_order(
                    symbol=TradingConfig.symbol,
                    type='market',
                    side='sell',
                    amount=TradingConfig.trade_amount_eth
                )
                self.trade_state.in_trade = False
                logger.info("Strategy position closed")
        except Exception as e:
            logger.error(f"Error closing position: {e}")

    def execute_trade(self, side: str, price: float) -> bool:
        if side == 'sell':
            # Ignore sell signals in a long-only strategy
            return False

        try:
            # Check daily limits
            if (self.trade_state.daily_loss >= TradingConfig.max_daily_loss_usd):
                logger.info("Daily limits reached, skipping trade")
                return False

            # Slippage check
            latest_ticker = self.exchange.fetch_ticker(TradingConfig.symbol)
            current_price = float(latest_ticker['last'])
            price_diff = abs(current_price - price) / price

            if price_diff > TradingConfig.max_slippage:
                logger.warning(f"Price slippage too high: {price_diff:.2%}")
                return False

            # Use fixed ETH amount
            eth_amount = TradingConfig.trade_amount_eth

            # Calculate stop loss and take profit prices
            stop_loss = price * (1 - TradingConfig.stop_loss_pct)
            take_profit = price * (1 + TradingConfig.stop_loss_pct * TradingConfig.risk_reward_ratio)

            # Place the entry order
            entry_order = self.exchange.create_order(
                symbol=TradingConfig.symbol,
                type='limit',
                side=side,
                amount=eth_amount,
                price=price
            )

            # Monitor entry order
            start_time = time.time()
            while time.time() - start_time < TradingConfig.order_timeout:
                order_status = self.exchange.fetch_order(entry_order['id'])
                if order_status['status'] == 'closed':
                    # Place stop loss order
                    stop_loss_order = self.exchange.create_order(
                        symbol=TradingConfig.symbol,
                        type='stop-loss',
                        side='sell',
                        amount=eth_amount,
                        price=stop_loss,
                    )

                    # Place take profit order
                    take_profit_order = self.exchange.create_order(
                        symbol=TradingConfig.symbol,
                        type='limit',
                        side='sell',
                        amount=eth_amount,
                        price=take_profit
                    )

                    # Update trade state
                    self.trade_state.in_trade = True
                    self.trade_state.current_position = side
                    self.trade_state.entry_price = price
                    self.trade_state.stop_loss = stop_loss
                    self.trade_state.take_profit = take_profit
                    self.trade_state.daily_trades += 1
                    self.trade_state.last_trade_time = datetime.now()

                    logger.info(
                        f"{side.upper()} order executed - "
                        f"Amount: {eth_amount} ETH, "
                        f"Entry: ${price:.2f}, SL: ${stop_loss:.2f}, TP: ${take_profit:.2f}"
                    )
                    return True

                time.sleep(2)

            # Cancel order if not filled
            if order_status['status'] != 'closed':
                self.exchange.cancel_order(entry_order['id'])
                logger.warning("Order cancelled due to timeout")
                return False

        except Exception as e:
            logger.error(f"Error executing trade: {e}")
            return False

    def run_strategy(self):
        # Fetch and validate data
        df = self.fetch_data()
        if df is None or len(df) < TradingConfig.min_data_points:
            logger.warning("Insufficient data to run strategy")
            return

        current_price = df['close'].iloc[-1]

        # Position management
        try:
            if self.trade_state.in_trade:
                # Check if position was closed by exchange-side orders
                position = self.exchange.fetch_position(TradingConfig.symbol)
                if position['size'] == 0:  # Position was closed
                    self.trade_state.in_trade = False
                    logger.info(f"Position closed by exchange orders")
                    return
        except Exception as e:
            logger.error(f"Error in position management: {e}")
            return

        # Calculate ADX (matching backtest)
        adx = ADXIndicator(
            df['high'],
            df['low'],
            df['close'],
            TradingConfig.adx_period
        ).adx()

        current_adx = adx.iloc[-1]

        # Check trading conditions (matching backtest)
        if TradingConfig.adx_low < current_adx < TradingConfig.adx_high:
            if crossover(df['close'], df['high'].shift(2)):
                self.execute_trade('buy', current_price)

    def run(self):
        logger.info(f"Bot started! Running strategy on {TradingConfig.symbol}")
        logger.info(f"Timeframe: {TradingConfig.timeframe}")
        logger.info(f"Trade amount: {TradingConfig.trade_amount_eth} ETH")
        
        # Initial balance check
        try:
            balance = self.exchange.fetch_balance()
            usd_balance = float(balance['free'].get('USD', 0))
            if usd_balance < TradingConfig.minimum_usd_balance:
                logger.error(f"Insufficient USD balance: ${usd_balance}")
                return
        except Exception as e:
            logger.error(f"Error checking balance: {e}")
            return

        while self.running:
            try:
                logger.info(f"Checking for trade opportunities... {datetime.now()}")
                self.run_strategy()
                time.sleep(240)  # 4-hour sleep to match timeframe
            except Exception as e:
                logger.error(f"Error in main loop: {e}")
                time.sleep(60)

if __name__ == "__main__":
    bot = TradingBot()
    bot.run()