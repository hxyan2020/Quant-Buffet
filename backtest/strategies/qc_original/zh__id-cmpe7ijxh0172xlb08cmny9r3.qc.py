# Original QuantConnect / library Python
# locale=zh slug="国家和行业股票指数中的阿尔法动量"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

import numpy as np
from AlgorithmImports import *
class AlphaMomentumCountryIndustryEquityIndexes(QCAlgorithm):
def Initialize(self):
    self.SetStartDate(2005, 1, 1)
    self.SetCash(100000)
    
    self.symbols = [
        "EWJ",  # iShares MSCI Japan Index ETF
        "EZU",  # iShares MSCI Eurozone ETF
        "EFNL", # iShares MSCI Finland Capped Investable Market Index ETF
        "EWW",  # iShares MSCI Mexico Inv. Mt. Idx
        "ERUS", # iShares MSCI Russia ETF
        "IVV",  # iShares S&P 500 Index
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
    
    self.lookup_period = 12 * 21
    self.SetWarmup(self.lookup_period)
    self.data = {}
    
    for symbol in self.symbols:
        self.AddEquity(symbol, Resolution.Daily)
        self.data[symbol] = RollingWindow[float](self.lookup_period)
    
    self.settings.minimum_order_margin_portfolio_percentage = 0.
    self.Schedule.On(self.DateRules.MonthStart(self.symbols[0]), self.TimeRules.AfterMarketOpen(self.symbols[0]), self.Rebalance)

def OnData(self, data):
    for symbol in self.symbols:
        if symbol in data and data[symbol]:
            price = data[symbol].Value
            self.data[symbol].Add(price)
            
def Rebalance(self):
    if self.IsWarmingUp: return

    # Returns calculation.
    returns = {x : (self.data[x][0] / self.data[x][self.lookup_period - 1] - 1) for x in self.symbols if self.data[x].IsReady}
    if len(returns) == 0: return
    
    # Alpha score calc.
    eq_returns = [x[1] for x in returns.items()]
    return_mean = np.mean(eq_returns)
    return_std = np.std(eq_returns)
    
    alpha_score = {}
    for symbol in self.symbols:
        if symbol in returns:
            alpha = returns[symbol] - return_mean
            alpha_score[symbol] = alpha / return_std
            
    # Alpha score sorting.
    sorted_by_alpha_score = sorted(alpha_score.items(), key = lambda x: x[1], reverse = True)
    quintile = int(len(sorted_by_alpha_score) / 5)
    long = [x[0] for x in sorted_by_alpha_score[:quintile]]
    short = [x[0] for x in sorted_by_alpha_score[-quintile:]]
    
    # Trade execution.
    invested = [x.Key.Value for x in self.Portfolio if x.Value.Invested]
    for symbol in invested:
        if symbol not in long + short:
            self.Liquidate(symbol)
    long_count = len(long)
    short_count = len(short)
    
    for symbol in long:
        self.SetHoldings(symbol, 1/long_count)
    for symbol in short:
        self.SetHoldings(symbol, -1/short_count)
