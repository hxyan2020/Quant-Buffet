# Original QuantConnect / library Python
# locale=zh slug="股票行业中的低波动率异象"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

from AlgorithmImports import *
from pandas.core.frame import DataFrame
from itertools import chain
class TheLowVolatilityAnomalyInEquitySectors(QCAlgorithm):
def Initialize(self):
    self.SetStartDate(2000, 1, 1)
    self.SetCash(100000)
    
    self.data:Dict[Symbol, SymbolData] = {}
    self.longs:List[List[Symbol]] = []
    self.period:int = 3 * 12 * 21 # Three years of daily returns
    self.quantile:int = 10
    self.leverage:int = 5
    
    market:Symbol = self.AddEquity('SPY', Resolution.Daily).Symbol
    self.fundamental_count:int = 500
    self.fundamental_sorting_key = lambda x: x.DollarVolume
    self.selection_flag:bool = False
    self.UniverseSettings.Resolution = Resolution.Daily
    self.Settings.MinimumOrderMarginPortfolioPercentage = 0.
    self.AddUniverse(self.FundamentalSelectionFunction)
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
        # Store monthly price.
        if symbol in self.data:
            self.data[symbol].update(stock.AdjustedPrice)
    if not self.selection_flag:
        return Universe.Unchanged
    selected:List[Fundamental] = [x for x in fundamental if x.HasFundamentalData and x.Market == 'usa']
    if len(selected) > self.fundamental_count:
        selected = [x for x in sorted(selected, key=self.fundamental_sorting_key, reverse=True)[:self.fundamental_count]]
    sectors = {}
    # Warmup price rolling windows.
    for stock in selected:
        symbol:Symbol = stock.Symbol
        if symbol not in self.data:
            self.data[symbol] = SymbolData(self.period)
            history:DataFrame = self.History(symbol, self.period, Resolution.Daily)
            if history.empty:
                self.Log(f"Not enough data for {symbol} yet.")
                continue
            closes:pd.Series = history.loc[symbol].close
            for time, close in closes.items():
                self.data[symbol].update(close)
        
        if self.data[symbol].is_ready():
            sector = stock.AssetClassification.MorningstarSectorCode
            if sector not in sectors:
                sectors[sector] = []
            sectors[sector].append(symbol)
    
    for sector, symbols in sectors.items():
        symbols_volatility:Dict[Symbol, float] = { symbol : self.data[symbol].volatility() for symbol in symbols}
        quantile:int = int(len(symbols_volatility) / self.quantile)
        sorted_by_volatility:List[Symbol] = [x[0] for x in sorted(symbols_volatility.items(), key=lambda item: item[1])]
        
        self.longs.append(sorted_by_volatility[:quantile]) # Least volatile decile of sector 
        
    return list(set(chain.from_iterable(self.longs)))
def OnData(self, data: Slice) -> None:
    if not self.selection_flag:
        return
    self.selection_flag = False
    
    # Trade execution
    self.Liquidate()
    
    total_sectors:int = len(self.longs)
    
    for long in self.longs:
        long_length:int = len(long)
        
        for symbol in long:
            if symbol in data and data[symbol]:
                self.SetHoldings(symbol, 1. / long_length / total_sectors)
            
    self.longs.clear()
    
def Selection(self) -> None:
    self.selection_flag = True
    
class SymbolData():
def __init__(self, period):
    self._closes:RollingWindow = RollingWindow[float](period)
    
def update(self, close: float) -> None:
    self._closes.Add(close)
    
def is_ready(self) -> bool:
    return self._closes.IsReady
    
def volatility(self) -> float:
    closes:np.ndarray = np.array(list(self._closes))
    returns:np.ndarray = (closes[:-1] - closes[1:]) / closes[1:]
    return np.std(returns)
    
class CustomFeeModel(FeeModel):
def GetOrderFee(self, parameters):
    fee = parameters.Security.Price * parameters.Order.AbsoluteQuantity * 0.00005
    return OrderFee(CashAmount(fee, "USD"))
