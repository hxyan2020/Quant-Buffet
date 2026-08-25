# Original QuantConnect / library Python
# locale=en slug="currency-momentum-factor"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

import data_tools
from AlgoLib import *

class CurrencyMomentumFactor(XXX):
'''This class implements a currency momentum factor strategy using futures contracts. It selects 
a subset of currencies based on their momentum, calculated over a predefined period, and 
rebalances the portfolio monthly into long and short positions.'''

def Initialize(self):
    '''Initializes the algorithm settings, including start date, initial cash, data subscriptions,
    fee model, leverage, and indicators. It also sets a warm-up period to pre-load historical data 
    for the momentum calculation.'''
    
    self.SetStartDate(2000, 1, 1)  # Set the starting date for the backtest
    self.SetCash(100000)  # Set the initial cash

    self.data = {}  # Initialize a dictionary to store data subscriptions
    self.period = 12 * 21  # Define the lookback period for momentum calculation
    self.SetWarmUp(self.period, Resolution.Daily)  # Set a warm-up period

    self.symbols = [
        "CME_AD1", "CME_BP1", "CME_CD1", "CME_EC1", 
        "CME_JY1", "CME_MP1", "CME_NE1", "CME_SF1"
    ]
    # List of futures contracts to trade
    
    for symbol in self.symbols:
        data = self.AddData(data_tools.QuantpediaFutures, symbol, Resolution.Daily)
        data.SetFeeModel(data_tools.CustomFeeModel())
        data.SetLeverage(5)
        self.data[symbol] = self.ROC(symbol, self.period, Resolution.Daily)
    
    self.recent_month = -1  # Variable to track the current month for monthly rebalancing
    
def OnData(self, data):
    '''This method is called whenever new data is received. It checks whether it's time to rebalance
    the portfolio based on the current month. If so, it calculates the performance of each currency 
    based on the Rate of Change (ROC) indicator, ranks them, and then rebalances the portfolio into 
    long and short positions accordingly.'''
    
    if self.IsWarmingUp:  # Skip if data is being warmed up
        return

    if self.Time.month == self.recent_month:  # Check for monthly rebalancing
        return
    self.recent_month = self.Time.month

    performance = {x[0]: x[1].Current.Value for x in self.data.items() if self.data[x[0]].IsReady and x[0] in data and data[x[0]]}
    # Calculate performance and filter ready symbols
    
    long_symbols = []
    short_symbols = []
    if len(performance) >= 6:  # Ensure there are enough symbols for ranking
        sorted_performance = sorted(performance.items(), key=lambda x: x[1], reverse=True)
        long_symbols = [x[0] for x in sorted_performance[:3]]  # Select top 3 for long positions
        short_symbols = [x[0] for x in sorted_performance[-3:]]  # Select bottom 3 for short positions

    
    invested_symbols = [x.Key.Value for x in self.Portfolio if x.Value.Invested] # Execute trades
    for symbol in invested_symbols:
        if symbol not in long_symbols + short_symbols:
            self.Liquidate(symbol)  # Liquidate positions not in the current long or short list
            
    for symbol in long_symbols:
        self.SetHoldings(symbol, 1 / len(long_symbols))  # Set holdings for long positions
    for symbol in short_symbols:
        self.SetHoldings(symbol, -1 / len(short_symbols))  # Set holdings for short positions
