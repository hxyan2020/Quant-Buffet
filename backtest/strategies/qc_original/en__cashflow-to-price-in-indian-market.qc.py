# Original QuantConnect / library Python
# locale=en slug="cashflow-to-price-in-indian-market"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

from AlgorithmImports import *
from typing import Dict, List
import data_tools
from datetime import datetime
# endregion
class CashflowToPriceInIndianMarket(QCAlgorithm):
def Initialize(self):
    self.SetStartDate(2010, 1, 1)
    self.SetCash(1e9) # INR
    # set variables
    self.quantile:int = 5
    self.leverage:int = 10
    self.data:Dict[Symbol, data_tools.SymbolData] = {}
    self.excluded_tickers:List[str] = ['LODHA']
    # download tickers
    ticker_file_str:str = self.Download('data.quantpedia.com/backtesting_data/equity/india_stocks/nse_500_tickers.csv')
    ticker_lines:List[str] = ticker_file_str.split('\r\n')
    tickers:List[str] = [ ticker_line.split(',')[0] for ticker_line in ticker_lines[1:] ]
    for t in tickers:
        if t in self.excluded_tickers: continue
        # price data subscription
        data = self.AddData(data_tools.IndiaStocks, t, Resolution.Daily)
        data.SetFeeModel(data_tools.CustomFeeModel())
        data.SetLeverage(self.leverage)
        stock_symbol:Symbol = data.Symbol
        # fundamental data subscription
        balance_sheet = self.AddData(data_tools.IndiaBalanceSheet, t, Resolution.Daily).Symbol 
        cashflow_sheet = self.AddData(data_tools.IndiaCashflowStatement, t, Resolution.Daily).Symbol
        self.data[stock_symbol] = data_tools.SymbolData(stock_symbol, balance_sheet, cashflow_sheet)
    
    self.recent_month:int = -1
def OnData(self, data: Slice) -> None:
    rebalance_flag:bool = False
    metric_by_symbol:Dict[Symbol, float] = {}
    price_last_update_date:Dict[Symbol, datetime.date] = data_tools.IndiaStocks.get_last_update_date()
    bs_last_update_date:Dict[Symbol, datetime.date] = data_tools.IndiaBalanceSheet.get_last_update_date()
    cf_last_update_date:Dict[Symbol, datetime.date] = data_tools.IndiaCashflowStatement.get_last_update_date()
    for price_symbol, symbol_data in self.data.items():
        # store price data
        if data.ContainsKey(price_symbol) and data[price_symbol] and data[price_symbol].Value != 0:
            price:float = data[price_symbol].Value
            self.data[price_symbol].update_price(price)
        bs_symbol:Symbol = symbol_data._balance_sheet_symbol
        cf_symbol:Symbol = symbol_data._cashflow_sheet_symbol
        # check if BS and CF statement is present
        if bs_symbol in data and data[bs_symbol] and cf_symbol in data and data[cf_symbol]:
            bs_statement:Dict = data[bs_symbol].Statement
            cf_statement:Dict = data[cf_symbol].Statement
            shares_field:str = 'commonStockSharesOutstanding'
            operating_field:str = 'totalCashFromOperatingActivities'
            if shares_field in bs_statement and bs_statement[shares_field] is not None and \
                operating_field in cf_statement and cf_statement[operating_field] is not None:
                shares_outstanding:float = float(bs_statement[shares_field])
                cashflow: float = float(cf_statement[operating_field])
                # store fundamentals
                symbol_data.update_fundamentals(shares_outstanding, cashflow)
        if self.IsWarmingUp: continue
        if self.Time.month != self.recent_month or rebalance_flag:
            self.recent_month = self.Time.month
            rebalance_flag = True
            # fundamental data are ready and still arriving
            if self.Securities[price_symbol].GetLastData() and price_symbol in price_last_update_date and self.Time.date() = self.quantile:
            # sort cashflow to price ratio
            sorted_cftp:List = sorted(metric_by_symbol.items(), key=lambda x: x[1][0], reverse=True)
            quantile:int = int(len(sorted_cftp) / self.quantile)
            # get top and bottom quantile
            short_assets = [x[0] for x in sorted_cftp[:quantile]]
            long_assets = [x[0] for x in sorted_cftp[-quantile:]]
            # calculate weights based on values
            sum_short:float = sum([metric_by_symbol[i][1] for i in short_assets])
            for asset in short_assets:
                weights[asset] = -metric_by_symbol[asset][1] / sum_short
        
            sum_long:float = sum([metric_by_symbol[i][1] for i in long_assets])
            for asset in long_assets:
                weights[asset] = metric_by_symbol[asset][1] / sum_long
        # liquidate and rebalance
        invested:List[Symbol] = [x.Key for x in self.Portfolio if x.Value.Invested]
        for price_symbol in invested:
            if price_symbol not in weights:
                self.Liquidate(price_symbol)
        
        for price_symbol, weight in weights.items():
            if price_symbol in data and data[price_symbol]:
                self.SetHoldings(price_symbol, weight)
