# Original QuantConnect / library Python
# locale=en slug="a-multi-strategy-approach-to-trading-foreign-exchange-futures"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

from AlgorithmImports import *
import numpy as np
from typing import List, Dict, Tuple
from scipy import stats
class AMultiStrategyApproachtoTradingForeignExchangeFutures(QCAlgorithm):
def Initialize(self):
    self.SetStartDate(2000, 1, 1)
    self.SetCash(100000)
    
    # Symbols - Currency future, equity future, 10Y bond yield, cash rate data.
    # Cash rate source: https://www.quandl.com/data/OECD-Organisation-for-Economic-Co-operation-and-Development
    # 10Y bond yield source: www.investing.com
    self.symbols:List[Tuple[str, str, str, str]] = [
        ('CME_AD1', 'ASX_YAP1', 'AU10YT', 'IR3TIB01AUM156N'),    # Australian Dollar Futures, Continuous Contract #1
        ('CME_CD1', 'LIFFE_FCE1', 'CA10YT', 'IR3TIB01CAM156N'),  # Canadian Dollar Futures, Continuous Contract #1
        ('CME_SF1', 'EUREX_FSMI1', 'CH10YT', 'IR3TIB01CHM156N'), # Swiss Franc Futures, Continuous Contract #1
        ('CME_EC1', 'EUREX_FSTX1', 'DE10YT', 'IR3TIB01EZM156N'), # Euro FX Futures, Continuous Contract #1
        ('CME_BP1', 'LIFFE_Z1', 'GB10YT', 'LIOR3MUKM'),          # British Pound Futures, Continuous Contract #1
        ('CME_JY1', 'SGX_NK1', 'JP10YT', 'IR3TIB01JPM156N'),     # Japanese Yen Futures, Continuous Contract #1
    ]
                
    # Symbol data.
    self.data:Dict[Symbol, SymbolData] = {}
    self.short_period:int = 3
    self.long_period:int = 12
    self.leverage:int = 20
    
    # Target risk of the allocation.
    self.target_risk:float = 0.1
    
    for currency_future, equity_future, bond_yield_symbol, cash_rate_symbol in self.symbols:
        # Currency future data.
        data = self.AddData(data_tools.QuantpediaFutures, currency_future, Resolution.Daily)
        data.SetFeeModel(data_tools.CustomFeeModel())
        data.SetLeverage(self.leverage)
        self.data[currency_future] = data_tools.SymbolData(currency_future, self, self.short_period*21, self.long_period*21, True)
        
        # Equity future data.
        self.AddData(data_tools.QuantpediaFutures, equity_future, Resolution.Daily)
        self.data[equity_future] = data_tools.SymbolData(equity_future, self, self.short_period*21, self.long_period*21, False)
        
        # Bond yield data.
        self.AddData(data_tools.QuantpediaBondYield, bond_yield_symbol, Resolution.Daily)
        # Interbank rate data.
        self.AddData(data_tools.InterestRate3M, cash_rate_symbol, Resolution.Daily)
    
    self.usa_10Y_yield:str = 'US10Y'
    self.usa_cash_rate:str = 'IR3TIB01USM156N'
    self.AddData(data_tools.QuantpediaBondYield, self.usa_10Y_yield, Resolution.Daily)
    self.AddData(data_tools.InterestRate3M, self.usa_cash_rate, Resolution.Daily)
    self.commodity_index:Symbol = self.AddEquity('DBC', Resolution.Daily).Symbol
    self.data[self.commodity_index] = data_tools.SymbolData(self.commodity_index, self, self.short_period*21, self.long_period*21, False)
    
    self.last_month:int = -1
    
def OnData(self, data:Slice) -> None:
    # Rebalance once a month.
    if self.last_month != self.Time.month:
        self.last_month = self.Time.month
        ir_last_update_date:Dict[str, datetime.date] = data_tools.InterestRate3M.get_last_update_date()
        qp_futures_last_update_date:Dict[str, datetime.date] = data_tools.QuantpediaFutures.get_last_update_date()
        
        # Create indicators.
        weight:Dict[Symbol, float] = {}
        for currency_future, equity_future, bond_yield_symbol, cash_rate_symbol in self.symbols:
            # data is still coming
            if self.Securities[currency_future].GetLastData() and qp_futures_last_update_date[currency_future]
