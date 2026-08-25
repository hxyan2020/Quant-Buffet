# Original QuantConnect / library Python
# locale=zh slug="货币因子动量"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

from AlgorithmImports import *
import data_tools
from  typing import List, Dict
class CurrencyFactorMomentum(QCAlgorithm):
def Initialize(self):
    self.SetStartDate(2000, 1, 1)
    self.SetCash(100000)
    
    self.data:Dict[str, SymbolData] = {}
    self.period:int = 21
    self.leverage:int = 5
    self.quantile:int = 5
    
    self.carry_factor_long:List[str] = []
    self.carry_factor_short:List[str] = []
    
    # Cash rate source: https://fred.stlouisfed.org/series/IR3TIB01USM156N
    self.symbols = [
        ("CME_AD1", "IR3TIB01AUM156N"),  # Australian Dollar Futures, Continuous Contract #1
        ("CME_BP1", "LIOR3MUKM"),        # British Pound Futures, Continuous Contract #1
        ("CME_CD1", "IR3TIB01CAM156N"),  # Canadian Dollar Futures, Continuous Contract #1
        ("CME_EC1", "IR3TIB01EZM156N"),  # Euro FX Futures, Continuous Contract #1
        ("CME_JY1", "IR3TIB01JPM156N"),  # Japanese Yen Futures, Continuous Contract #1
        ("CME_MP1", "IR3TIB01MXM156N"),  # Mexican Peso Futures, Continuous Contract #1
        ("CME_NE1", "IR3TIB01NZM156N"),  # New Zealand Dollar Futures, Continuous Contract #1
        ("CME_SF1", "IR3TIB01CHM156N")   # Swiss Franc Futures, Continuous Contract #1
    ]
    
    self.symbol:Symbol = self.AddEquity('SPY', Resolution.Daily).Symbol
    
    for currency_futures, cash_rate_symbol in self.symbols:
        data = self.AddData(data_tools.QuantpediaFutures, currency_futures, Resolution.Daily)
        data.SetFeeModel(data_tools.CustomFeeModel())
        data.SetLeverage(self.leverage)
        
        self.AddData(data_tools.InterestRate3M, cash_rate_symbol, Resolution.Daily)
        
        self.data[currency_futures] = data_tools.SymbolData(self.period)
     
    self.Schedule.On(self.DateRules.MonthStart(self.symbol), self.TimeRules.BeforeMarketClose(self.symbol), self.Rebalance)
def OnData(self, data):
    for symbol_pairs in self.symbols:
        currency_future:str = symbol_pairs[0]
        cash_rate_symbol:str = symbol_pairs[1]
        
        if currency_future in data:
            if data[currency_future]:
                price:float = data[currency_future].Value
                self.data[currency_future].update(price)
        if cash_rate_symbol in data:
            if data[cash_rate_symbol]:
                cash_rate:float = data[cash_rate_symbol].Value
                self.data[currency_future].InterBankRate = cash_rate

def Rebalance(self):
    carry_factor:Dict[str, float] = {}
    dollar_factor:Dict[str, float] = {}
    ir_last_update_date:Dict[str, datetime.date] = data_tools.InterestRate3M.get_last_update_date()
    qp_futures_last_update_date:Dict[str, datetime.date] = data_tools.QuantpediaFutures.get_last_update_date()  
    
    for symbol_pairs in self.symbols:
        currency_future:str = symbol_pairs[0]
        cash_rate_symbol:str = symbol_pairs[1]
        
        # data is still coming
        if self.Securities[currency_future].GetLastData() and qp_futures_last_update_date[currency_future]  0:
        long_carry_factor = True
        
    for symbol in curr_carry_factor_long:
        if long_carry_factor:
            self.SetHoldings(symbol, 1 / len(curr_carry_factor_long) / 2)
        else:
            self.SetHoldings(symbol, -1 / len(curr_carry_factor_long) / 2)
    
    if symbol in curr_carry_factor_short:
        if long_carry_factor:
            self.SetHoldings(symbol, -1 / len(curr_carry_factor_short) / 2)
        else:
            self.SetHoldings(symbol, 1 / len(curr_carry_factor_short) / 2)
    
    # Trade dollar factor
    long_dollar_factor:bool = False
    if dollar_factor_perf > 0:
        long_dollar_factor = True
    
    for symbol, _ in dollar_factor.items():
        if long_dollar_factor:
            self.SetHoldings(symbol, 1 / len(dollar_factor) / 2)
        else:
            self.SetHoldings(symbol, -1 / len(dollar_factor) / 2)

def CarryFactorPerformance(self):
    total_performance:List[float] = []
    
    for symbol in self.carry_factor_long:
        total_performance.append(self.data[symbol].performance())
        
    for symbol in self.carry_factor_short:
        total_performance.append(-self.data[symbol].performance())
        
    return np.mean(total_performance)
