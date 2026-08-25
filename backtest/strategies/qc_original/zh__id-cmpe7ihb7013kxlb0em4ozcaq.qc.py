# Original QuantConnect / library Python
# locale=zh slug="卖空回补天数策略"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

import numpy as np
from AlgorithmImports import *
class ShortInterestEffect(QCAlgorithm):
def Initialize(self):
    self.SetStartDate(2015, 1, 1)
    self.SetCash(100000)
    # NOTE: We use only s&p 100 stocks so it's possible to fetch short interest data from quandl.
    self.symbols = ['AAPL','MSFT','AMZN','FB','BRK.B','GOOGL','GOOG','JPM','JNJ','V','PG','XOM','UNH','BAC','MA','T','DIS','INTC','HD','VZ','MRK','PFE','CVX','KO','CMCSA','CSCO','PEP','WFC','C','BA','ADBE','WMT','CRM','MCD','MDT','BMY','ABT','NVDA','NFLX','AMGN','PM','PYPL','TMO','COST','ABBV','ACN','HON','NKE','UNP','UTX','NEE','IBM','TXN','AVGO','LLY','ORCL','LIN','SBUX','AMT','LMT','GE','MMM','DHR','QCOM','CVS','MO','LOW','FIS','AXP','BKNG','UPS','GILD','CHTR','CAT','MDLZ','GS','USB','CI','ANTM','BDX','TJX','ADP','TFC','CME','SPGI','COP','INTU','ISRG','CB','SO','D','FISV','PNC','DUK','SYK','ZTS','MS','RTN','AGN','BLK']
    self.period = 21
    self.fine = []
    
    self.symbol = self.AddEquity('SPY', Resolution.Daily).Symbol
    
    self.last_month = -1
    self.selection_flag = False
    self.AddUniverseSelection(FineFundamentalUniverseSelectionModel(self.SelectCoarse, self.SelectFine))
 
    for symbol in self.symbols:
        self.AddData(QuandlFINRA_ShortVolume, 'FINRA/FNSQ_' + symbol, Resolution.Daily)

def SelectCoarse(self, coarse):
    if not self.selection_flag:
        return Universe.Unchanged
        
    return [Symbol.Create(x, SecurityType.Equity, Market.USA) for x in self.symbols]
def SelectFine(self, fine):
    self.fine = [f.Symbol for f in fine] 
    return self.fine

def OnSecuritiesChanged(self, changes):
    for security in changes.AddedSecurities:
        security.SetLeverage(10)
        security.SetFeeModel(CustomFeeModel())

def OnData(self, data):
    # Rebalance once a month.
    if self.last_month != self.Time.month:
        self.selection_flag = True
        self.last_month = self.Time.month
        return
            
    if not self.selection_flag:
        return
    self.selection_flag = False
    
    # Days to cover calc.
    days_to_cover = {}
    for symbol in self.fine:
        ticker = symbol.Value
        
        hist = self.History(symbol, self.period, Resolution.Daily)
        if len(hist) == self.period:
            mean_volume = np.mean(hist.loc[symbol]['volume'])
            shares_outstanding = self.Securities[symbol].Fundamentals.EarningReports.BasicAverageShares.ThreeMonths
            if mean_volume != 0 and shares_outstanding != 0:
                daily_turnover = mean_volume / shares_outstanding
            
                if self.Securities.ContainsKey('FINRA/FNSQ_' + ticker):
                    data = self.Securities['FINRA/FNSQ_' + ticker].GetLastData()
                    if data != None:
                        short_vol = data.GetProperty("SHORTVOLUME")
                        total_vol = data.GetProperty("TOTALVOLUME")
                        if short_vol != 0 and total_vol != 0:
                            short_ratio = short_vol / total_vol
                            days_to_cover[symbol] = short_ratio / daily_turnover
        
    # Sorting by DTC.
    sorted_by_dtc = sorted(days_to_cover.items(), key = lambda x: x[1], reverse = True)
    decile = int(len(sorted_by_dtc) / 10)
    long = [x[0] for x in sorted_by_dtc[-decile:]]
    short = [x[0] for x in sorted_by_dtc[:decile]]
            
    # Trade execution and rebalance.
    long_count = len(long)
    short_count = len(short)
    
    stocks_invested = [x.Key for x in self.Portfolio if x.Value.Invested]
    for symbol in stocks_invested:
        if symbol not in long + short:
            self.Liquidate(symbol)
    for symbol in long:
        if self.Securities[symbol].Price != 0:
            self.SetHoldings(symbol, 1 / long_count)
    for symbol in short:
        if self.Securities[symbol].Price != 0:
            self.SetHoldings(symbol, -1 / short_count)
        
class QuandlFINRA_ShortVolume(PythonQuandl):
def __init__(self):
    self.ValueColumnName = 'SHORTVOLUME'    # also 'TOTALVOLUME' is accesible
# Custom fee model
class CustomFeeModel(FeeModel):
def GetOrderFee(self, parameters):
    fee = parameters.Security.Price * parameters.Order.AbsoluteQuantity * 0.00005
    return OrderFee(CashAmount(fee, "USD"))
