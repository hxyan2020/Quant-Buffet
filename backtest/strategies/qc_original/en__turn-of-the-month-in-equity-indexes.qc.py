# Original QuantConnect / library Python
# locale=en slug="turn-of-the-month-in-equity-indexes"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

from AlgoLib import *

class MonthlyMarketTiming(XXX):

def Initialize(self):
    self.SetStartDate(1998, 1, 1)  # Set the start date
    self.SetCash(100000)  # Set the initial capital
    
    self.spy = self.AddEquity("SPY", Resolution.Daily).Symbol  # Add SPY ETF
    
    self.readyToSell = False  # Flag to trigger selling
    self.tradeDaysCount = 0  # Count trade days since buying
    
    # Schedule the buy action at the month's end
    self.Schedule.On(self.DateRules.MonthEnd(self.spy), self.TimeRules.AfterMarketOpen(self.spy), self.EnterPosition)
    # Schedule the sell action 3 trading days after the start of the month
    self.Schedule.On(self.DateRules.MonthStart(self.spy), self.TimeRules.AfterMarketOpen(self.spy), self.InitiateSell)

def EnterPosition(self):
    self.SetHoldings(self.spy, 1)  # Invest all in SPY

def InitiateSell(self):
    self.readyToSell = True  # Set flag to start counting days to sell
    
def OnData(self, data):
    if self.readyToSell:
        self.tradeDaysCount += 1  # Increment the day count
        if self.tradeDaysCount == 3:  # On the third day, sell
            self.Liquidate(self.spy)  # Sell all SPY shares
            self.readyToSell = False  # Reset the flag
            self.tradeDaysCount = 0  # Reset the day count
