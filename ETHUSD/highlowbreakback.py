from backtesting import Backtest, Strategy
from backtesting.lib import crossover
from ta.trend import ADXIndicator
import pandas as pd
import ccxt
from datetime import datetime, timedelta

class HighLowBreakLongOnly(Strategy):
    adx_period = 28
    adx_low = 26
    adx_high = 46
    risk_reward_ratio = 3
    stop_loss_pct = 0.027

    def init(self):
        high = self.data.High
        low = self.data.Low
        close = self.data.Close

        price_data = pd.DataFrame({'High': high, 'Low': low, 'Close': close})

        self.adx = self.I(ADXIndicator(price_data['High'], price_data['Low'], price_data['Close'], self.adx_period).adx)

    def next(self):
        if self.adx[-1] > self.adx_low and self.adx[-1] < self.adx_high:
            if crossover(self.data.Close, self.data.High[-2]):
                self.buy(sl=self.data.Close[-1] * (1 - self.stop_loss_pct),
                         tp=self.data.Close[-1] * (1 + self.stop_loss_pct * self.risk_reward_ratio))


def fetch_ohlcv_kraken(symbol: str, timeframe: str, since: int):
    """Fetch historical OHLCV data from Kraken using CCXT."""
    exchange = ccxt.kraken({
        'rateLimit': 1200,
        'enableRateLimit': True
    })

    ohlcv = exchange.fetch_ohlcv(symbol, timeframe, since)
    df = pd.DataFrame(ohlcv, columns=['timestamp', 'Open', 'High', 'Low', 'Close', 'Volume'])  # Capitalize column names
    df['datetime'] = pd.to_datetime(df['timestamp'], unit='ms')
    df.set_index('datetime', inplace=True)
    df.drop(columns=['timestamp'], inplace=True)
    return df


# Load CSV data
csv_path = '/Users/ethansung/quant/memebot/Data/ETHUSD_240.csv'
csv_data = pd.read_csv(csv_path)
csv_data['datetime'] = pd.to_datetime(csv_data['datetime'], unit='s')  # Convert timestamp
csv_data.set_index('datetime', inplace=True)
csv_data.sort_index(inplace=True)

# Get the last timestamp from the CSV data
last_csv_timestamp = int(csv_data.index[-1].timestamp() * 1000)  # Convert to milliseconds

# Fetch API data starting from the end of the CSV data
symbol = 'ETH/USD'
timeframe = '4h'
api_data = fetch_ohlcv_kraken(symbol, timeframe, last_csv_timestamp)

# Combine CSV and API data
combined_data = pd.concat([csv_data, api_data])
combined_data = combined_data[~combined_data.index.duplicated(keep='last')]  # Remove duplicates
combined_data.sort_index(inplace=True)  # Ensure the data is sorted by datetime

# Filter data for the desired date range
start_date = '2024-01-01'
end_date = '2024-12-08'
filtered_data = combined_data.loc[start_date:end_date]

# Define and run the backtest
backtest = Backtest(filtered_data, HighLowBreakLongOnly, cash=100000, commission=.0025)
output = backtest.run()

print(output)
print("done")