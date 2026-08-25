# Original QuantConnect / library Python
# locale=en slug="volatility-weighted-short-term-reversal-strategy-in-emerging-market-equities"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

from AlgorithmImports import *
import numpy as np
from collections import deque
class VolatilityWeightedShortTermReversal(QCAlgorithm):
def Initialize(self):
    self.SetStartDate(2012, 1, 1)
    self.SetCash(100000)
    
    self.tickers:List[str] = ['FXI', 'EWH', 'EWT', 'EIDO', 'EPHE', 'EWM', 'THD', 'EWS', 'TUR', 'EWZ', 'ARGT', 'ECH', 'EPOL']
                    
    self.daily_period:int = 21
    self.monthly_period:int = 3
    self.data:Dict[Symbol, SymbolData] = { self.AddEquity(ticker, Resolution.Daily).Symbol : SymbolData(self.daily_period, self.monthly_period) for ticker in self.tickers }
    self.recent_month:int = -1

def OnData(self, data: Slice) -> None:
    rebalance_flag:bool = False
    volatility:Dict[Symbol, float] = {}
    # update daily price
    for symbol, symbol_data in self.data.items():
        if symbol in data and data[symbol]:
            # set rebalance flag once a month
            if self.recent_month != self.Time.month:
                rebalance_flag = True
                self.recent_month = self.Time.month
            price:float = data[symbol].Value
            symbol_data.update_price(price)
            if rebalance_flag:
                if symbol_data.prices_are_ready():
                    performance:float = symbol_data.performance()
                    symbol_data.update_perf(performance)
    
                    if symbol_data.returns_are_ready():
                        # current month realized return is below the 3-month average
                        if performance  None:
    self._prices:RollingWindow = RollingWindow[float](period)
    self._returns:RollingWindow = RollingWindow[float](month_period)

def prices_are_ready(self) -> bool:
    return self._prices.IsReady

def returns_are_ready(self) -> bool:
    return self._returns.IsReady

def performance(self) -> float:
    return self._prices[0] / self._prices[self._prices.Count - 1] - 1

def update_price(self, price:float) -> None:
    self._prices.Add(price)
def update_perf(self, perf:float) -> None:
    self._returns.Add(perf)
    
def volatility(self) -> float:
    prices:np.ndarray = np.array([x for x in self._prices])
    returns:np.ndarray = prices[:-1] / prices[1:] - 1
    return np.std(returns)

def monthly_avg(self) -> float:
    return np.mean(list(self._returns))
