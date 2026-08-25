# Original QuantConnect / library Python
# locale=zh slug="周五晚上公告的财报后漂移"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

import numpy as np
from AlgorithmImports import *
from collections import deque
from dateutil.relativedelta import relativedelta
from typing import List, Dict, Tuple
from numpy import isnan
class PostEarningsAnnouncementDriftFridayEveningAnnouncers(QCAlgorithm):
def Initialize(self):
    self.SetStartDate(2000, 1, 1)
    self.SetCash(100000)
    self.period:int = 13
    self.leverage:int = 5
    self.min_share_price:int = 2
    
    # EPS quarterly data.
    self.eps_data:Dict[Symbol, List[Tuple[float]]] = {}
    
    market:Symbol = self.AddEquity('SPY', Resolution.Daily).Symbol
    # Surprise data count needed to count standard deviation.
    self.surprise_period:int = 4
    self.earnings_surprise:Dict[Symbol, List[float]] = {}
    
    # SUE history for previous year used for statistics.
    self.sue_previous_year:List[float] = []
    self.sue_actual_year:List[float] = []
    
    # Trenching.
    self.holding_period:int = 12
    self.managed_queue:List[RebalanceQueueItem] = []
    self.market_cap_threshold: float = 100_000_000
    
    # Last fundamental stock price
    self.last_price:Dict[Symbol, float] = {}
    
    self.month:int = 12
    self.fundamental_sorting_key = lambda x: x.DollarVolume
    self.fundamental_count:int = 1000
    self.selection_flag:bool = False
    self.UniverseSettings.Resolution = Resolution.Daily
    self.AddUniverse(self.FundamentalSelectionFunction)
    self.Settings.MinimumOrderMarginPortfolioPercentage = 0.
    self.Schedule.On(self.DateRules.MonthEnd(market), self.TimeRules.AfterMarketOpen(market), self.Selection)
    self.settings.daily_precise_end_time = False
def OnSecuritiesChanged(self, changes: SecurityChanges) -> None:
    for security in changes.AddedSecurities:
        security.SetFeeModel(CustomFeeModel())
        security.SetLeverage(self.leverage)
    
def FundamentalSelectionFunction(self, fundamental: List[Fundamental]) -> List[Symbol]:
    if not self.selection_flag:
        return Universe.Unchanged

    selected:List[Fundamental] = [
        x for x in fundamental if x.HasFundamentalData and x.Price > self.min_share_price and x.Market == 'usa' and not\
        isnan(x.EarningReports.BasicEPS.ThreeMonths) and (x.EarningReports.BasicEPS.ThreeMonths != 0) and x.MarketCap > self.market_cap_threshold
    ]
    if len(selected) > self.fundamental_count:
        selected = [x for x in sorted(selected, key=self.fundamental_sorting_key, reverse=True)[:self.fundamental_count]]
    
    for stock in selected:
        self.last_price[stock.Symbol] = stock.AdjustedPrice
    
    # Stocks with last month's earnings.
    last_month_date:datetime = self.Time - timedelta(self.Time.day)
    filered_fundamental:List[Symbol] = [x for x in selected if (x.EarningReports.FileDate.Value.year == last_month_date.year and x.EarningReports.FileDate.Value.month == last_month_date.month)]    
    
    sue_data:Dict[Symbol, float] = {}
    
    for stock in filered_fundamental:
        symbol:Symbol = stock.Symbol
        
        # Store eps data.
        if symbol not in self.eps_data:
            self.eps_data[symbol] = deque(maxlen = self.period)
        data:Tuple[float] = (stock.EarningReports.FileDate.Value.date(), stock.EarningReports.BasicEPS.ThreeMonths)
        # NOTE: Handles duplicate values. QC fundamental contains duplicated stocks in some cases.
        if data not in self.eps_data[symbol]:
            self.eps_data[symbol].append(data)
            
        if len(self.eps_data[symbol]) == self.eps_data[symbol].maxlen:
            recent_eps_data:Tuple[float] = self.eps_data[symbol][-1]
            
            year_range:range = range(self.Time.year - 3, self.Time.year)
            
            last_month_date:datetime = recent_eps_data[0] + relativedelta(months = -1)
            next_month_date:datetime = recent_eps_data[0] + relativedelta(months = 1)
            month_range:List[int] = [last_month_date.month, recent_eps_data[0].month, next_month_date.month]
            # Earnings with todays month number 4 years back.
            seasonal_eps_data:List[Tuple[float]] = [x for x in self.eps_data[symbol] if x[0].month in month_range and x[0].year in year_range]
            if len(seasonal_eps_data) != 3: continue
            
            # Make sure we have a consecutive seasonal data. Same months with one year difference.
            year_diff:float = np.diff([x[0].year for x in seasonal_eps_data])
            if all(x == 1 for x in year_diff):
                seasonal_eps:List[float] = [x[1] for x in seasonal_eps_data]
                diff_values:List[float] = np.diff(seasonal_eps)
                drift:float = np.average(diff_values)
                
                # SUE calculation.
                last_earnings:Tuple[float] = seasonal_eps[-1]
                expected_earnings:Tuple[float] = last_earnings + drift
                actual_earnings:Tuple[float] = recent_eps_data[1]
                # Store sue value with earnigns date.
                earnings_surprise:Tuple[float] = actual_earnings - expected_earnings
                if symbol not in self.earnings_surprise:
                    self.earnings_surprise[symbol] = deque()
                else:
                    # Surprise data is ready.
                    if len(self.earnings_surprise[symbol]) >= self.surprise_period:
                        earnings_surprise_std:float = np.std(self.earnings_surprise[symbol])
                        sue:float = earnings_surprise / earnings_surprise_std
                        
                        # Store sue in this years's history of friday's earnings.
                        self.sue_actual_year.append(sue)
                
                        # Only stocks with last month's earnings on friday.
                        if stock.EarningReports.FileDate.Value.weekday() == 4:
                            sue_data[symbol] = sue
                
                self.earnings_surprise[symbol].append(earnings_surprise)
    
    long:List[Symbol] = []
    short:List[Symbol] = []
    
    # Wait until we have history data for previous year.
    if len(sue_data) != 0 and len(self.sue_previous_year) != 0: 
        positive_sue_values:List[float] = [x for x in self.sue_previous_year if x > 0]
        positive_sue_median:float = np.median(positive_sue_values)
        
        negative_sue_values:List[float] = [x for x in self.sue_previous_year if x  0 and x[1] >= positive_sue_median]
        short = [x[0] for x in sue_data.items() if x[1]  None:
    if not self.selection_flag:
        return
    self.selection_flag = False
    # Trade execution
    remove_item:Union[None, RebalanceQueueItem] = None
    
    # Rebalance portfolio
    for item in self.managed_queue:
        if item.holding_period == self.holding_period:
            for symbol, quantity in item.long_symbol_q + item.short_symbol_q:
                if symbol in data and data[symbol]:
                    if self.Securities[symbol].Price != 0 and self.Securities[symbol].IsTradable:
                        self.MarketOrder(symbol, -quantity)
                        
            remove_item = item
            
        elif item.holding_period == 0:
            open_long_symbol_q:List[Tuple[Symbol, float]] = []
            open_short_symbol_q:List[Tuple[Symbol, float]] = []
            
            for symbol, quantity in item.long_symbol_q + item.short_symbol_q:
                if symbol in data and data[symbol]:
                    if self.Securities[symbol].Price != 0 and self.Securities[symbol].IsTradable:
                        self.MarketOrder(symbol, quantity)
                        open_long_symbol_q.append((symbol, quantity))
                        
            # Only opened orders will be closed        
            item.long_symbol_q = open_long_symbol_q
            item.short_symbol_q = open_short_symbol_q
            
        item.holding_period += 1
        
    # We need to remove closed part of portfolio after loop. Otherwise it will miss one item in self.managed_queue.
    if remove_item:
        self.managed_queue.remove(remove_item)
    
def Selection(self) -> None:
    self.selection_flag = True
    
    # Save yearly history.
    if self.month == 12:
        self.sue_previous_year = list(self.sue_actual_year)
        self.sue_actual_year.clear()
    self.month += 1
    if self.month > 12:
        self.month = 1
class RebalanceQueueItem():
def __init__(self, long_symbol_q:List[Tuple[Symbol, float]], short_symbol_q:List[Tuple[Symbol, float]]):
    # symbol/quantity collections
    self.long_symbol_q:List[Tuple[Symbol, float]] = long_symbol_q  
    self.short_symbol_q:List[Tuple[Symbol, float]] = short_symbol_q
    self.holding_period:int = 0
# Custom fee model.
class CustomFeeModel(FeeModel):
def GetOrderFee(self, parameters):
    fee = parameters.Security.Price * parameters.Order.AbsoluteQuantity * 0.00005
    return OrderFee(CashAmount(fee, "USD"))
