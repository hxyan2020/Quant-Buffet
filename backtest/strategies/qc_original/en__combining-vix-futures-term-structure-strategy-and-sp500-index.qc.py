# Original QuantConnect / library Python
# locale=en slug="combining-vix-futures-term-structure-strategy-and-sp500-index"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

from AlgorithmImports import *
import numpy as np
#endregion
class CombiningVIXFuturesTermStructureStrategySP500Index(QCAlgorithm):
def Initialize(self):
    self.SetStartDate(2010, 1, 1)
    self.SetCash(10_000_000)
    self.market: Symbol = self.AddEquity('SPY', Resolution.Daily).Symbol
    self.vix_futures: Symbol = self.AddEquity('VIXY', Resolution.Daily).Symbol
    
    # VIX and VIX3M filter
    self.vix: Symbol = self.AddData(CBOE, 'VIX', Resolution.Daily).Symbol
    self.vix_3M: Symbol = self.AddData(CBOE, 'VIX3M', Resolution.Daily).Symbol
    
    self.traded_symbol: List[Symbol] = [self.market, self.vix_futures]
    # daily price data
    period:int = 20
    self.price_data: Dict[Symbol, RollingWindow] = {symbol : RollingWindow[float](period) for symbol in self.traded_symbol}
    self.Settings.MinimumOrderMarginPortfolioPercentage = 0.
    self.settings.daily_precise_end_time = False
    
def OnData(self, slice: Slice) -> None:
    # store daily prices
    for symbol in self.traded_symbol:
        if symbol in slice and slice[symbol]:
            self.price_data[symbol].Add(slice[symbol].Value)
    
    # rebalance daily
    if all(x in slice and slice[x] for x in self.traded_symbol + [self.vix, self.vix_3M]):
        if all(self.price_data[x].IsReady for x in self.traded_symbol):
            vix: float = slice[self.vix].Value
            vix_3m: float = slice[self.vix_3M].Value
            vix_volatility: float = self.volatility(list(self.price_data[self.vix_futures])[1:]) # one-day lag
            market_volatility: float = self.volatility(list(self.price_data[self.market])[1:]) # one-day lag
            total_volatility: float = 1. / vix_volatility + 1. / market_volatility
            
            market_w: float = (1. / market_volatility) / total_volatility
            vix_w: float = (1. / vix_volatility) / total_volatility
            self.SetHoldings(self.market, market_w)
            if vix_3m >= vix:
                # contango -> short vixy
                self.SetHoldings(self.vix_futures, -vix_w)
            else:
                # backwardation -> long vixy
                self.SetHoldings(self.vix_futures, vix_w)
def volatility(self, daily_prices: List[float]) -> float:
    daily_prices: np.ndarray = np.array(daily_prices)
    returns: np.ndarray = daily_prices[:-1] / daily_prices[1:] - 1
    return np.std(returns)
