# Original QuantConnect / library Python
# locale=zh slug="在月末最后一小时做空股票"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

from AlgorithmImports import *
class ShortingStocks(QCAlgorithm):
def Initialize(self):
    self.SetStartDate(2002, 1, 1)
    self.SetCash(100000)
    self.symbol = self.AddEquity("SPY", Resolution.Minute).Symbol
    
    self.Schedule.On(self.DateRules.MonthEnd(self.symbol), self.TimeRules.At(15, 0), self.Open)
    self.Schedule.On(self.DateRules.MonthEnd(self.symbol), self.TimeRules.BeforeMarketClose(self.symbol, 1), self.Close)
    
def Open(self):
    if not self.Portfolio[self.symbol].IsShort:
        self.SetHoldings(self.symbol, -1)
    
def Close(self):
    if self.Portfolio[self.symbol].IsShort:
        self.Liquidate(self.symbol)
