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
'''
SYMBOLS TO TRADE:
SOL/USD
TON/USD
PEPE/USD
CRO/USD
TAO/USD
KAS/USD
TIA/USD
WIF/USD
BONK/USD
FLOKI/USD
POPCAT/USD

MAYBE:
JUP/USD
NEAR/USD
RENDER/USD
PYTH/USD

'''
symbols_data = {
    'WIF/USD': {
        'buy_range': (14, 15),
        'sell_range': (14, 22)
    },
    'POPCAT/USD': {
        'buy_range': (10, 12),
        'sell_range': (18, 20)
    }
}
def get_ranges(symbol):
    return symbols_data.get(symbol, {'buy_range': (0, 0), 'sell_range': (0, 0)})

symbol = 'WIF/USD'
ranges = get_ranges(symbol)
buy_range = ranges['buy_range']
sell_range = ranges['sell_range']


