# Original QuantConnect / library Python
# locale=en slug="the-size-effect-in-indian-market"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

from AlgorithmImports import *
from typing import Dict, List
import data_tools
# endregion
class TheSizeEffectinIndianMarket(QCAlgorithm):
def Initialize(self):
    self.SetStartDate(2010, 1, 1)
    self.SetCash(100000000) # INR
    self.quantile:int = 5
    self.leverage:int = 5
    self.data:Dict[Symbol, data_tools.SymbolData] = {}
    # download tickers
    ticker_file_str:str = self.Download('data.quantpedia.com/backtesting_data/equity/india_stocks/nse_500_tickers.csv')
    ticker_lines:List[str] = ticker_file_str.split('\r\n')
    tickers:List[str] = [ ticker_line.split(',')[0] for ticker_line in ticker_lines[1:] ]
    for t in tickers:
        # price data subscription
        data = self.AddData(data_tools.IndiaStocks, t, Resolution.Daily)
        data.SetFeeModel(data_tools.CustomFeeModel())
        data.SetLeverage(self.leverage)
        stock_symbol:Symbol = data.Symbol
        # fundamental data subscription
        balance_sheet = self.AddData(data_tools.IndiaBalanceSheet, t, Resolution.Daily).Symbol 
        self.data[stock_symbol] = data_tools.SymbolData(stock_symbol, balance_sheet)
    
    self.recent_month:int = -1
def OnData(self, data: Slice) -> None:
    rebalance_flag:bool = False
    metric_by_symbol:Dict[Symbol, float] = {}
    price_last_update_date:Dict[Symbol, datetime.date] = data_tools.IndiaStocks.get_last_update_date()
    bs_last_update_date:Dict[Symbol, datetime.date] = data_tools.IndiaBalanceSheet.get_last_update_date()
    for price_symbol, symbol_data in self.data.items():
        # store price data
        if data.ContainsKey(price_symbol) and data[price_symbol] and data[price_symbol].Value != 0:
            price: float = data[price_symbol].Value
            self.data[price_symbol].update_price(price)
        bs_symbol:Symbol = symbol_data._balance_sheet_symbol
        # check if BS statement is present
        if bs_symbol in data and data[bs_symbol]:
            bs_statement:Dict = data[bs_symbol].Statement
            shares_field:str = 'commonStockSharesOutstanding'
            if shares_field in bs_statement and bs_statement[shares_field] is not None:
                shares_outstanding:float = float(bs_statement[shares_field])
                # store fundamentals
                symbol_data.update_fundamentals(shares_outstanding)
        
        if self.IsWarmingUp: 
            continue
        
        # monthly rebalance
        if self.Time.month != self.recent_month or rebalance_flag:
            self.recent_month = self.Time.month
            rebalance_flag = True
            # fundamental data are ready and still arriving
            if self.Securities[price_symbol].GetLastData() and price_symbol in price_last_update_date and self.Time.date() = self.quantile:
            # sort by market capitalization
            sorted_market_cap = sorted(metric_by_symbol, key=metric_by_symbol.get)
            quantile: int = int(len(sorted_market_cap) / self.quantile)
            # get top and bottom quintile
            long_assets:List[Symbol] = sorted_market_cap[:quantile]
            short_assets:List[Symbol] = sorted_market_cap[-quantile:]
            # calculate weights based on values
            sum_long = sum([metric_by_symbol[i] for i in long_assets])
            for asset in long_assets:
                weights[asset] = metric_by_symbol[asset] / sum_long
            sum_short = sum([metric_by_symbol[i] for i in short_assets])
            for asset in short_assets:
                weights[asset] = -metric_by_symbol[asset] / sum_short
        
        # liquidate and rebalance
        invested:List[Symbol] = [x.Key for x in self.Portfolio if x.Value.Invested]
        for price_symbol in invested:
            if price_symbol not in weights:
                self.Liquidate(price_symbol)
        
        for price_symbol, weight in weights.items():
            if price_symbol in data and data[price_symbol]:
                self.SetHoldings(price_symbol, weight)
