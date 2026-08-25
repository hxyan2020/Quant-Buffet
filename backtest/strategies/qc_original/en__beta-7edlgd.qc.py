# Original QuantConnect / library Python
# locale=en slug="通过失业率-beta-预测跨类别股票收益策略"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

from AlgorithmImports import *
from pandas.core.frame import DataFrame
from typing import List, Dict
import statsmodels.api as sm
from dateutil.relativedelta import relativedelta
# endregion

class ForecastedUnemploymentBetaPredictstheCrossSectionofStockReturns(QCAlgorithm):

def Initialize(self):
    self.SetStartDate(2005, 1, 1) 
    self.SetCash(100000)
 
    self.market:Symbol = self.AddEquity('SPY', Resolution.Daily).Symbol
    self.ue:Symbol = self.AddData(UnemploymentRate, 'UE', Resolution.Daily).Symbol

    self.period:int = 60
    self.ue_period:int = 72
    self.ue_len_threshold:int = 24
    self.unemployment_beta:Dict[Symbol, float] = {}

    self.weight:Dict[Symbol, float] = {}
    self.quantile:int = 10 

    self.leverage:int = 10
    self.coarse_count:int = 500
    self.selection_flag:bool = False
    self.rebalance_flag:bool = False
    self.UniverseSettings.Resolution = Resolution.Daily
    self.AddUniverse(self.CoarseSelectionFunction, self.FineSelectionFunction)
    self.Schedule.On(self.DateRules.MonthStart(self.market), self.TimeRules.AfterMarketOpen(self.market), self.Selection)

def OnSecuritiesChanged(self, changes:SecurityChanges) -> None:
    for security in changes.AddedSecurities:
        security.SetFeeModel(CustomFeeModel())
        security.SetLeverage(self.leverage)

def CoarseSelectionFunction(self, coarse:List[CoarseFundamental]) -> List[Symbol]:
    # monthly selection
    if not self.selection_flag:
        return Universe.Unchanged
    self.selection_flag = False

    selected:List[Symbol] = [x.Symbol
        for x in sorted([x for x in coarse if x.HasFundamentalData and x.Market == 'usa' and x.AdjustedPrice > 5], 
        key = lambda x: x.DollarVolume, reverse = True)][:self.coarse_count]
    # selected:List[Symbol] = [x.Symbol for x in coarse if x.HasFundamentalData and x.Market == 'usa' and x.AdjustedPrice > 5]

    return selected

def FineSelectionFunction(self, fine:List[FineFundamental]) -> List[Symbol]:
    fine:Dict[Symbol, FineFundamental] = {x.Symbol : x for x in fine if x.MarketCap != 0 and \
                        (x.SecurityReference.ExchangeId == 'NYS') or (x.SecurityReference.ExchangeId == 'NAS') or (x.SecurityReference.ExchangeId == 'ASE')}

    # fine:List[FineFundamental] = [x for x in fine if x.MarketCap != 0 and \
    #                     (x.SecurityReference.ExchangeId == 'NYS') or (x.SecurityReference.ExchangeId == 'NAS') or (x.SecurityReference.ExchangeId == 'ASE')]
    # if len(fine) > self.coarse_count:
    #     fine:Dict[Symbol, FineFundamental] = {x.Symbol : x for x in sorted(fine, key=lambda x:x.MarketCap, reverse=True)[:self.coarse_count]}
    # else:
    #     fine = {x.Symbol : x for x in fine}

    # call history on assets and unemployment rates
    history:DataFrame = self.History(list(fine.keys()) + [self.market], start=self.Time.date() - relativedelta(months=self.period), end=self.Time.date())['close'].unstack(level=0)
    history = history.groupby(pd.Grouper(freq='M')).last()
    history = history.iloc[:-1]

    ue_last_update_date:Dict[Symbol, datetime.date] = UnemploymentRate.get_last_update_date()
    
    # check if uemployment data are still arriving
    if self.Securities[self.ue].GetLastData() and self.ue in ue_last_update_date and self.Time.date() = self.period and len(history_ue) >= self.ue_len_threshold:
            history = history.iloc[-self.period:]
            asset_returns:DataFrame = history.pct_change().iloc[1:]
            history_ue = history_ue.reset_index()

            history_ue.set_index('time', inplace=True)
            
            rolling_mean_ue:DataFrame = history_ue.rolling(window=4).mean()
            rolling_mean_ue = rolling_mean_ue.resample('M').last().ffill()
            x_df:DataFrame = pd.concat((asset_returns[self.market], rolling_mean_ue['value']), axis=1).ffill().dropna()
            stock_returns:DataFrame = asset_returns.loc[:, asset_returns.columns != self.market]
            stock_returns = stock_returns.loc[stock_returns.index.isin(x_df.index)]

            # run regression
            x:np.ndarray = x_df.values
            y:np.ndarray = stock_returns.values
            model = self.multiple_linear_regression(x, y)
            beta_values:np.ndarray = model.params[2]

            for i, asset in enumerate(list(stock_returns.columns)):
                asset_s:Symbol = self.Symbol(asset)

                if asset_s not in beta_by_symbol:
                    if beta_values[i] != 0 and beta_values[i] is not None:
                        beta_by_symbol[fine[asset_s]] = beta_values[i]

        # sort by beta and divide to upper decile and lower decile
        if len(beta_by_symbol) >= self.quantile:
            sorted_by_beta:List[FineFundamental] = sorted(beta_by_symbol, key=beta_by_symbol.get)
            quantile:int = int(len(sorted_by_beta) / self.quantile)
            long:List[FineFundamental] = sorted_by_beta[:quantile]
            short:List[FineFundamental] = sorted_by_beta[-quantile:]

            # calculate weights based on values
            sum_long:float = sum([x.MarketCap for x in long])
            for stock in long:
                self.weight[stock.Symbol] = stock.MarketCap / sum_long

            sum_short:float = sum([x.MarketCap for x in short])
            for stock in short:
                self.weight[stock.Symbol] = -stock.MarketCap / sum_short

    return list(self.weight.keys())

def OnData(self, data: Slice):
    # monthly rebalance
    if not self.rebalance_flag:
        return
    self.rebalance_flag = False

    invested:List[Symbol] = [x.Key for x in self.Portfolio if x.Value.Invested]
    for price_symbol in invested:
        if price_symbol not in self.weight:
            self.Liquidate(price_symbol)
    
    for price_symbol, weight in self.weight.items():
        if price_symbol in data and data[price_symbol]:
            self.SetHoldings(price_symbol, weight)

    self.weight.clear()

def Selection(self):
    self.selection_flag = True
    self.rebalance_flag = True

def multiple_linear_regression(self, x:np.ndarray, y:np.ndarray):
    # x:np.ndarray = np.array(x).T
    x = sm.add_constant(x, prepend=True)
    result = sm.OLS(endog=y, exog=x).fit()
    return result

# Source: https://www.philadelphiafed.org/surveys-and-data/real-time-data-research/survey-of-professional-forecasters
class UnemploymentRate(PythonData):
def GetSource(self, config, date, isLiveMode):
    return SubscriptionDataSource('data.quantpedia.com/backtesting_data/economic/next_q_unemployment_forecast.csv', SubscriptionTransportMedium.RemoteFile, FileFormat.Csv)

_last_update_date:Dict[Symbol, datetime.date] = {}

@staticmethod
def get_last_update_date() -> Dict[Symbol, datetime.date]:
   return UnemploymentRate._last_update_date

def Reader(self, config, line, date, isLiveMode):
    data = UnemploymentRate()
    data.Symbol = config.Symbol

    if not line[0].isdigit(): return None
    split = line.split(';')
    
    # Parse the CSV file's columns into the custom data class
    data.Time = datetime.strptime(split[0], "%Y-%m-%d") + timedelta(days=1)
    data.Value = float(split[1])

    if config.Symbol not in UnemploymentRate._last_update_date:
        UnemploymentRate._last_update_date[config.Symbol] = datetime(1,1,1).date()
    if data.Time.date() > UnemploymentRate._last_update_date[config.Symbol]:
        UnemploymentRate._last_update_date[config.Symbol] = data.Time.date()
    
    return data

# Custom fee model.
class CustomFeeModel(FeeModel):
def GetOrderFee(self, parameters):
    fee = parameters.Security.Price * parameters.Order.AbsoluteQuantity * 0.00005
    return OrderFee(CashAmount(fee, "USD"))
