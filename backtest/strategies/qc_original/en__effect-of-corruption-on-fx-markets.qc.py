# Original QuantConnect / library Python
# locale=en slug="effect-of-corruption-on-fx-markets"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

from AlgorithmImports import *
#endregion
class EffectCorruptionFX(QCAlgorithm):
def Initialize(self):
    self.SetStartDate(2010, 1, 1)
    self.SetCash(100000)
    self.symbols = {'CAD' : 'USDCAD',
                    'GBP' : 'USDGBP', 
                    'MXN' : 'USDMXN',
                    'EUR' : 'USDEUR',
                    'NOK' : 'USDNOK', 
                    'CHF' : 'USDCHF',
                    'SEK' : 'USDSEK',
                    'AUD' : 'USDAUD',
                    'NZD' : 'NZDUSD',
                    'JPY' : 'USDJPY', 
                    'HKD' : 'USDHKD',
                    'SGD' : 'USDSGD', 
                    'ZAR' : 'USDZAR',
                    'INR' : 'USDINR'
                    }
    for symbol in self.symbols:
        data = self.AddForex(self.symbols[symbol], Resolution.Daily, Market.FXCM)
    
    self.cpi = self.AddData(CPIData, 'CPI', Resolution.Daily).Symbol
    self.quantile = 3
    first_key = [x for x in self.symbols.keys()][0]
    self.Schedule.On(self.DateRules.MonthStart(self.symbols[first_key]), self.TimeRules.AfterMarketOpen(self.symbols[first_key]), self.Rebalance)
def Rebalance(self):
    if self.Time.month != 1: return
    cpi = {}
    for symbol in self.symbols:
        if self.Securities[self.cpi].GetLastData():
            cpi[symbol] = self.Securities['CPI'].GetLastData()[symbol]
        
    if len(cpi)
