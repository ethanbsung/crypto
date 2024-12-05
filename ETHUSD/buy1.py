import sys
import os
import time
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import ccxt
import dontshare as d

def place_bid_and_sell(api_key: str, api_secret: str):
    """
    Places a limit buy order for ETH/USD on Kraken and, if executed, sets a limit sell order
    $100 higher than the current ETH price.

    Parameters:
    """
    # Define the amount of ETH to buy
    volume = 0.002  # Fixed amount of ETH to buy

    # Initialize Kraken exchange with API credentials
    exchange = ccxt.kraken({
        'apiKey': d.kraken_api_key,
        'secret': d.kraken_secret_key,
        'enableRateLimit': True,
    })

    try:
        # Fetch the current market data for ETH/USD
        ticker = exchange.fetch_ticker('ETH/USD')
        current_bid_price = ticker['bid']  # Current bid price

        print(f"Current Bid Price: ${current_bid_price:.2f}")

        print(f"Buying {volume} ETH")

        # Place a limit buy order at the current bid price
        buy_order = exchange.create_limit_buy_order('ETH/USD', volume, current_bid_price)
        print("Limit Buy Order Placed:", buy_order)

        # Wait for the buy order to fill
        order_id = buy_order['id']
        timeout = 300  # Timeout in seconds (e.g., 5 minutes)
        interval = 10  # Check every 10 seconds
        elapsed_time = 0

        while elapsed_time < timeout:
            order_status = exchange.fetch_order(order_id, 'ETH/USD')['status']
            if order_status == 'closed':
                print("Buy order filled.")
                break
            elif order_status == 'canceled':
                print("Buy order was canceled.")
                return
            else:
                print(f"Order status: {order_status}. Waiting for it to fill...")
                time.sleep(interval)
                elapsed_time += interval

        if order_status != 'closed':
            print("Buy order not filled within the timeout period. Canceling order...")
            exchange.cancel_order(order_id, 'ETH/USD')

        # If the order was filled, place the sell order
        if order_status == 'closed':
            # Set the limit sell price $100 higher than the current price
            limit_sell_price = current_bid_price + 100
            print(f"Setting limit sell order at ${limit_sell_price:.2f}")

            # Place the limit sell order
            sell_order = exchange.create_limit_sell_order('ETH/USD', volume, limit_sell_price)
            print("Limit Sell Order Placed:", sell_order)

    except ccxt.BaseError as e:
        print(f"An error occurred: {str(e)}")

if __name__ == "__main__":
    # Replace with your Kraken API credentials
    API_KEY = d.kraken_api_key
    API_SECRET = d.kraken_secret_key

    place_bid_and_sell(API_KEY, API_SECRET)