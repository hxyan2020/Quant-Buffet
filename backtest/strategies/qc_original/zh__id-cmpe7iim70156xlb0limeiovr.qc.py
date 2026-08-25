# Original QuantConnect / library Python
# locale=zh slug="跨资产类别的波动率投资"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

from collections import deque
import numpy as np

class VolatilityInvestingAcrossAssetClasses(QCAlgorithm):

def Initialize(self):
    self.SetStartDate(2015, 1, 1)
    self.SetCash(100000)
    
    self.symbols = ['SPY', 'IWM', 'EUE', 'CNKY', 'EEM', 'EWZ', 'HSI', 'USO', 'GLD', 'SLV', 'EURUSD', 'GBPUSD', 'JPYUSD', 'IEF']
    
    # Daily price data.
    self.data = {}
    self.period = 21
    self.SetWarmUp(self.period)
    
    for symbol in self.symbols:
        data = self.AddEquity(symbol, Resolution.Daily)
        data.SetLeverage(5)
        
        data_symbol = data.Symbol
        option = self.AddOption(data_symbol, Resolution.Minute)
        self.data[symbol] = deque(maxlen = self.period)
    
    self.last_day = -1
    
    self.invested_etf = []

def OnData(self, slice):
    # Check once a day.
    if self.Time.day == self.last_day:
        return
    self.last_day = self.Time.day

    # Store underlying daily price data.
    for symbol in self.symbols:
        if symbol in slice and slice[symbol]:
            price = slice[symbol].Value
            self.data[symbol].append(price)

    if self.IsWarmingUp: return
    
    weight_ratio = sum([1 / Volatility(self.data[symbol]) for symbol in self.data if len(self.data[symbol]) == self.data[symbol].maxlen])
    if weight_ratio == 0: return

    invested = [x.Key for x in self.Portfolio if x.Value.Invested]
    if len(invested)
