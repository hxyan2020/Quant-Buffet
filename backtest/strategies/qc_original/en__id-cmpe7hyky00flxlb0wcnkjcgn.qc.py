# Original QuantConnect / library Python
# locale=en slug="基于相对情绪的市场时机策略"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

from AlgorithmImports import *
import numpy as np
import data_tools
from typing import Dict, List
import pandas as pd
from  pandas.core.series import Series as series
#endregion

class MarketTimingwithRelativeSentiment(QCAlgorithm):

def Initialize(self):
    self.SetStartDate(2000, 1, 1)
    self.SetCash(100000)
   
    self.cot_symbols:List[str] = [
        'QEP', # S&P 500
        'QTY', # 10 Yr Note Futures
        'QUS'  # 30 Yr Note Futures
    ]

    self.SetTimeZone(TimeZones.NewYork)

    self.max_missing_days:int = 7
    self.missing_days:int = 0

    self.market:Symbol = self.AddEquity('SPY', Resolution.Daily).Symbol
    self.N:int = 78 # lookback period
    self.M:int = 5  # extrema lookback

    self.symbol_data:Dict[str, data_tools.SymbolData] = {}
    for cot_symbol in self.cot_symbols:
        # COT data
        self.AddData(data_tools.CommitmentsOfTraders, cot_symbol, Resolution.Daily)

        self.symbol_data[cot_symbol] = data_tools.SymbolData(self.N)

def OnData(self, data:Slice) -> None:
    rebalance_flag:bool = False

    # store most recent open interest for every symbol - weekly data
    if all((cot_symbol in data and data[cot_symbol]) for cot_symbol in self.cot_symbols):
        for cot_symbol in self.cot_symbols:
            inst_long_count:float = data[cot_symbol].GetProperty("COMMERCIAL_HEDGER_LONG")
            inst_short_count:float = data[cot_symbol].GetProperty("COMMERCIAL_HEDGER_SHORT")
            indiv_long_count:float = data[cot_symbol].GetProperty("SMALL_TRADER_LONG")
            indiv_short_count:float = data[cot_symbol].GetProperty("SMALL_TRADER_SHORT")
            oi:float = data[cot_symbol].GetProperty("open_interest")

            delta_cm:float = (inst_long_count + inst_short_count) / oi
            delta_nr:float = (indiv_long_count + indiv_short_count) / oi

            self.symbol_data[cot_symbol].update(delta_cm, delta_nr)
            rebalance_flag = True
    else:
        self.missing_days += 1

    # rebalance once a week
    if rebalance_flag:
        self.missing_days = 0
        
        if all(self.symbol_data[cot_symbol].is_ready() for cot_symbol in self.cot_symbols):
            a = self.symbol_data[self.cot_symbols[0]].z_score()
            z_sp:series = pd.Series(self.symbol_data[self.cot_symbols[0]].z_score()[::-1])
            z_ty:series = pd.Series(self.symbol_data[self.cot_symbols[1]].z_score()[::-1])
            z_us:series = pd.Series(self.symbol_data[self.cot_symbols[2]].z_score()[::-1])

            z_sp_max:np.ndarray = z_sp.rolling(self.M).max().values
            z_ty_max:np.ndarray = z_ty.rolling(self.M).max().values
            z_us_max:np.ndarray = z_us.rolling(self.M).max().values
            z_us_min:np.ndarray = z_us.rolling(self.M).min().values

            z_smi:np.ndarray = z_sp_max - z_us_min + (z_ty_max - z_us_max)
            smi_index_value:float = z_smi[-1]
            
            if smi_index_value > 0.:
                # investor goes long SPY on the day when the prior-week SMI is positive
                self.SetHoldings(self.market, 1.)
            else:
                # and is flat (staying in cash) otherwise
                self.Liquidate(self.market)
        else:
            self.Liquidate(self.market)
    else:
        if self.missing_days == self.max_missing_days:
            # log messages
            for cot_symbol in self.cot_symbols:
                self.symbol_data[cot_symbol].reset()

                missing_days:int = int((self.Time.date() - self.Securities[cot_symbol].GetLastData().Time.date()).days)
                self.Log(f'{cot_symbol} COT data missing days: {missing_days} on {self.Time.date()}')

            self.Liquidate(self.market)
            self.missing_days = 0
