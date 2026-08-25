# Original QuantConnect / library Python
# locale=en slug="daily-momentum-in-chinese-equities"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

from AlgorithmImports import *
from typing import Dict, List
import data_tools
# endregion

class DailyMomentuminChineseEquities(QCAlgorithm):

def Initialize(self):
    self.SetStartDate(2015, 1, 1)   # Chinese data starts in 2015
    self.SetCash(100000)

    self.leverage:int = 5
    self.quantile:int = 10
    self.period:int = 2 + 1

    self.data:Dict[Symbol, SymbolData] = {}

    self.top_size_symbol_count:int = 300
    ticker_file_str:str = self.Download('data.quantpedia.com/backtesting_data/equity/chinese_stocks/large_cap_500.csv')
    tickers:List[str] = ticker_file_str.split('\r\n')[:self.top_size_symbol_count]

    for t in tickers:
        data = self.AddData(data_tools.ChineseStocks, t, Resolution.Daily)
        data.SetFeeModel(data_tools.CustomFeeModel())
        data.SetLeverage(self.leverage)

        stock_symbol:Symbol = data.Symbol

        self.data[stock_symbol] = data_tools.SymbolData(data.Symbol, self.period)

    self.Settings.MinimumOrderMarginPortfolioPercentage = 0.

def OnData(self, data: Slice) -> None:
    price_last_update_date:Dict[Symbol, datetime.date] = data_tools.ChineseStocks.get_last_update_date()
    asset_returns:Dict[Symbol, float] = {}

    # store daily data
    for symbol, symbol_data in self.data.items():
        if symbol in data and data[symbol]:
            price_data:dict[str, str] = data[symbol].GetProperty('price_data')
            # valid price data
            if data[symbol].Value != 0 and price_data:
                close_price:float = data[symbol].Value
                symbol_data.update_price(close_price)

                mc:float = float(price_data['marketValue'])
                symbol_data.update_market_cap(mc)
        
        # calculate momentum
        if symbol_data.is_ready() and self.Time.date() = self.quantile:
        sorted_stocks:List[Symbol] = sorted(asset_returns, key=asset_returns.get , reverse=True)
        quantile:int = int(len(sorted_stocks) / self.quantile)
        long:List[Symbol] = sorted_stocks[:quantile]
        short:List[Symbol] = sorted_stocks[-quantile:]

        # calculate weights based on market cap
        for i, portfolio in enumerate([long, short]):
            mc_sum:float = sum(list(map(lambda symbol: self.data[symbol].get_market_cap(), portfolio)))
            for symbol in portfolio:
                weight[symbol] = ((-1)**i) * self.data[symbol].get_market_cap() / mc_sum

    # trade execution
    invested:List[Symbol] = [x.Key for x in self.Portfolio if x.Value.Invested]
    for symbol in invested:
        if symbol not in weight:
            self.Liquidate(symbol)
    
    for price_symbol, weight in weight.items():
        if price_symbol in data and data[price_symbol]:
            self.SetHoldings(price_symbol, weight)
