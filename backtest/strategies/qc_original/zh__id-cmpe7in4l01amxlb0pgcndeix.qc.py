# Original QuantConnect / library Python
# locale=zh slug="多资产对冲动量策略"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

from AlgorithmImports import *
class MultiAssetPairsMomentum(QCAlgorithm):
def Initialize(self):
    self.SetStartDate(2000, 1, 1)
    self.SetCash(100000)
    
    # Country symbol and currency future symbol.
    self.symbols = [
        'SHY', 'AGG', 'BWX', 'TLT', 'LQD', 'EMB',
        'HYG', 'DBC', 'VNQ', 'IWM', 'SPY', 'EFA',
        'EEM'
    ]
    self.Settings.FreePortfolioValuePercentage = 0.05
    
    self.momentum_period: int = 13
    self.signal_min_period: int = 12
    self.component_period: int = 60
    
    self.pairs = []
    self.data = {}
    
    for i, symbol1 in enumerate(self.symbols):
        for j, symbol2 in enumerate(self.symbols):
            if i = self.momentum_period:
                    monthly_prices = np.array([x for x in self.data[symbol].price][:self.momentum_period])
                    monthly_returns = monthly_prices[:-1] / monthly_prices[1:] - 1
                    raw_current_momentum = np.mean(monthly_returns)
                    
                    self.data[symbol].signal.append(raw_current_momentum)
                    
                    if len(self.data[symbol].signal) >= self.signal_min_period:
                        signal_mean = np.mean(self.data[symbol].signal)
                        signal_std = np.std(self.data[symbol].signal)
                        standardized_signal = (raw_current_momentum - signal_mean) / signal_std
                        
                        self.data[symbol].standardized_signal.Add(standardized_signal)
                        raw_signal[symbol] = raw_current_momentum
        score = {}
        for symbol1, symbol2 in self.pairs:
            # Compute components.
            # Monthly price and stand.signal data is ready.
            if self.data[symbol1].is_ready() and self.data[symbol2].is_ready():
                monthly_prices1 = np.array( [x for x in self.data[symbol1].price] )
                monthly_returns1 = monthly_prices1[:-1] / monthly_prices1[1:] - 1
                
                monthly_prices2 = np.array( [x for x in self.data[symbol2].price] )
                monthly_returns2 = monthly_prices2[:-1] / monthly_prices2[1:] - 1
                
                monthly_signals1 = [x for x in self.data[symbol1].standardized_signal]
                monthly_signals2 = [x for x in self.data[symbol2].standardized_signal]
                
                # The first component.
                b11 = np.corrcoef(monthly_signals1[1:], monthly_returns1[:-1])[0, 1]
                b22 = np.corrcoef(monthly_signals2[1:], monthly_returns2[:-1])[0, 1]

                # The second component.
                p12 = np.corrcoef(monthly_signals1, monthly_signals2)[0, 1]
            
                # The third component.
                b12 = np.corrcoef(monthly_signals1[1:], monthly_returns2[:-1])[0, 1]
                b21 = np.corrcoef(monthly_signals2[1:], monthly_returns1[:-1])[0, 1]
                
                # composite_score = ( (b11 + b12) - (b22 + b21) ) * np.sqrt( (1 - p12) / pi)
                composite_score = ( (b11 - b12) + (b22 - b21) ) * np.sqrt( (1 - p12) / pi)
                score[(symbol1, symbol2)] = composite_score ** 3
        
        # Sorting by composite score.
        sorted_by_score = sorted(score.items(), key = lambda x: x[1], reverse = True)
        count = 4
        traded_pairs = [x for x in sorted_by_score[:count]]
        
        # Trade execution.
        self.Liquidate()
        
        total_score = sum([abs(score) for _, score in traded_pairs])
        
        for (symbol1, symbol2), score in traded_pairs:
            if symbol1 in raw_signal and symbol2 in raw_signal:
                pair_w = score / total_score
                q1 = (self.Portfolio.TotalPortfolioValue * pair_w) / 2 / self.data[symbol1].price[0]
                q2 = (self.Portfolio.TotalPortfolioValue * pair_w) / 2 / self.data[symbol2].price[0]
                
                # The individual asset signals (raw momentum) determine which asset is long or short in that pair for the month.
                if raw_signal[symbol1] >= raw_signal[symbol2]:
                    self.MarketOrder(symbol1, q1)
                    self.MarketOrder(symbol2, -q2)
                else:
                    self.MarketOrder(symbol1, -q1)
                    self.MarketOrder(symbol2, q2)
class SymbolData():
def __init__(self, algorithm, symbol, component_period):
    self.symbol = symbol
    self.algorithm = algorithm
    self.price = RollingWindow[float](component_period + 1)  # monthly price
    self.signal = []
    self.standardized_signal = RollingWindow[float](component_period)
    
    # Warmup.
    history = algorithm.History(algorithm.Symbol(symbol), component_period*21, Resolution.Daily)
    if history.empty:
        algorithm.Debug(f"Not warmed up yet: {symbol}")
        return
    closes = history.loc[symbol].close
    
    closes_len = len(closes.keys())
    
    # Find monthly closes.
    for index, time_close in enumerate(closes.items()):
        # index out of bounds check.
        if index + 1  bool:
    return (self.price.IsReady and self.standardized_signal.IsReady)
