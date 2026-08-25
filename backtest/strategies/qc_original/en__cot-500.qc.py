# Original QuantConnect / library Python
# locale=en slug="使用cot报告对商品和标普500进行时机选择"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

from collections import deque
from AlgorithmImports import *
import numpy as np
import data_tools
import pandas as pd
from scipy.optimize import minimize
class TimingCommoditiesandSP500withCOTReport(QCAlgorithm):

def Initialize(self):
    self.SetStartDate(2005, 1, 1)
    self.SetCash(100000)
   
    # Future symbol with COT symbol.
    self.symbols = {
        'CME_ES1' : 'QEP',
        'CME_HG1' : 'QHG',
        'CME_CL1' : 'QCL'
    }

    # Daily price data.
    self.data = {}
    self.period = 60
    for symbol, cot_symbol in self.symbols.items():
        # Futures data.
        data = self.AddData(data_tools.QuantpediaFutures, symbol, Resolution.Daily)
        data.SetFeeModel(data_tools.CustomFeeModel())
        data.SetLeverage(10)
        
        self.symbol = data.Symbol
        self.data[symbol] = SymbolData(symbol,self.period)
    
        # COT data.
        self.AddData(data_tools.CommitmentsOfTraders, cot_symbol, Resolution.Daily)
    # Cash asset.
    self.cash = self.AddEquity('BIL', Resolution.Daily).Symbol
    self.data[self.cash.Value] = SymbolData(self.cash.Value, self.period)
    
    # Regression data.
    self.period = 12 * 4    # 1 year worth of weekly data.
    self.regression_data = deque(maxlen = self.period)
    
def OnData(self, data):
    # Store daily price data.
    for symbol in self.data:
        symbol_obj = self.Symbol(symbol)
        if symbol_obj in data and data[symbol_obj]:
            price = data[symbol_obj].Value
            self.data[symbol].update(price)
        
    copper_hedging_pressure = 0
    oil_hedging_pressure = 0
    
    market_commercial_hedging_pressure = 0
    market_nonreportable_hedging_pressure = 0
    
    # Copper and oil COT data.
    for cot_symbol in ['QHG', 'QCL']:
        # Store COT data every wednesday.
        if cot_symbol in data and data[cot_symbol]:
            cot_data = self.Securities[cot_symbol].GetLastData()
            if cot_data:
                speculator_long_count = cot_data.GetProperty("LARGE_SPECULATOR_LONG")
                speculator_short_count = cot_data.GetProperty("LARGE_SPECULATOR_SHORT")
                if speculator_long_count != 0 and speculator_short_count != 0:
                    hedging_pressure = speculator_long_count / (speculator_long_count + speculator_short_count)
                    
                    if cot_symbol == 'QHG':
                        copper_hedging_pressure = hedging_pressure
                    elif cot_symbol == 'QCL':
                        oil_hedging_pressure = hedging_pressure
    
    # Market COT data.
    cot_symbol = 'QEP'
    if cot_symbol in data and data[cot_symbol]:
        cot_data = self.Securities[cot_symbol].GetLastData()
        if cot_data:
            # Commercial hedging pressure.
            commercial_long_count = cot_data.GetProperty("COMMERCIAL_HEDGER_LONG")
            commercial_short_count = cot_data.GetProperty("COMMERCIAL_HEDGER_SHORT")
            if commercial_long_count != 0 and commercial_short_count != 0:
                market_commercial_hedging_pressure = commercial_long_count / (commercial_long_count + commercial_short_count)
            # Non-reportable hedging pressure.
            trader_long_count = cot_data.GetProperty("SMALL_TRADER_LONG")
            trader_short_count = cot_data.GetProperty("SMALL_TRADER_SHORT")                            
            if trader_long_count != 0 and trader_short_count != 0:
                market_nonreportable_hedging_pressure = trader_long_count / (trader_long_count + trader_short_count)
                
    returns = { x: self.data[x].performance() for x in self.data if self.data[x].is_ready() }
    # Store regression data.
    if len(returns) == len(self.data) and copper_hedging_pressure != 0 and oil_hedging_pressure != 0 and market_commercial_hedging_pressure != 0 and market_nonreportable_hedging_pressure != 0:
        asset_returns = [ret for symbol, ret in returns.items()]
        self.regression_data.append((asset_returns[0], asset_returns[1], asset_returns[2], asset_returns[3], copper_hedging_pressure, oil_hedging_pressure, market_commercial_hedging_pressure, market_nonreportable_hedging_pressure))

    # Regression data is ready.
    if len(self.regression_data) == self.regression_data.maxlen:
        
        # check futures and cot data arrival
        for symbol, cot_symbol in self.symbols.items():
            if any([self.securities[x].get_last_data() and self.time.date() > data_tools.LastDateHandler.get_last_update_date()[x] for x in [symbol, cot_symbol]]):
                self.liquidate()
                return

        returns = {}
        for index in range(4):
            symbol = [x for x in self.data.keys()][index]
            # Linear regression calc.
            asset_returns = [x[index] for x in self.regression_data]
            
            copper_hedging_pressures = [x[4] for x in self.regression_data]
            oil_hedging_pressures = [x[5] for x in self.regression_data]
            market_commercial_hedging_pressures = [x[6] for x in self.regression_data]
            market_nonreportable_hedging_pressures = [x[7] for x in self.regression_data]
            
            x = [copper_hedging_pressures[:-1], oil_hedging_pressures[:-1], market_commercial_hedging_pressures[:-1], market_nonreportable_hedging_pressures[:-1]]
            regression_model = data_tools.MultipleLinearRegression(x, asset_returns[1:])
            
            alpha = regression_model.params[0]
            pred_x = [copper_hedging_pressures[-1], oil_hedging_pressures[-1], market_commercial_hedging_pressures[-1], market_nonreportable_hedging_pressures[-1]]
            betas = np.array(regression_model.params[1:])
            return_predicted = alpha + sum(np.multiply(betas, pred_x))
            
            returns[symbol] = asset_returns + [return_predicted]
        
        if len(returns) > 0:
            returns = pd.DataFrame(returns, columns=returns.keys()).dropna()
            
            # The optimization method processes the data frame.
            opt, weights = self.optimization_method(returns)
            
            for symbol in returns.keys():
                w = weights[symbol]
                if w >= 0.001:
                    self.SetHoldings(symbol, w)
        else:
            self.Liquidate()
def optimization_method(self, returns):
    # '''Minimum variance optimization method'''
    # # Objective function
    # fun = lambda weights: np.dot(weights.T, np.dot(returns.cov(), weights))
    '''Maximum Sharpe Ratio optimization method'''
    # Objective function
    fun = lambda weights: -self.sharpe_ratio(returns, weights)
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
    
def sharpe_ratio(self, returns, weights):
    annual_return = np.dot(np.matrix(returns.mean()), np.matrix(weights).T).item()
    annual_volatility = np.sqrt(np.dot(weights.T, np.dot(returns.cov(), weights)))
    return annual_return/annual_volatility        
class QuandlVix(PythonQuandl):
def __init__(self):
    self.ValueColumnName = "VIX Close"
    
class SymbolData():
def __init__(self, symbol, period):
    self.Symbol = symbol
    self.Price = RollingWindow[float](period)

def is_ready(self):
    return self.Price.IsReady

def update(self, close):
    self.Price.Add(close)
    
def performance(self):
    closes = [x for x in self.Price]
    return (closes[0] / closes[-1] - 1)
