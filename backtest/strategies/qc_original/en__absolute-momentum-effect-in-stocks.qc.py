# Original QuantConnect / library Python
# locale=en slug="absolute-momentum-effect-in-stocks"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

from AlgorithmImports import *
from scipy import stats
from pandas.core.frame import DataFrame
class AbsoluteMomentumEffectStocks(QCAlgorithm):
def Initialize(self):
    self.SetStartDate(2000, 1, 1)
    self.SetCash(100000)
    market:Symbol = self.AddEquity('SPY', Resolution.Daily).Symbol
    
    self.period:int = 13
    self.quantile:int = 5
    self.leverage:int = 5
    self.exchange_codes:List[str] = ['NYS', 'NAS', 'ASE']
    self.required_yearly_return_period:int = 10 # Minimum of years to calculate distribution from.
    
    self.data:Dict[Symbol, SymbolData] = {} # Monthly price data.
    self.weight:Dict[Symbol, float] = {}
    
    self.fundamental_count:int = 500
    self.fundamental_sorting_key = lambda x: x.DollarVolume
    self.selection_flag:bool = False
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
    if not self.selection_flag:
        return Universe.Unchanged
    # Update the rolling window every month.
    for stock in fundamental:
        symbol:Symbol = stock.Symbol
        # Store monthly price.
        if symbol in self.data:
            self.data[symbol].update(stock.AdjustedPrice)

            # Add yearly performance.
            if self.data[symbol].is_ready():
                self.data[symbol].add_yearly_return(self.data[symbol].performance())
    selected:List[Fundamental] = [x for x in fundamental if x.HasFundamentalData and x.Market == 'usa' and \
        x.SecurityReference.ExchangeId in self.exchange_codes and x.MarketCap != 0]
    if len(selected) > self.fundamental_count:
        selected = [x for x in sorted(selected, key=self.fundamental_sorting_key, reverse=True)[:self.fundamental_count]]
    long:List[Fundamental] = []
    short:List[Fundamental] = []
    # Warmup price rolling windows.
    for stock in selected:
        symbol:Symbol = stock.Symbol
        if symbol not in self.data:
            self.data[symbol] = SymbolData(self.period, self.required_yearly_return_period)
            history:DataFrame = self.History(symbol, self.period*30, Resolution.Daily)
            if history.empty:
                self.Log(f"Not enough data for {symbol} yet.")
                continue
            closes:pd.Series = history.loc[symbol].close
            
            closes_len:int = len(closes.keys())
            # Find monthly closes.
            for index, time_close in enumerate(closes.items()):
                # index out of bounds check.
                if index + 1 = 0.9:
                long.append(stock)
            elif percentile  None:
    if not self.selection_flag:
        return
    self.selection_flag = False
    # Trade execution.
    portfolio:List[PortfolioTarget] = [
        PortfolioTarget(symbol, w) for symbol, w in self.weight.items() if symbol in data and data[symbol]
    ]
    self.SetHoldings(portfolio, True)
    self.weight.clear()
def selection(self) -> None:
    self.selection_flag = True
    
class SymbolData():
def __init__(self, period: int, required_yearly_return_period: int):
    self._prices:RollingWindow = RollingWindow[float](period)
    self._yearly_returns:List[float] = []
    self._required_yearly_return_period:int = required_yearly_return_period

def update(self, price: float) -> None:
    self._prices.Add(price)

def add_yearly_return(self, value: float) -> None:
    self._yearly_returns.append(value)
    
def is_ready(self) -> bool:
    return self._prices.IsReady

def yearly_returns_ready(self) -> bool:
    return len(self._yearly_returns) >= self._required_yearly_return_period
    
# Yearly performance, one month skipped.
def performance(self) -> float:
    return (self._prices[1] / self._prices[self._prices.Count - 1] - 1)

# Custom fee model.
class CustomFeeModel(FeeModel):
def GetOrderFee(self, parameters):
    fee = parameters.Security.Price * parameters.Order.AbsoluteQuantity * 0.00005
    return OrderFee(CashAmount(fee, "USD"))
