# Original QuantConnect / library Python
# locale=zh slug="小盘股效应的时机选择-第3版"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

import numpy as np
from AlgorithmImports import *

class TimingtheSmallCapEffect(QCAlgorithm):

def Initialize(self):
    self.SetStartDate(2000, 1, 1)
    self.SetCash(100000)

    self.period = 21
    self.SetWarmUp(self.period, Resolution.DAILY)
    
    self.market = self.AddEquity('SPY', Resolution.Daily).Symbol
    self.data = RollingWindow[float](self.period)   # spy history
    self.historical_volatility = []
    self.min_vol_history_period = 12
    self.was_high_risk_month = False
    
    self.trade_month_count = 0

    data = self.AddEquity("DIA", Resolution.Daily)
    data.SetLeverage(5)
    self.large_cap = data.Symbol
    
    data = self.AddEquity("IWM", Resolution.Daily)
    data.SetLeverage(5)
    self.small_cap = data.Symbol
    
    self.Schedule.On(self.DateRules.MonthEnd(self.market), self.TimeRules.BeforeMarketClose(self.market), self.Rebalance)

def OnData(self, data):
    # store market prices
    if self.market in data and data[self.market]:
        price = data[self.market].Value
        self.data.Add(price)
    
def Rebalance(self):
    if self.IsWarmingUp: return
    if not self.data.IsReady: return

    if self.time.year == 2023 and self.time.month == 8:
        foo=3

    self.trade_month_count += 1
    if self.trade_month_count == 6:
        self.trade_month_count = 0
        self.Liquidate()

    if self.was_high_risk_month:
        self.was_high_risk_month = False
        self.trade_month_count = 0

        # One month after high risk month.
        self.SetHoldings(self.small_cap, 1)
        self.SetHoldings(self.large_cap, -1)            
    
    market_prices = np.array([x for x in self.data])
    market_returns = market_prices[:-1] / market_prices[1:] - 1
    market_volatility = np.std(market_returns) * np.sqrt(252)
    
    self.historical_volatility.append(market_volatility)
    if len(self.historical_volatility) >= self.min_vol_history_period:
        top_quintile = np.percentile(self.historical_volatility[1:], 80)
        
        if market_volatility > top_quintile:
            # one month lag
            self.was_high_risk_month = True
