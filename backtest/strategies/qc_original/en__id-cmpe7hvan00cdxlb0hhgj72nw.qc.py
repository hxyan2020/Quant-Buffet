# Original QuantConnect / library Python
# locale=en slug="凯勒和克尼格的谨慎资产配置策略"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

from AlgorithmImports import *
from typing import List, Dict
#endregion

class VigilantAssetAllocation(QCAlgorithm):

def Initialize(self) -> None:
    self.SetCash(100000)
    self.SetStartDate(2008, 1, 1)

    # VAA-G12 risk investment universe assets
    self.growth_symbols:List[str] = [
        "SPY", "IWM", "QQQ", "VGK", 
        "EWJ", "EEM", "EFA", "ACWX", 
        "IYR", "GSG", "GLD", "SHY", 
        "IEF", "TLT", "LQD", "HYG", "AGG"
        ]

    # cash universe assets
    self.safety_symbols:List[str] = ["LQD", "IEF", "SHY"]

    momentum_periods:List[int] = [21, 63, 126, 252]
    self.score_weights:np.ndarray = np.array([12, 4, 2, 1])

    self.SetWarmUp(momentum_periods[-1], Resolution.Daily)

    self.symbol_data:Dict[List] = {}
    self.B:int = 4
    self.T:int = 2
    self.leverage:int = 3

    for ticker in self.growth_symbols + self.safety_symbols:
        data:Equity = self.AddEquity(ticker, Resolution.Minute)
        data.SetLeverage(self.leverage)
        self.symbol_data[ticker] = [self.MOMP(ticker, period, Resolution.Daily) for period in momentum_periods]

    self.recent_month:int = -1
    
def OnData(self, data:Slice) -> None:
    # monthly rebalance
    if self.recent_month == self.Time.month:
        return
    self.recent_month = self.Time.month

    if self.IsWarmingUp: return

    # this approach overweights the front month momentum value and progressively underweights older momentum values
    growth_score:Dict[str, float] = { ticker : sum(np.array([x.Current.Value for x in momentum_indicators]) * self.score_weights) for ticker, momentum_indicators in self.symbol_data.items() 
                                    if ticker in self.growth_symbols if all(ind.IsReady for ind in momentum_indicators) }
    
    safe_score:Dict[str, float] = { ticker : sum(np.array([x.Current.Value for x in momentum_indicators]) * self.score_weights) for ticker, momentum_indicators in self.symbol_data.items() 
                                    if ticker in self.safety_symbols if all(ind.IsReady for ind in momentum_indicators) }

    # wait until all the assets' indicators are warmed-up
    if len(growth_score) != len(self.growth_symbols) or len(safe_score) != len(self.safety_symbols):
        return

    sorted_growth:List = sorted(growth_score.items(), key=lambda x: x[1], reverse=True)
    sorted_safe:List = sorted(safe_score.items(), key=lambda x: x[1], reverse=True)

    # count the number of risky assets with negative momentum scores and store in b
    b:int = sum(1 for x in sorted_growth if x[1] = self.B:
        # liquidate
        invested:List[str] = [x.Key.Value for x in self.Portfolio if x.Value.Invested]
        for ticker in invested:
            if ticker != best_safe:
                self.Liquidate(ticker)

        self.SetHoldings(best_safe, 1)
    
    # if none of the risky assets come back with negative momentum scores, allocation 100% to the 2 best scoring risky assets
    else:
        # liquidate
        invested:List[str] = [x.Key.Value for x in self.Portfolio if x.Value.Invested]
        for ticker in invested:
            if ticker not in best_growth + [best_safe]:
                self.Liquidate(ticker)

        for ticker in best_growth:
            self.SetHoldings(ticker, (1-CF) / 2) 
        
        self.SetHoldings(best_safe, CF)
