# Original QuantConnect / library Python
# locale=en slug="size-factor-small-capitalization-stocks-premium"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

from AlgorithmImports import *  # Import necessary modules from the QuantConnect library
from typing import List  # Import the List type from the typing module for type annotations

class SmallCapPremiumStrategy(QCAlgorithm):
'''
This strategy focuses on trading small-cap stocks, utilizing leverage and a monthly rebalancing schedule
to adjust holdings based on market capitalization deciles. The strategy trades stocks from NYSE, NASDAQ,
and AMEX exchanges.
'''

def Initialize(self):
    '''
    Initialize the algorithm settings, including start date, initial cash, universe settings, and scheduling
    rebalance events.
    '''
    
    self.SetStartDate(2000, 1, 1)  # Start date for the algorithm
    self.SetCash(100000)  # Initial cash for the algorithm

    self.UniverseSettings.Leverage = 5  # Leverage for the universe
    self.UniverseSettings.Resolution = Resolution.Daily  # Resolution for data requests
    self.AddUniverse(self.SelectStocks)  # Adding the universe selection method
    self.Settings.MinimumOrderMarginPortfolioPercentage = 0.0  # Set the minimum margin
    
    self.long_list: List[Symbol] = []  # List for stocks to long
    self.short_list: List[Symbol] = []  # List for stocks to short

    self.market_ids: List[str] = ['NYSE', 'NASDAQ', 'AMEX']  # Targeted exchanges
    self.top_stocks_count: int = 3000  # Number of stocks to consider based on market cap
    
    self.deciles: int = 10  # Split into deciles
    self.rebalance_period: int = 12  # Monthly rebalance
    self.should_rebalance: bool = True  # Flag for rebalancing

    spy_symbol: Symbol = self.AddEquity('SPY', Resolution.Daily).Symbol  # Add SPY as a benchmark
    self.Schedule.On(self.DateRules.MonthEnd(spy_symbol), 
                     self.TimeRules.AfterMarketOpen(spy_symbol), 
                     self.RebalancePortfolio)  # Schedule the rebalance at the end of each month after market opens

def SelectStocks(self, fundamentals: List[Fundamental]) -> List[Symbol]:
    '''
    Universe selection function that filters and sorts stocks based on market capitalization and 
    selects stocks for long and short positions.
    
    Parameters:
    fundamentals (List[Fundamental]): List of fundamental data for universe selection.

    Returns:
    List[Symbol]: Symbols of stocks selected for trading.
    '''
    
    if not self.should_rebalance:
        return Universe.Unchanged  # Do not change the universe if rebalance is not needed

    # Filter stocks that have fundamental data and are in the specified exchanges
    filtered_stocks = [f for f in fundamentals if f.HasFundamentalData and f.SecurityReference.ExchangeId in self.market_ids]
    
    # Sort the filtered stocks by market cap and select the top stocks
    sorted_by_cap = sorted(filtered_stocks, key=lambda x: x.MarketCap)[:self.top_stocks_count]

    if len(sorted_by_cap) >= self.deciles:
        size = len(sorted_by_cap) // self.deciles  # Calculate the size of each decile
        self.long_list = [x.Symbol for x in sorted_by_cap[:size]]  # Select stocks for long positions
        self.short_list = [x.Symbol for x in sorted_by_cap[-size:]]  # Select stocks for short positions

    return self.long_list + self.short_list  # Return the combined list of stocks for trading

def OnData(self, data: Slice):
    '''
    Event handler for new data. This function adjusts the portfolio based on the selected stocks for long
    and short positions.

    Parameters:
    data (Slice): The current market data.
    '''
    
    if not self.should_rebalance:
        return  # Do nothing if no rebalance is required
    
    self.should_rebalance = False  # Reset the rebalance flag
    
    # Calculate the target portfolio weights and create investment targets
    investments = [PortfolioTarget(symbol, 1 / len(self.long_list)) for symbol in self.long_list] + \
                  [PortfolioTarget(symbol, -1 / len(self.short_list)) for symbol in self.short_list]

    self.SetHoldings(investments)  # Adjust the portfolio according to the investment targets

    self.long_list.clear()  # Clear the list of long stocks
    self.short_list.clear()  # Clear the list of short stocks

def RebalancePortfolio(self):
    '''
    Sets the flag to indicate that the portfolio should be rebalanced at the next OnData event.
    '''
    
    self.should_rebalance = True  # Set the rebalance flag to True

def OnSecuritiesChanged(self, changes: SecurityChanges):
    '''
    Event handler for changes in the investment universe. This function sets the fee model for added securities.

    Parameters:
    changes (SecurityChanges): The changes in the investment universe.
    '''
    
    for security in changes.AddedSecurities:
        security.SetFeeModel(SimpleFeeModel())  # Set the fee model for added securities

class SimpleFeeModel(FeeModel):
'''
Simple fee model class that calculates order fees based on a fixed percentage of the trade value.
'''

def GetOrderFee(self, parameters: OrderFeeParameters) -> OrderFee:
    '''
    Calculates the fee for an order.

    Parameters:
    parameters (OrderFeeParameters): The parameters of the order for which the fee is calculated.

    Returns:
    OrderFee: The calculated order fee.
    '''
    
    fee = parameters.Security.Price * parameters.Order.AbsoluteQuantity * 0.00005  # Calculate the fee
    return OrderFee(CashAmount(fee, "USD"))  # Return the fee as an OrderFee object
