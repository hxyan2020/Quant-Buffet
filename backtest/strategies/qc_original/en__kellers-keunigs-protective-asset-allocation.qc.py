# Original QuantConnect / library Python
# locale=en slug="kellers-keunigs-protective-asset-allocation"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

from AlgorithmImports import *
#endregion

class KellersKeunigsPAA(QCAlgorithm):

def Initialize(self):
    self.SetStartDate(2000, 1, 1)  
    self.SetCash(100000)
    
    # Parameters for algorithm 
    self.lookback:int = 12 * 21                 # Lookback period (in months)
    self.protection:int = 2                     # Protection factor = 0 (low), 1, 2 (high)
    self.topM:int = 6                           # topM is the max number of equities
    self.n_levels:int = 2                       # number of discrete levels for bond_fraction (>=2)
    self.cash_universe:List[str] = ["SHY"]      # risk free asset to move into for protection 
    self.N_safe:int = int(len(self.cash_universe))

    self.risky_universe:List[str] = [
        "SPY", "QQQ", "IWM",
        "VGK", "EWJ", "EEM",
        "IYR", "GSG", "GLD"
        ]

    self.N_eq:int = len(self.risky_universe)

    sec = self.AddSecurity(SecurityType.Equity, "SHY", Resolution.Minute)
    sec.MarketPrice = self.GetLastKnownPrice(sec)
    
    self.symbol_objs = []
    
    for ticker in list(self.risky_universe):
        self.symbol_objs.append(self.AddSecurity(SecurityType.Equity, ticker, Resolution.Minute).Symbol)
    
    for symbol_obj in self.symbol_objs:
        symbol_obj.lookback_ma = self.SMA(symbol_obj, self.lookback, Resolution.Daily)
        
    self.SetWarmup(self.lookback, Resolution.Daily)
    self.recent_month:int = -1

def OnData(self, data:Slice) -> None:
    if self.IsWarmingUp: return

    if not (self.cash_universe[0] in data and data[self.cash_universe[0]]):
        return

    if not(self.Time.hour == 9 and self.Time.minute == 45):
        return

    if self.Time.month == self.recent_month:
        return
    self.recent_month = self.Time.month

    # poll the Risk Universe set to determine the number of assets with positive momentum
    n = 0
    for symbol_obj in self.symbol_objs:
        if symbol_obj in data and data[symbol_obj]:
            if symbol_obj.lookback_ma.IsReady:
                price = data[symbol_obj].Value
                sma = symbol_obj.lookback_ma.Current.Value
                if price > sma: n += 1
    
    # Calculate the bond fraction based on N_eq, prot, and n
    # This is the portion to be invested in safe harbor
    # Calculate equity fraction and weight per equity (frac_eq, w_eq) 
    # Limit bond_fraction to a discrete number of levels (n_levels >=2)
    
    # n1 = a*N/4
    n1:float = (self.protection * self.N_eq) / 4.0
    # BF = (N-n)/(N-n1)
    bond_fraction:float = min(1.0, (float(self.N_eq) - float(n)) / (float(self.N_eq) - n1))
    w_safe:float = bond_fraction
    
    # calculate the MOM for each equity determine the number of equities to be purchases
    N = 0
    for symbol_obj in self.symbol_objs:
        symbol_obj.MOM = 0.

        if symbol_obj in data and data[symbol_obj]:
            if symbol_obj.lookback_ma.IsReady:
                price = data[symbol_obj].Value
                sma = symbol_obj.lookback_ma.Current.Value
                symbol_obj.MOM = (price / sma) - 1
                if symbol_obj.MOM > 0.0: N+=1
    
    if N == 0:
        self.Liquidate()
        return

    frac_eq:float = 1.0 - w_safe
    n_eq:int = min(N, self.topM)
    w_eq:float = 0.
    if N > 0: w_eq = frac_eq / float(n_eq)
    mom_threshold = sorted([i.MOM for i in self.symbol_objs if i.MOM != 0.], reverse=True)[n_eq - 1]
    
    if frac_eq > 0.0:
        for symbol_obj in self.symbol_objs:
            if symbol_obj.MOM >= float(mom_threshold):
                self.SetHoldings(symbol_obj, w_eq)
            else:
                if self.Portfolio[symbol_obj].Invested:
                    self.Liquidate(symbol_obj)

        self.SetHoldings(self.cash_universe[0], w_safe)
    else:
        for symbol_obj in self.symbol_objs:
            if self.Portfolio[symbol_obj].Invested:
                self.Liquidate(symbol_obj)

        self.SetHoldings(self.cash_universe[0], 1.0)
