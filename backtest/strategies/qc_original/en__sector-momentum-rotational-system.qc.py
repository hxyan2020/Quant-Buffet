# Original QuantConnect / library Python
# locale=en slug="sector-momentum-rotational-system"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

from AlgoLib import *

class SectorMomentumAlgorithm(XXX):
'''
A sector momentum trading algorithm that selects sectors based on their momentum,
rebalances monthly, and leverages the AlgoLib for executing trades and managing portfolio.
'''

def Initialize(self):
    '''
    Initializes the trading algorithm settings, including start date, initial cash,
    selected sectors, momentum period, and warm-up period.
    '''
    
    self.SetStartDate(2015, 1, 1)  # Set the start date of the algorithm
    self.SetCash(100000)  # Set the initial cash amount
    
    # Initialize dictionary to store monthly momentum data for each sector
    self.data:Dict[str, Momentum] = {}
    
    # Set the period (in trading days) over which to measure momentum
    self.momentum_period:int = 252
    
    # Set the algorithm to warm up with the specified number of days of data
    self.SetWarmUp(self.momentum_period, Resolution.Daily)
    
    # Number of top sectors to select based on momentum
    self.selected_symbol_count:int = 3 

    # Define the list of sectors to be considered for momentum trading
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

    # Loop through the selected sectors, add them to the algorithm, set leverage, and calculate momentum
    for sector in self.selected_sectors:
        data = self.AddEquity(sector, Resolution.Daily)
        data.SetLeverage(2)  # Set leverage for each sector
        
        # Calculate momentum for each sector and store it
        self.data[sector] = self.MOMP(sector, self.momentum_period, Resolution.Daily)
    
    # Subscribe to the momentum update event for the first sector
    self.data[self.selected_sectors[0]].Updated += self.OnMomentumUpdated
    
    # Variable to store the most recent month processed
    self.recent_month:int = -1
    
    # Flag to indicate when rebalancing should occur
    self.rebalance_flag:bool = False

def OnMomentumUpdated(self, sender, updated) -> None:
    '''
    Event handler for momentum updates. Sets a flag to trigger rebalancing
    if the current month has changed since the last update.
    '''
    
    # Set rebalance flag if the month has changed
    if self.recent_month != self.Time.month:
        self.recent_month = self.Time.month
        self.rebalance_flag = True
    
def OnData(self, data: Slice) -> None:
    '''
    Called on new data. Rebalances the portfolio monthly based on momentum,
    liquidating positions not in the top momentum sectors and investing in new top sectors.
    '''
    
    if self.IsWarmingUp: return  # Skip if the algorithm is still warming up

    # Check if it's time to rebalance
    if self.rebalance_flag:
        self.rebalance_flag = False  # Reset the rebalance flag
        
        # Sort sectors by momentum and filter out those not ready or not present in the latest data
        sorted_by_momentum:List = sorted([x for x in self.data.items() if x[1].IsReady and \
            x[0] in self.selected_sectors and \
            x[0] in data and data[x[0]]], \
            key = lambda x: x[1].Current.Value, reverse = True)

        # Liquidate if there are not enough sectors to select
        if len(sorted_by_momentum)
