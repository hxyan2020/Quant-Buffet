# Original QuantConnect / library Python
# locale=en slug="chronological-return-ordering"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

import numpy as np
from AlgorithmImports import *
class ChronologicalReturnOrdering(QCAlgorithm):
def Initialize(self):
    self.SetStartDate(2000, 1, 1)
    self.SetCash(100000)
    
    self.period:int = 21
    self.quantile:int = 10
    self.leverage:int = 5
    market:Symbol = self.AddEquity('SPY', Resolution.Daily).Symbol
    # daily price data
    self.prices:Dict[Symbol, RollingWindow] = {}
    
    self.long:List[Symbol] = []
    self.short:List[Symbol] = []
    self.fundamental_count:int = 500
    self.fundamental_sorting_key = lambda x: x.DollarVolume
    self.selection_flag:bool = False
    self.UniverseSettings.Resolution = Resolution.Daily
    self.AddUniverse(self.FundamentalSelectionFunction)
    self.Settings.MinimumOrderMarginPortfolioPercentage = 0.
    self.Schedule.On(self.DateRules.MonthStart(market), self.TimeRules.AfterMarketOpen(market), self.Selection)
    self.settings.daily_precise_end_time = False
def OnSecuritiesChanged(self, changes: SecurityChanges) -> None:
    for security in changes.AddedSecurities:
        security.SetFeeModel(CustomFeeModel())
        security.SetLeverage(self.leverage)    
def FundamentalSelectionFunction(self, fundamental: List[Fundamental]) -> List[Symbol]:
    # update the rolling window every day
    for stock in fundamental:
        symbol:Symbol = stock.Symbol
        # store daily price
        if symbol in self.prices:
            self.prices[symbol].Add(stock.AdjustedPrice)
    if not self.selection_flag:
        return Universe.Unchanged
    selected:List[Fundamental] = [x for x in fundamental if x.HasFundamentalData]
    if len(selected) > self.fundamental_count:
        selected = [x for x in sorted(selected, key=self.fundamental_sorting_key, reverse=True)[:self.fundamental_count]]
    # warmup price rolling windows
    for stock in selected:
        symbol:Symbol = stock.Symbol
        if symbol in self.prices:
            continue
        self.prices[symbol] = RollingWindow[float](self.period)
        history = self.History(symbol, self.period, Resolution.Daily)
        if history.empty:
            self.Log(f"Not enough data for {symbol} yet.")
            continue
        closes = history.loc[symbol].close
        for time, close in closes.items():
            self.prices[symbol].Add(close)
        
    # cro calc - Pearson product-moment correlation coefficients
    daily_returns:Dict[Symbol, pd.Series] = { x.Symbol : pd.Series([p for p in self.prices[x.Symbol]][::-1]).cumprod().dropna() for x in selected if self.prices[x.Symbol].IsReady }
    CRO:Dict[Symbol, float] = { x : np.corrcoef(daily_returns[x].values, range(len(daily_returns[x])))[0,1] for x in daily_returns }
    
    # cro sorting
    if len(CRO) >= self.quantile:
        sorted_by_cro = sorted(CRO.items(), key = lambda x: x[1], reverse=True)
        quantile:int = int(len(sorted_by_cro) / self.quantile)
        self.long = [x[0] for x in sorted_by_cro[:quantile]]
        self.short = [x[0] for x in sorted_by_cro[-quantile:]]
    
    return self.long + self.short
def OnData(self, data: Slice) -> None:
    if not self.selection_flag:
        return
    self.selection_flag = False
    
    # order execution
    targets:List[PortfolioTarget] = []
    for i, portfolio in enumerate([self.long, self.short]):
        for symbol in portfolio:
            if symbol in data and data[symbol]:
                targets.append(PortfolioTarget(symbol, ((-1) ** i) / len(portfolio)))
		
    self.SetHoldings(targets, True)
    self.long.clear()
    self.short.clear()
def Selection(self) -> None:
    self.selection_flag = True
# Custom fee model.
class CustomFeeModel(FeeModel):
def GetOrderFee(self, parameters):
    fee = parameters.Security.Price * parameters.Order.AbsoluteQuantity * 0.00005
    return OrderFee(CashAmount(fee, "USD"))
