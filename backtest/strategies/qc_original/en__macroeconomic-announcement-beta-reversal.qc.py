# Original QuantConnect / library Python
# locale=en slug="macroeconomic-announcement-beta-reversal"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

from AlgorithmImports import *
import numpy as np
from pandas.tseries.offsets import BDay
from scipy import stats
from typing import List, Dict
from pandas.core.frame import DataFrame
from pandas.core.series import Series
#endregion
class MacroeconomicAnnouncementBetaReversal(QCAlgorithm):
def Initialize(self) -> None:
    self.SetStartDate(2000, 1, 1)
    self.SetCash(100000)
    
    self.market: Symbol = self.AddEquity("SPY", Resolution.Daily).Symbol
    self.period: int = 5 * 12
    self.daily_period: int = 21
    self.quantile: int = 10
    self.leverage: int = 5
    
    self.data: Dict[Symbol, SymbolData] = {}
    self.selected_symbols: List[Symbol] = []
    self.long: List[Symbol] = []
    self.short: List[Symbol] = []
    csv_string_file: str = self.Download('data.quantpedia.com/backtesting_data/economic/economic_announcements.csv')
    dates: List[str] = csv_string_file.split('\r\n')
    announcement_dates: List[datetime.date] = [datetime.strptime(x, "%Y-%m-%d") for x in dates]
    sort_dates: List[datetime.date] = [(x + BDay(1)).date() for x in announcement_dates]
    liquidation_dates: List[datetime.date] = [(x + BDay(2)).date() for x in announcement_dates]
    
    self.fundamental_count: int = 500
    self.fundamental_sorting_key = lambda x: x.DollarVolume
    self.selection_flag: bool = False
    self.rebalance_flag: bool = False
    self.settings.daily_precise_end_time = False
    self.Settings.MinimumOrderMarginPortfolioPercentage = 0.
    self.UniverseSettings.Resolution = Resolution.Daily
    self.AddUniverse(self.FundamentalSelectionFunction)
    self.Schedule.On(self.DateRules.MonthEnd(self.market), self.TimeRules.At(0,0), self.Selection)
    self.Schedule.On(self.DateRules.On(sort_dates), self.TimeRules.At(0,0), self.Rebalance)
    self.Schedule.On(self.DateRules.On(liquidation_dates), self.TimeRules.At(0,0), self.Liquidation)
def OnSecuritiesChanged(self, changes: SecurityChanges) -> None:
    for security in changes.AddedSecurities:
        security.SetFeeModel(CustomFeeModel())
        security.SetLeverage(self.leverage)
def FundamentalSelectionFunction(self, fundamental: List[Fundamental]) -> List[Symbol]:
    # monthly selection
    if not self.selection_flag:
        return Universe.Unchanged
    self.selection_flag = False
    
    # calculate monthly return
    for stock in fundamental:
        symbol = stock.Symbol
        
        # check if current stock have last month price
        if symbol in self.data and self.data[symbol].last_month_price:
            self.data[symbol].update_monthly_return(stock.AdjustedPrice)
    
    selected: List[Fundamental] = [x for x in fundamental if x.HasFundamentalData]
    if len(selected) > self.fundamental_count:
        selected = [x for x in sorted(selected, key=self.fundamental_sorting_key, reverse=True)[:self.fundamental_count]]
    
    # Store monthly return for every stock selected this month.
    for stock in selected + [self.market]:
        if stock == self.market:
            symbol = stock
        else:
            symbol: Symbol = stock.Symbol
        if symbol in self.data:
            continue
        
        self.data[symbol] = SymbolData(self.period)
        history: DataFrame = self.History([symbol], self.daily_period * self.period, Resolution.Daily)
        
        if history.empty:
            self.Log(f"Not enough data for {symbol} yet")
            continue
        
        closes: Series = history.loc[symbol].close
        closes_grouped: Series = closes.groupby(pd.Grouper(freq='M')).last()
        for close in closes_grouped:
            self.data[symbol].update_monthly_return(close)
    
    # get stocks, which have ready monthly returns
    self.selected_symbols = [x.Symbol for x in selected if self.data[x.Symbol].is_ready() and x.Symbol != self.market]        
    
    return self.selected_symbols

def OnData(self, data: Slice) -> None:
    if not self.rebalance_flag:
        return
    self.rebalance_flag = False
    # there has to be at least one selected symbol and market returns has to be ready
    if len(self.selected_symbols) == 0 or not self.data[self.market].is_ready():
        return
    
    market_monthly_returns: List[float] = [x for x in self.data[self.market].monthly_returns]
    
    beta: Dict[Symbol, float] = {}
    for symbol in self.selected_symbols:
        stock_monthly_returns: List[float] = [x for x in self.data[symbol].monthly_returns]
        
        # Linear regression - X = market returns, Y = stock returns
        slope, intercept, r_value, p_value, std_err = stats.linregress(market_monthly_returns, stock_monthly_returns)
        beta[symbol] = slope
    
    # check if there are enough data for decile selection    
    if len(beta)  None:
    self.rebalance_flag = True
def Selection(self) -> None:
    self.selection_flag = True
    
def Liquidation(self) -> None:
    self.Liquidate()
class SymbolData():
def __init__(self, period: int) -> None:
    self.monthly_returns: RollingWindow = RollingWindow[float](period)
    self.last_month_price = 0
    
def update_monthly_return(self, price: float) -> None:
    if self.last_month_price != 0:
        monthly_return: float = (price - self.last_month_price) / self.last_month_price
        self.monthly_returns.Add(monthly_return)
    self.last_month_price = price
    
def is_ready(self) -> bool:
    return self.monthly_returns.IsReady
# Custom fee model.
class CustomFeeModel(FeeModel):
def GetOrderFee(self, parameters: OrderFeeParameters) -> OrderFee:
    fee: float = parameters.Security.Price * parameters.Order.AbsoluteQuantity * 0.00005
    return OrderFee(CashAmount(fee, "USD"))
