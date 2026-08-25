# Original QuantConnect / library Python
# locale=zh slug="固定收益中的失业缺口因子"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

import numpy as np
from AlgorithmImports import *
import data_tools
class UnemploymentGapFactorinFixedIncome(QCAlgorithm):
def Initialize(self):
    self.SetStartDate(2000, 1, 1)
    self.SetCash(100000)
    
    self.symbols = {
                    "ASX_XT1"       : "RBA/H05_GLFSURSA",   # 10 Year Commonwealth Treasury Bond Futures, Continuous Contract #1 (Australia)
                    "MX_CGB1"       : "UKONS/ZXDZ_M",       # Ten-Year Government of Canada Bond Futures, Continuous Contract #1 (Canada)
                    "EUREX_FGBL1"   : "UKONS/ZXDK_M",       # Euro-Bund (10Y) Futures, Continuous Contract #1 (Germany)
                    "LIFFE_R1"      : "UKONS/YCNO_M",       # Long Gilt Futures, Continuous Contract #1 (U.K.)
                    "CME_TY1"       : "UKONS/ZXDX_M"        # 10 Yr Note Futures, Continuous Contract #1 (USA)
                    }
    # Monthly unemployment data.
    self.data = {}
    self.period = 3 * 12
    
    for symbol in self.symbols:
        data = self.AddData(data_tools.QuantpediaFutures, symbol, Resolution.Daily)
        data.SetFeeModel(data_tools.CustomFeeModel())
        data.SetLeverage(5)
        
        unempl_symbol = self.symbols[symbol]
        if unempl_symbol == 'ASX_XT1':
            data = self.AddData(data_tools.UnemploymentDataAUD, unempl_symbol, Resolution.Daily)
        else:
            data = self.AddData(data_tools.UnemploymentData, unempl_symbol, Resolution.Daily)
        self.data[symbol] = RollingWindow[float](self.period)
        
    first_key = [x for x in self.symbols.keys()][0]
    self.Schedule.On(self.DateRules.MonthStart(self.symbols[first_key]), self.TimeRules.At(0, 0), self.Rebalance)

def OnData(self, data):
    # store monthly rates
    for symbol in self.symbols:
        unempl_symbol = self.symbols[symbol]
        if unempl_symbol in data and data[unempl_symbol]:
            unempl_rate = data[unempl_symbol].Value
            if unempl_rate != 0:
                self.data[symbol].Add(unempl_rate)

def Rebalance(self):
    # Difference from MA.
    ma_diff = {}
    for symbol in self.symbols:
        if self.Securities[symbol].GetLastData() and (self.Time.date() - self.Securities[symbol].GetLastData().Time.date()).days
