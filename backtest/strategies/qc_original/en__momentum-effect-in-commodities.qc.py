# Original QuantConnect / library Python
# locale=en slug="momentum-effect-in-commodities"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

from AlgorithmImports import *

class CommodityMomentumStrategy(QCAlgorithm):
'''
This class defines a commodity momentum trading strategy.
It initializes trading settings, selects commodities based on momentum,
and manages positions accordingly.
'''

def Initialize(self):
    '''Initializes the trading algorithm settings, including start date, initial cash,
    commodity tickers to trade, analysis period, and momentum indicators for each commodity.'''
    
    self.SetStartDate(2000, 1, 1)  # Set the start date for the algorithm
    self.SetCash(100000)  # Set the initial cash for the algorithm

    # Define the commodity tickers that will be traded
    self.commodity_tickers = [
        "CME_S1", "CME_W1", "CME_SM1", "CME_BO1", "CME_C1", "CME_O1",
        "CME_LC1", "CME_FC1", "CME_LN1", "CME_GC1", "CME_SI1", "CME_PL1",
        "CME_CL1", "CME_HG1", "CME_LB1", "CME_NG1", "CME_PA1", "CME_RR1",
        "CME_DA1", "ICE_RS1", "ICE_GO1", "CME_RB2", "CME_KW2", "ICE_WT1",
        "ICE_CC1", "ICE_CT1", "ICE_KC1", "ICE_O1", "ICE_OJ1", "ICE_SB1",
    ]

    self.analysis_period = 252  # Approx. 12 months of trading days
    self.SetWarmUp(self.analysis_period, Resolution.Daily)  # Set warm-up period for indicators
    self.momentum_indicator = {}  # Dictionary to store momentum indicators for each commodity

    # Initialize momentum indicators for each commodity ticker
    for ticker in self.commodity_tickers:
        commodity = self.AddData(QuantpediaFutures, ticker, Resolution.Daily)  # Add commodity data
        commodity.SetFeeModel(StandardFeeModel())  # Set fee model for the commodity
        commodity.SetLeverage(5)  # Set leverage for the commodity
        
        # Add a Rate of Change (ROC) indicator for the commodity based on the analysis period
        self.momentum_indicator[commodity.Symbol] = self.ROC(ticker, self.analysis_period, Resolution.Daily)

    self.previous_month = -1  # Variable to track the last processed month

def OnData(self, data: Slice):
    '''Processes new data and manages portfolio positions based on momentum strategy.'''
    
    if self.IsWarmingUp:  # Check if the algorithm is still in the warm-up period
        return

    if self.Time.month == self.previous_month:  # Check if this month has already been processed
        return
    self.previous_month = self.Time.month  # Update the last processed month

    # Calculate the performance (momentum) for each commodity and filter out the ones not ready
    performance = {symbol: indicator.Current.Value for symbol, indicator in self.momentum_indicator.items() if indicator.IsReady and symbol in data}

    if len(performance)
