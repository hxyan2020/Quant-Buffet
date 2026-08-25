# Original QuantConnect / library Python
# locale=en slug="short-term-reversal-in-equity-index-futures"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

import numpy as np
from AlgorithmImports import *
class ShortTermReversal(QCAlgorithm):
def Initialize(self):
    self.SetStartDate(2000, 1, 1)
    self.SetCash(100000)
    
    self.symbols = ['EWG', 'EWQ', 'EWI', 'EWP', 'EWN', 'EWK', 'EWO']
    
    # Daily price data.
    self.data = {}
    self.period = 5
    self.SetWarmUp(self.period)
    
    for symbol in self.symbols:
        data = self.AddEquity(symbol, Resolution.Daily)
        data.SetFeeModel(CustomFeeModel())
        data.SetLeverage(5)
        
        self.data[symbol] = RollingWindow[float](self.period)
    
    self.Schedule.On(self.DateRules.Every(DayOfWeek.Thursday), self.TimeRules.AfterMarketOpen(self.symbols[0]), self.Rebalance)
def OnData(self, data):
    for symbol in self.data:
        symbol_obj = self.Symbol(symbol)
        if symbol_obj in data.Keys:
            if data[symbol_obj]:
                price = data[symbol_obj].Value
                if price != 0:
                    self.data[symbol].Add(price)
def Rebalance(self):
    self.Liquidate()
    
    symbol_return = {}
    for symbol in self.symbols:
        if self.data[symbol].IsReady: 
            if self.Securities[symbol].GetLastData() and (self.Time.date() - self.Securities[symbol].GetLastData().Time.date()).days  avg_ret]
        losers = [x[0] for x in return_diff.items() if symbol_return[x[0]]
