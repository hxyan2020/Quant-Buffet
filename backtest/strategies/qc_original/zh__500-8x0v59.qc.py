# Original QuantConnect / library Python
# locale=zh slug="欧市开盘期间的标普500期货收益"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

from AlgorithmImports import *
from typing import List
class SP500FuturesReturnDuringtheEUOpenPeriod(QCAlgorithm):
def Initialize(self):
    self.SetStartDate(2010, 1, 1)
    self.SetCash(1000000)
    data:Future = self.AddFuture(Futures.Indices.SP500EMini, Resolution.Minute)
    data.SetFilter(timedelta(5), timedelta(90))
    self.future:Symbol = data.Symbol
    self.contract_share_multiplier:int = 100
    self.active_contract = None
    
    self.Schedule.On(self.DateRules.EveryDay(self.future), self.TimeRules.At(9, 30), self.MarketOpen)
    self.Schedule.On(self.DateRules.EveryDay(self.future), self.TimeRules.At(16, 0), self.MarketClose)
def MarketOpen(self) -> None:
    if self.active_contract:
        # don't trade on expiry day
        if self.Time.date() == self.active_contract.Expiry.date(): 
            return
        if not self.Portfolio.Invested:
            symbol = self.active_contract.Symbol
            if self.Securities[symbol].IsTradable:
                price:float = self.active_contract.LastPrice
                future_q:int = int(self.Portfolio.TotalPortfolioValue / (price * self.contract_share_multiplier))
                
                self.MarketOrder(symbol, future_q)
        
def MarketClose(self) -> None:
    if self.Portfolio.Invested:
        self.Liquidate()
def OnData(self, slice:Slice) -> None:
    chains:List = [x for x in slice.FutureChains]
    
    chain = None
    if len(chains) > 0:
        chain = chains[0]
    else:
        return
    
    if chain.Value.Contracts.Count >= 1:
        contracts:List = [i for i in chain.Value]
        contracts:List = sorted(contracts, key = lambda x: x.Expiry)
        near_contract = contracts[0]
        self.active_contract = near_contract
