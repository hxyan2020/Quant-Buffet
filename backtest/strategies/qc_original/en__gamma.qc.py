# Original QuantConnect / library Python
# locale=en slug="gamma-因子溢价策略"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

from AlgorithmImports import *
import data_tools
import statsmodels.api as sm
import numpy as np
from dateutil.relativedelta import relativedelta
# endregion

class GammaFactorPremium(QCAlgorithm):

def Initialize(self):
    self.SetStartDate(2010, 1, 1)
    self.SetCash(100_000)

    self.tickers_to_ignore:List[str] = ['TOPS']

    self.market:Symbol = self.AddEquity('SPY', Resolution.Daily).Symbol
    self.world_market:Symbol = self.AddEquity('VT', Resolution.Daily).Symbol
    self.asia_market:Symbol = self.AddEquity('ASHR', Resolution.Daily).Symbol
    self.vix:Symbol = self.AddData(CBOE, "VIX").Symbol
    # self.cpi_us:symbol = self.AddData(data_tools.QuandlValue, 'RATEINF/CPI_USA', Resolution.Daily).Symbol
    self.market_ff:Symbol = self.AddData(data_tools.MarketEQ, 'ff_market', Resolution.Daily).Symbol

    self.custom_data_monthly:List[str] = ['GS3M', 'GS1', 'GS2', 'GS10', 'UMCSENT', 'RTWEXBGS', 'BOGMBASE', 'CPIAUCSL']
    self.custom_data_weekly:List[str] = ['WALCL', 'ECBASSETSW']
    self.custom_data_daily:List[str] = ['DTWEXBGS', 'T10Y2Y', 'DCOILWTICO']
    self.currencies:List[str] = ['USDEUR', 'CNHUSD']

    # subscribe data
    self.currencies_symbol:List[Symbol] = [self.AddForex(x, Resolution.Daily, Market.Oanda).Symbol for x in self.currencies]

    self.monthly_custom_data:List[Symbol] = [self.AddData(data_tools.MonthlyQPData, ticker, Resolution.Daily).Symbol for ticker in self.custom_data_monthly]
    self.weekly_custom_data:List[Symbol] = [self.AddData(data_tools.WeeklyQPData, ticker, Resolution.Daily).Symbol for ticker in self.custom_data_weekly]
    self.daily_custom_data:List[Symbol] = [self.AddData(data_tools.DailyQPData, ticker, Resolution.Daily).Symbol for ticker in self.custom_data_daily]

    self.custom_data:List[Symbol] = self.monthly_custom_data + self.weekly_custom_data + self.daily_custom_data
    self.qc_data:List[Symbol] = [self.market, self.asia_market, self.vix] + self.currencies_symbol

    self.data:Dict[Symbol, float] = {}
    self.convex_stocks:List[Symbol] = []
    self.concave_stocks:List[Symbol] = []
    self.xma_factor_returns:List[float] = []

    self.period:int = 36
    self.quantile:int = 10
    self.leverage:int = 5
    self.threshold:int = 12

    self.traded_portolio:None|List[Symbol] = None

    self.fundamental_sorting_key = lambda x: x.MarketCap
    self.fundamental_count:int = 3000

    self.selection_flag:bool = False
    self.rebalance_flag:bool = False
    self.Settings.MinimumOrderMarginPortfolioPercentage = 0
    self.UniverseSettings.Resolution = Resolution.Daily
    self.AddUniverse(self.FundamentalSelectionFunction)
    self.Schedule.On(self.DateRules.MonthStart(self.market), self.TimeRules.AfterMarketOpen(self.market), self.Selection)

def OnSecuritiesChanged(self, changes: SecurityChanges) -> None:
    for security in changes.AddedSecurities:
        security.SetFeeModel(data_tools.CustomFeeModel())
        security.SetLeverage(self.leverage)

    for security in changes.RemovedSecurities:
        if security.Symbol in self.data:
            self.data.pop(security.Symbol)
        if security.Symbol in self.convex_stocks:
            self.convex_stocks.remove(security.Symbol)
        if security.Symbol in self.concave_stocks:
            self.concave_stocks.remove(security.Symbol)

def FundamentalSelectionFunction(self, fundamental: List[Fundamental]) -> List[Symbol]:
    # selected on month start
    if not self.selection_flag:
        return Universe.Unchanged
    self.selection_flag = False

    market_ff_last_update_date:datetime.date = data_tools.MarketEQ._last_update_date
    monthly_custom_data_last_update_date:Dict[Symbol, datetime.date] = data_tools.MonthlyQPData._last_update_date
    weekly_custom_data_last_update_date:Dict[Symbol, datetime.date] = data_tools.WeeklyQPData._last_update_date
    daily_custom_data_last_update_date:Dict[Symbol, datetime.date] = data_tools.DailyQPData._last_update_date

    # data is still comming in
    if all([self.Securities[x].GetLastData() for x in self.custom_data]) and any([self.Time.date() >= monthly_custom_data_last_update_date[x] for x in monthly_custom_data_last_update_date]) \
        and any([self.Time.date() >= weekly_custom_data_last_update_date[x] for x in weekly_custom_data_last_update_date]) and any([self.Time.date() >= daily_custom_data_last_update_date[x] for x in daily_custom_data_last_update_date]) \
        and any(symbol not in data and not data[symbol] for symbol in self.qc_data):
        self.Liquidate()
        return Universe.Unchanged

    # FF data is still comming in
    if self.Securities[self.market_ff].GetLastData() and self.Time.date() >= market_ff_last_update_date:
        self.Liquidate()
        return Universe.Unchanged

    # store monthly FF prices
    if self.market_ff in self.data:
        self.data[self.market_ff].update_daily_return(self.Securities[self.market_ff].Price)

    # store daily stock prices
    for stock in fundamental:
        symbol:Symbol = stock.Symbol

        if symbol in self.data:
            self.data[symbol].update_daily_return(stock.AdjustedPrice)

    selected:List[Fundamental] = [x for x in fundamental if x.HasFundamentalData and x.MarketCap != 0 and x.Symbol.Value not in self.tickers_to_ignore]
    if len(selected) > self.fundamental_count:
                selected = [x for x in sorted(selected, key=self.fundamental_sorting_key, reverse=True)[:self.fundamental_count]]
    
    # price warmup
    for stock in selected:
        symbol:Symbol = stock.Symbol
        if symbol in self.data:
            continue
        
        self.data[symbol] = data_tools.SymbolData(self.period)
        history:DataFrame = self.History(symbol, self.period, Resolution.Daily)
        if history.empty:
            self.Log(f"Not enough data for {symbol} yet.")
            continue
        closes:pd.Series = history.loc[symbol].close
        closes = closes.groupby(pd.Grouper(freq='MS')).last()
        for time, close in closes.items():
            self.data[symbol].update_daily_return(close)

    if self.market_ff not in self.data:
        self.data[self.market_ff] = data_tools.SymbolData(self.period)
        history:DataFrame = self.History(self.market_ff, self.period, Resolution.Daily)
        if not history.empty:
            values:pd.Series = history.loc[self.market_ff].value.groupby(pd.Grouper(freq='MS')).last()
            for time, value in values.items():
                self.data[self.market_ff].update_daily_return(value)
        else:
            self.Log(f"Not enough data for {symbol} yet.")

    selected:Dict[Symbol, Fundamental] = {x.Symbol: x for x in selected if self.data[x.Symbol].is_ready()}
    
    # second regression and prediction
    if len(self.convex_stocks) != 0 and len(self.concave_stocks) != 0:
        self.xma_factor_returns.append(np.mean(np.array([self.data[x].get_last_return() for x in self.convex_stocks if self.data[x].is_ready()]), axis=0) - np.mean(np.array([self.data[x].get_last_return() for x in self.concave_stocks if self.data[x].is_ready()]), axis=0))

    if len(self.xma_factor_returns) >= self.threshold:
        history_custom_data:DataFrame = self.History(self.custom_data, start=self.Time.date() - relativedelta(months=len(self.xma_factor_returns)), end=self.Time.date())['value'].unstack(level=0)
        history_qc_data:DataFrame = self.History(self.qc_data, start=self.Time.date() - relativedelta(months=len(self.xma_factor_returns)), end=self.Time.date())['close'].unstack(level=0)
        history_custom_data = history_custom_data.groupby(pd.Grouper(freq='MS')).last()
        history_qc_data = history_qc_data.groupby(pd.Grouper(freq='MS')).last()
        independent_variables:DataFrame = pd.concat([history_custom_data, history_qc_data], axis=1)[-len(self.xma_factor_returns):]

        independent_variables = independent_variables.dropna(axis=1, how='any')

        x:np.ndarray = independent_variables[:-1].values
        y:np.ndarray = self.xma_factor_returns[1:]

        model = self.multiple_linear_regression(x, y)
        predicted_y:np.ndarray = model.predict(sm.add_constant(independent_variables[-1:].values, has_constant='add'))

        self.traded_portfolio = self.convex_stocks if predicted_y > 0 else [self.world_market]

        self.rebalance_flag = True

    if len(selected) != 0:
        if not self.data[self.market_ff].is_ready():
            return Universe.Unchanged

        # stock returns
        returns_by_stock:Dict[Symbol, List[Tuple[datetime, float]]] = {sym : sym_data.get_returns() for sym, sym_data in self.data.items() if sym_data.is_ready() and sym in selected and sym != self.market_ff}
        stock_returns:List = list(zip(*[[i for i in x] for x in returns_by_stock.values()]))
        
        # FF returns
        ff_returns:np.ndarray = np.array(self.data[self.market_ff].get_returns())
        transformed_array = np.column_stack((
            ff_returns,
            ff_returns ** 2))

        transformed_array = np.array(transformed_array, dtype=float)

        # run stock regression
        x:np.ndarray = transformed_array
        y:np.ndarray = stock_returns
        model = self.multiple_linear_regression(x, y)
        gamma_values:np.ndarray = model.params[2]

        gamma:Dict[Symbol, float] = {}
        
        # fetch gamma parameters for each stock
        for i, asset in enumerate(returns_by_stock):
            asset_s:Symbol = self.Symbol(asset)

            # fill data
            if asset in selected:
                if gamma_values[i] is not None:
                    gamma[asset_s] = gamma_values[i]

        # sort by gamma and divide into quantiles
        if len(gamma) >= self.quantile:
            sorted_gamma:List[Symbol] = sorted(gamma.items(), key=lambda x:x[1])
            quantile:int = int(len(gamma) / self.quantile)
            self.convex_stocks = [symbol for symbol, gamma in sorted_gamma][-quantile:]
            self.concave_stocks = [symbol for symbol, gamma in sorted_gamma][:quantile]

    return self.convex_stocks + self.concave_stocks

def OnData(self, data: Slice) -> None:
    if not self.rebalance_flag:
        return Universe.Unchanged
    self.rebalance_flag = False

    # order execution
    # invested: List[Symbol] = [x.Key for x in self.Portfolio if x.Value.Invested]
    # for symbol in invested:
    #     if symbol not in self.traded_portfolio:
    #         self.Liquidate(symbol)

    # for symbol in self.traded_portfolio:
    #     if symbol in data and data[symbol]:
    #         self.SetHoldings(symbol, round(1 / len(self.traded_portfolio), 5))

    targets:List[PortfolioTarget] = [PortfolioTarget(symbol, round(1 / len(self.traded_portfolio), 5)) for symbol in self.traded_portfolio if symbol in data and data[symbol]]      
    self.SetHoldings(targets, True)

def Selection(self) -> None:
    self.selection_flag = True

def multiple_linear_regression(self, x:np.ndarray, y:np.ndarray):
    x = sm.add_constant(x, has_constant='add')
    result = sm.OLS(endog=y, exog=x).fit()
    return result
