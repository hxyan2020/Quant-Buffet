# Original QuantConnect / library Python
# locale=zh slug="彩票型股票与52周最高价"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

import numpy as np
from AlgorithmImports import *
from typing import List, Dict
class LotteryStocks52WeekHigh(QCAlgorithm):
def Initialize(self):
    self.SetStartDate(2010, 1, 1)
    self.SetCash(100000)
    self.exchange_codes: List[str] = ['NYS', 'NAS', 'ASE']    
    self.period: int = 52 * 5
    self.month_period: int = 21
    self.leverage: int = 10
    self.min_share_price: int = 5
    self.quantile: int = 10
    
    self.data: Dict[Symbol, RollingWindow] = {}
    self.long: List[Symbol] = []
    self.short: List[Symbol] = []
    
    market: Symbol = self.AddEquity('SPY', Resolution.Daily).Symbol
    self.fundamental_count: int = 1_000
    self.fundamental_sorting_key = lambda x: x.DollarVolume
    self.selection_flag: bool = True
    self.settings.daily_precise_end_time = False
    self.Settings.MinimumOrderMarginPortfolioPercentage = 0.
    self.UniverseSettings.Resolution = Resolution.Daily
    self.AddUniverse(self.FundamentalSelectionFunction)
    self.Schedule.On(self.DateRules.MonthStart(market), self.TimeRules.AfterMarketOpen(market), self.Selection)

def OnSecuritiesChanged(self, changes: SecurityChanges) -> None:
    for security in changes.AddedSecurities:
        security.SetFeeModel(CustomFeeModel())
        security.SetLeverage(self.leverage)

def FundamentalSelectionFunction(self, fundamental: List[Fundamental]) -> List[Symbol]:
    # update the rolling window every day
    for stock in fundamental:
        symbol: Symbol = stock.Symbol
        if symbol in self.data:
            self.data[symbol].Add(stock.AdjustedPrice)
    if not self.selection_flag:
        return Universe.Unchanged
    selected: List[Fundamental] = [
        x for x in fundamental if x.HasFundamentalData and x.Price > self.min_share_price and x.Market == 'usa' \
        and x.MarketCap != 0 and x.SecurityReference.ExchangeId in self.exchange_codes
    ]
    
    if len(selected) > self.fundamental_count:
        selected = [x for x in sorted(selected, key=self.fundamental_sorting_key, reverse=True)[:self.fundamental_count]]
    MAX: Dict[Symbol, float] = {}
    NH: Dict[Symbol, float] = {}
    for stock in selected:
        symbol: Symbol = stock.Symbol
        # warmup price rolling windows
        if symbol not in self.data:
            self.data[symbol] = RollingWindow[float](self.period)
            history:DataFrame = self.History(symbol, self.period, Resolution.Daily)
            if history.empty:
                self.Log(f"Not enough data for {symbol} yet")
                continue
            closes:Series = history.loc[symbol].close
            for time, close in closes.items():
                self.data[symbol].Add(close)
        if not self.data[symbol].IsReady:
            continue
        
        closes: List[float] = list(self.data[symbol])
        last_month_closes: np.ndarray = np.array(closes[:self.month_period])
        last_close: float = closes[0]
        
        daily_returns: np.ndarray = (last_month_closes[:-1] - last_month_closes[1:]) / last_month_closes[1:]
        MAX[symbol] = max(daily_returns)
        
        # NH calc    
        if last_close != 0:
            local_highest_close: float = max(closes)
            NH[symbol] = last_close / local_highest_close
    if len(MAX)  None:
    if not self.selection_flag:
        return
    self.selection_flag = False
    
    # Trade execution
    targets:List[PortfolioTarget] = []
    for i, portfolio in enumerate([self.long, self.short]):
        for symbol in portfolio:
            if symbol in slice and slice[symbol]:
                targets.append(PortfolioTarget(symbol, ((-1) ** i) / len(portfolio)))
    
    self.SetHoldings(targets, True)
    self.long.clear()
    self.short.clear()
    
def Selection(self) -> None:
    self.selection_flag = True
    
class CustomFeeModel(FeeModel):
def GetOrderFee(self, parameters):
    fee = parameters.Security.Price * parameters.Order.AbsoluteQuantity * 0.00005
    return OrderFee(CashAmount(fee, "USD"))
