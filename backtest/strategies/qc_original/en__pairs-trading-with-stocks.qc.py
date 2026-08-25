# Original QuantConnect / library Python
# locale=en slug="pairs-trading-with-stocks"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

from AlgoLib import *
import numpy as np
from itertools import combinations
from pandas import DataFrame

class StockPairsTradingAlgorithm(XXX):
'''Implements a stock pairs trading strategy using quantitative methods.
This algorithm selects stocks based on fundamental and historical price data to form pairs that are expected to move together. When the spread between the pairs diverges, trades are executed with the expectation that the spread will revert to its historical mean.'''

def Initialize(self):
    '''Sets up the initial environment of the trading algorithm, including starting cash, start date, and universe selection parameters.'''
    
    self.SetStartDate(2010, 1, 1)  # Set the start date of the backtest
    self.SetCash(100000)  # Set the starting cash
    
    self.benchmark: Symbol = self.AddEquity('SPY', Resolution.Daily).Symbol  # Define the benchmark security

    self.price_history: Dict[Symbol, RollingWindow] = {}  # Initialize a dictionary to store price history for each symbol
    self.analysis_period: int = 252  # Define the period for analysis (typically 252 trading days in a year)
    self.leverage: int = 5  # Set the leverage to be used for trading
    self.minimum_price: float = 5.  # Set the minimum price filter for stock selection
    self.rebalance_month: int = 6  # Set the month for rebalancing
    
    self.maximum_pairs: int = 5  # Set the maximum number of stock pairs to hold
    self.active_pairs: List = []  # Initialize a list to track active pairs
    self.position_sizes: Dict = {}  # Initialize a dictionary to manage the sizes of positions
    
    self.pairs_sorted: List = []  # Initialize a list to keep sorted pairs based on some criteria
    
    self.top_fundamentals: int = 500  # Set the number of stocks to consider based on fundamentals
    self.sort_key = lambda x: x.DollarVolume  # Define the key for sorting stocks

    self.current_month: int = 6  # Track the current month for rebalancing
    self.should_select: bool = True  # Flag to decide whether to select new stocks
    self.UniverseSettings.Resolution = Resolution.Daily  # Set the data resolution for the universe selection
    self.AddUniverse(self.SelectStocks)  # Add a universe selection method
    self.Settings.MinimumOrderMarginPortfolioPercentage = 0.  # Set the minimum margin requirement
    self.Schedule.On(self.DateRules.MonthStart(self.benchmark), self.TimeRules.AfterMarketOpen(self.benchmark), self.Rebalance)  # Schedule the rebalancing method

def OnSecuritiesChanged(self, changes):
    '''Handles changes to the securities in the universe, including setting leverage and fee model for added securities and updating the possible pairs of securities for trading.'''
    
    for security in changes.AddedSecurities:
        security.SetLeverage(5)  # Set leverage for added securities
        security.SetFeeModel(CustomFeeModel())  # Set a custom fee model
    
    for security in changes.RemovedSecurities:
        if security.Symbol in self.price_history:
            del self.price_history[security.Symbol]  # Remove the price history of removed securities
    
    all_symbols = [sym for sym in self.price_history if sym != self.benchmark]  # Get all symbols except the benchmark
    self.possible_pairs = list(combinations(all_symbols, 2))  # Generate all possible pairs
    
    pair_distances = {}
    for pair in self.possible_pairs:
        if all([self.price_history[sym].IsReady for sym in pair]):
            pair_distances[pair] = self.CalculateDistance(self.price_history[pair[0]], self.price_history[pair[1]])  # Calculate the distance for each pair
    
    self.pairs_sorted = [pair for pair, _ in sorted(pair_distances.items(), key=lambda item: item[1])[:20]]  # Sort pairs based on distance and select top 20
    
    self.ClearPositions()  # Clear all positions

def SelectStocks(self, fundamentals: List[Fundamental]) -> List[Symbol]:
    '''Selects stocks based on fundamental data and historical price data, ensuring they meet minimum criteria such as having fundamental data, meeting a minimum price, and belonging to a specific market.'''
    
    for stock in fundamentals:
        symbol = stock.Symbol
        if symbol in self.price_history:
            self.price_history[symbol].Add(stock.AdjustedPrice)  # Update price history with the latest price

    if not self.should_select:
        return Universe.Unchanged  # Return if no selection is needed
    self.should_select = False  # Reset the selection flag
    
    filtered = [x for x in fundamentals if x.HasFundamentalData and x.AdjustedPrice > self.minimum_price and x.Market == 'usa']  # Filter stocks based on criteria
    if len(filtered) > self.top_fundamentals:
        filtered = sorted(filtered, key=self.sort_key, reverse=True)[:self.top_fundamentals]  # Sort and select top stocks based on fundamentals
    
    for stock in filtered:
        symbol = stock.Symbol
        if symbol not in self.price_history:
            self.price_history[symbol] = RollingWindow[float](self.analysis_period)  # Initialize rolling window for new symbols
            price_data: DataFrame = self.History(symbol, self.analysis_period, Resolution.Daily)  # Get historical price data
            if price_data.empty:
                continue
            for _, row in price_data.iterrows():
                self.price_history[symbol].Add(row['close'])  # Populate rolling window with historical prices
    
    return [stock.Symbol for stock in filtered if self.price_history[stock.Symbol].IsReady]  # Return symbols with ready price history

def OnData(self, data: Slice) -> None:
    '''Executes logic when new data arrives, such as evaluating pairs for trading decisions.'''
    
    if not self.pairs_sorted: return  # Exit if no pairs are sorted
    
    pairs_to_remove = self.EvaluatePairs(data)  # Evaluate pairs for potential removal
    
    for pair in pairs_to_remove:
        self.active_pairs.remove(pair)  # Remove inactive pairs
        del self.position_sizes[pair]  # Clear position sizes for removed pairs

def CalculateDistance(self, window_a, window_b) -> float:
    '''Calculates the distance between two securities based on their normalized historical price differences.'''
    
    norm_a = np.array(list(window_a)) / list(window_a)[-1]  # Normalize prices for the first window
    norm_b = np.array(list(window_b)) / list(window_b)[-1]  # Normalize prices for the second window
    
    return np.sum((norm_a - norm_b) ** 2)  # Calculate and return the Euclidean distance
    
def Rebalance(self) -> None:
    '''Triggers the selection of new stocks and pairs based on the rebalance schedule.'''
    
    if self.current_month == self.rebalance_month:
        self.should_select = True  # Enable stock selection
        
    self.current_month = (self.current_month % 12) + 1  # Increment the current month

def ClearPositions(self):
    '''Clears all existing positions to prepare for new trades.'''
    
    self.Liquidate()  # Liquidate all positions
    self.active_pairs.clear()  # Clear list of active pairs
    self.position_sizes.clear()  # Clear position sizes

def EvaluatePairs(self, data):
    '''Evaluates active pairs to determine if any should be closed or adjusted based on new market data.'''
    
    removals = []
    for pair in self.pairs_sorted:
        self.ManagePair(pair, data)  # Placeholder for managing each pair
        # Logic to determine if a pair should be removed goes here
    return removals

# Placeholder for ManagePair method could be added here for detailed trading logic

# Implement the custom fee model here
class CustomFeeModel(FeeModel):
'''Defines a custom fee model for transactions based on the price and quantity of the order.'''

def GetOrderFee(self, parameters):
    '''Calculates the transaction fee based on the order details.'''
    
    fee = parameters.Security.Price * parameters.Order.AbsoluteQuantity * 0.00005  # Calculate fee
    return OrderFee(CashAmount(fee, "USD"))  # Return the fee as an OrderFee object
