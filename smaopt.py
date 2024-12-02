from backtesting import Backtest, Strategy
from backtesting.lib import crossover
import pandas as pd
import multiprocessing

# Set the multiprocessing start method to 'fork'
multiprocessing.set_start_method('fork')

class SMAStrategy(Strategy):
    window_short = 13
    window_long = 32
    stoploss_multiple = 0.02
    risk_reward_ratio = 5

    def init(self):
        self.in_trade = False

    def calculate_sma(self, close_prices, window):
        if not isinstance(close_prices, pd.Series):
            close_prices = pd.Series(close_prices)
        sma_values = close_prices.rolling(window=window).mean()
        return sma_values

    def next(self):
        if len(self.data) < self.window_long:
            return
        
        sma_short_values = self.calculate_sma(self.data.Close, self.window_short)
        sma_long_values = self.calculate_sma(self.data.Close, self.window_long)

        if crossover(sma_short_values, sma_long_values) and not self.in_trade:
            entry_price = self.data.Close[-1]
            stop_loss = entry_price * (1 - self.stoploss_multiple)
            take_profit = entry_price * (1 + self.stoploss_multiple * self.risk_reward_ratio)
            self.buy(sl=stop_loss, tp=take_profit)
            self.in_trade = True

        elif crossover(sma_long_values, sma_short_values) and self.in_trade:
            self.position.close()
            self.in_trade = False

data = pd.read_csv('/Users/ethansung/quant/memebot/Data/ETHUSD_30.csv')
data['datetime'] = pd.to_datetime(data['datetime'], unit='s')
data.set_index('datetime', inplace=True)
data.sort_index(inplace=True)

start_date = '2023-01-01'
end_date = '2024-11-30'

data = data.loc[start_date:end_date]

bt = Backtest(data, SMAStrategy, cash=100000, commission=0.0025)

print("Optimization is starting...")

# Optimization
stats = bt.optimize(
    window_short=range(5, 20, 1),
    window_long=range(20, 50, 1),
    stoploss_multiple=[0.01, 0.02, 0.03],
    risk_reward_ratio=[3, 4, 5, 6],
    maximize='Equity Final [$]'
)

print("Optimization completed.")
print("Best parameters found:")
print(stats['_strategy'])