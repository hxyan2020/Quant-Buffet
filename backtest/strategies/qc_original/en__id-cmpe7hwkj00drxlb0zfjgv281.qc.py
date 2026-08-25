# Original QuantConnect / library Python
# locale=en slug="股票中的跨类别情绪反转策略"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

from AlgorithmImports import *
from typing import List, Dict
from pandas.core.frame import DataFrame
import statsmodels.api as sm
from dateutil.relativedelta import relativedelta
# endregion

class CrossSectionalMoodReversalStrategyinEquities(QCAlgorithm):

def Initialize(self):
    self.SetStartDate(2000, 1, 1)
    self.SetCash(100000)

    self.market:Symbol = self.AddEquity('SPY', Resolution.Daily).Symbol

    self.regression_year_window:int = 10
    self.period:int = self.regression_year_window * 12
    self.noncongruent_period:int = 5
    self.historical_pred_high_ret:Dict[Symbol, RollingWindow] = {}
    self.historical_pred_low_ret:Dict[Symbol, RollingWindow] = {}
    
    self.low_mood_months:List[int] = [1, 3]
    self.high_mood_months:List[int] = [9, 10]

    self.weight:Dict[Symbol, float] = {}
    self.quantile:int = 10

    self.leverage:int = 3
    self.fundamental_count:int = 500
    self.selection_flag:bool = False
    self.rebalance_flag:bool = False
    self.UniverseSettings.Resolution = Resolution.Daily
    self.AddUniverse(self.FundamentalSelectionFunction)
    self.Settings.MinimumOrderMarginPortfolioPercentage = 0.
    self.Schedule.On(self.DateRules.MonthStart(self.market), self.TimeRules.AfterMarketOpen(self.market), self.Selection)

def OnSecuritiesChanged(self, changes: SecurityChanges) -> None:
    for security in changes.RemovedSecurities:
        if security.Symbol in self.historical_pred_low_ret:
            del self.historical_pred_low_ret[security.Symbol]

        if security.Symbol in self.historical_pred_high_ret:
            del self.historical_pred_high_ret[security.Symbol]
        
    for security in changes.AddedSecurities:
        security.SetFeeModel(CustomFeeModel())
        security.SetLeverage(self.leverage)

def FundamentalSelectionFunction(self, fundamental: List[Fundamental]) -> List[Symbol]:
    if not self.selection_flag:
        return Universe.Unchanged
    self.selection_flag = False

    selected:List[Symbol] = [x.Symbol
        for x in sorted([x for x in fundamental if x.HasFundamentalData and x.Market == 'usa' and x.MarketCap != 0 and \
            ((x.SecurityReference.ExchangeId == "NYS") or (x.SecurityReference.ExchangeId == "NAS") or (x.SecurityReference.ExchangeId == "ASE"))],
            key = lambda x: x.DollarVolume, reverse = True)[:self.fundamental_count]]
   
    is_high_month:bool = False
    is_low_month:bool = False

    history:DataFrame = self.History(selected, start=self.Time.date() - relativedelta(months=self.period), end=self.Time.date())['close'].unstack(level=0)
    history = history.groupby(pd.Grouper(freq='M')).last()
    if len(history) >= self.period:
        history = history.iloc[-self.period:]
        history.index = history.index.to_pydatetime()
        
        asset_returns:DataFrame = history.pct_change().iloc[1:]
        year_range:List[int] = list(range(self.Time.year - self.regression_year_window, self.Time.year + 1))

        if self.Time.month == self.high_mood_months[1] + 1:
            is_high_month = True
            x_var_months:List[int] = self.high_mood_months
            y_var_months:List[int] = self.low_mood_months
        elif self.Time.month == self.low_mood_months[1] + 1:
            is_low_month = True
            x_var_months:List[int] = self.low_mood_months
            y_var_months:List[int] = self.high_mood_months
            
        # regression X variable data
        x_prespecified_months:List[datetime.date] = []
        for year in [asset_returns[asset_returns.index.year == year].index for year in year_range]:
            for date in year:
                if date.month in x_var_months:
                    x_prespecified_months.append(date.date())

        # regression Y variable data
        y_prespecified_months:List[datetime.date] = []
        for year in [asset_returns[asset_returns.index.year == year].index for year in year_range]:
            for date in year:
                if date.month in y_var_months:
                    y_prespecified_months.append(date.date())

        # average two relevant months
        x:np.ndarray = asset_returns.loc[x_prespecified_months].rolling(2).mean().iloc[::2, :].iloc[1:].values.T
        y:np.ndarray = asset_returns.loc[y_prespecified_months].rolling(2).mean().iloc[::2, :].iloc[1:].values.T

        pred_ret:Dict[Symbol, float] = {}
        for i, asset in enumerate(list(asset_returns.columns)):
            asset_s:Symbol = self.Symbol(asset)

            if not (any(np.isnan(value) for value in x[i]) or any(np.isnan(value) for value in x[i])):
                model = self.multiple_linear_regression(x[i][:-1], y[i][1:])
                pred_ret_:float = model.predict(x[i][-1])[0]
                
                # store mood month predicted non-congruent return
                if is_low_month:
                    if asset_s not in self.historical_pred_low_ret:
                        self.historical_pred_low_ret[asset_s] = RollingWindow[float](self.noncongruent_period)
                    self.historical_pred_low_ret[asset_s].Add(pred_ret_)
                    mood_month_storage:Dict[Symbol, RollingWindow] = self.historical_pred_high_ret

                if is_high_month:
                    if asset_s not in self.historical_pred_high_ret:
                        self.historical_pred_high_ret[asset_s] = RollingWindow[float](self.noncongruent_period)
                    self.historical_pred_high_ret[asset_s].Add(pred_ret_)
                    mood_month_storage:Dict[Symbol, RollingWindow] = self.historical_pred_low_ret

                # sort all selected number of stocks into deciles based on their average historical non-congruent mood month return during years t−2 through t−5
                if asset_s in mood_month_storage and mood_month_storage[asset_s].IsReady:
                    avg_mood_return:float = np.mean(list(mood_month_storage[asset_s])[2:])
                    pred_ret[asset_s] = avg_mood_return

        # sort by mean predicted non-congruent return
        if len(pred_ret) >= self.quantile:
            sorted_by_ret:List[Symbol] = sorted(pred_ret, key=pred_ret.get)
            quantile:int = int(len(sorted_by_ret) / self.quantile)
            long:List[Symbol] = sorted_by_ret[-quantile:]
            short:List[Symbol] = sorted_by_ret[:quantile]

            # EW
            for i, portfolio in enumerate([long, short]):
                for symbol in portfolio:
                    self.weight[symbol] = ((-1) ** i) / len(portfolio)

    return list(self.historical_pred_low_ret.keys()) if is_low_month else list(self.historical_pred_high_ret.keys())

def OnData(self, data: Slice) -> None:
    if not self.rebalance_flag:
        return
    self.rebalance_flag = False

    if not(self.Time.month in self.low_mood_months + self.high_mood_months):
        self.Liquidate()
    else:
        for price_symbol, weight in self.weight.items():
            if price_symbol in data and data[price_symbol]:
                self.SetHoldings(price_symbol, weight)

def Selection(self) -> None:
    if self.Time.month in [self.low_mood_months[1] + 1, self.high_mood_months[1] + 1]:
        self.weight.clear()
        self.selection_flag = True

    self.rebalance_flag = True
    
def multiple_linear_regression(self, x:np.ndarray, y:np.ndarray):
    # x:np.ndarray = np.array(x).T
    # x = sm.add_constant(x, prepend=True)
    result = sm.OLS(endog=y, exog=x).fit()
    return result

# custom fee model
class CustomFeeModel(FeeModel):
def GetOrderFee(self, parameters):
    fee:float = parameters.Security.Price * parameters.Order.AbsoluteQuantity * 0.00005
    return OrderFee(CashAmount(fee, "USD"))
