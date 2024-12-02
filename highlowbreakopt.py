from backtesting import Backtest, Strategy
from backtesting.lib import crossover
from ta.trend import ADXIndicator
import pandas as pd
import numpy as np
import multiprocessing

# Set the multiprocessing start method to 'fork'
multiprocessing.set_start_method('fork')

class HighLowBreak(Strategy):
    adx_period = 14
    adx_low = 25
    adx_high = 35
    risk_reward_ratio = 5
    stop_loss_pct = 0.02  # 2% stop loss

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
            elif crossover(self.data.Low[-2], self.data.Close):
                self.sell(sl=self.data.Close[-1] * (1 + self.stop_loss_pct),
                          tp=self.data.Close[-1] * (1 - self.stop_loss_pct * self.risk_reward_ratio))

# Load data
data = pd.read_csv('/Users/ethansung/quant/memebot/Data/ETHUSD_60.csv')
data['datetime'] = pd.to_datetime(data['datetime'], unit='s')
data.set_index('datetime', inplace=True)
data.sort_index(inplace=True)

# Define the backtest
backtest = Backtest(data, HighLowBreak, cash=100000, commission=.0025)

# Print statement indicating the start of optimization
print("Optimization is running...")

# Run optimization
output = backtest.optimize(
    adx_period=range(10, 30, 2),  # Ensure this is a range object
    adx_low=range(20, 30, 2),     # Ensure this is a range object
    adx_high=range(30, 40, 2),    # Ensure this is a range object
    risk_reward_ratio=[2, 3, 4, 5],  # Use a list instead of np.arange
    stop_loss_pct=[0.01, 0.02, 0.03],         # Use a list instead of np.arange
    maximize='Sharpe Ratio',
    return_heatmap=False
)

# Print the best parameters
print("Optimization completed.")
print("Best parameters found:")
print(output['_strategy'])