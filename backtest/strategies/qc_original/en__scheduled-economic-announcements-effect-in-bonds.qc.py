# Original QuantConnect / library Python
# locale=en slug="scheduled-economic-announcements-effect-in-bonds"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

from AlgorithmImports import *
#endregion
class ScheduledEconomicAnnouncementsEffectBonds(QCAlgorithm):
def Initialize(self):
    self.SetStartDate(2002, 1, 1)
    self.SetCash(100000)
    
    self.symbol = "TLT"
    data = self.AddEquity(self.symbol, Resolution.Minute)
    csv_string_file = self.Download('data.quantpedia.com/backtesting_data/economic/scheduled_economic_announcements_bonds.csv')
    dates = csv_string_file.split('\r\n')
    dates = [datetime.strptime(x, "%Y-%m-%d") for x in dates]
    self.liquidate_next_day = False
    self.Schedule.On(self.DateRules.On(dates), self.TimeRules.BeforeMarketClose(self.symbol, 1), self.DayBeforeAnnouncement)
    self.Schedule.On(self.DateRules.EveryDay(self.symbol), self.TimeRules.BeforeMarketClose(self.symbol, 1), self.Rebalance)

def DayBeforeAnnouncement(self):
    if not self.Portfolio[self.symbol].IsLong:
        self.SetHoldings(self.symbol, 1)
        self.liquidate_next_day = True
def Rebalance(self):
    if self.liquidate_next_day:
        self.liquidate_next_day = False
        return
    
    if self.Portfolio[self.symbol].IsLong:
        self.Liquidate(self.symbol)
