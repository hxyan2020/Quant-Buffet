# Original QuantConnect / library Python
# locale=zh slug="用综合模型预测债券回报"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

import data_tools
from AlgorithmImports import *
import numpy as np
from typing import List, Dict, Tuple, Deque
from collections import deque
class PredictingBondReturnswithaCombinedModel(QCAlgorithm):
def Initialize(self):
    self.SetStartDate(2000, 1, 1)
    self.SetCash(100000)
    
    # Symbols - 10Y bond futures, equity etf, 10Y bond yield, cash rate data.
    # Cash rate source: https://fred.stlouisfed.org/series/IR3TIB01USM156N
    self.symbols:List[Tuple[str]] = [
        ("ASX_XT1", 'EWA', 'AU10YT', 'IR3TIB01AUM156N'),      # 10 Year Commonwealth Treasury Bond Futures, Continuous Contract #1 (Australia)
        ("MX_CGB1", 'EWC', 'CA10YT', 'IR3TIB01CAM156N'),      # Ten-Year Government of Canada Bond Futures, Continuous Contract #1 (Canada)
        ("EUREX_FGBL1", 'EWG', 'DE10Y', 'IR3TIB01EZM156N'),   # Euro-Bund (10Y) Futures, Continuous Contract #1 (Germany)
        ("LIFFE_R1", 'EWU', 'GB10Y', 'LIOR3MUKM'),            # Long Gilt Futures, Continuous Contract #1 (U.K.)
        ("SGX_JB1", 'EWJ', 'JP10Y', 'IR3TIB01JPM156N'),       # SGX 10-Year Mini Japanese Government Bond Futures, Continuous Contract #1 (Japan)
        ("CME_TY1", 'SPY', 'US10Y', 'IR3TIB01USM156N')        # 10 Yr Note Futures, Continuous Contract #1 (USA)
    ]
                
    # Daily price data.
    self.data:Dict[Symbol, SymbolData] = {}
   
    self.month_period:int = 10
    self.future_period:int = 13
    self.period:int = self.month_period * 12 + 1
    self.SetWarmUp(self.period * 21)
    self.leverage:int = 5
    
    # Daily spread data. (10y yield minus cash rate)
    self.spread:Dict[Symbol, Deque[float]] = {}
    
    self.commodity_index:str = 'DBC'
    self.AddEquity(self.commodity_index, Resolution.Daily)
    self.data[self.commodity_index] = deque(maxlen = self.period)
    
    for bond_future, equity_etf, bond_yield_symbol, cash_rate_symbol in self.symbols:
        # Bond future data.
        data = self.AddData(data_tools.QuantpediaFutures, bond_future, Resolution.Daily)
        self.data[bond_future] = deque(maxlen = self.future_period)
        data.SetFeeModel(data_tools.CustomFeeModel())
        data.SetLeverage(self.leverage)
        
        # Equity data.
        self.AddEquity(equity_etf, Resolution.Daily)
        self.data[equity_etf] = deque(maxlen = self.period)
        
        # Bond yield data.
        self.AddData(data_tools.QuantpediaBondYield, bond_yield_symbol, Resolution.Daily)
        # Interbank rate data.
        self.AddData(data_tools.InterestRate3M, cash_rate_symbol, Resolution.Daily)
        # Steepness of the yield curve.
        self.spread[bond_yield_symbol] = deque(maxlen = self.period)
    
    self.Settings.MinimumOrderMarginPortfolioPercentage = 0.
    self.last_month:int = -1
    self.Schedule.On(self.DateRules.MonthStart(self.commodity_index), self.TimeRules.AfterMarketOpen(self.commodity_index), self.Rebalance)
    self.settings.daily_precise_end_time = False
def OnData(self, data):
    # Update only on new month start.
    if self.Time.month == self.last_month:
        return
    self.last_month = self.Time.month      
    
    # Store monthly data.
    for bond_future, equity_etf, bond_yield_symbol, cash_rate_symbol in self.symbols:
        if bond_future in data and data[bond_future]:
            price:float = data[bond_future].Value
            self.data[bond_future].append(price)
        
        if equity_etf in data and data[equity_etf]:
            price:float = data[equity_etf].Value
            self.data[equity_etf].append(price)
        if bond_yield_symbol in data and data[bond_yield_symbol] and cash_rate_symbol in data and data[cash_rate_symbol]:
            bond_yield:float = data[bond_yield_symbol].Value
            cash_rate:float = data[cash_rate_symbol].Value
            steepness:float = bond_yield - cash_rate
            self.spread[bond_yield_symbol].append(steepness)
    
    # Store commodity index price.
    if self.commodity_index in data and data[self.commodity_index]:
        price:float = data[self.commodity_index].Value
        self.data[self.commodity_index].append(price)
    
def Rebalance(self):
    ir_last_update_date:Dict[str, datetime.date] = data_tools.InterestRate3M.get_last_update_date()
    qp_futures_last_update_date:Dict[str, datetime.date] = data_tools.QuantpediaFutures.get_last_update_date()  
    
    # Z score calc.
    weight:Dict[Symbol, float] = {}
    
    commodity_index_z_score:None|float = None
    # Past commodities returns for which only sign is used.
    minimum_data_count:float = ((self.period-1) / self.month_period) * 3
    if len(self.data[self.commodity_index]) >= minimum_data_count:
        closes:List[float] = [x for x in self.data[self.commodity_index]]
        separete_yearly_returns:List[float] = [data_tools.Return(closes[x:x+13]) for x in range(0, len(closes),1)]
        
        return_mean:float = np.mean(separete_yearly_returns)
        return_std:float = np.std(separete_yearly_returns)
        commodity_index_z_score:float = (separete_yearly_returns[-1] - return_mean) / return_std            
    else:
        return
    for bond_future, equity_etf, bond_yield_symbol, cash_rate_symbol in self.symbols:
        # data is still coming
        if self.Securities[bond_future].GetLastData() and qp_futures_last_update_date[bond_future]  0 else -1
            z_scores.append(bond_future_z_score)
        else:
            continue
        
        data_queues = [self.data[equity_etf], self.spread[bond_yield_symbol]]
        for queue in data_queues:
            if len(queue) >= minimum_data_count:
                closes:List[float] = [x for x in queue]
                separete_yearly_returns:List[float] = [data_tools.Return(closes[x:x+13]) for x in range(0, len(closes),1)]
                return_mean:float = np.mean(separete_yearly_returns)
                return_std:float = np.std(separete_yearly_returns)
                z_score:float = (separete_yearly_returns[-1] - return_mean) / return_std
                
                z_scores.append(z_score)
        
        z_scores.append(commodity_index_z_score)
        
        if len(z_scores) == 4:
            final_z_score:float = np.mean(z_scores)
            if final_z_score > 1: final_z_score = 1
            elif final_z_score
