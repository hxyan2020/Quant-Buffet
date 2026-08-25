# Original QuantConnect / library Python
# locale=zh slug="在股票中在价值和动量之间切换"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

from math import isnan
import pandas as pd
import numpy as np
from scipy.optimize import minimize
from AlgorithmImports import *
class SwitchingbetweenValueMomentum(QCAlgorithm):
def Initialize(self):
    self.SetStartDate(2010, 1, 1)
    self.SetCash(100000)
    self.data:Dict[Symbol, SymbolData] = {}
    self.period:int = 36 * 21
    self.leverage:int = 5
    self.quantile:int = 10
    self.symbol:Symbol = self.AddEquity('IEF', Resolution.Daily).Symbol
    self.data[self.symbol] = SymbolData(self, self.symbol, self.period) # T-note prices
    
    self.portfolio_symbols:Set[Symbol] = set() # Selected sorted symbols
    self.fundamental_count:int = 200
    self.fundamental_sorting_key = lambda x: x.DollarVolume
    self.selection_flag:bool = False
    self.UniverseSettings.Resolution = Resolution.Daily
    self.AddUniverse(self.FundamentalSelectionFunction)
    self.Settings.MinimumOrderMarginPortfolioPercentage = 0.
    self.Schedule.On(self.DateRules.MonthEnd(self.symbol), self.TimeRules.AfterMarketOpen(self.symbol), self.Selection)
    self.settings.daily_precise_end_time = False
def OnSecuritiesChanged(self, changes: SecurityChanges) -> None:
    for security in changes.AddedSecurities:
        security.SetFeeModel(CustomFeeModel())
        security.SetLeverage(self.leverage)
        
def FundamentalSelectionFunction(self, fundamental: List[Fundamental]) -> List[Symbol]:
    # Update the rolling window every day.
    for stock in fundamental:
        symbol:Symbol = stock.Symbol
        
        # Store monthly price.
        if symbol in self.data:
            self.data[symbol].update(stock.AdjustedPrice)
    if not self.selection_flag:
        return Universe.Unchanged
    selected:List[Fundamental] = [x for x in fundamental if x.HasFundamentalData and x.Market == 'usa' and \
        not isnan(x.ValuationRatios.PERatio) and x.ValuationRatios.PERatio != 0
    ]
    if len(selected) > self.fundamental_count:
        selected = [x for x in sorted(selected, key=self.fundamental_sorting_key, reverse=True)[:self.fundamental_count]]
    ep:Dict[Symbol, float] = {}
    performance:Dict[Symbol, float] = {}
    # Warmup price rolling windows.
    for stock in selected:
        symbol:Symbol = stock.Symbol
        if symbol not in self.data:
            self.data[symbol] = SymbolData(self, symbol, self.period)
        
        if self.data[symbol].is_ready():
            ep[symbol] = (1 / stock.ValuationRatios.PERatio)
            performance[symbol] = self.data[symbol].performance()
    
    if len(ep) >= self.quantile:
        # Sorting by return and EP.
        sorted_by_ret:List = sorted(performance.items(), key = lambda x: x[1], reverse = True)
        quantile:int = int(len(sorted_by_ret) / self.quantile)
        high_by_ret:List[Symbol] = [x[0] for x in sorted_by_ret[:quantile]]
        
        sorted_by_ep:List = sorted(ep.items(), key = lambda x: x[1], reverse = True)
        quantile = int(len(sorted_by_ep) / self.quantile)
        high_by_ep:List[Symbol] = [x[0] for x in sorted_by_ep[:quantile]]
        
        self.portfolio_symbols = set(high_by_ret + high_by_ep)   # portfolios with no duplication
    
    return list(self.portfolio_symbols)
def OnData(self, data: Slice) -> None:
    if not self.selection_flag:
        return
    self.selection_flag = False
    
    self.Liquidate()
    
    if len(self.portfolio_symbols) == 0: return

    # Optimalization.
    data:Dict = { symbol : [x for x in self.data[symbol].Price] for symbol in self.portfolio_symbols if symbol in data and data[symbol]}
    data[self.symbol] = [x for x in self.data[self.symbol].Price]
    df_price = pd.DataFrame(data, columns=data.keys()) 
    daily_return = (df_price / df_price.shift(1)).dropna()
    a = PortfolioOptimization(daily_return, 0, len(data))
    opt_weight = a.opt_portfolio()
    
    if isnan(sum(opt_weight)): return
    for i in range(len(data)):
        w = opt_weight[i]
        if w >= 0.001:
            self.SetHoldings(df_price.columns[i], w)
def Selection(self) -> None:
    if not self.data[self.symbol].is_ready(): return
    self.selection_flag = True
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
    return - self.annual_port_return(weights) / self.annual_port_vol(weights)
    
    # method 2: maximize the return with target volatility
    # return - self.annual_port_return(weights) / self.target_vol
    # method 3: minimize variance with target volatility
    # return (1 / self.annual_port_vol(weights)) / self.target_vol
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
    
    #opt_sharpe = - opt['fun']
    #opt_weights = opt['x']
    #opt_return = self.annual_port_return(opt_weights)
    #opt_volatility = self.annual_port_vol(opt_weights)
    
    return opt_weights
    
class SymbolData():
def __init__(self, algorithm, symbol, period):
    self.Symbol = symbol
    self.Price = RollingWindow[float](period)
    self.Algorithm = algorithm
    
    # Warmup.
    history = algorithm.History(algorithm.Symbol(symbol), period, Resolution.Daily)
    if not history.empty:
        closes = history.loc[symbol].close
        for time, close in closes.items():
            self.Price.Add(close)
        
def update(self, value):
    self.Price.Add(value)

def is_ready(self) -> bool:
    return self.Price.IsReady

# performance t12-t6.
def performance(self) -> float:
    closes = [x for x in self.Price][:12*21][-6*21:]
    return (closes[0] / closes[-1] - 1)
# Custom fee model.
class CustomFeeModel(FeeModel):
def GetOrderFee(self, parameters):
    fee = parameters.Security.Price * parameters.Order.AbsoluteQuantity * 0.00005
    return OrderFee(CashAmount(fee, "USD"))
