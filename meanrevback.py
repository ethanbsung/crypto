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

import pandas as pd
import requests
from backtesting import Backtest, Strategy

# Adjusted parameters for a proper mean reversion strategy
symbols_data = {
    'WIF/USD': {
        'buy_threshold_pct': 1.0,  # Buy if price is 1% below SMA
        'sell_threshold_pct': 1.0  # Sell if price is 1% above SMA
    },
    'POPCAT/USD': {
        'buy_threshold_pct': 3.0,
        'sell_threshold_pct': 7.0
    }
}

sma_period = 20  # Adjusted SMA period to align with mean reversion

# Custom Strategy Class
class MeanReversionStrategy(Strategy):
    # Define all parameters as class variables
    sma_period = 10  # Default SMA period, can be overridden during optimization
    buy_threshold_pct = 3.0  # Default buy threshold
    sell_threshold_pct = 7.0  # Default sell threshold

    def init(self):
        # Calculate SMA using the sma_period parameter
        self.sma = self.I(lambda x: pd.Series(x).rolling(self.sma_period).mean(), self.data.Close)

    def next(self):
        # Calculate thresholds
        buy_threshold = self.sma[-1] * (1 - self.buy_threshold_pct / 100)
        sell_threshold = self.sma[-1] * (1 + self.sell_threshold_pct / 100)

        # Buy condition: price is far below the SMA
        if self.data.Close[-1] < buy_threshold:
            self.buy()

        # Sell condition: price is far above the SMA
        elif self.data.Close[-1] > sell_threshold:
            self.sell()

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

# Backtest function
def backtest_strategy(data, symbol):
    thresholds = symbols_data.get(symbol, {'buy_threshold_pct': 0.0, 'sell_threshold_pct': 0.0})
    buy_threshold_pct = thresholds['buy_threshold_pct']
    sell_threshold_pct = thresholds['sell_threshold_pct']

    print(f"{symbol} - Buy Threshold: {buy_threshold_pct}%, Sell Threshold: {sell_threshold_pct}%")

    bt = Backtest(
        data, 
        MeanReversionStrategy, 
        cash=10_000, 
        commission=0.0025,
        exclusive_orders=True
    )
    stats = bt.run(
        buy_threshold_pct=buy_threshold_pct, 
        sell_threshold_pct=sell_threshold_pct
    )

    # Output the stats in the desired format
    print("\nBacktest Results:")
    print(f"sma_period={sma_period},buy_threshold_pct={buy_threshold_pct},sell_threshold_pct={sell_threshold_pct}")
    print(stats)

    return stats

if __name__ == "__main__":
    symbol = "POPCAT/USD"  # Symbol to trade
    interval = 240  # 4-hour interval

    try:
        # Fetch data from Kraken
        historical_data = fetch_ohlcv_from_kraken(symbol, interval)

        # Print the first few rows for debugging
        print("Fetched Data:")
        print(historical_data.head())

        # Backtest the strategy
        stats = backtest_strategy(historical_data, symbol)
    except Exception as e:
        print(f"Error: {e}")