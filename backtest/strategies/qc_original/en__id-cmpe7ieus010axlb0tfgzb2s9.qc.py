# Original QuantConnect / library Python
# locale=en slug="价值因子策略-账面市值比"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

from AlgorithmImports import *
import numpy as np
from typing import List

class MarketBookValueFactor(QCAlgorithm):

def Initialize(self):
    self.SetStartDate(2000, 1, 1)
    self.SetCash(100000)

    self.UniverseSettings.Leverage = 5
    self.UniverseSettings.Resolution = Resolution.Daily
    self.AddUniverse(self.CoarseSelectionFunction)
    self.Settings.MinimumOrderMarginPortfolioPercentage = 0.0
    
    self.longList: List[Symbol] = []
    self.shortList: List[Symbol] = []

    self.exchangeList: List[str] = ['NYSE', 'NASDAQ', 'AMEX']        
    self.quintile: int = 5
    self.rebalancePeriod: int = 12
    self.shouldRebalance: bool = True

    self.spy: Symbol = self.AddEquity('SPY', Resolution.Daily).Symbol
    self.Schedule.On(self.DateRules.MonthEnd(self.spy), 
                     self.TimeRules.AfterMarketOpen(self.spy), 
                     self.RebalancePortfolio)

def CoarseSelectionFunction(self, coarse: List[CoarseFundamental]) -> List[Symbol]:
    if not self.shouldRebalance:
        return Universe.Unchanged

    filtered = [c for c in coarse if c.Symbol.SecurityType == SecurityType.Equity
                and c.Exchange in self.exchangeList
                and c.PriceBookRatio > 0]

    sortedSecurities = sorted(filtered, key=lambda x: x.PriceBookRatio)
    
    if len(sortedSecurities) > self.quintile:
        quintileSize = len(sortedSecurities) // self.quintile
        self.longList = [s.Symbol for s in sortedSecurities[:quintileSize]]
        self.shortList = [s.Symbol for s in sortedSecurities[-quintileSize:]]

    return self.longList + self.shortList

def OnData(self, data: Slice):
    if not self.shouldRebalance:
        return
    self.shouldRebalance = False
    
    targets = [PortfolioTarget(symbol, 1 / len(self.longList)) for symbol in self.longList] + \
              [PortfolioTarget(symbol, -1 / len(self.shortList)) for symbol in self.shortList]

    self.SetHoldings(targets)

def RebalancePortfolio(self):
    self.shouldRebalance = True

def OnSecuritiesChanged(self, changes: SecurityChanges):
    for security in changes.AddedSecurities:
        security.SetFeeModel(StandardFeeModel())

# Standard fee model to simplify the fee structure
class StandardFeeModel(FeeModel):
def GetOrderFee(self, parameters: OrderFeeParameters):
    fee = parameters.Security.Price * parameters.Order.AbsoluteQuantity * 0.00005
    return OrderFee(CashAmount(fee, "USD"))
