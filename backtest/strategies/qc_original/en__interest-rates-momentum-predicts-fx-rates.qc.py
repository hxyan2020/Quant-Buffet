# Original QuantConnect / library Python
# locale=en slug="interest-rates-momentum-predicts-fx-rates"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

import data_tools
from AlgorithmImports import *
import numpy as np
class InterestRatesMomentumPredictsFXRates(QCAlgorithm):
def Initialize(self):
    self.SetStartDate(2000, 1, 1)
    self.SetCash(100000)
    
    # Country symbol and currency future symbol.
    self.symbols = {
                    "USD" : "not_traded", # US Dollar index Futures, Continuous Contract #1
                    "EUR" : "CME_EC1", # Euro FX Futures, Continuous Contract #1
                    "GBP" : "CME_BP1", # British Pound Futures, Continuous Contract #1
                    "CHF" : "CME_SF1", # Swiss Franc Futures, Continuous Contract #1
                    "JPY" : "CME_JY1", # Japanese Yen Futures, Continuous Contract #1
                    }
    # Interest rate data.
    self.interest_rate = self.AddData(data_tools.InterestRate, 'InterestRate', Resolution.Daily).Symbol
    
    self.period = 15
    self.yield_difference = {}
    
    countries = [x[0] for x in self.symbols.items()]
    for i, country1 in enumerate(countries):
        for j, country2 in enumerate(countries):
            if i = 5:
        self.Liquidate()
        return
    
    countries = [x[0] for x in self.symbols.items()]
    signal = {}
    for i, country1 in enumerate(countries):
        sub_signal = {}
        for j, country2 in enumerate(countries):
            if i  0:
            abs_percentile = np.percentile([abs(x[1]) for x in sub_signal.items()], 50)
            
            for signal_index, sig in sub_signal.items():
                iter_country1 = signal_index[:3]
                iter_country2 = signal_index[-3:]
                if abs(sig) > abs_percentile:
                    if iter_country1 != 'USD':
                        iter_future1 = self.symbols[iter_country1]
                        if iter_future1 not in signal:
                            signal[iter_future1] = 0
                        signal[iter_future1] += np.sign(sig)
                        
                    if iter_country2 != 'USD':
                        iter_future2 = self.symbols[iter_country2]
                        if iter_future2 not in signal:
                            signal[iter_future2] = 0
                        signal[iter_future2] -= np.sign(sig)
    
    if len(signal) != 0:
        futures_invested = [x.Key.Value for x in self.Portfolio if x.Value.Invested]
        for currency_future in futures_invested:
            if currency_future not in signal:
                self.Liquidate(currency_future)
        
        foo = 3
        
        for currency_future, country_signal in signal.items():
            self.SetHoldings(currency_future, country_signal)
