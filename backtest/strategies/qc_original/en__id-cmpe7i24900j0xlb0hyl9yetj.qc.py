# Original QuantConnect / library Python
# locale=en slug="大宗商品市场中的高价比因子策略"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

from AlgorithmImports import *
from functools import reduce
from data_tools import CustomFeeModel, QuantpediaFutures, SymbolData
# endregion
class HighToPriceFactorInCommodities(QCAlgorithm):
def Initialize(self):
    self.SetStartDate(2000, 1, 1)
    self.SetCash(100000)
    self.leverage:int = 5
    self.quantile:int = 3
    self.month_period:int = 21
    self.period:int = self.month_period * 12
    self.total_months_in_year:int = 12
    self.max_missing_days:int = 5
    self.min_prices:int = 15
    self.recent_month:int = -1
    self.data:dict[Symbol, SymbolData] = {}
    tickers:list[str] = [
        "CME_S1",   # Soybean Futures, Continuous Contract #1
        "CME_W1",   # Wheat Futures, Continuous Contract #1
        "CME_SM1",  # Soybean Meal Futures, Continuous Contract #1
        "CME_BO1",  # Soybean Oil Futures, Continuous Contract #1
        "CME_C1",   # Corn Futures, Continuous Contract #1
        "CME_O1",   # Oats Futures, Continuous Contract #1
        "CME_LC1",  # Live Cattle Futures, Continuous Contract #1
        "CME_FC1",  # Feeder Cattle Futures, Continuous Contract #1
        "CME_LN1",  # Lean Hog Futures, Continuous Contract #1
        "CME_GC1",  # Gold Futures, Continuous Contract #1
        "CME_SI1",  # Silver Futures, Continuous Contract #1
        "CME_PL1",  # Platinum Futures, Continuous Contract #1
        "CME_CL1",  # Crude Oil Futures, Continuous Contract #1
        "CME_HG1",  # Copper Futures, Continuous Contract #1
        "CME_LB1",  # Random Length Lumber Futures, Continuous Contract #1
        "CME_NG1",  # Natural Gas (Henry Hub) Physical Futures, Continuous Contract #1
        "CME_PA1",  # Palladium Futures, Continuous Contract  #1
        "CME_RR1",  # Rough Rice Futures, Continuous Contract #1
        "CME_CU1",  # Chicago Ethanol (Platts) Futures
        "CME_DA1",  # Class III Milk Futures
        
        "ICE_CC1",  # Cocoa Futures, Continuous Contract  #1
        "ICE_CT1",  # Cotton No. 2 Futures, Continuous Contract #1
        "ICE_KC1",  # Coffee C Futures, Continuous Contract #1
        "ICE_O1",   # Heating Oil Futures, Continuous Contract #1
        "ICE_OJ1",  # Orange Juice Futures, Continuous Contract #1
        "ICE_SB1"   # Sugar No. 11 Futures, Continuous Contract #1
    ]
    for ticker in tickers:
        security = self.AddData(QuantpediaFutures, ticker, Resolution.Daily)
        security.SetFeeModel(CustomFeeModel())
        security.SetLeverage(self.leverage)
        symbol:Symbol = security.Symbol
        self.data[symbol] = SymbolData(self.period)
    self.SetWarmup(self.period)
def OnData(self, data: Slice):
    curr_date:datetime.date = self.Time.date()
    for symbol, symbol_data in self.data.items():
        if symbol in data and data[symbol] and data[symbol].Value != 0:
            price:float = data[symbol].Value
            symbol_data.update_monthly_prices(price)
            symbol_data.set_last_update_date(curr_date)
    if self.recent_month == self.Time.month:
        return
    self.recent_month = self.Time.month
    htp:dict[Symbol, float] = {}
    for symbol, symbol_data in self.data.items():
        if not symbol_data.monthly_prices_ready(self.min_prices) or \
             not symbol_data.data_still_coming(curr_date, self.max_missing_days):
            symbol_data.reset_data()
        else:
            symbol_data.update_prices(self.total_months_in_year)
        if symbol_data.is_ready(self.total_months_in_year):
            prices_in_months:list[list[float]] = symbol_data.get_prices_in_months()
            prices_in_months = prices_in_months[:-1] # ommit last month
            prices:list[float] = list(reduce(lambda x,y: x+y, prices_in_months))
            highest_price:float = max(prices)
            first_price:float = prices[0]
            htp_value:float = np.log(highest_price / first_price)
            htp[symbol] = htp_value
        symbol_data.reset_monthly_prices()
    if self.IsWarmingUp or len(htp)
