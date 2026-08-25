# Original QuantConnect / library Python
# locale=zh slug="联邦公开市场委员会（fomc）周期与信用风险"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

from AlgorithmImports import *
class FOMCCycleAndCreditRisk(QCAlgorithm):
def Initialize(self):
    self.SetStartDate(2012, 1, 1)   # HYG price is causing margin call in 2011.
    self.SetCash(100000)
    
    self.weights = { "HYG" : 1, 'IEI' : -0.5, 'SHY': -0.5 }
    
    for symbol in self.weights:
        data = self.AddEquity(symbol, Resolution.Minute)
        data.SetLeverage(5) # leverage can be set according to the strategy
    csv_string_file = self.Download('data.quantpedia.com/backtesting_data/economic/fed_days.csv')
    dates = csv_string_file.split('\r\n')
    dates_before_fed = [datetime.strptime(x, "%Y-%m-%d") for x in dates]
    
    self.trade_flag = False
    self.days_to_switch_positions = 5
    
    symbol = [x for x in self.weights.keys()][0]
    self.Schedule.On(self.DateRules.On(dates_before_fed), self.TimeRules.AfterMarketOpen(symbol, 1), self.FEDDays)
    self.Schedule.On(self.DateRules.EveryDay(symbol), self.TimeRules.AfterMarketOpen(symbol, 1), self.Rebalance)
    
# At FED day go +1.0HYG - 0.5xIEI - 0.5xSHY
def FEDDays(self):
    # At first liquidate portfolio on FED days
    self.Liquidate()
    
    self.FedDaysAndOddWeeksInvestment()
    self.days_to_switch_positions = 5
    self.trade_flag = True
# every odd week go +1.0xHYG - 0.5xIEI - 0.5xSHY
# every even week go -1.0xHYG + 0.5xIEI + 0.5xSHY
def Rebalance(self):
    if self.trade_flag:
        if self.days_to_switch_positions == 0: 
            if self.Portfolio["HYG"].IsLong:
                self.FedDaysAndEvenWeeksInvestment()
            else:
                self.FedDaysAndOddWeeksInvestment()
            self.days_to_switch_positions = 5
        self.days_to_switch_positions -= 1

def FedDaysAndOddWeeksInvestment(self):
    for symbol, weight in self.weights.items():
        if self.Securities[symbol].Price != 0:
            self.SetHoldings(symbol, weight)
def FedDaysAndEvenWeeksInvestment(self):
    for symbol, weight in self.weights.items():
        if self.Securities[symbol].Price != 0:
            self.SetHoldings(symbol, -weight)
