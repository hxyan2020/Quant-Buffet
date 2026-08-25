# Original QuantConnect / library Python
# locale=en slug="timing-vix-etns"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

from AlgorithmImports import *
#endregion
class TimingVIXETNs(QCAlgorithm):
def Initialize(self):
    self.SetStartDate(2012, 1, 1)
    self.SetCash(100000)
    
    self.symbols = ['SVXY', 'VIXM', 'XVZ']
    for symbol in self.symbols:
        data = self.AddEquity(symbol, Resolution.Daily)
        data.SetLeverage(5)
    self.vix = self.AddData(CBOE, 'VIX', Resolution.Daily).Symbol
    self.vxv = self.AddData(CBOE, 'VIX3M', Resolution.Daily).Symbol
    self.settings.daily_precise_end_time = False
def OnData(self, data):
    if not all(x in data for x in self.symbols): 
        self.Liquidate()
        return

    if self.vix in data and self.vxv in data:
        vix_price = data[self.vix].Value
        vxv_price = data[self.vxv].Value
        
        if vix_price != 0 and vxv_price != 0:
            ratio = float(vix_price / vxv_price)
            
            if ratio
