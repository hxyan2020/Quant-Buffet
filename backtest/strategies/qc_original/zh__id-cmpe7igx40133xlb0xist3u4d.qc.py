# Original QuantConnect / library Python
# locale=zh slug="股票的日内动量"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

from AlgorithmImports import *
class IntradayMomentumEquities(QCAlgorithm):
def Initialize(self):
    self.SetStartDate(2000, 1, 1)
    self.SetCash(100000)
    self.symbol = self.AddEquity("SPY", Resolution.Minute).Symbol
    self.Schedule.On(self.DateRules.EveryDay(self.symbol), self.TimeRules.BeforeMarketClose(self.symbol, 30), self.Rebalance)
    self.Schedule.On(self.DateRules.EveryDay(self.symbol), self.TimeRules.BeforeMarketClose(self.symbol, 1), self.MarketClose)

def Rebalance(self):
    day_history = self.History([self.symbol], 12*30, Resolution.Minute)
    
    if len(day_history) == 12*30 and 'close' in day_history:
        first_half_hour = day_history['close'][:30]
        first_half_hour_ret = self.Return(first_half_hour)
        
        twelfth_half_hour = day_history['close'][-30:]
        twelfth_half_hour_ret = self.Return(twelfth_half_hour)
        if first_half_hour_ret > 0 and twelfth_half_hour_ret > 0:
            self.SetHoldings(self.symbol, 1)
        elif first_half_hour_ret
