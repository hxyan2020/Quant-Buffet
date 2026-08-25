# Original QuantConnect / library Python
# locale=en slug="commodities-timing-based-on-a-monetary-conditions"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

from math import isnan
from AlgorithmImports import *
import pandas as pd
import numpy as np
from scipy.optimize import minimize
class CommoditiesTimingbasedonaMonetaryConditions(QCAlgorithm):
def Initialize(self):
    self.SetStartDate(2004, 1, 1)
    self.SetCash(100000)
    
    self.data = {}  # daily closes
    period = 12 * 21
    self.SetWarmUp(period)
    
    self.symbols = ["SPY", "EFA", "IEF", "LQD"]
    self.commodities = ["DBC"]
    for symbol in self.symbols + self.commodities:
        self.AddEquity(symbol, Resolution.Daily)
        self.data[symbol] = RollingWindow[float](period)
    # changes in FED policy from restrictive to expansive
    dates_str = ["24.08.1999", "03.01.2001", "30.06.2004", "18.09.2007", "14.12.2016", "31.7.2019"]
    self.dates = [datetime.strptime(x, "%d.%m.%Y").date() for x in dates_str] # datetime type
    
    # import quandl federal rate data
    self.target_rate = self.AddData(QuandlValue, 'FRED/DFEDTARU', Resolution.Daily).Symbol
    self.restrictive_flag = True    # from start of the algorithm
    self.last_target_rate = None
    self.external_restrictive_flag = None
    self.recent_month = -1
def OnData(self, data):
    if self.target_rate in data and data[self.target_rate]:
        curr_target_rate = data[self.target_rate].Value
        
        restrictive_flag = None
        
        # switch to external data source, when self.dates ends
        if self.Time.date() > self.dates[-1]:
            if self.last_target_rate:
                if curr_target_rate > self.last_target_rate:
                    restrictive_flag = True
                elif curr_target_rate  5:
            self.Liquidate()
            return
    else:
        restrictive_flag = self.restrictive_flag
    symbols = [x for x in self.symbols]
    
    if restrictive_flag:
        symbols += self.commodities
    # construct dataframe
    data = {}
    for symbol in symbols:
        if self.data[symbol].IsReady:
            data[symbol] = [x for x in self.data[symbol]][::-1]
            
    if len(data) != 0:
        df_price = pd.DataFrame(data,columns=data.keys()) 
        daily_return = (df_price / df_price.shift(1) - 1).dropna()
        a = PortfolioOptimization(daily_return, 0, len(data))
        opt_weight = a.opt_portfolio()
        
        if isnan(sum(opt_weight)): return
        
        for i in range(len(data)):
            if opt_weight[i] >= 0.001:
                self.SetHoldings(df_price.columns[i], opt_weight[i])
    else:
        if self.Portfolio.Invested:
            self.Liquidate()
        
class PortfolioOptimization(object):
def __init__(self, df_return, risk_free_rate, num_assets):
    self.daily_return = df_return
    self.risk_free_rate = risk_free_rate
    self.n = num_assets # numbers of risk assets in portfolio
    self.target_vol = 0.05
def annual_port_return(self, weights):
    # calculate the annual return of portfolio
    return np.sum(self.daily_return.mean() * weights) * 252
def annual_port_vol(self, weights):
    # calculate the annual volatility of portfolio
    return np.sqrt(np.dot(weights.T, np.dot(self.daily_return.cov() * 252, weights)))
def min_func(self, weights):
    # method 1: maximize sharp ratio
    return - self.annual_port_return(weights) / self.annual_port_vol(weights)
    
    # method 2: maximize the return with target volatility
    #return - self.annual_port_return(weights) / self.target_vol
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
# Quandl "value" data
class QuandlValue(PythonQuandl):
def __init__(self):
    self.ValueColumnName = 'Value'
