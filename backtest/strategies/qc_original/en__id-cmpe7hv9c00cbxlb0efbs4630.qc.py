# Original QuantConnect / library Python
# locale=en slug="印度股票中的投资因子策略"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

from AlgorithmImports import *
import data_tools
from typing import List, Dict, Tuple
from datetime import datetime
# endregion

class InvestmentFactorInIndianStocks(QCAlgorithm):

def Initialize(self):
    self.SetStartDate(2010, 1, 1)
    self.SetCash(1e9) # INR

    self.quantile:int = 3
    self.leverage:int = 20
    self.period:int = 12 # 3 years of quarters
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

        self.data[stock_symbol] = data_tools.SymbolData(stock_symbol, balance_sheet, self.period)
    
    self.rebalance_month:int = 10
    self.rebalance_day:int = 1

def OnData(self, data: Slice) -> None:
    rebalance_flag:bool = False
    metric_by_symbol:Dict[Symbol, Tuple(float, float)] = {}

    price_last_update_date:Dict[Symbol, datetime.date] = data_tools.IndiaStocks.get_last_update_date()
    bs_last_update_date:Dict[Symbol, datetime.date] = data_tools.IndiaBalanceSheet.get_last_update_date()

    for symbol, symbol_data in self.data.items():
        # store price data
        if data.ContainsKey(symbol) and data[symbol] and data[symbol].Value != 0:
            price:float = data[symbol].Value
            self.data[symbol].update_price(price)

        bs_symbol:Symbol = symbol_data._balance_sheet_symbol

        # check if BS statement is present
        if bs_symbol in data and data[bs_symbol]:
            bs_statement:Dict = data[bs_symbol].Statement

            assets_field:str = 'totalAssets'
            shares_field:str = 'commonStockSharesOutstanding'
            if assets_field in bs_statement and bs_statement[assets_field] is not None \
                and shares_field in bs_statement and bs_statement[shares_field] is not None:
                date:datetime.date = self.Time
                total_assets:float = float(bs_statement[assets_field])
                shares:float = float(bs_statement[shares_field])
                # store fundamentals
                symbol_data.update_fundamentals(date, total_assets, shares)
        
        if self.IsWarmingUp: 
            continue
        
        # rebalance on first of October
        if self.Time.month == self.rebalance_month and self.Time.day == self.rebalance_day:
            rebalance_flag = True

            # fundamental data are ready and still arriving
            if self.Securities[bs_symbol].GetLastData() and bs_symbol in bs_last_update_date and self.Time.date()  0 and len(total_assets_t1) > 0:
                        change:float = (total_assets_t1[0] / total_assets_t2[0]) - 1
                        metric_by_symbol[symbol] = (change, market_cap)

    if rebalance_flag:
        weights:Dict[Symbol, float] = {}

        if len(metric_by_symbol) >= self.quantile:
            # sort by investment factor
            sorted_changes:List = sorted(metric_by_symbol.items(), key=lambda x: x[1][0], reverse=True)
            quantile:int = int(len(sorted_changes) / self.quantile)

            # get top and bottom tercile
            long_tercile:List[Symbol] = [x[0] for x in sorted_changes][:quantile]
            short_tercile:List[Symbol] = [x[0] for x in sorted_changes][-quantile:]

            # calculate weights based on marketcap
            sum_long = sum([metric_by_symbol[i][1] for i in long_tercile])
            for asset in long_tercile:
                weights[asset] = metric_by_symbol[asset][1] / sum_long

            sum_short = sum([metric_by_symbol[i][1] for i in short_tercile])
            for asset in short_tercile:
                weights[asset] = -metric_by_symbol[asset][1] / sum_short

        # liquidate and rebalance
        invested:List[Symbol] = [x.Key for x in self.Portfolio if x.Value.Invested]
        for symbol in invested:
            if symbol not in weights:
                self.Liquidate(symbol)
        
        for symbol, weight in weights.items():
            if symbol in data and data[symbol]:
                self.SetHoldings(symbol, weight)
