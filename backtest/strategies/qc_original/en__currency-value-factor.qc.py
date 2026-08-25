# Original QuantConnect / library Python
# locale=en slug="currency-value-factor"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

# Import the algorithm base and dictionary collection from external libraries.
from AlgoLib import algorithm
from System.Collections.Generic import Dictionary

# Define the class PPPBasedCurrencyStrategy which inherits from an unspecified class XXX.
class PPPBasedCurrencyStrategy(XXX):
def Initialize(self):
    """Initializes the trading algorithm with starting conditions and data subscriptions."""
    
    # Set the start date of the algorithm to January 1st, 2000.
    self.SetStartDate(2000, 1, 1)
    
    # Set the initial cash to $100,000.
    self.SetCash(100000)

    # Define leverage and the number of symbols to trade.
    self.leverage = 3
    self.symbols_to_trade = 3
    
    # Initialize an empty dictionary to store purchasing power parity data.
    self.purchasing_power_parity = {}

    # Define a mapping between future symbols and their corresponding PPP symbols.
    self.future_to_ppp_mapping = {
        "CME_AD1": "AUS_PPP",
        "CME_BP1": "GBR_PPP",
        "CME_CD1": "CAD_PPP",
        "CME_EC1": "DEU_PPP",
        "CME_JY1": "JPN_PPP",
        "CME_NE1": "NZL_PPP",
        "CME_SF1": "CHE_PPP"
    }

    # Subscribe to futures data and purchasing power parity data for each mapped symbol.
    for future_symbol, ppp_symbol in self.future_to_ppp_mapping.items():
        self.AddFuture(future_symbol, Resolution.Daily, self.leverage)
        self.AddData(custom.PurchasingPowerParity, ppp_symbol, Resolution.Daily)
    
    # Set the minimum order margin as a percentage of the portfolio to 0.0, allowing for higher leverage.
    self.Settings.MinimumOrderMarginPortfolioPercentage = 0.0
    
    # Initialize a variable to keep track of the last month processed.
    self.last_month_processed = None
    
def OnData(self, data):
    """Handles new data events and decides when to rebalance the portfolio."""
    
    # If the current month is the same as the last processed month, do nothing.
    if self.Time.month == self.last_month_processed:
        return
    
    # Update the PPP data with the latest values.
    self.UpdatePPPData(data)
    
    # Update the last processed month to the current month.
    self.last_month_processed = self.Time.month

    # If it's January, rebalance the portfolio.
    if self.Time.month == 1:
        self.RebalancePortfolio(data)

def AddFuture(self, symbol, resolution, leverage):
    """Adds a future to the data subscription with specified leverage."""
   
    # Add the future data to the algorithm with specified resolution.
    future = self.AddData(custom.QuantpediaFutures, symbol, resolution)
    
    # Set the leverage for the future.
    future.SetLeverage(leverage)
    
    # Return the future object for further use (if needed).
    return future

def UpdatePPPData(self, data):
    """Updates the purchasing power parity data for each symbol in the mapping."""
    
    # Iterate through each symbol and its corresponding PPP symbol.
    for symbol, ppp_symbol in self.future_to_ppp_mapping.items():
        
        # If the PPP symbol data is available in the new data, update the PPP data dictionary.
        if ppp_symbol in data:
            self.purchasing_power_parity[symbol] = data[ppp_symbol].Value

def RebalancePortfolio(self, data):
    """Rebalances the portfolio based on the purchasing power parity data."""
    
    # Check if there's enough PPP data to rebalance the portfolio.
    if len(self.purchasing_power_parity) >= self.symbols_to_trade * 2:
        
        # Sort the symbols by their PPP value.
        sorted_symbols = sorted(self.purchasing_power_parity.items(), key=lambda x: x[1])
        
        # Select symbols for long positions (the ones with highest PPP).
        long_symbols = [symbol for symbol, _ in sorted_symbols[-self.symbols_to_trade:]]
        
        # Select symbols for short positions (the ones with lowest PPP).
        short_symbols = [symbol for symbol, _ in sorted_symbols[:self.symbols_to_trade]]

        # Clear the PPP data for the next rebalance.
        self.purchasing_power_parity.clear()
        
        # Execute the trades based on the selected long and short positions.
        self.ExecuteTrades(long_symbols, short_symbols, data)

def ExecuteTrades(self, long_symbols, short_symbols, data):
    """Executes the trading strategy by setting holdings based on desired long and short positions."""
    
    # Liquidate positions that are no longer in the selected long or short symbols.
    for symbol in self.Portfolio.keys():
        if symbol not in long_symbols + short_symbols and self.Portfolio[symbol].Invested:
            self.Liquidate(symbol)

    # Set holdings for long positions, equally distributing the investment.
    for symbol in long_symbols:
        if symbol in data:
            self.SetHoldings(symbol, 1 / len(long_symbols))
    
    # Set holdings for short positions, equally distributing the investment.
    for symbol in short_symbols:
        if symbol in data:
            self.SetHoldings(symbol, -1 / len(short_symbols))
