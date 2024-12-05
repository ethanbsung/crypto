import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import ccxt
import pandas as pd
import dontshare as d
import time
from datetime import datetime, timedelta
import logging
import requests
import json

kristen = ccxt.kraken({
    'apiKey': d.kraken_api_key,
    'secret': d.kraken_secret_key,
    'enableRateLimit': True,
})

'''
SYMBOLS TO TRADE:
WIF/USD
POPCAT/USD
SOL/USD
TON/USD
PEPE/USD
CRO/USD
TAO/USD
KAS/USD
TIA/USD
BONK/USD
FLOKI/USD

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

print(f"{symbol} - Buy range: {buy_range}, Sell range: {sell_range}")

