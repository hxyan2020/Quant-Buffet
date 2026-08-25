# Original QuantConnect / library Python
# locale=en slug="google-search-volume-combined-with-extent-of-press-news-predicts-stocks-returns"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

from AlgorithmImports import *
from dateutil.relativedelta import relativedelta
from typing import List, Dict
#endregion
class GoogleSearchVolumeCombinedWithExtentOfPressNewsPredictsStocksReturns(QCAlgorithm):
def Initialize(self) -> None:
    self.SetStartDate(2004, 1, 1) # News data are since 2010 and Google search data are since 2004
    self.SetCash(100_000)
    
    self.leverage: int = 5
    self.data: Dict[str, SymbolData] = {}
    self.tickers: List[str] = []
    self.selected: Dict[str, Symbol] = {}
    self.symbols_tickers: Dict[Symbol, str] = {}
    
    self.stocks_news_last_date: datetime.date = datetime(1,1,1).date()
    # Data source: https://www.nasdaq.com/market-activity/stocks/aapl/news-headlines
    # dates in dictionaries aren't sorted in ascending or descending way
    csv_string_file: str = self.Download('data.quantpedia.com/backtesting_data/index/stocks_news.csv')
    lines: List[str] = csv_string_file.split('\r\n')
    
    columns: List[str] = lines[0].split(';')
    
    # subscribe to Quantpedia Google Search data and create SymbolData object for each stock's ticker
    for ticker in columns[1:]:
        # convert ticker to upper to match Symbol.Value from quantconnect
        ticker: str = ticker.upper()
        
        # subscribe to QuantpediaGoogleSeach data
        symbol: Symbol = self.AddData(QuantpediaGoogleSearch, ticker, Resolution.Daily).Symbol
        self.symbols_tickers[symbol] = ticker
        
        # create SymbolData object for current stock
        self.data[ticker] = SymbolData()
        
        self.tickers.append(ticker)
    
    for line in lines[1:]: # skip header line
        if line == '':
            continue
        
        # split line
        line: List[str] = line.split(';')
        
        # convert string to date
        str_date = line[0]
        date: datetime.date = datetime.strptime(str_date, '%d.%m.%Y').date()
        if date > self.stocks_news_last_date:
            self.stocks_news_last_date = date
        for index in range(1, len(line)): # skip date as a first value of the row
            # retrive ticker from list created based on csv header
            ticker: str = self.tickers[index - 1]
            # get total stock's news for specific date
            total_news: str = line[index]
            
            # initialize dictionary for total stock's news for specific date
            self.data[ticker].news[date] = float(total_news)
    
    market: Symbol = self.AddEquity('SPY', Resolution.Daily).Symbol
    
    self.selection_flag: bool = False
    self.UniverseSettings.Leverage = self.leverage
    self.UniverseSettings.Resolution = Resolution.Daily
    self.AddUniverse(self.FundamentalSelectionFunction)
    self.Settings.MinimumOrderMarginPortfolioPercentage = 0.
    self.settings.daily_precise_end_time = False
    self.Schedule.On(self.DateRules.MonthStart(market), self.TimeRules.AfterMarketOpen(market), self.Selection)
def OnSecuritiesChanged(self, changes: SecurityChanges) -> None:
    for security in changes.AddedSecurities:
        security.SetFeeModel(CustomFeeModel())
    
def FundamentalSelectionFunction(self, fundamental: List[Fundamental]) -> List[Symbol]:
    # rebalance monthly
    if not self.selection_flag:
        return Universe.Unchanged
            
    # Select S&P 100 stocks
    self.selected = {x.Symbol.Value: x.Symbol for x in fundamental if x.Symbol.Value in self.data}
            
    return list(self.selected.values())
def OnData(self, slice: Slice) -> None:
    custom_data_last_update: Dict[Symbol, datetime.date] = QuantpediaGoogleSearch.get_last_update_date()
    if self.time.date() > self.stocks_news_last_date:
        self.Liquidate()
        return
    # update google search values for each stock
    for google_search_symbol, stock_ticker in self.symbols_tickers.items():
        if self.securities[google_search_symbol].get_last_data() and self.time.date() > custom_data_last_update[google_search_symbol]:
            self.liquidate(stock_ticker)
            continue
        # check if google search value exists
        if slice.contains_key(google_search_symbol) and slice[google_search_symbol]:
            # retrive and update google search value
            google_search_value: float = slice[google_search_symbol].Value
            self.data[stock_ticker].update_google_search_values(google_search_value)
    
    # rebalance monthly
    if not self.selection_flag:
        return
    self.selection_flag = False
    
    search_increase: List[Symbol] = [] # storing symbol of stocks, which had google search increase 
    news_increase: List[Symbol] = [] # storing symbol of stocks, which had news increase
    
    search_decrease: List[Symbol] = [] # storing symbol of stocks, which had google search decrease
    news_decrease: List[Symbol] = [] # storing symbol of stocks, which had news decrease
    
    # calculate stocks search intensity and news intensity
    for stock_ticker, symbol_obj in self.data.items():
        # make sure stock has stock symbol from fundamental function
        if stock_ticker not in self.selected:
            continue
        
        # make sure google search data are ready
        if not symbol_obj.is_google_search_ready():
            continue
        
        # get stock symbol based on it's ticker
        stock_symbol: Symbol = self.selected[stock_ticker]
        
        # check if stock is in increase of google search for this month according to last twelve months mean
        google_search_increase_flag: bool = symbol_obj.google_search_increase() # return False/True/None
        
        if google_search_increase_flag is True:
            search_increase.append(stock_symbol)
        elif google_search_increase_flag is False:
            search_decrease.append(stock_symbol)
        
        current_date: datetime.date = self.Time.date()
        twelve_months_before: datetime.date = current_date - relativedelta(months=13) # substract 13 months, because rebalancing is at the start of the month
        # check if stock is in increase of total_news for this month according to last twelve months mean
        news_increase_flag: bool = symbol_obj.news_increase(current_date, twelve_months_before) # return False/True/None
            
        if news_increase_flag is True:
            news_increase.append(stock_symbol)
        elif news_increase_flag is True:
            news_decrease.append(stock_symbol)
        
    # long stocks, which had increase of news and google search
    long: List[Symbol] = [stock_symbol for stock_symbol in news_increase if stock_symbol in search_increase]
    
    # short stocks, which had decrease of news and google search
    short: List[Symbol] = [stock_symbol for stock_symbol in news_decrease if stock_symbol in search_decrease]
    
    long_length = len(long)
    short_length = len(short)   
            
    # trade execution
    targets: List[PortfolioTarget] = []
    for i, portfolio in enumerate([long, short]):
        for symbol in portfolio:
            if slice.contains_key(symbol) and slice[symbol]:
                targets.append(PortfolioTarget(symbol, ((-1) ** i) / len(portfolio)))
    
    self.SetHoldings(targets, True)
    
def Selection(self) -> None:
    self.selection_flag = True
    
class SymbolData():
def __init__(self) -> None:
    self.google_search_values: List[float] = []
    self.news: Dict[datetime.date, float] = {}
    
def update_google_search_values(self, google_search_value: float) -> None:
    self.google_search_values.append(google_search_value)
    
def is_google_search_ready(self) -> bool:
    # return True if there are atleast twelve months of google search values
    if len(self.google_search_values) >= 12:
        return True
    else:
        return False
        
def google_search_increase(self) -> bool:
    # check if stock has no search volume
    if self.google_search_values[-1] == 0:
        # stock has no search volume
        return None
    
    max_value: float = max(self.google_search_values)
    
    twelve_months_values: List[float] = []
    
    # normalize and store google search values for last 12 months
    for google_search_value in self.google_search_values[-12:]:
        if google_search_value != 0:
            twelve_months_values.append(google_search_value / max_value)
        else:
            twelve_months_values.append(0)
    
    twelve_months_mean: float = np.mean(twelve_months_values)
    
    last_value: float = self.google_search_values[-1] / max_value
    
    # check if google search volume increased
    if last_value > twelve_months_mean:
        # google search volume increased
        return True
    else:
        # google search volume decreased
        return False
        
def news_increase(self, current_date: datetime.date, twelve_months_before: datetime.date) -> bool:
    news_data: Dict[str, np.ndarray]  = {} # storing numpy array of total news values keyed by string of it's month and year
    prev_month_year_string: str = str(current_date.month - 1) + str(current_date.year)
    current_month_year_string: str = str(current_date.month) + str(current_date.year)
    
    for date, total_news in self.news.items():
        # check if date is in period last twelve months from current date
        if date >= twelve_months_before and date  twelve_months_news_mean:
        # news volume increased
        return True
    else:
        # news volume decreased
        return False
    
# Custom fee model.
class CustomFeeModel(FeeModel):
def GetOrderFee(self, parameters: OrderFeeParameters) -> OrderFee:
    fee: float = parameters.Security.Price * parameters.Order.AbsoluteQuantity * 0.00005
    return OrderFee(CashAmount(fee, "USD"))
    
# Quantpedia data.
# NOTE: IMPORTANT: Data order must be ascending (datewise)
class QuantpediaGoogleSearch(PythonData):
_last_update_date:Dict[Symbol, datetime.date] = {}
@staticmethod
def get_last_update_date() -> Dict[Symbol, datetime.date]:
   return QuantpediaGoogleSearch._last_update_date
def GetSource(self, config, date, isLiveMode):
    return SubscriptionDataSource("data.quantpedia.com/backtesting_data/google_search/{0}.csv".format(config.Symbol.Value), SubscriptionTransportMedium.RemoteFile, FileFormat.Csv)
def Reader(self, config, line, date, isLiveMode):
    data = QuantpediaGoogleSearch()
    data.Symbol = config.Symbol
    
    if not line[0].isdigit(): return None
    split = line.split(';')
    
    data.Time = datetime.strptime(split[0], "%d.%m.%Y") + timedelta(days=1)
    data['value'] = float(split[1])
    data.Value = float(split[1])
    if config.Symbol not in QuantpediaGoogleSearch._last_update_date:
        QuantpediaGoogleSearch._last_update_date[config.Symbol] = datetime(1,1,1).date()
    if data.Time.date() > QuantpediaGoogleSearch._last_update_date[config.Symbol]:
        QuantpediaGoogleSearch._last_update_date[config.Symbol] = data.Time.date()
    return data
