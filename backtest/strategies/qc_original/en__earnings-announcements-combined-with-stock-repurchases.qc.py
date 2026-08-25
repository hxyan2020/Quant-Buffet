# Original QuantConnect / library Python
# locale=en slug="earnings-announcements-combined-with-stock-repurchases"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

from AlgoLib import *
import numpy as np
#endregion

class EarningsAnnouncementsCombinedWithStockRepurchases(XXX):

def Initialize(self):
    self.SetStartDate(2011, 1, 1) # Buyback data strats at 2011
    self.SetCash(100000) 
    
    self.fine = {}
    self.price = {}
    self.managed_symbols = []
    self.earnings_universe = []
    
    self.earnings = {}
    self.buybacks = {}
    
    self.max_traded_stocks = 40 # maximum number of trading stocks
    self.quantile = 4
    
    self.symbol = self.AddEquity("SPY", Resolution.Daily).Symbol
    
    # load earnings dates
    csv_data = self.Download('data.quantpedia.com/backtesting_data/economic/earning_dates.csv')
    lines = csv_data.split('\r\n')
    
    for line in lines:
        line_split = line.split(';')
        date = line_split[0]
        
        if date == '' :
            continue
        
        date = datetime.strptime(date, "%Y-%m-%d").date()
        self.earnings[date] = []
        
        for ticker in line_split[1:]: # skip date in current line
            self.earnings[date].append(ticker)
            
            if ticker not in self.earnings_universe:
                self.earnings_universe.append(ticker)
    
    # load buyback dates
    csv_data = self.Download('data.quantpedia.com/backtesting_data/equity/BUY_BACKS.csv')
    lines = csv_data.split('\r\n')
    
    for line in lines[1:]: # skip header
        line_split = line.split(';')
        date = line_split[0]
        
        if date == '' :
            continue
        
        date = datetime.strptime(date, "%d.%m.%Y").date()
        self.buybacks[date] = []
        
        for ticker in line_split[1:]: # skip date in current line
            self.buybacks[date].append(ticker)
    
    self.months_counter = 0
    self.selection_flag = False
    self.UniverseSettings.Resolution = Resolution.Daily
    self.AddUniverse(self.CoarseSelectionFunction, self.FineSelectionFunction)
    self.Schedule.On(self.DateRules.MonthStart(self.symbol), self.TimeRules.AfterMarketOpen(self.symbol), self.Selection)
    
def OnSecuritiesChanged(self, changes):
    for security in changes.AddedSecurities:
        security.SetFeeModel(CustomFeeModel())
        security.SetLeverage(5)
        
def CoarseSelectionFunction(self, coarse):
    # update stocks last prices
    for stock in coarse:
        ticker = stock.Symbol.Value
        
        if ticker in self.earnings_universe:
            # store stock's last price
            self.price[ticker] = stock.AdjustedPrice
    
    # rebalance quarterly
    if not self.selection_flag:
        return Universe.Unchanged
    self.selection_flag = False
    
    # select stocks, which had spin off
    selected = [x.Symbol for x in coarse if x.Symbol.Value in self.earnings_universe]

    return selected
    
def FineSelectionFunction(self, fine):
    fine = [x for x in fine if x.MarketCap != 0 and 
                                ((x.SecurityReference.ExchangeId == "NYS") or
                                (x.SecurityReference.ExchangeId == "NAS") or 
                                (x.SecurityReference.ExchangeId == "ASE"))]
    
    if len(fine)  None:
    remove_managed_symbols = []
    # maybe there should be BDay(15)
    liquidate_date = self.Time.date() - timedelta(15)
    
    # check if bought stocks have 15 days after earnings annoucemnet
    for managed_symbol in self.managed_symbols:
        if managed_symbol.earnings_date >= liquidate_date:
            remove_managed_symbols.append(managed_symbol)
            
            # liquidate stock by selling it's quantity
            self.MarketOrder(managed_symbol.symbol, -managed_symbol.quantity)
            
    # remove liquidated stocks from self.managed_symbols
    for managed_symbol in remove_managed_symbols:
        self.managed_symbols.remove(managed_symbol)
    
    # maybe there should be BDay(10)
    after_current = self.Time.date() + timedelta(10)
    
    if after_current in self.earnings:
        # this stocks has earnings annoucement after 10 days
        stocks_with_earnings = self.earnings[after_current]
        
        # 30 days before earnings annoucement
        buyback_start = self.Time.date() - timedelta(20)
        # 15 days before earnings annoucement
        buyback_end = self.Time.date() - timedelta(5)
        
        stocks_with_buyback = [] # storing stocks with buyback in period -30 to -15 days before earnings annoucement
        
        for buyback_date, tickers in self.buybacks.items():
            # check if buyback date is in period before earnings annoucement
            if buyback_date >= buyback_start and buyback_date
