# Original QuantConnect / library Python
# locale=en slug="growth-gap-factor-in-fixed-income"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

import numpy as np
from AlgorithmImports import *
import data_tools
from typing import Dict, List
class GrowthGapFactorinFixedIncome(QCAlgorithm):
def Initialize(self):
    self.SetStartDate(1990, 1, 1)
    self.SetCash(100000)
    
    # Bond symbol and GDP symbol. (GDP at current prices)
    self.symbols = {
        "ASX_XT1" : "AUS_GDP",        # 10 Year Commonwealth Treasury Bond Futures, Continuous Contract #1 (Australia)
        "MX_CGB1" : "CAN_GDP",        # Ten-Year Government of Canada Bond Futures, Continuous Contract #1 (Canada)
        "EUREX_FGBL1" : "DEU_GDP",    # Euro-Bund (10Y) Futures, Continuous Contract #1 (Germany)
        "LIFFE_R1" : "GBR_GDP",       # Long Gilt Futures, Continuous Contract #1 (U.K.)
        "CME_TY1" : "USA_GDP"         # 10 Yr Note Futures, Continuous Contract #1 (USA)
    }
    
    # Yearly GDP data used for SMA.
    self.data:Dict[str, float] = {}
    self.sma_period:int = 5
    self.leverage:int = 3
    
    for bond_future, gdp_symbol in self.symbols.items():
        # Futures data.
        data = self.AddData(data_tools.QuantpediaFutures, bond_future, Resolution.Daily)
        data.SetFeeModel(data_tools.CustomFeeModel())
        data.SetLeverage(self.leverage)
        self.data[gdp_symbol] = RollingWindow[float](self.sma_period)
        
        # Bond yield data.
        self.AddData(data_tools.GDPData, gdp_symbol, Resolution.Daily)
    self.Settings.MinimumOrderMarginPortfolioPercentage = 0.

def OnData(self, data: Slice) -> None:
    trade_flag:bool = False
    gdp_last_update_date:Dict[str, datetime.date] = data_tools.GDPData.get_last_update_date()
    future_last_update_date:Dict[str, datetime.date] = data_tools.QuantpediaFutures.get_last_update_date()
    symbols_to_delete:List[str] = []
    # store yearly gdp data
    for bond_future, gdp_symbol in self.symbols.items():
        # data is still coming
        if self.Securities[bond_future].GetLastData() and self.Time.date() > future_last_update_date[bond_future] \
            or self.Securities[gdp_symbol].GetLastData() and self.Time.date() > gdp_last_update_date[gdp_symbol]:
            symbols_to_delete.append(bond_future)
            continue
        if gdp_symbol in data and data[gdp_symbol]:
            gdp:float = data[gdp_symbol].Value
            self.data[gdp_symbol].Add(gdp)
            trade_flag = True
        
    if len(symbols_to_delete) != 0:
        for symbol in symbols_to_delete:
            self.symbols.pop(symbol)
    # rebalance once the new data arrived
    if not trade_flag: 
        return
    
    # SMA gap
    sma_gap:Dict[str, float] = { x[0] : ((self.Securities[x[1]].Price - np.average([gdp for gdp in self.data[x[1]]])) / np.average([gdp for gdp in self.data[x[1]]])) for x in self.symbols.items()
                                        if self.Securities.ContainsKey(x[1]) and x[1] in self.data and self.data[x[1]].IsReady and self.Securities[x[0]].GetLastData() and (self.Time.date() - self.Securities[x[0]].GetLastData().Time.date()).days
