import ccxt
import time
import dontshare as d

# Initialize Kraken exchange
kraken = ccxt.kraken({
    'apiKey': d.kraken_api_key,
    'secret': d.kraken_secret_key,
})

def print_account_balance():
    try:
        balance = kraken.fetch_balance()
        usd_balance = balance['total'].get('USD', 0)
        print(f"USD Balance: {usd_balance}")
    except Exception as e:
        print(f"Error fetching balance: {e}")

def print_open_positions():
    try:
        # Fetch open positions
        positions = kraken.fetch_positions()
        if positions:
            print("Open Positions:")
            for position in positions:
                print(f"Symbol: {position['symbol']}, Amount: {position['amount']}, Side: {position['side']}")
        else:
            print("No open positions.")
    except Exception as e:
        print(f"Error fetching positions: {e}")

def risk_manager():
    while True:
        print("Checking account status...")
        print_account_balance()
        print_open_positions()
        print("Next update in 15 minutes...\n")
        time.sleep(900)  # Sleep for 900 seconds (15 minutes)

if __name__ == "__main__":
    risk_manager()