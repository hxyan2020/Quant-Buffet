# Original QuantConnect / library Python
# locale=en slug="post-earnings-annoucement-drift-using-nlp-on-earnings-calls"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

from AlgorithmImports import *
from dateutil.relativedelta import relativedelta
from itertools import combinations
#endregion
class PostEarningsAnnoucementDriftUsingNLPonEarningsCalls(QCAlgorithm):
def Initialize(self):
    self.SetStartDate(2012, 1, 1)
    self.SetCash(100_000)
    
    self.quantile: int = 5
    self.period: int = 8
    self.leverage: int = 5
    self.holding_period: int = 12 # weeks
    self.min_share_price: float = 5.
    self.managed_queue: List[RebalanceQueueItem] = [] # tranched queue
    self.ticker_universe: List = []
    self.weight: Dict[Symbol, float] = {}
    self.sentiment_by_transcript_date: Dict[datetime.datetime, Dict[str, float]] = {}
    self.sentiment_history: Dict[str, Dict[datetime.datetime, float]] = {}
    # management discussion sentiment data
    sentiment_file: str = self.Download('data.quantpedia.com/backtesting_data/index/management_discussion_sentiment.csv')
    sentiment_file_lines: List[str] = sentiment_file.split('\r\n')
    # parse sentiment data
    for i, line in enumerate(sentiment_file_lines):
        # transcript_date;A;ADSK;ANF;...
        # 2011-10-12;;;;;;;;;;;;;;;0.1625;0.4507;0.3004;...
        if i == 0:
            # get available tickers
            self.ticker_universe = line.split(';')[1:]
        else:
            line_split: List[str] = line.split(';')
            
            # store sentiment data by transcript date and by ticker
            date_str: str = line_split[0]
            if date_str != '':
                transcript_date: datetime.datetime = datetime.strptime(line_split[0], "%Y-%m-%d") + relativedelta(months=1)
                self.sentiment_by_transcript_date[transcript_date] = {}
                for j, sentiment in enumerate(line_split[1:]):
                    if sentiment != '':
                        ticker: str = self.ticker_universe[j]
                        if ticker not in self.sentiment_history:
                            self.sentiment_history[ticker] = {}
                        
                        sentiment: float = float(sentiment)
                        
                        self.sentiment_by_transcript_date[transcript_date][ticker] = sentiment
                        self.sentiment_history[ticker][transcript_date] = sentiment
    market: Symbol = self.AddEquity('SPY', Resolution.Daily).Symbol
    # universe setup
    self.fundamental_count: int = 500
    self.fundamental_sorting_key = lambda x: x.DollarVolume
    self.selection_flag: bool = False
    self.UniverseSettings.Resolution = Resolution.Daily
    self.AddUniverse(self.FundamentalSelectionFunction)
    self.Settings.MinimumOrderMarginPortfolioPercentage = 0.
    self.settings.daily_precise_end_time = False
    self.Schedule.On(self.DateRules.WeekStart(market), self.TimeRules.BeforeMarketClose(market), self.Selection)
def OnSecuritiesChanged(self, changes: SecurityChanges) -> None:
    for security in changes.AddedSecurities:
        security.SetFeeModel(CustomFeeModel())
        security.SetLeverage(self.leverage)
def FundamentalSelectionFunction(self, fundamental: List[Fundamental]) -> List[Symbol]:
    if not self.selection_flag:
        return Universe.Unchanged
    selected: List[Fundamental] = [
        f for f in fundamental if f.HasFundamentalData
        and f.Price >= self.min_share_price 
        and f.Symbol.Value in self.ticker_universe
    ]
    if len(selected) > self.fundamental_count:
        selected = [x for x in sorted(selected, key=self.fundamental_sorting_key, reverse=True)[:self.fundamental_count]]
        
    symbols_by_ticker: Dict[str, Symbol] = { x.Symbol.Value : x.Symbol for x in selected }
    prices_by_symbol: Dict[Symbol, float] = { x.Symbol : x.AdjustedPrice for x in selected }
    surprise: Dict[Symbol, float] = {}
    # there is some sentiment data available
    lookup_date: datetime.datetime = self.Time - timedelta(days=1)
    if lookup_date in self.sentiment_by_transcript_date:
        for ticker, sentiment in self.sentiment_by_transcript_date[lookup_date].items():
            if ticker in symbols_by_ticker:
                # get previous ticker history up utill previous day
                previous_transcript_dates: List = [x for x in self.sentiment_history[ticker].items() if x[0] = self.period:
                    trimmed_history: List = previous_transcript_dates[-self.period:]
                    avg_sentiment: float = np.mean([x[1] for x in trimmed_history])
                    latest_sentiment: float = self.sentiment_by_transcript_date[lookup_date][ticker]
                    surprise[symbols_by_ticker[ticker]] = latest_sentiment - avg_sentiment
    long: List[Symbol] = []
    short: List[Symbol] = []
    
    # sort by surprise
    if len(surprise) >= self.quantile:
        sorted_by_surprise: List[Symbol] = sorted(surprise, key=surprise.get, reverse=True)
        quantile: int = int(len(sorted_by_surprise) / self.quantile)
        long = sorted_by_surprise[:quantile]
        short = sorted_by_surprise[-quantile:]
        symbol_q: List[Tuple[Symbol, float]] = []
        for i, portfolio in enumerate([long, short]):
            w: float = self.Portfolio.TotalPortfolioValue / self.holding_period / len(portfolio)
            for symbol in portfolio:
                symbol_q.append((symbol, ((-1) ** i) * np.floor(w / prices_by_symbol[symbol])))
        self.managed_queue.append(RebalanceQueueItem(symbol_q))
    # return both - held symbols and new symbols
    symbols_to_return: Set[Symbol] = set([x.Key for x in self.Portfolio if x.Value.Invested])
    for symbol in long + short:
        symbols_to_return.add(symbol)
    return list(symbols_to_return)
def OnData(self, slice: Slice) -> None:
    if not self.selection_flag:
        return
    self.selection_flag = False
    # trade execution
    remove_item: None | RebalanceQueueItem = None
    
    # rebalance portfolio
    for item in self.managed_queue:
        if item.holding_period == self.holding_period:
            for symbol, quantity in item.symbol_q:
                self.MarketOrder(symbol, -quantity)
            remove_item = item
            
        elif item.holding_period == 0:
            open_symbol_q: List = []
            
            for symbol, quantity in item.symbol_q:
                if slice.contains_key(symbol) and slice[symbol]:
                    if quantity != 0:
                        self.MarketOrder(symbol, quantity)
                        open_symbol_q.append((symbol, quantity))
                        
            # only opened orders will be closed
            item.symbol_q = open_symbol_q
            
        item.holding_period += 1
        
    if remove_item:
        self.managed_queue.remove(remove_item)
def Selection(self) -> None:
    # weekly rebalance
    self.selection_flag = True
class RebalanceQueueItem():
def __init__(self, symbol_q: List[Tuple[Symbol, float]]):
    # symbol/quantity collections
    self.symbol_q: List[Tuple[Symbol, float]] = symbol_q
    self.holding_period: int = 0
def get_symbols(self) -> List:
    return list(map(lambda x: x[0], self.symbol_q))
# custom fee model
class CustomFeeModel():
def GetOrderFee(self, parameters):
    fee = parameters.Security.Price * parameters.Order.AbsoluteQuantity * 0.00005
    return OrderFee(CashAmount(fee, "USD"))
