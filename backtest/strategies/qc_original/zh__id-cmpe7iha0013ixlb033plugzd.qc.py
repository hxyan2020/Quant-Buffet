# Original QuantConnect / library Python
# locale=zh slug="股息风险溢价策略"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

from AlgorithmImports import *
from scipy import stats
import numpy as np
#endregion
class DividendRiskPremiumStrategy(QCAlgorithm):
def Initialize(self):
    self.SetStartDate(2010, 1, 1)
    self.SetCash(100000)
    
    self.dividend_futures = ['FEXD1', 'FEXD2', 'FEXD3']
    
    self.fexd1 = None
    for i, div_symbol in enumerate(self.dividend_futures):
        data = self.AddData(QuantpediaFutures, div_symbol, Resolution.Daily)
        data.SetLeverage(10)
        data.SetFeeModel(CustomFeeModel())
        
        # store nearby contract
        if i == 0:
            self.fexd1 = data.Symbol
    
    # STOXX 50 future
    data = self.AddData(QuantpediaFutures, "EUREX_FSTX1", Resolution.Daily)
    data.SetLeverage(10)
    data.SetFeeModel(CustomFeeModel())
    self.SX5E = data.Symbol
    
    # daily price
    self.data = {}
    self.period = 10
    self.max_missing_days = 5
    for symbol in [self.fexd1, self.SX5E]:
        self.data[symbol] = RollingWindow[float](self.period)
    
    self.selection_flag = False
    self.recent_month:int = -1

def OnData(self, data):
    # store daily prices
    if self.fexd1 in data and data[self.fexd1] and self.SX5E in data and data[self.SX5E]:
        self.data[self.fexd1].Add(data[self.fexd1].Value)
        self.data[self.SX5E].Add(data[self.SX5E].Value)
    else:
        if (self.Securities[self.fexd1].GetLastData() and (self.Time.date() - self.Securities[self.fexd1].GetLastData().Time.date()).days > self.max_missing_days) or \
            (self.Securities[self.SX5E].GetLastData() and (self.Time.date() - self.Securities[self.SX5E].GetLastData().Time.date()).days > self.max_missing_days):
            self.data[self.fexd1].Reset()
            self.data[self.SX5E].Reset()
            self.Liquidate()
    if self.recent_month == self.Time.month:
        return
    self.recent_month = self.Time.month
    if self.Time.month in [7, 1]:
        self.Liquidate()
        self.weights = [1, 0]   # divident future #2 and #3 weights
        self.selection_flag = True
    
    if self.Portfolio.Invested or self.selection_flag:
        if self.data[self.fexd1].IsReady and self.data[self.SX5E].IsReady:
            dividend_future_prices = np.array([x for x in self.data[self.fexd1]])
            market_prices = np.array([x for x in self.data[self.SX5E]])
            
            dividend_future_returns = dividend_future_prices[:-1] / dividend_future_prices[1:] - 1
            market_returns = market_prices[:-1] / market_prices[1:] - 1
            if not all(x==0 for x in dividend_future_returns):
                slope, intercept, r_value, p_value, std_err = stats.linregress(market_returns, dividend_future_returns)
                
                # dividend futures exposure
                self.SetHoldings(self.dividend_futures[1], self.weights[0])
                self.SetHoldings(self.dividend_futures[2], self.weights[1])
                
                # adjust weights every invested day
                if self.weights[0] >= 0.008:
                    self.weights[0] -= 0.008
                
                if self.weights[0]
