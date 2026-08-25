# Original QuantConnect / library Python
# locale=zh slug="财报公告期间的对比效应"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

from AlgorithmImports import *
import numpy as np
from collections import deque
from pandas.tseries.offsets import BDay
from dateutil.relativedelta import relativedelta
from typing import Dict, List
#endregion
class ContrastEffectDuringtheEarningsAnnouncements(QCAlgorithm):
def Initialize(self):
    self.SetStartDate(2010, 1, 1)   # scheduled earnings data starts in 2010
    self.SetCash(100000)
    self.leverage:int = 5
    self.seasonal_eps_count:int = 3
    self.holding_period:int = 2
    self.surprise_period:int = 4
    self.period:int = 13
    # trenching
    self.managed_queue:List[RebalanceQueueItem] = []
    
    # surprise data count needed to count standard deviation
    self.earnings_surprise:Dict[Symbol, deque] = {}
       
    self.last_price:Dict[Symbol, float] = {}
    
    # SUE and EAR history for previous quarter used for statistics
    self.surprise_history_previous:deque = deque()
    self.surprise_history_actual:deque = deque()
    self.eps:Dict[Symbol, deque] = {}
    data = self.AddEquity('SPY', Resolution.Daily)
    data.SetFeeModel(CustomFeeModel())
    data.SetLeverage(self.leverage)
    self.symbol:Symbol = data.Symbol
    # Earning data parsing.
    self.earnings_data:Dict[datetime.date, Dict[str, float]] = {}
    self.tickers:Set(str) = set() 
    earnings_data:str = self.Download('data.quantpedia.com/backtesting_data/economic/earnings_dates_eps.json')
    earnings_data_json:list[dict] = json.loads(earnings_data)
    
    for obj in earnings_data_json:
        date:datetime.date = datetime.strptime(obj['date'], '%Y-%m-%d').date()
        self.earnings_data[date] = {}
        
        for stock_data in obj['stocks']:
            ticker:str = stock_data['ticker']
            if stock_data['eps'] != '':
                self.earnings_data[date][ticker] = float(stock_data['eps'])
                
            self.tickers.add(ticker)
    
    self.month:int = 0
    self.settings.daily_precise_end_time = False
    self.Settings.MinimumOrderMarginPortfolioPercentage = 0.
    self.UniverseSettings.Resolution = Resolution.Daily
    self.AddUniverse(self.FundamentalSelectionFunction)
    self.Schedule.On(self.DateRules.MonthStart(self.symbol), self.TimeRules.AfterMarketOpen(self.symbol), self.Selection)
def OnSecuritiesChanged(self, changes: SecurityChanges) -> None:
    for security in changes.AddedSecurities:
        security.SetFeeModel(CustomFeeModel())
        security.SetLeverage(self.leverage)

def FundamentalSelectionFunction(self, fundamental: List[Fundamental]) -> List[Symbol]:
    self.last_price.clear()
    for equity in fundamental:
        symbol:Symbol = equity.Symbol
        ticker:str = symbol.Value
        if ticker in self.tickers or symbol == self.symbol:
            self.last_price[symbol] = equity.AdjustedPrice
    selected:List[FineFundamental] = [x for x in fundamental if x.MarketCap != 0]
    # make sure there are some stocks with yesterday's earnings
    yesterday:datetime.date = (self.Time - BDay(1)).date()
    if yesterday not in self.earnings_data:
        return Universe.Unchanged
    tickers_with_yesterday_earnings:List[str] = list(self.earnings_data[yesterday].keys())
    # stocks with yesterday's earnings
    filtered_fine:List[Fundamental] = [x for x in selected if x.Symbol.Value in tickers_with_yesterday_earnings] 
    # SUE data
    sue_data:Dict[Symbol, float] = {}
    
    for stock in filtered_fine:
        symbol:Symbol = stock.Symbol
        ticker:str = symbol.Value
        # store eps data
        if symbol not in self.eps:
            self.eps[symbol] = deque(maxlen = self.period)
        data:List[datetime.date, float] = [yesterday, self.earnings_data[yesterday][ticker]]
        self.eps[symbol].append(data)
        
        # consecutive EPS data
        if len(self.eps[symbol]) == self.eps[symbol].maxlen:
            recent_eps_data:float = self.eps[symbol][-1]
            
            year_range:range = range(self.Time.year - 3, self.Time.year)
            
            last_month_date:datetime.date = recent_eps_data[0] - relativedelta(months=1)
            next_month_date:datetime.date = recent_eps_data[0] + relativedelta(months=1)
            month_range:List[int] = [last_month_date.month, recent_eps_data[0].month, next_month_date.month]
            # earnings with todays month number 4 years back
            seasonal_eps_data:List[List[datetime.date, float]] = [x for x in self.eps[symbol] \
                if x[0].month in month_range and x[0].year in year_range]
            if len(seasonal_eps_data) != self.seasonal_eps_count: continue
            
            # Make sure we have a consecutive seasonal data. Same months with one year difference.
            year_diff:np.array = np.diff([x[0].year for x in seasonal_eps_data])
            if all(x == 1 for x in year_diff):
                seasonal_eps:List[float] = [x[1] for x in seasonal_eps_data]
                diff_values:np.array = np.diff(seasonal_eps)
                drift:float = np.average(diff_values)
                
                # SUE calculation
                last_earnings:float = seasonal_eps[-1]
                expected_earnings:float = last_earnings + drift
                actual_earnings:float = recent_eps_data[1]
                # store sue value with earnigns date
                earnings_surprise:float = actual_earnings - expected_earnings

                if symbol not in self.earnings_surprise:
                    self.earnings_surprise[symbol] = deque(maxlen=self.surprise_period)
                elif len(self.earnings_surprise[symbol]) >= self.surprise_period:
                    earnings_surprise_std:float = np.std(self.earnings_surprise[symbol])
                    sue:float = earnings_surprise / earnings_surprise_std
                    
                    sue_data[symbol] = sue
                self.earnings_surprise[symbol].append(earnings_surprise)
    
    if len(sue_data) == 0:
        return Universe.Unchanged
    
    long_symbol_q:List[Symbol, float] = []
    short_symbol_q:List[Symbol, float] = []
    
    # store total yesterday's surprise in this month's history
    yesterdays_surprises:float = sum([x[1] for x in sue_data.items()])
    # wait until there is surprise history data for previous three months
    if len(self.surprise_history_previous) != 0:
        # find symbols with next day scheduled earnings
        earnings_date = (self.Time + BDay(1)).date()
        if earnings_date in self.earnings_data:
            surprise_values:List = [x for x in self.surprise_history_previous]
        
            top_surprise_percentile:float  = np.percentile(surprise_values, 75)
            bottom_surprise_percentile:float = np.percentile(surprise_values, 25)
            
            traded_symbols:List[List[Symbol, float]] = []
            for stock in selected:
                symbol:Symbol = stock.Symbol
                ticker:str = symbol.Value
                # stock has earnings in 1 day
                if ticker in self.earnings_data[earnings_date]:
                    traded_symbols.append([symbol, stock.MarketCap])
            
            if len(traded_symbols) != 0:
                if self.symbol in self.last_price:
                    total_market_cap:float = sum([x[1] for x in traded_symbols])
                    
                    stocks_w:float = self.Portfolio.TotalPortfolioValue / self.holding_period
                    spy_quantity:float = self.Portfolio.TotalPortfolioValue / self.holding_period / self.last_price[self.symbol]
                    
                    if yesterdays_surprises > top_surprise_percentile:
                        long_symbol_q = [(x[0], np.floor(stocks_w * (x[1] / total_market_cap) / self.last_price[x[0]])) for x in traded_symbols]
                        
                        # Quantity instead of weight is used in case of SPY.
                        short_symbol_q = [(self.symbol, -spy_quantity)]
                        
                    elif yesterdays_surprises  None:
    # trade execution
    remove_item:Union[RebalanceQueueItem, None] = None
    
    # rebalance portfolio
    for item in self.managed_queue:
        if item.holding_period == self.holding_period:
            for symbol, quantity in item.symbol_q:
                self.MarketOrder(symbol, -quantity)
                        
            remove_item = item
            
        elif item.holding_period == 0:
            open_symbol_q:List[List[Symbol, float]] = []
            
            for symbol, quantity in item.symbol_q:
                if symbol in data and data[symbol]:
                    self.MarketOrder(symbol, quantity)
                    open_symbol_q.append((symbol, quantity))
                        
            # Only opened orders will be closed        
            item.symbol_q = open_symbol_q
            
        item.holding_period += 1
        
    # remove closed part of portfolio after loop
    # otherwise it will miss one item in self.managed_queue
    if remove_item:
        self.managed_queue.remove(remove_item)
        
def Selection(self) -> None:        
    # every three months
    if self.month % 3 == 0:
        # save history
        self.surprise_history_previous = [x for x in self.surprise_history_actual]
        self.surprise_history_actual.clear()
    
    self.month += 1
        
class RebalanceQueueItem:
def __init__(self, symbol_q):
    # symbol/quantity collections
    self.symbol_q:List[List[Symbol, float]] = symbol_q  
    self.holding_period:int = 0
    
# Custom fee model
class CustomFeeModel(FeeModel):
def GetOrderFee(self, parameters):
    fee = parameters.Security.Price * parameters.Order.AbsoluteQuantity * 0.00005
    return OrderFee(CashAmount(fee, "USD"))
