# Original QuantConnect / library Python
# locale=en slug="trading-commodity-calendar-spreads"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

import numpy as np
class TradingCommodityCalendarSpreads(QCAlgorithm):

def Initialize(self):
    self.SetStartDate(2010, 1, 1)
    self.SetCash(100000)
   
    # 1st contract and the number of contracts to approximately 12 months away.
    self.contracts = {
                    "CHRIS/CME_S" :  8,  # Soybean Futures, Continuous Contract
                    "CHRIS/CME_W"  : 6,  # Wheat Futures, Continuous Contract
                    "CHRIS/CME_SM" : 9,  # Soybean Meal Futures, Continuous Contract
                    "CHRIS/CME_BO" : 9,  # Soybean Oil Futures, Continuous Contract
                    "CHRIS/CME_C" :  6,  # Corn Futures, Continuous Contract
                    "CHRIS/CME_O" :  6,  # Oats Futures, Continuous Contract
                    "CHRIS/CME_LC" : 7,  # Live Cattle Futures, Continuous Contract
                    "CHRIS/CME_FC" : 7,  # Feeder Cattle Futures, Continuous Contract
                    "CHRIS/CME_LN" : 9,  # Lean Hog Futures, Continuous Contract
                    "CHRIS/CME_GC" : 9,  # Gold Futures, Continuous Contract
                    "CHRIS/CME_SI" : 9,  # Silver Futures, Continuous Contract
                    "CHRIS/CME_PL" : 7,  # Platinum Futures, Continuous Contract
                    "CHRIS/CME_CL" : 12, # Crude Oil Futures, Continuous Contract
                    "CHRIS/CME_HG" : 13, # Copper Futures, Continuous Contract
                    "CHRIS/CME_LB" : 7,  # Random Length Lumber Futures, Continuous Contract
                    "CHRIS/CME_NG" : 12, # Natural Gas (Henry Hub) Physical Futures, Continuous Contract
                    "CHRIS/CME_PA" : 7,  # Palladium Futures, Continuous Contract 
                    "CHRIS/CME_RR" : 7,  # Rough Rice Futures, Continuous Contract
                    # "CHRIS/CME_CU" : 13, # Chicago Ethanol (Platts) Futures
                    "CHRIS/CME_DA" : 13, # Class III Milk Futures
                    
                    "CHRIS/ICE_CC" : 6,  # Cocoa Futures, Continuous Contract 
                    "CHRIS/ICE_CT" : 6,  # Cotton No. 2 Futures, Continuous Contract
                    "CHRIS/ICE_KC" : 6,  # Coffee C Futures, Continuous Contract
                    "CHRIS/ICE_O" :  13, # Heating Oil Futures, Continuous Contract
                    "CHRIS/ICE_OJ" : 7,  # Orange Juice Futures, Continuous Contract
                    "CHRIS/ICE_SB" : 5   # Sugar No. 11 Futures, Continuous Contract
                    }
    self.rebalance_flag = True
    
    for future, future_count in self.contracts.items():
        for index in range(1, future_count + 1):
            contract = future + str(index)

            data = self.AddData(QuandlFutures, contract, Resolution.Daily)
            data.SetFeeModel(CustomFeeModel(self))
            data.SetLeverage(5)
    
    self.Schedule.On(self.DateRules.MonthStart('CHRIS/CME_S1'), self.TimeRules.AfterMarketOpen('CHRIS/CME_S1'), self.Rebalance)

def Rebalance(self):
    self.rebalance_flag = True
    
def OnData(self, data):
    if not self.rebalance_flag:
        return
    self.rebalance_flag = False
    
    long = []
    short = []
    for future, future_count in self.contracts.items():
        # curve_shape = sum( np.diff( [ self.Securities[future + str(index)].Price for index in range(1, 6) if self.Securities.ContainsKey(future + str(index)) ] ) )
        curve_shape = sum( np.diff( [ data[future + str(index)].Value for index in range(1, 6) if (future + str(index)) in data ] ) )
        curve_shape /= future_count
        if curve_shape != 0:
            # diff = np.diff( [ self.Securities[future + str(index)].Price for index in range(1, future_count + 1) if self.Securities.ContainsKey(future + str(index)) ] )
            diff = np.diff( [ data[future + str(index)].Value for index in range(1, future_count + 1) if (future + str(index)) in data ] )
            abs_diff = [abs(x) for x in diff]
            max_diff_index = abs_diff.index(max(abs_diff))
            min_diff_index = abs_diff.index(min(abs_diff))
            
            # Offset index by 2 to get right symbols to trade.
            max_diff_index += 2
            min_diff_index += 2
            
            if curve_shape > 0:
                # Backwardation.
                long.append(future + str(max_diff_index))
                short.append(future + str(min_diff_index))
            else:
                # Contango.
                long.append(future + str(min_diff_index))
                short.append(future + str(max_diff_index))
    
    # Trade execution.
    invested = [x.Key.Value for x in self.Portfolio if x.Value.Invested]
    for symbol in invested:
        if symbol not in long + short:
            self.Liquidate(symbol)
    
    weight = 1 / len(self.contracts)
    
    for symbol in long:
        if self.Securities[symbol].Price != 0:
            self.SetHoldings(symbol, weight)
    for symbol in short:
        if self.Securities[symbol].Price != 0:
            self.SetHoldings(symbol, -weight)
# Quandl free data
class QuandlFutures(PythonQuandl):
def __init__(self):
    self.ValueColumnName = "settle"
# Custom fee model.
class CustomFeeModel(FeeModel):
def GetOrderFee(self, parameters):
    fee = parameters.Security.Price * parameters.Order.AbsoluteQuantity * 0.00005
    return OrderFee(CashAmount(fee, "USD"))
