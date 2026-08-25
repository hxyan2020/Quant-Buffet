# Original QuantConnect / library Python
# locale=zh slug="货币中的经济动能"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

from AlgorithmImports import *
from io import StringIO
import data_tools
from dateutil.relativedelta import relativedelta
import numpy as np
import pandas as pd
from collections import deque
from pandas.core.frame import DataFrame
# endregion
class EconomicMomentuminCurrencies(QCAlgorithm):
def Initialize(self):
    self.SetStartDate(2005, 1, 1)
    self.SetCash(100000)
    self.leverage:int = 5
    self.period:int = 60
    self.volatility_period:int = 36
    self.rolling_period:int = 2
    self.max_missing_days:int = 32
    self.min_lookback_period:int = 24
    self.data:Dict[Symbol, data_tools.SymbolData] = {}
    self.custom_data_df:Dict[str, DataFrame] = {}
    self.measures:Dict[Symbol, Tuple[int, float]] = {}
    self.custom_data_index:List[str] = ['IND_PRO_countries', 'goods_export_countries', 'goods_import_countries']
    self.custom_data_perc:List[str] = ['CPI_countries', 'LTIR_countries', 'STIR_countries', 'UNEMPLOYMENT_countries']
    # create dataframes from custom data
    for variable in self.custom_data_index + self.custom_data_perc:
        load:str = self.Download(f'data.quantpedia.com/backtesting_data/economic/{variable}.csv')
        df:DataFrame = pd.read_csv(StringIO(load), delimiter=';')
        df['TIME'] = pd.to_datetime(df['TIME']).dt.date
        df.set_index('TIME', inplace=True)
        self.custom_data_df[variable] = df
    
    # calculate yield sread and trade balance of countries
    self.custom_data_df['yield_spread'] = self.custom_data_df['LTIR_countries'] - self.custom_data_df['STIR_countries']
    self.custom_data_df['trade_balance'] = (self.custom_data_df['goods_export_countries'] - self.custom_data_df['goods_import_countries']) \
         / (self.custom_data_df['goods_export_countries'] + self.custom_data_df['goods_import_countries'])
    self.custom_data_df = {k:v for k, v in self.custom_data_df.items() if k not in ['goods_export_countries', 'goods_import_countries']}
    self.symbols:Dict[str, str] = {"AUDUSD": 'AUS', "GBPUSD": 'GBR', "CADUSD": 'CAN', "EURUSD": 'EU', "JPYUSD": 'JPN', "NOKUSD": 'NOR', "SEKUSD": 'SWE', "NZDUSD": 'NZL', "CHFUSD": 'CHE'}
    
    # data subscription
    for symbol in self.symbols:
        data:Security = self.AddForex(symbol, Resolution.Daily, Market.Oanda)
        data.SetFeeModel(data_tools.CustomFeeModel())
        data.SetLeverage(self.leverage)
        self.data[data.Symbol] = data_tools.SymbolData(self.rolling_period)
    self.selection_flag:bool = False            
    self.Settings.MinimumOrderMarginPortfolioPercentage = 0.
    self.recent_month:int = -1
def OnData(self, data: Slice) -> None:
    # monthly rebalance
    if self.recent_month == self.Time.month:
        return
    self.recent_month = self.Time.month
    
    # store monthly prices
    for symbol, symbol_data in self.data.items():
        if symbol in data and data[symbol]:
            symbol_data.update_price(data[symbol].Price)
    look_back:DateTime.date = self.Time.date() - relativedelta(months=self.period)
    current_date:DateTime.date = self.Time.date()
    currency_returns:Dict[Symbol, float] = {self.symbols[sym.Value] : data.get_return() for sym, data in self.data.items() if data.is_ready()}
    if len(currency_returns) == 0:
        return
    returns_df:DataFrame = pd.DataFrame([currency_returns])
    for i in range(self.min_lookback_period, self.period):
        measure_df:DataFrame = pd.DataFrame()
        weights_df:DataFrame = pd.DataFrame()
        for data_title, df in self.custom_data_df.items():
            total_performance:float = 0
            df:DataFrame = df.loc[df.index = self.max_missing_days:
                if data_title in self.measures:
                    self.measures.pop(data_title)
                continue
            
            # shifted values for measures
            measure:float = np.log(df.iloc[-2, df.columns.isin(list(returns_df.columns))]) - np.log(df.iloc[-i - 1, df.columns.isin(list(returns_df.columns))]) \
                            if data_title in self.custom_data_index else df.iloc[-2, df.columns.isin(list(returns_df.columns))] - df.iloc[-i - 1, df.columns.isin(list(returns_df.columns))]
            
            # rank based on measures
            df_ranks:DataFrame = pd.DataFrame([measure.rank()]).dropna(axis=1)
            measure_df = returns_df
            for country in df_ranks:
                weight:float = (df_ranks[country] - df_ranks.mean(axis=1)) / ((df_ranks.max(axis=1) - df_ranks.min(axis=1)) / 2)
                if country in returns_df:
                    country_performance = returns_df[country] * weight
                    total_performance += country_performance
                weights_df[country] = weight
            if data_title not in self.measures:
                self.measures[data_title] = {}
            if i not in self.measures[data_title]:
                self.measures[data_title][i] = deque(maxlen=self.volatility_period)
            self.measures[data_title][i].append((total_performance, weights_df))
    if self.Time.month % 3 != 0: 
        return
    traded_portfolio_portion:Dict[str, float] = {}
    if any([any([len(data) == data.maxlen for lb, data in value.items()]) for key, value in self.measures.items()]):
        aggregated_inverse_volatility:float = sum([sum([1 / np.std(list(map(lambda x:x[0][0], v))) for i,v in y.items()]) for x, y in self.measures.items()])
        for variable, lookback in self.measures.items():
            for lb, perf_weights in lookback.items():
                weight:float = (1 / np.std(list(map(lambda x:x[0][0], list(perf_weights))))) / aggregated_inverse_volatility
                for country in perf_weights[-1][1]:
                    portion:float = (self.Portfolio.TotalPortfolioValue / len(self.measures) / len(lookback) / len(perf_weights[-1][1])) * weight 
                    if np.isnan(portion):
                        continue
                    if country not in traded_portfolio_portion:
                        traded_portfolio_portion[country] = 0
                    traded_portfolio_portion[country] += portion
    # trade execution
    invested:List[Symbol] = [x.Key for x in self.Portfolio if x.Value.Invested]
    for symbol in invested:
        if self.symbols[symbol.Value] not in traded_portfolio_portion:
            self.Liquidate(symbol)
    for symbol in list(self.data.keys()):
        if symbol in data and data[symbol]:
            if self.symbols[symbol.Value] in traded_portfolio_portion:
                quantity:float = (traded_portfolio_portion[self.symbols[symbol.Value]] // data[symbol].Price) - self.Portfolio[symbol].Quantity
                self.MarketOrder(symbol, quantity)
