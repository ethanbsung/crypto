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
    # Strategy parameters
    adx_period = 10
    adx_low = 26
    adx_high = 32
    risk_reward_ratio = 2
    stop_loss_pct = 0.03
    
    # Trading parameters
    trade_amount_usd = 1
    timeframe = '30m'
    symbol = 'ETH/USD'
    max_slippage = 0.002  # 0.2% maximum allowed slippage
    order_timeout = 60    # seconds to wait for order to fill
    
    # Risk management
    max_daily_loss_usd = 5  # Maximum daily loss in USD
    max_trades_per_day = 10
    minimum_usd_balance = 10
    panic_drop_pct = 0.10  # 10% sudden price drop triggers panic mode
    
    # Technical parameters
    min_data_points = 20
    health_check_interval = 300  # 5 minutes

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
        self.is_panic_mode = False
        self.last_health_check = datetime.now()

class TradingBot:
    def __init__(self):
        self.exchange = ccxt.kraken({
            'apiKey': d.kraken_api_key,
            'secret': d.kraken_secret_key,
            'enableRateLimit': True,
        })
        self.trade_state = TradeState()
        self.last_known_price = None
        self.running = True
        
        # Set up signal handlers
        signal.signal(signal.SIGINT, self.handle_shutdown)
        signal.signal(signal.SIGTERM, self.handle_shutdown)

    def handle_shutdown(self, signum, frame):
        logger.info("Shutdown signal received. Cleaning up...")
        self.running = False
        self.close_all_positions()
        sys.exit(0)

    def reset_daily_metrics(self):
        if (datetime.now() - self.trade_state.last_reset_time).days >= 1:
            self.trade_state.daily_loss = 0
            self.trade_state.daily_trades = 0
            self.trade_state.last_reset_time = datetime.now()
            logger.info("Daily metrics reset")

    def check_system_health(self) -> bool:
        try:
            if (datetime.now() - self.trade_state.last_health_check).seconds >= TradingConfig.health_check_interval:
                # Check exchange connection
                self.exchange.fetch_ticker(TradingConfig.symbol)
                
                # Check balance
                balance = self.exchange.fetch_balance()
                usd_balance = float(balance['free'].get('USD', 0))
                
                if usd_balance < TradingConfig.minimum_usd_balance:
                    raise Exception(f"Balance too low: ${usd_balance}")
                
                # Check if we can fetch recent data
                data = self.fetch_data()
                if data is None or len(data) < TradingConfig.min_data_points:
                    raise Exception("Unable to fetch sufficient market data")
                
                self.trade_state.last_health_check = datetime.now()
                return True
                
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return False
        
        return True

    def fetch_data(self) -> Optional[pd.DataFrame]:
        try:
            ohlcv = self.exchange.fetch_ohlcv(
                TradingConfig.symbol,
                timeframe=TradingConfig.timeframe,
                limit=100
            )
            df = pd.DataFrame(
                ohlcv,
                columns=['timestamp', 'open', 'high', 'low', 'close', 'volume']
            )
            df['datetime'] = pd.to_datetime(df['timestamp'], unit='ms')
            df.set_index('datetime', inplace=True)
            return df
        except Exception as e:
            logger.error(f"Error fetching data: {e}")
            return None

    def check_panic_mode(self, current_price: float) -> bool:
        if self.last_known_price is None:
            self.last_known_price = current_price
            return False
        
        price_change = (current_price - self.last_known_price) / self.last_known_price
        self.last_known_price = current_price
        
        if abs(price_change) > TradingConfig.panic_drop_pct:
            logger.warning(f"PANIC MODE: Price changed by {price_change:.2%}")
            self.trade_state.is_panic_mode = True
            self.close_all_positions()
            return True
            
        return False

    def close_all_positions(self):
        try:
            positions = self.exchange.fetch_positions()
            for position in positions:
                if position['symbol'] == TradingConfig.symbol:
                    self.exchange.create_market_order(
                        symbol=TradingConfig.symbol,
                        type='market',
                        side='sell' if position['side'] == 'buy' else 'buy',
                        amount=abs(float(position['contracts']))
                    )
            self.trade_state.in_trade = False
            logger.info("All positions closed")
        except Exception as e:
            logger.error(f"Error closing positions: {e}")

    def execute_trade(self, side: str, price: float) -> bool:
        try:
            # Check daily limits
            if (self.trade_state.daily_loss >= TradingConfig.max_daily_loss_usd or 
                self.trade_state.daily_trades >= TradingConfig.max_trades_per_day):
                logger.info("Daily limits reached, skipping trade")
                return False

            # Check for panic mode
            if self.trade_state.is_panic_mode:
                logger.info("In panic mode, skipping trade")
                return False

            # Slippage check
            latest_ticker = self.exchange.fetch_ticker(TradingConfig.symbol)
            current_price = float(latest_ticker['last'])
            price_diff = abs(current_price - price) / price

            if price_diff > TradingConfig.max_slippage:
                logger.warning(f"Price slippage too high: {price_diff:.2%}")
                return False

            # Calculate position size
            eth_amount = TradingConfig.trade_amount_usd / price
            eth_amount = round(eth_amount, 8)

            # Calculate stop loss and take profit
            if side == 'buy':
                stop_loss = price * (1 - TradingConfig.stop_loss_pct)
                take_profit = price * (1 + TradingConfig.stop_loss_pct * TradingConfig.risk_reward_ratio)
            else:
                stop_loss = price * (1 + TradingConfig.stop_loss_pct)
                take_profit = price * (1 - TradingConfig.stop_loss_pct * TradingConfig.risk_reward_ratio)

            # Place the order
            order = self.exchange.create_order(
                symbol=TradingConfig.symbol,
                type='limit',
                side=side,
                amount=eth_amount,
                price=price
            )

            # Monitor order
            start_time = time.time()
            while time.time() - start_time < TradingConfig.order_timeout:
                order_status = self.exchange.fetch_order(order['id'])
                if order_status['status'] == 'closed':
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
                        f"Amount: {eth_amount} ETH (${TradingConfig.trade_amount_usd}), "
                        f"Entry: ${price:.2f}, SL: ${stop_loss:.2f}, TP: ${take_profit:.2f}"
                    )
                    return True

                time.sleep(2)

            # Cancel order if not filled
            if order_status['status'] != 'closed':
                self.exchange.cancel_order(order['id'])
                logger.warning("Order cancelled due to timeout")
                return False

        except Exception as e:
            logger.error(f"Error executing trade: {e}")
            return False

    def run_strategy(self):
        # Basic health check
        if not self.check_system_health():
            return

        # Reset daily metrics if needed
        self.reset_daily_metrics()

        # Fetch and validate data
        df = self.fetch_data()
        if df is None or len(df) < TradingConfig.min_data_points:
            logger.warning("Insufficient data to run strategy")
            return

        current_price = df['close'].iloc[-1]
        
        # Check for panic conditions
        if self.check_panic_mode(current_price):
            return

        # Position management
        try:
            if self.trade_state.in_trade:
                # Check for stop loss or take profit
                if self.trade_state.current_position == 'buy':
                    if (current_price <= self.trade_state.stop_loss or 
                        current_price >= self.trade_state.take_profit):
                        self.close_all_positions()
                        pnl = (current_price - self.trade_state.entry_price) * TradingConfig.trade_amount_usd
                        self.trade_state.daily_loss -= min(pnl, 0)
                else:  # sell position
                    if (current_price >= self.trade_state.stop_loss or 
                        current_price <= self.trade_state.take_profit):
                        self.close_all_positions()
                        pnl = (self.trade_state.entry_price - current_price) * TradingConfig.trade_amount_usd
                        self.trade_state.daily_loss -= min(pnl, 0)
                return
        except Exception as e:
            logger.error(f"Error in position management: {e}")
            return

        # Calculate ADX
        adx = ADXIndicator(
            df['high'],
            df['low'],
            df['close'],
            TradingConfig.adx_period
        ).adx()

        current_adx = adx.iloc[-1]

        # Check trading conditions
        if TradingConfig.adx_low < current_adx < TradingConfig.adx_high:
            if crossover(df['close'], df['high'].shift(2)):
                self.execute_trade('buy', current_price)
            elif crossover(df['low'].shift(2), df['close']):
                self.execute_trade('sell', current_price)

    def run(self):
        logger.info(f"Bot started! Running strategy on {TradingConfig.symbol}")
        logger.info(f"Timeframe: {TradingConfig.timeframe}")
        logger.info(f"Trade amount: ${TradingConfig.trade_amount_usd}")
        
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
                current_time = datetime.now()
                logger.info(f"Checking for trade opportunities... {current_time}")
                self.run_strategy()
                
                # Sleep until next candle
                sleep_until = current_time.replace(second=0, microsecond=0)
                if TradingConfig.timeframe == '30m':
                    if current_time.minute >= 30:
                        sleep_until = sleep_until.replace(minute=30)
                    else:
                        sleep_until = sleep_until.replace(minute=0)
                    sleep_until += pd.Timedelta(minutes=30)
                
                sleep_seconds = (sleep_until - current_time).total_seconds()
                if sleep_seconds > 0:
                    time.sleep(sleep_seconds)
                
            except Exception as e:
                logger.error(f"Error in main loop: {e}")
                time.sleep(60)

if __name__ == "__main__":
    bot = TradingBot()
    bot.run()