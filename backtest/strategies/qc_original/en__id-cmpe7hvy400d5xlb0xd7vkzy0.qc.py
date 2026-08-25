# Original QuantConnect / library Python
# locale=en slug="地缘政治风险与大宗商品"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

from AlgorithmImports import *
#endregion

import data_tools
import statsmodels.api as sm

class GeopoliticalRiskAndCommodities(QCAlgorithm):

def Initialize(self):
    self.SetStartDate(2000, 1, 1)
    self.SetCash(100000)
    
    self.leverage:int = 5
    self.part_length = 5
    self.max_missing_days = 5
    
    self.month_period = 21
    self.regression_period = 60
    self.period = 6 * self.month_period
    
    self.data = {}
    
    self.symbols = [
        "CME_S1",   # Soybean Futures, Continuous Contract #1
        "CME_W1",   # Wheat Futures, Continuous Contract #1
        "CME_SM1",  # Soybean Meal Futures, Continuous Contract #1
        "CME_BO1",  # Soybean Oil Futures, Continuous Contract #1
        "CME_C1",   # Corn Futures, Continuous Contract #1
        "CME_O1",   # Oats Futures, Continuous Contract #1
        "CME_LC1",  # Live Cattle Futures, Continuous Contract #1
        "CME_FC1",  # Feeder Cattle Futures, Continuous Contract #1
        "CME_LN1",  # Lean Hog Futures, Continuous Contract #1
        "CME_GC1",  # Gold Futures, Continuous Contract #1
        "CME_SI1",  # Silver Futures, Continuous Contract #1
        "CME_PL1",  # Platinum Futures, Continuous Contract #1
        "CME_CL1",  # Crude Oil Futures, Continuous Contract #1
        "CME_HG1",  # Copper Futures, Continuous Contract #1
        "CME_LB1",  # Random Length Lumber Futures, Continuous Contract #1
        "CME_NG1",  # Natural Gas (Henry Hub) Physical Futures, Continuous Contract #1
        "CME_PA1",  # Palladium Futures, Continuous Contract  #1
        "CME_RR1",  # Rough Rice Futures, Continuous Contract #1
        "CME_CU1",  # Chicago Ethanol (Platts) Futures
        "CME_DA1",  # Class III Milk Futures
        
        "ICE_CC1",  # Cocoa Futures, Continuous Contract  #1
        "ICE_CT1",  # Cotton No. 2 Futures, Continuous Contract #1
        "ICE_KC1",  # Coffee C Futures, Continuous Contract #1
        "ICE_O1",   # Heating Oil Futures, Continuous Contract #1
        "ICE_OJ1",  # Orange Juice Futures, Continuous Contract #1
        "ICE_SB1"   # Sugar No. 11 Futures, Continuous Contract #1
    ]
    
    for symbol in self.symbols:
        # subscribe price data
        data = self.AddData(data_tools.QuantpediaFutures, symbol, Resolution.Daily)
        data.SetFeeModel(data_tools.CustomFeeModel())
        data.SetLeverage(self.leverage)
        
        # quandl data
        quandl_symbol_1 = 'CHRIS/' + symbol
        quandl_symbol_2 = 'CHRIS/' + symbol.replace('1', '2')
        
        # subscribe to quandl data
        self.AddData(data_tools.QuandlFutures, quandl_symbol_1, Resolution.Daily)
        self.AddData(data_tools.QuandlFutures, quandl_symbol_2, Resolution.Daily)
        
        # store SymbolData
        self.data[symbol] = data_tools.SymbolData([quandl_symbol_1, quandl_symbol_2], self.month_period, self.period, self.regression_period)
    
    # subscribe to geopolitical risk data    
    self.geo_risk_index_symbol = self.AddData(data_tools.QuantpediaGeopoliticalRisk, 'GEOPOLITICAL_RISK_INDEX', Resolution.Daily).Symbol
    self.geo_risk_index_data = data_tools.IndexData(self.month_period)
    
    self.regression_x_data = data_tools.RegressionData(self.regression_period)
    
    # rebalancing monthly based on self.curr_month variable
    self.curr_month = -1

def OnData(self, data):
    curr_date = self.Time.date()
    
    # rebalance monthly
    if self.curr_month != self.Time.month:
        self.curr_month = self.Time.month
        self.Rebalance(curr_date)
    
    # check if geopolitical risk index data are ready
    if self.geo_risk_index_symbol in data and data[self.geo_risk_index_symbol]:
        # collect index data
        index_value = data[self.geo_risk_index_symbol].Value
        self.geo_risk_index_data.update(index_value, curr_date)
    
    for symbol in self.data:
        q_sym1, q_sym2 = self.data[symbol].quandl_symbols
        
        # update futures daily prices 
        if symbol in data and data[symbol]:
            close = data[symbol].Value
            self.data[symbol].update(close, curr_date)
        
        # calculate carry factor only when carry value wasn't set in this month
        if self.data[symbol].carry_value == None and q_sym1 in data and q_sym2 in data and data[q_sym1] and data[q_sym2]:
            value1 = data[q_sym1].Value
            value2 = data[q_sym2].Value
            self.data[symbol].update_carry_value(np.log(value2 / value1))
                
def Rebalance(self, curr_date):
    ''' collects needed data for regression, then perform regresion, selection and trade '''
    
    # continue only if geopolitical index values are ready and new geopolitical index values are still coming
    if not self.geo_risk_index_data.is_ready(curr_date, self.max_missing_days):
        self.Liquidate()
        return 
    
    symbol_values = {}
    
    for symbol, symbol_obj in self.data.items():
        # make sure future data are ready and are still coming
        if symbol_obj.is_ready(curr_date, self.max_missing_days):
            future_closes = [x for x in symbol_obj.closes]
            
            # calculate future's monthly performance
            short_term_momentum = self.CalculatePerformance(future_closes, self.month_period)
            
            # calculate long term momentum for momentum factor
            long_term_momentum = self.CalculatePerformance(future_closes, self.period)
            
            # carry
            carry_value = symbol_obj.carry_value
            
            symbol_values[symbol] = data_tools.SymbolValue(short_term_momentum, carry_value, long_term_momentum)
            
            # update future's performance
            symbol_obj.update_momentum_values(short_term_momentum)
            
        symbol_obj.reset_carry_value()
    
    # to make sure X regression data has same length update only when condition isn't true
    if len(symbol_values)  float:
    values = values[:period]
    performance = (values[0] - values[-1]) / values[-1]
    
    return performance
    
def CarryFactorCalculation(self, symbol_values: dict) -> float:
    ''' based on carry factor change value select backwardation and contango futures and calculate total performance for current month '''
    
    sorted_by_carry_value = [x[0] for x in sorted(symbol_values.items(), key=lambda item: item[1].carry_value)]
    
    # long commodities that are most in backwardation
    long_part = sorted_by_carry_value[:self.part_length]
    
    # short the ones that are most in contango
    short_part = sorted_by_carry_value[-self.part_length:]
    
    carry_factor_perf = self.CalculateFactorReturn(symbol_values, long_part, short_part)
    
    return carry_factor_perf
    
def MomentumFactorCalculation(self, symbol_values: dict) -> float:
    ''' select top n and low n futures based on momentum factor value and calculate their total performance for current month '''
    
    sorted_by_mom = [x[0] for x in sorted(symbol_values.items(), key=lambda item: item[1].long_term_performance)]
    
    # long highest n futures
    long_part = sorted_by_mom[-self.part_length:]
    
    # short lowest n futures
    short_part = sorted_by_mom[:self.part_length]
    
    momentum_factor_perf = self.CalculateFactorReturn(symbol_values, long_part, short_part)
    
    return momentum_factor_perf
    
def CalculateFactorReturn(self, symbol_values: dict, long_part: list, short_part: list) -> float:
    ''' calculate total performance of factor for current month '''
    
    long_value = np.mean([symbol_values[symbol].short_term_performance for symbol in long_part])
    short_value = np.mean([-symbol_values[symbol].short_term_performance for symbol in short_part])
    
    factor_value = (long_value + short_value) / 2
    
    return factor_value
    
def MultipleLinearRegression(self, x, y):
    x = np.array(x).T
    x = sm.add_constant(x)
    result = sm.OLS(endog=y, exog=x).fit()
    return result
