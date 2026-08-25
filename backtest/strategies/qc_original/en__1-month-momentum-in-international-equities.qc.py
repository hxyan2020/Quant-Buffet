# Original QuantConnect / library Python
# locale=en slug="1-month-momentum-in-international-equities"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

from collections import deque
from AlgorithmImports import *
class OneMonthMomentumInternationalEquities(QCAlgorithm):
def Initialize(self):
    self.SetStartDate(2010, 1, 1)
    self.SetCash(100000)
    
    self.symbols = ["EWJ",  # iShares MSCI Japan Index ETF
                    "EZU",  # iShares MSCI Eurozone ETF
                    "EFNL", # iShares MSCI Finland Capped Investable Market Index ETF
                    "EWW",  # iShares MSCI Mexico Inv. Mt. Idx
                    "ERUS", # iShares MSCI Russia ETF
                    "IVV",  # iShares S&P 500 Index
                    "ICOL", # Consumer Discretionary Select Sector SPDR Fund
                    "AAXJ", # iShares MSCI All Country Asia ex Japan Index ETF
                    "AUD",  # Australia Bond Index Fund
                    "EWQ",  # iShares MSCI France Index ETF
                    "BUND", # Pimco Germany Bond Index Fund
                    "EWH",  # iShares MSCI Hong Kong Index ETF
                    "EPI",  # WisdomTree India Earnings ETF
                    "EIDO"  # iShares MSCI Indonesia Investable Market Index ETF
                    "EWI",  # iShares MSCI Italy Index ETF
                    "GAF",  # SPDR S&P Emerging Middle East & Africa ETF
                    "ENZL", # iShares MSCI New Zealand Investable Market Index Fund
                    "NORW"  # Global X FTSE Norway 30 ETF
                    "EWY",  # iShares MSCI South Korea Index ETF
                    "EWP",  # iShares MSCI Spain Index ETF
                    "EWD",  # iShares MSCI Sweden Index ETF
                    "EWL",  # iShares MSCI Switzerland Index ETF
                    "GXC",  # SPDR S&P China ETF
                    "EWC",  # iShares MSCI Canada Index ETF
                    "EWZ",  # iShares MSCI Brazil Index ETF
                    "ARGT", # Global X FTSE Argentina 20 ETF
                    "AND",  # Global X FTSE Andean 40 ETF
                    "AIA",  # iShares S&P Asia 50 Index ETF
                    "EWO",  # iShares MSCI Austria Investable Mkt Index ETF
                    "EWK",  # iShares MSCI Belgium Investable Market Index ETF
                    "BRAQ", # Global X Brazil Consumer ETF
                    "ECH",  # iShares MSCI Chile Investable Market Index ETF
                    "CHIB", # Global X China Technology ETF
                    "EGPT", # Market Vectors Egypt Index ETF
                    "ADRU"  # BLDRS Europe 100 ADR Index ETF
                    ]
                    
    self.period = 21
    self.SetWarmUp(self.period, Resolution.Daily)
    
    self.data = {}
    for symbol in self.symbols:
        self.AddEquity(symbol, Resolution.Daily)
        self.data[symbol] = self.ROC(symbol, self.period, Resolution.Daily)
    self.Schedule.On(self.DateRules.MonthStart(self.symbols[0]), self.TimeRules.AfterMarketOpen(self.symbols[0]), self.Rebalance)

def Rebalance(self):
    if self.IsWarmingUp: return

    # Return sorting
    returns = { x: self.data[x].Current.Value for x in self.data if self.data[x].IsReady }
    
    long = []
    short = []
    if len(returns) >= 5:
        sorted_by_return = sorted(returns.items(), key = lambda x: x[1], reverse = True)
        quintile = int(len(sorted_by_return)/5)
        long = [x[0] for x in sorted_by_return[:quintile]]
        short = [x[0] for x in sorted_by_return[-quintile:]]
        
    # Trade execution
    long_count = len(long)
    short_count = len(short)
    invested = [x.Key for x in self.Portfolio if x.Value.Invested]
    for symbol in invested:
        if symbol not in long + short:
            self.Liquidate(symbol)
    
    for symbol in long:
        self.SetHoldings(symbol, 1/long_count)
    for symbol in short:
        self.SetHoldings(symbol, -1/short_count)
