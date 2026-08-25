# Original QuantConnect / library Python
# locale=en slug="国家股指中的动量因子效应"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

from AlgoLib import *

class GlobalIndexMomentumStrategy(XXX):
'''
This strategy implements a global index momentum-based trading strategy.
It invests in the top-performing country equity indexes based on their
momentum, which is calculated using the Rate of Change (ROC) indicator
over a predefined analysis period.
'''

def Initialize(self):
    '''
    Initializes the trading algorithm settings, including the start date,
    initial cash, list of index symbols to be tracked, and the setup for
    the Rate of Change (ROC) indicator for each symbol.
    '''
    self.SetStartDate(2000, 1, 1)  # Set the start date of the algorithm.
    self.SetCash(100000)  # Set the initial cash for the portfolio.

    # Initialize performance tracking dictionary.
    self.performance = {}
    
    # Analysis period set for 6 months, approximated by trading days.
    self.analysis_period = 6 * 21
    self.SetWarmUp(self.analysis_period, Resolution.Daily)  # Warm-up period for indicators.
    
    # List of ETFs representing various country equity indexes.
    self.index_symbols = [
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
        "EWU",  # United Kingdom
        "SPY",  # USA
    ]

    self.top_performers_count = 5  # Number of top performers to invest in.

    for symbol in self.index_symbols:
        equity = self.AddEquity(symbol, Resolution.Daily)  # Add equity for tracking.
        equity.SetFeeModel(StandardFeeModel())  # Set the fee model.
        equity.SetLeverage(5)  # Set leverage for each equity.
        
        # Initialize and track the Rate of Change (ROC) indicator for each symbol.
        self.performance[symbol] = self.ROC(symbol, self.analysis_period, Resolution.Daily)
        
    self.last_month_processed = -1  # Track the last processed month.

def OnData(self, data: Slice):
    '''
    This method is called at the start of each trading day. It checks for
    the top-performing indexes based on momentum and adjusts the portfolio
    accordingly by liquidating positions not in the top performers and
    investing in the new top performers.
    '''
    
    if self.IsWarmingUp:
        return  # Do nothing if the algorithm is still warming up.

    # Execute trades at the start of the trading day after warm-up.
    if self.Time.hour == 9 and self.Time.minute == 30:
        if self.Time.month == self.last_month_processed:
            return  # Do nothing if we have already processed this month.
        
        self.last_month_processed = self.Time.month  # Update the last processed month.
        
        # Sort symbols by their momentum in descending order.
        momentum_sorted = sorted([x for x in self.performance.items() if x[1].IsReady and x[0] in data], key=lambda x: x[1].Current.Value, reverse=True)
        to_invest = []

        # Select the top performers to invest in.
        if len(momentum_sorted) >= self.top_performers_count:
            to_invest = [x[0] for x in momentum_sorted[:self.top_performers_count]]
            
        # Adjust portfolio based on the selected top performers.
        for symbol in self.Portfolio:
            if symbol not in to_invest:
                self.Liquidate(symbol)  # Liquidate positions not in the top performers.
        
        for symbol in to_invest:
            self.SetHoldings(symbol, 1 / len(to_invest))  # Invest in the top performers evenly.
        
class StandardFeeModel(FeeModel):
'''
This class represents a customized fee model where the order fee is calculated
as a percentage of the transaction amount, with a custom fee rate specified.
'''

def GetOrderFee(self, parameters: OrderFeeParameters):
    '''
    Calculates the fee for an order based on the custom fee rate.
    
    :param parameters: Contains details about the order for which the fee is calculated.
    :return: The calculated fee for the order.
    '''
    
    fee = parameters.Security.Price * parameters.Order.AbsoluteQuantity * 0.0001  # Calculate the fee at the custom rate.
    return OrderFee(CashAmount(fee, "USD"))  # Return the calculated fee.
