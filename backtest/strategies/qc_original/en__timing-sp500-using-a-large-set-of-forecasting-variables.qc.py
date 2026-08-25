# Original QuantConnect / library Python
# locale=en slug="timing-sp500-using-a-large-set-of-forecasting-variables"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

from AlgorithmImports import *
import data_tools
from pandas.core.frame import DataFrame
from dateutil.relativedelta import relativedelta
import statsmodels.api as sm
from statsmodels.tools.eval_measures import rmse
# endregion
class TimingSP500UsingaLargeSetofForecastingVariables(QCAlgorithm):
def Initialize(self):
    self.SetStartDate(2000, 1, 1)
    self.SetCash(100000)
    self.period:int = 24
    self.quarter_period:int = 3 # due to Deliquencies quarterly data
    self.month_period:int = 21
    self.max_alocation:float = 1.5
    self.decay_factor:float = 0.99
    self.leverage:int = 3
    self.max_missing_days:int = 31
    self.independent_variables_num:int = 12
    self.market:Symbol = self.AddEquity("SPY", Resolution.Daily).Symbol
    self.bil:Symbol = self.AddEquity('BIL', Resolution.Daily).Symbol
    self.commodity_index:Symbol = self.AddEquity('GSG', Resolution.Daily).Symbol
    self.dollar_index:Symbol = self.AddEquity('UUP', Resolution.Daily).Symbol
    self.baltic_index:Symbol = self.AddData(data_tools.BalticDryIndex, 'BADI', Resolution.Daily).Symbol
    for symbol in [self.market, self.bil]:
        self.Securities[symbol].SetLeverage(self.leverage)
    quandl_tickers:List[str] = ['RATEINF/CPI_USA']
    self.consumer_index_usa:Symbol = self.AddData(data_tools.QuandlValue, 'RATEINF/CPI_USA', Resolution.Daily).Symbol
    quarterly_custom_data:List[str] = ['DRALACBN_YOY']
    monthly_custom_data:List[str] = ['INDPRO_YOY', 'BAA_AAA', 'NEWORDER', 'HOUST', 'UNEMPLOYMENT_RATE']
    daily_custom_data:List[str] = ['T10Y3M']
    self.data:Dict[Symbol, float] = {}
    self.quarterly_custom_data:List[Symbol] = [self.AddData(data_tools.QuarterlyCustomData, x, Resolution.Daily).Symbol for x in quarterly_custom_data]
    self.monthly_custom_data:List[Symbol] = [self.AddData(data_tools.MonthlyCustomData, x, Resolution.Daily).Symbol for x in monthly_custom_data]
    self.daily_custom_data:List[Symbol] = [self.AddData(data_tools.DailyCustomData, x, Resolution.Daily).Symbol for x in daily_custom_data] + [self.baltic_index]
    self.qc_data:List[Symbol] = [self.consumer_index_usa]
    self.recent_month:int = -1
def OnData(self, data: Slice):
    # monthly rebalance
    if self.recent_month == self.Time.month:
        return
    self.recent_month = self.Time.month
    quarterly_custom_data_last_update_date:Dict[Symbol, datetime.date] = data_tools.QuarterlyCustomData._last_update_date
    monthly_custom_data_last_update_date:Dict[Symbol, datetime.date] = data_tools.MonthlyCustomData._last_update_date
    daily_custom_data_last_update_date:Dict[Symbol, datetime.date] = data_tools.DailyCustomData._last_update_date
    # check if data is still arriving
    if all([self.Securities[x].GetLastData() for x in self.quarterly_custom_data + self.monthly_custom_data + self.daily_custom_data + self.qc_data]) \
        and any([self.Time.date() >= monthly_custom_data_last_update_date[x] for x in monthly_custom_data_last_update_date]) \
        and any([self.Time.date() >= quarterly_custom_data_last_update_date[x] for x in quarterly_custom_data_last_update_date]) \
        and any([self.Time.date() >= daily_custom_data_last_update_date[x] for x in daily_custom_data_last_update_date]) \
        and any((self.Time.date() - self.Securities[x].GetLastData().Time.date()).days >= self.max_missing_days for x in self.qc_data):
        self.Liquidate()
        return Universe.Unchanged
    # call history on all variables
    history:DataFrame = self.History(self.monthly_custom_data + self.daily_custom_data + self.qc_data + self.quarterly_custom_data, start=self.Time.date() - relativedelta(months=self.period + self.quarter_period), end=self.Time.date())['value'].unstack(level=0)
    history_equities:DataFrame = self.History([self.market, self.commodity_index, self.dollar_index], start=self.Time.date() - relativedelta(months=self.period), end=self.Time.date())['close'].unstack(level=0)
    history = history.groupby(pd.Grouper(freq='MS')).last()
    history_equities = history_equities.groupby(pd.Grouper(freq='MS')).last()
    history['DRALACBN_YOY'] = history['DRALACBN_YOY'].fillna(method='ffill') # forward fill due quarterly data
    history = history[self.quarter_period:]
    history = pd.concat([history, history_equities], axis=1)
    history = history[1:]
    if history.iloc[0].isna().any():
        return
    
    if len(history.columns) = self.period:
        df:DataFrame = pd.DataFrame(self.data)
        result_factors:Dict[Symbol, float] = self.factor_analysis(self.market, df, len(history.loc[:, history.columns != self.market].columns))
        # run regression on best model and predict return of market 
        if result_factors:
            y:np.ndarray = df[self.market][1:].values
            x:np.ndarray = df[list(result_factors.keys())][:-1].values
            model = self.multiple_linear_regression(x, y)
            predicted_y:np.ndarray = model.predict(sm.add_constant(df[list(result_factors.keys())][-1:].values, has_constant='add'))
            rmse_value:float = rmse(y, predicted_y)
            alocation:float = predicted_y * (1 / rmse_value) * 5
            # trade execution
            if predicted_y  Dict:
    """ 
    Performs factor analysis.
    :param asset_id: Id of asset that is going to be fit.
    :param factor_df: Performance dataframe with all the factors and asset with asset_id.
    :param n: Max number of assets in the model.
    :return: Fitted model dictionary.
    """
    order:List[str] = []
    y:np.ndarray = factor_df[asset_id].values 
    reduced_df:DataFrame = factor_df.drop([asset_id], axis=1)
    # reduced_df.drop(['Date'], axis=1, inplace=True)
    
    for i, _ in enumerate(reduced_df.items()):
        # not negative beta models properties
        aic_reduced:List[float] = []
        col_names_reduced:List[str] = []
            
        for j, (j_asset_name, _) in enumerate(reduced_df.items()):
            if j_asset_name in order:
                continue
            
            if i > len(order) - 1:
                order.append(j_asset_name)
            else:
                order[i] = j_asset_name
            
            order_reduced:List[str] = [x for x in order if x != '']
            x:np.ndarray = reduced_df[order_reduced].values
            model = self.multiple_linear_regression(x, y)
            aic:float = model.aic
            
            if ignore_negative_loading:
                # store only not negative beta models
                if not any(x  0:
            order_reduced:List[str] = [x for x in order if x != '']
            previous_order:List[str] = [x for x in order_reduced[:-1]]
            
            if len(order_reduced) != 0 and len(previous_order) != 0:
                # build previous and actual regression models
                x:np.ndarray = reduced_df[order_reduced].values
                model = self.multiple_linear_regression(x, y)
                aic:float = model.aic
                betas:List[float] = model.params[1:]
                # betas, _, lm_aic = self.multiple_linear_regression(x, y)
                x = reduced_df[previous_order].values
                model = self.multiple_linear_regression(x, y)
                prev_aic:float = model.aic
                prev_betas:List[float] = model.params[1:]
                # prev_betas, _, previous_aic = self.multiple_linear_regression(y, x)
                
                if (aic >= prev_aic) or (n != 0 and len(order_reduced) > n):
                    result:Dict[str, float] = { order_id : beta for order_id, beta in zip(previous_order, betas.tolist()) }
                    return result
    
    order_reduced:List[str] = [x for x in order if x != '']
    x:np.ndarray = reduced_df[order_reduced].values
    model = self.multiple_linear_regression(x, y)
    betas:List[float] = model.params[1:]
    # betas, _, lm_aic = self.multiple_linear_regression(y, x)
    result:Dict[str, float] = { order_id : betas  for order_id, betas in zip(order_reduced, betas.tolist()) }
    return result
def multiple_linear_regression(self, x:np.ndarray, y:np.ndarray):
    # x:np.ndarray = np.array(x).T
    x = sm.add_constant(x, prepend=True)
    w:List[float] = self.decay_factor ** np.arange(len(y), 0, -1)
    result = sm.WLS(endog=y, exog=x, weights=w).fit()
    return result
