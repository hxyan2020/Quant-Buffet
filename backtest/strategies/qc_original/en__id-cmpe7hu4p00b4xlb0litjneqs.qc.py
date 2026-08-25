# Original QuantConnect / library Python
# locale=en slug="全球股指中的市场季节性效应"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

from MyAlgos import *

class SeasonalEquityStrategy(XXX):

def Initialize(self):
    self.SetStartDate(2005, 1, 1)  
    self.SetCash(100000) 

    self.AddEquity("AAPL", Resolution.Daily)
    self.AddEquity("GOOG", Resolution.Daily)
    
    self.Schedule.On(self.DateRules.MonthStart("AAPL"), self.TimeRules.AfterMarketOpen("AAPL"), self.Rebalance)
    
def Rebalance(self):
    if self.Time.month == 6:
        self.Liquidate("AAPL")
    if self.Time.month == 12:
        self.SetHoldings("AAPL", 1)
