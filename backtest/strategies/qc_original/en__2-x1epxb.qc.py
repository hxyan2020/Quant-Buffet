# Original QuantConnect / library Python
# locale=en slug="动量资产配置策略-2"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

from AlgorithmImports import *

class AssetMomentumStrategy(QCAlgorithm):
def Initialize(self):
    self.SetStartDate(2000, 1, 1)  # Start Date
    self.SetCash(100000)  # Initial Cash
    
    self.momentum_data = {}  # Store Rate of Change (ROC) objects
    momentum_period = 252  # 12 months * 21 trading days
    self.SetWarmUp(momentum_period, Resolution.Daily)
    
    self.assets_to_trade = 3  # Number of assets to trade
    
    self.asset_symbols = ["SPY", "EFA", "IEF", "VNQ", "GSG"]  # List of asset symbols
    
    # Add Equity and ROC for each symbol
    for asset in self.asset_symbols:
        self.AddEquity(asset, Resolution.Minute)
        self.momentum_data[asset] = self.ROC(asset, momentum_period, Resolution.Daily)
    
    self.last_rebalance_month = None  # Track last rebalance month
