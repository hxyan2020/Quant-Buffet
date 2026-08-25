# Original QuantConnect / library Python
# locale=en slug="momentum-asset-allocation-strategy-2"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

from AlgoLib import *

class AssetMomentumStrategy(XXX):
'''
This class implements a momentum-based trading strategy, inheriting from a base trading algorithm class.
It selects a subset of assets based on their momentum and rebalances the portfolio monthly, aiming to hold positions in assets demonstrating the strongest momentum.
'''

def Initialize(self):
    '''
    Initializes the trading strategy by setting the start date, initial cash, the momentum period for calculating rate of change (ROC), 
    the assets to be traded, and setting up the necessary indicators and parameters for the trading algorithm.
    '''
    
    self.SetStartDate(2000, 1, 1)  # Set the start date of the backtest.
    self.SetCash(100000)  # Set the initial capital for the backtest.
    
    self.momentum_data = {}  # Initialize a dictionary to store Rate of Change (ROC) indicators for each asset.
    momentum_period = 252  # Define the momentum period (typically 252 trading days, equivalent to 12 months).
    self.SetWarmUp(momentum_period, Resolution.Daily)  # Set the warm-up period for the algorithm.
    
    self.assets_to_trade = 3  # Define the number of assets to hold positions in simultaneously.
    
    self.asset_symbols = ["SPY", "EFA", "IEF", "VNQ", "GSG"]  # List of asset symbols to consider for trading.
    
    # Loop through each asset symbol, adding them to the algorithm and initializing their ROC indicators.
    for asset in self.asset_symbols:
        self.AddEquity(asset, Resolution.Minute)  # Add the equity data for the asset.
        self.momentum_data[asset] = self.ROC(asset, momentum_period, Resolution.Daily)  # Initialize and store the ROC indicator for the asset.
    
    self.last_rebalance_month = None  # Variable to track the last month the portfolio was rebalanced.

def OnData(self, data):
    '''
    The event handler for new data points. This function checks for the right conditions to rebalance the portfolio based on asset momentum.
    '''
    
    if self.IsWarmingUp:  # Check if the algorithm is still in the warm-up period.
        return
    
    # Check if the current time is the market open time (9:30 AM).
    if self.Time.hour != 9 or self.Time.minute != 30:
        return
    
    self.Debug(f"Market open at: {self.Time}")  # Debug log for market opening time.
    
    # Check if it's time to rebalance the portfolio (done monthly).
    current_month = self.Time.month
    if current_month == self.last_rebalance_month:  # If already rebalanced this month, do nothing.
        return
    self.last_rebalance_month = current_month  # Update the last rebalance month.
    
    self.Debug("Initiating monthly rebalance...")  # Debug log for rebalancing.
    
    # Filter the assets that are ready for trading based on their ROC being ready.
    ready_assets = {
        symbol: roc for symbol, roc in self.momentum_data.items() 
        if symbol in data and data[symbol] and roc.IsReady
    }
    
    # Sort the assets by their momentum in descending order.
    assets_sorted_by_momentum = sorted(ready_assets.items(), key=lambda item: item[1].Current.Value, reverse=True)
    self.Debug(f"Assets sorted for trading: {len(assets_sorted_by_momentum)} required: {self.assets_to_trade}")
    
    # Select the top assets for trading based on momentum.
    assets_to_long = [asset for asset, _ in assets_sorted_by_momentum[:self.assets_to_trade]]
    
    # Liquidate positions not in the top assets list.
    for asset in self.Portfolio:
        if asset not in assets_to_long and self.Portfolio[asset].Invested:
            self.Liquidate(asset)
    
    self.Debug(f"Assets selected for long positions: {assets_to_long}")  # Debug log for selected assets.
    
    # Allocate equal weight to each selected asset in the portfolio.
    for asset in assets_to_long:
        self.SetHoldings(asset, 1 / len(assets_to_long))
