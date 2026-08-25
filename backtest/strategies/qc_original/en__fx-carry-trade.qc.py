# Original QuantConnect / library Python
# locale=en slug="fx-carry-trade"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

from AlgoLib import *

class SectorMomentumAlgorithm(XXX):
"""
A Sector Momentum Algorithm that selects and trades sectors based on their momentum.
It initializes with a set starting cash, selects a subset of sectors to trade, and
rebalances the portfolio based on momentum indicators.
"""

def Initialize(self):
    """
    Initializes the algorithm settings, including start date, initial cash, and the momentum calculation period.
    Sets up the sectors to monitor and applies leverage.
    """
    
    self.SetStartDate(2015, 1, 1)  # Set the start date of the algorithm.
    self.SetCash(100000)  # Set the starting cash for the portfolio.
    
    # Initializes a dictionary to hold momentum data for each sector.
    self.data:Dict[str, Momentum] = {}
    
    # The period over which momentum is calculated.
    self.momentum_period:int = 252
    
    # Set the algorithm to warm up with the specified period to allow indicators to initialize.
    self.SetWarmUp(self.momentum_period, Resolution.Daily)
    
    # The number of sectors to select based on momentum.
    self.selected_symbol_count:int = 3 

    # A list of selected sectors to monitor for momentum.
    self.selected_sectors:List[str] = [
        "XLK",  # Technology
        "XLE",  # Energy
        "XLV",  # Health Care
        "XLF",  # Financial
        "XLI",  # Industrial
        "XLB",  # Materials
        "XLY",  # Consumer Discretionary
        "XLP",  # Consumer Staples
        "XLU"   # Utilities
    ]

    # Add equity data for each sector, set leverage, and initialize momentum indicators.
    for sector in self.selected_sectors:
        data = self.AddEquity(sector, Resolution.Daily)
        data.SetLeverage(2)
        
        # Initializes momentum object for each sector with the specified period.
        self.data[sector] = self.MOMP(sector, self.momentum_period, Resolution.Daily)
    
    # Subscribe to the momentum indicator's updated event for the first sector.
    self.data[self.selected_sectors[0]].Updated += self.OnMomentumUpdated
    
    # Variable to track the most recent month processed to ensure monthly rebalance.
    self.recent_month:int = -1
    
    # A flag to trigger portfolio rebalance.
    self.rebalance_flag:bool = False

def OnMomentumUpdated(self, sender, updated) -> None:
    """
    Event handler for momentum indicator updates. It sets a flag to trigger portfolio rebalancing.
    """
    
    # Check if the month has changed since the last update and set the rebalance flag.
    if self.recent_month != self.Time.month:
        self.recent_month = self.Time.month
        self.rebalance_flag = True
    
def OnData(self, data: Slice) -> None:
    """
    Event handler for new data. This function rebalances the portfolio based on sector momentum, if necessary.
    """
    
    if self.IsWarmingUp: return  # Skip if the algorithm is still warming up.

    # Check if it's time to rebalance the portfolio.
    if self.rebalance_flag:
        self.rebalance_flag = False  # Reset the flag
        
        # Sort sectors by momentum and filter for readiness and data availability.
        sorted_by_momentum:List = sorted([x for x in self.data.items() if x[1].IsReady and \
            x[0] in self.selected_sectors and \
            x[0] in data and data[x[0]]], \
            key = lambda x: x[1].Current.Value, reverse = True)

        # If there are fewer sectors than the target count, liquidate the portfolio.
        if len(sorted_by_momentum)
