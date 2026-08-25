# Original QuantConnect / library Python
# locale=en slug="卫星发射与股票回报策略"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

from AlgorithmImports import *
from pandas.tseries.offsets import BDay
from collections import deque
import data_tools
import statsmodels.api as sm
import numpy as np
# endregion
class HowSatelliteLaunchesInfluenceStockReturns(QCAlgorithm):
def Initialize(self):
    self.SetStartDate(2010, 1, 1)
    self.SetCash(100000)
    self.market:Symbol = self.AddEquity('SPY', Resolution.Daily).Symbol
    ff_tickers:List[str] = [
        'fama_french_5_market_eq',
        'fama_french_5_investment_eq',
        'fama_french_5_profitability_eq',
        'fama_french_5_size_eq',
        'fama_french_5_value_eq',
    ]
    self.ff_factors:List[Symbol] = [self.AddData(data_tools.FFFactorsEQ, ff_ticker, Resolution.Daily).Symbol for ff_ticker in ff_tickers]
    self.market_ff:Symbol = self.ff_factors[0]
    self.traded_portfolio_portion:Dict[Symbol, float] = {}
    self.data:Dict[Symbol, deque] = {}
    self.overpriced_betas:Dict[Symbol, float] = {}
    self.underpriced_betas:Dict[Symbol, float] = {}
    
    self.stocks_to_liquidate:List[data_tools.HoldingItem] = []
    self.active_coarse:list[CoarseFundamental] = []
    # we employ one-year data up to 10 days prior to the event (i.e., from t – 375 to t – 10)
    self.market_period:int = 375
    self.pre_launch_period:int = 2      # [-2, 0] holding period @table 8
    self.t_10:int = 10 - self.pre_launch_period
    self.holding_period:int = 3         # days [-2, -1, 0] before launch
    self.quantile:int = 5
    self.leverage:int = 5
    self.coarse_count:int = 500
    # load Satelite launch dates
    # Source: https://en.wikipedia.org/wiki/2000_in_spaceflight
    csv_string_file:str = self.Download('data.quantpedia.com/backtesting_data/calendar/spaceflight_dates.csv')
    dates:str = csv_string_file.split('\r\n')
    self.launch_dates:List[datetime.date] = [datetime.strptime(x, "%Y-%m-%d") - BDay(self.pre_launch_period) for x in dates[:-1]]
    self.selection_flag:bool = False
    self.rebalance_flag:bool = False
    self.UniverseSettings.Resolution = Resolution.Daily
    self.AddUniverse(self.CoarseSelectionFunction, self.FineSelectionFunction)
    self.Schedule.On(self.DateRules.MonthStart(self.market), self.TimeRules.AfterMarketOpen(self.market), self.Selection)
def OnSecuritiesChanged(self, changes:SecurityChanges) -> None:
    for security in changes.AddedSecurities:
        security.SetFeeModel(data_tools.CustomFeeModel())
        security.SetLeverage(self.leverage)
def CoarseSelectionFunction(self, coarse:List[CoarseFundamental]) -> List[Symbol]:
    # update the returns every day
    ff_factors_last_update_date:datetime.date = data_tools.FFFactorsEQ._last_update_date
    # FF data is still comming in
    if all([self.Securities[x].GetLastData() for x in self.ff_factors]) and self.Time.date() >= ff_factors_last_update_date:
        self.Liquidate()
        return Universe.Unchanged
    # store daily FF prices
    for symbol_ff in self.ff_factors:
        if symbol_ff in self.data:
            price = self.Securities[symbol_ff].Price
            if symbol_ff == self.market_ff:
                self.data[symbol_ff].update_daily_return(self.Time, price)
            else:
                self.data[symbol_ff].update_value(self.Time, price)
    # store daily stock prices
    for stock in coarse:
        symbol:Symbol = stock.Symbol
        if symbol in self.data:
            self.data[symbol].update_daily_return(self.Time , stock.AdjustedPrice)
    if self.Time in self.launch_dates:
        self.rebalance_flag = True
        return self.active_coarse
    # selection on month start
    if not self.selection_flag:
        return Universe.Unchanged
    self.selection_flag = False
    self.active_coarse:List[Symbol] = [x.Symbol
        for x in sorted([x for x in coarse if x.HasFundamentalData and x.Market == 'usa'],
            key = lambda x: x.DollarVolume, reverse = True)[:self.coarse_count]]
    # selected = [x.Symbol for x in coarse if x.HasFundamentalData and x.Market == 'usa']
    
    # price warmup
    for symbol in self.active_coarse:
        if symbol in self.data:
            continue
        
        self.data[symbol] = data_tools.SymbolData(self.market_period)
        history:DataFrame = self.History(symbol, self.market_period, Resolution.Daily)
        if history.empty:
            self.Log(f"Not enough data for {symbol} yet.")
            continue
        closes:pd.Series = history.loc[symbol].close
        for time, close in closes.iteritems():
            self.data[symbol].update_daily_return(time, close)
    for symbol_ff in self.ff_factors:
        if symbol_ff not in self.data:
            self.data[symbol_ff] = data_tools.SymbolData(self.market_period)
            history:DataFrame = self.History(symbol_ff, self.market_period, Resolution.Daily)
            if not history.empty:
                values:pd.Series = history.loc[symbol_ff].value
                for time, value in values.iteritems():
                    if symbol_ff == self.market_ff:
                        self.data[symbol_ff].update_daily_return(time, value)
                    else:
                        self.data[symbol_ff].update_value(time, value)
            else:
                self.Log(f"Not enough data for {symbol_ff} yet.")
    return [x for x in self.active_coarse if self.data[x].is_ready()]
def FineSelectionFunction(self, fine:List[FineFundamental]) -> List[Symbol]:
    fine = [x for x in fine if x.MarketCap != 0 and \
            (x.SecurityReference.ExchangeId == 'NYS') or (x.SecurityReference.ExchangeId == 'NAS') or (x.SecurityReference.ExchangeId == 'ASE')]
    fine:Dict[Symbol, FineFundamental] = {x.Symbol: x for x in fine}
    if len(fine) != 0:
        last_start:datetime.date = (self.Time.date() - timedelta(self.market_period))
        last_end:datetime.date = (self.Time.date() - timedelta(self.t_10))
        if not all([self.data[x].is_ready() for x in self.ff_factors]):
            return Universe.Unchanged
        
        # stock returns
        daily_returns_by_stock:Dict[Symbol, List[Tuple[datetime, float]]] = {sym : sym_data.get_daily_returns(last_start, last_end) for sym, sym_data in self.data.items() if sym_data.is_ready() and sym in fine}
        stock_daily_returns:List = list(zip(*[[i[1] for i in x] for x in daily_returns_by_stock.values()]))
        
        # FF factors values
        launch_dates:List[datetime] = pd.to_datetime(self.launch_dates)
        ff_returns_with_dt, ff_size_with_dt, ff_investment_with_dt, ff_profitability_with_dt, ff_book_to_market_with_dt = [np.array(self.data[x].get_daily_returns(last_start, last_end)) for x in self.ff_factors]
        ff_returns = ff_returns_with_dt[:, 1]
        ff_size = ff_size_with_dt[:, 1]
        ff_investment = ff_investment_with_dt[:, 1]
        ff_profitability = ff_profitability_with_dt[:, 1]
        ff_book_to_market = ff_book_to_market_with_dt[:, 1]
        
        # regression X variables
        transformed_array = np.column_stack((
            ff_returns,
            ff_returns * np.where(ff_returns >= 0, 1, 0),
            ff_returns * np.where(ff_returns = self.quantile:
            sorted_overprized_betas:List[FineFundamental] = sorted(overpriced_betas, key=overpriced_betas.get)
            sorted_underprized_betas:List[FineFundamental] = sorted(underpriced_betas, key=underpriced_betas.get)
            quantile:int = int(len(sorted_overprized_betas) / self.quantile)
            long_underprized:List[FineFundamental] = sorted_underprized_betas[-quantile:]
            short_overprized:List[FineFundamental] = sorted_overprized_betas[-quantile:]
            # calculate weights based on values
            sum_long:float = sum([x.MarketCap for x in long_underprized])
            for stock in long_underprized:
                self.traded_portfolio_portion[stock.Symbol] = (stock.MarketCap / sum_long) * (self.Portfolio.TotalPortfolioValue / self.holding_period)
            sum_short:float = sum([x.MarketCap for x in short_overprized])
            for stock in short_overprized:
                self.traded_portfolio_portion[stock.Symbol] = (-stock.MarketCap / sum_short) * (self.Portfolio.TotalPortfolioValue / self.holding_period)
    # return list(fine.keys())
    return list(self.traded_portfolio_portion.keys())
def OnData(self, data: Slice) -> None:
    items_to_remove:List[data_tools.HoldingItem] = []
    # execute order and hold for holding period
    for item in self.stocks_to_liquidate:
        item._holding_period += 1
        if item._holding_period >= self.holding_period:
            self.MarketOrder(item._symbol, -item._quantity)
            items_to_remove.append(item)    
    # remove from collection
    for item in items_to_remove:
        self.stocks_to_liquidate.remove(item)    
    if not self.rebalance_flag:
        return
    self.rebalance_flag = False
    # execute order
    for price_symbol, portfolio_portion in self.traded_portfolio_portion.items():
        if price_symbol in data and data[price_symbol]:
            final_quantity:int = portfolio_portion // data[price_symbol].Price
            if portfolio_portion != 0:
                self.MarketOrder(price_symbol, final_quantity)
                self.stocks_to_liquidate.append(data_tools.HoldingItem(price_symbol, final_quantity))
    self.traded_portfolio_portion.clear()
def Selection(self) -> None:
    self.selection_flag = True
def multiple_linear_regression(self, x:np.ndarray, y:np.ndarray):
    # x:np.ndarray = np.array(x).T
    x = sm.add_constant(x, prepend=True)
    result = sm.OLS(endog=y, exog=x).fit()
    return result
