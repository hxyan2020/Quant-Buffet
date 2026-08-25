# Original QuantConnect / library Python
# locale=en slug="firm-level-investor-sentiment-factor-in-us"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

from AlgorithmImports import *
from pandas.core.frame import DataFrame
from typing import List, Dict
import statsmodels.api as sm
from dateutil.relativedelta import relativedelta
# endregion

class FirmLevelInvestorSentimentFactorInUS(QCAlgorithm):

def Initialize(self) -> None:
    self.SetStartDate(2010, 1, 1)
    self.SetCash(100000)

    self.market:Symbol = self.AddEquity("SPY", Resolution.Daily).Symbol

    self.periods:List[int] = [3, 60]
    self.long_period:int = 60
    self.short_period:int = 3
    self.rolling_period:int = 2
    self.short_term_stock_beta:Dict[Symbol, RollingWindow] = {}
    self.long_term_stock_beta:Dict[Symbol, RollingWindow] = {}
    self.long_term_industry_beta:Dict[str, RollingWindow] = {}

    self.weight:Dict[Symbol, float] = {}
    self.quantile:int = 10
    self.min_share_price:int = 5

    self.leverage:int = 3
    self.fundamental_count:int = 500
    self.selection_flag:bool = False
    self.UniverseSettings.Resolution = Resolution.Daily
    self.Settings.MinimumOrderMarginPortfolioPercentage = 0.
    self.AddUniverse(self.FundamentalSelectionFunction)
    self.Schedule.On(self.DateRules.MonthEnd(self.market), self.TimeRules.BeforeMarketClose(self.market), self.Selection)

def OnSecuritiesChanged(self, changes: SecurityChanges) -> None:
    for security in changes.RemovedSecurities:
        if security.Symbol in self.short_term_stock_beta:
            del self.short_term_stock_beta[security.Symbol]
        if security.Symbol in self.long_term_stock_beta:
            del self.long_term_stock_beta[security.Symbol]

    for security in changes.AddedSecurities:
        security.SetFeeModel(CustomFeeModel())
        security.SetLeverage(self.leverage)

def FundamentalSelectionFunction(self, fundamental: List[Fundamental]) -> List[Symbol]:
    # monthly selection
    if not self.selection_flag:
        return Universe.Unchanged

    selected:List[Fundamental] = [x for x in sorted([x for x in fundamental if x.HasFundamentalData and x.Market == 'usa' and x.AdjustedPrice >= self.min_share_price and \
        x.AssetClassification.MorningstarIndustryGroupCode != 0 and x.MarketCap != 0 and \
        (x.SecurityReference.ExchangeId == 'NYS') or (x.SecurityReference.ExchangeId == 'NAS') or (x.SecurityReference.ExchangeId == 'ASE')], 
        key = lambda x: x.DollarVolume, reverse = True)][:self.fundamental_count]

    history:DataFrame = self.History(list(map(lambda x: x.Symbol, selected)) + [self.market], start=self.Time.date() - relativedelta(months=self.long_period), end=self.Time.date())['close'].unstack(level=0)
    history = history.groupby(pd.Grouper(freq='M')).last()

    # sort stocks on industry numbers
    industries:Set[MorningstarIndustryGroupCode] = set([x.AssetClassification.MorningstarSectorCode for x in selected])
    grouped_industries:Dict[MorningstarIndustryGroupCode, List[Symbol]] = { industry : [stock.Symbol for stock in selected if stock.AssetClassification.MorningstarSectorCode == industry] for industry in industries }

    # get stock returns and clean up the data
    if len(history) >= self.long_period:
        history = history.iloc[-self.long_period:]
        history.index = history.index.to_pydatetime()

        asset_returns:DataFrame = history.pct_change().iloc[1:]

        stock_returns = asset_returns.loc[:, asset_returns.columns != self.market].tail(-1)
        asset_returns['spy_lag'] = asset_returns[self.market].shift(1)
        asset_returns = asset_returns.iloc[1:]

        industry_df:DataFrame = pd.DataFrame(index=asset_returns.index)

        for industry_code in grouped_industries:
            ind_symbols:List[Symbol] = grouped_industries[industry_code]
            if all(symbol in asset_returns.columns for symbol in ind_symbols):
                industry_df[industry_code] = asset_returns[ind_symbols].mean(axis=1)

        # run industry regression
        x:np.ndarray = asset_returns[[self.market, 'spy_lag']].values
        y:np.ndarray = industry_df.values
        model = self.multiple_linear_regression(x, y)
        beta_values:np.ndarray = sum(model.params[1:])

        for i, industry in enumerate(industry_df):
            if industry not in self.long_term_industry_beta:
                self.long_term_industry_beta[industry] = RollingWindow[float](self.rolling_period)
            self.long_term_industry_beta[industry].Add(beta_values[i])

        # run stock regression
        for period in self.periods:
            x:np.ndarray = asset_returns[[self.market, 'spy_lag']][-period:].values
            y:np.ndarray = stock_returns[-period:].values
            model = self.multiple_linear_regression(x, y)
            beta_values:np.ndarray = sum(model.params[1:])

            for i, asset in enumerate(stock_returns):
                asset_s:Symbol = self.Symbol(asset)

                # fill rolling windows with data
                if asset_s not in self.short_term_stock_beta or asset_s not in self.long_term_stock_beta:
                    if beta_values[i] != 0 and beta_values[i] is not None:
                        if period == self.periods[0]:
                            self.short_term_stock_beta[asset_s] = RollingWindow[float](self.rolling_period)
                        else:
                            self.long_term_stock_beta[asset_s] = RollingWindow[float](self.rolling_period)

                if beta_values[i] != 0 and beta_values[i] is not None:
                    if period == self.periods[0]:
                        self.short_term_stock_beta[asset_s].Add(beta_values[i])
                    else:
                        self.long_term_stock_beta[asset_s].Add(beta_values[i])

    beta_by_symbol:Dict[Fundamental, float] = {}

    # FIS calculation
    for stock in selected:
        symbol:Symbol = stock.Symbol

        if symbol in self.short_term_stock_beta or symbol in self.long_term_stock_beta:
            if self.short_term_stock_beta[symbol].IsReady and self.long_term_stock_beta[symbol].IsReady:
                bc:float = (self.short_term_stock_beta[symbol][0] - self.short_term_stock_beta[symbol][1]) / self.long_term_stock_beta[symbol][1]

                for industry in grouped_industries:
                    if industry in self.long_term_industry_beta:
                        if symbol in grouped_industries[industry] and self.long_term_industry_beta[industry].IsReady:
                            dc:float = (self.short_term_stock_beta[symbol][0] - self.long_term_industry_beta[(industry)][1]) / self.long_term_industry_beta[industry][1]
                            beta_by_symbol[stock] = bc * dc

    # sort by beta and divide to upper decile and lower decile
    if len(beta_by_symbol) >= self.quantile:
        sorted_by_beta:List[Fundamental] = sorted(beta_by_symbol, key=beta_by_symbol.get)
        quantile:int = int(len(sorted_by_beta) / self.quantile)
        long:List[Fundamental] = sorted_by_beta[:quantile]
        short:List[Fundamental] = sorted_by_beta[-quantile:]

        # calculate weights based on values
        for i, portfolio in enumerate([long, short]):
            mc_sum:float = sum(list(map(lambda stock: stock.MarketCap, portfolio)))
            for stock in portfolio:
                self.weight[stock.Symbol] = ((-1)**i) * stock.MarketCap / mc_sum

    return list(map(lambda x: x.Symbol, selected))

def OnData(self, data: Slice) -> None:
    # monthly rebalance
    if not self.selection_flag:
        return
    self.selection_flag = False

    portfolio:List[PortfolioTarget] = [PortfolioTarget(symbol, w) for symbol, w in self.weight.items() if symbol in data and data[symbol]]
    self.SetHoldings(portfolio, True)

    self.weight.clear()

def Selection(self) -> None:
    self.selection_flag = True

def multiple_linear_regression(self, x:np.ndarray, y:np.ndarray):
    # x:np.ndarray = np.array(x).T
    x = sm.add_constant(x, prepend=True)
    result = sm.OLS(endog=y, exog=x).fit()
    return result

# Custom fee model.
class CustomFeeModel(FeeModel):
def GetOrderFee(self, parameters):
    fee = parameters.Security.Price * parameters.Order.AbsoluteQuantity * 0.00005
    return OrderFee(CashAmount(fee, "USD"))
