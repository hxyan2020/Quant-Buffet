# Original QuantConnect / library Python
# locale=en slug="comomentum-strategy"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

import itertools as it
import numpy as np
from AlgorithmImports import *
from pandas.core.frame import DataFrame
class ComomentumStrategy(QCAlgorithm):
def Initialize(self):
    self.SetStartDate(2010, 1, 1)
    self.SetCash(100000)
    self.long:List[Symbol] = []
    self.short:List[Symbol] = []
    market:Symbol = self.AddEquity('SPY', Resolution.Daily).Symbol
    
    # Weekly price data.
    self.data:Dict[Symbol, SymbolData] = {}
    self.period:int = 52
    self.quantile:int = 10
    self.leverage:int = 3
    self.min_share_price:float = 5.
    self.exchange_codes:List[str] = ['NYS', 'NAS', 'ASE']
    self.fundamental_count:int = 500
    self.fundamental_sorting_key = lambda x: x.DollarVolume
    # Historical commonL values.
    self.historical_CommonL:List[float] = []
    self.min_historical_CommonL_period:int = 12
    
    self.last_month:int = -1
    self.selection_flag:bool = False
    self.UniverseSettings.Resolution = Resolution.Daily
    self.AddUniverse(self.FundamentalSelectionFunction)
    self.settings.daily_precise_end_time = False
    self.settings.minimum_order_margin_portfolio_percentage = 0.
    market: Symbol = self.AddEquity('SPY', Resolution.Daily).Symbol
    self.schedule.on(self.date_rules.month_start(market),
                    self.time_rules.after_market_open(market),
                    self.selection)
    
def OnSecuritiesChanged(self, changes: SecurityChanges) -> None:
    for security in changes.AddedSecurities:
        security.SetFeeModel(CustomFeeModel())
        security.SetLeverage(self.leverage)
def FundamentalSelectionFunction(self, fundamental: List[Fundamental]) -> List[Symbol]:
    for stock in fundamental:
        symbol:Symbol = stock.Symbol
        # Store monthly price.
        if symbol in self.data:
            self.data[symbol].update(stock.AdjustedPrice)
    if not self.selection_flag:
        return Universe.Unchanged
    
    selected:List[Fundamental] = [x for x in fundamental if x.HasFundamentalData and x.Market == 'usa' and \
        x.Price >= self.min_share_price and x.SecurityReference.ExchangeId in self.exchange_codes]
    
    if len(selected) > self.fundamental_count:
        selected = [x for x in sorted(selected, key=self.fundamental_sorting_key, reverse=True)[:self.fundamental_count]]
    performance:Dict[Symbol, float] = {}
    for stock in selected:
        symbol:Symbol = stock.Symbol
        if symbol not in self.data:
            self.data[symbol] = SymbolData(self.period)
            history:DataFrame = self.History(symbol, self.period * 5, Resolution.Daily)
            if history.empty:
                self.Log(f"Not warmed up yet: {symbol}")
                continue
            closes:pd.Series = history.loc[symbol].close
            for index, close in enumerate(closes):
                if index % 5 == 0:
                    self.data[symbol].update(close)
        
        if self.data[symbol].is_ready():
            performance[symbol] = self.data[symbol].performance()
    if len(performance) = self.min_historical_CommonL_period:
            bottom_commonL_quintile:float = np.percentile(self.historical_CommonL, 20)
            if commonL  None:
    if not self.selection_flag:
        return
    self.selection_flag = False
    # order execution
    targets:List[PortfolioTarget] = []
    for i, portfolio in enumerate([self.long, self.short]):
        for symbol in portfolio:
            if symbol in slice and slice[symbol]:
                targets.append(PortfolioTarget(symbol, ((-1) ** i) / len(portfolio)))
    
    self.SetHoldings(targets, True)
    self.long.clear()
    self.short.clear()
    
def selection(self) -> None:
    self.selection_flag = True
class SymbolData():
def __init__(self, period: int):
    self._price:RollingWindow = RollingWindow[float](period)
def is_ready(self) -> bool:
    return self._price.IsReady

def update(self, close: float) -> None:
    self._price.Add(close)
    
# Performance for previous 52 weeks, one month skipped.
def performance(self) -> float:
    values = [x for x in self._price][4:]
    return (values[3] / values[-1] - 1)
# Custom fee model.
class CustomFeeModel(FeeModel):
def GetOrderFee(self, parameters):
    fee = parameters.Security.Price * parameters.Order.AbsoluteQuantity * 0.00005
    return OrderFee(CashAmount(fee, "USD"))
