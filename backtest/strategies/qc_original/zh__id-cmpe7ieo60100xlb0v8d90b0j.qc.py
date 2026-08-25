# Original QuantConnect / library Python
# locale=zh slug="在期权到期日做空股票策略"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

from AlgorithmImports import *
#endregion
class OptionExpirationWeekEffect(QCAlgorithm):
def Initialize(self):
    self.SetStartDate(2010, 1, 1)
    self.SetCash(100000)
    
    self.symbol = self.AddEquity('DIA', Resolution.Minute).Symbol
    option = self.AddOption('DIA')
    option.SetFilter(-3, 3, timedelta(0), timedelta(days = 60))       
    
    self.SetBenchmark('DIA')
    self.last_expiry = datetime.min
    
    self.Schedule.On(self.DateRules.Every(DayOfWeek.Tuesday, DayOfWeek.Tuesday), self.TimeRules.AfterMarketOpen(self.symbol), self.GetExpiryDay)
    self.Schedule.On(self.DateRules.Every(DayOfWeek.Thursday, DayOfWeek.Thursday), self.TimeRules.AfterMarketOpen(self.symbol), self.Open)
    self.Schedule.On(self.DateRules.Every(DayOfWeek.Friday, DayOfWeek.Friday), self.TimeRules.AfterMarketOpen(self.symbol), self.Close)
def GetExpiryDay(self):
    # Expiry days are available only on Tuesday
    calendar = self.TradingCalendar.GetDaysByType(TradingDayType.OptionExpiration, self.Time, self.EndDate)
    expiries = [i.Date for i in calendar]
    if len(expiries) == 0: return
    self.last_expiry = expiries[0]
def Close(self):
    # Liquidate on Friday
    self.Liquidate()

def Open(self):
    # Buy on Thursday before expiry date.
    if (self.last_expiry - self.Time).days
