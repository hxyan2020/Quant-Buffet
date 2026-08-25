# Original QuantConnect / library Python
# locale=zh slug="利用vix进行期权时机选择"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

from collections import deque
from AlgorithmImports import *
import numpy as np
from QuantConnect.Python import PythonQuandl
class UsingVIXtoTimeOptionsWriting(QCAlgorithm):
def Initialize(self):
    self.SetStartDate(2015, 1, 1)
    self.SetCash(100000)
    
    self.symbol = self.AddEquity("SPY", Resolution.Minute).Symbol
    data = self.AddEquity("BIL", Resolution.Minute)
    data.SetLeverage(2)
    self.bills = data.Symbol
    
    # SPY options.
    option = self.AddOption("SPY", Resolution.Minute)
    option.SetFilter(-20, 20, 25, 35)
    # Vix spot.
    self.vix_spot = self.AddData(CBOE, 'VIX', Resolution.Daily).Symbol
    
    # VIX historical monthly data.
    self.data = None
    # Get vix history.
    history = self.History(self.vix_spot, 10*12*30, Resolution.Daily)
    if 'close' in history.columns:
        closes = history['close']
        self.data = deque(closes)
    
    # Next expiration date.
    self.expiration_date = None
def OnData(self, slice):
    # store VIX price
    if self.vix_spot in slice and slice[self.vix_spot]:
        price = slice[self.vix_spot].Value
        self.data.append(price)
        
    # Open new trades only on market close.
    if not (self.Time.hour == 15 and self.Time.minute == 59):
        return
    
    # At least year of data is ready.
    if len(self.data)
