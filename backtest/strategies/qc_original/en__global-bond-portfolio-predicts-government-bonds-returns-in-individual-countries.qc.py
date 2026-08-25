# Original QuantConnect / library Python
# locale=en slug="global-bond-portfolio-predicts-government-bonds-returns-in-individual-countries"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

import data_tools
from AlgorithmImports import *
import numpy as np
from typing import List, Dict, Tuple
class GlobalBondPortfolioPredictsGovernmentBondsReturnsinIndividualCountries(QCAlgorithm):
def Initialize(self):
    self.SetStartDate(2000, 1, 1)
    self.SetCash(100000)
    
    self.leverage:int = 5
    # Symbols - 10Y bond futures, 10Y bond yield, cash rate data.
    # Cash rate source: https://fred.stlouisfed.org/series/IR3TIB01USM156N
    # 10Y bond yield source: www.investing.com
    self.symbols:List[Tuple[str]] = [
        ("ASX_XT1", 'AU10YT', 'IR3TIB01AUM156N'),    # 10 Year Commonwealth Treasury Bond Futures, Continuous Contract #1 (Australia)
        ("MX_CGB1", 'CA10YT', 'IR3TIB01CAM156N'),    # Ten-Year Government of Canada Bond Futures, Continuous Contract #1 (Canada)
        ("EUREX_FGBL1", 'DE10Y', 'IR3TIB01EZM156N'), # Euro-Bund (10Y) Futures, Continuous Contract #1 (Germany)
        ("LIFFE_R1", 'GB10Y', 'LIOR3MUKM'),          # Long Gilt Futures, Continuous Contract #1 (U.K.)
        ("SGX_JB1", 'JP10Y', 'IR3TIB01JPM156N'),     # SGX 10-Year Mini Japanese Government Bond Futures, Continuous Contract #1 (Japan)
        ("CME_TY1", 'US10Y', 'IR3TIB01USM156N')      # 10 Yr Note Futures, Continuous Contract #1 (USA)
    ]
                
    for bond_future,  bond_yield_symbol, cash_rate_symbol in self.symbols:
        # Bond future data.
        data = self.AddData(data_tools.QuantpediaFutures, bond_future, Resolution.Daily)
        data.SetFeeModel(data_tools.CustomFeeModel())
        data.SetLeverage(self.leverage)
        
        # Bond yield data.
        self.AddData(data_tools.QuantpediaBondYield, bond_yield_symbol, Resolution.Daily)
        # Interbank rate data.
        self.AddData(data_tools.InterestRate3M, cash_rate_symbol, Resolution.Daily)
    self.settings.daily_precise_end_time = False
    self.settings.minimum_order_margin_portfolio_percentage = 0.
    self.Schedule.On(self.DateRules.MonthStart(self.symbols[0][0]), self.TimeRules.At(0, 0), self.Rebalance)
    
def Rebalance(self):
    qp_futures_last_update_date:Dict[str, datetime.date] = data_tools.QuantpediaFutures.get_last_update_date()  
    bond_yield_last_update_date:Dict[str, datetime.date] = data_tools.QuantpediaBondYield.get_last_update_date()  
    ir_last_update_date:Dict[str, datetime.date] = data_tools.InterestRate3M.get_last_update_date()
    excess_bond_return:Dict[str, float] = { bond_future : (self.Securities[bond_yield_symbol].Price - self.Securities[cash_rate_symbol].Price) for bond_future, bond_yield_symbol, cash_rate_symbol in self.symbols  \
                            if self.Securities[bond_future].GetLastData() and self.Securities[bond_yield_symbol].GetLastData() and self.Securities[cash_rate_symbol].GetLastData() \
                                and qp_futures_last_update_date[bond_future] > self.Time.date() and bond_yield_last_update_date[bond_yield_symbol] > self.Time.date() and ir_last_update_date[cash_rate_symbol] > self.Time.date()}
    
    avg_excess_bond_return:float = np.average([x[1] for x in excess_bond_return.items()])
    if avg_excess_bond_return > 0:
        long_count:int = len(excess_bond_return)
        
        for symbol, excess_return in excess_bond_return.items():
            self.SetHoldings(symbol, 1 / long_count)
    else:
        self.Liquidate()
