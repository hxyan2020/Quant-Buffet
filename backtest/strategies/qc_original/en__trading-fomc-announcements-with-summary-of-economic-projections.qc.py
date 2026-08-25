# Original QuantConnect / library Python
# locale=en slug="trading-fomc-announcements-with-summary-of-economic-projections"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

from AlgorithmImports import *
#endregion

class TradingFOMCAnnouncementsSummaryEconomicProjections(QCAlgorithm):

def Initialize(self):
    self.SetStartDate(2007, 1, 1)
    self.SetCash(100000)
    
    self.symbol = self.AddEquity("SPY", Resolution.Minute).Symbol

    csv_string_file = self.Download('data.quantpedia.com/backtesting_data/economic/fed_summary_economic_projections.csv')
    dates = csv_string_file.split('\r\n')
    dates = [datetime.strptime(x, "%Y-%m-%d") for x in dates]
    
    self.liquidate_next_day = True
    
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
