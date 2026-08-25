# Original QuantConnect / library Python
# locale=zh slug="国家股票指数中的偏度效应"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

import numpy as np
from AlgorithmImports import *
from scipy.stats import skew
class SkewnessEffectEquities(QCAlgorithm):
def Initialize(self):
    self.SetStartDate(2000, 1, 1)
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
    
    self.lookup_period = 24 * 21
    self.SetWarmup(self.lookup_period)
    self.data = {}
    
    for symbol in self.symbols:
        data = self.AddEquity(symbol, Resolution.Daily)
        data.SetLeverage(10)
        self.data[symbol] = RollingWindow[float](self.lookup_period)
        
    self.Schedule.On(self.DateRules.MonthStart(self.symbols[0]), self.TimeRules.AfterMarketOpen(self.symbols[0]), self.Rebalance)

def OnData(self, data):
    for symbol in self.data:
        if symbol in data and data[symbol]:
            price = data[symbol].Value
            if price != 0:
                self.data[symbol].Add(price)
            
def Rebalance(self):
    if self.IsWarmingUp: return

    # Skewness calculation
    skewness_data = {}
    for symbol in self.symbols:
        if self.data[symbol].IsReady and self.Securities[symbol].IsTradable and (self.Time.date() - self.Securities[symbol].GetLastData().Time.date()).days
