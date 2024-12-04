import dontshare as d
import ccxt
import pandas as pd
import time
from datetime import datetime

'''
SYMBOLS TO TRADE:
BTC/USD
ETH/USD
XRP/USD
BNB/USD
ADA/USD
AVAX/USD
LINK/USD
DOT/USD
UNI/USD
LTC/USD
ICP/USD
ETC/USD


MAYBE:
NEAR/USD
'''

symbols = ['BTC/USD', 'ETH/USD', 'XRP/USD', 'BNB/USD', 'ADA/USD', 'AVAX/USD', 'LINK/USD', 'DOT/USD', 'UNI/USD', 'LTC/USD', 'ICP/USD', 'ETC/USD']
timeframe = '1h'
risk_reward_ratio = 3
stop_loss_pct = 0.03

trade_amount_usd = 1
max_slippage = 0.002
order_timeout = 60

minimum_usd_balance = 10
min_data_points = 20