# Original QuantConnect / library Python
# locale=en slug="abnormal-turnover-in-china"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

import numpy as np
class AbnormalTurnoverInChina(QCAlgorithm):
def Initialize(self):
    self.SetStartDate(2010, 1, 1)
    self.SetCash(100000)
    
    self.period = 250       # Storing 250 daily turnovers
    self.min_period = 20    # Calculate average of last n daily turnovers
    
    self.data = {}
    self.weight = {}
    
    self.symbol = self.AddEquity('SPY', Resolution.Daily).Symbol
    
    self.stock_outstanding = {}
    
    self.selection_flag = False
    self.UniverseSettings.Resolution = Resolution.Daily
    self.AddUniverse(self.CoarseSelectionFunction, self.FineSelectionFunction)
    self.Schedule.On(self.DateRules.MonthStart(self.symbol), self.TimeRules.AfterMarketOpen(self.symbol), self.Selection)
def OnSecuritiesChanged(self, changes):
    for security in changes.AddedSecurities:
        security.SetFeeModel(CustomFeeModel(self))
        security.SetLeverage(5)
        
def CoarseSelectionFunction(self, coarse):
    # Update the rolling window every day.
    for stock in coarse:
        symbol = stock.Symbol
        # Store daily volume.
        if symbol in self.data:
            if symbol in self.stock_outstanding:
                # NOTE: Updated basic average share count is used.
                self.data[symbol].update(stock.Volume / self.stock_outstanding[symbol])
    
    # Rebalace monthly
    if not self.selection_flag:
        return Universe.Unchanged
    
    # Select all stocks with fundamental data and 
    # they will be filtered in FineSelectionFunction based on strategy description
    return [x.Symbol for x in coarse if x.HasFundamentalData]
def FineSelectionFunction(self, fine):
    # Filter chinese stocks by BusinessCountryID 
    fine = [x for x in fine if x.MarketCap != 0 and x.EarningReports.BasicAverageShares.ThreeMonths != 0 and x.CompanyReference.BusinessCountryID == 'CHN']
    
    # Exclude 30% of lowest stocks by MarketCap
    sorted_by_market_cap = sorted(fine, key = lambda x: x.MarketCap)
    fine = sorted_by_market_cap[int(len(sorted_by_market_cap) * 0.3):]
    
    market_cap = {}
    abnormal_turnover = {}
    
    for stock in fine:
        symbol = stock.Symbol
        
        self.stock_outstanding[symbol] = stock.EarningReports.BasicAverageShares.ThreeMonths
        # Get stock's turnover.
        if symbol not in self.data:
            self.data[symbol] = SymbolData(self.period)
        # Calculate abnormal turnover only if stock has enough data
        if not self.data[symbol].is_ready():
            continue
        
        # Store market cap for value weighting
        market_cap[symbol] = stock.MarketCap
        
        # Calculate avg daily turnovers based on values in self.min_period and self.period
        short_period_turnover = self.data[symbol].avg_daily_turnover(self.min_period)
        long_period_turnover = self.data[symbol].avg_daily_turnover(self.period)
        
        # Calculate abnormal turnover base ond min and max avg daily turnovers for current stock
        abnormal_turnover[symbol] = short_period_turnover / long_period_turnover
    
    if len(abnormal_turnover)
