# Original QuantConnect / library Python
# locale=en slug="option-expiration-week-effect"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

from AlgoLib import *

class OptionExpirationWeekEffect(XXX):

def Initialize(self):
    self.SetStartDate(2010, 1, 1)
    self.SetCash(10000)

    self.symbol = self.AddEquity("OEF", Resolution.Minute).Symbol
    
    option = self.AddOption("OEF")
    option.SetFilter(-3, 3, timedelta(0), timedelta(days = 60))       

    self.SetBenchmark("OEF")
    self.near_expiry = datetime.min
    
    self.Schedule.On(self.DateRules.Every(DayOfWeek.Monday, DayOfWeek.Monday), self.TimeRules.AfterMarketOpen(self.symbol, 1), self.Rebalance)

def OnData(self, slice):
    if self.Time.date() == self.near_expiry.date():
        self.Liquidate()

def Rebalance(self):
    calendar = self.TradingCalendar.GetDaysByType(TradingDayType.OptionExpiration, self.Time, self.EndDate)
    expiries = [i.Date for i in calendar]
    if len(expiries) == 0: return

    self.near_expiry = expiries[0]

    if (self.near_expiry - self.Time).days
