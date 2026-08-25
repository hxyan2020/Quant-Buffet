# Original QuantConnect / library Python
# locale=en slug="overlapping-momentum-portfolios"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

import numpy as np
from AlgorithmImports import *
from pandas.core.frame import DataFrame
class OverlappingMomentumPortfolios(QCAlgorithm):
def Initialize(self):
    self.SetStartDate(2005, 1, 1)
    self.SetCash(100000)
    self.fundamental_count:int = 500
    self.fundamental_sorting_key = lambda x: x.DollarVolume
    market:Symbol = self.AddEquity('SPY', Resolution.Daily).Symbol
    
    # Monthly price data.
    self.data:Dict[Symbol, SymbolData] = {}
    self.weight:Dict[Symbol, float] = {}
    self.period:int = 13
    self.leverage:int = 5
    self.min_share_price:float = 1.
    self.exchange_codes:List[str] = ['NYS', 'NAS', 'ASE']
    self.quantile:int = 10
    self.current_year:int = -1
    self.selection_flag:bool = False
    self.record_price_flag:bool = False
    self.UniverseSettings.Resolution = Resolution.Daily
    self.Settings.MinimumOrderMarginPortfolioPercentage = 0.
    self.AddUniverse(self.FundamentalSelectionFunction)
    self.Schedule.On(self.DateRules.MonthEnd(market), self.TimeRules.AfterMarketOpen(market), self.Selection)
    self.settings.daily_precise_end_time = False
def OnSecuritiesChanged(self, changes: SecurityChanges) -> None:
    for security in changes.AddedSecurities:
        security.SetFeeModel(CustomFeeModel())
        security.SetLeverage(self.leverage)
        
def FundamentalSelectionFunction(self, fundamental: List[Fundamental]) -> List[Symbol]:
    if not self.record_price_flag or not self.selection_flag:
        return Universe.Unchanged
        
    self.record_price_flag = False
    
    # Update the rolling window every month.
    for stock in fundamental:
        symbol:Symbol = stock.Symbol
        # Store monthly price.
        if symbol in self.data:
            self.data[symbol].update(stock.AdjustedPrice)
    if not self.selection_flag:
        return Universe.Unchanged
    selected:List[Fundamental] = [
        x for x in fundamental if x.HasFundamentalData and x.Price >= self.min_share_price and x.Market == 'usa' and \
        x.SecurityReference.ExchangeId in self.exchange_codes and x.MarketCap != 0
    ]
    if len(selected) > self.fundamental_count:
        selected = [x for x in sorted(selected, key=self.fundamental_sorting_key, reverse=True)[:self.fundamental_count]]
    symbol_data:Dict[Fundamental, SymbolDataMomentum] = {}
    # Warmup price rolling windows.
    for stock in selected:
        symbol:Symbol = stock.Symbol
        if symbol not in self.data:
            self.data[symbol] = SymbolData(self.period)
            history:DataFrame = self.History(symbol, self.period*30, Resolution.Daily)
            if history.empty:
                self.Log(f"Not enough data for {symbol} yet.")
                continue
            closes:pd.Series = history.loc[symbol].close
            
            closes_len:int = len(closes.keys())
            # Find monthly closes.
            for index, time_close in enumerate(closes.items()):
                # index out of bounds check.
                if index + 1 = self.quantile:
        quantile:int = int(len(symbol_data) / self.quantile)
        sorted_by_12m_mom = sorted(symbol_data.items(), key = lambda x: x[1].momentum_12m, reverse = True)
        sorted_by_6m_mom = sorted(symbol_data.items(), key = lambda x: x[1].momentum_6m, reverse = True)
        
        high_by_12m_mom = [x for x in sorted_by_12m_mom[:quantile]]
        low_by_12m_mom = [x for x in sorted_by_12m_mom[-quantile:]]
        
        high_by_6m_mom = [x for x in sorted_by_6m_mom[:quantile]]
        low_by_6m_mom = [x for x in sorted_by_6m_mom[-quantile:]]
        
        long_data = [x for x in high_by_12m_mom if x in high_by_6m_mom]
        short_data = [x for x in low_by_12m_mom if x in low_by_6m_mom]
        
        # Market cap weighting.
        for i, portfolio in enumerate([long_data, short_data]):
            mc_sum:float = sum(map(lambda x: x[0].MarketCap, portfolio))
            for stock, symbol_data in portfolio:
                self.weight[stock.Symbol] = ((-1) ** i) * stock.MarketCap / mc_sum
    return list(self.weight.keys())
def OnData(self, data: Slice) -> None:
    if not self.selection_flag:
        return
    self.selection_flag = False
    
    # Trade execution.
    portfolio:List[PortfolioTarget] = [PortfolioTarget(symbol, w) for symbol, w in self.weight.items() if symbol in data and data[symbol]]
    self.SetHoldings(portfolio, True)
    self.weight.clear()
    
def Selection(self) -> None:
    self.record_price_flag = True
    if self.current_year != self.Time.year:
        self.current_year = self.Time.year
        self.selection_flag = True
class SymbolData():
def __init__(self, period: int):
    self._monthly_closes:RollingWindow = RollingWindow[float](period)
    
def update(self, close: float) -> None:
    self._monthly_closes.Add(close)
    
def is_ready(self) -> bool:
    return self._monthly_closes.IsReady
def calculate_performances(self) -> float:
    months_closes:List[float] = list(self._monthly_closes)
    twelve_months_closes:List[float] = months_closes[1:]
    six_months_closes:List[float] = months_closes[1:7]
    
    twelve_months_performance:float = twelve_months_closes[0] / twelve_months_closes[-1] - 1
    six_months_performance:float = six_months_closes[0] / six_months_closes[-1] - 1
    
    return (twelve_months_performance, six_months_performance)
    
class SymbolDataMomentum():
def __init__(self, momentum_12m: float, momentum_6m: float):
    self.momentum_12m:float = momentum_12m
    self.momentum_6m:float = momentum_6m
    
# Custom fee model
class CustomFeeModel(FeeModel):
def GetOrderFee(self, parameters):
    fee = parameters.Security.Price * parameters.Order.AbsoluteQuantity * 0.00005
    return OrderFee(CashAmount(fee, "USD"))
