# Original QuantConnect / library Python
# locale=en slug="slope-carry"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

import data_tools
from AlgorithmImports import *
import numpy as np
from typing import List, Dict
from dateutil.relativedelta import relativedelta
class SlopeCarry(QCAlgorithm):
def Initialize(self):
    self.SetStartDate(2000, 1, 1)
    self.SetCash(100000)
    
    # Symbols - 10Y bond futures, 10Y bond yield, cash rate data, GDP data.
    # Cash rate source: https://fred.stlouisfed.org/series/IR3TIB01USM156N
    # 10Y bond yield source: www.investing.com
    self.symbols:List[Tuple[str, str, str, str]] = [
        ("ASX_XT1", 'AU10YT', 'IR3TIB01AUM156N', 'AUS_GDP'),    # 10 Year Commonwealth Treasury Bond Futures, Continuous Contract #1 (Australia)
        ("MX_CGB1", 'CA10YT', 'IR3TIB01CAM156N', 'CAN_GDP'),    # Ten-Year Government of Canada Bond Futures, Continuous Contract #1 (Canada)
        ("EUREX_FGBL1", 'DE10Y', 'IR3TIB01EZM156N', 'DEU_GDP'), # Euro-Bund (10Y) Futures, Continuous Contract #1 (Germany)
        ("LIFFE_R1", 'GB10Y', 'LIOR3MUKM', 'GBR_GDP'),          # Long Gilt Futures, Continuous Contract #1 (U.K.)
        ("SGX_JB1", 'JP10Y', 'IR3TIB01JPM156N', 'JPN_GDP'),     # SGX 10-Year Mini Japanese Government Bond Futures, Continuous Contract #1 (Japan)
        ("CME_TY1", 'US10Y', 'IR3TIB01USM156N', 'USA_GDP')      # 10 Yr Note Futures, Continuous Contract #1 (USA)
    ]
    self.traded_count:int = 1
    self.leverage:int = 3
    
    for bond_future, bond_yield_symbol, cash_rate_symbol, gdp_symbol in self.symbols:
        # Bond future data.
        data = self.AddData(data_tools.QuantpediaFutures, bond_future, Resolution.Daily)
        data.SetFeeModel(data_tools.CustomFeeModel())
        data.SetLeverage(self.leverage)
        
        # Bond yield data.
        self.AddData(data_tools.QuantpediaBondYield, bond_yield_symbol, Resolution.Daily)
        # Interbank rate data.
        self.AddData(data_tools.InterestRate3M, cash_rate_symbol, Resolution.Daily)
        # GDP.
        self.AddData(data_tools.GDPData, gdp_symbol, Resolution.Daily)
    self.Settings.MinimumOrderMarginPortfolioPercentage = 0.
    self.Schedule.On(self.DateRules.MonthStart(self.symbols[0][0]), self.TimeRules.At(0, 0), self.Rebalance)
def Rebalance(self):
    qp_futures_last_update_date:Dict[str, datetime.date] = data_tools.QuantpediaFutures.get_last_update_date()  
    bond_yield_last_update_date:Dict[str, datetime.date] = data_tools.QuantpediaBondYield.get_last_update_date()  
    ir_last_update_date:Dict[str, datetime.date] = data_tools.InterestRate3M.get_last_update_date()
    gdp_last_update_date:Dict[str, datetime.date] = data_tools.GDPData.get_last_update_date()
    # A steep yield curve is a variation of the normal yield curve, possessing the same basic properties; 
    # whereby the interest rates paid on securities with shorter maturities is lower than rates paid on debt with longer maturities.
    yield_curve_slope:Dict[str, float] = { bond_future : (self.Securities[bond_yield_symbol].Price - self.Securities[cash_rate_symbol].Price) for bond_future, bond_yield_symbol, cash_rate_symbol, gdp_symbol in self.symbols  \
                            if self.Securities[bond_future].GetLastData() and self.Securities[bond_yield_symbol].GetLastData() and self.Securities[cash_rate_symbol].GetLastData() and self.Securities[gdp_symbol].GetLastData() \
                                and qp_futures_last_update_date[bond_future] > self.Time.date() and bond_yield_last_update_date[bond_yield_symbol] > self.Time.date() and ir_last_update_date[cash_rate_symbol] > self.Time.date() \
                                and gdp_last_update_date[gdp_symbol] + relativedelta(months=12) > self.Time.date()}
                            
    gdp:Dict[str, float] = { bond_future : self.Securities[gdp_symbol].Price for bond_future, _, _, gdp_symbol in self.symbols if self.Securities.ContainsKey(gdp_symbol)}
    if len(yield_curve_slope) >= self.traded_count * 2:
        sorted_by_slope:List[str] = sorted(yield_curve_slope.items(), key = lambda x: abs(x[1]), reverse = True)
        weight:Dict[str, float] = {}
        
        long:List[str] = [x[0] for x in sorted_by_slope[:self.traded_count]]
        short:List[str] = [x[0] for x in sorted_by_slope[-self.traded_count:]]
        
        # GDP weighting
        total_gdp_long:float = sum([gdp[x] for x in long])
        for symbol in long:
            if total_gdp_long == 0:
                continue
            weight[symbol] = gdp[symbol] / total_gdp_long
        total_gdp_short:float = sum([gdp[x] for x in short])
        for symbol in short:
            if total_gdp_short == 0:
                continue
            weight[symbol] = -gdp[symbol] / total_gdp_short
        # liquidate
        invested:List[str] = [x.Key.Value for x in self.Portfolio if x.Value.Invested]
        for symbol in invested:
            if symbol not in weight:
                self.Liquidate(symbol)
                
        # trade execution
        for symbol, w in weight.items():
            self.SetHoldings(symbol, w)
    else:
        self.Liquidate()
