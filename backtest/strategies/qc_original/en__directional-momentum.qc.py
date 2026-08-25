# Original QuantConnect / library Python
# locale=en slug="directional-momentum"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

from AlgorithmImports import *
import pandas as pd
import data_tools
from typing import List, Dict
import statsmodels.api as sm
from dateutil.relativedelta import relativedelta
from collections import deque
import numpy as np
from pandas.core.frame import DataFrame
from pandas.core.series import Series
# endregion

class DirectionalMomentum(QCAlgorithm):

def Initialize(self):
    self.SetStartDate(2000, 1, 1)
    self.SetCash(100000)

    self.exchange_codes: List[str] = ['NYS', 'NAS', 'ASE']    

    self.data: Dict[Symbol, data_tools.SymbolData] = {}
    self.weight: Dict[Symbol, float] = {}

    self.warmup_period: int = 12
    self.period: int = 60
    self.month_period: int = 21
    self.leverage: int = 5
    self.quantile: int = 10

    self.market: Symbol = self.AddEquity('SPY', Resolution.Daily).Symbol

    self.fundamental_count: int = 500
    self.fundamental_sorting_key = lambda x: x.DollarVolume

    self.selection_flag: bool = False
    self.UniverseSettings.Resolution = Resolution.Daily
    self.AddUniverse(self.FundamentalSelectionFunction)
    self.Settings.MinimumOrderMarginPortfolioPercentage = 0.
    self.Schedule.On(self.DateRules.MonthStart(self.market), self.TimeRules.AfterMarketOpen(self.market), self.Selection)

def OnSecuritiesChanged(self, changes: SecurityChanges) -> None:
    for security in changes.AddedSecurities:
        security.SetFeeModel(data_tools.CustomFeeModel())
        security.SetLeverage(self.leverage)
        
def FundamentalSelectionFunction(self, fundamental: List[Fundamental]) -> List[Symbol]:
    # update the data every day
    for stock in fundamental:
        symbol: Symbol = stock.Symbol
        
        # store monthly price
        if symbol in self.data:
            self.data[symbol].update_daily_return(self.Time.date(), stock.AdjustedPrice)
            if self.selection_flag:
                self.data[symbol].update_monthly_return(stock.AdjustedPrice)
        
    if not self.selection_flag:
        return Universe.Unchanged

    selected: List[Fundamental] = [x for x in fundamental if x.HasFundamentalData and x.Market == 'usa' \
                              and x.MarketCap != 0 and x.SecurityReference.ExchangeId in self.exchange_codes]

    if len(selected) > self.fundamental_count:
        selected = [x for x in sorted(selected, key=self.fundamental_sorting_key, reverse=True)[:self.fundamental_count]]

    selected_dict: Dict[Symbol, Fundamental] = {x.Symbol: x for x in selected}

    # warmup price rolling windows
    for stock in selected + [self.market]:
        if stock == self.market:
            symbol: Symbol = stock
        else:
            symbol: Symbol = stock.Symbol

        if symbol not in self.data:
            self.data[symbol] = data_tools.SymbolData(self.period * self.month_period, self.warmup_period * self.month_period, self.period)
            history: DataFrame = self.History(symbol, self.period * self.month_period, Resolution.Daily)
            if history.empty:
                self.Log(f"Not enough data for {symbol} yet.")
                continue
            data: Series = history.loc[symbol]
            monthly_data: Series = data.groupby(pd.Grouper(freq='MS')).last()
            for time, row in data.iterrows():
                self.data[symbol].update_daily_return(time.date(), row.close)
            for time, row in monthly_data.iterrows():
                self.data[symbol].update_monthly_return(row.close)

    if len(selected) != 0:

        returns: Dict[Symbol, List[float]] = {symbol: data.get_returns_idiosyncratic_regression() for symbol, data in self.data.items() if data.is_ready_for_first_regression() and symbol in list(selected_dict.keys()) and symbol != self.market}
        stock_returns: List[List[float]] = list(zip(*[[i for i in x] for x in returns.values()]))

        if len(returns) != 0:
            # get idiosyncratic variance
            x: np.ndarray = np.array(self.data[self.market].get_returns_idiosyncratic_regression())
            y: np.ndarray = stock_returns[-self.month_period:]
            model = self.multiple_linear_regression(x, y)
            variance: float = np.std(model.resid, axis=0) ** 2

            for i, symbol in enumerate(returns):
                self.data[symbol].update_variance(variance[i])

            reg_data_dict: Dict[Symbol,List[Tuple[datetime.date, float]]] = {symbol: self.data[symbol].get_variance_values() for symbol in list(returns.keys()) if self.data[symbol].is_ready_for_regression()}
        
            if len(reg_data_dict) != 0:
                reg_data: List[List[float]] = list(zip (*[[i for i in x] for x in reg_data_dict.values()]))
                df_stocks: DataFrame = pd.DataFrame(index=self.data[self.market].get_dates())

                returns: Dict[Symbol, List[float]] = {symbol: data.get_data() for symbol, data in self.data.items() if data.is_ready_for_regression() and symbol in list(selected_dict.keys()) and symbol != self.market}

                # fill dataframe with data
                for symbol, data in returns.items():
                    symbol_df: DataFrame = pd.DataFrame(data, columns=['date', 'return'])
                    symbol_df['date'] = pd.to_datetime(symbol_df['date'])
                    symbol_df = symbol_df.set_index('date')
                    symbol_df = symbol_df.loc[~symbol_df.index.duplicated(keep='first')]

                    df_stocks[symbol] = symbol_df['return']
    
                df_stocks = df_stocks.ffill().fillna(0)

                # get current positive and negative runs
                df_reg: DataFrame = self.longest_consecutive_run_for_stocks(df_stocks)[-self.period:]

                independent_variable: np.ndarray = np.column_stack((reg_data, self.data[self.market].get_monthly_returns(), df_reg.values))

                # # run stock regression
                x: np.ndarray = independent_variable[:-1]
                y: np.ndarray = np.where(df_stocks.groupby(pd.Grouper(freq='M')).sum()[-self.period:].values[1:] = self.quantile:
                    sorted_PS: List[Symbol] = sorted(PS, key=PS.get, reverse=True)
                    quantile: int = int(len(sorted_PS) / self.quantile)
                    long: List[Symbol] = sorted_PS[:quantile]
                    short: List[Symbol] = sorted_PS[-quantile:]

                # calculate weights
                for i, portfolio in enumerate([long, short]):
                    mc_sum: float = sum(list(map(lambda symbol: selected_dict[symbol].MarketCap, portfolio)))
                    for symbol in portfolio:
                        self.weight[symbol] = ((-1)**i) * selected_dict[symbol].MarketCap / mc_sum

    return list(self.weight.keys())

def OnData(self, data: Slice):
    if not self.selection_flag:
        return
    self.selection_flag = False

    # trade execution
    portfolio: List[PortfolioTarget] = [PortfolioTarget(symbol, w) for symbol, w in self.weight.items() if symbol in data and data[symbol]]
    self.SetHoldings(portfolio, True)

    self.weight.clear()

def Selection(self) -> None:
    self.selection_flag = True

def multiple_linear_regression(self, x: np.ndarray, y: np.ndarray):
    # x:np.ndarray = np.array(x).T
    x = sm.add_constant(x, prepend=True)
    result = sm.OLS(endog=y, exog=x).fit()
    return result

def longest_consecutive_run_for_stocks(self, df, threshold=0) -> DataFrame:
    df_daily: DataFrame = df
    df_daily.index = pd.to_datetime(df_daily.index)
    df_weekly: DataFrame = df_daily.groupby(pd.Grouper(freq='W')).sum()
    df_monthly: Dataframe = df_daily.groupby(pd.Grouper(freq='M')).sum()
    df_list: List[DataFrame] = [df_daily, df_weekly, df_monthly]

    df_end: DataFrame = pd.DataFrame()

    for df in df_list:
        positive_df: DataFrame = df.applymap(lambda x: 1 if x > 0 else 0).apply(lambda col: col.groupby((col != col.shift()).cumsum()).cumsum()).groupby(pd.Grouper(freq='M')).last()
        negative_df: DataFrame = df.applymap(lambda x: 1 if x
