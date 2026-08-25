# Original QuantConnect / library Python
# locale=en slug="timing-carry-trade"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

import data_tools
from AlgorithmImports import *
from collections import deque
import numpy as np
class TimingCarryTrade(QCAlgorithm):
def Initialize(self):
    self.SetStartDate(2000, 1, 1) 
    self.SetCash(100000)
    
    # Source: https://www.quandl.com/data/OECD-Organisation-for-Economic-Co-operation-and-Development
    self.symbols = {
                    "CME_AD1" : "OECD/KEI_IR3TIB01_AUS_ST_M",   # Australian Dollar Futures, Continuous Contract #1
                    "CME_BP1" : "OECD/KEI_IR3TIB01_GBR_ST_M",   # British Pound Futures, Continuous Contract #1
                    "CME_CD1" : "OECD/KEI_IR3TIB01_CAN_ST_M",   # Canadian Dollar Futures, Continuous Contract #1
                    "CME_EC1" : "OECD/KEI_IR3TIB01_EA19_ST_M",  # Euro FX Futures, Continuous Contract #1
                    "CME_JY1" : "OECD/KEI_IR3TIB01_JPN_ST_M",   # Japanese Yen Futures, Continuous Contract #1
                    "CME_MP1" : "OECD/KEI_IR3TIB01_MEX_ST_M",   # Mexican Peso Futures, Continuous Contract #1
                    "CME_NE1" : "OECD/KEI_IR3TIB01_NZL_ST_M",   # New Zealand Dollar Futures, Continuous Contract #1
                    "CME_SF1" : "SNB/ZIMOMA"                    # Swiss Franc Futures, Continuous Contract #1
    }
    
    # Daily price data.
    self.data = {}
    self.period = 3 * 21
    self.SetWarmUp(self.period)
    # Regression data rolling window.
    self.regression_min_period = 60
    self.regression_data = deque()
    
    self.commodity_index = self.AddEquity('DBC', Resolution.Daily).Symbol    
    self.data[self.commodity_index] = deque(maxlen = self.period)
    
    # Quandl ted spread.
    self.ted_spread = self.AddData(data_tools.QuandlValue, 'FRED/TEDRATE', Resolution.Daily).Symbol
    
    # Last selected long and short symbols used to calculate monthly performace of carry trade.
    self.long = []
    self.short = []
    
    for symbol, rate_symbol in self.symbols.items():
        self.AddData(data_tools.QuandlValue, rate_symbol, Resolution.Daily)
        data = self.AddData(data_tools.QuantpediaFutures, symbol, Resolution.Daily)
        data.SetFeeModel(data_tools.CustomFeeModel())
        data.SetLeverage(5)
        
        self.data[symbol] = deque(maxlen = self.period)
    
    self.Schedule.On(self.DateRules.MonthStart(self.commodity_index), self.TimeRules.AfterMarketOpen(self.commodity_index), self.Rebalance)
def OnData(self, data):
    for symbol in self.data:
        symbol_obj = self.Symbol(symbol)
        if symbol_obj in data and data[symbol_obj]:
            price = data[symbol_obj].Value
            self.data[symbol].append(price)
def Rebalance(self):
    # make sure data is still comming in
    if self.Securities[self.commodity_index].GetLastData() and (self.Time.date() - self.Securities[self.commodity_index].GetLastData().Time.date()).days > 5:
        self.Liquidate()
        return
    if self.Securities[self.ted_spread].GetLastData() and (self.Time.date() - self.Securities[self.ted_spread].GetLastData().Time.date()).days > 5:
        self.Liquidate()
        return
    
    # Regression data.
    carry_trade_performance = None
    delta_crb = None
    delta_vol = None
    ted_spread = None
    
    # Calculate carry trade last month's performance.
    if len(self.long) != 0 and len(self.short) != 0:
        carry_trade_perf_long = np.sum([data_tools.Return([y for y in self.data[x]][-21:]) for x in self.long if x in self.data and len(self.data[x]) == self.data[x].maxlen])
        carry_trade_perf_short = np.sum([-1 * data_tools.Return([y for y in self.data[x]][-21:]) for x in self.short if x in self.data and len(self.data[x]) == self.data[x].maxlen])
        carry_trade_performance = (carry_trade_perf_long + carry_trade_perf_short) / len(self.long + self.short)
        self.long.clear()
        self.short.clear()
        
    # Interbank rate sorting.
    sorted_by_rate = sorted([y for y in self.symbols if self.Securities[y].GetLastData() and (self.Time.date() - self.Securities[y].GetLastData().Time.date()).days  traded_count*2:
        self.long = [x for x in sorted_by_rate[:traded_count]]
        self.short = [x for x in sorted_by_rate[-traded_count:]]
    
    # Commodity index log change.
    if len(self.data[self.commodity_index]) == self.data[self.commodity_index].maxlen:
        delta_crb = np.log(self.data[self.commodity_index][-1] / self.data[self.commodity_index][0]) / 3
        
    # Average volatility.
    # t and t-3 volatility tuples.
    t_t_3_vol = [(data_tools.Volatility([y for y in self.data[x]][-21:]), data_tools.Volatility([y for y in self.data[x]][:21])) for x in self.symbols if x in self.data and len(self.data[x]) == self.data[x].maxlen]
    if len(t_t_3_vol) != 0:
        avg_t_volatility = np.average([x[0] for x in t_t_3_vol])
        avg_t_3_volatility = np.average([x[1] for x in t_t_3_vol])
        if avg_t_volatility != 0 and avg_t_3_volatility != 0:
            delta_vol = np.log(avg_t_volatility / avg_t_3_volatility) / 3
    # TED spread.
    if self.Securities[self.ted_spread].Price != 0:
        ted_spread = self.Securities[self.ted_spread].Price
    
    if delta_crb and delta_vol and ted_spread:
        self.regression_data.append((carry_trade_performance, delta_crb, delta_vol, ted_spread))
    
    # Regression data is ready.
    if len(self.regression_data) >= self.regression_min_period:
        carry_trade_performances = [float(x[0]) for x in self.regression_data]
        crb_deltas = [float(x[1]) for x in self.regression_data]
        vol_deltas = [float(x[2]) for x in self.regression_data]
        ted_spreads = [float(x[3]) for x in self.regression_data]
    
        # Regression.
        x = [crb_deltas[:-1], vol_deltas[:-1], ted_spreads[:-1]]
        regression_model = data_tools.MultipleLinearRegression(x, carry_trade_performances[1:])
        # Predicted carry return.
        alpha = regression_model.params[0]
        prediction_x = [crb_deltas[-1], vol_deltas[-1], ted_spreads[-1]]
        betas = np.array(regression_model.params[1:])
        carry_return_predicted = alpha + sum(np.multiply(betas, prediction_x))
        
        if carry_return_predicted > 0:
            # Trade execution.
            invested = [x.Key.Value for x in self.Portfolio if x.Value.Invested]
            for symbol in invested:
                if symbol not in self.long + self.short:
                    self.Liquidate(symbol)
            
            for symbol in self.long:
                self.SetHoldings(symbol, 1 / len(self.long))
            for symbol in self.short:
                self.SetHoldings(symbol, -1 / len(self.short))
