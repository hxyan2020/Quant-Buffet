# Original QuantConnect / library Python
# locale=en slug="印度市场中的保守公式策略"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

from AlgorithmImports import *
from typing import Dict, Tuple, List
import data_tools
from datetime import datetime
# endregion

class ConservativeFormulaInIndia(QCAlgorithm):

def Initialize(self):
    self.SetStartDate(2010, 1, 1)
    self.SetCash(10000000) # INR

    self.price_period:int = 12 * 21
    self.price_skip_period:int = 21
    self.q_fundamental_period:int = 8 # 2 years of quarters
    
    self.data:Dict[Symbol, data_tools.SymbolData] = {}

    ticker_file_str:str = self.Download('data.quantpedia.com/backtesting_data/equity/india_stocks/nse_500_tickers.csv')
    ticker_lines:List[str] = ticker_file_str.split('\r\n')
    tickers:List[str] = [ ticker_line.split(',')[0] for ticker_line in ticker_lines[1:] ]

    self.quantile:int = 10
    self.leverage:int = 5
    self.rebalance_every_n_months:int = 3

    for t in tickers:
        # price data subscription
        data:Security = self.AddData(data_tools.IndiaStocks, t, Resolution.Daily)
        data.SetFeeModel(data_tools.CustomFeeModel())
        data.SetLeverage(self.leverage)
        stock_symbol:Symbol = data.Symbol
        
        # fundamental data subscription
        balance_sheet_symbol:Symbol = self.AddData(data_tools.IndiaBalanceSheetStatement, t, Resolution.Daily).Symbol
        cashflow_symbol:Symbol = self.AddData(data_tools.IndiaCashflowStatement, t, Resolution.Daily).Symbol

        self.data[stock_symbol] = data_tools.SymbolData(stock_symbol, balance_sheet_symbol, cashflow_symbol, self.price_period, self.q_fundamental_period)

    # BSE index hedge
    self.hedge_with_index:bool = False
    self.bse_index_data:Security = self.AddData(data_tools.BSEIndex, 'BSE_100', Resolution.Daily)
    self.bse_index_data.SetFeeModel(data_tools.CustomFeeModel())
    self.bse_index_data.SetLeverage(self.leverage)
    self.bse_index:Symbol = self.bse_index_data.Symbol

    self.recent_month:int = -1

def OnData(self, data: Slice) -> None:
    rebalance_flag:bool = False
    metrics_by_symbol:Dict[Symbol, Tuple[float, float]] = {}

    price_last_update_date:Dict[Symbol, datetime.date] = data_tools.IndiaStocks.get_last_update_date()
    bs_last_update_date:Dict[Symbol, datetime.date] = data_tools.IndiaBalanceSheetStatement.get_last_update_date()
    cf_last_update_date:Dict[Symbol, datetime.date] = data_tools.IndiaCashflowStatement.get_last_update_date()

    for price_symbol, symbol_data in self.data.items():
        # store price data
        if price_symbol in data and data[price_symbol] and data[price_symbol].Value != 0:
            price:float = data[price_symbol].Value
            self.data[price_symbol].update_price(price)
        
        bs_symbol:Symbol = symbol_data._balance_sheet_symbol
        cf_symbol:Symbol = symbol_data._cashflow_symbol

        # both CF and BS statement data is present at the same time
        if bs_symbol in data and data[bs_symbol] and cf_symbol in data and data[cf_symbol]:
            bs_statement:Dict = data[bs_symbol].Statement
            cf_statement:Dict = data[cf_symbol].Statement

            shares_field:str = 'commonStockSharesOutstanding'
            dividends_field:str = 'dividendsPaid'
            if shares_field in bs_statement and bs_statement[shares_field] is not None and \
                dividends_field in cf_statement and cf_statement[dividends_field] is not None:
                shares_outstanding:float = float(bs_statement[shares_field])
                dividend:float = float(cf_statement[dividends_field])

                # store fundamentals
                symbol_data.update_fundamentals(shares_outstanding, dividend)

        if self.IsWarmingUp: continue

        if (self.recent_month != self.Time.month and self.Time.month % self.rebalance_every_n_months == 0) or rebalance_flag:
            self.recent_month = self.Time.month
            rebalance_flag = True

            if self.Securities[price_symbol].GetLastData() and price_symbol in price_last_update_date and self.Time.date() = self.quantile:
            # calculate aggregate rank from the momentum and NPY ranks
            sorted_by_npy:List = sorted(metrics_by_symbol.items(), key=lambda x: x[1][0])
            sorted_by_momentum:List = sorted(metrics_by_symbol.items(), key=lambda x: x[1][1])
            rank:Dict[Symbol, float] = { data[0] : np.mean([sorted_by_npy.index(data), sorted_by_momentum.index(data)]) for data in sorted_by_npy}

            # portfolio consists of the top ranked stocks
            sorted_by_rank:List = sorted(rank.items(), key=lambda x: x[1], reverse=True)
            quantile:int = int(len(sorted_by_rank) / self.quantile)
            long = [x[0] for x in sorted_by_rank[:quantile]]

        # liquidate and rebalance
        invested:List[Symbol] = [x.Key for x in self.Portfolio if x.Value.Invested]
        for price_symbol in invested:
            if price_symbol not in long:# + [self.bse_index] if self.hedge_with_index else []:
                self.Liquidate(price_symbol)

        long_count:float = float(len(long))
        for price_symbol in long:
            if price_symbol in data and data[price_symbol]:
                self.SetHoldings(price_symbol, 1. / long_count)
        
        # hedge
        if self.hedge_with_index:
            if long_count != 0:
                self.SetHoldings(self.bse_index, -1)
            else:
                if self.Portfolio[self.bse_index].Invested:
                    self.Liquidate(self.bse_index)
    else:
        if self.Portfolio.Invested:
            # BSE index ended
            bse_last_udpate_date:datetime.date = data_tools.BSEIndex.get_last_update_date()
            if self.Securities[self.bse_index].GetLastData() and self.Time.date() > bse_last_udpate_date:
                self.Liquidate()
