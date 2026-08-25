# Original QuantConnect / library Python
# locale=en slug="selling-options-on-bond-etfs"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

from AlgorithmImports import *
class SellingOptionsonBondETFs(QCAlgorithm):
def Initialize(self):
    self.SetStartDate(2000, 1, 1)
    self.SetCash(100000)
    
    data = self.AddEquity("BIL", Resolution.Minute)
    self.bills = data.Symbol
    data.SetLeverage(5)
    
    data = self.AddEquity("TLT", Resolution.Minute)
    self.symbol = data.Symbol
    data.SetLeverage(5)
    
    option = self.AddOption("TLT", Resolution.Minute)
    option.SetFilter(-20, 20, 25, 35)
    
    self.last_day = -1
    
def OnData(self,slice):
    # Check once a day.
    if self.Time.day == self.last_day:
        return
    self.last_day = self.Time.day
    
    for i in slice.OptionChains:
        chains = i.Value
        # Only bill position is opened.
        invested = [x.Key for x in self.Portfolio if x.Value.Invested]
        if len(invested)
