# Original QuantConnect / library Python
# locale=zh slug="股票中的货币政策（fomc）动量效应"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

from AlgorithmImports import *
class MonetaryFOMCMomentuminStocks(QCAlgorithm):
def Initialize(self):
    self.SetStartDate(1998, 1, 1)
    self.SetCash(100000)
    
    data = self.AddEquity("SPY", Resolution.Minute)
    data.SetFeeModel(CustomFeeModel())
    self.symbol = data.Symbol
    self.fed_funds = self.AddData(FederalFundsTargetRate, 'FederalFundsTargetRate', Resolution.Daily).Symbol
    
    # import quandl federal rate data
    self.target_rate = self.AddData(QuandlValue, 'FRED/DFEDTARL', Resolution.Daily).Symbol
    
    # Federal funds target rate history.
    self.rate_history = RollingWindow[float](2)
    self.days_to_liquidate = -1
    
    self.Schedule.On(self.DateRules.EveryDay(self.symbol), self.TimeRules.AfterMarketOpen(self.symbol, 1), self.SPYLiquidate)

def OnData(self, data):
    # Until 2009 we are taking data from Quantpedia,
    # then we take data from Quandl
    if self.fed_funds in data and data[self.fed_funds]:
        rate = data[self.fed_funds].Value
        self.rate_history.Add(rate)
        self.Trade() # Trade spy
        
    elif self.target_rate in data and data[self.target_rate] and self.Time.year > 2008:
        rate = data[self.target_rate].Value
        self.rate_history.Add(rate)
        self.Trade() # Trade spy
        
def Trade(self):
    if self.rate_history.IsReady:
        rates = [x for x in self.rate_history]
        previous_rate = rates[-1]
        current_rate = rates[0]
        if current_rate > previous_rate:    # contractionary policy decision
            self.SetHoldings(self.symbol, -1)
        elif current_rate
