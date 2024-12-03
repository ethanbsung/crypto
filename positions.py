import ccxt
import time
import dontshare as d
import logging
from datetime import datetime

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('positions.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Initialize Kraken exchange with rate limiting enabled
kraken = ccxt.kraken({
    'apiKey': d.kraken_api_key,
    'secret': d.kraken_secret_key,
    'enableRateLimit': True,  # Enable built-in rate limiting
})

def print_account_balance():
    try:
        logger.info("Attempting to fetch balance...")
        balance = kraken.privatePostBalance()
        if 'result' in balance:
            usd_balance = float(balance['result'].get('ZUSD', 0))
            logger.info(f"USD Balance: {usd_balance}")
        else:
            logger.error(f"Unexpected balance response: {balance}")
    except ccxt.AuthenticationError as e:
        logger.error(f"Authentication error: {str(e)}")
    except ccxt.RateLimitExceeded as e:
        logger.error(f"Rate limit exceeded: {str(e)}")
        time.sleep(60)
    except ccxt.NetworkError as e:
        logger.error(f"Network error: {str(e)}")
        time.sleep(5)
    except Exception as e:
        logger.error(f"Error fetching balance: {str(e)}")
        logger.error(f"Error type: {type(e)}")

def print_open_positions():
    try:
        positions = kraken.fetch_positions()
        if positions:
            logger.info("Open Positions:")
            for position in positions:
                logger.info(f"Symbol: {position['symbol']}, Amount: {position['amount']}, Side: {position['side']}")
        else:
            logger.info("No open positions.")
    except ccxt.AuthenticationError as e:
        logger.error(f"Authentication error: {str(e)}")
    except ccxt.RateLimitExceeded as e:
        logger.error(f"Rate limit exceeded: {str(e)}")
        time.sleep(60)  # Wait a minute if rate limited
    except Exception as e:
        logger.error(f"Error fetching positions: {str(e)}")

def risk_manager():
    logger.info("Risk manager started")
    
    while True:
        try:
            current_time = datetime.now()
            logger.info(f"\nChecking account status at {current_time}...")
            
            print_account_balance()
            time.sleep(2)  # Add small delay between API calls
            print_open_positions()
            
            logger.info("Next update in 15 minutes...")
            time.sleep(900)  # Sleep for 900 seconds (15 minutes)
            
        except Exception as e:
            logger.error(f"Error in risk manager: {str(e)}")
            time.sleep(60)  # Wait a minute before retrying

if __name__ == "__main__":
    try:
        # Test API connection first
        kraken.privatePostBalance()
        logger.info("API connection successful")
        risk_manager()
    except Exception as e:
        logger.error(f"Failed to start risk manager: {str(e)}")