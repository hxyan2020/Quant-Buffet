# Original QuantConnect / library Python
# locale=en slug="post-loss-profit-announcement-drift-in-stocks"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

import numpy as np
from AlgorithmImports import *
import data_tools
from collections import deque
from pandas.tseries.offsets import BDay
from dateutil.relativedelta import relativedelta
from typing import Dict, List, Deque
from numpy import isnan
class SwitchingBetweenValueMomentum(QCAlgorithm):
def Initialize(self) -> None:
    self.SetStartDate(2000, 1, 1)
    self.SetCash(100_000)
    self.period: int = 13
    self.eps_data: Dict[Symbol, Deque[datetime.date]] = {} # EPS quarterly data
    
    self.coarse_count: int = 500
    self.leverage: int = 5
    self.min_share_price: int = 5
    self.symbol: Symbol = self.AddEquity('SPY', Resolution.Daily).Symbol
    
    self.long: List[Symbol] = []
    self.short: List[Symbol] = []
    
    self.last_selected: List[str] = []     # This year's selected stocks.
    
    # Surprise data count needed to count standard deviation.
    self.surprise_period: int = 4
    self.earnings_surprise: Dict[Symbol, float] = {}
    # SUE history for previous quarter used for statistics.
    self.sue_history_previous: Deque[float] = deque()
    self.sue_history_actual: Deque[float] = deque()
    
    # 50 equally weighted brackets for traded symbols.
    self.trade_manager: data_tools.TradeManager = data_tools.TradeManager(self, 15, 15, 60)
    
    self.month: int = 12
    self.selection_flag: bool = False
    self.rebalance_flag: bool = False
    self.Settings.MinimumOrderMarginPortfolioPercentage = 0.
    self.settings.daily_precise_end_time = False
    self.UniverseSettings.Resolution = Resolution.Daily
    self.AddUniverse(self.FundamentalSelectionFunction)
    
    self.Schedule.On(self.DateRules.MonthEnd(self.symbol), self.TimeRules.AfterMarketOpen(self.symbol), self.Selection)
def OnSecuritiesChanged(self, changes: SecurityChanges) -> None:
    for security in changes.AddedSecurities:
        security.SetFeeModel(data_tools.CustomFeeModel())
        security.SetLeverage(self.leverage)
def FundamentalSelectionFunction(self, fundamental: List[Fundamental]) -> List[Symbol]:
    # At the begining of the year pick whole new set of stocks.
    if self.selection_flag: 
        self.selection_flag = False
        selected: List[Fundamental] = [x for x in fundamental if x.HasFundamentalData and x.Price > self.min_share_price and x.Market == 'usa' and not isnan(x.EarningReports.BasicEPS.ThreeMonths) and (x.EarningReports.BasicEPS.ThreeMonths != 0)]
        if len(selected) > self.coarse_count:
            selected = sorted(selected, key=lambda x: x.DollarVolume, reverse=True)[:self.coarse_count]
        
        self.last_selected = [x.Symbol.Value for x in selected]
    # During the year, filter just already picked stocks.
    # Stock with yesterdays earnings.
    filtered_fundamental: List[Fundamental] = [x for x in fundamental if x.Symbol.Value in self.last_selected and x.EarningReports.FileDate.Value.year != 1  and (self.Time.date() == (x.EarningReports.FileDate.Value + BDay(1)).date())]      
    symbol_sue: Dict[Symbol, float] = {}     # SUE for this day.
    
    for stock in filtered_fundamental:
        symbol: Symbol = stock.Symbol
        
        # Store eps data.
        if symbol not in self.eps_data:
            self.eps_data[symbol] = deque(maxlen = self.period)
        data: Tuple[float] = (stock.EarningReports.FileDate.Value.date(), stock.EarningReports.BasicEPS.ThreeMonths)
        # NOTE: Handles duplicate values. QC fine contains duplicated stocks in some cases.
        if data not in self.eps_data[symbol]:
            self.eps_data[symbol].append(data)
            
        if len(self.eps_data[symbol]) == self.eps_data[symbol].maxlen:
            recent_eps_data = self.eps_data[symbol][-1]
            
            year_range: List[int] = range(self.Time.year - 3, self.Time.year)
            
            last_month_date: datetime.date = recent_eps_data[0] + relativedelta(months = -1)
            next_month_date: datetime.date = recent_eps_data[0] + relativedelta(months = 1)
            month_range: List[datetime.date] = [last_month_date.month, recent_eps_data[0].month, next_month_date.month]
            # Earnings with todays month number 4 years back.
            seasonal_eps_data: List[float] = [x for x in self.eps_data[symbol] if x[0].month in month_range and x[0].year in year_range]
            if len(seasonal_eps_data) != 3: continue
            
            # Make sure we have a consecutive seasonal data. Same months with one year difference.
            year_diff:np.ndarray = np.diff([x[0].year for x in seasonal_eps_data])
            if all(x == 1 for x in year_diff):
                seasonal_eps: List[float] = [x[1] for x in seasonal_eps_data]
                diff_values: np.ndarray = np.diff(seasonal_eps)
                drift: float = np.average(diff_values)
                
                # SUE calculation.
                last_earnings: float = seasonal_eps[-1]
                expected_earnings: float = last_earnings + drift
                actual_earnings: float = recent_eps_data[1]
                # Store sue value with earnigns date.
                earnings_surprise: float = actual_earnings - expected_earnings
                if symbol not in self.earnings_surprise:
                    self.earnings_surprise[symbol] = deque(maxlen = self.surprise_period)
                else:
                    # Surprise data is ready.
                    if len(self.earnings_surprise[symbol]) >= self.surprise_period:
                        earnings_surprise_std: float = np.std(self.earnings_surprise[symbol])
                        sue: float = earnings_surprise / earnings_surprise_std
                        symbol_sue[symbol] = sue
                        
                        self.sue_history_actual.append(sue)
                
                self.earnings_surprise[symbol].append(earnings_surprise)
                
    if len(symbol_sue) != 0:
        # Wait until we have history data for previous three months.
        if len(self.sue_history_previous) != 0:
            # Sort by SUE.
            sue_values: List[float] = [x for x in self.sue_history_previous]
            top_sue_decile: float  = np.percentile(sue_values, 90)
            bottom_sue_decile: float = np.percentile(sue_values, 10)
        
            self.long = [x[0] for x in symbol_sue.items() if x[1] >= top_sue_decile]
            self.short = [x[0] for x in symbol_sue.items() if x[1]  None:
    self.selection_flag = True
    # Every three months.    
    if self.month % 3 == 0:
        # Save previous month history.
        self.sue_history_previous = [x for x in self.sue_history_actual]
        self.sue_history_actual.clear()
    self.month += 1
    if self.month > 12:
        self.month = 1
        
def OnData(self, data: Slice) -> None:
    if not self.rebalance_flag:
        return
    self.rebalance_flag = False
    
    # Open new trades.
    for i, portfolio in enumerate([self.short, self.long]):
        for symbol in portfolio:
            if symbol in data and data[symbol]:
                self.trade_manager.Add(symbol, bool(i))
            
    self.trade_manager.TryLiquidate()
    
    self.long.clear()
    self.short.clear()
