# Original QuantConnect / library Python
# locale=en slug="barbell-strategy"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

from AlgorithmImports import *
class VolatilityRiskPremiumEffect(QCAlgorithm):
def Initialize(self):
    self.SetStartDate(2010, 1, 1)
    self.SetCash(1000000)
    
    data = self.AddEquity("IEF", Resolution.Minute)
    data.SetLeverage(5)
    self.symbol = data.Symbol
    
    option = self.AddOption("IEF", Resolution.Minute)
    # first parameter is min strike, second is max strike, third is min expiry and fourth is max expiry 
    option.SetFilter(-20, 20, timedelta(days=360), timedelta(days=500))
    
    self.delta_target = 0.7
    
    # storing an entire chain of option contracts for a single underlying security
    self.chains = None

    self.recent_month = -1
    self.traded_flag = False
    
def OnData(self,slice):
    # We have to check options contracts each minute,
    # because we don't exactly know, when they are available
    for i in slice.OptionChains:
        self.chains = i.Value
    
    # Check once a quarter.
    if self.Time.month == self.recent_month:
        return
    
    if self.Time.month in [3,6,9,12] and not self.traded_flag:
        self.recent_month = self.Time.month
    else:
        self.traded_flag = False
        return
    
    # Continue only if we have any option contracts
    if self.chains != None:
        # divide option chains into call and put options 
        calls = list(filter(lambda x: x.Right == OptionRight.Call, self.chains))
        
        # if lists are empty return
        if not calls: return
            
        underlying_price = self.Securities[self.symbol].Price
        expiries = [i.Expiry for i in calls]
        
        # determine expiration date nearly one month
        # expiry = min(expiries, key=lambda x: abs((x.date()-self.Time.date()).days-30))
        expiry = min(expiries, key=lambda x: abs((x.date()-self.Time.date()).days-360))
        strikes = [i.Strike for i in calls]
        
        # determine at-the-money strike
        strike = min(strikes, key=lambda x: abs(x-underlying_price))
        
        # determine ITM strike by delta
        itm_call = min([c for c in calls if c.Expiry == expiry], key=lambda x: abs(x.Greeks.Delta-self.delta_target))

        if itm_call:
            options_q = int((self.Portfolio.TotalPortfolioValue*0.03) / (underlying_price * 100))
            # set leverage
            self.Securities[itm_call.Symbol].MarginModel = BuyingPowerModel(5)
            
            # buy ITM call
            self.Buy(itm_call.Symbol, options_q)
            
            # buy index.
            self.SetHoldings(self.symbol, 0.88)
            self.traded_flag = True
            
    else: # In this case we don't have any option contracts ready, so we will liquidate IEF, if it is the only asset in portfolio
        invested = [x.Key.Value for x in self.Portfolio]
        if len(invested) == 1:
            self.Liquidate()
