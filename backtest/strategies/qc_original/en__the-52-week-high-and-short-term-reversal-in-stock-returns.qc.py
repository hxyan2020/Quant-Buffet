# Original QuantConnect / library Python
# locale=en slug="the-52-week-high-and-short-term-reversal-in-stock-returns"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

from AlgorithmImports import *
class ReversalCombinedwithVolatility(QCAlgorithm):
def Initialize(self):
    self.SetStartDate(2000, 1, 1)
    self.SetCash(100000)
    self.SetSecurityInitializer(lambda x: x.SetMarketPrice(self.GetLastKnownPrice(x)))
    self.leverage:int = 10
    self.quantile:int = 5
    self.period:int = 52 * 5
    self.exchange_codes:List[str] = ['NYS', 'NAS', 'ASE']
    
    market:Symbol = self.AddEquity('SPY', Resolution.Daily).Symbol
    
    self.long:List[Symbol] = []
    self.short:List[Symbol] = []
    self.data:Dict[Symbol, SymbolData] = {}
    self.fundamental_count:int = 500
    self.fundamental_sorting_key = lambda x: x.DollarVolume
    
    self.selection_flag:bool = False
    self.Settings.MinimumOrderMarginPortfolioPercentage = 0.
    self.UniverseSettings.Resolution = Resolution.Daily
    self.AddUniverse(self.FundamentalSelectionFunction)
    self.Schedule.On(self.DateRules.MonthEnd(market), self.TimeRules.AfterMarketOpen(market), self.Selection)
    self.settings.daily_precise_end_time = False
def OnSecuritiesChanged(self, changes: SecurityChanges) -> None:
    for security in changes.AddedSecurities:
        security.SetFeeModel(CustomFeeModel())
        security.SetLeverage(self.leverage)
def FundamentalSelectionFunction(self, fundamental: List[Fundamental]) -> List[Symbol]:
    # Update the rolling window every day.
    for stock in fundamental:
        symbol:Symbol = stock.Symbol
        # Store monthly price.
        if symbol in self.data:
            self.data[symbol].update(stock.AdjustedPrice)
    if not self.selection_flag:
        return Universe.Unchanged
    selected:List[Fundamental] = [x for x in fundamental if x.HasFundamentalData and x.Market == 'usa' and x.SecurityReference.ExchangeId in self.exchange_codes]
    if len(selected) > self.fundamental_count:
        selected = [x for x in sorted(selected, key=self.fundamental_sorting_key, reverse=True)[:self.fundamental_count]]
    
    selected_ready:List[Fundamental] = []
    # Warmup price rolling windows.
    for stock in selected:
        symbol:Symbol = stock.Symbol
        if symbol not in self.data:
            self.data[symbol] = SymbolData(self.period)
            history:DataFrame = self.History(symbol, self.period, Resolution.Daily)
            if history.empty:
                self.Log(f"Not enough data for {symbol} yet.")
                continue
            closes:Series = history.loc[symbol].close
            for time, close in closes.items():
                self.data[symbol].update(close)
        
        if self.data[symbol].is_ready():
            selected_ready.append(stock)
    
    pth_performance:Dict[Symbol, Tuple[float]] = {x.Symbol : (self.data[x.Symbol].pth(), self.data[x.Symbol].performance()) for x in selected_ready}
    sorted_by_pth:List[Tuple[Symbol, float]] = sorted(pth_performance.items(), key = lambda x: x[1][0], reverse = True)
    sorted_by_pth:List[Symbol] = [x[0] for x in sorted_by_pth]
    
    sorted_by_ret:List[Tuple[Symbol, float]] = sorted(pth_performance.items(), key = lambda x: x[1][1], reverse = True)
    sorted_by_ret:List[Symbol] = [x[0] for x in sorted_by_ret]
    quintile:int  = int(len(sorted_by_ret) / self.quantile)
    
    low_pth:List[Symbol] = sorted_by_pth[-quintile:]
    top_ret:List[Symbol] = sorted_by_ret[:quintile]
    low_ret:List[Symbol] = sorted_by_ret[-quintile:]
    
    self.long = [x for x in low_pth if x in low_ret]
    self.short = [x for x in low_pth if x in top_ret]
    
    return self.long + self.short
def OnData(self, data: Slice) -> None:
    if not self.selection_flag:
        return
    self.selection_flag = False
    
    # Trade execution.
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
class SymbolData():
def __init__(self, period:int):
    self._price:RollingWindow = RollingWindow[float](period)

def update(self, value:float) -> None:
    self._price.Add(value)

def is_ready(self) -> bool:
    return self._price.IsReady

def pth(self) -> float:
    high_proxy = [x for x in self._price]
    symbol_price = high_proxy[0]
    return  symbol_price / max(high_proxy[21:])

def performance(self) -> float:
    closes = [x for x in self._price][:21]
    return (closes[0] / closes[-1] - 1)
# Custom fee model.
class CustomFeeModel(FeeModel):
def GetOrderFee(self, parameters):
    fee = parameters.Security.Price * parameters.Order.AbsoluteQuantity * 0.00005
    return OrderFee(CashAmount(fee, "USD"))
