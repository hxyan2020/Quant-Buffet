# Original QuantConnect / library Python
# locale=en slug="the-conservative-formula"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

import numpy as np
from AlgorithmImports import *
from typing import List, Dict
from numpy import isnan
class TheConservativeFormula(QCAlgorithm):
def Initialize(self):
    self.SetStartDate(2000, 1, 1)
    self.SetCash(100000)
    self.period:int = 36 * 21
    self.leverage:int = 10
    self.quantile:int = 5
    self.long:List[Symbol] = []
    self.data:Dict[Symbol, SymbolData] = {}
    
    market:Symbol = self.AddEquity('SPY', Resolution.Daily).Symbol
    
    self.fundamental_count:int = 500
    self.fundamental_sorting_key = lambda x: x.DollarVolume
    self.selection_flag:bool = False
    self.Settings.MinimumOrderMarginPortfolioPercentage = 0.
    self.UniverseSettings.Resolution = Resolution.Daily
    self.AddUniverse(self.FundamentalSelectionFunction)
    self.Schedule.On(self.DateRules.MonthStart(market), self.TimeRules.AfterMarketOpen(market), self.Selection)
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
                              not isnan(x.ValuationRatios.TotalYield) and (x.ValuationRatios.TotalYield > 0)]
    
    # Warmup price rolling windows.
    for stock in selected:
        symbol:Symbol = stock.Symbol
        if symbol in self.data:
            continue
        
        self.data[symbol] = SymbolData(self.period)
        history = self.History(symbol, self.period, Resolution.Daily)
        if history.empty:
            self.Log(f"Not enough data for {symbol} yet.")
            continue
        closes = history.loc[symbol].close
        for time, close in closes.items():
            self.data[symbol].update(close)
        
    yield_performance_volatility:Dict[Symbol, (Tuple[float])] = { x.Symbol : (x.ValuationRatios.TotalYield , self.data[x.Symbol].performance(), self.data[x.Symbol].volatility()) for x in selected if self.data[x.Symbol].is_ready()}
    
    # Volatility sorting.
    if len(yield_performance_volatility) = self.quantile:
        sorted_by_rank:List[Tuple[Symbol, float]] = sorted(rank.items(), key = lambda x: x[1], reverse = True)
        quintile:int = int(len(sorted_by_rank) / self.quantile)
    
        self.long:List[Symbol] = [x[0] for x in sorted_by_rank[:quintile]]
    
    return self.long
def OnData(self, data: Slice) -> None:
    if not self.selection_flag: 
        return
    self.selection_flag = False
    
    # Trade execution
    portfolio:List[PortfolioTarget] = [PortfolioTarget(symbol, 1 / len(self.long)) for symbol in self.long if symbol in data and data[symbol]]
    self.SetHoldings(portfolio, True)
    self.long.clear()
def Selection(self) -> None:
    if self.Time.month % 3 == 0:
        self.selection_flag = True
class SymbolData():
def __init__(self, period:int):
    self._price:RollingWindow = RollingWindow[float](period)

def update(self, price:float) -> None:
    self._price.Add(price)

def is_ready(self) -> bool:
    return self._price.IsReady
    
def performance(self, values_to_skip = 0) -> float:
    closes:List[float] = [x for x in self._price][:12*21][values_to_skip:]
    return (closes[0] / closes[-1] - 1)                

def volatility(self) -> float:
    closes:np.ndarray = np.array([x for x in self._price])
    returns:np.ndarray = (closes[:-1] / closes[1:]) - 1
    return np.std(returns)
    
# Custom fee model.
class CustomFeeModel(FeeModel):
def GetOrderFee(self, parameters):
    fee = parameters.Security.Price * parameters.Order.AbsoluteQuantity * 0.00005
    return OrderFee(CashAmount(fee, "USD"))
