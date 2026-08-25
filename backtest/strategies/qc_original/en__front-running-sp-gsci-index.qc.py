# Original QuantConnect / library Python
# locale=en slug="front-running-sp-gsci-index"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

from AlgorithmImports import *
from io import StringIO
import pandas as pd
#endregion
class FrontRunningSAndPGSCIIndex(QCAlgorithm):

def Initialize(self):
    self.SetStartDate(2010, 1, 1)
    self.SetCash(100000)
    
    self.symbols = {}
    self.trading_day = 0
    self.symbol = self.AddEquity('SPY', Resolution.Daily).Symbol
    
    csv_string_file = self.Download(f'data.quantpedia.com/backtesting_data/economic/future_comodities_RPWD.csv')
    # does not take first row as a header
    separated_file = pd.read_csv(StringIO(csv_string_file), sep=';', header=None)
    
    first_row = True   
    for row in separated_file.itertuples():
        if first_row: # first row includes symbols of future comodities
            first_row = False
            for symbol in row[2:]:
                data = self.AddData(QuantpediaFutures, symbol, Resolution.Daily)
                data.SetFeeModel(CustomFeeModel())
                self.symbols[symbol] = {}
        else:
            for (value), (symbol) in zip(row[2:], self.symbols):
                self.symbols[symbol][int(row[1])] = value # second element in row is year
    
def OnData(self, data):
    if self.Time.month == 1:
        if self.trading_day == 5:
            short = {}
            total_weight_changed = 0
            
            for symbol in self.symbols:
                year = self.Time.year # get current year
                # check if future comodity has weight for current year and year before
                if (year in self.symbols[symbol]) and ((year - 1) in self.symbols[symbol]):
                    weight_change = float(self.symbols[symbol][year]) - float(self.symbols[symbol][year - 1])
                    if weight_change
