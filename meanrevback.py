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
symbols = ['WIF/USD','POPCAT/USD']
timeframe = '1h'



