# Original QuantConnect / library Python
# locale=en slug="市场季节性效应策略"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

from AlgoLib import *

class SeasonalityInEquitiesAlgorithm(XXX):

def Initialize(self):
    self.SetStartDate(1999, 1, 1)  
    self.SetCash(100000)

    self.AddEquity("SPY", Resolution.Daily)  
    self.AddEquity("SHY", Resolution.Daily)  

    self.Schedule.On(self.DateRules.MonthStart("SPY"), 
self.TimeRules.AfterMarketOpen("SPY"), self.Rebalance)

def Rebalance(self):
    if self.Time.month == 5:
        self.Liquidate("SPY")
    if self.Time.month == 11:
        self.SetHoldings("SPY", 1)
