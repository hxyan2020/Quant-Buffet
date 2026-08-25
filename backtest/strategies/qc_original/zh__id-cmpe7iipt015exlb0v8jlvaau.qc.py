# Original QuantConnect / library Python
# locale=zh slug="股票市场中的盈利公告季节性效应"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

from AlgorithmImports import *
from data_tools import TradeManager
import numpy as np
from collections import deque
from pandas.tseries.offsets import BDay
from dateutil.relativedelta import relativedelta
from typing import List, Dict
#endregion
class EarningsAnnouncementSeasonalityEffectinEquities(QCAlgorithm):
def Initialize(self) -> None:
    self.SetStartDate(2010, 1, 1)
    self.SetCash(100_000)
    self.period: int = 20
    self.long_symbols: int = 10
    self.short_symbols: int = 10
    self.holding_period: int = 4
    self.leverage: int = 5
    self.quantile: int = 20
    self.prev_month: int = -1
    self.prev_month_year: int = -1
    symbol: Symbol = self.AddEquity('SPY', Resolution.Daily).Symbol
    self.long: List[Symbol] = []
    self.short: List[Symbol] = []
   
    self.eps: Dict[Symbol, deque] = {}
    self.earnings: Dict[datetime.date, List[str]] = {} 
    self.eps_data: Dict[int, Dict[int, Dict[str, Dict[datetime.date, float]]]] = {}
    # parse earnings dataset - Source: https://www.nasdaq.com/market-activity/earnings
    earnings_data: str = self.Download('data.quantpedia.com/backtesting_data/economic/earnings_dates_eps.json')
    earnings_data_json: List[dict] = json.loads(earnings_data)
    
    for obj in earnings_data_json:
        date: datetime.date = datetime.strptime(obj['date'], '%Y-%m-%d').date()
        year: int = date.year
        month: int = date.month
        self.earnings[date] = []
        
        for stock_data in obj['stocks']:
            ticker: str = stock_data['ticker']
            self.earnings[date].append(ticker)
            if stock_data['eps'] == '':
                continue
            if year not in self.eps_data:
                self.eps_data[year] = {}
            if month not in self.eps_data[year]:
                self.eps_data[year][month] = {}
            if ticker not in self.eps_data[year][month]:
                self.eps_data[year][month][ticker] = {}
            self.eps_data[year][month][ticker][date] = float(stock_data['eps'])
    # equally weighted brackets for traded symbols
    # hodling period 3 days + 1 day due to QC midnight offset (00:00 trading)
    self.trade_manager: TradeManager = TradeManager(self, self.long_symbols, self.short_symbols, self.holding_period)
    
    self.selection_flag: bool = False
    self.settings.daily_precise_end_time = False
    self.Settings.MinimumOrderMarginPortfolioPercentage = 0.
    self.UniverseSettings.Resolution = Resolution.Daily
    self.AddUniverse(self.FundamentalSelectionFunction)
    self.Schedule.On(self.DateRules.MonthStart(symbol), self.TimeRules.AfterMarketOpen(symbol), self.Selection)
def OnSecuritiesChanged(self, changes: SecurityChanges) -> None:
    for security in changes.AddedSecurities:
        security.SetFeeModel(CustomFeeModel())
        security.SetLeverage(self.leverage)

def FundamentalSelectionFunction(self, fundamental: List[Fundamental]) -> List[Symbol]:
    if not self.selection_flag: 
        return Universe.Unchanged
    self.selection_flag = False
    prev_month_date: datetime.date = (self.Time - relativedelta(months=1)).date()
    self.prev_month_year: int = prev_month_date.year
    self.prev_month: int = prev_month_date.month
    if self.prev_month_year not in self.eps_data or self.prev_month not in self.eps_data[self.prev_month_year]:
        return Universe.Unchanged
    
    # select stocks, which has earning in previous month
    stocks_with_prev_month_eps: Dict[str, Dict[datetime.date, float]] = self.eps_data[self.prev_month_year][self.prev_month]
    selected: List[Fundamental] = [x for x in fundamental if x.Symbol.Value in stocks_with_prev_month_eps]
    for stock in selected: 
        symbol: Symbol = stock.Symbol
        ticker: str = symbol.Value
        
        # store eps data
        if symbol not in self.eps:
            self.eps[symbol] = deque(maxlen=self.period)
        
        # get all stock's eps from previous month
        stock_prev_month_eps: Dict[datetime.date, float] = self.eps_data[self.prev_month_year][self.prev_month][ticker]
        # get the date of the latest eps in previous month
        stock_latest_eps_date:datetime.date = list(stock_prev_month_eps.keys())[-1]
        # store stock's latest eps date in previous month and it's eps value
        data_eps: List[datetime.date, float] = [stock_latest_eps_date, stock_prev_month_eps[stock_latest_eps_date]]
        self.eps[symbol].append(data_eps)
    
    # Earn rank calc
    earn_rank: Dict[Symbol, float] = {}
    for symbol in self.eps:
        if len(self.eps[symbol]) != self.eps[symbol].maxlen:
            continue
        relevant_earnings_dates:List[datetime.date] = [self.eps[symbol][-4][0], self.eps[symbol][-8][0], \
            self.eps[symbol][-12][0] ,self.eps[symbol][-16][0], self.eps[symbol][-20][0]]
            
        # stock with potencial upcoming month earnings
        eps_months: List[int] = [x.month for x in relevant_earnings_dates]
        if self.Time.month in eps_months:
            # rank the 20 quarters of earnings data from largest to smallest
            ranked_earnings: List[Tuple[datetime.date, float]] = [i for i in sorted(list(self.eps[symbol]), key=lambda x: x[1], reverse=True)]
            
            ranks: List[int] = [ranked_earnings.index(earnings_data)+1 for earnings_data in ranked_earnings if earnings_data[0] in relevant_earnings_dates]
            
            earn_rank[symbol] = np.mean(ranks)
                
    if len(earn_rank)  None:
    earnings_date: datetime.date = (self.Time + BDay(1)).date()
    
    if earnings_date in self.earnings:
        for symbol in self.long + self.short:
            if symbol not in data or not data[symbol]:
                continue
            ticker:str = symbol.Value
            # symbol has earnings in 1 day
            if ticker not in self.earnings[earnings_date]:
                continue
            if symbol in self.long:
                self.trade_manager.Add(symbol, True)
            else:
                self.trade_manager.Add(symbol, False)
    
    self.trade_manager.TryLiquidate()
    
def Selection(self) -> None:
    self.long.clear()
    self.short.clear()
    self.selection_flag = True
# Custom fee model
class CustomFeeModel(FeeModel):
def GetOrderFee(self, parameters: OrderFeeParameters) -> OrderFee:
    fee: float = parameters.Security.Price * parameters.Order.AbsoluteQuantity * 0.00005
    return OrderFee(CashAmount(fee, "USD"))
