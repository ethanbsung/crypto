'''
adx_period=10,adx_low=26,adx_high=32,risk_reward_ratio=2,stop_loss_pct=0.03
Start                     2024-01-01 00:00:00
End                       2024-09-30 20:00:00
Duration                    273 days 20:00:00
Exposure Time [%]                   46.894032
Equity Final [$]                258489.635375
Equity Peak [$]                 263962.930475
Return [%]                         158.489635
Buy & Hold Return [%]               14.483696
Return (Ann.) [%]                  254.341829
Volatility (Ann.) [%]              135.603502
Sharpe Ratio                         1.875629
Sortino Ratio                       13.382622
Calmar Ratio                        19.322624
Max. Drawdown [%]                  -13.162903
Avg. Drawdown [%]                   -2.257716
Max. Drawdown Duration       36 days 12:00:00
Avg. Drawdown Duration        3 days 13:00:00
# Trades                                   58
Win Rate [%]                        56.896552
Best Trade [%]                       5.863512
Worst Trade [%]                     -3.288872
Avg. Trade [%]                       1.681154
Max. Trade Duration          11 days 00:00:00
Avg. Trade Duration           2 days 08:00:00
Profit Factor                        2.269784
Expectancy [%]                       1.777132
SQN                                  2.737852
_strategy                        HighLowBreak
'''

from backtesting import Backtest, Strategy
from backtesting.lib import crossover
from ta.trend import ADXIndicator
import pandas as pd

class HighLowBreak(Strategy):
    adx_period = 10
    adx_low = 26
    adx_high = 32
    risk_reward_ratio = 2
    stop_loss_pct = 0.03  # 2% stop loss

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

data = pd.read_csv('/Users/ethansung/quant/memebot/Data/ETHUSD_240.csv')
data['datetime'] = pd.to_datetime(data['datetime'], unit='s')
data.set_index('datetime', inplace=True)
data.sort_index(inplace=True)

backtest = Backtest(data, HighLowBreak, cash=100000, commission=.0025)

output = backtest.run()

print(output)