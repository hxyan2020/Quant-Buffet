# Original QuantConnect / library Python
# locale=zh slug="产出缺口预测外汇收益"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

from AlgorithmImports import *
import numpy as np
import statsmodels.api as sm
#endregion
class OutputGapPredictsFXReturns(QCAlgorithm):
def Initialize(self):
    self.SetStartDate(2000, 1, 1)
    self.SetCash(100000)
    
    self.symbols = [
        ("CME_AD1", "AUS"),   # Australian Dollar Futures, "AUS"
        ("CME_BP1", "GBR"),   # British Pound Futures, "GBR"
        ("CME_CD1", "CAN"),   # Canadian Dollar Futures, "CAN"
        ("CME_EC1", "EA19"),   # Euro FX Futures, "EA19"
        ("CME_JY1", "JPN"),   # Japanese Yen Futures, "JPN"
        ("CME_MP1", "MEX"),   # Mexican Peso Futures, "MEX"
        ("CME_NE1", "NZL"),   # New Zealand Dollar Futures, "NZL"
        ("CME_SF1", "CHE")   # Swiss Franc Futures "CHE"
    ]
    
    self.data = {}
    self.length = 12 # Lenght of each variable in regression
    self.regression_period = 48 # Need 48 monthly data for regression x
    self.quantile = 5
    self.max_missing_days = 5
    
    # These are countries with quarterly data, which were adjusted to monthly data
    self.not_complete_monthly_data = ['AUS', 'NZL', 'CHE']
    
    # Takes only countries with complete monthly data, when flag is True
    self.monthly_flag = False
    
    for currency, industrial in self.symbols:
        # Check if strategy works with all data
        if not self.monthly_flag or industrial not in self.not_complete_monthly_data:
            # Subscribe to future
            data = self.AddData(QuantpediaFutures, currency, Resolution.Daily)
            data.SetFeeModel(CustomFeeModel())
            data.SetLeverage(5)
            
            # Subscribe to country industrial
            self.AddData(QuantpediaIndustrial, industrial, Resolution.Daily)
            # Create SymbolData for industrial, with future symbol
            self.data[industrial] = SymbolData(self.regression_period, data.Symbol)
            
    self.symbol = self.AddEquity('SPY', Resolution.Daily).Symbol
    self.recent_month = -1
def OnData(self, data):
    # Update industrial values
    for symbol in self.data:
        if symbol in data and data[symbol]:
            value = data[symbol].Value
            self.data[symbol].update(value, self.Time.date())
    
    if self.recent_month == self.Time.month:
        return
    self.recent_month = self.Time.month
    output_gaps = {}
    
    # Go through each country industrial and make regression
    for industrial_symbol, symbol_data in self.data.items():
        if not self.Securities[industrial_symbol].GetLastData() or not self.Securities[symbol_data.future_symbol].GetLastData():
            continue
        if (self.Time.date() - self.Securities[industrial_symbol].GetLastData().Time.date()).days > self.max_missing_days or \
            (self.Time.date() - self.Securities[symbol_data.future_symbol].GetLastData().Time.date()).days > self.max_missing_days:
            continue
        # Check if regression data are ready
        if not symbol_data.is_ready():
            continue
        
        # Change flag to prevent including country in next rebalance, if new value won't come in OnData
        symbol_data.new_value_flag = False
        
        # Get future symbol for this country
        future_symbol = symbol_data.future_symbol
        
        # Create regression variables (y, x)
        regression_y, regression_x = symbol_data.create_regression_variables(self.length)
        
        regression_model = self.MultipleLinearRegression(regression_x, regression_y)
        
        # Store output gap under future symbol of this country
        output_gaps[future_symbol] = regression_model.resid[-1]
        
    # Continue only if there is enough data for quintile selection
    if len(output_gaps)
