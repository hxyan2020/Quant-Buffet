# Original QuantConnect / library Python
# locale=zh slug="顺周期股票与预期未来经济状况"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

from AlgorithmImports import *
import data_tools
from typing import List, Dict
from pandas.core.frame import DataFrame
from pandas.core.series import Series
class ProCyclicalStocksandExpectedFutureEconomicConditions(QCAlgorithm):
def Initialize(self) -> None:
    self.SetStartDate(2000, 1, 1)
    self.SetCash(100000)
    
    self.period: int = 36
    self.min_daily_perfs: int = 15
    self.production_beta_threshold: int = 0
    self.p_value_threshold: int = 0.05
    self.leverage: int = 5
    self.quantile: int = 5
    self.min_share_price: int = 5
    
    self.long: List[Symbol] = []
    self.short: List[Symbol] = []
    self.monthly_prices: Dict[Symbol, RollingWindow] = {}
    symbol: Symbol = self.AddEquity('SPY', Resolution.Daily).Symbol
    
    self.production_index: Symbol = self.AddData(data_tools.QuantpediaIndustrialProduction, 'INDPRO', Resolution.Daily).Symbol # daily data
    
    self.fama_french: Symbol = self.AddData(
        data_tools.QuantpediaFamaFrench, 'fama_french_5_factor', Resolution.Daily).Symbol
    self.fama_french_momentum: Symbol = self.AddData(
        data_tools.QuantpediaFamaFrenchMomentum, 'fama_french_5_momentum', Resolution.Daily).Symbol
    
    self.ff_factor_names: List[str] = ['market', 'size', 'value', 'momentum']
    self.factors: Dict[str, data_tools.FactorData|data_tools.FactorDataFF] = { 'production': data_tools.FactorData(self.period + 1) }
    for ff_factor_name in self.ff_factor_names:
        self.factors[ff_factor_name] = data_tools.FactorDataFF(self.period)
    
    self.fundamental_count: int = 1000
    self.fundamental_sorting_key = lambda x: x.DollarVolume
    self.selection_flag: bool = False
    self.settings.daily_precise_end_time = False
    self.Settings.MinimumOrderMarginPortfolioPercentage = 0.
    self.UniverseSettings.Resolution = Resolution.Daily
    self.AddUniverse(self.FundamentalSelectionFunction)
    self.Schedule.On(self.DateRules.MonthStart(symbol), self.TimeRules.AfterMarketOpen(symbol), self.Selection)
def OnSecuritiesChanged(self, changes: SecurityChanges) -> None:
    for security in changes.AddedSecurities:
        security.SetFeeModel(data_tools.CustomFeeModel())
        security.SetLeverage(self.leverage)
        
def FundamentalSelectionFunction(self, fundamental: List[Fundamental]) -> List[Symbol]:
    custom_data_last_update_date: Dict[Symbol, datetime.date] = data_tools.LastDateHandler.get_last_update_date()
    if any([self.Securities[symbol].GetLastData() and self.Time.date() > custom_data_last_update_date[symbol] for symbol in [self.production_index, self.fama_french, self.fama_french_momentum]]):
        self.Liquidate()
        return Universe.Unchanged
    if not self.selection_flag:
        return Universe.Unchanged
    curr_date: datetime.date = self.Time.date()
    # update monthly prices
    for stock in fundamental:
        symbol: Symbol = stock.Symbol
        if symbol in self.monthly_prices:
            self.monthly_prices[symbol].Add(stock.AdjustedPrice)
    selected: List[Fundamental] = [
        x for x in fundamental 
        if x.HasFundamentalData 
        and x.MarketCap != 0 
        and x.Price > self.min_share_price 
        and x.Market == 'usa'
    ]
    
    if len(selected) > self.fundamental_count:
        selected = [x for x in sorted(selected, key=self.fundamental_sorting_key, reverse=True)[:self.fundamental_count]]
    warmed_up_stocks: List[Symbol] = []
    for stock in selected:
        symbol: Symbol = stock.Symbol
        if symbol in self.monthly_prices:
            continue
        
        self.monthly_prices[symbol] = RollingWindow[float](self.period + 1)
        history: DataFrame = self.History(symbol, (self.period + 1) * 21, Resolution.Daily)
        if history.empty:
            continue
        closes: Series = history.loc[symbol].close
        grouped_by_years: Series = closes.groupby(closes.index.year)
        for group_id, grouped_timestamps in grouped_by_years.groups.items():
            datetime_series:pd.Series = pd.to_datetime(pd.Series(grouped_timestamps.date), format='%Y-%m-%d')
            first_dates_in_months = datetime_series.groupby(datetime_series.dt.month).head(1)
            
            for timestamp in first_dates_in_months:
                close: float = closes.loc[timestamp]
                self.monthly_prices[symbol].Add(close)
        if self.monthly_prices[symbol].IsReady:
            warmed_up_stocks.append(stock)
    all_factors_ready_flag: bool = True
    for factor_name, factor_data in self.factors.items():
        if factor_name in self.ff_factor_names:
            if factor_data.daily_perfs_ready(self.min_daily_perfs):
                factor_data.update(curr_date)
            factor_data.reset_daily_perfs()
        if not factor_data.factor_data_ready():
            all_factors_ready_flag = False
    if not all_factors_ready_flag:
        return Universe.Unchanged
    
    # sort by market cap
    if len(selected) > self.fundamental_count:
        sorted_by_market_cap: List[Fundamental] = sorted(selected, key = lambda x: x.MarketCap)
        selected: List[Fundamental] = sorted_by_market_cap[-self.fundamental_count:]
    x: List[List[float]] = [factor_data.get_factor_data() for _, factor_data in self.factors.items()]
    production_index: float = self.factors['production'].get_latest_factor_data_value()
    production_index_sma: float = self.factors['production'].get_factor_data_avg(self.period)
    for stock in warmed_up_stocks:
        symbol: Symbol = stock.Symbol
        
        monthly_prices: np.ndarray = np.array(list(self.monthly_prices[symbol]))
        monthly_returns: np.ndarray = (monthly_prices[:-1] - monthly_prices[1:]) / monthly_prices[1:]
        
        regression_model: RegressionResultWrapper = data_tools.MultipleLinearRegression(x, monthly_returns)

        production_beta: float = regression_model.params[1]
        p_val: float = regression_model.f_pvalue
        # Beta is positive and relation is significant.
        # Source: https://stattrek.com/regression/slope-test.aspx
        if production_beta > self.production_beta_threshold:# and p_val  production_index_sma:
                self.long.append(symbol)
            else:
                self.short.append(symbol)
    return self.long + self.short
def OnData(self, data: Slice) -> None:
    curr_date: datetime.date = self.Time.date()
    if self.production_index in data and data[self.production_index]:
        price: float = data[self.production_index].Value
        self.factors['production'].update(curr_date, price)
    
    if self.fama_french in data and data[self.fama_french] and self.fama_french_momentum in data and data[self.fama_french_momentum]:
        for factor_name in self.ff_factor_names:
            if data[self.fama_french].HasProperty(factor_name):
                ff_factor_daily_perf: float = float(data[self.fama_french].GetProperty(factor_name))
                self.factors[factor_name].update_daily_perfs(curr_date, ff_factor_daily_perf / 100.)
            elif data[self.fama_french_momentum].HasProperty(factor_name):
                ff_factor_daily_perf: float = float(data[self.fama_french_momentum].GetProperty(factor_name))
                self.factors[factor_name].update_daily_perfs(curr_date, ff_factor_daily_perf / 100.)
                
    if not self.selection_flag:
        return
    self.selection_flag = False
    # trade execution
    targets: List[PortfolioTarget] = []
    for i, portfolio in enumerate([self.long, self.short]):
        for symbol in portfolio:
            if symbol in data and data[symbol]:
                targets.append(PortfolioTarget(symbol, ((-1) ** i) / len(portfolio)))
    
    self.SetHoldings(targets, True)
    self.long.clear()
    self.short.clear()

def Selection(self) -> None:
    self.selection_flag = True
