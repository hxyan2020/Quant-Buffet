# Original QuantConnect / library Python
# locale=zh slug="期权到期周末交易策略"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

from AlgorithmImports import *
class TradingOptionsDuringExpirationWeekends(QCAlgorithm):
def Initialize(self):
    self.SetStartDate(2011, 1, 1)
    self.SetCash(100000)
    
    self.symbol = self.AddEquity("SPY", Resolution.Minute).Symbol
    
    # Next expiry date.
    self.expiry_date = None
    
    option = self.AddOption("SPY", Resolution.Minute)
    option.SetFilter(-20, 20, 25, 35)
    self.Schedule.On(self.DateRules.EveryDay(self.symbol), self.TimeRules.AfterMarketOpen(self.symbol, 1), self.Close)
    
def OnData(self, slice):
    # Open new trades only on market close.
    if not (self.Time.hour == 15 and self.Time.minute == 59):
        return
    
    if self.expiry_date:
        if self.Time.date()
