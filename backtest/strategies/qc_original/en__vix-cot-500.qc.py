# Original QuantConnect / library Python
# locale=en slug="使用vix指数和cot报告进行在标普500市场中的时机选择策"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

from collections import deque
from AlgorithmImports import *
import numpy as np
import data_tools
import pandas as pd
from scipy.optimize import minimize
class MarketTimingSP500withVIXandCOTReport(QCAlgorithm):

def Initialize(self):
    self.SetStartDate(2005, 1, 1)
    self.SetCash(100000)
   
    # Market data.
    data = self.AddData(data_tools.QuantpediaFutures, 'CME_ES1', Resolution.Daily)
    data.SetFeeModel(data_tools.CustomFeeModel())
    data.SetLeverage(10)
    self.symbol = data.Symbol
    
    self.cash = self.AddEquity('BIL', Resolution.Daily).Symbol
    
    # Daily price data.
    self.data = {}
    self.period = 60
    self.data[self.symbol] = RollingWindow[float](self.period)
    self.data[self.cash] = RollingWindow[float](self.period)
    
    # COT data.
    self.cot_symbol = 'QEP'  # S&P500 E-mini COT symbol.
    self.AddData(data_tools.CommitmentsOfTraders, self.cot_symbol, Resolution.Daily)
    
    # Vix data.
    self.vix = self.AddData(CBOE, "VIX", Resolution.Daily).Symbol
    
    # Regression data.
    self.period = 12 * 4    # 1 year worth of weekly data.
    self.regression_data = deque(maxlen = self.period)
    self.Schedule.On(self.DateRules.MonthStart(self.symbol), self.TimeRules.At(0, 0), self.Rebalance)
    
def OnData(self, data):
    # Store daily price data.
    for symbol in self.data:
        symbol_obj = self.Symbol(symbol)
        if symbol_obj in data and data[symbol_obj]:
            price = data[symbol_obj].Value
            self.data[symbol].Add(price)
        
    market_return = None
    cash_return = None
    hedging_pressure = 0
    open_interest = 0
    vix_price = 0
    # Market and cash asset daily data is ready.
    if self.data[self.symbol].IsReady and self.data[self.cash].IsReady:
        market_prices = [x for x in self.data[self.symbol]]
        market_return = market_prices[0] / market_prices[-1] - 1
        
        cash_prices =  [x for x in self.data[self.cash]]
        cash_return = cash_prices[0] / cash_prices[-1] - 1
    # Store COT data every wednesday.
    if self.cot_symbol in data and data[self.cot_symbol]:
        cot_data = self.Securities[self.cot_symbol].GetLastData()
        if cot_data:
            speculator_long_count = cot_data.GetProperty("LARGE_SPECULATOR_LONG")
            speculator_short_count = cot_data.GetProperty("LARGE_SPECULATOR_SHORT")
            commercial_long_count = cot_data.GetProperty("COMMERCIAL_HEDGER_LONG")
            commercial_short_count = cot_data.GetProperty("COMMERCIAL_HEDGER_SHORT")
            trader_long_count = cot_data.GetProperty("SMALL_TRADER_LONG")
            trader_short_count = cot_data.GetProperty("SMALL_TRADER_SHORT")
            
            if commercial_long_count != 0 and commercial_short_count != 0:
                hedging_pressure = commercial_long_count / (commercial_long_count + commercial_long_count)
                
            open_interest = speculator_long_count + speculator_short_count + commercial_long_count + commercial_short_count + trader_long_count+ trader_short_count
                
            if self.vix in data and data[self.vix]:
                vix_price = data[self.vix].Value
    
    if market_return and cash_return and hedging_pressure != 0 and open_interest != 0 and vix_price != 0:
        self.regression_data.append((market_return, cash_return, hedging_pressure, open_interest, vix_price))

def Rebalance(self):
    # Regression data is ready.
    if len(self.regression_data) == self.regression_data.maxlen:
        # check futures and cot data arrival
        if any([self.securities[symbol].get_last_data() and self.time.date() > data_tools.LastDateHandler.get_last_update_date()[symbol] for symbol in [self.symbol, self.cot_symbol]]):
            self.liquidate()
            return
            
        # Linear regression calc.
        market_returns = [x[0] for x in self.regression_data]
        cash_returns = [x[1] for x in self.regression_data]
        hedging_pressures = [x[2] for x in self.regression_data]
        open_interests = [x[3] for x in self.regression_data]
        vix_prices = [x[4] for x in self.regression_data]
        
        x = [hedging_pressures[:-1], open_interests[:-1], vix_prices[:-1]]
        regression_model = data_tools.MultipleLinearRegresion(x, market_returns[1:])
        market_return_predicted = regression_model.predict([hedging_pressures[-1], open_interests[-1], vix_prices[-1]]) # returns list.
        
        x = [hedging_pressures[:-1], open_interests[:-1], vix_prices[:-1]]
        regression_model = data_tools.MultipleLinearRegresion(x, cash_returns[1:])
        cash_return_predicted = regression_model.predict([hedging_pressures[-1], open_interests[-1], vix_prices[-1]]) # returns list.
        
        # Create return df.
        returns = {
            self.symbol.Value : market_returns + market_return_predicted,
            self.cash.Value : cash_returns + cash_return_predicted
        }
        returns = pd.DataFrame(returns, columns=returns.keys()).dropna()
        
        # The optimization method processes the data frame
        opt, weights = self.optimization_method(returns)
        
        for symbol in [self.symbol, self.cash]:
            w = weights[symbol.Value]
            if w > 0.001:
                self.SetHoldings(symbol, w)
def optimization_method(self, returns):
    '''Minimum variance optimization method'''
    # Objective function
    fun = lambda weights: np.dot(weights.T, np.dot(returns.cov(), weights))
    # Constraint #1: The weights can be negative, which means investors can short a security.
    constraints = [{'type': 'eq', 'fun': lambda w: np.sum(w) - 1}]
    # Constraint #2: Portfolio targets a given return
    # constraints.append({'type': 'eq', 'fun': lambda weights: np.dot(np.matrix(returns.mean()), np.matrix(weights).T).item() - self.target_return})
    size = returns.columns.size
    x0 = np.array(size * [1. / size])
    # bounds = tuple((self.minimum_weight, self.maximum_weight) for x in range(size))
    bounds = tuple((0, 1) for x in range(size))
    opt = minimize(fun,                         # Objective function
                   x0,                          # Initial guess
                   method='SLSQP',              # Optimization method:  Sequential Least SQuares Programming
                   bounds = bounds,             # Bounds for variables 
                   constraints = constraints)   # Constraints definition
    return opt, pd.Series(opt['x'], index = returns.columns)
class QuandlVix(PythonQuandl):
def __init__(self):
    self.ValueColumnName = "close"
