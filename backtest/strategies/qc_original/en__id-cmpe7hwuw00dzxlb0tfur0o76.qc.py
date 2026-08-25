# Original QuantConnect / library Python
# locale=en slug="激进型资产配置策略"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

from AlgorithmImports import *
import pandas as pd
import numpy as np
from typing import List, Dict
from pandas.core.frame import DataFrame
# endregion

class BoldAssetAllocation(QCAlgorithm):

def Initialize(self):
    self.SetCash(100000)
    self.SetStartDate(2008, 1, 1)

    # all assets
    self.offensive:List[str] = [
        "SPY", "QQQ",
        "IWM", "VGK",
        "EWJ", "VWO",
        "VNQ", "DBC",
        "GLD", "TLT",
        "HYG", "LQD",
    ]

    self.protective:List[str] = ["SPY", "VWO", "VEA", "BND"]
    self.defensive:List[str] = ["TIP", "DBC", "BIL", "IEF", "TLT", "LQD", "BND"]
    self.safe:str = "BIL"

    # strategy parameters (our implementation)
    self.prds:List[int] = [1, 3, 6, 12]                     # fast momentum settings
    self.prdweights:np.ndarray = np.array([12, 4, 2, 1])    # momentum weights
    self.LO, self.LP, self.LD, self.B, self.TO, self.TD = [
        len(self.offensive),
        len(self.protective),
        len(self.defensive),
        1,
        6,
        3,
    ]  # number of offensive, protective, defensive assets, threshold for "bad" assets, select top n of offensive and defensive assets
    
    self.hprd:int = (max(self.prds + [self.LO, self.LD]) * 21 + 50)  # momentum periods calculation

    # repeat safe asset so it can be selected multiple times
    self.all_defensive:List[str] = self.defensive + [self.safe] * max(
        0, self.TD - sum([1 * (e == self.safe) for e in self.defensive])
    )
    
    self.equities:List[str] = list(
        dict.fromkeys(self.protective + self.offensive + self.all_defensive)
    )
    
    leverage:int = 3
    for equity in self.equities:
        data:Equity = self.AddEquity(equity, Resolution.Daily)
        data.SetLeverage(leverage)

    self.recent_month:int = -1

def OnData(self, data:Slice) -> None:
    if self.IsWarmingUp:
        return

    # monthly rebalance
    if self.recent_month == self.Time.month:
        return
    self.recent_month = self.Time.month

    # get price data and trading weights
    h:DataFrame = self.History(self.equities, self.hprd, Resolution.Daily)["close"].unstack(level=0)
    weights:pd.Series = self.trade_weights(h)

    # trade
    self.SetHoldings([PortfolioTarget(x, y) for x, y in zip(weights.index, weights.values) if x in data and data[x]])

def trade_weights(self, hist:DataFrame) -> pd.Series:
    # initialize weights series
    weights:pd.Series = pd.Series(0, index=hist.columns)
    # end of month values
    h_eom:DataFrame = hist.loc[hist.groupby(hist.index.to_period("M")).apply(lambda x: x.index.max())].iloc[:-1, :]

    # Check if protective universe is triggered.

    # build dataframe of momentum values
    mom:DataFrame = (h_eom.iloc[-1, :].div(h_eom.iloc[[-p - 1 for p in self.prds], :], axis=0) - 1)
    mom = mom.loc[:, self.protective].T

    # determine number of protective securities with negative weighted momentum
    n_protective:float = np.sum(np.sum(mom.values * self.prdweights, axis=1)  0:
        # price / SMA
        mom_in = h_eom.iloc[-1, :].div(h_eom.iloc[[-t for t in range(1, self.LO + 1)]].mean(axis=0), axis=0)
        mom_in = mom_in.loc[self.offensive].sort_values(ascending=False)
        # equal weightings to top relative momentum securities
        in_weights = pd.Series(pct_in / self.TO, index=mom_in.index[:self.TO])
        weights = pd.concat([weights, in_weights])
    
    # determine weights of defensive universe
    if pct_in
