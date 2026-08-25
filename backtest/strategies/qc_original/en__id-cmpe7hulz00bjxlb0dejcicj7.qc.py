# Original QuantConnect / library Python
# locale=en slug="共同基金收益中的动量效应"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

from AlgoLib import *
#endregion

class MomentuminMutualFundReturns(XXX):

def Initialize(self):
    # NOTE: most of the data start from 2014 and until 2015 there wasn't any trade
    self.SetStartDate(2014, 1, 1)
    self.SetCash(100000)
    
    self.data = {}
    self.symbols = []
    
    self.period = 21 * 6 # Storing 6 months of daily prices
    self.quantile = 10
    
    self.symbol = self.AddEquity('SPY', Resolution.Daily).Symbol
    
    # Load csv file with etf symbols and split line with semi-colon
    etf_symbols_csv = self.Download("data.quantpedia.com/backtesting_data/equity/mutual_funds/symbols.csv")
    splitted_csv = etf_symbols_csv.split(';')
    
    for symbol in splitted_csv:
        self.symbols.append(symbol)
        
        # Subscribe for QuantpediaETF by etf symbol, then set fee model and leverage
        data = self.AddData(QuantpediaETF, symbol, Resolution.Daily)
        data.SetFeeModel(CustomFeeModel())
        data.SetLeverage(5)
        
        self.data[symbol] = RollingWindow[float](self.period)
    
    self.recent_month = -1

def OnData(self, data):
    # Update daily prices of etfs
    for symbol in self.symbols:
        if symbol in data and data[symbol]:
            price = data[symbol].Value
            self.data[symbol].Add(price)

    if self.recent_month == self.Time.month:
        return
    self.recent_month = self.Time.month

    # Rebalance quarterly
    if self.recent_month % 3 != 0:
        return
        
    performance = {}
    
    for symbol in self.symbols:
        # If data for etf are ready calculate it's 6 month performance
        if self.data[symbol].IsReady:
            if self.Securities[symbol].GetLastData() and (self.Time.date() - self.Securities[symbol].GetLastData().Time.date()).days
