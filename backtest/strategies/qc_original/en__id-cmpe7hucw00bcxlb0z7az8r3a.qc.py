# Original QuantConnect / library Python
# locale=en slug="行业动量策略-把握行业泡沫"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

import numpy as np
from AlgorithmImports import *
import statsmodels.api as sm

class RidingIndustryBubbles(QCAlgorithm):

def Initialize(self):
    self.SetStartDate(2008, 1, 1)
    self.SetCash(100000)

    self.spy = 'SPY'
    self.symbols = ['XLF', 'XLV', 'XLP', 'XLY', 'XLI', 'XLE', 'XLB', 'XLK', 'XLU']
    self.period = 10 * 12 * 21
    self.SetWarmUp(self.period)

    # Daily price data.
    self.data = {}
    
    for symbol in self.symbols + [self.spy]:
        data = self.AddEquity(symbol, Resolution.Daily)
        self.data[symbol] = RollingWindow[float](self.period)
    
    self.recent_month = -1

def OnData(self, data):
    # Store daily price data.
    for symbol in self.symbols + [self.spy]:
        symbol_obj = self.Symbol(symbol)
        if symbol_obj in data and data[symbol_obj]:
            self.data[symbol].Add(data[symbol_obj].Value)
    
    if self.recent_month == self.Time.month:
        return
    self.recent_month = self.Time.month

    if not self.data[self.spy].IsReady and self.spy in data: return

    market_closes = [x for x in self.data[self.spy]]
    separete_months = [market_closes[x:x+21] for x in range(0, len(market_closes),21)]
    market_monthly_returns = []
    for month in separete_months:
        month_of_prices = [x for x in month]
        market_monthly_returns.append(month_of_prices[0] / month_of_prices[-1] - 1)
    
    # Prepared for regression.    
    market_monthly_returns = np.array(market_monthly_returns).T
    market_monthly_returns = sm.add_constant(market_monthly_returns)
    
    t_stat = {}
    for symbol in self.symbols:
        if self.data[symbol].IsReady and symbol in data:
            closes = [x for x in self.data[symbol]]
            separete_months = [closes[x:x+21] for x in range(0, len(closes),21)]
            etf_monthly_returns = []
            for month in separete_months:
                month_of_prices = [x for x in month]
                etf_monthly_returns.append(month_of_prices[0] / month_of_prices[-1] - 1)
            
            # alpha t-stat calc.
            model = sm.OLS(etf_monthly_returns, market_monthly_returns)
            
            results = model.fit()
            alpha_tstat = results.tvalues[0]
            alpha_pvalue = results.pvalues[0]
            t_stat[symbol] = (alpha_tstat, alpha_pvalue)
    
    long = []
    if len(t_stat) != 0:
        long = [x[0] for x in t_stat.items() if x[1][0] >= 2 and x[1][1] >= 0.025] # The result is statistically significant, by the standards of the study, when p ≤ α
    
    # Trade execution.
    invested = [x.Key.Value for x in self.Portfolio if x.Value.Invested]
    for symbol in invested:
        if symbol not in long:
            self.Liquidate(symbol)

    for symbol in long:
        self.SetHoldings(symbol, 1 / len(long))
