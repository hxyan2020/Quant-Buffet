# Original QuantConnect / library Python
# locale=zh slug="财报公告贝塔"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

from AlgorithmImports import *
from pandas.tseries.offsets import BDay
from collections import deque
from scipy import stats
from typing import List, Dict, Set, Deque, Tuple
from pandas.core.frame import DataFrame
import json
#endregion
class EarningsAnnouncementBeta(QCAlgorithm):
def Initialize(self) -> None:
    self.SetStartDate(2010, 1, 1)   # Earnings days data begin at 2015.
    self.SetCash(100_000)
    # Earning data parsing
    self.earnings:Dict[str, List[str]] = {}
    self.earning:Dict[str, List[str]] = {}
    
    self.earnings_set:Set = set()
    self.earning_set:Set = set()
    self.quantile:int = 5
    earnings_data:str = self.Download('data.quantpedia.com/backtesting_data/economic/earnings_dates_eps.json')
    earnings_data_json:list[dict] = json.loads(earnings_data)
    for obj in earnings_data_json:
        date:datetime.date = datetime.strptime(obj['date'], "%Y-%m-%d").date()
        date_format:str = f'{date.month}/{date.year}'
        if date_format not in self.earnings:
            self.earnings[date_format] = []
        
        for stock_data in obj['stocks']:
            ticker:str = stock_data['ticker']
            self.earnings[date_format].append(ticker)
            self.earnings_set.add(ticker)
        
    self.data:Dict[Symbol, SymbolDate] = {}
    self.period:int = 21
    self.leverage:int = 5
    self.min_share_price:float = 5.
    self.market:Symbol = self.AddEquity('SPY', Resolution.Daily).Symbol
    self.data[self.market] = SymbolData(self.period)
    
    self.announcement_returns:Dict[Symbol, Deque[Tuple[float, float]]] = {}
    self.announcement_period:int = 12   # three years worth of earnings window returns
    
    self.weight:Dict[Symbol, float] = {}
    
    self.selection_flag:bool = False
    self.UniverseSettings.Resolution = Resolution.Daily
    self.AddUniverse(self.FundamentalSelectionFunction)
    self.Settings.MinimumOrderMarginPortfolioPercentage = 0.
    self.Schedule.On(self.DateRules.MonthStart(self.market), self.TimeRules.AfterMarketOpen(self.market), self.Selection)
    self.settings.daily_precise_end_time = False
def OnSecuritiesChanged(self, changes: SecurityChanges) -> None:
    for security in changes.AddedSecurities:
        security.SetFeeModel(CustomFeeModel())
        security.SetLeverage(self.leverage)
            
def FundamentalSelectionFunction(self, fundamental: List[Fundamental]) -> List[Symbol]:
    for stock in fundamental:
        symbol:Symbol = stock.Symbol
        
        # Store daily price.
        if symbol in self.data:
            self.data[symbol].update(self.Time.date(), stock.AdjustedPrice)
    if not self.selection_flag:
        return Universe.Unchanged
    
    selected:List[Fundamental] = [
        x for x in fundamental if x.HasFundamentalData and x.Market == 'usa' and x.Price >= self.min_share_price and \
        x.Symbol.Value in self.earnings_set and x.MarketCap != 0
    ]
    prev_month:DateTime = (self.Time - timedelta(days=self.Time.day))
    last_month:int = prev_month.month
    last_year:int = prev_month.year
    
    # Wait until market data is ready.
    if not self.data[self.market].is_ready():
        return Universe.Unchanged
    
    date_format:str = f'{self.Time.month}/{self.Time.year}'
    beta:Dict[Fundamental, float] = {}
    # Warming up prices for rolling window.
    for stock in selected:
        symbol:Symbol = stock.Symbol
        ticker:str = symbol.Value
        if symbol not in self.data:
            self.data[symbol] = SymbolData(self.period)
            history:DataFrame = self.History(symbol, self.period, Resolution.Daily)
            if history.empty:
                self.Log(f"Not enough data for {symbol} yet")
                continue
            closes:pd.Series = history.loc[symbol].close
            for time, close in closes.items():
                self.data[symbol].update(time.date(), close)
        
        if self.data[symbol].is_ready():
            # Stocks with last month's earnings.
            if stock.EarningReports.FileDate.Value.year == last_year and stock.EarningReports.FileDate.Value.month == last_month:
                annoucement_date:DateTime = stock.EarningReports.FileDate.Value
                date_from:DateTime = (annoucement_date - BDay(2)).date()
                date_to:DateTime = (annoucement_date + BDay(1)).date()
                
                relevant_stock_return:float = self.data[symbol].performance(date_from, date_to)
                relevant_market_return:float = self.data[self.market].performance(date_from, date_to)
                
                # Store announcement returns.
                if symbol not in self.announcement_returns:
                    self.announcement_returns[symbol] = deque(maxlen = self.announcement_period)
                
                if relevant_stock_return and relevant_market_return:
                    self.announcement_returns[symbol].append((relevant_stock_return, relevant_market_return))
            
            # Check if stock is about to have earnings announcement this month.
            if date_format in self.earnings and ticker in self.earnings[date_format]:
                if symbol in self.announcement_returns and len(self.announcement_returns[symbol]) == self.announcement_period:
                    # Calculate stock returns beta to market returns.
                    Y:List[float] = [x[0] for x in self.announcement_returns[symbol]]
                    X:List[float] = [x[1] for x in self.announcement_returns[symbol]]
                    slope, intercept, r_value, p_value, std_err = stats.linregress(X, Y)
                    beta[stock] = slope
    
    if len(beta) >= self.quantile:
        # Beta sorting.
        sorted_by_beta:List[Fundamental] = sorted(beta.items(), key = lambda x:x[1], reverse = True)
        quantile:int = int(len(sorted_by_beta) / self.quantile)
        long:List[Fundamental] = [x[0] for x in sorted_by_beta[:quantile]]
        short:List[Fundamental] = [x[0] for x in sorted_by_beta[-quantile:]]
        
        # Market cap weighting.
        for i, portfolio in enumerate([long, short]):
            mc_sum:float = sum(map(lambda x: x.MarketCap, portfolio))
            for stock in portfolio:
                self.weight[stock.Symbol] = ((-1) ** i) * stock.MarketCap / mc_sum
                
    return list(self.weight.keys())
    
def OnData(self, data: Slice) -> None:
    if not self.selection_flag:
        return
    self.selection_flag = False
    # Trade execution.
    portfolio:List[PortfolioTarget] = [PortfolioTarget(symbol, w) for symbol, w in self.weight.items() if symbol in data and data[symbol]]
    self.SetHoldings(portfolio, True)
    self.weight.clear()
        
def Selection(self) -> None:
    self.selection_flag = True
        
class SymbolData():
def __init__(self, period: int) -> None:
    self.closes:Dict[DateTime, float] = {}
    self.period:int = period
    
def update(self, date:DateTime, close:float) -> None:
    self.closes[date] = close
    
def is_ready(self) -> bool:
    return len(self.closes) >= self.period

def performance(self, date_from:DateTime, date_to:DateTime) -> float:
    perf:None|float = None
    if date_to in self.closes and date_from in self.closes:
        perf:float = self.closes[date_to] / self.closes[date_from] - 1
    return perf
# Custom fee model
class CustomFeeModel(FeeModel):
def GetOrderFee(self, parameters: OrderFeeParameters) -> OrderFee:
    fee: float = parameters.Security.Price * parameters.Order.AbsoluteQuantity * 0.00005
    return OrderFee(CashAmount(fee, "USD"))
