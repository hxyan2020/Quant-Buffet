# Original QuantConnect / library Python
# locale=zh slug="股票的预期偏度和动量"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

from AlgorithmImports import *
import numpy as np
#endregion
class ExpectedSkewnessMomentum(QCAlgorithm):
def Initialize(self):
    self.SetStartDate(2010, 1, 1)
    self.SetCash(100000)
    market:Symbol = self.AddEquity('SPY', Resolution.Daily).Symbol
    
    self.fundamental_count:int = 1000
    self.fundamental_sorting_key = lambda x: x.DollarVolume
    
    # Monthly close data.
    self.data:Dict[Symbol, SymbolData] = {}
    self.period:int = 12 * 21
    self.min_share_price:float = 1.
    self.quantile:int = 10
    self.leverage:int = 10
    self.exchange_codes:List[str] = ['NYS', 'NAS', 'ASE']
    
    self.long:List[Symbol] = []
    self.short:List[Symbol] = []
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
    # Update the rolling window every day.
    for stock in fundamental:
        symbol:Symbol = stock.Symbol
        # Store monthly price.
        if symbol in self.data:
            self.data[symbol].update(stock.AdjustedPrice)
    if not self.selection_flag:
        return Universe.Unchanged
    
    selected:List[Fundamental] = [
        x for x in fundamental if x.HasFundamentalData and x.Market == 'usa' and x.SecurityReference.ExchangeId in self.exchange_codes and \
        x.Price > self.min_share_price and x.MarketCap != 0
    ]
    
    if len(selected) > self.fundamental_count:
        selected = [x for x in sorted(selected, key=self.fundamental_sorting_key, reverse=True)[:self.fundamental_count]]
        
    performance_max_return:Dict[Symbol, Tuple[float, float]] = {}
    # Warmup price rolling windows.
    for stock in selected:
        symbol:Symbol = stock.Symbol
        if symbol not in self.data:
            self.data[symbol] = SymbolData(self.period)
            history = self.History(symbol, self.period, Resolution.Daily)
            if history.empty:
                self.Log(f"Not enough data for {symbol} yet")
                continue
            closes = history.loc[symbol].close
            for time, close in closes.items():
                self.data[symbol].update(close)
        
        if self.data[symbol].is_ready():
            performance_max_return[symbol] = (self.data[symbol].performance(), self.data[symbol].max_performance_last_month())
    
    if len(performance_max_return) >= self.quantile * 2:
        sorted_by_max_perf:List = sorted(performance_max_return.items(), key = lambda x: x[1][1], reverse = True)
        quantile:int = int(len(sorted_by_max_perf) / self.quantile)
        high_by_daily_perf:List = [x for x in sorted_by_max_perf[:quantile]]
        low_by_daily_perf:List = [x for x in sorted_by_max_perf[-quantile:]]
    
        # Most negatively skewed winners.
        sorted_by_performance:List = sorted(low_by_daily_perf, key = lambda x: x[1][0], reverse = True)
        quantile = int(len(sorted_by_performance) / self.quantile)
        self.long = [x[0] for x in sorted_by_performance[:quantile]]
        # Most positively skewed losers.
        sorted_by_performance:List = sorted(high_by_daily_perf, key = lambda x: x[1][0], reverse = True)
        quantile = int(len(sorted_by_performance) / self.quantile)
        self.short = [x[0] for x in sorted_by_performance[-quantile:]]
    
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

def max_performance_last_month(self) -> float:
    closes:np.ndarray = np.array(list(self._price)[:21])
    daily_returns:np.ndarray = closes[:-1] / closes[1:] - 1
    return max(daily_returns)
    
# Custom fee model.
class CustomFeeModel(FeeModel):
def GetOrderFee(self, parameters):
    fee = parameters.Security.Price * parameters.Order.AbsoluteQuantity * 0.00005
    return OrderFee(CashAmount(fee, "USD"))
