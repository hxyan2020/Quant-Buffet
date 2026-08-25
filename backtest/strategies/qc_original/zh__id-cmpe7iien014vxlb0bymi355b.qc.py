# Original QuantConnect / library Python
# locale=zh slug="基于多元回归分析的板块轮动策略"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

from collections import deque
from AlgorithmImports import *
from scipy import stats
import numpy as np
import statsmodels.api as sm
class SectorRotationStrategyBasedonMultivariateRegressionAnalysis(QCAlgorithm):
def Initialize(self):
    self.SetStartDate(2000, 1, 1)
    self.SetCash(100000)
    
    self.symbols = [
        'XLV',
        'XLI',
        'XLY',
        'XLP',
        'XLB',
        'XLK',
        'XLU',
        'XLE',
        'XLF'
        ]
    
    # Daily close data.
    self.data = {}
    self.period = 21
    # Regression data.
    self.regression_period = 13
    self.regression_data = {}
    self.market = self.AddEquity('SPY', Resolution.Daily).Symbol
    self.data[self.market] = deque(maxlen = self.period)
    
    self.cash = self.AddEquity('SHY', Resolution.Daily).Symbol
    
    for symbol in self.symbols:
        self.AddEquity(symbol, Resolution.Daily)
        self.regression_data[symbol] = deque(maxlen = self.regression_period)
        self.data[symbol] = deque(maxlen = self.period)
    
    self.Schedule.On(self.DateRules.MonthStart(self.symbols[0]), self.TimeRules.BeforeMarketClose(self.symbols[0]), self.Rebalance)

def OnData(self, data):
    for symbol in self.symbols + [self.market]:
        if symbol in data and data[symbol]:
            price = data[symbol].Value
            self.data[symbol].append(price)
def Rebalance(self):
    long = []
    
    for symbol in self.symbols:
        # Data is ready.
        if len(self.data[symbol]) == self.data[symbol].maxlen and len(self.data[self.market]) == self.data[self.market].maxlen:
            # Calculate regression independent variables.
            
            # Sector return.
            sector_return = np.log( self.data[symbol][-1] / self.data[symbol][0] )
            
            # Volatility.
            volatility = Volatility(self.data[symbol])
            
            # Drawdown.
            drawdown = min(0, sector_return)
            
            # The regression slope.
            x = range(1, len(self.data[symbol]) + 1)
            y = [x for x in self.data[symbol]]
            slope, intercept, r_value, p_value, std_err = stats.linregress(x, y)
            
            # Excess return.
            market_return = np.log( self.data[self.market][-1] / self.data[self.market][0] )
            ex_return = sector_return - market_return
            
            self.regression_data[symbol].append( (sector_return, volatility, drawdown, slope, ex_return) )
            
            # Regression data is ready.
            if len(self.regression_data[symbol]) == self.regression_data[symbol].maxlen:
                regression_data = [x for x in self.regression_data[symbol]]
                
                returns = [x[0] for x in self.regression_data[symbol]]
                volatilities = [x[1] for x in self.regression_data[symbol]]
                drawdowns = [x[2] for x in self.regression_data[symbol]]
                slopes = [x[3] for x in self.regression_data[symbol]]
                ex_returns = [x[4] for x in self.regression_data[symbol]]
                
                # Predict return for sector.
                x = [ returns[:-1], volatilities[:-1], drawdowns[:-1], slopes[:-1], ex_returns[:-1] ]
                y = returns[1:]
                regression_model = MultipleLinearRegression(x, y)
                
                alpha = regression_model.params[0]
                return_predict = np.array([returns[-1], volatilities[-1], drawdowns[-1], slopes[-1], ex_returns[-1]])
                betas = np.array(regression_model.params[1:])
                Y = alpha + sum(np.multiply(betas, return_predict))
                if Y > 0:
                    long.append(symbol)
        
    # Trade execution.
    self.Liquidate()
    
    weight = 1 / len(self.symbols)
    for symbol in long:
        if self.Securities[symbol].Price != 0:
            self.SetHoldings(symbol, weight)
    
    cash_weight = (len(self.symbols) - len(long)) / len(self.symbols)
    if self.Securities[self.cash].Price != 0:
        self.SetHoldings(self.cash, cash_weight)
def Volatility(values):
values = np.array(values)
returns = (values[1:] - values[:-1]) / values[:-1]
return np.std(returns)

def MultipleLinearRegression(x, y):
x = np.array(x).T
x = sm.add_constant(x)
result = sm.OLS(endog=y, exog=x).fit()
return result
