# Original QuantConnect / library Python
# locale=zh slug="收益反应弹性"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

from AlgorithmImports import *
import numpy as np
from collections import deque
from pandas.tseries.offsets import BDay
from trade_manager import TradeManager
from typing import List, Dict, Deque
from pandas.core.frame import DataFrame
from pandas.core.series import Series
#endregion
class EarningsResponseElasticity(QCAlgorithm):
def Initialize(self) -> None:
    self.SetStartDate(2010, 1, 1)
    self.SetCash(100000)
    self.period: int = 13
    self.ear_period: int = 4
    self.surprise_period: int = 4
    self.holding_period: int = 60
    self.long_size: int = 50
    self.short_size: int = 50
    self.leverage: int = 5
    self.threshold: int = 3
    self.percentile: int = 20
    
    # market daily price data
    self.market_prices: Deque = deque(maxlen = self.ear_period)
    
    self.earnings_surprise: Dict[Symbol, float] = {}
    self.long: List[Symbol] = []
    self.short: List[Symbol] = []
    self.ere_history_previous: List[float] = []
    self.ere_history_actual: List[float] = []
    self.eps: Dict[Symbol, deque] = {} 
    self.earnings_data: Dict[datetime.date, Dict[str, float]] = {}
    
    # 50 equally weighted brackets for traded symbols
    self.trade_manager: trade_manager.TradeManager = TradeManager(self, self.long_size, self.short_size, self.holding_period)
    self.symbol: Symbol = self.AddEquity('SPY', Resolution.Daily).Symbol
    earnings_data: str = self.Download('data.quantpedia.com/backtesting_data/economic/earnings_dates_eps.json')
    earnings_data_json: List[dict] = json.loads(earnings_data)
    
    for obj in earnings_data_json:
        date: datetime.date = datetime.strptime(obj['date'], "%Y-%m-%d").date()
        self.earnings_data[date] = {}
        
        for stock_data in obj['stocks']:
            ticker: str = stock_data['ticker']
            if stock_data['eps'] != '':
                self.earnings_data[date][ticker] = float(stock_data['eps'])
    
    self.month: int = 12
    self.settings.daily_precise_end_time = False
    self.Settings.MinimumOrderMarginPortfolioPercentage = 0.
    self.UniverseSettings.Resolution = Resolution.Daily
    self.AddUniverse(self.FundamentalSelectionFunction)
    self.Schedule.On(self.DateRules.MonthEnd(self.symbol), self.TimeRules.AfterMarketOpen(self.symbol), self.Selection)
def OnSecuritiesChanged(self, changes: SecurityChanges) -> None:
    for security in changes.AddedSecurities:
        security.SetFeeModel(CustomFeeModel())
        security.SetLeverage(self.leverage)

def FundamentalSelectionFunction(self, fundamental: List[Fundamental]) -> List[Symbol]:
    # stocks with yesterday's earnings
    yesterday: datetime.date = (self.Time - BDay(1)).date()
    if yesterday not in self.earnings_data:
        return Universe.Unchanged
    tickers_with_yesterday_earnings: List[str] = list(self.earnings_data[yesterday].keys())
    # stocks with yesterday's earnings
    selected: List[Fundamental] = [x for x in fundamental if x.Symbol.Value in tickers_with_yesterday_earnings]
    # ERE data
    ere_data: Dict[Symbol, List[float, float, float]] = {}
    
    for stock in selected:
        symbol: Symbol = stock.Symbol
        ticker: str = symbol.Value
        
        # Store eps data.
        if symbol not in self.eps:
            self.eps[symbol] = deque(maxlen = self.period)
        self.eps[symbol].append([yesterday, self.earnings_data[yesterday][ticker]])
        if len(self.eps[symbol]) == self.eps[symbol].maxlen:
            year_range: range = range(self.Time.year - 3, self.Time.year)
            month_range: List[int] = [self.Time.month-1, self.Time.month, self.Time.month+1]
            
            # earnings 4 years back
            seasonal_eps_data: List[List[datetime.date, float]] = [x for x in self.eps[symbol] if x[0].month in month_range and x[0].year in year_range]
            if len(seasonal_eps_data) != self.threshold: continue
            recent_eps_data: List[datetime.date, float] = self.eps[symbol][-1]
            
            # Make sure we have a consecutive seasonal data. Same months with one year difference.
            year_diff: np.ndarray = np.diff([x[0].year for x in seasonal_eps_data])
            if all(x == 1 for x in year_diff):
                seasonal_eps: List[float] = [x[1] for x in seasonal_eps_data]
                diff_values: np.ndarray = np.diff(seasonal_eps)
                drift: float = np.average(diff_values)
                
                # SUE calculation
                last_earnings: float = seasonal_eps[-1]
                expected_earnings: float = last_earnings + drift
                actual_earnings: float = recent_eps_data[1]
                # store sue value with earnigns date
                earnings_surprise: float = actual_earnings - expected_earnings
                if symbol not in self.earnings_surprise:
                    self.earnings_surprise[symbol] = deque(maxlen = self.surprise_period)
                elif len(self.earnings_surprise[symbol]) >= self.surprise_period:
                    earnings_surprise_std: float = np.std(self.earnings_surprise[symbol])
                    sue: float = earnings_surprise / earnings_surprise_std
            
                    # EAR calc
                    if len(self.market_prices) == self.market_prices.maxlen:
                        # abnormal return calc
                        history: DataFrame = self.History(symbol, self.ear_period, Resolution.Daily)
                        if len(history) == self.ear_period and 'close' in history:
                            stock_closes: Series = history['close']
                            ear: float = Return(stock_closes) - Return(self.market_prices)
                            ere: float = abs(ear) / sue
                            ere_data[symbol] = [ere, ear, sue]
                            
                            # store ere data in this month's history
                            self.ere_history_actual.append(ere)
                self.earnings_surprise[symbol].append(earnings_surprise)
            
    if len(ere_data) != 0 and len(self.ere_history_previous) != 0:
        # sort by ERE
        bottom_ere_quintile:float = np.percentile(self.ere_history_previous, self.percentile)
        self.long = [x[0] for x in ere_data.items() if x[1][0]  0 and x[1][2] > 0]
        self.short = [x[0] for x in ere_data.items() if x[1][0]  None:
    if self.symbol in data and data[self.symbol]:
        self.market_prices.append(data[self.symbol].Value)
    # open new trades
    for symbol in self.long:
        self.trade_manager.Add(symbol, True)
    for symbol in self.short:
        self.trade_manager.Add(symbol, False)
    
    self.trade_manager.TryLiquidate()
    
    self.long.clear()
    self.short.clear()
    
def Selection(self) -> None:
    # every three months  
    if self.month % 3 == 0:
        # save previous history
        self.ere_history_previous = [x for x in self.ere_history_actual]
        self.ere_history_actual.clear()
    self.month += 1
    if self.month > 12:
        self.month = 1
# Custom fee model.
class CustomFeeModel(FeeModel):
def GetOrderFee(self, parameters: OrderFeeParameters) -> OrderFee:
    fee: float = parameters.Security.Price * parameters.Order.AbsoluteQuantity * 0.00005
    return OrderFee(CashAmount(fee, "USD"))
def Return(values: np.ndarray) -> float:
return (values[-1] - values[0]) / values[0]
