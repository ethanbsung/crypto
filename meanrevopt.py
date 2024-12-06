from backtesting import Backtest
from meanrevback import MeanReversionStrategy  # Import updated strategy
import pandas as pd
import multiprocessing
import requests

# Set the multiprocessing start method to 'fork'
multiprocessing.set_start_method('fork')

# Function to fetch OHLCV data from Kraken
def fetch_ohlcv_from_kraken(symbol, interval):
    # Map symbol to Kraken format
    symbol = symbol.replace("/", "").upper()
    url = f"https://api.kraken.com/0/public/OHLC"
    params = {
        'pair': symbol,
        'interval': interval  # Interval in minutes: 1, 5, 15, 30, 60, 240, 1440, 10080, 21600
    }

    response = requests.get(url, params=params)
    response.raise_for_status()  # Raise an error for bad HTTP responses

    data = response.json()
    if 'error' in data and data['error']:
        raise ValueError(f"Kraken API Error: {data['error']}")

    pair_key = list(data['result'].keys())[0]  # Get the first key (symbol-specific data)
    ohlcv_data = data['result'][pair_key]

    # Convert data to DataFrame
    df = pd.DataFrame(ohlcv_data, columns=[
        'Time', 'Open', 'High', 'Low', 'Close', 'Volume', 'VWAP', 'Trades'
    ])
    df['Time'] = pd.to_datetime(df['Time'], unit='s')
    df.set_index('Time', inplace=True)

    # Keep only the relevant columns for backtesting
    df = df[['Open', 'High', 'Low', 'Close', 'Volume']].astype(float)

    return df

# Fetch the data for POPCAT/USD from Kraken
symbol = "POPCAT/USD"
interval = 240  # 4-hour interval
print("Fetching OHLCV data from Kraken...")
historical_data = fetch_ohlcv_from_kraken(symbol, interval)
print("Fetched Data:")
print(historical_data.head())

# Define the backtest
backtest = Backtest(historical_data, MeanReversionStrategy, cash=10000, commission=0.0025, exclusive_orders=True)

# Print statement indicating the start of optimization
print("Optimization is running...")

# Run optimization
output = backtest.optimize(
    sma_period=range(10, 50, 5),               # Range for the SMA period
    buy_threshold_pct=range(1, 10, 1),         # Range for buy threshold percentage
    sell_threshold_pct=range(1, 10, 1),        # Range for sell threshold percentage
    maximize='Sharpe Ratio',                   # Optimization goal
    return_heatmap=False                       # Don't return a heatmap
)

# Print the best parameters
print("Optimization completed.")
print("Best parameters found:")
print(output['_strategy'])