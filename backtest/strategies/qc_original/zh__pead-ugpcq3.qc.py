# Original QuantConnect / library Python
# locale=zh slug="拆股后漂移与pead异常的结合"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

from AlgorithmImports import *
import data_tools
import numpy as np
from collections import deque
import dateutil.relativedelta
from dateutil.relativedelta import relativedelta
from typing import List, Dict, Set, Deque
from numpy import isnan
#endregion
class PostSplitDriftCombinedWithPEADAnomaly(QCAlgorithm):
def Initialize(self) -> None:
    self.SetStartDate(2011, 1, 1)
    self.SetCash(100_000)
    
    self.symbol: Symbol = self.AddEquity('SPY', Resolution.Daily).Symbol
    
    # Set of unique symbols to trade.
    self.long: Set = set()
    self.short: Set = set()
    
    self.leverage: int = 5
    self.period: int = 13
    self.long_symbols: int = 20
    self.short_symbols: int = 20
    self.holding_period: int = 90
    self.percentiles: List[int] = [20, 80]
    self.eps_data: Dict[Symbol, Deque[datetime, float]] = {}
    # Import earnigns data.
    self.earnings_data: Dict[datetime, str] = {}
    # Import splits data
    self.splits_data: Dict[str, datetime.date] = {}
    
    # Surprise data count needed to count standard deviation.
    self.surprise_period: int = 4
    self.earnings_surprise: Dict[Deque[float]] = {}
    
    # SUE history for previous quarter used for statistics.
    self.sue_history_previous: Deque[float] = deque()
    self.sue_history_actual: Deque[float] = deque()
    
    self.first_date: Union[None, datetime.date] = None
    earnings_data: str = self.Download('data.quantpedia.com/backtesting_data/economic/earnings_dates_eps.json')
    earnings_data_json: List[dict] = json.loads(earnings_data)
    
    for obj in earnings_data_json:
        date: datetime.date = datetime.strptime(obj['date'], "%Y-%m-%d").date()
        self.earnings_data[date] = []
        if not self.first_date: self.first_date = date
        for stock_data in obj['stocks']:
            ticker: str = stock_data['ticker']
            self.earnings_data[date].append(ticker)
            
    csv_string_file: str = self.Download('data.quantpedia.com/backtesting_data/economic/splits.csv')
    lines: str = csv_string_file.split('\r\n')
    for line in lines:
        if line == '':
            continue
        line_split: str = line.split(';')
        symbol: str = line_split[0]
        
        self.splits_data[symbol] = []
        
        for i in range(1, len(line_split)):
            if line_split[i] is not '':
                date: datetime = datetime.strptime(line_split[i], '%m/%d/%Y').date()
                self.splits_data[symbol].append(date)
    
    # 70 equally weighted brackets for traded symbols. - 20 symbols long, 20 symbols short, 90 days of holding.
    self.trade_manager: data_tools.TradeManager = data_tools.TradeManager(self, self.long_symbols, self.short_symbols, self.holding_period)
    
    self.month: int = 12
    self.selection_flag: bool = True
    self.Settings.MinimumOrderMarginPortfolioPercentage = 0.
    self.settings.daily_precise_end_time = False
    self.UniverseSettings.Resolution = Resolution.Daily
    self.AddUniverse(self.FundamentalSelectionFunction)
    self.Schedule.On(self.DateRules.MonthStart(self.symbol), self.TimeRules.AfterMarketOpen(self.symbol), self.Selection)
def OnSecuritiesChanged(self, changes: SecurityChanges) -> None:
    for security in changes.AddedSecurities:
        security.SetFeeModel(data_tools.CustomFeeModel())
        security.SetLeverage(self.leverage)

def FundamentalSelectionFunction(self, fundamental: List[Fundamental]) -> List[Symbol]:
    if not self.selection_flag:
        return Universe.Unchanged
    self.selection_flag = False
    
    # S&P 500 universe from self.splits_data tickers.
    selected: List[Fundamental] = [x for x in fundamental if x.HasFundamentalData and x.Market == 'usa' \
                            and not isnan(x.EarningReports.BasicEPS.ThreeMonths) and x.EarningReports.BasicEPS.ThreeMonths != 0 \
                            and not isnan(x.EarningReports.FileDate.Value.year) and x.EarningReports.FileDate.Value.year != 1 \
                            and x.Symbol.Value in self.splits_data]
    # SUE data.
    sue_data: Dict[Symbol, float] = {}
    for stock in selected:
        symbol: Symbol = stock.Symbol
        # Store eps data.
        if symbol not in self.eps_data:
            self.eps_data[symbol] = deque(maxlen = self.period)
        data: Tuple[datetime.date, float] = (stock.EarningReports.FileDate.Value.date(), stock.EarningReports.BasicEPS.ThreeMonths)
        # NOTE: Handles duplicate values. QC fine contains duplicated stocks in some cases.
        if data not in self.eps_data[symbol]:
            self.eps_data[symbol].append(data)
            
        if len(self.eps_data[symbol]) == self.eps_data[symbol].maxlen:
            recent_eps_data: datetime = self.eps_data[symbol][-1]
            
            year_range: List[int] = range(self.Time.year - 3, self.Time.year)
            
            last_month_date: datetime.date = recent_eps_data[0] + relativedelta(months = -1)
            next_month_date: datetime.date = recent_eps_data[0] + relativedelta(months = 1)
            month_range: List[int] = [last_month_date.month, recent_eps_data[0].month, next_month_date.month]
            # Earnings with todays month number 4 years back.
            seasonal_eps_data: List[Tuple[datetime.date, float]] = [x for x in self.eps_data[symbol] if x[0].month in month_range and x[0].year in year_range]
            if len(seasonal_eps_data) != 3:
                continue
            
            # Make sure we have a consecutive seasonal data. Same months with one year difference.
            year_diff: np.ndarray = np.diff([x[0].year for x in seasonal_eps_data])
            if all(x == 1 for x in year_diff):
                seasonal_eps: List[float] = [x[1] for x in seasonal_eps_data]
                diff_values: List[float] = np.diff(seasonal_eps)
                drift: float = np.average(diff_values)
                
                # SUE calculation.
                last_earnings: float = seasonal_eps[-1]
                expected_earnings: float = last_earnings + drift
                actual_earnings: float = recent_eps_data[1]
                # Store sue value with earnigns date.
                earnings_surprise: float = actual_earnings - expected_earnings
                if symbol not in self.earnings_surprise:
                    self.earnings_surprise[symbol] = deque()
                else:
                    # Surprise data is ready.
                    if len(self.earnings_surprise[symbol]) >= self.surprise_period:
                        earnings_surprise_std:float = np.std(self.earnings_surprise[symbol])
                        sue: float = earnings_surprise / earnings_surprise_std

                        sue_data[symbol] = sue
                            
                        # Store pair in this month's history.
                        self.sue_history_actual.append(sue)
                self.earnings_surprise[symbol].append(earnings_surprise)
            
    if len(sue_data) != 0: 
        # Wait until we have history data for previous three months.
        if len(self.sue_history_previous) != 0:
            # Sort by SUE
            top_sue_quintile: float = np.percentile(self.sue_history_previous, self.percentiles[1])
            bottom_sue_quintile: float = np.percentile(self.sue_history_previous, self.percentiles[0])
            self.long = [x[0] for x in sue_data.items() if x[1] >= top_sue_quintile]
            self.short = [x[0] for x in sue_data.items() if x[1]  None:
    # Liquidate opened symbols after 90 days.
    self.trade_manager.TryLiquidate()
    current_date: datetime.date = (self.Time).date()
    three_months_ago: datetime.date = (current_date - dateutil.relativedelta.relativedelta(months=3))
    date_to_lookup: datetime.date = (self.Time - timedelta(days=3)).date()
    
    # If there is no earnings data yet.
    if date_to_lookup  bool:
    for split_date in self.splits_data[symbol]:
        if date_from  None:
    self.selection_flag = True
    
    # Every three months.    
    if self.month % 3 == 0:
        # Save previous month history.
        self.sue_history_previous = [x for x in self.sue_history_actual]
        self.sue_history_actual.clear()
    self.month += 1
    if self.month > 12:
        self.month = 1
        
# Custom fee model
class CustomFeeModel(FeeModel):
def GetOrderFee(self, parameters: OrderFeeParameters) -> OrderFee:
    fee: float = parameters.Security.Price * parameters.Order.AbsoluteQuantity * 0.00005
    return OrderFee(CashAmount(fee, "USD"))
