# Original QuantConnect / library Python
# locale=en slug="股票中的一月效应"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

from AlgoLib import *

class JanuaryEffectInStocks(XXX):

def Initialize(self):
    self.SetStartDate(2000, 1, 1)  
    self.SetCash(100000) 

    data = self.AddEquity("SPY", Resolution.Daily)
    data.SetLeverage(10)
    self.large_cap = data.Symbol
    
    data = self.AddEquity("IWM", Resolution.Daily)
    data.SetLeverage(10)
    self.small_cap = data.Symbol

    self.start_price = None
    self.recent_month = -1
    
def OnData(self, data):
    if self.recent_month == self.Time.month:
        return
    self.recent_month = self.Time.month

    if self.Securities[self.large_cap].GetLastData() and self.Securities[self.small_cap].GetLastData():
        if (self.Time.date() - self.Securities[self.large_cap].GetLastData().Time.date()).days
