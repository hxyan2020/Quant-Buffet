# Original QuantConnect / library Python
# locale=zh slug="接近52周最低点策略"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

from AlgorithmImports import *
from pandas.core.frame import DataFrame
class Nearnessto52WeekLow(QCAlgorithm):
def Initialize(self):
    self.SetStartDate(2000, 1, 1)
    self.SetCash(100000)
    market:Symbol = self.AddEquity('SPY', Resolution.Daily).Symbol
    
    self.fundamental_count:int = 3000
    self.fundamental_sorting_key = lambda x: x.MarketCap
    
    self.weight:Dict[Symbol, float] = {}
    self.data:Dict[Symbol, SymbolData] = {}
    
    self.period:int = 52 * 5 + 4*5
    self.quantile:int = 20
    self.leverage:int = 5
    self.min_share_price:float = 5.
    self.exchange_codes:List[str] = ['NYS', 'NAS', 'ASE']
    
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
    # Update the rolling window every day.
    for stock in fundamental:
        symbol:Symbol = stock.Symbol
        if symbol in self.data:
            # Store daily price.
            self.data[symbol].update(stock.AdjustedPrice)
        
    if not self.selection_flag:
        return Universe.Unchanged
    
    selected:List[Fundamental] = [
        x for x in fundamental if x.HasFundamentalData and x.Market == 'usa' and x.SecurityReference.ExchangeId in self.exchange_codes and \
        x.MarketCap != 0 and x.Price >= self.min_share_price
    ]
    if len(selected) > self.fundamental_count:
        selected = [x for x in sorted(selected, key=self.fundamental_sorting_key, reverse=True)[:self.fundamental_count]]
    LOW:Dict[Fundamental, float] = {}
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
            LOW[stock] = self.data[symbol].get_latest_price() / self.data[symbol].minimum()
    long:List[Fundamental] = []
    short:List[Fundamental] = []
    if len(LOW) >= self.quantile:
        # LOW sorting
        sorted_by_LOW:List[Fundamental] = sorted(LOW, key = LOW.get, reverse = True)
        quantile:int = int(len(sorted_by_LOW) / self.quantile)
        long = sorted_by_LOW[-quantile:]
        short = sorted_by_LOW[:len(sorted_by_LOW) - quantile]
    
    # Market cap weighting.
    for i, portfolio in enumerate([long, short]):
        mc_sum:float = sum(map(lambda x: x.MarketCap, portfolio))
        for stock in portfolio:
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
    self.selection_flag = True
    
class SymbolData():
def __init__(self, period: int):
    self._price:RollingWindow = RollingWindow[float](period)

def update(self, price: float) -> None:
    self._price.Add(price)

def is_ready(self) -> bool:
    return self._price.IsReady
 
# Skip last month.
def minimum(self) -> float:
    return min([x for x in self._price][4*5:])
    
def get_latest_price(self) -> float:
    return self._price[0]
# Custom fee model.
class CustomFeeModel(FeeModel):
def GetOrderFee(self, parameters):
    fee = parameters.Security.Price * parameters.Order.AbsoluteQuantity * 0.00005
    return OrderFee(CashAmount(fee, "USD"))
