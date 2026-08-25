# Original QuantConnect / library Python
# locale=zh slug="货币中的曲率因子"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

import data_tools
from typing import List, Dict
from AlgorithmImports import *
class CurvatureFactorInCurrencies(QCAlgorithm):
def Initialize(self):
    self.SetStartDate(2000, 1, 1)
    self.SetCash(100000)
    self.data:Dict[Symbol, SymbolData] = {}
    self.period:int = 21
    self.number_of_currencies:int = 3
    self.leverage:int = 5
    # Symbols - Currency futures, 10Y bond yield, 5Y bond yield, cash rate data.
    # Cash rate source: https://www.quandl.com/data/OECD-Organisation-for-Economic-Co-operation-and-Development
    self.symbols:List[str] = [
                    ('CME_AD1', 'AU10YT', 'AU5YT', 'IR3TIB01AUM156N'), # Australian Dollar Futures, Continuous Contract #1
                    ('CME_CD1', 'CA10YT', 'CA5YT', 'IR3TIB01CAM156N'), # Canadian Dollar Futures, Continuous Contract #1
                    ('CME_SF1', 'CH10YT', 'CH5YT', 'IR3TIB01CHM156N'), # Swiss Franc Futures, Continuous Contract #1
                    ('CME_EC1', 'DE10YT', 'DE5YT', 'IR3TIB01EZM156N'), # Euro FX Futures, Continuous Contract #1
                    ('CME_BP1', 'GB10YT', 'GB5YT', 'LIOR3MUKM'),       # British Pound Futures, Continuous Contract #1
                    ('CME_JY1', 'JP10YT', 'JP5YT', 'IR3TIB01JPM156N'), # Japanese Yen Futures, Continuous Contract #1
                    ('CME_NE1', 'NZ10YT', 'NZ5YT', 'IR3TIB01NZM156N'), # New Zealand Dollar Futures, Continuous Contract #1
                    ('CME_MP1', 'MX10YT', 'MX5YT', 'IR3TIB01MXM156N')  # Mexican Peso Futures, Continuous Contract #1
                    ]
                    
    for currency_future, bond_yield_symbol_10, bond_yield_symbol_5, cash_rate_symbol in self.symbols:
        # Currency futures data.
        data = self.AddData(data_tools.QuantpediaFutures, currency_future, Resolution.Daily)
        data.SetFeeModel(data_tools.CustomFeeModel())
        data.SetLeverage(self.leverage)
        
        # Bond yield data.
        self.AddData(data_tools.QuantpediaBondYield, bond_yield_symbol_10, Resolution.Daily)
        self.AddData(data_tools.QuantpediaBondYield, bond_yield_symbol_5, Resolution.Daily)
        
        # Interbank rate data.
        self.AddData(data_tools.InterestRate3M, cash_rate_symbol, Resolution.Daily)
        
    for symbol_tuple in self.symbols:
        self.data[symbol_tuple[0]] = data_tools.SymbolData(1) # Need to check data for trading  
        for symbol in symbol_tuple[1:]:
            self.data[symbol] = data_tools.SymbolData(self.period)
    
    self.Settings.MinimumOrderMarginPortfolioPercentage = 0.
    self.current_month:int = -1
def OnData(self, data:Slice) -> None:
    for symbol_tuple in self.symbols:
        for symbol in symbol_tuple:
            if symbol in data and data[symbol]:
                price:float = data[symbol].Value
                self.data[symbol].update(price)
    if self.Time.month == self.current_month:
        return
    self.current_month = self.Time.month
    ir_last_update_date:Dict[str, datetime.date] = data_tools.InterestRate3M.get_last_update_date()
    qp_futures_last_update_date:Dict[str, datetime.date] = data_tools.QuantpediaFutures.get_last_update_date()
    bond_last_update_date:Dict[str, datetime.date] = data_tools.QuantpediaBondYield.get_last_update_date()
    curvature = {}
    for currency_future, bond_yield_symbol_10, bond_yield_symbol_5, cash_rate_symbol in self.symbols:
        # check if data is still coming
        if (self.Securities[currency_future].GetLastData() and qp_futures_last_update_date[currency_future] > self.Time.date()) \
            and (self.Securities[cash_rate_symbol].GetLastData() and ir_last_update_date[cash_rate_symbol] > self.Time.date()) \
            and (self.Securities[bond_yield_symbol_10].GetLastData() and bond_last_update_date[bond_yield_symbol_10] > self.Time.date()) \
            and (self.Securities[bond_yield_symbol_5].GetLastData() and bond_last_update_date[bond_yield_symbol_5] > self.Time.date()):
            if self.data[currency_future].is_ready() and self.data[bond_yield_symbol_10].is_ready() \
                and self.data[bond_yield_symbol_5].is_ready() and self.data[cash_rate_symbol].is_ready():
                # curvature = (5y - 3m) - (10y - 5y)  
                first_bracket:float = self.data[bond_yield_symbol_5].performance() - self.data[cash_rate_symbol].performance()
                second_bracket:float = self.data[bond_yield_symbol_10].performance() - self.data[bond_yield_symbol_5].performance()
                curvature[currency_future] = first_bracket - second_bracket
    
    long:List[Symbol] = []
    short:List[Symbol] = []
    if len(curvature) >= self.number_of_currencies * 2:
        sorted_by_curvature:List[Symbol] = [x[0] for x in sorted(curvature.items(), key=lambda item: item[1], reverse=True)]
        long = sorted_by_curvature[:self.number_of_currencies]
        short = sorted_by_curvature[-self.number_of_currencies:]
    currencies_invested:List[Symbol] = [x.Key for x in self.Portfolio if x.Value.Invested]
    for symbol in currencies_invested:
        if symbol not in long + short: 
            self.Liquidate(symbol)
            
    for symbol in long:
        if symbol in data and data[symbol]:
            self.SetHoldings(symbol, 1 / len(long))
        
    for symbol in short:
        if symbol in data and data[symbol]:
            self.SetHoldings(symbol, -1 / len(short))
