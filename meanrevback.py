import ccxt
import pandas as pd
import dontshare as d
import time
from datetime import datetime

kraken = ccxt.kraken({
    'apiKey': d.kraken_api_key,
    'secret': d.kraken_secret_key,
    'enableRateLimit': True,
})

symbol = 'ETH/USD'
timeframe = '5m'

