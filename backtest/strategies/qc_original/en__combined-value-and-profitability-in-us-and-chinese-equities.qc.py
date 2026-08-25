# Original QuantConnect / library Python
# locale=en slug="combined-value-and-profitability-in-us-and-chinese-equities"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

from AlgorithmImports import *
from data_tools import CustomFeeModel, ChineseStocks, ChineseIncomeStatement, SymbolData, FamaFrench, ChineseBalanceSheet
from typing import List, Dict
# endregion

class CombinedValueandProfitabilityinUSandChineseEquities(QCAlgorithm):

def Initialize(self):
    self.SetStartDate(2015, 1, 1)   # Chinese data starts in 2015
    self.SetCash(100000)

    self.leverage:int = 5
    self.chinese_portfolio_weight:float = 0.5

    self.us_portfolio_part_weight:float = 0.25

    self.recent_month:int = -1

    self.min_stocks:int = 7

    self.percent_stocks_to_trade:float = 0.3

    self.data:Dict[Symbol, SymbolData] = {}

    self.top_size_symbol_count:int = 100
    ticker_file_str:str = self.Download('data.quantpedia.com/backtesting_data/equity/chinese_stocks/large_cap_500.csv')
    tickers:List[str] = ticker_file_str.split('\r\n')[:self.top_size_symbol_count]

    for t in tickers:
        data = self.AddData(ChineseStocks, t, Resolution.Daily)
        data.SetFeeModel(CustomFeeModel())
        data.SetLeverage(self.leverage)

        stock_symbol:Symbol = data.Symbol
        data = self.AddData(ChineseIncomeStatement, t, Resolution.Daily)
        income_statement_symbol:Symbol = data.Symbol

        data = self.AddData(ChineseBalanceSheet, t, Resolution.Daily)
        balance_sheet_symbol:Symbol = data.Symbol

        self.data[stock_symbol] = SymbolData(income_statement_symbol, balance_sheet_symbol)

    data = self.AddData(FamaFrench, 'fama_french_6_book_to_market_daily_price', Resolution.Daily)
    data.SetFeeModel(CustomFeeModel())
    self.HML = data.Symbol

    data = self.AddData(FamaFrench, 'fama_french_6_profitability_daily_price', Resolution.Daily)
    data.SetFeeModel(CustomFeeModel())
    self.RMW = data.Symbol

def OnData(self, data: Slice):
    curr_date:datetime.date = self.Time.date()

    # store daily data
    for symbol, symbol_data in self.data.items():
        income_statement_symbol:Symbol = symbol_data.get_income_statement_symbol()
        balance_sheet_symbol:Symbol = symbol_data.get_balance_sheet_symbol()

        if data.ContainsKey(symbol):
            price_data:Dict[str, str] = data[symbol].GetProperty('price_data')
            # valid price data
            if data[symbol].Value != 0. and price_data:
                mc:float = float(price_data['marketValue'])
                symbol_data.set_market_equity(mc)

        if data.ContainsKey(income_statement_symbol):
            # update operating, gross and net profit from income statement
            operating_profit:float = float(data[income_statement_symbol].GetProperty('operating_profit'))
            gross_profit:float = float(data[income_statement_symbol].GetProperty('gross_profit'))
            net_profit:float = float(data[income_statement_symbol].GetProperty('net_profit'))

            symbol_data.set_operating_profit(operating_profit)
            symbol_data.set_gross_profit(gross_profit)
            symbol_data.set_net_profit(net_profit)

        if data.ContainsKey(balance_sheet_symbol):
            # update total assets and total liabilities from balance sheet
            total_assets:float = float(data[balance_sheet_symbol].GetProperty('total_assets'))
            total_liabilities:float = float(data[balance_sheet_symbol].GetProperty('total_liabilities'))

            symbol_data.set_total_assets(total_assets)
            symbol_data.set_total_liabilities(total_liabilities)

    # rebalance monthly
    if self.recent_month == self.Time.month:
        return
    self.recent_month = self.Time.month

    symbols_with_measures:List[Symbol] = []
    measures:Dict[str, Dict[Symbol, float]] = {
        'OP_to_ME': {},
        'GP_to_ME': {},
        'NP_to_ME': {},
        'GP_to_TA': {},
        'OP_to_BE': {},
        'NP_to_BE': {},
    }

    for symbol, symbol_data in self.data.items():
        if not symbol_data.is_ready() or symbol not in data or not data[symbol] or \
            data[symbol].Value == 0 or not self.Securities[symbol].IsTradable:
            continue
        
        # calculate required mesaures
        measures['OP_to_ME'][symbol] = symbol_data.get_operating_profit_to_market_equity()
        measures['GP_to_ME'][symbol] = symbol_data.get_gross_profit_to_market_equity()
        measures['NP_to_ME'][symbol] = symbol_data.get_net_profit_to_market_equity()
        measures['GP_to_TA'][symbol] = symbol_data.get_gross_profit_to_total_assets()
        measures['OP_to_BE'][symbol] = symbol_data.get_operating_profit_to_book_equity()
        measures['NP_to_BE'][symbol] = symbol_data.get_net_profit_to_book_equity()

        symbols_with_measures.append(symbol)
    
    # make sure there are enough stocks with measures for selection
    if len(symbols_with_measures)
