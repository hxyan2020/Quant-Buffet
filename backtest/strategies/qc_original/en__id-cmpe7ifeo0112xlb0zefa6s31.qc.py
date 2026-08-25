# Original QuantConnect / library Python
# locale=en slug="中国零售股权逆转策略"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

from AlgorithmImports import *
from data_tools import CustomFeeModel, SymbolData, ChineseStocks
# endregion

class RetailEquityReversalInChina(QCAlgorithm):

def Initialize(self):
    self.SetStartDate(2005, 1, 1)
    self.SetCash(100000)
    
    self.perf_quantile:int = 5
    self.price_quantile:int = 10
    
    self.leverage:int = 5

    self.period:int = 21
    self.max_missing_days:int = 5

    self.data:dict[Symbol, SymbolData] = {}
    
    top_size_symbol_count:int = 400
    ticker_file_str:str = self.Download('data.quantpedia.com/backtesting_data/equity/chinese_stocks/large_cap_500.csv')
    tickers:List[str] = ticker_file_str.split('\r\n')[:top_size_symbol_count]

    for t in tickers:
        # price data
        data = self.AddData(ChineseStocks, t, Resolution.Daily)
        data.SetFeeModel(CustomFeeModel())
        data.SetLeverage(self.leverage)

        self.data[data.Symbol] = SymbolData(self.period)
    
    self.recent_month:int = -1
    self.exclusion_flag:bool = False

def OnData(self, data):
    curr_date:datetime.date = self.Time.date()

    for symbol, symbol_data in self.data.items():
        if symbol in data and data[symbol] and data[symbol].Value and data[symbol].GetProperty('price_data'):
            price:float = data[symbol].Value 
            symbol_data.update_prices(price)
            symbol_data.set_last_update(curr_date)

            price_data:dict = data[symbol].GetProperty('price_data')
            if self.exclusion_flag and 'marketValue' in price_data and price_data['marketValue'] != 0:
                market_cap:float = float(price_data['marketValue'])
                symbol_data.set_market_cap(market_cap)

    if self.recent_month == self.Time.month:
        return
    self.recent_month = self.Time.month

    if self.exclusion_flag:
        market_caps:dict[Symbol, float] = { sym: sym_data.get_market_cap() for sym, sym_data in self.data.items() if sym_data.market_cap_ready() }
        sorted_by_cap:list[Symbol] = [x[0] for x in sorted(market_caps.items(), key=lambda item: item[1])]
        # exclude lowest 30%
        active_universe:list[Symbol] = sorted_by_cap[int(len(sorted_by_cap) * 0.3):]
    else:
        active_universe:list[Symbol] = list(self.data.keys())

    performances:dict[Symbol, float] = {}
    prices:dict[Symbol, float] = {}

    for symbol in active_universe:
        symbol_data:SymbolData = self.data[symbol]

        if not symbol_data.data_still_coming(curr_date, self.max_missing_days):
            symbol_data.reset_data()

        if symbol_data.prices_ready():
            performances[symbol] = symbol_data.get_performance(self.period)
            prices[symbol] = symbol_data.get_last_price()

    if len(performances)
