# Original QuantConnect / library Python
# locale=en slug="美元套利交易"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

import data_tools
import numpy as np
from AlgoLib import *
from typing import Dict

class DollarCarryTrade(XXX):

def Initialize(self):
    self.SetStartDate(2000, 1, 1)
    self.SetCash(100000)
    
    self.leverage:int = 2

    # Source: https://fred.stlouisfed.org/series/IR3TIB01AUM156N
    self.symbols:Dict[str, str] = {
        "CME_AD1" : "IR3TIB01AUM156N",   # Australian Dollar Futures, Continuous Contract #1
        "CME_BP1" : "LIOR3MUKM",         # British Pound Futures, Continuous Contract #1
        "CME_CD1" : "IR3TIB01CAM156N",   # Canadian Dollar Futures, Continuous Contract #1
        "CME_EC1" : "IR3TIB01EZM156N",   # Euro FX Futures, Continuous Contract #1
        "CME_JY1" : "IR3TIB01JPM156N",   # Japanese Yen Futures, Continuous Contract #1
        "CME_MP1" : "IR3TIB01MXM156N",   # Mexican Peso Futures, Continuous Contract #1
        "CME_NE1" : "IR3TIB01NZM156N",   # New Zealand Dollar Futures, Continuous Contract #1
        "CME_SF1" : "IR3TIB01CHM156N"    # Swiss Franc Futures, Continuous Contract #1
    }
                            
    for symbol in self.symbols:
        data = self.AddData(data_tools.QuantpediaFutures, symbol, Resolution.Daily)
        data.SetFeeModel(data_tools.CustomFeeModel())
        data.SetLeverage(self.leverage)

        # Interbank rate data.
        cash_rate_symbol = self.symbols[symbol]
        self.AddData(data_tools.InterestRate3M, cash_rate_symbol, Resolution.Daily)
    
    self.treasury_rate:Symbol = self.AddData(data_tools.InterestRate3M, 'IR3TIB01USM156N', Resolution.Daily).Symbol
        
def OnData(self, data:Slice) -> None:
    ir_last_update_date:Dict[str, datetime.date] = data_tools.InterestRate3M.get_last_update_date()
    qp_futures_last_update_date:Dict[str, datetime.date] = data_tools.QuantpediaFutures.get_last_update_date()
    
    fd:Dict[str, float] = {}
    for future_symbol, cash_rate_symbol in self.symbols.items():
        if self.Securities[cash_rate_symbol].GetLastData() and ir_last_update_date[cash_rate_symbol] > self.Time.date():
            if cash_rate_symbol in data and data[cash_rate_symbol]:
                if qp_futures_last_update_date[future_symbol] > self.Time.date():
                    cash_rate:float = data[cash_rate_symbol].Value
                    
                    # Update cash rate only once a month.
                    fd[future_symbol] = cash_rate

    if len(fd) == 0:
        if self.Securities[self.treasury_rate].GetLastData() and ir_last_update_date[self.treasury_rate.Value]  afd:
        # Long on the US dollar and goes short on the basket of currencies.
        for symbol in self.symbols:
            if symbol in data and data[symbol]:
                self.SetHoldings(symbol, -1 / count)
    else:
        # Short on the US dollar and long on the basket of currencies.
        for symbol in self.symbols:
            if symbol in data and data[symbol]:
                self.SetHoldings(symbol, 1 / count)
