# Original QuantConnect / library Python
# locale=en slug="国际股票etf中的反转效应"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

from AlgoLib import *

class InternationalEquityReversals(XXX):
'''
This class implements an international equity reversal strategy using the XXX framework.
It focuses on identifying and trading based on momentum reversals in international ETFs.
'''

def Initialize(self):
    '''
    Initializes the algorithm settings, including start date, initial cash, 
    the list of ETF symbols to trade, momentum score dictionary, analysis period, 
    and rebalance interval.
    '''
    
    self.SetStartDate(2000, 1, 1)  # Set the start date of the algorithm
    self.SetCash(100000)  # Set the initial cash balance

    self.momentum_scores = {}  # Initialize a dictionary to store momentum scores

    self.analysis_period = 36 * 21  # Define the analysis period in trading days (approx. 36 months)
    self.SetWarmUp(self.analysis_period, Resolution.Daily)  # Warm-up period for indicators

    # Define a list of ETF symbols representing various international markets
    self.etf_symbols = [
        "EWA",  # Australia
        "EWO",  # Austria
        "EWK",  # Belgium
        "EWZ",  # Brazil
        "EWC",  # Canada
        "FXI",  # China
        "EWQ",  # France
        "EWG",  # Germany
        "EWH",  # Hong Kong
        "EWI",  # Italy
        "EWJ",  # Japan
        "EWM",  # Malaysia
        "EWW",  # Mexico
        "EWN",  # Netherlands
        "EWS",  # Singapore
        "EZA",  # South Africa
        "EWY",  # South Korea
        "EWP",  # Spain
        "EWD",  # Sweden
        "EWL",  # Switzerland
        "EWT",  # Taiwan
        "THD",  # Thailand
        "EWU",  # UK
        "SPY",  # USA
    ]

    # Add each ETF symbol to the algorithm, set fee model and leverage, and initialize momentum scores
    for symbol in self.etf_symbols:
        equity = self.AddEquity(symbol, Resolution.Daily)
        equity.SetFeeModel(EnhancedFeeModel())  # Set a custom fee model
        equity.SetLeverage(15)  # Set leverage for each equity

        # Calculate the Rate of Change (ROC) indicator for each symbol for the analysis period
        self.momentum_scores[symbol] = self.ROC(symbol, self.analysis_period, Resolution.Daily)
    
    self.rebalance_interval = 36  # Set rebalance interval in months
    self.last_rebalance_month = -1  # Initialize the last rebalance month

def OnData(self, data: Slice):
    '''
    This method is called whenever new data is received. It checks if the warm-up period is complete, 
    then rebalances the portfolio based on momentum scores if the rebalance interval has been reached.
    '''
    
    if self.IsWarmingUp:
        return  # Do nothing if the algorithm is still warming up

    current_month = self.Time.month  # Get the current month

    # Check if the current month is the same as the last rebalance month to avoid multiple rebalances within the same month
    if current_month == self.last_rebalance_month:
        return

    self.last_rebalance_month = current_month  # Update the last rebalance month
    self.rebalance_interval += 1  # Increment the rebalance interval counter

    # Check if the rebalance interval is less than or equal to 36 months
    if self.rebalance_interval
