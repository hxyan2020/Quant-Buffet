# Original QuantConnect / library Python
# locale=zh slug="克隆对冲基金指数"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

import numpy as np
from AlgorithmImports import *
from math import floor
from datetime import datetime
class CloningHedgeFundIndexes(QCAlgorithm):
def Initialize(self):
    self.SetStartDate(2013, 1, 1)
    self.SetCash(100000)
    
    self.symbol = self.AddEquity("SPY", Resolution.Minute).Symbol
    self.leverage:float = 2.
    
    # spy consolidator
    self.consolidator:TradeBarConsolidator = TradeBarConsolidator(timedelta(days=1))
    self.consolidator.DataConsolidated += self.CustomHandler
    self.SubscriptionManager.AddConsolidator(self.symbol, self.consolidator)            
    
    self.period:int = 21
    
    # Daily price data.
    self.data:RollingWindow = RollingWindow[float](self.period)
    
    option:Option = self.AddOption("SPY", Resolution.Minute)
    
def CustomHandler(self, sender: object, consolidated_bar: TradeBar) -> None:
    self.data.Add(consolidated_bar.Close)
    
def OnData(self, slice:Slice) -> None:
    for i in slice.OptionChains:
        chains:OptionChain = i.Value
        
        if self.Portfolio[self.symbol].Invested:
            self.Liquidate(self.symbol)
        
        if not self.Portfolio.Invested:
            # Market data is ready.
            if self.data.IsReady:
                market_closes:np.ndarray = np.array(list(self.data))
                market_returns:np.ndarray = market_closes[:-1] / market_closes[1:] - 1
                market_std:float = np.std(market_returns)
                
                # Divide option chains into put options
                puts:List = list(filter(lambda x: x.Right == OptionRight.Put, chains))
                if not puts: return
                underlying_price:float = self.Securities[self.symbol].Price
                expiries:List[datetime] = list(map(lambda x: x.Expiry, puts))

                # Determine expiration date nearly one month.
                expiry:datetime = min(expiries, key=lambda x: abs((x.date() - self.Time.date()).days - 30))
                strikes:List[float] = list(map(lambda x: x.Strike, puts))

                # Determine out-of-the-money strike.
                otm_strike:float = min(strikes, key = lambda x:abs(x - float(1 - market_std) * underlying_price))
                
                # Leverage calc.
                otm_put:OptionContract = [i for i in puts if i.Expiry == expiry and i.Strike == otm_strike]
                q:float = floor(float(self.Portfolio.MarginRemaining / (underlying_price * 100)) * self.leverage)

                if otm_put:
                    # Sell with 2x leverage.
                    self.Sell(otm_put[0].Symbol, q)
