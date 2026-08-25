# Original QuantConnect / library Python
# locale=zh slug="内部人士的沉默"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

from AlgorithmImports import *
from collections import deque
import pandas as pd
from io import StringIO
from numpy import floor
#endregion
class InsidersSilence(QCAlgorithm):
def Initialize(self):
    self.SetStartDate(2013, 1, 1)
    self.SetCash(100000)
    self.symbols = [
                    'AAPL','MSFT','AMZN','FB','BRKB','GOOGL','GOOG','JPM','JNJ','V',
                    'PG','XOM','UNH','BAC','MA','T','DIS','INTC','HD','VZ',
                    'MRK','PFE','CVX','KO','CMCSA','CSCO','PEP','WFC','C','BA',
                    'ADBE','WMT','CRM','MCD','MDT','BMY','ABT','NVDA','NFLX','AMGN',
                    'PM','PYPL','TMO','COST','ABBV','ACN','HON','NKE','UNP','UTX',
                    # 'NEE','IBM','TXN','AVGO','LLY','ORCL','LIN','SBUX','AMT','LMT',
                    # 'GE','MMM','DHR','QCOM','CVS','MO','LOW','FIS','AXP','BKNG',
                    # 'UPS','GILD','CHTR','CAT','MDLZ','GS','USB', 'CI','ANTM','BDX',
                    # 'TJX','ADP','TFC','CME','SPGI','COP','INTU','ISRG','CB','SO',
                    # 'D','FISV','PNC','DUK','SYK','ZTS','MS','RTN','AGN','BLK'
                    ]
                    
    # Create custom universe.
    self.UniverseSettings.Resolution = Resolution.Daily
    self.AddUniverseSelection(FineFundamentalUniverseSelectionModel(self.SelectCoarse, self.SelectFine))
    
    self.period = 21
    self.holding_period = 12
    self.quantile = 5
    self.max_SI_missing_days = 5
    self.max_missing_insider_days = 3 * 31
    self.trading_activity_period = 6 * 31
    
    self.symbol = self.AddEquity('SPY', Resolution.Daily).Symbol
    self.managed_queue = []
    
    # Dataframe with insider trades for every stock.
    self.insiders_trading = {}
    
    self.short_interest = {}
    
    for symbol in self.symbols:
        # Import insiders trading data.
        csv_string_file = self.Download(f'data.quantpedia.com/backtesting_data/economic/insiders_trading/{symbol}.csv')
        if csv_string_file == "": continue
        parser = lambda x: pd.datetime.strptime(x, "%Y-%m-%d")
        self.insiders_trading[symbol] = pd.read_csv(StringIO(csv_string_file), sep=';', parse_dates=['Tran.Date'], date_parser=parser)
        # Import short interest daily data.
        self.AddData(NasdaqCustomColumns, 'FINRA/FNSQ_' + symbol, Resolution.Daily)
        self.short_interest[symbol] = deque(maxlen = self.period)
    
    self.selection_flag = True
    self.Schedule.On(self.DateRules.MonthEnd(self.symbol), self.TimeRules.BeforeMarketClose(self.symbol), self.Selection)
def OnSecuritiesChanged(self, changes):
    for security in changes.AddedSecurities:
        security.SetFeeModel(CustomFeeModel())
        security.SetLeverage(10)
def SelectCoarse(self, coarse):
    if not self.selection_flag:
        return Universe.Unchanged
    
    return [Symbol.Create(x, SecurityType.Equity, Market.USA) for x in self.symbols]
    
def SelectFine(self, fine):
    fine = [x for x in fine if x.Symbol.Value in self.insiders_trading]
    
    short_interest = {}
    
    for stock in fine:
        symbol = stock.Symbol
        ticker = symbol.Value
    
        # Last month's short_interest data is ready.
        if len(self.short_interest[ticker]) == self.short_interest[ticker].maxlen:
            if self.Securities['FINRA/FNSQ_' + ticker].GetLastData() and (self.Time.date() - self.Securities['FINRA/FNSQ_' + ticker].GetLastData().Time.date()).days > self.max_SI_missing_days:
                self.short_interest[ticker].clear()
                continue
            # Calculate monthly short interest.
            short_interest[symbol] = sum([x[0] for x in self.short_interest[ticker]]) / sum([x[1] for x in self.short_interest[ticker]])
    
    if len(short_interest)  self.max_missing_insider_days:
            continue
        trades = [row['Tran.Date'] for index, row in self.insiders_trading[ticker].iterrows() if row['Symbol'] == ticker and row['Tran.Date'] >= (self.Time - timedelta(days = self.trading_activity_period)) and row['Tran.Date']  None:
    self.ValueColumnName = 'shortvolume'    # also 'TOTALVOLUME' is accesible
