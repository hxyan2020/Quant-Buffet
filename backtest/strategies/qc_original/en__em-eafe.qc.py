# Original QuantConnect / library Python
# locale=en slug="美国股票与新兴市场-em-和欧洲、澳大利亚及远东-eafe"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

from AlgorithmImports import *
import data_tools
from pandas.core.frame import DataFrame
# endregion

class WhyDoUSStocksOutperformEMandEAFERegions(QCAlgorithm):

def Initialize(self) -> None:
    self.SetStartDate(2000, 1, 1)
    self.SetCash(100000)

    self.period: int = 365
    self.leverage: int = 3

    self.spread_assets: List[Symbol] = [
        self.AddEquity('SPY', Resolution.Daily).Symbol,
        self.AddEquity('EEM', Resolution.Daily).Symbol
    ]

    for symbol in self.spread_assets:
        self.Securities[symbol].SetLeverage(self.leverage)

    self.Settings.MinimumOrderMarginPortfolioPercentage = 0.
    self.current_month: int = -1

def OnData(self, data: Slice) -> None:
    # monthly rebalance
    if self.Time.month == self.current_month:
        return
    self.current_month = self.Time.month

    trade_direction: int = 0

    returns_df: DataFrame = self.History(self.spread_assets, timedelta(days=self.period), Resolution.Daily)['close'].unstack(level=0).pct_change().iloc[1:].dropna(axis=1)
    if returns_df.shape[1] == 2:
        spread: pd.Series = returns_df[self.spread_assets[0]] - returns_df[self.spread_assets[1]]
        spread_equity: float = (1 + spread).cumprod()
        trade_direction: int = 1 if spread_equity[-1] > spread_equity[0] else -1

    # order execution
    portfolio: List[PortfolioTarget] = [PortfolioTarget(symbol, ((-1)**i) * trade_direction) for i, symbol in enumerate(self.spread_assets) if symbol in data and data[symbol]]
    self.SetHoldings(portfolio, True)
