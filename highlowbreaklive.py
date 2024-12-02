import ccxt
import pandas as pd
from ta.trend import ADXIndicator
from backtesting.lib import crossover
import dontshare as d
import time

# Initialize Kraken exchange
kraken = ccxt.kraken({
    'apiKey': d.kraken_api_key,
    'secret': d.kraken_secret_key,
})

# Define your strategy parameters
adx_period = 10
adx_low = 26
adx_high = 32
risk_reward_ratio = 2
stop_loss_pct = 0.03
trade_amount = 1  # $1 per position

# Global variable to track trade state
in_trade = False

def fetch_data(symbol, timeframe='4h', limit=100):
    # Fetch OHLCV data from Kraken
    ohlcv = kraken.fetch_ohlcv(symbol, timeframe=timeframe, limit=limit)
    df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
    df['datetime'] = pd.to_datetime(df['timestamp'], unit='ms')
    df.set_index('datetime', inplace=True)
    return df

def calculate_adx(data):
    adx = ADXIndicator(data['high'], data['low'], data['close'], adx_period).adx()
    return adx

def execute_trade(symbol, side, amount, price):
    global in_trade
    try:
        # Calculate the ETH amount based on USD trade_amount
        eth_amount = trade_amount / price
        # Round to 8 decimal places (Kraken's typical precision for crypto)
        eth_amount = round(eth_amount, 8)
        
        order = kraken.create_order(symbol, 'limit', side, eth_amount, {'price': price})
        print(f"Executed {side} limit order for {eth_amount} ETH (${trade_amount} worth) at ${price}")
        in_trade = True
    except Exception as e:
        print(f"Error executing trade: {e}")

def is_symbol_valid(symbol):
    try:
        markets = kraken.load_markets()
        if symbol in markets:
            return True
        else:
            print(f"Symbol {symbol} is not available to trade on Kraken.")
            return False
    except Exception as e:
        print(f"Error loading markets: {e}")
        return False

def run_strategy(symbol):
    global in_trade
    if not is_symbol_valid(symbol):
        return

    data = fetch_data(symbol)
    data['adx'] = calculate_adx(data)

    # Check if not in a trade
    if not in_trade:
        if data['adx'].iloc[-1] > adx_low and data['adx'].iloc[-1] < adx_high:
            if crossover(data['close'], data['high'].shift(2)):
                # Set limit price slightly above the current close for buy order
                limit_price = data['close'].iloc[-1] * (1 + 0.001)  # Example: 0.1% above current close
                execute_trade(symbol, 'buy', trade_amount, limit_price)
            elif crossover(data['low'].shift(2), data['close']):
                # Set limit price slightly below the current close for sell order
                limit_price = data['close'].iloc[-1] * (1 - 0.001)  # Example: 0.1% below current close
                execute_trade(symbol, 'sell', trade_amount, limit_price)

if __name__ == "__main__":
    symbol = 'ETH/USD'
    print(f"Bot started! Running strategy on {symbol}")
    while True:
        print(f"Checking for trade opportunities... {pd.Timestamp.now()}")
        run_strategy(symbol)
        time.sleep(60)  # Sleep for 60 seconds before checking again