# Original QuantConnect / library Python
# locale=en slug="skewness-and-52-week-highs-in-china"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

from AlgorithmImports import *
from data_tools import CustomFeeModel, SymbolData, ChineseStocks
# endregion

class SkewnessAnd52WeekHighsInChina(QCAlgorithm):

def Initialize(self):
    self.SetStartDate(2015, 1, 1)
    self.SetCash(100000)
    
    # chinese stock universe
    self.top_size_symbol_count:int = 300
    ticker_file_str:str = self.Download('data.quantpedia.com/backtesting_data/equity/chinese_stocks/large_cap_500.csv')
    self.tickers:List[str] = ticker_file_str.split('\r\n')[:self.top_size_symbol_count]

    self.quantile:int = 10
    self.leverage:int = 5
    self.max_missing_days:int = 5
    self.period:int = 52 * 5                  # daily period
    self.SetWarmUp(self.period, Resolution.Daily)
    
    self.data:dict[str, SymbolData] = {}

    for t in self.tickers:
        data = self.AddData(ChineseStocks, t, Resolution.Daily)
        data.SetFeeModel(CustomFeeModel())
        data.SetLeverage(self.leverage)

        self.data[data.Symbol] = SymbolData(self.period)
    
    self.recent_month:int = -1

def OnData(self, data: Slice):
    curr_date:datetime.date = self.Time.date()

    # store daily data
    for symbol, symbol_data in self.data.items():
        if data.ContainsKey(symbol):
            price_data:dict[str, str] = data[symbol].GetProperty('price_data')
            # valid price data
            if data[symbol].Value != 0. and price_data:
                # update price and market cap
                close:float = float(data[symbol].Value)
                symbol_data.update(curr_date, close)

                mc:float = float(price_data['marketValue'])
                symbol_data.update_market_cap(mc)

    if self.IsWarmingUp: return

    if self.recent_month == self.Time.month:
        return
    self.recent_month = self.Time.month

    W52:dict[Symbol, float] = {}
    SKEWNESS:dict[Symbol, float] = {}

    for symbol, symbol_data in self.data.items():
        if not symbol_data.data_still_coming(curr_date, self.max_missing_days):
            symbol_data.reset_data()
            continue

        if symbol_data.is_ready():
            W52[symbol] = symbol_data.get_W52_value()
            SKEWNESS[symbol] = symbol_data.get_SKEWNESS_value()

        symbol_data.reset_monthly_closes()

    if len(W52)
