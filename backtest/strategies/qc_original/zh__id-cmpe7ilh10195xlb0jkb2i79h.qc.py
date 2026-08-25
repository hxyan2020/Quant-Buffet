# Original QuantConnect / library Python
# locale=zh slug="比特币的日内动量效应"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

from AlgorithmImports import *
from pandas.core.frame import DataFrame
from math import floor
#endregion
class BitcoinIntradayMomentum(QCAlgorithm):
def Initialize(self):
    self.SetStartDate(2015, 1, 1)
    self.SetCash('USD', 100000)
    self.closes:List[float] = []
    self.period:int = 12 * 21
    self.SetWarmup(self.period, Resolution.Daily)
    
    self.percentage_traded:float = .9
    self.std_threshold:float = 2.
    self.signal_hours:List[int] = [16, 18]
    
    self.symbol:Symbol = self.AddCrypto('BTCUSD', Resolution.Minute, Market.Bitfinex).Symbol
def OnData(self, data: Slice) -> None:
    if not (self.symbol in data and data[self.symbol]):
        return
    
    current_price:float = data[self.symbol].Value
    if self.Time.hour == 23 and self.Time.minute == 59:
        # store daily price
        self.closes.append(current_price)
        if self.Portfolio[self.symbol].Invested:
            self.Liquidate(self.symbol)
    if self.IsWarmingUp: return
    if len(self.closes) = self.Securities[self.symbol].SymbolProperties.MinimumOrderSize:
            # overreaction handling
            if self.Time.hour == self.signal_hours[0] and self.Time.minute == 0:
                if not self.Portfolio[self.symbol].Invested:
                    if performance  ret_mean + self.std_threshold * ret_std:
                        self.MarketOrder(self.symbol, q)
