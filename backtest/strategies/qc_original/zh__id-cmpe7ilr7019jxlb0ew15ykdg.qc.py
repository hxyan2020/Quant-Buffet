# Original QuantConnect / library Python
# locale=zh slug="股票指数中的广义风险调整动量策略"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

from collections import deque
from AlgorithmImports import *
from math import sqrt
import operator
import numpy as np
class GeneralisedRiskAdjustedMomentuminEquityIndexes(QCAlgorithm):
def Initialize(self):
    self.SetStartDate(2008, 4, 1)   # ACWI data starts in 2008.
    self.SetCash(100000)
    
    self.symbols = [
                    "EWA",  # iShares MSCI Australia Index ETF
                    "EWO",  # iShares MSCI Austria Investable Mkt Index ETF
                    "EWK",  # iShares MSCI Belgium Investable Market Index ETF
                    "EWZ",  # iShares MSCI Brazil Index ETF
                    "EWC",  # iShares MSCI Canada Index ETF
                    "FXI",  # iShares China Large-Cap ETF
                    "EWQ",  # iShares MSCI France Index ETF
                    "EWG",  # iShares MSCI Germany ETF 
                    "EWH",  # iShares MSCI Hong Kong Index ETF
                    "EWI",  # iShares MSCI Italy Index ETF
                    "EWJ",  # iShares MSCI Japan Index ETF
                    "EWM",  # iShares MSCI Malaysia Index ETF
                    "EWW",  # iShares MSCI Mexico Inv. Mt. Idx
                    "EWN",  # iShares MSCI Netherlands Index ETF
                    "EWS",  # iShares MSCI Singapore Index ETF
                    "EZA",  # iShares MSCI South Africe Index ETF
                    "EWY",  # iShares MSCI South Korea ETF
                    "EWP",  # iShares MSCI Spain Index ETF
                    "EWD",  # iShares MSCI Sweden Index ETF
                    "EWL",  # iShares MSCI Switzerland Index ETF
                    "EWT",  # iShares MSCI Taiwan Index ETF
                    "THD",  # iShares MSCI Thailand Index ETF
                    "EWU",  # iShares MSCI United Kingdom Index ETF
                    "SPY",  # SPDR S&P 500 ETF
                    ]
    # Daily price data.
    self.data = {}
    self.index = self.AddEquity('ACWI', Resolution.Daily).Symbol
    self.data[self.index] = deque(maxlen = 21)
    self.leverage_cap = 3
    # Volatility factor.
    self.volatility_factor_symbols = []                  # Symbols
    self.volatility_factor_vector = deque(maxlen = 6)    # Monthly volatility.
    
    # Minimal data count needed for optimalization.
    self.period = 12 * 21
    self.quantile = 4
    
    for symbol in self.symbols:
        data = self.AddEquity(symbol, Resolution.Daily)
        data.SetLeverage(50)
        
        self.data[symbol] = deque()
    self.Schedule.On(self.DateRules.MonthStart(self.symbols[0]), self.TimeRules.AfterMarketOpen(self.symbols[0]), self.Rebalance)
    
def OnData(self, data):
    # Store daily data.
    for symbol in self.data:
        if symbol in data and data[symbol]:
            price = data[symbol].Value
            self.data[symbol].append(price)
                    
def Rebalance(self):
    # Sharpe ratio indexed by n.
    sharpe_ratio_data = {}
    
    n = 0
    while n = self.period:
                    # Realized volatility calc.
                    perf = Return(self.data[symbol])
                    vol = Volatility(self.data[symbol])
                    performance_volatility[symbol] = (perf, vol)
                    
                    daily_prices = np.array([x for x in self.data[symbol]])
                    daily_returns = (daily_prices[1:] - daily_prices[:-1]) / daily_prices[:-1]
                    realized_volatility = sqrt(sum(daily_returns**2) / self.period)
                    
                    generalized_momentum[symbol] = perf / (realized_volatility ** n)
                
        if len(generalized_momentum) >= self.quantile:
            sorted_by_momentum = sorted(generalized_momentum.items(), key = lambda x: x[1], reverse = True)
            quantile = int(len(sorted_by_momentum) / self.quantile)
            long = [x[0] for x in sorted_by_momentum[:quantile]]
            short = [x[0] for x in sorted_by_momentum[-quantile:]]
            
            # Sharpe ratio calc.
            symbol_count = len(long + short)
            total_performance = sum([performance_volatility[x][0] / symbol_count for x in long])
            total_performance += sum([((-1) * performance_volatility[x][0]) / symbol_count for x in short])
            
            total_volatility = sum([performance_volatility[x][1] / symbol_count for x in long + short])
            portfolio_sharpe_ratio = total_performance / total_volatility
            
            portfolio_symbols = [long, short]
            sharpe_ratio_data[str(n)] = (portfolio_sharpe_ratio, portfolio_symbols)
            
        n += 0.1
    
    if len(sharpe_ratio_data) != 0:
        max_by_sharpe_ratio = max(sharpe_ratio_data.items(), key = operator.itemgetter(1))
        long = max_by_sharpe_ratio[1][1][0]
        short = max_by_sharpe_ratio[1][1][1]
        # Calculate last month's volatility.
        if len(self.volatility_factor_symbols) != 0:
            monthly_volatility = self.CalculateFactorVolatility(self.data, self.volatility_factor_symbols)
            if monthly_volatility != 0:
                self.volatility_factor_vector.append(monthly_volatility)
        # Store new factor symbols.
        self.volatility_factor_symbols = long + short
        
        # Volatility factor is ready.
        if len(self.volatility_factor_vector) == self.volatility_factor_vector.maxlen:
            # Volatility targetting.
            if len(self.data[self.index]) == self.data[self.index].maxlen:
                annual_index_volatility = Volatility(self.data[self.index]) * sqrt(12*21)
                realized_strategy_volatility = np.mean(self.volatility_factor_vector)
                # Cap leverage if needed.
                target_leverage = min(self.leverage_cap, (annual_index_volatility / realized_strategy_volatility))
                
                # Trade execution.
                symbols_invested = [x.Key.Value for x in self.Portfolio if x.Value.Invested]
                for symbol in symbols_invested:
                    if symbol not in long + short:
                        self.Liquidate(symbol)
                
                count = len(long + short)
                for symbol in long:
                    self.SetHoldings(symbol, target_leverage / len(long))
                for symbol in short:
                    self.SetHoldings(symbol, -target_leverage / len(short))
def CalculateFactorVolatility(self, data, factor_symbols):
    monthly_volatility = 0
    if len(factor_symbols) != 0:
        for symbol in factor_symbols:
            if symbol in data and len(data[symbol]) >= 21:
                monthly_volatility += (Volatility([x for x in data[symbol]][-21:]) / len(factor_symbols))
    return monthly_volatility
def Return(values):
return (values[-1] - values[0]) / values[0]

def Volatility(values):
values = np.array(values)
returns = (values[1:] - values[:-1]) / values[:-1]
return np.std(returns)
