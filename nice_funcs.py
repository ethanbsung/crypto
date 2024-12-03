import pandas as pd
import numpy as np
import dontshare as d
import time
import ccxt
from datetime import datetime

kraken = ccxt.kraken({
    'apiKey': d.kraken_api_key,
    'secret': d.kraken_secret_key,
    'enableRateLimit': True,
})
'''
def kill_switch():

    # main kill function that works as a taker instead of a maker
    # make sure the kill function reports clearly on excel
    # sleep after killing, needs a breather whenever possible

    openposi = open_positions()[1] # returns T/F for open pos 
    long = open_positions()[3] # this sets long to T/F

    print('KILL SWITCH ACTIVATED... going to loop until limit close...')
    print(f' open position is set to: {openposi} if true we continue to kill')

    btc_kill_size = open_positions()[2] # this gets the open position size
    btc_kill_size = int(btc_kill_size) # this puts it in int form

    while openposi == True:
        print('starting kill swithc loop again until Limit fill...')
        temp_df = pd.DataFrame()
        print('just made a new temp_df for the kill switch, cancelling any open orders...')

        # this cancels all orders
        kraken.cancel_all_orders(symbol)
        # this cancles the conditional order
        kraken.cancel_all_orders(symbol=symbol, params={'untriggered': True})

        print('getting T/F for if open pos... and if long is T/F... ')
        openposi = open_positions()[1]
        long = open_positions()[3]

        #bringing kill size in here because I don't want to ever over sell
        btc_kill_size = open_positions()[2]
        btc_kill_size = int(btc_kill_size)

        print(f'we are inside the kill loop and the size we want to kill is: {btc_kill_size}')

        now = datetime.now()
        dt_string = now.strftime("%m/%d/%Y %H:%M:%S")
        comptime = int(time.time())

        # get bid ask
        ask = get_bid_ask()[0]
        bid = get_bid_ask()[1]

        # close all positions
        if long == False:
            kraken.cancel_all_orders(symbol)
            #this cancels the conditional order
            kraken.cancel_all_orders(symbol=symbol, params={'untriggered': True})
            params = {'timeInForce': 'PostOnly',}
            kraken.create_limit_buy_order(symbol, btc_kill_size, bid, params)
            temp_df['desc'] = ['kill switch']
            temp_df['open_time'] = [comptime]
            print(f'just made a post only BUY to CLOSE order of {btc_kill_size} at {bid}')
            print('sleeping for 30 seconds to see if it fills...')
            time.sleep(30)

        elif long == True:
            kraken.cancel_all_orders(symbol)
            kraken.cancel_all_orders(symbol=symbol, params={'untriggered': True})
            # create the close SELL order cause we are long
            params = {'timeInForce': 'PostOnly',}
            kraken.create_limit_sell_order(symbol, btc_kill_size, ask, params)
            temp_df['desc'] = ['kill switch']
            temp_df['open_time'] = [comptime]
            print(f'just made a post only SELL to CLOSE order of {btc_kill_size} at {ask}')

'''