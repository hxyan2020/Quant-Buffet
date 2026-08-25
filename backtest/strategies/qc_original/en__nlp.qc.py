# Original QuantConnect / library Python
# locale=en slug="通过自然语言处理（nlp）分析改进的财报公告后漂"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

from AlgorithmImports import *
from dateutil.relativedelta import relativedelta
from itertools import combinations
#endregion

class ImprovedPostEarningsAnnouncementDriftwithNLPAnalysis(QCAlgorithm):

def Initialize(self):
    self.SetStartDate(2012, 1, 1)
    self.SetCash(100000)
    
    self.quantile:int = 3
    self.period:int = 12
    self.week_holding_period:int = 4
    self.managed_queue:list[RebalanceQueueItem] = [] # tranched queue

    self.ticker_universe:list = []
    self.weight:dict[Symbol, float] = {}
    self.sentiment_by_transcript_date:dict[datetime.datetime, dict[str, float]] = {}
    self.sentiment_history:dict[str, dict[datetime.datetime, float]] = {}

    # management discussion sentiment data
    sentiment_file = self.Download('data.quantpedia.com/backtesting_data/index/management_discussion_sentiment.csv')
    sentiment_file_lines:list[str] = sentiment_file.split('\r\n')

    # parse sentiment data
    for i, line in enumerate(sentiment_file_lines):
        # transcript_date;A;ADSK;ANF;...
        # 2011-10-12;;;;;;;;;;;;;;;0.1625;0.4507;0.3004;...
        if i == 0:
            # get available tickers
            self.ticker_universe = line.split(';')[1:]
        else:
            line_split:list[str] = line.split(';')
            
            # store sentiment data by transcript date and by ticker
            date_str:str = line_split[0]
            if date_str != '':
                transcript_date:datetime.datetime = datetime.strptime(line_split[0], "%Y-%m-%d") + relativedelta(months=1)
                self.sentiment_by_transcript_date[transcript_date] = {}

                for j, sentiment in enumerate(line_split[1:]):
                    if sentiment != '':
                        ticker:str = self.ticker_universe[j]
                        if ticker not in self.sentiment_history:
                            self.sentiment_history[ticker] = {}
                        
                        sentiment:float = float(sentiment)
                        
                        self.sentiment_by_transcript_date[transcript_date][ticker] = sentiment
                        self.sentiment_history[ticker][transcript_date] = sentiment

    # universe setup
    self.coarse_count:int = 500
    self.selection_flag:bool = False
    self.market:Symbol = self.AddEquity('SPY', Resolution.Daily).Symbol
    self.UniverseSettings.Resolution = Resolution.Daily
    self.AddUniverse(self.CoarseSelectionFunction)
    self.Schedule.On(self.DateRules.WeekStart(self.market), self.TimeRules.BeforeMarketClose(self.market), self.Selection)

def OnSecuritiesChanged(self, changes):
    for security in changes.AddedSecurities:
        security.SetFeeModel(CustomFeeModel())
        security.SetLeverage(5)

def CoarseSelectionFunction(self, coarse):
    if not self.selection_flag:
        return Universe.Unchanged
    
    # coarse = [x for x in coarse if x.Symbol.Value in self.ticker_universe]
    coarse = sorted([x for x in coarse if x.HasFundamentalData and x.Price >= 5 and x.Symbol.Value in self.ticker_universe],
        key=lambda x: x.DollarVolume, reverse=True)[:self.coarse_count]

    symbols_by_ticker:list[Symbol] = {x.Symbol.Value : x.Symbol for x in coarse}
    prices_by_symbol:list[Symbol] = {x.Symbol : x.AdjustedPrice for x in coarse}

    surprise:dict[Symbol, float] = {}

    # there is some sentiment data available
    lookup_date:datetime.datetime = self.Time - timedelta(days=1)
    if lookup_date in self.sentiment_by_transcript_date:
        for ticker, sentiment in self.sentiment_by_transcript_date[lookup_date].items():
            if ticker in symbols_by_ticker:
                # get previous ticker history up utill previous day
                previous_transcript_dates:list = [x for x in self.sentiment_history[ticker].items() if x[0] = self.period:
                    trimmed_history:list = previous_transcript_dates[-self.period:]
                    avg_sentiment:float = np.mean([x[1] for x in trimmed_history])
                    latest_sentiment:float = self.sentiment_by_transcript_date[lookup_date][ticker]
                    surprise[symbols_by_ticker[ticker]] = latest_sentiment - avg_sentiment

    long:list[Symbol] = []
    short:list[Symbol] = []
    
    # sort by surprise
    if len(surprise) >= self.quantile:
        sorted_by_surprise:list = sorted(surprise.items(), key=lambda x: x[1], reverse=True)
        quantile:int = int(len(sorted_by_surprise) / self.quantile)
        long = [x[0] for x in sorted_by_surprise[:quantile]]
        short = [x[0] for x in sorted_by_surprise[-quantile:]]

        long_w = self.Portfolio.TotalPortfolioValue / self.week_holding_period / len(long)
        long_symbol_q = [(x, np.floor(long_w / prices_by_symbol[x])) for x in long]
    
        short_w = self.Portfolio.TotalPortfolioValue / self.week_holding_period / len(short)
        short_symbol_q = [(x, -np.floor(short_w / prices_by_symbol[x])) for x in short]
        
        self.managed_queue.append(RebalanceQueueItem(long_symbol_q + short_symbol_q))

    # return both - held symbols and new symbols
    symbols_to_return:set[Symbol] = set([x.Key for x in self.Portfolio if x.Value.Invested])
    for symbol in long+short:
        symbols_to_return.add(symbol)

    return list(symbols_to_return)

def OnData(self, data):
    if not self.selection_flag:
        return
    self.selection_flag = False

    # trade execution
    remove_item = None
    
    # rebalance portfolio
    for item in self.managed_queue:
        if item.holding_period == self.week_holding_period:
            for symbol, quantity in item.symbol_q:
                self.MarketOrder(symbol, -quantity)
            remove_item = item
            
        elif item.holding_period == 0:
            open_symbol_q = []
            
            for symbol, quantity in item.symbol_q:
                if symbol in data and data[symbol]:
                    if quantity != 0:
                        self.MarketOrder(symbol, quantity)
                        open_symbol_q.append((symbol, quantity))
                        
            # only opened orders will be closed
            item.symbol_q = open_symbol_q
            
        item.holding_period += 1
        
    if remove_item:
        self.managed_queue.remove(remove_item)

def Selection(self):
    # weekly rebalance
    self.selection_flag = True

class RebalanceQueueItem():
def __init__(self, symbol_q):
    # symbol/quantity collections
    self.symbol_q = symbol_q
    self.holding_period = 0

def get_symbols(self) -> list:
    return [x[0] for x in self.symbol_q]

# custom fee model
class CustomFeeModel():
def GetOrderFee(self, parameters):
    fee = parameters.Security.Price * parameters.Order.AbsoluteQuantity * 0.00005
    return OrderFee(CashAmount(fee, "USD"))
