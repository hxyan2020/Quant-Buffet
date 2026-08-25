# Original QuantConnect / library Python
# locale=zh slug="动态动量与逆势交易"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

import numpy as np
from AlgorithmImports import *
from pandas.core.frame import DataFrame
class DynamicMomentumContrarianTrading(QCAlgorithm):
def Initialize(self):
    self.SetStartDate(2000, 1, 1)
    self.SetCash(100000)
    self.weight:Dict[Symbol, float] = {}
    
    # Monthly price data.
    self.data:Dict[Symbol, SymbolData] = {}
    self.period:int = 13
    self.quantile:int = 10
    self.leverage:int = 5
    
    self.market:Symbol = self.AddEquity('SPY', Resolution.Daily).Symbol
    # Market daily data.
    daily_period:int = 21
    self.data[self.market] = SymbolData(daily_period)
    
    self.market_return_data:List[float] = []
    self.min_monthly_perf_period:int = 12
    self.contrarian_flag:bool = False
    self.contrarian_months:int = 0
    self.fundamental_count:int = 500
    self.fundamental_sorting_key = lambda x: x.DollarVolume
    self.selection_flag:int = False
    self.UniverseSettings.Resolution = Resolution.Daily
    self.Settings.MinimumOrderMarginPortfolioPercentage = 0.
    self.AddUniverse(self.FundamentalSelectionFunction)
    self.Schedule.On(self.DateRules.MonthEnd(self.market), self.TimeRules.BeforeMarketClose(self.market), self.Selection)        
    self.settings.daily_precise_end_time = False
def OnSecuritiesChanged(self, changes: SecurityChanges) -> None:
    for security in changes.AddedSecurities:
        security.SetFeeModel(CustomFeeModel())
        security.SetLeverage(self.leverage)
            
def FundamentalSelectionFunction(self, fundamental: List[Fundamental]) -> List[Symbol]:
    if not self.selection_flag or self.contrarian_flag:
        return Universe.Unchanged
    # Update the rolling window every month.
    for stock in fundamental:
        symbol:Symbol = stock.Symbol
        
        # Store monthly price.
        if symbol in self.data:
            self.data[symbol].update(stock.AdjustedPrice)
        
        # Market return calc.
        if self.data[self.market].is_ready():
            self.market_return_data.append(self.data[self.market].performance())

    selected:List[Fundamental] = [x for x in fundamental if x.HasFundamentalData and x.Market == 'usa' and x.MarketCap != 0]
    if len(selected) > self.fundamental_count:
        selected = [x for x in sorted(selected, key=self.fundamental_sorting_key, reverse=True)[:self.fundamental_count]]
        
    # Warmup price rolling windows.
    for stock in selected:
        symbol:Symbol = stock.Symbol
        if symbol not in self.data:
            self.data[symbol] = SymbolData(self.period)
            history:DataFrame = self.History(symbol, self.period * 30, Resolution.Daily)
            if history.empty:
                self.Log(f"Not enough data for {symbol} yet.")
                continue
            closes:pd.Series = history.loc[symbol].close
            
            closes_len:int = len(closes.keys())
            # Find monthly closes.
            for index, time_close in enumerate(closes.items()):
                # index out of bounds check.
                if index + 1 = self.min_monthly_perf_period and len(performance) >= self.quantile:
        mean_ret:float = np.mean(self.market_return_data)
        std_ret:float = np.std(self.market_return_data)
        recent_market_ret:float = self.market_return_data[-1]
    
        # There was a crash last month.
        if recent_market_ret  None:
    if not self.selection_flag:
        return
    self.selection_flag = False
    
    portfolio:List[PortfolioTarget] = [PortfolioTarget(symbol, w) for symbol, w in self.weight.items() if symbol in data and data[symbol]]
    self.SetHoldings(portfolio, True)
    # Trade execution.
    if self.contrarian_flag:
        self.contrarian_months += 1
        if self.contrarian_months == 3:
            self.contrarian_flag = False
            self.contrarian_months = 0
            self.weight.clear()
    else:
        self.weight.clear()
def Selection(self) -> None:
    self.selection_flag = True
    
class SymbolData():
def __init__(self, period: int) -> None:
    self._price:RollingWindow = RollingWindow[float](period)

def update(self, price: float) -> None:
    self._price.Add(price)

def is_ready(self) -> bool:
    return self._price.IsReady
    
# Performance, one month skipped.
def performance(self, values_to_skip = 0) -> float:
    return self._price[values_to_skip] / self._price[self._price.Count - 1] - 1

# Custom fee model.
class CustomFeeModel(FeeModel):
def GetOrderFee(self, parameters):
    fee = parameters.Security.Price * parameters.Order.AbsoluteQuantity * 0.00005
    return OrderFee(CashAmount(fee, "USD"))
