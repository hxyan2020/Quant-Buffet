# Original QuantConnect / library Python
# locale=zh slug="收益的季节性与信息周期"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

from AlgorithmImports import *
from dateutil.relativedelta import relativedelta
from pandas.core.frame import DataFrame
class ReturnSeasonalityAndInformationCycle(QCAlgorithm):
def Initialize(self):
    self.SetStartDate(2000, 1, 1)
    self.SetCash(100000)
    
    self.data:Dict[Symbol, RollingWindow] = {}
    self.weight:Dict[Symbol, float] = {}
    self.seasonal_data:Dict[Symbol, SymbolData] = {}
    
    self.period:int = 21
    self.seasonal_period:int = 5
    self.require_file_dates:int = 3
    self.leverage:int = 5
    
    market:Symbol = self.AddEquity('SPY', Resolution.Daily).Symbol
    self.fundamental_count:int = 3000
    self.fundamental_sorting_key = lambda x: x.MarketCap
    self.selection_flag:int = False
    self.UniverseSettings.Resolution = Resolution.Daily
    self.settings.daily_precise_end_time = False
    self.Settings.MinimumOrderMarginPortfolioPercentage = 0.
    self.AddUniverse(self.FundamentalSelectionFunction)
    self.Schedule.On(self.DateRules.MonthStart(market), self.TimeRules.AfterMarketOpen(market), self.Selection)
    
def OnSecuritiesChanged(self, changes: SecurityChanges) -> None:
    for security in changes.AddedSecurities:
        security.SetFeeModel(CustomFeeModel())
        security.SetLeverage(self.leverage)
            
def FundamentalSelectionFunction(self, fundamental: List[Fundamental]) -> List[Symbol]:
    # Update the rolling window every day.
    for stock in fundamental:
        symbol:Symbol = stock.Symbol
        # Store daily price.
        if symbol in self.data:
            self.data[symbol].Add(stock.AdjustedPrice)
    if not self.selection_flag:
        return Universe.Unchanged
    
    selected:List[Fundamental] = [x for x in fundamental if x.HasFundamentalData and x.Market == 'usa' and x.MarketCap != 0]
    if len(selected) > self.fundamental_count:
        selected = [x for x in sorted(selected, key=self.fundamental_sorting_key, reverse=True)[:self.fundamental_count]]
    stock_file_dates:Dict[Fundamental, int] = {}
    avg_performances:Dict[Fundamental, float] = {}
    current_year:int = self.Time.year
    current_month_year:str = str(self.Time.month) + '-' + str(current_year)
    # Warmup price rolling windows.
    for stock in selected:
        symbol:Symbol = stock.Symbol
        stock_file_date:datetime.date = stock.EarningReports.FileDate
        if symbol not in self.data:
            self.data[symbol] = RollingWindow[float](self.period)
            
            history:DataFrame = self.History(symbol, self.period, Resolution.Daily)
            if history.empty:
                self.Log(f"Not enough data for {symbol} yet")
                continue
            closes:pd.Series = history.loc[symbol].close
            for time, close in closes.items():
                self.data[symbol].Add(close)
        
        # calculate metrics
        if self.data[symbol].IsReady:
            if symbol not in self.seasonal_data:
                self.seasonal_data[symbol] = SymbolData(self.seasonal_period)
            
            performance:float = self.data[symbol][0] / self.data[symbol][self.data[symbol].Count - 1] - 1
            
            self.seasonal_data[symbol].months_perfs[current_month_year] = performance
            self.seasonal_data[symbol].file_dates[current_month_year] = stock_file_date # Check value
            
            if self.seasonal_data[symbol].last_year != current_year:
                self.seasonal_data[symbol].last_year = current_year
                self.seasonal_data[symbol].update(current_year)
                
            if self.seasonal_data[symbol].is_ready():
                seasonal_file_dates:int = 1
                seasonal_perfs:List[float] = [performance]
                look_date:datetime.date = self.Time.date()
                
                while len(seasonal_perfs) = 0 and stock in stock_file_dates and stock_file_dates[stock] >= self.require_file_dates:
            long.append(stock)
        elif avg  None:
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
    self._years:RollingWindow = RollingWindow[int](period)
    self.months_perfs = {}
    self.file_dates = {}
    self.last_year = -1
    
def update(self, year: int) -> None:
    self._years.Add(year)
    
def is_ready(self) -> bool:
    return self._years.IsReady
    
# Custom fee model
class CustomFeeModel(FeeModel):
def GetOrderFee(self, parameters):
    fee = parameters.Security.Price * parameters.Order.AbsoluteQuantity * 0.00005
    return OrderFee(CashAmount(fee, "USD"))
