# Original QuantConnect / library Python
# locale=zh slug="期权收益的择时"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

from AlgorithmImports import *
#endregion
class TimingOptionReturns(QCAlgorithm):
def Initialize(self):
    self.SetStartDate(2010, 1, 1)
    self.SetCash(100000)
    
    data = self.AddEquity("SPY", Resolution.Minute)
    self.symbol = data.Symbol
    
    option = self.AddOption("SPY", Resolution.Minute)
    option.SetFilter(-20, 20, 0, 7)
    
def OnData(self, slice):
    if self.symbol not in slice:
        return
    for i in slice.OptionChains:
        chains = i.Value
        if not self.Portfolio.Invested:
            puts = list(filter(lambda x: x.Right == OptionRight.Put, chains))
            if not puts: return
        
            underlying_price = slice[self.symbol].Value
            expiries = [i.Expiry for i in puts]
            
            # Determine expiration date nearly one month.
            expiry = min(expiries, key=lambda x: abs((x.date() - self.Time.date()).days - 7))
            strikes = [i.Strike for i in puts]
            
            # Determine 5% out-of-the-money strike.
            otm_strike = min(strikes, key = lambda x:abs(x - float(0.95) * underlying_price))
            otm_put = [i for i in puts if i.Expiry == expiry and i.Strike == otm_strike]
    
            if otm_put:
                # Sell 10% OTM put.
                options_q = int(self.Portfolio.MarginRemaining / (underlying_price * 100))
                self.Sell(otm_put[0].Symbol, options_q)
