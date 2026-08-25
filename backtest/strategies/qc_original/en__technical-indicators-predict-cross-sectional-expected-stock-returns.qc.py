# Original QuantConnect / library Python
# locale=en slug="technical-indicators-predict-cross-sectional-expected-stock-returns"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

from AlgorithmImports import *
import statsmodels.api as sm
# endregion

class TechnicalIndicatorsPredictCrossSectionalExpectedStockReturns(QCAlgorithm):

def Initialize(self):
    self.SetStartDate(2000, 1, 1)
    self.SetCash(100000)

    self.quantile:int = 10
    self.month_period:int = 21    
    self.regression_period:int = 60
    self.period:int = self.month_period * 12               
    self.leverage:int = 5
    self.long_periods:List[int] = [9 * self.month_period, 12 * self.month_period]
    self.short_periods:List[int] = [1* self.month_period, 2 * self.month_period, 3 * self.month_period]

    self.last_fine:List[Symbol] = []

    self.data:Dict[Symbol, SymbolData] = {}
    self.weight:Dict[Symbol, float] = {}

    self.symbol:Symbol = self.AddEquity('SPY', Resolution.Daily).Symbol
    
    self.fundamental_count:int = 500
    self.fundamental_sorting_key = lambda x: x.DollarVolume

    self.selection_flag:bool = False
    self.UniverseSettings.Resolution = Resolution.Daily
    self.AddUniverse(self.FundamentalSelectionFunction)
    self.Settings.MinimumOrderMarginPortfolioPercentage = 0.
    self.Schedule.On(self.DateRules.MonthStart(self.symbol), self.TimeRules.BeforeMarketClose(self.symbol, 0), self.Selection)

def OnSecuritiesChanged(self, changes: SecurityChanges) -> None:
    for security in changes.AddedSecurities:
        security.SetFeeModel(CustomFeeModel())
        security.SetLeverage(self.leverage)

def FundamentalSelectionFunction(self, fundamental: List[Fundamental]) -> None:
    # update stocks data on daily basis
    for stock in fundamental:
        symbol:Symbol = stock.Symbol
        
        if symbol in self.data:
            self.data[symbol].update(stock.AdjustedPrice, stock.Volume)

    if not self.selection_flag:
        return Universe.Unchanged
    
    selected:List[Fundamental] = [x for x in fundamental if x.HasFundamentalData and x.Market == 'usa' and x.MarketCap != 0 and \
        ((x.SecurityReference.ExchangeId == "NYS") or (x.SecurityReference.ExchangeId == "NAS") or (x.SecurityReference.ExchangeId == "ASE"))]

    if len(selected) > self.fundamental_count:
        selected = [x for x in sorted(selected, key=self.fundamental_sorting_key, reverse=True)[:self.fundamental_count]]
    
    pred_returns:Dict[Fundamental, float] = {}

    # warm up stock's data
    for stock in selected:
        symbol:Symbol = stock.Symbol

        if symbol not in self.data:
            self.data[symbol] = SymbolData(symbol, self.short_periods, self.long_periods, self.period)
            history = self.History(symbol, self.period, Resolution.Daily)
            if history.empty:
                continue
            
            closes = history.loc[symbol].close
            volumes = history.loc[symbol].volume

            for (_, close), (_, volume) in zip(closes.items(), volumes.items()):
                self.data[symbol].update(close, volume)
        
        if self.data[symbol].is_ready():
            symbol_obj = self.data[symbol]

            # make sure data are consecutive
            if symbol not in self.last_fine:
                symbol_obj.clear_regression_data()

            # make sure regression data are ready
            if symbol_obj.is_regression_data_ready(self.regression_period):
                regression_x, regression_y = symbol_obj.get_regression_data(self.regression_period)
                x_transpose:np.array = np.array(regression_x).T

                # skip x series with the same value throughout the whole series since there's not clear decision to make for which zeroed series should be intercept
                x_variable_skip_indices:List[int] = self.GetIndicesOfSameValues(x_transpose=x_transpose)

                # use adjusted x variable for model building and for prediction
                adjusted_x_variable:List = [x for i, x in enumerate(x_transpose) if i not in x_variable_skip_indices]
                regression_x:np.array = np.array(adjusted_x_variable).T
                regression_model = sm.OLS(endog=regression_y, exog=regression_x).fit()
                regression_params:List[float] = list(regression_model.params)

                # update this month regression data
                symbol_obj.update_returns(self.month_period)
                symbol_obj.update_technical_indicators(self.long_periods)

                if symbol_obj.is_smoothing_window_ready(self.regression_period):
                    pred_params:List = symbol_obj.get_prediction_params(self.regression_period)
                    pred_x:List = symbol_obj.get_prediction_x()

                    # predict price based on previous technical indicators
                    stock_pred_return:float = self.CalcStockPrediction(pred_params, pred_x)

                    pred_returns[stock] = stock_pred_return

                # update smoothing window
                smoothing_window_entry:List[float] = []
                for i, x_series in enumerate(x_transpose):
                    if i in x_variable_skip_indices:
                        smoothing_window_entry.append(0)
                    else:
                        smoothing_window_entry.append(regression_params.pop(0))

                symbol_obj.update_smoothing_window(smoothing_window_entry)

            else:
                # update this month regression data
                symbol_obj.update_returns(self.month_period)
                symbol_obj.update_technical_indicators(self.long_periods)

    # last_fine helps to secure data consecution
    self.last_fine = list(map(lambda x: x.Symbol, selected))

    # make sure there are enough stock for selection
    if len(pred_returns)  None:
    # rebalance monthly
    if not self.selection_flag:
        return
    self.selection_flag = False
    
    # trade execution
    portfolio:List[PortfolioTarget] = [PortfolioTarget(symbol, w) for symbol, w in self.weight.items() if symbol in data and data[symbol]]
    self.SetHoldings(portfolio, True)

    self.weight.clear()

def GetIndicesOfSameValues(self, x_transpose:np.array) -> list:
    x_variable_skip_indices:List= []

    for i, x_series in enumerate(x_transpose):
        # don't skip intercept
        if i != 0 and all(x_series[0] == x for x in x_series):
            x_variable_skip_indices.append(i)

    return x_variable_skip_indices

def CalcStockPrediction(self, pred_params:List, pred_x:List) -> float:
    pred_value:float = 0

    for param, x_value in zip(pred_params, pred_x):
        pred_value += param * x_value

    return pred_value

def Selection(self) -> NormalizedNetProfitMargin():
    self.selection_flag = True

class SymbolData():
def __init__(self, symbol:Symbol, short_periods:List, long_periods:List, period:float) -> None:
    self.short_SMA:List = []
    self.long_SMA:List = []

    self.long_volumes:List = []
    self.short_volumes:List = []

    self.technical_indicators:List = []
    self.returns:List = []

    self.smoothing_window:List = []

    self.prices:RollingWindow = RollingWindow[float](period)

    for period in short_periods:
        self.short_SMA.append(RollingWindow[float](period))
        self.short_volumes.append(RollingWindow[float](period))

    for period in long_periods:
        self.long_SMA.append(RollingWindow[float](period))
        self.long_volumes.append(RollingWindow[float](period))

def update(self, stock_price:float, stock_volume:float) -> None:
    for short_SMA_roll_win, short_volume in zip(self.short_SMA, self.short_volumes):
        short_SMA_roll_win.Add(stock_price)
        short_volume.Add(stock_volume)

    for long_SMA_roll_win, long_volume in zip(self.long_SMA, self.long_volumes):
        long_SMA_roll_win.Add(stock_price)
        long_volume.Add(stock_volume)

    self.prices.Add(stock_price)

def is_ready(self) -> bool:
    for short_SMA_roll_win, short_volume in zip(self.short_SMA, self.short_volumes):
        if not short_SMA_roll_win.IsReady or not short_volume.IsReady:
            return False

    for long_SMA_roll_win, long_volume in zip(self.long_SMA, self.long_volumes):
        if not long_SMA_roll_win.IsReady or not long_volume.IsReady:
            return False

    return self.prices.IsReady

def is_regression_data_ready(self, regression_period:int) -> bool:
    return len(self.technical_indicators) >= regression_period and len(self.returns) >= regression_period

def is_smoothing_window_ready(self, regression_period:int) -> bool:
    return len(self.smoothing_window) >= regression_period

def clear_regression_data(self):
    self.technical_indicators.clear()
    self.smoothing_window.clear()
    self.returns.clear()

def update_returns(self, period:int):
    # make sure between regression x and y is right shift
    if len(self.technical_indicators) > 0:
        prices:List = [x for x in self.prices][:period]
        return_value:float = (prices[0] - prices[-1]) / prices[-1]

        self.returns.append(return_value)

def update_technical_indicators(self, periods:List) -> list:
    technical_indicators_values:List = []

    # MA and OBV technical indicators
    for long_SMA_roll_win, long_volume in zip(self.long_SMA, self.long_volumes):
        mean_long_volume:float = np.mean([x for x in long_volume])
        long_SMA_value:float = self.calc_simple_moving_average([x for x in long_SMA_roll_win])

        for short_SMA_roll_win, short_volume in zip(self.short_SMA, self.short_volumes):
            mean_short_volume:float = np.mean([x for x in short_volume])
            short_SMA_value:float = self.calc_simple_moving_average([x for x in short_SMA_roll_win])

            if long_SMA_value > short_SMA_value:
                technical_indicators_values.append(0)
            else:
                technical_indicators_values.append(1)

            if mean_long_volume > mean_short_volume:
                technical_indicators_values.append(0)
            else:
                technical_indicators_values.append(1)

    prices:List = [x for x in self.prices]
    curr_price:float = prices[0]

    # MOM technical indicators
    for period in periods:
        if curr_price >= prices[period - 1]:
            technical_indicators_values.append(1)
        else:
            technical_indicators_values.append(0)

    self.technical_indicators.append(technical_indicators_values)

def update_smoothing_window(self, smoothing_window_entry:List):
    self.smoothing_window.append(smoothing_window_entry)

def calc_simple_moving_average(self, prices:List) -> float:
    return sum(prices) / len(prices)

def get_regression_data(self, regression_period:int) -> list:
    x = self.technical_indicators[-regression_period:]
    # add constant
    x = [[1] + tech_indi for tech_indi in x]
    y = self.returns[-regression_period:]

    return x, y

def get_prediction_params(self, regression_period:int) -> list:
    window_transpose:np.array = np.array(self.smoothing_window[-regression_period:]).T
    params:List = [np.mean(params_list) for params_list in window_transpose]

    return params

def get_prediction_x(self) -> list:
    last_indicators:List = self.technical_indicators[-1]
    return [1] + last_indicators

# Custom fee model
class CustomFeeModel(FeeModel):
def GetOrderFee(self, parameters):
    fee = parameters.Security.Price * parameters.Order.AbsoluteQuantity * 0.00005
    return OrderFee(CashAmount(fee, "USD"))
