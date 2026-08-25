# Original QuantConnect / library Python
# locale=en slug="原油预测股票收益"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

from data_tools import QuantpediaFutures, QuandlValue, CustomFeeModel, InterestRate3M
from AlgoLib import *
from typing import List, Dict
import numpy as np
from scipy import stats
from collections import deque

class CrudeOilPredictsEquityReturns(XXX):

def Initialize(self):
    self.SetStartDate(2000, 1, 1)
    self.SetCash(100000)

    self.min_period:int = 13
    self.leverage:int = 2

    self.data:Dict[Symbol, deque] = {}

    self.symbols:List[str] = [
        "CME_ES1",  # E-mini S&P 500 Futures, Continuous Contract #1
        "CME_CL1"   # Crude Oil Futures, Continuous Contract #1
    ]
    
    self.cash:Symbol = self.AddEquity('SHY', Resolution.Daily).Symbol
    self.risk_free_rate:Symbol = self.AddData(InterestRate3M, 'IR3TIB01USM156N', Resolution.Daily).Symbol
    
    for symbol in self.symbols:
        data = self.AddData(QuantpediaFutures, symbol, Resolution.Daily)
        data.SetLeverage(self.leverage)
        data.SetFeeModel(CustomFeeModel())
        self.data[symbol] = deque()
    
    self.Settings.MinimumOrderMarginPortfolioPercentage = 0.
    self.recent_month:int = -1

def OnData(self, data:Slice) -> None:
    rebalance_flag:bool = False
    
    for symbol in self.symbols:
        if symbol in data:
            if self.recent_month != self.Time.month:
                rebalance_flag = True
                
            if data[symbol]:
                price:float = data[symbol].Value
                self.data[symbol].append(price)

    if rebalance_flag:
        self.recent_month = self.Time.month
    
    ir_last_update_date:Dict[str, datetime.date] = InterestRate3M.get_last_update_date()
    last_update_date:Dict[str, datetime.date] = QuantpediaFutures.get_last_update_date()

    rf_rate:float = .0
    # check if data is still coming
    if self.Securities[self.risk_free_rate].GetLastData() and ir_last_update_date[self.risk_free_rate.Value] > self.Time.date():
        rf_rate = self.Securities[self.risk_free_rate].Price / 100
    else:
        return

    if not all(last_update_date[x] > self.Time.date() for x in self.symbols):
        self.Liquidate()
        return

    market_prices:np.ndarray = np.array(self.data[self.symbols[0]])
    oil_prices:np.ndarray = np.array(self.data[self.symbols[1]])
    
    # At least one year of data is ready.
    if len(market_prices)  rf_rate:
        if self.Portfolio[self.cash].Invested:
            self.Liquidate(self.cash)
        
        self.SetHoldings(self.symbols[0], 1)
    else:
        if self.Portfolio[self.symbols[0]].Invested:
            self.Liquidate(self.symbols[0])
        if self.cash in data and data[self.cash]:
            self.SetHoldings(self.cash, 1)
