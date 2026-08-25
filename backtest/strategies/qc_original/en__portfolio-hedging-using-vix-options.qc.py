# Original QuantConnect / library Python
# locale=en slug="portfolio-hedging-using-vix-options"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

from AlgorithmImports import *
class PortfolioHedgingUsingVIXOptions(QCAlgorithm):
def Initialize(self):
    self.SetStartDate(2010, 1, 1)
    self.SetCash(1000000)
    
    data = self.AddEquity("SPY", Resolution.Minute)
    data.SetLeverage(5)
    self.spy = data.Symbol
    
    data = self.AddEquity("IEF", Resolution.Minute)
    data.SetLeverage(5)
    self.ief = data.Symbol
    
    data = self.AddEquity("VIXY", Resolution.Minute)
    data.SetLeverage(5)
    self.vix = data.Symbol
    
    option = self.AddOption('VIXY', Resolution.Minute)
    option.SetFilter(-20, 20, 25, 35)
    
def OnData(self,slice):
    for i in slice.OptionChains:
        chains = i.Value
        # Max 2 positions - spy and ief are opened. That means option expired.
        invested = [x.Key for x in self.Portfolio if x.Value.Invested]
        if len(invested) = 15 and underlying_price  30 and underlying_price
