# Original QuantConnect / library Python
# locale=en slug="资产轮动策略-2"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

from AlgoLib import *

class AssetClassTrendFollowing(QCAlgorithm):

def Initialize(self):
    self.SetStartDate(2000, 1, 1)
    self.SetCash(100000)
    
    assets = ["SPY", "EFA", "IEF", "VNQ", "GSG"]
    moving_avg_period = 10 * 21

    self.asset_moving_avgs = { 
        self.AddEquity(asset, Resolution.Minute).Symbol : self.SMA(asset, moving_avg_period, Resolution.Daily) for asset in assets 
    }

    self.last_rebalance_month = -1
    self.SetWarmUp(moving_avg_period, Resolution.Daily)
    self.Settings.MinimumOrderMarginPortfolioPercentage = 0.

def OnData(self, data: Slice) -> None:
    if self.IsWarmingUp: 
        return

    if not (self.Time.hour == 9 and self.Time.minute == 31):
        return

    # rebalance once a month
    if self.Time.month == self.last_rebalance_month:
        return
    self.last_rebalance_month = self.Time.month
    
    long_assets = [symbol for symbol, moving_avg in self.asset_moving_avgs.items() 
        if symbol in data 
        and data[symbol] 
        and moving_avg.IsReady 
        and data[symbol].Value > moving_avg.Current.Value
    ]

    portfolio_targets = [PortfolioTarget(asset, 1. / len(long_assets)) for asset in long_assets]
    self.SetHoldings(portfolio_targets, True)
