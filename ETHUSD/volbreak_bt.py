import yfinance as yf
import pandas as pd
from backtesting import Backtest, Strategy

# Step 1: Fetch Historical Data Using yfinance
def fetch_yfinance_data(symbol='BTC-USD', start_date='2023-01-01', end_date='2024-12-06'):
    data = yf.download(symbol, start=start_date, end=end_date)

    # Rename columns to match Backtest library requirements
    data = data.rename(columns={
        'Open': 'Open',
        'High': 'High',
        'Low': 'Low',
        'Close': 'Close',
        'Volume': 'Volume'
    })

    # Ensure the index is flat
    data.reset_index(inplace=True)

    # Set the 'Date' column as the index
    data.set_index('Date', inplace=True)

    # Ensure data includes only required columns
    data = data[['Open', 'High', 'Low', 'Close', 'Volume']]
    return data

# Fetch data
symbol = 'BTC-USD'  # Bitcoin to USD
data = fetch_yfinance_data(symbol)

# Step 2: Define the Momentum Breakout Strategy
class MomentumBreakout(Strategy):
    lookback = 20  # Lookback period for the high and volume average
    volume_factor = 1.5  # Volume multiplier for breakout confirmation

    def init(self):
        # Calculate the breakout high and average volume
        self.high = self.data.High.rolling(self.lookback).max()
        self.avg_volume = self.data.Volume.rolling(self.lookback).mean()

    def next(self):
        # Check breakout conditions
        if (self.data.Close[-1] > self.high[-1] and
            self.data.Volume[-1] > self.volume_factor * self.avg_volume[-1]):
            self.buy()
        elif self.position:
            # Trailing stop-loss: Close position if price drops below 10-day low
            trailing_stop = min(self.data.Close[-10:])
            if self.data.Close[-1] < trailing_stop:
                self.position.close()

# Step 3: Run the Backtest
bt = Backtest(data, MomentumBreakout, cash=100000, commission=0.0025)  # Commission: 0.25%
stats = bt.run()
bt.plot()

# Step 4: Display Results
print(stats)