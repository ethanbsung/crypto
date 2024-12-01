import ccxt
import time
import logging
import dontshare
import dontshare as d

# Set up logging
logging.basicConfig(level=logging.INFO, filename='crypto_bot.log', filemode='a',
                    format='%(asctime)s - %(levelname)s - %(message)s')

# Initialize Kraken API
exchange = ccxt.kraken({
    'apiKey': d.API_KEY,
    'secret': d.SECRET_KEY,
})

def fetch_usdc_balance():
    """Fetch and print the account balance in USDC."""
    try:
        balance = exchange.fetch_balance()
        usdc_balance = balance['USDC']['free'] if 'USDC' in balance else 0
        print(f"USDC Balance: {usdc_balance:.2f}")
        logging.info(f"USDC Balance: {usdc_balance:.2f}")
    except Exception as e:
        logging.error(f"Error fetching USDC balance: {e}")

def run_bot():
    """Main loop to print USDC balance."""
    logging.info("Starting balance checker bot...")
    while True:
        fetch_usdc_balance()  # Print USDC balance
        time.sleep(60)  # Wait for 1 minute before checking again

if __name__ == "__main__":
    run_bot()