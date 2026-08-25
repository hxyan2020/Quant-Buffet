# Original QuantConnect / library Python
# locale=en slug="公告后收益效应"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

from AlgoLib import *
import numpy as np
from collections import deque
from pandas.tseries.offsets import BDay
from dateutil.relativedelta import relativedelta
from typing import Dict, List, Tuple, Deque

class PostEarningsAnnouncementEffectAlgorithm(XXX):

def Initialize(self):
    self.SetStartDate(2010, 1, 1)
    self.SetCash(100000)

    self.earnings_surprise: Dict[Symbol, float] = {}
    self.min_seasonal_eps_period: int = 4
    self.min_surprise_period: int = 4
    self.leverage: int = 5
    self.percentile_range: List[int] = [80, 20]
    
    self.long_positions: List[Symbol] = []
    
    self.sue_ear_history_previous: List[Tuple[float, float]] = []
    self.sue_ear_history_actual: List[Tuple[float, float]] = []
    
    self.eps_by_ticker: Dict[str, float] = {}
    self.price_data_with_date: Dict[Symbol, Deque[float]] = {}
    self.price_period: int = 63

    self.market: Symbol = self.AddEquity('SPY', Resolution.Daily).Symbol
    self.price_data_with_date[self.market] = deque(maxlen=self.price_period)

    self.first_date: Union[datetime.date, None] = None
    earnings_data: str = self.Download('data.quantpedia.com/backtesting_data/economic/earnings_dates_eps.json')
    earnings_data_json: list[dict] = json.loads(earnings_data)
    
    for obj in earnings_data_json:
        date: datetime.date = datetime.strptime(obj['date'], "%Y-%m-%d").date()
        
        if not self.first_date: self.first_date = date

        for stock_data in obj['stocks']:
            ticker: str = stock_data['ticker']

            if stock_data['eps'] == '':
                continue

            if ticker not in self.eps_by_ticker:
                self.eps_by_ticker[ticker] = {}
            
            self.eps_by_ticker[ticker][date] = float(stock_data['eps'])

    self.month: int = 12
    self.selection_flag: bool = False
    self.Settings.MinimumOrderMarginPortfolioPercentage = 0.
    self.UniverseSettings.Resolution = Resolution.Daily
    self.AddUniverse(self.FundamentalSelectionFunction)
    self.Schedule.On(self.DateRules.MonthStart(self.market), self.TimeRules.AfterMarketOpen(self.market), self.Selection)

def OnSecuritiesChanged(self, changes: SecurityChanges) -> None:
    for security in changes.AddedSecurities:
        security.SetFeeModel(CustomFeeModel())
        security.SetLeverage(self.leverage)
    
    for security in changes.RemovedSecurities:
        symbol: Symbol = security.Symbol
        if symbol in self.earnings_surprise:
            del self.earnings_surprise[symbol]

def FundamentalSelectionFunction(self, fundamental: List[Fundamental]) -> List[Symbol]:
    for stock in fundamental:
        symbol: Symbol = stock.Symbol

        if symbol in self.price_data_with_date:
            self.price_data_with_date[symbol].append((self.Time.date(), stock.AdjustedPrice))
    
    if not self.selection_flag:
        return Universe.Unchanged
    self.selection_flag = False
    
    selected: List[Symbol] = [x.Symbol for x in fundamental if x.Symbol.Value in self.eps_by_ticker]
    
    sue_ear: Dict[Symbol, float] = {}
    
    current_date: datetime.date = self.Time.date()
    prev_three_months: datetime = current_date - relativedelta(months=3)
    
    for symbol in selected:
        ticker: str = symbol.Value
        recent_eps_data: Union[None, datetime.date] = None

        if symbol not in self.price_data_with_date:
            self.price_data_with_date[symbol] = deque(maxlen=self.price_period)
            history: DataFrame = self.History(symbol, self.price_period, Resolution.Daily)
            if history.empty:
                self.Log(f"Not enough data for {symbol} yet.")
                continue
            closes: Series = history.loc[symbol].close
            for time, close in closes.iteritems():
                self.price_data_with_date[symbol].append((time.date(), close))
    
        if len(self.price_data_with_date[self.market]) != self.price_data_with_date[self.market].maxlen:
            return Universe.Unchanged

        if len(self.price_data_with_date[symbol]) != self.price_data_with_date[symbol].maxlen:
            continue 

        for date in self.eps_by_ticker[ticker]:
            if date = prev_three_months:
                EPS_value: float = self.eps_by_ticker[ticker][date]
                recent_eps_data: Tuple[datetime.date, float] = (date, EPS_value)
                break
        
        if recent_eps_data:
            last_earnings_date: datetime.date = recent_eps_data[0]
            earnings_eps_history: List[Tuple[datetime.date, float]] = [(x, self.eps_by_ticker[ticker][x]) for x in self.eps_by_ticker[ticker] if x = self.min_seasonal_eps_period:
                year_diff: np.ndarray = np.diff([x[0].year for x in seasonal_eps_data])
                if all(x == 1 for x in year_diff):
                    seasonal_eps: List[float] = [x[1] for x in seasonal_eps_data]
                    diff_values: np.ndarray = np.diff(seasonal_eps)
                    drift: float = np.average(diff_values)
                    
                    last_earnings_eps: float = seasonal_eps[-1]
                    expected_earnings: float = last_earnings_eps + drift
                    actual_earnings: float = recent_eps_data[1]
                    
                    earnings_surprise: float = actual_earnings - expected_earnings
                    
                    if symbol not in self.earnings_surprise:
                        self.earnings_surprise[symbol] = []
                    
                    elif len(self.earnings_surprise[symbol]) >= self.min_surprise_period:
                        earnings_surprise_std: float = np.std(self.earnings_surprise[symbol])
                        sue: float = earnings_surprise / earnings_surprise_std
                        
                        min_day: datetime.date = last_earnings_date - BDay(2)
                        max_day: datetime.date = last_earnings_date + BDay(1)
                        stock_closes_around_earnings: List[Symbol] = [x for x in self.price_data_with_date[symbol] if x[0] >= min_day and x[0] = min_day and x[0] = top_sue_quantile and x[1][1] >= top_ear_quantile]
    
    return self.long_positions
    
def OnData(self, data: Slice) -> None:
    targets: List[PortfolioTarget] = []
    for symbol in self.long_positions:
        if symbol in data and data[symbol]:
            targets.append(PortfolioTarget(symbol, 1. / len(self.long_positions)))
    
    self.SetHoldings(targets, True)

    self.long_positions.clear()

def Selection(self):
    self.selection_flag = True
    
    if self.month % 3 == 0:
        self.sue_ear_history_previous = self.sue_ear_history_actual
        self.sue_ear_history_actual.clear()

    self.month += 1
    if self.month > 12:
        self.month = 1

class CustomFeeModel(FeeModel):
def GetOrderFee(self, parameters):
    fee = parameters.Security.Price * parameters.Order.AbsoluteQuantity * 0.00005
    return OrderFee(CashAmount(fee, "USD"))
