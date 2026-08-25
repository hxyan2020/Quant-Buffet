# Original QuantConnect / library Python
# locale=en slug="kellers-van-puttens-generalized-momentum-and-flexible-asset-allocation"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

from AlgorithmImports import *
from pandas.core.frame import DataFrame
from typing import List, Dict, Tuple
# endregion

class GeneralizedMomentumandFlexibleAssetAllocation(QCAlgorithm):

def Initialize(self):
    self.SetStartDate(2005, 1, 1)
    self.SetCash(100000)

    self.period:int = 4 * 21
    self.top_equities:int = 3
    self.leverage:int = 2
    self.normalization_weights:np.ndarray = np.array([1., .5, .5])
    self.momentum_threshold:float = 0.

    self.investment_universe:List[str] = [
        "VTI", "VEA",
        "VWO", "SHY",
        "BND", "GSG",
        "VNQ",
    ]

    # equity subscription
    for ticker in self.investment_universe:
        self.AddEquity(ticker, Resolution.Daily, leverage=self.leverage)
    self.cash:Symbol = self.AddEquity("BIL", Resolution.Daily, leverage=self.leverage).Symbol
    
    self.recent_month:int = -1

def OnData(self, data:Slice) -> None:
    # monthly rebalance
    if self.Time.month == self.recent_month:
        return
    self.recent_month = self.Time.month

    if not (data.ContainsKey(self.cash) and data[self.cash]):
        return

    period:int = self.period + 1
    closes:DataFrame = self.History(self.investment_universe, period, Resolution.Daily).unstack(level=0)['close']

    if len(closes) == period and len(closes.columns) >= len(self.investment_universe):
        # momentum, volatility and correlation calculation
        returns:DataFrame = closes.pct_change().iloc[1:]
        momentum:pd.Series = closes.iloc[0] / closes.iloc[-1] - 1
        volatility:pd.Series = returns.std(axis=0) * np.sqrt(252)
        corr:DataFrame = returns.corr(method='pearson')
        mean_corr:pd.Series = abs((corr.sum(axis=0) - 1) / len(returns.columns)) # -1 for diagonal value we don't want to count in

        sorted_momentum:pd.Series = momentum.sort_index().sort_values(axis=0, ascending=False)
        sorted_volatility:pd.Series = volatility.sort_index().sort_values(axis=0, ascending=True)
        sorted_corr:pd.Series = mean_corr.sort_index().sort_values(axis=0, ascending=True)

        L:Dict[str, float] = {asset: np.dot(self.normalization_weights, np.array([list(sorted_momentum.index).index(asset), list(sorted_volatility.index).index(asset), list(sorted_corr.index).index(asset)])) for asset in list(returns.columns)}
        top_by_L:List[str] = sorted(L, key=L.get, reverse=True)[:self.top_equities]
        
        # equity allocation
        weight:Dict[Symbol, float] = {}
        for asset in top_by_L:
            if momentum.loc[asset] > self.momentum_threshold:
                weight[self.Symbol(asset)] = 1. / float(self.top_equities)
        
        # cash allocation
        if len(weight) != self.top_equities:
            cash_fraction_count:int = self.top_equities - len(weight)
            weight[self.cash] = float(cash_fraction_count) / float(self.top_equities)

        # trade execution
        invested:List[Symbol] = [x.Key for x in self.Portfolio if x.Value.Invested]
        for symbol in invested:
            if symbol not in weight:
                self.Liquidate(symbol)

        for symbol, w in weight.items():
            self.SetHoldings(symbol, w)
    else:
        if self.Portfolio.Invested:
            self.Liquidate()
