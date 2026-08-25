# Original QuantConnect / library Python
# locale=en slug="reversal-in-post-earnings-announcement-drift"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

from quantlib import AssetData, TradingCostModel, TradingControl
from StrategyCore import *
import pandas as pd
from collections import defaultdict
from typing import Dict, Tuple
from pandas.tseries.offsets import BusinessDay
from dateutil.relativedelta import relativedelta
import json
from datetime import datetime, date

class EarningsReversalStrategy(QCAlgorithm):
'''
A trading strategy that focuses on earnings announcements and attempts to 
profit from the reversal movement after such announcements. It leverages 
earnings date and EPS (earnings per share) data to make trading decisions.
'''

def Initialize(self):
    '''
    Initializes the strategy, setting the starting conditions, including 
    start date, initial cash, and various parameters for the trading strategy.
    '''
    
    self.SetStartDate(2009, 1, 1)  # Start Date
    self.SetCash(100000)  # Initial cash
    
    self.leverage = 5  # Leverage factor
    self.earnings_lookback = 30  # Lookback period for earnings data

    # Variables to track the last rebalance date
    self.last_rebalance_year = -1
    self.last_rebalance_month = -1
            
    self.asset_info = {}  # Stores information on assets

    # Dictionaries to store earnings and EPS data
    self.earnings_announcement_data = defaultdict(list)
    self.earnings_performance_data = defaultdict(lambda: defaultdict(dict))
    
    self.initial_date = None  # The earliest date from the earnings data

    # Load and parse earnings and EPS data from a JSON file
    earnings_info = self.Download('data.quantpedia.com/backtesting_data/economic/earnings_dates_eps.json')
    earnings_info_parsed = json.loads(earnings_info)
    
    for record in earnings_info_parsed:
        announcement_date = datetime.strptime(record['date'], '%Y-%m-%d').date()
        if not self.initial_date:
            self.initial_date = announcement_date

        for stock_info in record['stocks']:
            symbol = stock_info['ticker']
            self.earnings_announcement_data[announcement_date].append(symbol)

            if stock_info['eps'].strip():
                year, month = announcement_date.year, announcement_date.month
                self.earnings_performance_data[year][month][symbol] = float(stock_info['eps'])
    
    self.recent_ear_values = []  # Store recent earnings announcement returns
    self.past_ear_values = []  # Store past earnings announcement returns
    
    self.strategy_control = TradingControl(self, 10, 10, 2)  # Trading controls

    self.main_asset = self.AddEquity('SPY', Resolution.Daily).Symbol  # Main asset for the universe
    
    self.is_selection_time = False  # Flag to determine if it's time to select assets
    self.UniverseSettings.Resolution = Resolution.Daily
    self.AddUniverse(self.select_coarse, self.select_fine)
    self.Schedule.On(self.DateRules.MonthStart(self.main_asset), 
                     self.TimeRules.AfterMarketOpen(self.main_asset), 
                     lambda: self.is_selection_time = True)

def select_coarse(self, coarse):
    '''
    Filters the universe of assets based on coarse selection criteria, 
    primarily focusing on if the asset's information is updated and if it's 
    selection time based on the strategy's parameters.
    '''
    
    for asset in coarse:
        if asset.Symbol in self.asset_info:
            self.asset_info[asset.Symbol].update_price(self.Time, asset.AdjustedPrice)

    if not self.is_selection_time:
        return Universe.Unchanged
    
    self.is_selection_time = False
    prev_month = (self.Time - relativedelta(months=1)).date()
    self.last_rebalance_year, self.last_rebalance_month = prev_month.year, prev_month.month

    eligible_assets = [x for x in coarse if x.Symbol.Value in 
                       self.earnings_performance_data[self.last_rebalance_year][self.last_rebalance_month]]
    
    for asset in eligible_assets:
        if asset.Symbol not in self.asset_info:
            self.asset_info[asset.Symbol] = AssetData(self.earnings_lookback)
            historical_prices = self.History(asset.Symbol, self.earnings_lookback, Resolution.Daily)
            if not historical_prices.empty:
                for timestamp, price in historical_prices.loc[asset.Symbol].close.items():
                    self.asset_info[asset.Symbol].update_price(timestamp, price)

    return [asset.Symbol for asset in eligible_assets if self.asset_info[asset.Symbol].is_data_ready()]

def select_fine(self, fine):
'''
Performs a finer selection of assets based on more detailed criteria, 
including their earnings performance relative to the market. It filters 
assets that have a significant earnings announcement return (EAR) by 
comparing the asset's return to the market return around the announcement 
date. Assets with significant EAR are considered eligible for trading.
'''

    eligible_symbols = []  # Initialize a list to store symbols of eligible assets.
    
    # Loop through each asset provided in the 'fine' selection.
    for asset in fine:
        symbol = asset.Symbol  # Get the symbol of the current asset.

        # Check if the symbol is present in the earnings performance data for the last rebalance period.
        if symbol.Value in self.earnings_performance_data[self.last_rebalance_year][self.last_rebalance_month]:
            # Find the latest earnings announcement date for the symbol.
            earnings_date = max(self.earnings_performance_data[self.last_rebalance_year][self.last_rebalance_month][symbol.Value].keys())

            # Define the date range around the earnings announcement to analyze.
            date_range_start = earnings_date - BusinessDay(2)  # Start date is two business days before the announcement.
            date_range_end = earnings_date + BusinessDay(1)  # End date is one business day after the announcement.

            # Calculate the return of the main market asset and the current asset in the specified date range.
            market_return = self.asset_info[self.main_asset].calculate_return(date_range_start, date_range_end)
            asset_return = self.asset_info[symbol].calculate_return(date_range_start, date_range_end)

            # If both returns are successfully calculated, compute the earnings announcement return (EAR).
            if market_return is not None and asset_return is not None:
                ear = asset_return - market_return  # EAR is the difference between the asset's return and the market return.

                # Store the earnings date and EAR in the earnings announcement data for the symbol.
                self.earnings_announcement_data[symbol].append((earnings_date, ear))

                # Add the EAR to the list of recent EAR values for future analysis.
                self.recent_ear_values.append(ear)

                # Add the symbol to the list of eligible symbols, indicating it passed the selection criteria.
                eligible_symbols.append(symbol)

    # If no symbols are deemed eligible, return 'Universe.Unchanged' to indicate no change in the asset universe.
    if not eligible_symbols:
        return Universe.Unchanged

    # Return the list of eligible symbols, which will be used to adjust the asset universe for trading.
    return eligible_symbols

def OnData(self, data):
    '''
    Called each time new data is received for the algorithm. This function handles the logic to be 
    executed on each new data point, such as checking if it's the appropriate time to trade based on 
    the strategy's criteria. It liquidates positions if necessary, evaluates the earnings announcement 
    returns (EAR) of symbols against predefined thresholds, and decides whether to open new trades.
    
    Parameters:
    - data: The new market data at the current time step.
    '''

    target_date = self.Time.date()  # Get the current date from the algorithm's time object

    # If the current date is before the strategy's initial start date, do nothing
    if target_date = high_ear_threshold:
                self.strategy_control.open_trade(symbol, True)  # Open a long position
            
            # If the EAR value is below the low threshold, consider it a strong negative response
            elif ear_value
