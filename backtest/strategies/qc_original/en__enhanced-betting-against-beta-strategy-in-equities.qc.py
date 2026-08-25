# Original QuantConnect / library Python
# locale=en slug="enhanced-betting-against-beta-strategy-in-equities"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

import numpy as np
from AlgorithmImports import *
import pandas as pd
from typing import List, Dict
class EnhancedBettingAgainstBetaStrategyEquities(QCAlgorithm):

def Initialize(self):
    self.SetStartDate(2000, 1, 1)
    self.SetCash(100000)
    self.SetSecurityInitializer(lambda x: x.SetMarketPrice(self.GetLastKnownPrice(x)))
    
    # Daily price data.
    self.data:Dict[Symbol, SymbolData] = {}
    
    self.period:int = 4*12*21
    self.beta_period:int = 12*21
    self.leverage:int = 10
    self.quantile:int = 5
    self.beta_thresholds:List[float] = [0.3, 2.]
    self.exchange_codes:List[str] = ['NYS', 'NAS']	
    self.market:Symbol = self.AddEquity('SPY', Resolution.Daily).Symbol
    # Warmup market data.
    self.data[self.market] = SymbolData(self.period)
    history:DataFrame = self.History(self.market, self.period, Resolution.Daily)
    if not history.empty:
        closes:Series = history.loc[self.market].close
        for time, close in closes.items():
            self.data[self.market].update(close)        
        
    self.weight:Dict[Symbol, float] = {}
    
    self.fundamental_count:int = 1000
    self.fundamental_sorting_key = lambda x: x.DollarVolume
    self.selection_flag:bool = True
    self.Settings.MinimumOrderMarginPortfolioPercentage = 0.
    self.UniverseSettings.Resolution = Resolution.Daily
    self.AddUniverse(self.FundamentalSelectionFunction)
    self.Schedule.On(self.DateRules.MonthEnd(self.market), self.TimeRules.AfterMarketOpen(self.market), self.Selection)
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
    selected:List[Fundamental] = [x for x in fundamental if x.HasFundamentalData and x.Market == 'usa' and x.MarketCap != 0 and 
                                  x.SecurityReference.ExchangeId in self.exchange_codes]
    if len(selected) > self.fundamental_count:
        selected = [x for x in sorted(selected, key=self.fundamental_sorting_key, reverse=True)[:self.fundamental_count]]
    # Warmup price rolling windows.
    for stock in selected:
        symbol:Symbol = stock.Symbol
        if symbol in self.data:
            continue
        
        self.data[symbol] = SymbolData(self.period)
        history:DataFrame = self.History(symbol, self.period, Resolution.Daily)
        if history.empty:
            self.Log(f"Not enough data for {symbol} yet.")
            continue
        closes:Series = history.loc[symbol].close
        for time, close in closes.items():
            self.data[symbol].update(close)
        
    stock_data:Dict[Symbol, StockData] = {}
    
    market_closes:np.ndarray = np.array([x for x in self.data[self.market]._price][:self.beta_period])
    market_returns:np.ndarray = (market_closes[1:] - market_closes[:-1]) / market_closes[:-1]
    
    if len(market_returns) != 0:
        for stock in selected:
            symbol:Symbol = stock.Symbol
            
            if not self.data[symbol].is_ready():
                continue
            # Data is ready.
            stock_closes:np.ndarray = np.array([x for x in self.data[symbol]._price][:self.beta_period])
            stock_returns:np.ndarray = (stock_closes[1:] - stock_closes[:-1]) / stock_closes[:-1]
                
            # Manual beta calc.
            cov:np.ndarray = np.cov(market_returns, stock_returns)[0][1]
            market_variance:float = np.std(market_returns) ** 2
            beta:float = cov / market_variance            
                
            if beta >= self.beta_thresholds[0] and beta = self.quantile: 
        # Value weighted return sorting.
        total_market_cap:float = sum([x[1]._market_cap for x in stock_data.items()])
        sorted_by_return:[List[Tuple[Symbol, StockData]]] = sorted(stock_data.items(), key = lambda x: x[1]._performance * (x[1]._market_cap / total_market_cap), reverse = True)
        quintile:int = int(len(sorted_by_return) / self.quantile)
        top_by_ret:List[StockData] = [x for x in sorted_by_return[:quintile]]
        
        sorted_by_beta:[List[Tuple[Symbol, StockData]]] = sorted(top_by_ret, key = lambda x: x[1]._beta, reverse = True)
        
        beta_median:float = np.median([x[1]._beta for x in sorted_by_beta])
        
        low_beta_stocks:List[Tuple[StockData, float]] = [(x, abs(beta_median - x[1]._beta)) for x in sorted_by_beta if x[1]._beta  beta_median]
        
        # Beta diff weighting.
        for i, portfolio in enumerate([low_beta_stocks, high_beta_stocks]):
            total_diff:float = sum(list(map(lambda x: x[1], portfolio)))
            for symbol_data, diff in portfolio:
                self.weight[symbol_data[0]] = ((-1)**i) * (diff / total_diff)
    
    return [x[0] for x in self.weight.items()]
    
def OnData(self, data: Slice) -> None:
    if not self.selection_flag:
        return
    self.selection_flag = False
    
    portfolio:List[PortfolioTarget] = [PortfolioTarget(symbol, w) for symbol, w in self.weight.items() if symbol in data and data[symbol]]
    self.SetHoldings(portfolio, True)
    
    self.weight.clear()
    
def Selection(self) -> None:
    self.selection_flag = True
class StockData():
def __init__(self, beta:float, performance:float, market_cap:float):
    self._beta:float = beta
    self._performance:float = performance
    self._market_cap:float = market_cap
class SymbolData():
def __init__(self, period:int):
    self._price:RollingWindow = RollingWindow[float](period)

def update(self, value:float) -> None:
    self._price.Add(value)

def is_ready(self) -> bool:
    return self._price.IsReady

def performance(self) -> float:
    return (self._price[0] / self._price[self._price.Count - 1] - 1)
# Custom fee model.
class CustomFeeModel(FeeModel):
def GetOrderFee(self, parameters):
    fee = parameters.Security.Price * parameters.Order.AbsoluteQuantity * 0.00005
    return OrderFee(CashAmount(fee, "USD"))
