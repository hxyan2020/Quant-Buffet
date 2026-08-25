# Original QuantConnect / library Python
# locale=en slug="股票中的短期反转效应"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

from AlgoLib import *  # Import all components from a custom or third-party algorithm library
import pandas as pd  # Import the pandas library for data manipulation and analysis

class ReversalStrategyAlgorithm(XXX):
"""
This class implements a reversal trading strategy using a quantitative approach.
It selects stocks based on their market capitalization and recent price performance,
aiming to buy undervalued stocks and sell overvalued ones.
"""

def Initialize(self):
    """
    Initializes the algorithm settings, including the start date, initial cash,
    target index, stock selection criteria, and scheduling of the trading routine.
    """
    self.SetStartDate(2000, 1, 1)  # Sets the start date for the backtest
    self.SetCash(100000)  # Sets the initial cash for the portfolio
    
    # Defines the main index to track and various strategy parameters
    self.main_index = self.AddEquity('SPY', Resolution.Daily).Symbol
    self.num_stocks = 100
    self.sort_key_market_cap = lambda stock: stock.MarketCap
    self.lookback_days = 21
    self.lookback_week = 5
    self.select_count = 10
    self.max_leverage = 5
    self.minimum_price_threshold = 1.0
    
    # Initializes lists for buying and selling, and a dictionary to store stock data
    self.buy_list = []
    self.sell_list = []
    self.stock_data = {}
    
    # Flag for rebalancing the portfolio
    self.rebalance_flag = False
    self.UniverseSettings.Resolution = Resolution.Daily  # Sets the data resolution
    self.AddUniverse(self.stock_selection_criteria)  # Defines the universe selection function
    self.Settings.MinimumOrderMarginPortfolioPercentage = 0.0  # Sets the minimum margin requirement
    
    # Schedules the trading routine to run every day after market open for the main index
    self.Schedule.On(self.DateRules.EveryDay(self.main_index), self.TimeRules.AfterMarketOpen(self.main_index), self.DecideAndExecute)

def stock_selection_criteria(self, universe):
    """
    Defines the criteria for selecting stocks to include in the universe.
    It filters stocks based on fundamental data and price threshold, and ranks them
    by market capitalization.
    """
    
    for equity in universe:  # Updates price data for each equity in the universe
        if equity.Symbol in self.stock_data:
            self.stock_data[equity.Symbol].add_price(equity.AdjustedPrice)
    
    if not self.rebalance_flag:  # If not rebalancing, keep the universe unchanged
        return Universe.Unchanged

    # Filters and selects stocks based on fundamental data and minimum price threshold
    selected_stocks = [stock for stock in universe if stock.HasFundamentalData and 
                       stock.Market == 'usa' and stock.Price >= self.minimum_price_threshold]
    if len(selected_stocks) > self.num_stocks:  # Limits the number of stocks to num_stocks
        selected_stocks = sorted(selected_stocks, key=self.sort_key_market_cap, reverse=True)[:self.num_stocks]

    # Initializes dictionaries to store performance data
    performance_data_month = {}
    performance_data_week = {}

    # Calculates performance data for each selected stock
    for stock in selected_stocks:
        symbol = stock.Symbol
        if symbol not in self.stock_data:
            self.stock_data[symbol] = PriceData(self.lookback_days + 1)
            history = self.History(symbol, self.lookback_days + 1, Resolution.Daily)
            if history.empty:
                continue
            for close_price in history['close']:
                self.stock_data[symbol].add_price(close_price)
        
        if self.stock_data[symbol].ready():
            performance_data_month[symbol] = self.stock_data[symbol].calculate_performance(self.lookback_days)
            performance_data_week[symbol] = self.stock_data[symbol].calculate_performance(self.lookback_week)

    self.assign_trading_lists(performance_data_month, performance_data_week)  # Assigns buy and sell lists
    
    return [stock.Symbol for stock in selected_stocks]  # Returns the symbols of selected stocks

def assign_trading_lists(self, month_data, week_data):
    """
    Determines which stocks to buy and which to sell based on their monthly and weekly
    performance data.
    """
    
    if len(month_data) > 2 * self.select_count:  # Ensures enough data is available
        week_sorted = sorted(week_data, key=week_data.get)[:self.select_count]  # Selects top performers for buying
        month_sorted = sorted(month_data, key=month_data.get, reverse=True)[:self.select_count]  # Selects bottom performers for selling
        
        self.buy_list = week_sorted
        self.sell_list = month_sorted

def DecideAndExecute(self):
    """
    Decides whether to rebalance the portfolio based on the trading routine schedule
    and executes trades if necessary.
    """
    
    if self.Time.day % 5 == 0:  # Checks if it's time to consider rebalancing
        self.rebalance_flag = True
    
    if not self.rebalance_flag:  # If not rebalancing, exits the function
        return
    
    self.rebalance_flag = False  # Resets the rebalance flag
    self.execute_trades()  # Executes trades based on the current buy and sell lists

def execute_trades(self):
    """
    Executes the trading strategy by liquidating positions not in the buy or sell lists
    and adjusting holdings according to the buy and sell lists.
    """
    
    for symbol in self.Portfolio:  # Liquidates positions not in the buy or sell lists
        if symbol not in self.buy_list + self.sell_list and self.Portfolio[symbol].Invested:
            self.Liquidate(symbol)
    
    for symbol in self.buy_list:  # Sets holdings for stocks in the buy list
        self.SetHoldings(symbol, 1 / len(self.buy_list))
    for symbol in self.sell_list:  # Sets holdings for stocks in the sell list
        self.SetHoldings(symbol, -1 / len(self.sell_list))
    
    # Clears the buy and sell lists after execution
    self.buy_list.clear()
    self.sell_list.clear()

class PriceData:
"""
Stores and manages price data for a single stock, allowing for the calculation
of performance metrics over specified periods.
"""

def __init__(self, capacity):
    """
    Initializes the PriceData object with a capacity for storing price data.
    """
    
    self.prices = RollingWindow[float](capacity)  # Initializes a rolling window for price data

def add_price(self, price):
    """
    Adds a new price to the rolling window of price data.
    """
    
    self.prices.Add(price)  # Adds a new price to the rolling window

def ready(self):
    """
    Checks if the rolling window is filled to capacity and ready for analysis.
    """
    
    return self.prices.IsReady  # Returns true if the rolling window is ready

def calculate_performance(self, period):
    """
    Calculates the performance of the stock over a given period.
    """
    
    return self.prices[0] / self.prices[period] - 1  # Calculates performance based on price change

# Custom fee model remains unchanged
class CustomFeeModel(FeeModel):
"""
Implements a custom fee model for the algorithm, overriding the default fee model.
"""

def GetOrderFee(self, parameters):
    """
    Calculates the order fee based on the price and quantity of the security being traded.
    """
    
    fee = parameters.Security.Price * parameters.Order.AbsoluteQuantity * 0.00005  # Calculates the fee
    return OrderFee(CashAmount(fee, "USD"))  # Returns the calculated fee
