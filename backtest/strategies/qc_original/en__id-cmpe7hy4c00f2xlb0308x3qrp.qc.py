# Original QuantConnect / library Python
# locale=en slug="发薪日异常现象"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

from dateutil.relativedelta import relativedelta
from AlgoLib import *

class PayDayAnomaly(XXX):

def Initialize(self):
    self.SetStartDate(2000, 1, 1)
    self.SetCash(100000)
    
    self.market: Symbol = self.AddEquity('SPY', Resolution.Minute).Symbol
    self.liquidate_next_day: bool = False
    
    self.Schedule.On(self.DateRules.EveryDay(self.market), self.TimeRules.BeforeMarketClose(self.market, 1), self.Purchase)

def Purchase(self) -> None:
    alg_time = self.Time
    paydate = self.PaydayDate(alg_time)

    if alg_time.date() == paydate:
        self.SetHoldings(self.market, 1)
        self.liquidate_next_day = True

    if self.liquidate_next_day:
        self.liquidate_next_day = False
        return
    
    if self.Portfolio[self.market].IsLong:
        self.Liquidate(self.market)

def PaydayDate(self, date_time):
    payday = date(date_time.year, date_time.month, 1) + relativedelta(day=15)
    
    if payday.weekday() == 5: # Is saturday.
        payday = payday - timedelta(days=1)
    elif payday.weekday() == 6: # Is sunday.
        payday = payday - timedelta(days=2)
    
    return payday
