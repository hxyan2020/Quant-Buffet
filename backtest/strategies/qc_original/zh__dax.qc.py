# Original QuantConnect / library Python
# locale=zh slug="预测德国dax家族指数变化"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

from AlgorithmImports import *
from data_tools import GermanStocks, CustomFeeModel, SymbolData
import bz2
import pickle
import base64
# endregion
class ForecastingIndexChangesInTheGermanDAXFamily(QCAlgorithm):
def Initialize(self):
    self.SetStartDate(2000, 1, 1)
    self.SetCash(100000)
    self.leverage:int = 5
    self.total_DAX_stocks:int = 30  # number of DAX constituents up until 03/09/2021
    self.prev_DAX_stocks:list[Symbol] = []
    self.change_date:datetime.date = datetime(2021, 9, 3).date()    # date when DAX includes 40 stocks instead of 30
    self.rebalance_day:int = 5      # nth day in month
    self.rebalance_flag:bool = False
    self.trading_days_counter:int = 0
    self.rebalance_months:list[int] = [12, 3, 6, 9] # DAX rebalance months
    self.data:dict[str, SymbolData] = {}
    self.top_size_symbol_count:int = 437 # max number of german stocks is 437
    # Source: https://www.xetra.com/xetra-en/instruments/shares/list-of-tradable-shares/xetra/4750!search?state=H4sIAAAAAAAAADWKsQoCMRAFf0W2TqFtPsDKIuBhH5IXDawJ7m6Q47h_9xDSzTCzUY6Gq_Q3-TaY3d-XPq3EBFPy235wFbUbzCAzv6ppgIT4BPnL2VFtiUfGvRp0Tr3xGnIhXyIrHH0GZCVP5Eigg-1R8Z2zdrGj6VKNcYqaaP8BsKzzjqQAAAA&sort=sTitle+asc&hitsPerPage=10&pageNum=1
    tickers_file_str:str = self.Download('data.quantpedia.com/backtesting_data/equity/german_stocks/german_tickers.csv')
    self.tickers:List[str] = tickers_file_str.split('\r\n')[:self.top_size_symbol_count]
    basic_shares_file_str:str = self.Download('data.quantpedia.com/backtesting_data/economic/average_basic_shares/german_average_basic_shares.json')
    basic_shares_data:dict = json.loads(basic_shares_file_str)
    for index, data in enumerate(basic_shares_data):
        year = datetime.strptime(data['date'], '%d.%m.%Y').year
        for key, value in data.items():
            if key not in self.tickers:
                continue
            if key not in self.data:
                data = self.AddData(GermanStocks, key, Resolution.Daily)
                data.SetFeeModel(CustomFeeModel())
                data.SetLeverage(self.leverage)
                self.data[key] = SymbolData(data.Symbol)
            
            self.data[key].update_basic_shares(year, value)
def OnData(self, data: Slice):
    if self.Portfolio.Invested:
        # liquidate on next trading day
        self.Liquidate()
        return
    if self.Time.month not in self.rebalance_months:
        self.rebalance_flag = True
        return
    
    if self.rebalance_flag:
        self.trading_days_counter += 1
        if self.trading_days_counter >= self.rebalance_day:
            if self.Time.date() > self.change_date:
                self.total_DAX_stocks = 40
            # forbid rebalance until next rebalance month
            self.rebalance_flag = False
            self.trading_days_counter = 0
            market_cap:dict[Symbol, float] = {}
            for ticker, symbol_data in self.data.items():
                symbol:Symbol = symbol_data.symbol
                if not data.ContainsKey(symbol) or data[symbol].Value == 0:
                    continue
                price:float = data[symbol].Value
                basic_shares:int = float(symbol_data.get_basic_share(self.Time.year))
                market_cap_value:float = price * basic_shares
                market_cap[symbol_data.symbol] = market_cap_value
            if len(market_cap) == 0:
                self.Liquidate()
                return
            sorted_by_cap:list[Symbol] = [x[0] for x in sorted(market_cap.items(), key=lambda item: item[1])]
            top_n_symbols:list[Symbol] = sorted_by_cap[-self.total_DAX_stocks:]
            if len(self.prev_DAX_stocks) != self.total_DAX_stocks:
                self.prev_DAX_stocks = top_n_symbols
                self.Liquidate()
                return
            long_leg:list[Symbol] = list(filter(lambda symbol: symbol not in self.prev_DAX_stocks, top_n_symbols))
            short_leg:list[Symbol] = [] #list(filter(lambda symbol: symbol not in top_n_symbols, self.prev_DAX_stocks))
            long_length:int = len(long_leg)
            short_length:int = len(short_leg)
            for symbol in long_leg:
                self.SetHoldings(symbol, 1 / long_length)
            for symbol in short_leg:
                self.SetHoldings(symbol, -1 / short_length)
            self.prev_DAX_stocks = top_n_symbols
