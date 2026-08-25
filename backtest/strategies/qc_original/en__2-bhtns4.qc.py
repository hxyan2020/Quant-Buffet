# Original QuantConnect / library Python
# locale=en slug="财报逆转策略-2"
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

def Initialize(self):
    self.SetStartDate(2009, 1, 1)  # Start Date
    self.SetCash(100000)

    self.leverage = 5
    self.earnings_lookback = 30

    self.last_rebalance_year = -1
    self.last_rebalance_month = -1
            
    self.asset_info = {}

    # Earnings and EPS data storage
    self.earnings_announcement_data = defaultdict(list)
    self.earnings_performance_data = defaultdict(lambda: defaultdict(dict))
    
    self.initial_date = None

    earnings_info = self.Download('data.quantpedia.com/backtesting_data/
economic/earnings_dates_eps.json')
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
                self.earnings_performance_data[year][month][symbol] = 
                                                     float(stock_info['eps'])
    
    self.recent_ear_values = []
    self.past_ear_values = []
    
    self.strategy_control = TradingControl(self, 10, 10, 2)

    self.main_asset = self.AddEquity('SPY', Resolution.Daily).Symbol
    
    self.is_selection_time = False
    self.UniverseSettings.Resolution = Resolution.Daily
    self.AddUniverse(self.select_coarse, self.select_fine)
    self.Schedule.On(self.DateRules.MonthStart(self.main_asset), 
self.TimeRules.AfterMarketOpen(self.main_asset), lambda: self.is_selection_time = True)

def select_coarse(self, coarse):
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
            historical_prices = self.History(asset.Symbol, self.earnings_lookback, 
Resolution.Daily)
            if not historical_prices.empty:
                for timestamp, price in historical_prices.loc[asset.Symbol].close.items():
                    self.asset_info[asset.Symbol].update_price(timestamp, price)

    return [asset.Symbol for asset in eligible_assets if self.asset_info[asset.Symbol].is_data_ready()]

def select_fine(self, fine):
    eligible_symbols = []
    for asset in fine:
        symbol = asset.Symbol
        if symbol.Value in self.earnings_performance_data[self.last_rebalance_year]
[self.last_rebalance_month]:
            earnings_date = max(self.earnings_performance_data[self.last_rebalance_year][self.last_rebalance_month][symbol.Value].keys())
            date_range_start = earnings_date - BusinessDay(2)
            date_range_end = earnings_date + BusinessDay(1)

            market_return = self.asset_info[self.main_asset].calculate_return(date_range_start, date_range_end)
            asset_return = self.asset_info[symbol].calculate_return(date_range_start, date_range_end)

            if market_return is not None and asset_return is not None:
                ear = asset_return - market_return
                self.earnings_announcement_data[symbol].append((earnings_date, ear))
                self.recent_ear_values.append(ear)
                eligible_symbols.append(symbol)

    if not eligible_symbols:
        return Universe.Unchanged

    return eligible_symbols

def OnData(self, data):
    target_date = self.Time.date()

    if target_date = high_ear_threshold:
                self.strategy_control.open_trade(symbol, True)
            elif ear_value
