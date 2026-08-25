# Original QuantConnect / library Python
# locale=zh slug="内部交易与动量结合"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

from AlgorithmImports import *
import pandas as pd
from io import StringIO
from numpy import floor
#endregion
class MomentumCombinedInsiderTrading(QCAlgorithm):
def Initialize(self):
    self.SetStartDate(2010, 1, 1)
    self.SetCash(100000)
    # NOTE: We use only s&p 100 stocks so it's possible to fetch short interest data from quandl.
    self.symbols = [
        'AAPL','MSFT','AMZN','FB','BRKB','GOOGL','GOOG','JPM','JNJ','V','PG','XOM','UNH','BAC','MA','T','DIS','INTC','HD','VZ','MRK',
        'PFE','CVX','KO','CMCSA','CSCO','PEP','WFC','C','BA','ADBE','WMT','CRM','MCD','MDT','BMY','ABT','NVDA','NFLX','AMGN','PM','PYPL',
        'TMO','COST','ABBV','ACN','HON','NKE','UNP','UTX','NEE','IBM','TXN','AVGO','LLY','ORCL','LIN','SBUX','AMT','LMT','GE','MMM','DHR',
        'QCOM','CVS','MO','LOW','FIS','AXP','BKNG','UPS','GILD','CHTR','CAT','MDLZ','GS','USB','CI','ANTM','BDX','TJX','ADP','TFC','CME',
        'SPGI','COP','INTU','ISRG','CB','SO','D','FISV','PNC','DUK','SYK','ZTS','MS','RTN','AGN','BLK'
        ]
        
    self.period = 6 * 21
    
    # Trenching
    self.holding_period = 12
    self.managed_queue = []
    
    # Dataframe with insider trades for every stock.
    self.insiders_trading = {}
    
    # Create custom universe.
    self.selection_flag = False
    
    self.symbol = self.AddEquity('SPY', Resolution.Daily).Symbol
    self.shares_outstanding = {}
    for symbol in self.symbols:
        # Import insiders trading data.
        csv_string_file = self.Download(f'data.quantpedia.com/backtesting_data/economic/insiders_trading/{symbol}.csv')
        if csv_string_file == "": continue
        parser = lambda x: pd.datetime.strptime(x, "%Y-%m-%d")
        self.insiders_trading[symbol] = pd.read_csv(StringIO(csv_string_file), sep=';', parse_dates=['Tran.Date'], date_parser=parser)
    self.UniverseSettings.Resolution = Resolution.Daily
    self.AddUniverseSelection(FineFundamentalUniverseSelectionModel(self.CoarseSelectionFunction, self.FineSelectionFunction))
    self.Schedule.On(self.DateRules.MonthEnd(self.symbol), self.TimeRules.AfterMarketOpen(self.symbol), self.Selection)
def OnSecuritiesChanged(self, changes):
    for security in changes.AddedSecurities:
        security.SetFeeModel(CustomFeeModel())
        security.SetLeverage(10)
        
def CoarseSelectionFunction(self, coarse):
    if not self.selection_flag:
        return Universe.Unchanged
    
    return [Symbol.Create(x, SecurityType.Equity, Market.USA) for x in self.symbols]
def FineSelectionFunction(self, fine):
    fine = [x for x in fine if x.EarningReports.BasicAverageShares.ThreeMonths > 0 and x.Symbol.Value in self.insiders_trading]
    symbols = [x.Symbol for x in fine]
    
    history = self.History(symbols, self.period, Resolution.Daily)
    if history.empty:
        self.Log(f'Empty history request for {len(symbols)} symbols')
        return Universe.Unchanged
    history = history.close.unstack(0)
    
    last_prices = {}
    performance = {}
    
    for symbol in symbols:
        if symbol in history:
            closes = history[symbol]
            if len(closes) == self.period:
                performance[symbol] = closes[-1] / closes[0] - 1
                last_prices[symbol] = closes[-1]
            
    # Stock which have not been traded last 6 months.
    silence = []
    
    # Traded stocks.
    nid = {}
    
    for stock in fine:
        symbol = stock.Symbol
        
        # Get number of buys and sells during last 6 months.
        ticker = symbol.Value
        buys = [row['Shares'] for index, row in self.insiders_trading[ticker].iterrows() if row['Symbol'] == ticker and row['Tran.Date'] >= (self.Time - timedelta(days = 6 * 30)) and row['Tran.Date'] = (self.Time - timedelta(days = 6 * 30)) and row['Tran.Date']  0 and x[0] in nid and nid[x[0]] > 0]
    # short = [x[0] for x in performance.items() if x[1]  0]
    short = [x for x in losers if x in silence]
    
    if len(long) != 0:
        long_w = self.Portfolio.TotalPortfolioValue / self.holding_period / len(long)
        # symbol/quantity collection
        long_symbol_q = [(x, floor(long_w / last_prices[x])) for x in long]
    else:
        long_symbol_q = []

    if len(short) != 0:
        short_w = self.Portfolio.TotalPortfolioValue / self.holding_period / len(short)
        # symbol/quantity collection
        short_symbol_q = [(x, -floor(short_w / last_prices[x])) for x in short]
    else:
        short_symbol_q = []
    
    self.managed_queue.append(RebalanceQueueItem(long_symbol_q + short_symbol_q))
    
    return long + short
def OnData(self, data):
    if not self.selection_flag:
        return
    self.selection_flag = False
    
    # Trade execution
    remove_item = None
    
    # Rebalance portfolio
    for item in self.managed_queue:
        if item.holding_period == self.holding_period + 1: # Each month investor goes long past winners with a positive NID and goes short past losers from “silence” portfolio.
            # Liquidate
            for symbol, quantity in item.symbol_q:
                self.MarketOrder(symbol, -quantity)
            
            remove_item = item
            
        elif item.holding_period == 1: # Each month investor goes long past winners with a positive NID and goes short past losers from “silence” portfolio.
            open_symbol_q = []
            
            for symbol, quantity in item.symbol_q:
                if symbol in data and data[symbol]:
                    self.MarketOrder(symbol, quantity)
                    open_symbol_q.append((symbol, quantity))
                        
            # Only opened orders will be closed        
            item.symbol_q = open_symbol_q
            
        item.holding_period += 1
        
    # We need to remove closed part of portfolio after loop. Otherwise it will miss one item in self.managed_queue.
    if remove_item:
        self.managed_queue.remove(remove_item)
        
def Selection(self):
    self.selection_flag = True
class RebalanceQueueItem():
def __init__(self, symbol_q):
    # symbol/quantity collections
    self.symbol_q = symbol_q
    self.holding_period = 0
# Custom fee model
class CustomFeeModel(FeeModel):
def GetOrderFee(self, parameters):
    fee = parameters.Security.Price * parameters.Order.AbsoluteQuantity * 0.00005
    return OrderFee(CashAmount(fee, "USD"))
