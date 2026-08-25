# Original QuantConnect / library Python
# locale=en slug="long-term-reversal-combined-with-a-momentum-effect-in-industry-portfolios"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

from AlgorithmImports import *
class LongTermReversalCombinedWithMomentumEffectAlgorithm(QCAlgorithm):
def Initialize(self):
    
    self.SetStartDate(2010, 1, 1) 
    self.SetCash(100000)      
    self.tickers = [
        "XLY", # Consumer Discretionary Select Sector SPDR Fund
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
    
    self.data = {} # Storing closes
    self.symbols = []
    
    self.symbol = self.AddEquity('SPY', Resolution.Daily).Symbol
    
    self.current_month = 0
    self.needed_months = 120
    self.months_for_short_perf = 12
    self.period = self.needed_months * 21
    self.SetWarmUp(self.period)
    
    for ticker in self.tickers:
        security = self.AddEquity(ticker, Resolution.Daily)
        security.SetFeeModel(CustomFeeModel())
        security.SetLeverage(5)
        
        self.data[security.Symbol] = SymbolData(self.period)
        self.symbols.append(security.Symbol)
     
    self.selection_flag = False    
    self.Schedule.On(self.DateRules.MonthEnd(self.symbol), self.TimeRules.AfterMarketOpen(self.symbol), self.Selection)
    
def OnData(self, data):
    for symbol in self.symbols:
        if symbol in data:
            if data[symbol]:
                price = data[symbol].Value
                self.data[symbol].update(price)
    
    if self.IsWarmingUp: return
    
    if not self.selection_flag:
        return
    self.selection_flag = False
    
    performances = {}
    for symbol in self.symbols:
        if self.data[symbol].is_ready():
            performances[symbol] = self.data[symbol].performance()
        
    sorted_by_performance = [x[0] for x in sorted(performances.items(), key=lambda item: item[1])]
    
    quartile = int(len(sorted_by_performance) / 4)
    winners = sorted_by_performance[-quartile:]
    losers = sorted_by_performance[:quartile]
            
    short_term_perf_losers = {}
    short_term_perf_winners = {}
    
    for symbol in losers:
        short_term_perf_losers[symbol] = self.data[symbol].short_term_performance(self.months_for_short_perf)
    
    for symbol in winners:
        short_term_perf_winners[symbol] = self.data[symbol].short_term_performance(self.months_for_short_perf)
        
    short_term_losers_sort_by_perf = [x[0] for x in sorted(short_term_perf_losers.items(), key=lambda item: item[1])]
    short_term_winners_sort_by_perf = [x[0] for x in sorted(short_term_perf_winners.items(), key=lambda item: item[1])]
    
    quartile = int(len(short_term_winners_sort_by_perf) / 4)
    short = short_term_winners_sort_by_perf[:quartile]
    
    quartile = int(len(short_term_losers_sort_by_perf) / 4)
    long = short_term_losers_sort_by_perf[-quartile:]
    
    # Trade Execution
    stocks_invested = [x.Key for x in self.Portfolio if x.Value.Invested]
    for symbol in stocks_invested:
        if symbol not in long + short:
            self.Liquidate(symbol)
    
    long_length = len(long)
    short_length = len(short)
    
    for symbol in long:
        if self.Securities[symbol].Price != 0 and self.Securities[symbol].IsTradable:
            self.SetHoldings(symbol, 1 / long_length)
    
    for symbol in short:
        if self.Securities[symbol].Price != 0 and self.Securities[symbol].IsTradable:
            self.SetHoldings(symbol, -1 / short_length)
    
def Selection(self):
    self.current_month += 1
    
    if self.current_month % 3 == 0: # Selection each quarter
        self.selection_flag = True
    
class SymbolData():
def __init__(self, period):
    self.Closes = RollingWindow[float](period)
    
def update(self, close):
    self.Closes.Add(close)
    
def is_ready(self):
    return self.Closes.IsReady
    
def performance(self):
    closes = [x for x in self.Closes]
    return (closes[0] - closes[-1]) / closes[-1]
    
def short_term_performance(self, months):
    closes = [x for x in self.Closes][:21 * months] # Takes last months
    return (closes[0] - closes[-1]) / closes[-1]
    
# Custom fee model
class CustomFeeModel(FeeModel):
def GetOrderFee(self, parameters):
    fee = parameters.Security.Price * parameters.Order.AbsoluteQuantity * 0.00005
    return OrderFee(CashAmount(fee, "USD"))
