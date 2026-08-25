# Original QuantConnect / library Python
# locale=zh slug="固定收益中的反转-收益率变动因子"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

import numpy as np
from AlgorithmImports import *
import data_tools
class ReversalYieldChangeFactor(QCAlgorithm):
def Initialize(self):
    self.SetStartDate(2000, 1, 1)
    self.SetCash(100000)
    
    self.symbols = {
                    "ASX_XT1"     : "AU10YT",        # 10 Year Commonwealth Treasury Bond Futures, Continuous Contract #1 (Australia)
                    "MX_CGB1"     : "CA10YT",        # Ten-Year Government of Canada Bond Futures, Continuous Contract #1 (Canada)
                    "EUREX_FGBL1" : "DE10YT",        # Euro-Bund (10Y) Futures, Continuous Contract #1 (Germany)
                    "LIFFE_R1"    : "GB10YT",        # Long Gilt Futures, Continuous Contract #1 (U.K.)
                    "CME_TY1"     : "US10YT"         # 10 Yr Note Futures, Continuous Contract #1 (USA)
                    }
    self.bond_yield = {}  # Bond yield data
    self.period = 6*21
    self.SetWarmUp(self.period)
    
    for symbol in self.symbols:
        data = self.AddData(data_tools.QuantpediaFutures, symbol, Resolution.Daily)
        data.SetFeeModel(data_tools.CustomFeeModel())
        
        bond_yield_symbol = self.symbols[symbol]
        self.AddData(data_tools.QuantpediaBondYield, bond_yield_symbol, Resolution.Daily)
        
        self.bond_yield[symbol] = RollingWindow[float](self.period)
        
    first_key = [x for x in self.symbols.keys()][0]
    self.rebalance_flag: bool = False
    self.Schedule.On(self.DateRules.MonthStart(first_key), self.TimeRules.At(0, 0), self.Rebalance)
    self.settings.minimum_order_margin_portfolio_percentage = 0.

def OnData(self, data):
    # store daily bond yield values
    for symbol in self.symbols:
        yield_symbol = self.symbols[symbol]
        if yield_symbol in data and data[yield_symbol]:
            bond_yield = data[yield_symbol].Value
            self.bond_yield[symbol].Add(bond_yield)
    
    if not self.rebalance_flag:
        return
    self.rebalance_flag = False
    yield_change = {
        symbol : self.bond_yield[symbol][self.period-1] - self.bond_yield[symbol][0] 
        for symbol, bond in self.symbols.items() 
        if self.bond_yield[symbol].IsReady 
        and all([self.Securities[x].GetLastData() and self.Time.date()
