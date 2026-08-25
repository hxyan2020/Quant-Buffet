# Original QuantConnect / library Python
# locale=en slug="climate-beta-and-mutual-funds"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

import statsmodels.api as sm
from AlgorithmImports import *
from data_tools import CustomFeeModel, MutualFund, SymbolData, ClimateChangeData, ClimateChange
from typing import Dict, List
# endregion
class ClimateBetaAndMutualFunds(QCAlgorithm):
def Initialize(self):
    self.SetStartDate(2004, 1, 1)
    self.SetCash(100000)
    
    self.leverage:int = 5
    self.period:int = 24
    self.quantile:int = 5
    self.max_missing_days:int = 5
    self.max_missing_days_climate_change:int = 40
    self.min_prices:int = 15
    self.long_only_flag:bool = False
    self.recent_month:int = -1
    self.data:Dict[Symbol, SymbolData] = {}
    self.climate_change:Symbol = self.AddData(ClimateChange, 'CLIMATE_CHANGE', Resolution.Daily).Symbol
    self.climate_change_data:ClimateChangeData = ClimateChangeData(self.period)
    self.symbol_count:int = 500
    ticker_file_str:str = self.Download('data.quantpedia.com/backtesting_data/equity/mutual_funds/500_mutual_funds_tickers.csv')
    ticker_file_str = ticker_file_str.replace('\r', '')
    self.tickers:List[str] = ticker_file_str.split('\n')[:self.symbol_count]
    for t in self.tickers:
        data = self.AddData(MutualFund, t, Resolution.Daily)
        data.SetFeeModel(CustomFeeModel())
        data.SetLeverage(self.leverage)
        self.data[data.Symbol] = SymbolData(self.period)
def OnData(self, data: Slice) -> None:
    curr_date:datetime.date = self.Time.date()
    
    # store data
    for symbol, symbol_data in self.data.items():
        if symbol in data and data[symbol] and data[symbol].Value != 0:
            symbol_data.update_daily_prices(curr_date, data[symbol].Value)
    if self.climate_change in data and data[self.climate_change]:
        search_value:float = data[self.climate_change].Value
        self.climate_change_data.update(curr_date, search_value)
    # rebalance
    if self.recent_month == self.Time.month:
        return
    self.recent_month = self.Time.month
    # data is still comming in
    if not self.climate_change_data.data_still_coming(curr_date, self.max_missing_days_climate_change):
        self.climate_change_data.reset()
    x:List[float]|None = self.climate_change_data.get_monthly_changes() \
        if self.climate_change_data.is_ready() else None
    beta_values:Dict[Symbol, float] = {}
    # run regression
    for symbol, symbol_data in self.data.items():
        if not symbol_data.prices_still_coming(curr_date, self.max_missing_days):
            symbol_data.reset()
            continue
        if symbol_data.daily_prices_ready(self.min_prices):
            symbol_data.update_monthly_returns()
        if x != None and symbol_data.monthly_returns_ready() and symbol in data \
            and data[symbol] and data[symbol].Value != 0:
            monthly_returns:List[float] = symbol_data.get_monthly_returns()
            regression_model = self.MultipleLinearRegression(x, monthly_returns)
            beta:float = regression_model.params[1]
            beta_values[symbol] = beta
        symbol_data.reset_daily_prices()
    if len(beta_values)
