# Original QuantConnect / library Python
# locale=en slug="factor-momentum-in-the-chinese-stock-market"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

from AlgorithmImports import *
from data_tools import ChineseStocks, CustomFeeModel, ChineseBalanceSheet, \
ChineseIncomeStatement, ChineseCashflowStatement, SymbolData, FactorData
# endregion

class FactorMomentumInTheChineseStockMarket(QCAlgorithm):

def Initialize(self):
    self.SetStartDate(2010, 1, 1)
    self.SetCash(100000)

    self.top_size_symbol_count:int = 200
    ticker_file_str:str = self.Download('data.quantpedia.com/backtesting_data/equity/chinese_stocks/large_cap_500.csv')
    self.tickers:List[str] = ticker_file_str.split('\r\n')[:self.top_size_symbol_count]

    self.quantile:int = 3
    self.leverage:int = 5

    self.period:int = 3 * 21
    self.monthly_returns_period:int = 1

    self.min_prices:int = 15
    self.min_volumes:int = 15
    self.max_missing_statement_days:int = 3 * 30

    self.data:dict[Symbol, SymbolData] = {}

    self.factors_identificators:list[str] = ['SIZE', 'BM', 'ILLIQUIDITY','EARNINGS-TO-PRICE','CF-TO-PRICE','TURNOVER']
    self.factors_data:dict[str, FactorData] = { identificator: FactorData(self.monthly_returns_period) \
        for identificator in self.factors_identificators }

    for t in self.tickers:
        # price data
        data = self.AddData(ChineseStocks, t, Resolution.Daily)
        data.SetFeeModel(CustomFeeModel())
        data.SetLeverage(self.leverage)

        china_stock_symbol:Symbol = data.Symbol
        income_symbol:Symbol = self.AddData(ChineseIncomeStatement, t, Resolution.Daily).Symbol
        balance_symbol:Symbol = self.AddData(ChineseBalanceSheet, t, Resolution.Daily).Symbol
        cashflow_symbol:Symbol = self.AddData(ChineseCashflowStatement, t, Resolution.Daily).Symbol

        self.data[china_stock_symbol] = SymbolData(self.period, income_symbol, balance_symbol, cashflow_symbol)
    
    self.recent_month:int = -1
    self.spy:Symbol = self.AddEquity('SPY', Resolution.Daily).Symbol
    self.Schedule.On(self.DateRules.MonthEnd(self.spy), self.TimeRules.BeforeMarketClose(self.spy, 0), self.UpdateFactorsPerformances)

def OnData(self, data: Slice):
    factors:dict[str, dict] = { identificator: {} for identificator in self.factors_identificators }
    curr_date:datetime.date = self.Time.date()

    for symbol, symbol_data in self.data.items():
        income_symbol:Symbol = symbol_data.income_symbol
        if income_symbol in data and data[income_symbol] and data[income_symbol].GetProperty('statement'):
            symbol_data.update_income_data(curr_date, data[income_symbol].GetProperty('statement'))

        balance_symbol:Symbol = symbol_data.balance_symbol
        if balance_symbol in data and data[balance_symbol] and data[balance_symbol].GetProperty('statement'):
            symbol_data.update_balance_data(curr_date, data[balance_symbol].GetProperty('statement'))

        cashflow_symbol:Symbol = symbol_data.cashflow_symbol
        if cashflow_symbol in data and data[cashflow_symbol] and data[cashflow_symbol].GetProperty('statement'):
            symbol_data.update_cashflow_data(curr_date, data[cashflow_symbol].GetProperty('statement'))

        if symbol in data and data[symbol] and data[symbol].Value and data[symbol].GetProperty('price_data'):
            price_data:dict = data[symbol].GetProperty('price_data')
        
            price:float = data[symbol].Value 
            volume:float = price_data['turnoverVol']
            symbol_data.update_prices_volumes_last_update(price, volume, curr_date)

            if self.recent_month != self.Time.month \
                and symbol_data.statements_still_coming(curr_date, self.max_missing_statement_days):

                balance_data:dict[str, str] = symbol_data.balance_data
                income_data:dict[str, str] = symbol_data.income_data
                cashflow_data:dict[str, str] = symbol_data.cashflow_data

                market_cap:float = float(price_data['marketValue'])
                total_assets:float = float(balance_data['TAssets'])

                if market_cap != 0 and total_assets != 0 and symbol_data.turnover_volumes_ready() \
                    and symbol_data.prices_ready(self.min_prices) and symbol_data.volumes_ready(self.min_volumes):
                    
                    factors['SIZE'][symbol] = market_cap

                    book_value:float = total_assets - float(balance_data['TLiab'])
                    book_to_market:float = book_value / market_cap
                    factors['BM'][symbol] = book_to_market

                    factors['ILLIQUIDITY'][symbol] = symbol_data.get_illiquidity()

                    net_income:float = float(income_data['NIncome'])
                    earnings_to_price:float = net_income / market_cap
                    factors['EARNINGS-TO-PRICE'][symbol] = earnings_to_price

                    shares_oustanding:float = market_cap / price
                    avg_vol_for_turnover:float = symbol_data.get_avg_vol_for_turnover()
                    factors['TURNOVER'][symbol] = avg_vol_for_turnover / shares_oustanding

                    operating_cashflow:float = float(cashflow_data['NCFOperateA'])
                    factors['CF-TO-PRICE'][symbol] = operating_cashflow / market_cap

                symbol_data.reset_prices_and_volumes()

    if self.recent_month != self.Time.month:
        self.Liquidate()
        self.recent_month = self.Time.month

        if len(factors[self.factors_identificators[0]]) >= self.quantile:
            for factor_identificator, factor_value_by_symbol in factors.items():
                quantile:int = int(len(factor_value_by_symbol) / self.quantile)
                sorted_by_factor_value:list[Symbol] = [x[0] for x in sorted(factor_value_by_symbol.items(), key=lambda item: item[1])]

                highest_quantile:list[Symbol] = sorted_by_factor_value[-quantile:]
                lowest_quantile:list[Symbol] = sorted_by_factor_value[:quantile]

                self.factors_data[factor_identificator].set_factor_quantiles(highest_quantile, lowest_quantile)

            factor_cumulative_perf:dict[str, float] = { identificator: factor_data.get_cumulative_perf() \
                for identificator, factor_data in self.factors_data.items() if factor_data.factor_monthly_perfs_ready() }
            
            factor_perf_median:float = np.median(list(factor_cumulative_perf.values()))

            long_leg:list[Symbol] = []
            short_leg:list[Symbol] = []

            for identificator, cumulative_perf in factor_cumulative_perf.items():
                if cumulative_perf > factor_perf_median:
                    long_leg += list(factors[identificator].keys())
                else:
                    short_leg += list(factors[identificator].keys())

            long_len:int = len(long_leg)
            short_len:int = len(short_leg)

            for symbol in long_leg:
                self.SetHoldings(symbol, 1 / long_len)

            for symbol in short_leg:
                self.SetHoldings(symbol, -1 / short_len)

def UpdateFactorsPerformances(self) -> None:
    for identificator, factor_data in self.factors_data.items():
        if factor_data.factor_quantiles_ready():
            highest_quantile_perf:float = sum([self.data[symbol].get_performance() for symbol in factor_data.highest_quantile])
            lowest_quantile_perf:float = -sum([self.data[symbol].get_performance() for symbol in factor_data.lowest_quantile])

            factor_perf:float = highest_quantile_perf + lowest_quantile_perf

            factor_data.update_factor_monthly_perfs(factor_perf)

        else:
            factor_data.reset_monthly_perfs()

        factor_data.reset_factor_quantiles()

def AreDataStillComing(self, symbol:Symbol, max_missing_days:int) -> bool:
    return (self.Time.date() - self.Securities[symbol].GetLastData().Time.date()).days
