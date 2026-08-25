# Original QuantConnect / library Python
# locale=en slug="when-short-sellers-and-corporate-insiders-agree-on-stock-pricing"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

from AlgorithmImports import *
from collections import deque
import pandas as pd
import numpy as np
from io import StringIO
#endregion
class WhenShortSellersandCorporateInsidersAgreeonStockPricing(QCAlgorithm):
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
                    
    self.period = 3 * 21
    self.quantile = 4
    self.max_SI_missing_days = 5

    # Create custom universe.
    self.UniverseSettings.Resolution = Resolution.Daily
    self.AddUniverseSelection(FineFundamentalUniverseSelectionModel(self.SelectCoarse, self.SelectFine))
    # Dataframe with insider trades for every stock.
    self.insiders_trading = {}
    
    # Daily short interest data.
    self.short_interest = {}
    
    # Short interest and investor demand quarterly pairs.
    self.data = {}
    
    self.long = []
    self.short = []
    
    self.symbol = self.AddEquity('SPY', Resolution.Daily).Symbol
    
    for symbol in self.symbols:
        # Import insiders trading data.
        csv_string_file = self.Download(f'data.quantpedia.com/backtesting_data/economic/insiders_trading/{symbol}.csv')
        if csv_string_file == "": continue
        parser = lambda x: pd.datetime.strptime(x, "%Y-%m-%d")
        self.insiders_trading[symbol] = pd.read_csv(StringIO(csv_string_file), sep=';', parse_dates=['Tran.Date'], date_parser=parser)
        # Import short interest daily data.
        self.AddData(NasdaqCustomColumns, 'FINRA/FNSQ_' + symbol, Resolution.Daily)
        self.short_interest[symbol] = deque(maxlen = self.period)
    self.selection_flag = False
    self.rebalance_flag = False
    
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
    fine = [x for x in fine if x.EarningReports.BasicAverageShares.ThreeMonths > 0 and x.Symbol.Value in self.insiders_trading]
    # Short interests and demand diffs.
    data_change = {}    
    for stock in fine:
        symbol = stock.Symbol
        ticker = symbol.Value
        if self.Securities['FINRA/FNSQ_' + ticker].GetLastData() and (self.Time.date() - self.Securities['FINRA/FNSQ_' + ticker].GetLastData().Time.date()).days > self.max_SI_missing_days:
            self.data[symbol].clear()
            continue
        # Last month's short_interest data is ready.
        if len(self.short_interest[ticker]) == self.short_interest[ticker].maxlen:
            # Calculate investor demand.
            buys = [row['Shares'] for index, row in self.insiders_trading[ticker].iterrows() if row['Symbol'] == ticker and row['Tran.Date'] >= (self.Time - timedelta(days = self.period)) and row['Tran.Date'] = (self.Time - timedelta(days = self.period)) and row['Tran.Date'] = 4:
                    short_interest_diff = np.diff([x[0] for x in self.data[symbol]])
                    demand_diff = np.diff([x[1] for x in self.data[symbol]])
                    
                    data_change[symbol] = [np.median(short_interest_diff), np.median(demand_diff)]
        
    if len(data_change) >= self.quantile:
        # Sorting by short interest and demand diffs.
        sorted_by_interest_change = sorted(data_change.items(), key = lambda x: x[1][0], reverse = True)
        quantile = int(len(sorted_by_interest_change) / self.quantile)
        high_by_interest_change = [x[0] for x in sorted_by_interest_change[:quantile]]
        low_by_interest_change = [x[0] for x in sorted_by_interest_change[-quantile:]]
        
        sorted_by_demand_change = sorted(data_change.items(), key = lambda x: x[1][1], reverse = True)
        quantile  = int(len(sorted_by_demand_change) / self.quantile)
        high_by_demand_change = [x[0] for x in sorted_by_demand_change[:quantile]]
        low_by_demand_change = [x[0] for x in sorted_by_demand_change[-quantile:]]
        
        self.long = [x for x in high_by_interest_change if x in low_by_demand_change]
        self.short = [x for x in low_by_interest_change if x in high_by_demand_change]
    
    return self.long + self.short
def OnData(self, data):
    # Store short interest data.
    for symbol in self.symbols:
        look_up_symbol = 'FINRA/FNSQ_' + symbol
        if look_up_symbol in data and data[look_up_symbol]:
            short_vol = data[look_up_symbol].GetProperty("SHORTVOLUME")
            total_vol = data[look_up_symbol].GetProperty("TOTALVOLUME")
            
            if symbol in self.short_interest:
                self.short_interest[symbol].append((short_vol, total_vol))
    
    # rebalance once a month     
    if not self.rebalance_flag:
        return
    self.selection_flag = False
    self.rebalance_flag = False
    
    # Trade execution
    stocks_invested = [x.Key for x in self.Portfolio if x.Value.Invested]
    for symbol in stocks_invested:
        if symbol not in self.long + self.short:
            self.Liquidate(symbol)
    long_count = len(self.long)
    short_count = len(self.short)
    
    for symbol in self.long:
        if symbol in data and data[symbol]:
            self.SetHoldings(symbol, 1 / long_count)
    for symbol in self.short:
        if symbol in data and data[symbol]:
            self.SetHoldings(symbol, -1 / short_count)
           
def Selection(self):
    if self.Time.month in [3,6,9,12]:
        # clear long and short selection once every selection period, so that portoflio can be rabalanced monthly even without new selection
        self.long.clear()
        self.short.clear()
        self.selection_flag = True
    
    self.rebalance_flag = True
        
# Custom fee model
class CustomFeeModel(FeeModel):
def GetOrderFee(self, parameters):
    fee = parameters.Security.Price * parameters.Order.AbsoluteQuantity * 0.00005
    return OrderFee(CashAmount(fee, "USD"))
# Quandl short interest data.
class NasdaqCustomColumns(NasdaqDataLink):
def __init__(self) -> None:
    self.ValueColumnName = 'shortvolume'    # also 'TOTALVOLUME' is accesible
