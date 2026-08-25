# Original QuantConnect / library Python
# locale=zh slug="动量策略中的无崩盘成分"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

from AlgorithmImports import *
class MomentumWithoutTheCrashComponent(QCAlgorithm):
def Initialize(self):
    self.SetStartDate(2000, 1, 1)
    self.SetCash(100000)
    
    self.data:Dict[Symbol, SymbolData] = {}
    self.weight:Dict[Symbol, float] = {}
    
    self.fundamental_count:int = 1000
    self.fundamental_sorting_key = lambda x: x.DollarVolume
    
    self.exchange_codes:List[str] = ['NYS', 'NAS', 'ASE']
    self.period:int = 12 * 21
    self.rebalance_month:int = 4
    self.quantile:int = 10
    self.leverage:int = 5
    self.min_share_price:float = 5.
    market:Symbol = self.AddEquity('SPY', Resolution.Daily).Symbol
    
    self.selection_flag:bool = False
    self.UniverseSettings.Resolution = Resolution.Daily
    self.AddUniverse(self.FundamentalSelectionFunction)
    self.settings.daily_precise_end_time = False
    self.settings.minimum_order_margin_portfolio_percentage = 0.
    self.Schedule.On(self.DateRules.MonthEnd(market), self.TimeRules.BeforeMarketClose(market, 0), self.Selection)
def OnSecuritiesChanged(self, changes: SecurityChanges) -> None:
    for security in changes.AddedSecurities:
        security.SetFeeModel(CustomFeeModel())
        security.SetLeverage(self.leverage)
def FundamentalSelectionFunction(self, fundamental: List[Fundamental]) -> List[Symbol]:
    # update initial value and highest value
    for stock in fundamental:
        symbol = stock.Symbol
        
        if symbol in self.data:
            self.data[symbol].update(stock.AdjustedPrice)
    
    # rebalance monthly
    if not self.selection_flag:
        return Universe.Unchanged
    
    selected:List[Fundamental] = [
        x for x in fundamental if x.HasFundamentalData and x.Market == 'usa' and x.Price > self.min_share_price and \
        x.MarketCap != 0 and x.SecurityReference.ExchangeId in self.exchange_codes
    ]
    if len(selected) > self.fundamental_count:
        selected = [x for x in sorted(selected, key=self.fundamental_sorting_key, reverse=True)[:self.fundamental_count]]
    
    HTP:Dict[Fundamental, float] = {} # storing HTP values keyed by stocks symbols
    # warm up stock prices
    for stock in selected:
        symbol = stock.Symbol
        
        if symbol not in self.data:
            self.data[symbol] = SymbolData(self.period)
            history = self.History(symbol, self.period, Resolution.Daily)
            if history.empty:
                continue
            closes = history.loc[symbol].close
            for time, close in closes.items():
                self.data[symbol].update(close)
        
        if self.data[symbol].is_ready():
            # calculate stock's HTP value
            HTP[stock] = self.data[symbol].HTP()
    
    # make sure, there are enough stocks for decile selection    
    if len(HTP)  None:
    # rebalance monthly
    if not self.selection_flag:
        return
    self.selection_flag = False
    
    # trade execution
    portfolio:List[PortfolioTarget] = [
        PortfolioTarget(symbol, w) for symbol, w in self.weight.items() if symbol in data and data[symbol]
    ]
    self.SetHoldings(portfolio, True)
    self.weight.clear()
    
def Selection(self) -> None:
    self.selection_flag = True
    
class SymbolData():
def __init__(self, period: int):
    self._closes:RollingWindow = RollingWindow[float](period)
    
def update(self, close: float) -> None:
    self._closes.Add(close)
    
def is_ready(self) -> bool:
    return self._closes.IsReady
    
def HTP(self) -> float:
    closes:np.ndarray = np.array([x for x in self._closes][21:]) # skip last month
    highest_price:float = np.amax(closes)
    initial_price:float = closes[-1]
    
    return np.log(highest_price / initial_price)
    
# Custom fee model
class CustomFeeModel(FeeModel):
def GetOrderFee(self, parameters):
    fee = parameters.Security.Price * parameters.Order.AbsoluteQuantity * 0.00005
    return OrderFee(CashAmount(fee, "USD"))
