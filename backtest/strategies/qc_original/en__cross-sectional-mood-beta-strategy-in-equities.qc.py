# Original QuantConnect / library Python
# locale=en slug="cross-sectional-mood-beta-strategy-in-equities"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

from AlgorithmImports import *
from typing import List, Dict
from pandas.core.frame import DataFrame
import statsmodels.api as sm
from dateutil.relativedelta import relativedelta
# endregion

class CrossSectionalMoodBetaStrategyinEquities(QCAlgorithm):

def Initialize(self):
    self.SetStartDate(2000, 1, 1)
    self.SetCash(100000)

    self.market:Symbol = self.AddEquity('SPY', Resolution.Daily).Symbol

    self.regression_year_window:int = 5
    self.period:int = self.regression_year_window * 12
    self.mood_beta_period:int = 5
    self.historical_mood_beta:Dict[str, RollingWindow] = {}
            
    # four prespecified (January, March, September, and October) months
    self.high_mood_months:List[int] = [1, 3]
    self.low_mood_months:List[int] = [9, 10]

    self.weight:Dict[Symbol, float] = {}
    self.quantile:int = 10

    self.leverage:int = 5
    self.coarse_count:int = 500
    self.selection_flag:bool = False
    self.rebalance_flag:bool = False
    self.UniverseSettings.Resolution = Resolution.Daily
    self.AddUniverse(self.CoarseSelectionFunction, self.FineSelectionFunction)
    self.Schedule.On(self.DateRules.MonthStart(self.market), self.TimeRules.AfterMarketOpen(self.market), self.Selection)

def OnSecuritiesChanged(self, changes:SecurityChanges) -> None:
    for security in changes.RemovedSecurities:
        if security.Symbol in self.historical_mood_beta:
            del self.historical_mood_beta[security.Symbol]
        
    for security in changes.AddedSecurities:
        security.SetFeeModel(CustomFeeModel())
        security.SetLeverage(self.leverage)

def CoarseSelectionFunction(self, coarse:List[CoarseFundamental]) -> List[Symbol]:
    if not self.selection_flag:
        return Universe.Unchanged
    self.selection_flag = False

    selected = [x.Symbol
        for x in sorted([x for x in coarse if x.HasFundamentalData and x.Market == 'usa'],
            key = lambda x: x.DollarVolume, reverse = True)[:self.coarse_count]]
    # selected:List[Symbol] = [x.Symbol for x in coarse if x.HasFundamentalData and x.Market == 'usa']

    return selected
            
def FineSelectionFunction(self, fine:List[FineFundamental]) -> List[Symbol]:
    fine = [x.Symbol for x in fine if x.MarketCap != 0 and \
                ((x.SecurityReference.ExchangeId == "NYS") or (x.SecurityReference.ExchangeId == "NAS") or (x.SecurityReference.ExchangeId == "ASE"))]

    history:DataFrame = self.History(fine + [self.market], start=self.Time.date() - relativedelta(months=self.period), end=self.Time.date())['close'].unstack(level=0)
    history = history.groupby(pd.Grouper(freq='M')).last()

    if len(history) >= self.period:
        history = history.iloc[-self.period:]
        history.index = history.index.to_pydatetime()
        
        asset_returns:DataFrame = history.pct_change().iloc[1:]

        # find best and worst performing months
        market_returns:DataFrame = asset_returns[self.market]
        asset_returns = asset_returns.loc[:, asset_returns.columns != self.market]    # drop market column
        year_range:List[int] = range(self.Time.year - (self.regression_year_window), self.Time.year-1)
        
        # four realized high and low mood months
        highest_performing_months:np.ndarray = list(np.array([market_returns[market_returns.index.year == year].nlargest(2).index.date for year in year_range]).reshape(-1))
        lowest_performing_months:np.ndarray = list(np.array([market_returns[market_returns.index.year == year].nsmallest(2).index.date for year in year_range]).reshape(-1))

        # four prespecified (January, March, September, and October)
        prespecified_months:List[datetime.date] = []
        for year in [market_returns[market_returns.index.year == year].index for year in year_range]:
            for date in year:
                if date.month in [self.high_mood_months + self.low_mood_months]:
                    prespecified_months.append(date.date())

        selected_months:Set[datetime.date] = sorted(set(highest_performing_months + lowest_performing_months + prespecified_months), key=lambda x: x, reverse=False)
        
        # run regression
        x:np.ndarray = market_returns.loc[selected_months].values
        y:np.ndarray = asset_returns.loc[selected_months].values
        model = self.multiple_linear_regression(x, y)
        beta_values:np.ndarray = model.params[1]
        
        # store historical beta values
        beta_by_asset:Dict[str, float] = {}
        assets:List[str] = list(asset_returns.columns)

        for i, asset in enumerate(assets):
            asset_s:Symbol = self.Symbol(asset)
            beta_by_asset[asset_s] = beta_values[i]

        # sort by mean beta
        if len(beta_by_asset) >= self.quantile:
            sorted_by_beta:List[Symbol] = sorted(beta_by_asset, key=beta_by_asset.get, reverse=True)
            quantile:int = int(len(sorted_by_beta) / self.quantile)
            long:List[Symbol] = sorted_by_beta[:quantile]
            short:List[Symbol] = sorted_by_beta[-quantile:]

            # EW
            for asset in long:
                self.weight[asset] = 1. / float(len(long))
            for asset in short:
                self.weight[asset] = -1. / float(len(short))

    return list(self.weight.keys())

def OnData(self, data:Slice) -> None:
    # monthly rebalance
    if not self.rebalance_flag:
        return
    self.rebalance_flag = False

    # long the highest decile and short the lowest mood beta decile during the high-mood months 
    # (January and March) and flip the long and short lags during the low-mood months (September and October)
    trade_direction:float = 0.
    if self.Time.month in self.high_mood_months:
        trade_direction = 1.
    elif self.Time.month in self.low_mood_months:
        trade_direction = -1.

    # rebalance
    for symbol, w in self.weight.items():
        self.SetHoldings(symbol, trade_direction*w)

def Selection(self) -> None:
    # monthly rebalance
    self.rebalance_flag = True

    # yearly selection
    if self.Time.month == 1:
        self.selection_flag = True
        self.weight.clear()

def multiple_linear_regression(self, x:np.ndarray, y:np.ndarray):
    x:np.ndarray = np.array(x).T
    x = sm.add_constant(x)
    result = sm.OLS(endog=y, exog=x).fit()
    return result

# custom fee model
class CustomFeeModel(FeeModel):
def GetOrderFee(self, parameters):
    fee:float = parameters.Security.Price * parameters.Order.AbsoluteQuantity * 0.00005
    return OrderFee(CashAmount(fee, "USD"))
