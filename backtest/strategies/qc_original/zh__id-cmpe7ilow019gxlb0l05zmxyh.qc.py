# Original QuantConnect / library Python
# locale=zh slug="投机者扩散压力与商品期货风险溢价"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

import numpy as np
from AlgorithmImports import *
import data_tools
class SpeculatorSpreadingPressureandtheCommodityFuturesRiskPremium(QCAlgorithm):

def Initialize(self):
    self.SetStartDate(2000, 1, 1)
    self.SetCash(100000)
   
    self.symbols = [
                    "CME_S1",   # Soybean Futures, Continuous Contract
                    "CME_W1",   # Wheat Futures, Continuous Contract
                    "CME_SM1",  # Soybean Meal Futures, Continuous Contract
                    "CME_BO1",  # Soybean Oil Futures, Continuous Contract
                    "CME_C1",   # Corn Futures, Continuous Contract
                    "CME_O1",   # Oats Futures, Continuous Contract
                    "CME_LC1",  # Live Cattle Futures, Continuous Contract
                    "CME_FC1",  # Feeder Cattle Futures, Continuous Contract
                    "CME_LN1",  # Lean Hog Futures, Continuous Contract
                    "CME_GC1",  # Gold Futures, Continuous Contract
                    "CME_SI1",  # Silver Futures, Continuous Contract
                    "CME_PL1",  # Platinum Futures, Continuous Contract
                    "CME_CL1",  # Crude Oil Futures, Continuous Contract
                    "CME_HG1",  # Copper Futures, Continuous Contract
                    "CME_LB1",  # Random Length Lumber Futures, Continuous Contract
                    # "CME_NG1",  # Natural Gas (Henry Hub) Physical Futures, Continuous Contract
                    "CME_PA1",  # Palladium Futures, Continuous Contract 
                    "CME_RR1",  # Rough Rice Futures, Continuous Contract
                    "CME_DA1",  # Class III Milk Futures
                    "ICE_RS1",  # Canola Futures, Continuous Contract
                    "ICE_GO1",  # Gas Oil Futures, Continuous Contract
                    "CME_RB2",  # Gasoline Futures, Continuous Contract
                    "CME_KW2",  # Wheat Kansas, Continuous Contract
                    "ICE_WT1",  # WTI Crude Futures, Continuous Contract
                    "ICE_CC1",  # Cocoa Futures, Continuous Contract 
                    "ICE_CT1",  # Cotton No. 2 Futures, Continuous Contract
                    "ICE_KC1",  # Coffee C Futures, Continuous Contract
                    "ICE_O1",   # Heating Oil Futures, Continuous Contract
                    "ICE_OJ1",  # Orange Juice Futures, Continuous Contract
                    "ICE_SB1"   # Sugar No. 11 Futures, Continuous Contract
                    ]
    self.period = 12 * 4
    self.traded_count = 3
    
    # Spreading pressure weekly data.
    self.spreading_pressure = {}
    for symbol in self.symbols:
        # Add quantpedia back-adjusted data.
        data = self.AddData(data_tools.QuantpediaFutures, symbol, Resolution.Daily)
        data.SetFeeModel(data_tools.CustomFeeModel())
        data.SetLeverage(5)
        
        # COT data import.
        cot_symbol = 'Q' + symbol.split('_')[1][:-1]
        self.AddData(data_tools.CommitmentsOfTraders, cot_symbol, Resolution.Daily)
        self.spreading_pressure[symbol] = RollingWindow[float](self.period)
    self.recent_month = -1
    
def OnData(self, data):
    for symbol in self.symbols:
        cot_symbol = 'Q' + symbol.split('_')[1][:-1]
        # Check if custom data is still coming.
        if any([self.securities[x].get_last_data() and self.time.date() > data_tools.LastDateHandler.get_last_update_date()[x] for x in [symbol, cot_symbol]]):
            self.liquidate(symbol)
            self.spreading_pressure[symbol].reset()
            continue
        if cot_symbol in data and data[cot_symbol]:
            cot_data = self.Securities[cot_symbol].GetLastData()
            if cot_data:
                speculator_long_count = cot_data.GetProperty("LARGE_SPECULATOR_LONG")
                speculator_short_count = cot_data.GetProperty("LARGE_SPECULATOR_SHORT")
                hedger_long_count = cot_data.GetProperty("COMMERCIAL_HEDGER_LONG")
                hedger_short_count = cot_data.GetProperty("COMMERCIAL_HEDGER_SHORT")
                trader_long_count = cot_data.GetProperty("SMALL_TRADER_LONG")
                trader_short_count = cot_data.GetProperty("SMALL_TRADER_SHORT")
                
                spread = min(speculator_long_count, speculator_short_count)
                open_interest = speculator_long_count + speculator_short_count + hedger_long_count + hedger_short_count + trader_long_count + trader_short_count
                if spread != 0 and open_interest != 0:
                    self.spreading_pressure[symbol].Add(spread / open_interest)
    if self.recent_month == self.Time.month:
        return
    self.recent_month = self.Time.month
    sorted_by_avg_spreading_pressure = sorted([x for x in self.spreading_pressure.items() if x[1].IsReady], key = lambda y: np.mean([x for x in y[1]]), reverse = True)
    long = []
    short = []
    if len(sorted_by_avg_spreading_pressure) >= self.traded_count*2:
        long = [x[0] for x in sorted_by_avg_spreading_pressure[-self.traded_count:]]
        short = [x[0] for x in sorted_by_avg_spreading_pressure[:self.traded_count]]
    # Trade execution.
    targets: List[PortfolioTarget] = []
    for i, portfolio in enumerate([long, short]):
        for symbol in portfolio:
            if symbol in data and data[symbol]:
                targets.append(PortfolioTarget(symbol, ((-1) ** i) / len(portfolio)))
    
    self.SetHoldings(targets, True)
