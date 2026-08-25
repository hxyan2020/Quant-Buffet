# Original QuantConnect / library Python
# locale=zh slug="长期市净率-pb-ratio-效应与动量策略结合在股票中的应"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

from numpy import average
from AlgorithmImports import *
class LongTermPBRatio(QCAlgorithm):
def Initialize(self):
    self.SetStartDate(2000, 1, 1)
    self.SetCash(100000)
    market:Symbol = self.AddEquity('SPY', Resolution.Daily).Symbol
    self.bm_period:int = 10 * 12
    self.momentum_period:int = 13
    self.quantile:int = 5
    self.leverage:int = 5
    self.exchange_codes:List[str] = ['NYS', 'NAS', 'ASE']
    # Daily close data.
    self.data:Dict[Symbol, SymbolData] = {}
    self.long:List[Symbol] = []
    self.fundamental_count:int = 3000
    self.fundamental_sorting_key = lambda x: x.MarketCap
    self.selection_flag:bool = False
    self.UniverseSettings.Resolution = Resolution.Daily
    self.Settings.MinimumOrderMarginPortfolioPercentage = 0.
    self.AddUniverse(self.FundamentalSelectionFunction)
    self.Schedule.On(self.DateRules.MonthEnd(market), self.TimeRules.BeforeMarketClose(market), self.Selection)
    
    self.settings.daily_precise_end_time = False
    
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
            self.data[symbol].update_price(stock.AdjustedPrice)
    selected:List[Fundamental] = [x for x in fundamental if x.HasFundamentalData and x.Market == 'usa' and x.SecurityReference.ExchangeId in self.exchange_codes and \
        not np.isnan(x.ValuationRatios.BookValuePerShare) and x.ValuationRatios.BookValuePerShare > 0 and x.CompanyReference.IsREIT == 0]
    if len(selected) > self.fundamental_count:
    	selected = [x for x in sorted(selected, key=self.fundamental_sorting_key, reverse=True)[:self.fundamental_count]]
    bm_return_data:Dict[Symbol, Tuple[float, float]] = {}
    # Warmup price rolling windows.
    for stock in selected:
        symbol:Symbol = stock.Symbol
        
        if symbol not in self.data:
            self.data[symbol] = SymbolData(symbol, self, self.momentum_period, self.bm_period)
            history = self.History(symbol, self.momentum_period*30, Resolution.Daily)
            if history.empty:
                self.Log(f"Not enough data for {symbol} yet.")
                continue
            closes = history.loc[symbol].close
            
            closes_len = len(closes.keys())
            # Find monthly closes.
            for index, time_close in enumerate(closes.items()):
                # index out of bounds check.
                if index + 1 = self.quantile * 2:
        sorted_by_bm:List = sorted(bm_return_data.items(), key=lambda x: x[1][0], reverse=True)
        quantile:int = int(len(sorted_by_bm) / self.quantile)
        top_by_bm = [x for x in sorted_by_bm[:quantile]]
        
        sorted_by_ret:List = sorted(top_by_bm, key=lambda x: bm_return_data[x[0]][1], reverse=True)
        half = int(len(sorted_by_ret) / 2)
        self.long = [x[0] for x in sorted_by_ret[:half]]
    return self.long
def OnData(self, data: Slice) -> None:
    # Rebalance once a month.
    if not self.selection_flag:
        return
    self.selection_flag = False
    # Trade execution.
    portfolio:List[PortfolioTarget] = [PortfolioTarget(symbol, 1/len(self.long)) for symbol in self.long if symbol in data and data[symbol]]
    self.SetHoldings(portfolio, True)
    self.long.clear()
    
def Selection(self) -> None:
    self.selection_flag = True
    
class SymbolData():
def __init__(self, symbol, algorithm, momentum_period, book_period):
    self._price:RollingWindow = RollingWindow[float](momentum_period)
    self._book_value:RollingWindow = RollingWindow[float](book_period)

def update_book_value(self, value: float) -> None:
    self._book_value.Add(value)

def book_values_are_ready(self) -> bool:
    return self._book_value.IsReady

def update_price(self, price: float) -> None:
    self._price.Add(price)
    
def performance_is_ready(self) -> bool:
    return self._price.IsReady
    
def get_last_price(self) -> float:
    return self._price[0]
# 12 month momentum, one month skipped.
def performance(self) -> float:
    return self._price[1] / self._price[self._price.Count - 1] - 1
# Custom fee model.
class CustomFeeModel(FeeModel):
def GetOrderFee(self, parameters):
    fee = parameters.Security.Price * parameters.Order.AbsoluteQuantity * 0.00005
    return OrderFee(CashAmount(fee, "USD"))
