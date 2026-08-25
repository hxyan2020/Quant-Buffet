# Original QuantConnect / library Python
# locale=en slug="payroll-news-timing-in-fx"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

from AlgorithmImports import *
import numpy as np
import data_tools
#endregion

class PayrollNewsTiminginFX(QCAlgorithm):

def Initialize(self):
    self.SetStartDate(2000, 1, 1)
    self.SetCash(100000)
   
    self.symbols:dict[str, str] = {
        "AUDUSD" : "QAD", # Australian Dollar Futures, Continuous Contract #1
        "GBPUSD" : "QBP", # British Pound Futures, Continuous Contract #1
        "CADUSD" : "QCD", # Canadian Dollar Futures, Continuous Contract #1
        "EURUSD" : "QEC", # Euro FX Futures, Continuous Contract #1
        "JPYUSD" : "QJY", # Japanese Yen Futures, Continuous Contract #1
        "NZDUSD" : "QNE", # New Zealand Dollar Futures, Continuous Contract #1
        "CHFUSD" : "QSF"  # Swiss Franc Futures, Continuous Contract #1
    }

    self.SetTimeZone(TimeZones.NewYork)

    # storing most recent open interest for every currency
    self.recent_net_open_interest:dict[str, float] = {}

    for forex_symbol, cot_symbol in self.symbols.items():
        # forex data
        data = self.AddForex(forex_symbol, Resolution.Minute, Market.Oanda)
        data.SetFeeModel(data_tools.CustomFeeModel())
        data.SetLeverage(10)
        
        # COT data
        self.AddData(data_tools.CommitmentsOfTraders, cot_symbol, Resolution.Daily)

    self.rebalance_flag:bool = False
    self.recent_month:int = -1
    
def OnData(self, data):
    # liquidate one hour after announcement
    if self.Time.hour == 9 and self.Time.minute == 30:
        if self.Portfolio.Invested:
            self.Liquidate()

    # first friday of the month
    if self.Time.weekday() == 4 and self.Time.month != self.recent_month:
        self.rebalance_flag = True

    if self.Time.month != self.recent_month:
        self.recent_month = self.Time.month

    net_open_interest:dict[str, float] = {}

    # store most recent open interest for every currency
    for forex_symbol, cot_symbol in self.symbols.items():
        if cot_symbol in data and data[cot_symbol]:
            # forex data is still comming in
            if self.Securities[forex_symbol].GetLastData() and (self.Time.date() - self.Securities[forex_symbol].GetLastData().Time.date()).days
