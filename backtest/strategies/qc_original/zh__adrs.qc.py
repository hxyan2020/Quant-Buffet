# Original QuantConnect / library Python
# locale=zh slug="利用美国存托凭证（adrs）进行价差交易"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

from AlgorithmImports import *
class SpreadTradingADRs(QCAlgorithm):
def Initialize(self):
    self.SetStartDate(2000, 1, 1)
    self.SetCash(100000)
    self.symbols = ['SPY', 'FXI']
    
    self.k = -0.004
    
    for symbol in self.symbols:
        self.AddEquity(symbol, Resolution.Minute)
    
    self.spy_open_price = 0
    self.fxi_open_price = 0
    
    self.Schedule.On(self.DateRules.EveryDay(self.symbols[0]), self.TimeRules.AfterMarketOpen(self.symbols[0], 1), self.MarketOpen)
    self.Schedule.On(self.DateRules.EveryDay(self.symbols[0]), self.TimeRules.BeforeMarketClose(self.symbols[0], 1), self.Rebalance)

def MarketOpen(self):
    if self.Securities.ContainsKey(self.symbols[0]) and self.Securities.ContainsKey(self.symbols[1]):
        spy_price = self.Securities[self.symbols[0]].Open
        fxi_price = self.Securities[self.symbols[1]].Open
        if spy_price != 0 and fxi_price != 0:
            self.spy_open_price = spy_price
            self.fxi_open_price = fxi_price
                    
def Rebalance(self):
    self.Liquidate()
    
    if self.Securities.ContainsKey(self.symbols[0]) and self.Securities.ContainsKey(self.symbols[1]):
        spy_price = self.Securities[self.symbols[0]].Close
        fxi_price = self.Securities[self.symbols[1]].Close
        
        if spy_price != 0 and fxi_price != 0 and self.spy_open_price != 0 and self.fxi_open_price != 0:
            spy_ret = spy_price / self.spy_open_price - 1
            fxi_ret = fxi_price / self.fxi_open_price - 1
            
            if fxi_ret - spy_ret
