# Original QuantConnect / library Python
# locale=en slug="timing-betting-against-beta-bab-anomaly-v-2"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

from AlgorithmImports import *
import numpy as np
from pandas.core.frame import DataFrame
from typing import List, Dict

class TimingBettingAgainstBetaAnomalyv2(QCAlgorithm):

def Initialize(self):
    self.SetStartDate(2000, 1, 1)
    self.SetCash(100000)

    # daily price data
    self.data:Dict[Symbol, RollingWindow] = {}
    self.period:int = 12 * 21

    self.factor_perf_d_period:int = 21
    self.factor_perf_min_period:int = 36
    self.factor_performance:List[float] = []
    self.leverage_restriction:float = 2.

    self.symbol:Symbol = self.AddEquity('SPY', Resolution.Daily).Symbol
    self.data[self.symbol] = RollingWindow[float](self.period)

    self.vix:Symbol = self.AddData(CBOE, 'VIX', Resolution.Daily).Symbol
    self.data[self.vix] = RollingWindow[float](self.factor_perf_d_period)
    
    self.long:List[Symbol] = []
    self.short:List[Symbol] = []
    self.long_lvg:float = 1.   # leverage for long portfolio calculated from average beta
    self.short_lvg:float = 1.  # leverage for short portfolio calculated from average beta
    self.leverage_cap:float = 2.
    
    self.coarse_count:int = 1000
    self.quantile:int = 10
    self.min_share_price:float = 5.
    
    self.selection_flag:bool = False
    self.UniverseSettings.Resolution = Resolution.Daily
    self.AddUniverse(self.FundamentalSelectionFunction)
    self.Settings.MinimumOrderMarginPortfolioPercentage = 0.
    self.Schedule.On(self.DateRules.MonthStart(self.symbol), self.TimeRules.AfterMarketOpen(self.symbol), self.Selection)
    
def OnSecuritiesChanged(self, changes: SecurityChanges) -> None:
    for security in changes.AddedSecurities:
        security.SetFeeModel(CustomFeeModel())
        security.SetLeverage(self.leverage_cap * self.leverage_restriction * 5)
        
def FundamentalSelectionFunction(self, fundamental: List[Fundamental]) -> List[Symbol]:
    # update the rolling window every day
    for stock in fundamental:
        symbol:Symbol = stock.Symbol

        if symbol in self.data:
            # store daily price
            self.data[symbol].Add(stock.AdjustedPrice)
    
    # selection once a month
    if not self.selection_flag:
        return Universe.Unchanged

    # store BAB performance
    if self.long and self.short:
        long_closes:np.ndarray = np.array([np.array(list(self.data[symbol])[:self.factor_perf_d_period][::-1]) for symbol in self.long])
        short_closes:np.ndarray = np.array([np.array(list(self.data[symbol])[:self.factor_perf_d_period][::-1]) for symbol in self.short])
        long_returns:np.ndarray = (np.diff(long_closes) / long_closes[:,:-1])
        short_returns:np.ndarray = (np.diff(short_closes) / short_closes[:,:-1])

        factor_perf:float = np.cumproduct(1 + (np.mean(long_returns, axis=0) - np.mean(short_returns, axis=0)))[-1] - 1

        self.factor_performance.append(factor_perf)

    selected:List[Symbol] = [x.Symbol
        for x in sorted([x for x in fundamental if x.HasFundamentalData and x.Market == 'usa' and x.AdjustedPrice >= self.min_share_price and x.MarketCap != 0],
            key = lambda x: x.DollarVolume, reverse = True)[:self.coarse_count]]
    
    rebalance:bool = False
    if self.data[self.symbol].IsReady:
        rebalance = True

    beta:Dict[Symbol, float] = {}

    for symbol in selected:
        # warmup price rolling windows
        if symbol not in self.data:
            self.data[symbol] = RollingWindow[float](self.period)
            history:DataFrame = self.History(symbol, self.period, Resolution.Daily)
            if history.empty:
                self.Log(f"Not enough data for {symbol} yet")
                continue
            closes:pd.Series = history.loc[symbol].close
            for time, close in closes.items():
                self.data[symbol].Add(close)
        
        if rebalance:
            if self.data[symbol].IsReady:
                market_closes:np.ndarray = np.array(list(self.data[self.symbol]))
                stock_closes:np.ndarray = np.array(list(self.data[symbol]))
                
                market_returns:np.ndarray = (market_closes[:-1] - market_closes[1:]) / market_closes[1:]
                stock_returns:np.ndarray = (stock_closes[:-1] - stock_closes[1:]) / stock_closes[1:]
                
                cov:float = np.cov(stock_returns[::-1], market_returns[::-1])[0][1]
                market_variance:float = np.var(market_returns)
                beta[symbol] = cov / market_variance

    if len(beta) >= self.quantile:
        # sort by beta
        sorted_by_beta:List = sorted(beta.items(), key = lambda x:x[1], reverse=True)
        quantile:int = int(len(sorted_by_beta) / self.quantile)
        self.long = [x for x in sorted_by_beta[-quantile:]]
        self.short = [x for x in sorted_by_beta[:quantile]]
        
        # create zero-beta portfolio
        long_mean_beta:float = np.mean([x[1] for x in self.long])
        short_mean_beta:float = np.mean([x[1] for x in self.short])
        
        self.long = [x[0] for x in self.long]
        self.short = [x[0] for x in self.short]
        
        # cap leverage
        self.long_lvg = min(self.leverage_cap, abs(1. / long_mean_beta))
        self.short_lvg = min(self.leverage_cap, abs(1. / short_mean_beta))

    return self.long + self.short

def OnData(self, data: Slice) -> None:
    # store vix value
    if self.vix in data and data[self.vix]:
        self.data[self.vix].Add(data[self.vix].Value)

    if not self.selection_flag:
        return
    self.selection_flag = False
    
    if len(self.factor_performance)  None:
    self.selection_flag = True
        
# Custom fee model.
class CustomFeeModel(FeeModel):
def GetOrderFee(self, parameters):
    fee = parameters.Security.Price * parameters.Order.AbsoluteQuantity * 0.00005
    return OrderFee(CashAmount(fee, "USD"))
