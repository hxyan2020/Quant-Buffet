# Original QuantConnect / library Python
# locale=en slug="trend-following-in-commodity-calendar-spreads"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

import numpy as np
class TrendFollowinginCommodityCalendarSpreads(QCAlgorithm):

def Initialize(self):
    self.SetStartDate(2010, 1, 1)
    self.SetCash(100000)
   
    # quandl contract symbol and contract number approximately 12 months away
    self.futures_last_contract = {
                    "CHRIS/CME_S" :  "8",   # Soybean Futures, Continuous Contract
                    "CHRIS/CME_W"  : "6",   # Wheat Futures, Continuous Contract
                    "CHRIS/CME_SM" : "9",   # Soybean Meal Futures, Continuous Contract
                    "CHRIS/CME_BO" : "9",   # Soybean Oil Futures, Continuous Contract
                    "CHRIS/CME_C" :  "6",   # Corn Futures, Continuous Contract
                    # "CHRIS/CME_O" :  "6",   # Oats Futures, Continuous Contract
                    "CHRIS/CME_LC" : "7",   # Live Cattle Futures, Continuous Contract
                    "CHRIS/CME_FC" : "7",   # Feeder Cattle Futures, Continuous Contract
                    "CHRIS/CME_LN" : "9",   # Lean Hog Futures, Continuous Contract
                    "CHRIS/CME_GC" : "9",   # Gold Futures, Continuous Contract
                    "CHRIS/CME_SI" : "9",   # Silver Futures, Continuous Contract
                    # "CHRIS/CME_PL" : "7",   # Platinum Futures, Continuous Contract
                    "CHRIS/CME_CL" : "12",  # Crude Oil Futures, Continuous Contract
                    "CHRIS/CME_HG" : "13",  # Copper Futures, Continuous Contract
                    # "CHRIS/CME_LB" : "7",   # Random Length Lumber Futures, Continuous Contract
                    # "CHRIS/CME_PA" : "7",   # Palladium Futures, Continuous Contract 
                    # "CHRIS/CME_RR" : "7",   # Rough Rice Futures, Continuous Contract
                    # "CHRIS/CME_DA" : "13",  # Class III Milk Futures
                    
                    "CHRIS/ICE_CC" : "6",   # Cocoa Futures, Continuous Contract 
                    "CHRIS/ICE_CT" : "6",   # Cotton No. 2 Futures, Continuous Contract
                    "CHRIS/ICE_KC" : "6",   # Coffee C Futures, Continuous Contract
                    "CHRIS/ICE_O" :  "3",   # Heating Oil Futures, Continuous Contract
                    "CHRIS/ICE_OJ" : "7",   # Orange Juice Futures, Continuous Contract
                    "CHRIS/ICE_SB" : "5"    # Sugar No. 11 Futures, Continuous Contract
                    }
    self.period:int = 50
    self.SetWarmUp(self.period, Resolution.Daily)
    
    # spread data - MA is calculated out of signal spread
    self.signal_spread:dict = {}
            
    for c_sym, last_c_num in self.futures_last_contract.items():
        # add #1 and #2 and one approx. year away contracts
        for c_num in [1, 2, last_c_num]:
            data = self.AddData(QuandlFutures, c_sym+str(c_num), Resolution.Daily)
            data.SetFeeModel(CustomFeeModel(self))
            data.SetLeverage(5)
        self.signal_spread[c_sym] = RollingWindow[float](self.period)
    
def OnData(self, data):
    for c_sym, last_c_num in self.futures_last_contract.items():
        
        front_contract_sym:str = c_sym + '1'
        further_contract_sym:str = c_sym + '2'
        contract_1y_away_sym:str = c_sym + last_c_num
        
        # calculate #1 and #2 spread
        if front_contract_sym in data and further_contract_sym in data and contract_1y_away_sym in data and \
            data[front_contract_sym] and data[further_contract_sym] and data[contract_1y_away_sym]:
            front_price:float = data[front_contract_sym].Value
            further_price:float = data[further_contract_sym].Value
            
            if front_price > 0 and further_price > 0:
                current_spread:float = front_price - further_price
                self.signal_spread[c_sym].Add(current_spread)
                if self.signal_spread[c_sym].IsReady:
                    spread_ma:float = np.mean([x for x in self.signal_spread[c_sym]])
                    weight:float = 1. / len(self.futures_last_contract)
                    
                    if current_spread > spread_ma:
                        # long trading spread
                        self.SetHoldings(contract_1y_away_sym, weight)
                        self.SetHoldings(front_contract_sym, -weight)
                    else:
                        # short trading spread
                        self.SetHoldings(front_contract_sym, weight)
                        self.SetHoldings(contract_1y_away_sym, -weight)
            else:
                self.Debug(f"Price bellow 0: {front_contract_sym}:{front_price}, {further_contract_sym}:{further_price}")
        else:
            # check if quandl data is still comming in
            if not all(self.Securities[symbol].GetLastData() and (self.Time.date() - self.Securities[symbol].GetLastData().Time.date()).days
