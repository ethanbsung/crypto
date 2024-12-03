import ccxt
import pandas as pd
import dontshare as d
import time, schedule
from datetime import datetime
from nice_funcs import kill_switch
import warnings
warnings.filterwarnings("ignore")


############## INPUTS ###############
amount_usd = 1
symbol = 'ETH/USD'
perc_from_lh = .35
close_seconds = 60*47
max_lh = 800
timeframe = '1m'
num_bars = 180
max_risk = 1000
sl_perc = 0.1
exit_perc = 0.002
max_tr = 550
quartile = 0.33
time_limit = 60
sleep = 30
#####################################

kraken = ccxt.kraken({
    'apiKey': d.kraken_api_key,
    'secret': d.kraken_secret_key,
    'enableRateLimit': True,
})

def fetch_market_data():
    # Fetch market data for ETH/USD
    ohlcv = kraken.fetch_ohlcv(symbol, timeframe, limit=num_bars)
    df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
    df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
    return df

def place_orders():
    # Example function to place buy and sell orders
    ticker = kraken.fetch_ticker(symbol)
    bid = ticker['bid']
    ask = ticker['ask']
    
    # Calculate your bid and ask prices based on your strategy
    my_bid = bid * (1 - perc_from_lh)
    my_ask = ask * (1 + perc_from_lh)
    
    # Place buy order
    kraken.create_limit_buy_order(symbol, amount_usd / bid, my_bid)
    
    # Place sell order
    kraken.create_limit_sell_order(symbol, amount_usd / ask, my_ask)

