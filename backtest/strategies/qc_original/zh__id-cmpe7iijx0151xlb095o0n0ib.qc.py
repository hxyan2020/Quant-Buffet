# Original QuantConnect / library Python
# locale=zh slug="风险管理的行业动量"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

from AlgorithmImports import *
class RiskManagedIndustryMomentum(QCAlgorithm):
def Initialize(self):
    self.SetStartDate(2010, 1, 1)
    self.SetCash(100000)
    self.symbols = ["XLY", # Consumer Discretionary Select Sector SPDR Fund
                    "PBS", # Invesco Dynamic Media ETF
                    "PEJ", # Invesco Dynamic Leisure and Entertainment ETF
                    "PMR", # Invesco Dynamic Retail ETF
                    
                    "XLP", # Consumer Staples Select Sector SPDR Fund
                    "PBJ", # Invesco Dynamic Food & Beverage ETF
                    
                    "XLE", # Energy Select Sector SPDR Fund
                    "PBW", # Invesco WilderHill Clean Energy ETF
                    "PXE", # Invesco Dynamic Energy Exploration & Production ETF
                    "NLR", # VanEck Vectors Uranium+Nuclear Energy ETF
                    "AMJ", # JPMorgan Alerian MLP Index ETN
                    
                    "XLF", # Financial Select Sector SPDR Fund
                    "KBE", # SPDR S&P Bank ETF
                    "KIE", # SPDR S&P Insurance ETF
                    "KRE", # SPDR S&P Regional Banking ETF
                    "PSP", # Invesco Global Listed Private Equity ETF
                    
                    "XLV", # Health Care Select Sector SPDR Fund
                    "IBB", # iShares Nasdaq Biotechnology ETF
                    "IHF", # iShares U.S. Healthcare Providers ETF
                    "IHE", # iShares U.S. Pharmaceuticals ETF
                    
                    "XLI", # Industrial Select Sector SPDR Fund
                    "ITA", # iShares U.S. Aerospace & Defense ETF
                    "IYT", # iShares Transportation Average ETF
                    "PHI", # Invesco Water Resources ETF
                    
                    "XLB", # Materials Select Sector SPDR ETF
                    "MOO", # VanEck Vectors Agribusiness ETF
                    "GDX", # VanEck Vectors Gold Miners ETF
                    "XHB", # SPDR S&P Homebuilders ETF
                    "IGE", # iShares North American Natural Resources ETF
                    
                    "XLK", # Technology Select Sector SPDR Fund
                    "FDN", # First Trust Dow Jones Internet Index
                    "SOXX", # iShares PHLX Semiconductor ETF
                    "IGV", # iShares Expanded Tech-Software Sector ET
                    "IYZ", # iShares U.S. Telecommunications ETF
                    
                    "XLU", # Utilities Select Sector SPDR Fund
                    "IGF", # iShares Global Infrastructure ETF
                    ]
    self.period = 21
    self.SetWarmUp(self.period)
    self.data = {}
    
    for symbol in self.symbols:
        data = self.AddEquity(symbol, Resolution.Daily)
        data.SetLeverage(10)
        
        self.data[symbol] = RollingWindow[float](self.period)
        
    self.Schedule.On(self.DateRules.MonthStart(self.symbols[0]), self.TimeRules.AfterMarketOpen(self.symbols[0]), self.Rebalance)
def OnData(self, data):
    for symbol in self.data:
        if symbol in data and data[symbol]:
            price = data[symbol].Value
            self.data[symbol].Add(price)
                
def Rebalance(self):
    if self.IsWarmingUp: return

    # Return sorting
    return_volatility = {}
    for symbol in self.symbols:
        if self.data[symbol].IsReady:
            prices = np.array([x for x in self.data[symbol]])
            ret = prices[0] / prices[-1] - 1
            
            daily_returns = prices[:-1] / prices[1:] - 1
            vol = np.std(daily_returns) * np.sqrt(252)
            return_volatility[symbol] = (ret, vol)
    sorted_by_return = sorted(return_volatility.items(), key = lambda x: x[1][0], reverse = True)
    sixth = int(len(sorted_by_return) / 6)
    long = [x for x in sorted_by_return[:sixth]]
    short = [x for x in sorted_by_return[-sixth:]]
    # Volatility weighting
    total_vol_long = sum([1/x[1][1] for x in long])
    weight = {}
    for symbol, ret_vol in long:
        vol = ret_vol[1]
        if vol != 0:
            weight[symbol] = (1.0 / vol) / total_vol_long
        else: 
            weight[symbol] = 0
    total_vol_short = sum([1/x[1][1] for x in short])
    for symbol, ret_vol in short:
        vol = ret_vol[1]
        if vol != 0:
            weight[symbol] = -(1.0 / vol) / total_vol_short
        else: 
            weight[symbol] = 0
    
    # Trade execution.
    invested = [x.Key.Value for x in self.Portfolio if x.Value.Invested]
    for symbol in invested:
        if symbol not in weight:
            self.Liquidate(symbol)
    
    for symbol, w in weight.items():
        self.SetHoldings(symbol, w)
