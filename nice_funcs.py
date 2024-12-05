import pandas as pd
import numpy as np
import dontshare as d
import time
import ccxt
from datetime import datetime, timedelta, timezone
import requests
import csv


kraken = ccxt.kraken({
    'apiKey': d.kraken_api_key,
    'secret': d.kraken_secret_key,
    'enableRateLimit': True,
})

def fetch_ohlcv(symbol: str, api_key: str, timeframe: str, start_date: str):
    """
    Fetches OHLCV data for a specified symbol, timeframe, and start date from CoinAPI,
    calculates support and resistance, and saves the data to a CSV file.

    Parameters:
        symbol (str): The trading symbol (e.g., "BINANCE_SPOT_ETH_BTC").
        api_key (str): Your CoinAPI API key.
        timeframe (str): The time period for OHLCV data (e.g., "1HRS", "1DAY").
        start_date (str): The start date in ISO 8601 format (e.g., "2023-03-01T00:00:00").

    Returns:
        None
    """
    # Define the API request details
    url = f"https://rest.coinapi.io/v1/ohlcv/{symbol}/history?period_id={timeframe}&time_start={start_date}"
    headers = {"X-CoinAPI-Key": api_key}  # Pass the API key dynamically

    # Make the API request
    response = requests.get(url, headers=headers)

    # Check if the response is successful
    if response.status_code == 200:
        if response.content:
            # Parse the JSON response
            data = response.json()

            # Prepare the output CSV file
            filename = f"{symbol}_{timeframe}.csv"

            # Initialize lists for resistance and support
            resistance_levels = []
            support_levels = []

            # Calculate resistance and support dynamically
            for i in range(len(data)):
                # Consider data up to the current point
                past_data = data[:i]
                
                if past_data:
                    # Calculate resistance as the maximum high up to the current point
                    resistance = max(d["price_high"] for d in past_data)
                    # Calculate support as the minimum low up to the current point
                    support = min(d["price_low"] for d in past_data)
                else:
                    # Default values for the first data point
                    resistance = None
                    support = None
                
                resistance_levels.append(resistance)
                support_levels.append(support)

            # Write data to the CSV file
            with open(filename, mode="w", newline="", encoding="utf-8") as file:
                writer = csv.writer(file)
                # Write the header
                writer.writerow(["datetime", "open", "high", "low", "close", "volume", "support", "resistance"])
                
                # Write the rows
                for entry, resistance, support in zip(data, resistance_levels, support_levels):
                    writer.writerow([
                        entry.get("time_period_start"),
                        entry.get("price_open"),
                        entry.get("price_high"),
                        entry.get("price_low"),
                        entry.get("price_close"),
                        entry.get("volume_traded"),
                        support,
                        resistance
                    ])

            print(f"Data saved to {filename}")
        else:
            print("Response is empty.")
    else:
        # Handle other HTTP status codes
        print(f"Failed to fetch data. Status code: {response.status_code}")

# Example usage
if __name__ == "__main__":
    # Replace with your API key
    api_key = d.COINAPI_GMAIL

    # Test with different symbols, timeframes, and start dates
    # Correct formats:
    # - symbol: "BINANCE_SPOT_ETH_BTC" (Exchange_TradingPair format)
    # - timeframe: "1HRS", "1DAY", "1MTH", etc. (valid CoinAPI period_id values)
    # - start_date: "YYYY-MM-DDTHH:MM:SS" (ISO 8601 format)

    fetch_ohlcv(
        symbol="BINANCE_SPOT_SOL_USDT",
        api_key = api_key,
        timeframe="1HRS",
        start_date="2023-03-01T00:00:00"
    )

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