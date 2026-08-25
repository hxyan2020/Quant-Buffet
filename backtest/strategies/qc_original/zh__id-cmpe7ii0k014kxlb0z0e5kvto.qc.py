# Original QuantConnect / library Python
# locale=zh slug="动量季节性与投资者偏好"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

from AlgorithmImports import *
from pandas.core.frame import DataFrame
class MomentumSeasonalityInvestorPreferences(QCAlgorithm):

def Initialize(self):
    self.SetStartDate(2010, 1, 1)
    self.SetCash(100000)
    market:Symbol = self.AddEquity('SPY', Resolution.Daily).Symbol
    
    self.fundamental_count:int = 500
    self.fundamental_sorting_key = lambda x: x.DollarVolume
    
    self.period:int = 12 * 21
    self.quantile:int = 10
    self.leverage:int = 5
    self.exchange_codes:List[str] = ['NYS', 'NAS', 'ASE']
    self.long:List[Symbol] = []
    self.short:List[Symbol] = []
    
    # Daily price data.
    self.data:Dict[Symbol, SymbolData] = {}
    
    self.selection_flag:bool = True
    self.UniverseSettings.Resolution = Resolution.Daily
    self.AddUniverse(self.FundamentalSelectionFunction)
    self.settings.daily_precise_end_time = False
    self.settings.minimum_order_margin_portfolio_percentage = 0.
    self.schedule.on(self.date_rules.month_start(market),
                    self.time_rules.after_market_open(market),
                    self.selection)
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
    selected:List[Fundamental] = [x for x in fundamental if x.HasFundamentalData and x.Market == 'usa' and x.SecurityReference.ExchangeId in self.exchange_codes and x.MarketCap != 0]
    if len(selected) > self.fundamental_count:
        selected = [x for x in sorted(selected, key=self.fundamental_sorting_key, reverse=True)[:self.fundamental_count]]
        
    performance:Dict[Symbol, float] = {}
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
            performance[symbol] = self.data[symbol].performance()
    
    if len(performance) >= self.quantile:
        sorted_by_performance:List = sorted(performance, key = performance.get, reverse = True)
        quantile:int = int(len(sorted_by_performance) / self.quantile)
        self.long = sorted_by_performance[:quantile]
        self.short = sorted_by_performance[-quantile:]
    
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
def selection(self) -> None:
    if self.Time.month % 3 == 0:
        self.Liquidate()
        self.selection_flag = True
class SymbolData():
def __init__(self, period: int):
    self._price:RollingWindow = RollingWindow[float](period)

def update(self, price: float) -> None:
    self._price.Add(price)

def is_ready(self) -> bool:
    return self._price.IsReady
    
# Yearly performance, one month skipped.
def performance(self) -> float:
    closes:List[float] = list(self._price)[21:]
    return (closes[0] / closes[-1] - 1)

# Custom fee model.
class CustomFeeModel(FeeModel):
def GetOrderFee(self, parameters):
    fee = parameters.Security.Price * parameters.Order.AbsoluteQuantity * 0.00005
    return OrderFee(CashAmount(fee, "USD"))
