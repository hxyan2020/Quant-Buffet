# Original QuantConnect / library Python
# locale=en slug="macroeconomic-announcement-beta-strategy"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

from AlgorithmImports import *
import numpy as np
from pandas.tseries.offsets import BDay
from scipy import stats
from data_tools import CustomFeeModel, SymbolData
from typing import List, Dict
from pandas.core.frame import DataFrame
from pandas.core.series import Series
#endregion
class MacroeconomicAnnouncementBeta(QCAlgorithm):
def Initialize(self) -> None:
    self.SetStartDate(2000, 1, 1)
    self.SetCash(100000)
    
    self.leverage: int = 5
    self.quantile: int = 10
    self.period: int = 5 * 12
    self.daily_period: int = 21
    self.days_offset: int = 1
    self.data: Dict[Symbol, SymbolData] = {}
    self.selected_symbols: List[Symbol] = []
    self.market: Symbol = self.AddEquity('SPY', Resolution.Daily).Symbol
    self.data[self.market] = SymbolData(self.period)
    self.WarmUpSymbolPrices(self.market)
    
    csv_string_file: str = self.Download('data.quantpedia.com/backtesting_data/economic/economic_announcements.csv')
    dates: List[str] = csv_string_file.split('\r\n')
    before_announcement_dates: List[datetime.date] = [(datetime.strptime(x, '%Y-%m-%d') - BDay(self.days_offset)).date() for x in dates]
    self.fundamental_count: int = 500
    self.fundamental_sorting_key = lambda x: x.DollarVolume
    self.sort_flag: bool = False
    self.selection_flag: bool = False
    self.settings.daily_precise_end_time = False
    self.Settings.MinimumOrderMarginPortfolioPercentage = 0.
    self.UniverseSettings.Resolution = Resolution.Daily
    self.AddUniverse(self.FundamentalSelectionFunction)
    self.Schedule.On(self.DateRules.On(before_announcement_dates), self.TimeRules.AfterMarketOpen(self.market), self.DayBeforeAnnouncement)
    self.Schedule.On(self.DateRules.MonthEnd(self.market), self.TimeRules.AfterMarketOpen(self.market), self.Selection)
def OnSecuritiesChanged(self, changes: SecurityChanges) -> None:
    for security in changes.AddedSecurities:
        security.SetFeeModel(CustomFeeModel())
        security.SetLeverage(self.leverage)
def FundamentalSelectionFunction(self, fundamental: List[Fundamental]) -> List[Symbol]:
    # monthly selection
    if not self.selection_flag:
        return Universe.Unchanged
    self.selection_flag = False
    
    selected: List[fundamental] = []
    self.selected_symbols.clear()
    for stock in fundamental:
        symbol: Symbol = stock.Symbol
        
        if symbol in self.data and self.data[symbol].is_last_month_price_ready():
            self.data[symbol].update_monthly_return(stock.AdjustedPrice)
        if stock.HasFundamentalData:
            selected.append(stock)
    
    if len(selected) > self.fundamental_count:
        selected = [x for x in sorted(selected, key=self.fundamental_sorting_key, reverse=True)[:self.fundamental_count]]
    
    for stock in selected:
        symbol: Symbol = stock.Symbol
        if symbol not in self.data:
            self.data[symbol] = SymbolData(self.period)
            self.WarmUpSymbolPrices(symbol)
        if self.data[symbol].is_ready():
            self.selected_symbols.append(symbol)
    return self.selected_symbols     

def OnData(self, data: Slice) -> None:
    self.Liquidate()
    
    # sort one day before earnings annoucement
    if not self.sort_flag or len(self.selected_symbols) == 0:
        return
    self.sort_flag = False

    # make sure there is n years of SPY monthly returns history
    if not self.data[self.market].is_ready():
        return
    market_monthly_returns: List[float] = self.data[self.market].get_monthly_returns()
    
    beta: Dict[Symbol, float] = {}
    for symbol in self.selected_symbols:
        if symbol in data and data[symbol]:
            stock_monthly_returns: List[float] = self.data[symbol].get_monthly_returns()
            
            # linear regression - X = market returns, Y = stock returns
            slope, intercept, r_value, p_value, std_err = stats.linregress(market_monthly_returns, stock_monthly_returns)
            beta[symbol] = slope
        
    # check if there are enough stocks for selection
    if len(beta)  None:
    history: DataFrame = self.History([symbol], self.daily_period * self.period, Resolution.Daily)
    if history.empty:
        return
    
    closes: Series = history.loc[symbol].close
    closes_grouped: Series = closes.groupby(pd.Grouper(freq='M')).last()
    for close in closes_grouped:
        self.data[symbol].update_monthly_return(close)
def Selection(self) -> None:
    self.selection_flag = True
    
def DayBeforeAnnouncement(self) -> None:
    self.sort_flag = True
