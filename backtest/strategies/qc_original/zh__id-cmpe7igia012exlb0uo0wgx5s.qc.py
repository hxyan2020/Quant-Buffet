# Original QuantConnect / library Python
# locale=zh slug="自适应资产配置"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

from AlgorithmImports import *
# The investment universe consists of 10 ETFs which are proxy for the main asset classes (US Stocks, European Stocks, Japanese Stocks, EM Stocks, US REITs, 
# International REITs, US Intermediate Treasuries, US Long-term Treasuries, Commodities, and Gold). Each week, the asset classes are sorted based on their 
# 6-month momentum. Only the top 5 assets are then used in the next step, when the investor uses the minimum variance calculation to compute the weights 
# for each asset class for the next week. 60-day historical volatilities and correlations are used in the minimum variance computation. The overall portfolio
# volatility prediction is then estimated (based on the weights from the min. variance algorithm and on historical volatilities and correlations) 
# and the portfolio is rescaled to target 8% volatility. These steps are performed every week and the portfolio is rebalanced accordingly.
import pandas as pd
import numpy as np
from scipy.optimize import minimize
class AdaptiveAssetAllocation(QCAlgorithm):
def Initialize(self):
    self.SetStartDate(2008, 1, 1)
    self.SetCash(100000)
    self.symbols = ['SPY', 'VGK', 'EWJ', 'EEM', 'VNQ', 'RWX', 'IEI', 'IEF', 'DBC', 'GLD']
    self.period = 6 * 21
    self.data = {}
    
    for symbol in self.symbols:
        self.AddEquity(symbol, Resolution.Daily)
        self.data[symbol] = SymbolData(self.period)
    self.Schedule.On(self.DateRules.WeekStart(self.symbols[0]), self.TimeRules.AfterMarketOpen(self.symbols[0]), self.Rebalance)
def OnData(self, data):
    for symbol in self.data:
        symbol_obj = self.Symbol(symbol)
        if symbol_obj in data and data[symbol_obj]:
            self.data[symbol].update(data[symbol_obj].Value)
    
def Rebalance(self):
    self.Liquidate()
    
    ret_data = { x : self.data[x].performance() for x in self.symbols if self.data[x].is_ready()}
    # Performance sorting.
    if len(ret_data) == 0: return
    sorted_by_ret = sorted(ret_data.items(), key = lambda x: x[1], reverse = True)
    top_symbols = [x[0] for x in sorted_by_ret[:5]]
    
    # Optimalization
    data = {}
    for symbol in top_symbols:
        closes = [x for x in self.data[symbol].price]
        data[symbol] = closes[:60]
        
    df_price = pd.DataFrame(data, columns=data.keys()) 
    daily_return = (df_price / df_price.shift(1)).dropna()
    a = PortfolioOptimization(daily_return, 0, len(data))
    opt_weight = a.opt_portfolio()
    
    for i in range(len(data)):
        # Weight is higher than minumum QC supported weight.
        if opt_weight[i] > 0.001:
            self.SetHoldings(df_price.columns[i], opt_weight[i])
    
class PortfolioOptimization(object):
def __init__(self, df_return, risk_free_rate, num_assets):
    self.daily_return = df_return
    self.risk_free_rate = risk_free_rate
    self.n = num_assets # numbers of risk assets in portfolio
    self.target_vol = 0.08
def annual_port_return(self, weights):
    # calculate the annual return of portfolio
    return np.sum(self.daily_return.mean() * weights) * 252
def annual_port_vol(self, weights):
    # calculate the annual volatility of portfolio
    return np.sqrt(np.dot(weights.T, np.dot(self.daily_return.cov() * 252, weights)))
def min_func(self, weights):
    # method 1: maximize sharp ratio
    #return - self.annual_port_return(weights) / self.annual_port_vol(weights)
    
    # method 2: maximize the return with target volatility
    # return - self.annual_port_return(weights) / self.target_vol
    # method 3: minimize variance with target volatility
    return (1 / self.annual_port_vol(weights)) / self.target_vol
def opt_portfolio(self):
    # maximize the sharpe ratio to find the optimal weights
    cons = ({'type': 'eq', 'fun': lambda x: np.sum(x) - 1})
    bnds = tuple((0, 1) for x in range(2)) + tuple((0, 0.25) for x in range(self.n - 2))
    opt = minimize(self.min_func,                               # object function
                   np.array(self.n * [1. / self.n]),            # initial value
                   method='SLSQP',                              # optimization method
                   bounds=bnds,                                 # bounds for variables 
                   constraints=cons)                            # constraint conditions
                  
    opt_weights = opt['x']
 
    return opt_weights
class SymbolData():
def __init__(self, period):
    self.price = RollingWindow[float](period)
    
def update(self, value):
    self.price.Add(value)

def is_ready(self) -> bool:
    return self.price.IsReady
    
def performance(self, values_to_skip = 0) -> float:
    closes = [x for x in self.price][values_to_skip:]
    return (closes[0] / closes[-1] - 1)
