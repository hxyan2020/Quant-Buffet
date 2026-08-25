# Original QuantConnect / library Python
# locale=en slug="kellers-keunigs-defensive-asset-allocation"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

from AlgorithmImports import *
from typing import List, Dict
import numpy as np
# endregion

class DefensiveAssetAllocation(QCAlgorithm):

def Initialize(self):
    self.SetCash(100000)
    self.SetStartDate(2008, 1, 1)

    self.risky_topT:int = 6
    self.half_risky_topT:int = 3

    self.risky_universe:List[str] = [
        "SPY", "IWM",
        "QQQ", "VGK",
        "EWJ", "VWO",
        "VNQ", "GSG",
        "GLD", "TLT",
        "HYG", "LQD",
    ]

    self.cash_universe:List[str] = ["BIL", "IEF", "LQD"]
    self.canary_universe:List[str] = ["VWO", "BND"]
    self.all_tickers:List[str] = self.risky_universe + self.cash_universe + self.canary_universe

    self.period_list:List[int] = [21, 63, 126, 252]
    self.objective_score_weights:np.ndarray = [12., 4., 2., 1.]

    self.SetWarmUp(max(self.period_list), Resolution.Daily)

    self.momp_data_by_ticker:Dict[str, List[MomentumPercent]] = {}

    # subscribe data
    for ticker in self.all_tickers:
        self.AddEquity(ticker, Resolution.Daily)
        self.momp_data_by_ticker[ticker] = [self.MOMP(ticker, period, Resolution.Daily) for period in self.period_list]

    self.recent_month:int = -1

def OnData(self, data:Slice) -> None:
    if self.IsWarmingUp:
        return

    if self.recent_month == self.Time.month:
        return
    self.recent_month = self.Time.month
    
    # rank all the risky and cash symbol groups by momentum score
    sorted_risky:List = sorted([item for item in self.momp_data_by_ticker.items() if item[0] in self.risky_universe and
                                all(indicator.IsReady for indicator in item[1])],   # all indicators for ticker are ready
                                key=lambda x: np.dot(np.array([momentum.Current.Value for momentum in x[1]]), self.objective_score_weights),
                                reverse=True)

    best_growth:List[str] = [x[0] for x in sorted_risky[:self.risky_topT]]
    second_best_growth:List[str] = best_growth[:self.half_risky_topT]

    sorted_cash:List = sorted([item for item in self.momp_data_by_ticker.items() if item[0] in self.cash_universe and
                                all(indicator.IsReady for indicator in item[1])],   # all indicators for ticker are ready
                                key=lambda x: np.dot(np.array([momentum.Current.Value for momentum in x[1]]), self.objective_score_weights),
                                reverse=True)
    if len(sorted_cash)  0 for x in canary_scores):
        weight = { x : 1. / float(len(best_growth)) for x in best_growth}

    elif any(x
