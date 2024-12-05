from backtesting import Backtest, Strategy
from backtesting.lib import crossover
from ta.trend import ADXIndicator
import pandas as pd
import time


class HighLowBreak(Strategy):
    adx_period = 10
    adx_low = 26
    adx_high = 32
    risk_reward_ratio = 2
    stop_loss_pct = 0.03

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

data = pd.read_csv('/home/ebsung/quanttrading/Data/SOLUSD_240.csv')
data['datetime'] = pd.to_datetime(data['datetime'], unit='s')
data.set_index('datetime', inplace=True)
data.sort_index(inplace=True)

# Define date range
start_date = '2023-01-01'
end_date = '2024-11-30'

# Filter data for date range
data = data.loc[start_date:end_date]

backtest = Backtest(data, HighLowBreak, cash=100000, commission=.0025)

output = backtest.run()

print(output)