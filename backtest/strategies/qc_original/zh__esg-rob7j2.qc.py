# Original QuantConnect / library Python
# locale=zh slug="货币中的esg因素"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

from AlgorithmImports import *
import data_tools
#endregion
class ESGInCurrencies(QCAlgorithm):
def Initialize(self):
    self.SetStartDate(2016, 1, 1) # first esg data are from 2016
    self.SetCash(100000)
    
    # switching ratings from letters to number for easier sorting
    self.rating_switcher = {
        'AAA': 9,
        'AA': 8,
        'A': 7,
        'BBB': 6,
        'BB': 5,
        'B': 4,
        'CCC': 3,
        'CC': 2,
        'C': 1,
    }
    
    self.indexes_currencies = {
        'ASX': 'AUDUSD', # Australia
        # 'DJ30':  # USA
        'EUROSTOXX': 'EURUSD', # Europe
        'FTSE100': 'GBPUSD', # Britain
        'NIKKEI': 'USDJPY', # Japan
        'NZX50': 'NZDUSD', # New Zeland
        'SMI': 'USDCHF', # Switzerland
        'TSX': 'USDCAD' # Canada
    }
    
    self.securities_count = 2 # long n securities and short n securities
    self.max_missing_days = 31
    
    self.data = {} # storing objects of SymbolData class keyed by tickers
    
    # subscribe to esg indexes data
    for index_ticker, currency_ticker in self.indexes_currencies.items():
        index_esg = self.AddData(data_tools.IndexESG, index_ticker, Resolution.Daily)
        currency = self.AddForex(currency_ticker, Resolution.Daily, Market.Oanda)
        # currency = self.AddData(data_tools.QuantpediaFutures, currency_ticker, Resolution.Daily)
        currency.SetLeverage(5)
        
        # create SymbolData object for current index
        self.data[index_ticker] = data_tools.SymbolData(index_esg.Symbol, currency.Symbol)
        
    self.symbol = self.AddEquity('SPY', Resolution.Daily).Symbol
    
    self.months_counter = 0    
    self.selection_flag = False
    self.UniverseSettings.Resolution = Resolution.Daily
    self.Schedule.On(self.DateRules.MonthStart(self.symbol), self.TimeRules.AfterMarketOpen(self.symbol), self.Selection)
def OnData(self, data):
    # update esg data on daily basis
    for index_ticker, symbol_obj in self.data.items():
        index_esg_symbol = symbol_obj.index_esg_symbol
        
        if index_esg_symbol in data and data[index_esg_symbol]:
            # get ratings for current date
            ratings = [x for x in data[index_esg_symbol].Ratings]
            # get and convert valid ratings
            valid_ratings:list = self.GetValidRatings(ratings)
            # add valid ratings to all index ratings for current year
            symbol_obj.esg_ratings = symbol_obj.esg_ratings + valid_ratings
    
    # rebalance yearly
    if not self.selection_flag:
        return
    self.selection_flag = False
    
    # get mean of index esg rating keyed by currency symbol
    mean_esg_ratings:dict = {}
    
    for index_ticker, symbol_obj in self.data.items():
        if self.Securities[index_ticker].GetLastData() and (self.Time.date() - self.Securities[index_ticker].GetLastData().Time.date()).days > self.max_missing_days:
            continue
        # check if esg data are ready
        if len(symbol_obj.esg_ratings)
