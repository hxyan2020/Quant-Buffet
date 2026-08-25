# Original QuantConnect / library Python
# locale=zh slug="危机阿尔法投资组合"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

import numpy as np
from AlgorithmImports import *
class TheCrisisAlphaPortfolio(QCAlgorithm):
def Initialize(self):
    self.SetStartDate(2008, 1, 1)
    self.SetCash(100000)
    self.symbols = ['TLT', 'IEF', 'IEI', 'SHY']
    self.treasuries_1year = 'BIL'
    
    period = 10
    self.SetWarmUp(period)
    
    # Monthly etf price.
    self.data = {}
    
    for symbol in self.symbols + [self.treasuries_1year]:
        data = self.AddEquity(symbol, Resolution.Daily)
        self.data[symbol] = SymbolData(symbol, period)
    
    self.last_month = -1
    self.Schedule.On(self.DateRules.MonthStart(self.symbols[0]), self.TimeRules.At(0, 0), self.Rebalance)

def OnData(self, data):
    if self.last_month == self.Time.month: return
    self.last_month = self.Time.month
    # Store monthly prices.
    for symbol in self.symbols + [self.treasuries_1year]:
        symbol_obj = self.Symbol(symbol)
        if symbol_obj in data.Keys:
            if data[symbol_obj]:
                price = data[symbol_obj].Value
                if price != 0:
                    self.data[symbol].update(price)
    
def Rebalance(self):
    self.Liquidate()
    
    # Etfs with positive momentum. - symbol -> (performance, volatility)
    positive_mom = {x : (self.data[x].performance(), self.data[x].volatility()) for x in self.symbols if self.data[x].is_ready() and self.data[x].performance() > 0}

    if not self.data[self.treasuries_1year].is_ready(): return
    if len(positive_mom) > 0:
        bil_ret = self.data[self.treasuries_1year].performance()
        
        rank = {}
        for symbol, perf_volatility in positive_mom.items():
            excess_ret = perf_volatility[0] - bil_ret
            variance = perf_volatility[1] ** 2
            rank[symbol] = excess_ret / variance
        
        sorted_by_rank = [x[0] for x in sorted(rank.items(), key = lambda x: x[1], reverse = True)]
        
        rank_len = len(sorted_by_rank)
        total_score = sum(range(0, rank_len + 1))
        
        rank_index = rank_len
        for symbol in sorted_by_rank:
            weight = (1 / total_score) * rank_index
            self.SetHoldings(symbol, weight)
            rank_index -= 1
    else:
        self.SetHoldings(self.treasuries_1year, 1)
        
class SymbolData():
def __init__(self, symbol, period):
    self.Symbol = symbol
    self.Price = RollingWindow[float](period)

def update(self, value):
    self.Price.Add(value)

def is_ready(self) -> bool:
    return self.Price.IsReady
    
def performance(self, values_to_skip = 0) -> float:
    closes = [x for x in self.Price][values_to_skip:]
    return (closes[0] / closes[-1] - 1)

def volatility(self):
    prices = np.array([x for x in self.Price])
    daily_returns = prices[:-1] / prices[1:] - 1
    return np.std(daily_returns)
