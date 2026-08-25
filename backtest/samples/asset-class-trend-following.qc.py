from AlgoLib import *

class AssetClassTrendFollowing(QCAlgorithm):
'''
A quant trading algorithm that implements a trend-following strategy across multiple asset classes.
It rebalances the portfolio monthly based on the assets' prices relative to their moving averages.
'''

def Initialize(self):
    '''
    Initializes the algorithm settings, including start date, initial cash, selected assets, and moving average period.
    It also configures the moving averages for each asset and sets up the algorithm warm-up period.
    '''
    
    self.SetStartDate(2000, 1, 1)  # Sets the start date of the backtest
    self.SetCash(100000)  # Sets the initial cash for the backtest

    assets = ["SPY", "EFA", "IEF", "VNQ", "GSG"]  # List of asset symbols to include in the strategy
    moving_avg_period = 10 * 21  # Moving average period (10 months, assuming 21 trading days per month)

    # Dictionary to store the moving average indicator for each asset
    self.asset_moving_avgs = { 
        self.AddEquity(asset, Resolution.Minute).Symbol: self.SMA(asset, moving_avg_period, Resolution.Daily) for asset in assets 
    }

    self.last_rebalance_month = -1  # Tracks the last month the portfolio was rebalanced
    self.SetWarmUp(moving_avg_period, Resolution.Daily)  # Sets the warm-up period for the algorithm
    self.Settings.MinimumOrderMarginPortfolioPercentage = 0.  # Sets the minimum margin for order portfolio percentage

def OnData(self, data: Slice) -> None:
    '''
    The event handler for new data. It rebalances the portfolio once a month based on the defined trend-following strategy.
    '''
    
    if self.IsWarmingUp: 
        return  # Returns immediately if the algorithm is still warming up

    if not (self.Time.hour == 9 and self.Time.minute == 31):
        return  # Ensures rebalancing happens at the beginning of the trading day (9:31 AM)

    # Checks if it's time to rebalance (once a month)
    if self.Time.month == self.last_rebalance_month:
        return  # If already rebalanced this month, do nothing
    self.last_rebalance_month = self.Time.month  # Updates the last rebalance month
    
    # Identifies long assets based on their current price vs moving average
    long_assets = [symbol for symbol, moving_avg in self.asset_moving_avgs.items() 
        if symbol in data 
        and data[symbol] 
        and moving_avg.IsReady 
        and data[symbol].Value > moving_avg.Current.Value
    ]

    # Calculates the target portfolio weights for the assets to go long
    portfolio_targets = [PortfolioTarget(asset, 1. / len(long_assets)) for asset in long_assets]
    self.SetHoldings(portfolio_targets, True)  # Rebalances the portfolio based on the target weights