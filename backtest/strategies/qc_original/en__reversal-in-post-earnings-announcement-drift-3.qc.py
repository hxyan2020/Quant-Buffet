# Original QuantConnect / library Python
# locale=en slug="reversal-in-post-earnings-announcement-drift-3"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

from data_tools import SymbolData, CustomFeeModel, TradeManager
from AlgorithmImports import *
import numpy as np
from collections import deque
from typing import Dict, List
from pandas.core.frame import DataFrame
from pandas.tseries.offsets import BDay
from dateutil.relativedelta import relativedelta
class ReversalPostEarningsAnnouncementDrift(QCAlgorithm):
def Initialize(self) -> None:
    self.SetStartDate(2009, 1, 1) # earnings dates starts in 2010
    self.SetCash(100_000)
    self.long_symbols: int = 10
    self.short_symbols: int = 10
    self.holding_period: int = 2
    self.lookback_period: int = 3
    
    self.leverage: int = 5
    self.ear_period: int = 30
    self.prev_month_year: int = -1
    self.prev_month: int = -1
    self.percentiles: List[int] = [10, 90]
            
    self.data: Dict[Symbol, SymbolData] = {}
    # EAR last quarter data
    self.ear_data: Dict[Symbol, List[datetime.date, float]] = {}
    self.earnings_data: Dict[datetime.date, List[str]] = {}
    self.eps_data: Dict[int, Dict[int, Dict[str, Dict[datetime.date, float]]]] = {}
    
    self.first_date: Union[datetime.date, None] = None
    earnings_data: str = self.Download('data.quantpedia.com/backtesting_data/economic/earnings_dates_eps.json')
    earnings_data_json: List[dict] = json.loads(earnings_data)
    
    for obj in earnings_data_json:
        date: datetime.date = datetime.strptime(obj['date'], '%Y-%m-%d').date()
        year: int = date.year
        month: int = date.month
        self.earnings_data[date] = []
        if not self.first_date: self.first_date = date
        
        for stock_data in obj['stocks']:
            ticker: str = stock_data['ticker']
            self.earnings_data[date].append(ticker)
            if stock_data['eps'] == '':
                continue
            if year not in self.eps_data:
                self.eps_data[year] = {}
            if month not in self.eps_data[year]:
                self.eps_data[year][month] = {}
            if ticker not in self.eps_data[year][month]:
                self.eps_data[year][month][ticker] = {}
            self.eps_data[year][month][ticker][date] = float(stock_data['eps'])
    
    # EAR quarters history
    self.current_quarter_ears: List[float] = []
    self.previous_quarter_ears: List[float] = []
    
    # equally weighted brackets for traded symbols - 10 symbols long and short, 2 days of holding
    self.trade_manager: TradeManager = TradeManager(self, self.long_symbols, self.short_symbols, self.holding_period)
    self.symbol: Symbol = self.AddEquity('SPY', Resolution.Daily).Symbol
    
    self.selection_flag: bool = False
    self.store_sales_data_flag: bool = True
    self.sales_growth_sort_flag: bool = False
    self.Settings.MinimumOrderMarginPortfolioPercentage = 0.
    self.settings.daily_precise_end_time = False
    self.UniverseSettings.Resolution = Resolution.Daily
    self.AddUniverse(self.FundamentalSelectionFunction)
    self.Schedule.On(self.DateRules.MonthStart(self.symbol), self.TimeRules.AfterMarketOpen(self.symbol), self.Selection)
def OnSecuritiesChanged(self, changes: SecurityChanges) -> None:
    for security in changes.AddedSecurities:
        security.SetFeeModel(CustomFeeModel())
        security.SetLeverage(self.leverage)

def FundamentalSelectionFunction(self, fundamental: List[Fundamental]) -> List[Symbol]:
    # update daily prices
    for stock in fundamental:
        symbol: Symbol = stock.Symbol
        
        if symbol in self.data:
            self.data[symbol].update(self.Time, stock.AdjustedPrice)
    
    # monthly selection
    if not self.selection_flag:
        return Universe.Unchanged
    self.selection_flag = False
    prev_month_date: datetime.date = (self.Time - relativedelta(months=1)).date()
    self.prev_month_year: int = prev_month_date.year
    self.prev_month: int = prev_month_date.month
    if self.prev_month_year not in self.eps_data or self.prev_month not in self.eps_data[self.prev_month_year]:
        return Universe.Unchanged
    # select every stock, which had earnings in previous month
    stocks_with_prev_month_eps: Dict[str, Dict[datetime.date, float]] = self.eps_data[self.prev_month_year][self.prev_month]
    selected_symbols: List[Symbol] = [x.Symbol for x in fundamental if x.Symbol.Value in stocks_with_prev_month_eps]
    
    for symbol in selected_symbols + [self.symbol]:
        if symbol not in self.data:   
            # warm up stock prices
            self.data[symbol] = SymbolData(self.ear_period)
            history: DataFrame = self.History(symbol, self.ear_period, Resolution.Daily)
            if history.empty:
                continue
            
            closes: Series = history.loc[symbol].close
            for time, close in closes.items():
                self.data[symbol].update(self.Time, close)
    for symbol in selected_symbols:
        if not self.data[symbol].is_ready():
            continue
        ticker: str = symbol.Value
        # get all stock's eps from previous month
        stock_prev_month_eps: Dict[datetime.date, float] = self.eps_data[self.prev_month_year][self.prev_month][ticker]
        # get the date of the latest eps in previous month
        stock_latest_eps_date: datetime.date = list(stock_prev_month_eps.keys())[-1]
        # get 4 days around earnings and calculate EAR
        date_from: datetime = stock_latest_eps_date - BDay(2)
        date_to: datetime = stock_latest_eps_date + BDay(1)
        
        market_return: float = self.data[self.symbol].get_prices([date_from, date_to])
        stock_return: float = self.data[symbol].get_prices([date_from, date_to])
        
        # check if returns are ready 
        if market_return and stock_return:
            ear: float = stock_return - market_return
            ear_data: List[datetime.date] = (stock_latest_eps_date, ear)
            self.ear_data[symbol] = ear_data
                
            # store ear in this month's history
            self.current_quarter_ears.append(ear)
    
    # check if there are any symbols, which can be traded                
    if len(self.ear_data) == 0:
        return Universe.Unchanged
    
    # return symbols from self.ear_data, because they will be traded
    return list(self.ear_data.keys())
def OnData(self, data: Slice) -> None:
    # open trades on earnings day
    date_to_lookup: datetime.date = self.Time.date()
    # if there is no earnings data yet
    if date_to_lookup = (self.Time - relativedelta(months=self.lookback_period)).date():
                if symbol in data and data[symbol]:
                    if self.ear_data[symbol][1] >= top_ear_decile:
                        self.trade_manager.Add(symbol, True)
                        symbols_to_delete.append(symbol)
                    elif self.ear_data[symbol][1]  None:
    self.selection_flag = True
    
    if self.Time.month % 3 == 0:
        # store previous quarter's history
        self.previous_quarter_ears = [x for x in self.current_quarter_ears]
        self.current_quarter_ears.clear()
