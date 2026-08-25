# Original QuantConnect / library Python
# locale=en slug="consistent-momentum-strategy-2"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

from AlgorithmImports import *
class ConsistentMomentumStrategy(QCAlgorithm):
def Initialize(self):
    self.SetStartDate(2010, 1, 1)
    self.SetCash(100000)
    market:Symbol = self.AddEquity('SPY', Resolution.Daily).Symbol
    
    self.long:List[Symbol] = []
    self.short:List[Symbol] = []
    
    self.data:Dict[Symbol, SymbolData] = {}
    
    self.fundamental_count:int = 1000
    self.fundamental_sorting_key = lambda x: x.DollarVolume
    
    self.period:int = 7 * 21
    self.quantile:int = 10
    self.leverage:int = 5
    self.exchange_codes:List[str] = ['NYS', 'NAS', 'ASE']
    
    self.selection_flag:bool = False
    self.UniverseSettings.Resolution = Resolution.Daily
    self.Settings.MinimumOrderMarginPortfolioPercentage = 0.
    self.AddUniverse(self.FundamentalSelectionFunction)
    self.Schedule.On(self.DateRules.MonthStart(market), self.TimeRules.AfterMarketOpen(market), self.Rebalance)
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
    
    selected:List[Fundamental] = [x for x in fundamental if x.HasFundamentalData and x.Market == 'usa' and x.SecurityReference.ExchangeId in self.exchange_codes and \
        x.MarketCap != 0 and x.CompanyReference.IsREIT != 1]
    if len(selected) > self.fundamental_count:
        selected = [x for x in sorted(selected, key=self.fundamental_sorting_key, reverse=True)[:self.fundamental_count]]
    
    momentum_t71_t60:Dict[Symbol, float] = {}
    # Warmup price rolling windows.
    for stock in selected:
        symbol:Symbol = stock.Symbol
        if symbol not in self.data:
            self.data[symbol] = SymbolData(self.period)
            history:DataFrame = self.History(symbol, self.period, Resolution.Daily)
            if history.empty:
                self.Log(f"Not enough data for {symbol} yet")
                continue
            closes:pd.Series = history.loc[symbol].close
            for time, close in closes.items():
                self.data[symbol].update(close)
            
        if self.data[symbol].is_ready():
            momentum_t71_t60[symbol] = (self.data[symbol].performance_t7t1(), self.data[symbol].performance_t6t0())
    
    if len(momentum_t71_t60) >= self.quantile:
        # Momentum t-7 to t-1 sorting
        sorted_by_perf_t71:List = sorted(momentum_t71_t60.items(), key = lambda x: x[1][0], reverse = True)
        quantile:int = int(len(sorted_by_perf_t71) / self.quantile)
        high_by_perf_t71:List[Symbol] = [x[0] for x in sorted_by_perf_t71[:quantile]]
        low_by_perf_t71:List[Symbol] = [x[0] for x in sorted_by_perf_t71[-quantile:]]
        # Momentum t-6 to t sorting
        sorted_by_perf_t60:List = sorted(momentum_t71_t60.items(), key = lambda x: x[1][1], reverse = True)
        quantile = int(len(sorted_by_perf_t60) / self.quantile)
        high_by_perf_t60:List[Symbol] = [x[0] for x in sorted_by_perf_t60[:quantile]]
        low_by_perf_t60:List[Symbol] = [x[0] for x in sorted_by_perf_t60[-quantile:]]
        
        self.long = [x for x in high_by_perf_t71 if x in high_by_perf_t60]
        self.short = [x for x in low_by_perf_t71 if x in low_by_perf_t60]
    
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
def Rebalance(self) -> None:
    if self.Time.month % 6 == 0:
        self.selection_flag = True
class SymbolData():
def __init__(self, period: int):
    self._price:RollingWindow = RollingWindow[float](period)

def update(self, price: float) -> None:
    self._price.Add(price)

def is_ready(self) -> bool:
    return self._price.IsReady
    
def performance_t7t1(self) -> float:
    closes:List[float] = [x for x in self._price][21:]
    return (closes[0] / closes[-1] - 1)
def performance_t6t0(self) -> float:
    closes:List[float] = [x for x in self._price][:-21]
    return (closes[0] / closes[-1] - 1)

# Custom fee model.
class CustomFeeModel(FeeModel):
def GetOrderFee(self, parameters):
    fee = parameters.Security.Price * parameters.Order.AbsoluteQuantity * 0.00005
    return OrderFee(CashAmount(fee, "USD"))
