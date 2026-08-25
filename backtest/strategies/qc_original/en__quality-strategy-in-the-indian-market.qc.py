# Original QuantConnect / library Python
# locale=en slug="quality-strategy-in-the-indian-market"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

from AlgorithmImports import *
from typing import Dict, Tuple, List
import data_tools
from datetime import datetime
from pandas.core.frame import DataFrame
# endregion
class QualityStrategyintheIndianMarket(QCAlgorithm):
def Initialize(self):
    self.SetStartDate(2010, 1, 1)
    self.SetCash(10000000) # INR
    self.price_period:int = 12 * 21
    self.q_fundamental_period:int = 8 # 2 years of quarters
    self.data:Dict[Symbol, data_tools.SymbolData] = {}
    ticker_file_str:str = self.Download('data.quantpedia.com/backtesting_data/equity/india_stocks/nse_500_tickers.csv')
    ticker_lines:List[str] = ticker_file_str.split('\r\n')
    tickers = [ ticker_line.split(',')[0] for ticker_line in ticker_lines[1:] ]
    self.quantile:int = 5
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
        income_statement_symbol:Symbol = self.AddData(data_tools.IndiaIncomeStatement, t, Resolution.Daily).Symbol
        cashflow_symbol:Symbol = self.AddData(data_tools.IndiaCashflowStatement, t, Resolution.Daily).Symbol
        self.data[stock_symbol] = data_tools.SymbolData(stock_symbol, 
                                                        balance_sheet_symbol, 
                                                        income_statement_symbol, 
                                                        cashflow_symbol, 
                                                        self.price_period, 
                                                        self.q_fundamental_period)
    self.recent_month:int = -1
def OnData(self, data: Slice) -> None:
    rebalance_flag:bool = False
    
    # profitability, growth, and safety 
    fundamentals_by_symbol:Dict[Symbol, Tuple[np.ndarray]] = {}
    price_last_update_date:Dict[Symbol, datetime.date] = data_tools.IndiaStocks.get_last_update_date()
    bs_last_update_date:Dict[Symbol, datetime.date] = data_tools.IndiaBalanceSheetStatement.get_last_update_date()
    is_last_update_date:Dict[Symbol, datetime.date] = data_tools.IndiaIncomeStatement.get_last_update_date()
    cf_last_update_date:Dict[Symbol, datetime.date] = data_tools.IndiaCashflowStatement.get_last_update_date()
    for price_symbol, symbol_data in self.data.items():
        # store price data
        if price_symbol in data and data[price_symbol] and data[price_symbol].Value != 0:
            price:float = data[price_symbol].Value
            self.data[price_symbol].update_price(price)
        
        bs_symbol:Symbol = symbol_data._balance_sheet_symbol
        cf_symbol:Symbol = symbol_data._cashflow_symbol
        is_symbol:Symbol = symbol_data._income_statement_symbol
        # fundamental data is present at the same time
        if bs_symbol in data and data[bs_symbol] and \
            cf_symbol in data and data[cf_symbol] and \
            is_symbol in data and data[is_symbol]:
            bs_statement = data[bs_symbol]
            cf_statement = data[cf_symbol]
            is_statement = data[is_symbol]
            if hasattr(bs_statement, 'Totalstockholderequity') and bs_statement.Totalstockholderequity != 0 and \
                hasattr(bs_statement, 'Totalassets') and bs_statement.Totalassets != 0 and \
                hasattr(bs_statement, 'Shortlongtermdebttotal') and bs_statement.Shortlongtermdebttotal != 0 and \
                hasattr(is_statement, 'Netincome') and is_statement.Netincome != 0 and \
                hasattr(is_statement, 'Operatingincome') and is_statement.Operatingincome != 0 and \
                hasattr(is_statement, 'Totalrevenue') and is_statement.Totalrevenue != 0 and \
                hasattr(cf_statement, 'Totalcashfromoperatingactivities') and cf_statement.Totalcashfromoperatingactivities != 0 and \
                hasattr(cf_statement, 'Freecashflow') and cf_statement.Freecashflow != 0 and \
                hasattr(cf_statement, 'Endperiodcashflow')  and cf_statement.Endperiodcashflow != 0:
                    current_date:datetime.date = self.Time.date()
                    # store fundamentals
                    symbol_data.update_growth_fundamentals('roe', is_statement.Netincome / bs_statement.Totalstockholderequity)
                    symbol_data.update_growth_fundamentals('roa', is_statement.Netincome / bs_statement.Totalassets)
                    symbol_data.update_growth_fundamentals('cfoa', cf_statement.Endperiodcashflow / bs_statement.Totalassets)
                    symbol_data.update_growth_fundamentals('opmar', is_statement.Operatingincome / is_statement.Totalrevenue)
                    symbol_data.update_growth_fundamentals('acc', (is_statement.Netincome - cf_statement.Freecashflow) / bs_statement.Totalassets)
                    if symbol_data.prices_ready():
                        lev:float = bs_statement.Shortlongtermdebttotal / bs_statement.Totalassets
                        cflev:float = cf_statement.Totalcashfromoperatingactivities / bs_statement.Shortlongtermdebttotal
                        symbol_data.update_fundamentals('lev', lev)
                        symbol_data.update_fundamentals('cflev', cflev)
        if self.IsWarmingUp: continue
        if (self.recent_month != self.Time.month and self.Time.month % self.rebalance_every_n_months == 0) or rebalance_flag:
            self.recent_month = self.Time.month
            rebalance_flag = True
            # fundamental data are ready and still arriving
            if self.Securities[price_symbol].GetLastData() and price_symbol in price_last_update_date and self.Time.date() = self.quantile:
            # calculate z-scores
            items:List = list(fundamentals_by_symbol.items())
            symbols:List[str] = list(map(lambda x: x[0], items))
            fundamentals:List[str] = list(map(lambda x: x[1], items))
            quality:np.ndarray = np.array([0.] * len(symbols))
            profitability_values:np.ndarray = np.array([x[0] for x in fundamentals])
            growth_values:np.ndarray = np.array([x[1] for x in fundamentals])
            safety_values:np.ndarray = np.array([x[2] for x in fundamentals])
            for metrics_values in [profitability_values, growth_values, safety_values]:
                metrics_z_scores:np.ndarray = (metrics_values - np.mean(metrics_values, axis=0)) / np.std(metrics_values, axis=0)
                metrics_z_score_sum:np.ndarray = metrics_z_scores.sum(axis=1)
                metrics:np.ndarray = (metrics_z_score_sum - metrics_z_score_sum.mean(axis=0)) / metrics_z_score_sum.std(axis=0)
                quality += metrics
            
            # total quality score
            quality_z_score:np.ndarray = (quality - np.mean(quality, axis=0)) / np.std(quality, axis=0)
            quality_by_symbol = {symbol : z_score for symbol, z_score in zip(symbols, quality_z_score)}
            # quality sort
            sorted_by_quality:List = sorted(quality_by_symbol.items(), key=lambda x: x[1], reverse=True)
            quantile:int = int(len(sorted_by_quality) / self.quantile)
            long = [x[0] for x in sorted_by_quality[:quantile]]
        # liquidate and rebalance
        invested:List[Symbol] = [x.Key for x in self.Portfolio if x.Value.Invested]
        for price_symbol in invested:
            if price_symbol not in long:
                self.Liquidate(price_symbol)
        long_count:float = float(len(long))
        for price_symbol in long:
            if price_symbol in data and data[price_symbol]:
                self.SetHoldings(price_symbol, 1. / long_count)
