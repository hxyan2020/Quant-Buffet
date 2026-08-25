# Original QuantConnect / library Python
# locale=zh slug="商品期货回报的序列依赖性"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

from AlgorithmImports import *
# but it is a normal regression with added penalization term). The shrinkage parameter lambda for each regression is found by minimizing the AICc information criterion (equation 3.12). AICc
# is corrected AIC for small-sample bias. After the LASSO selects the important predictors, OLS is used to estimate the regression, using only the selected predictors to overcome the
# underfitting of LASSO parameter estimates. Prediction of the returns in the month t+1 is based on OLS estimated parameters of month t (using returns of month t and t-1; naturally, the OLS 
# regression to obtain parameters at time t, uses returns of months t-1 and t-2). If LASSO does not select any predictor for some commodity, the commodity is omitted. Based on the predicted
# returns, long top five commodities and short bottom five commodities. The portfolio is rebalanced monthly.
#
# QC implementation:
#   - Shrinkage parameter is found by cross-validation instead of minimizing AIC, although AIC minimalization code is also included.
import statsmodels.api as sm
from sklearn import linear_model
class TheSerialDependenceoftheCommodityFuturesReturns(QCAlgorithm):
def Initialize(self):
    self.SetStartDate(2000, 1, 1)
    self.SetCash(100000)
    # the full list - table 1
    self.symbols = [
                    "CME_BO1",  # Soybean Oil Futures, Continuous Contract
                    "CME_C1",   # Corn Futures, Continuous Contract
                    "CME_KW2",  # Wheat Kansas, Continuous Contract
                    "CME_O1",   # Oats Futures, Continuous Contract
                    "CME_RR1",  # Rough Rice Futures, Continuous Contract
                    "CME_S1",   # Soybean Futures, Continuous Contract
                    "CME_SM1",  # Soybean Meal Futures, Continuous Contract
                    "CME_W1",   # Wheat Futures, Continuous Contract
                    "ICE_CC1",  # Cocoa Futures, Continuous Contract 
                    "ICE_CT1",  # Cotton No. 2 Futures, Continuous Contract
                    "CME_DA1",  # Class III Milk Futures
                    "ICE_OJ1",  # Orange Juice Futures, Continuous Contract
                    "ICE_KC1",  # Coffee C Futures, Continuous Contract
                    "CME_LB1",  # Random Length Lumber Futures, Continuous Contract
                    "ICE_SB1",  # Sugar No. 11 Futures, Continuous Contract
                    "CME_CL1",  # Crude Oil Futures, Continuous Contract
                    "ICE_O1",   # Heating Oil Futures, Continuous Contract
                    "CME_NG1",  # Natural Gas (Henry Hub) Physical Futures, Continuous Contract
                    "CME_RB2",  # Gasoline Futures, Continuous Contract
                    "CME_FC1",  # Feeder Cattle Futures, Continuous Contract
                    "CME_LC1",  # Live Cattle Futures, Continuous Contract
                    "CME_LN1",  # Lean Hog Futures, Continuous Contract
                    "CME_GC1",  # Gold Futures, Continuous Contract
                    "CME_HG1",  # Copper Futures, Continuous Contract
                    "CME_PA1",  # Palladium Futures, Continuous Contract 
                    "CME_PL1",  # Platinum Futures, Continuous Contract
                    "CME_SI1",  # Silver Futures, Continuous Contract
                    ]
    
    self.daily_period = 21
    self.period = 60 + 1
    # self.monthly_period = self.period * self.daily_period
    
    self.SetWarmUp(self.period * self.daily_period, Resolution.Daily)
    
    self.perf_data = {}
    self.roc = {}
    
    for symbol in self.symbols:
        data = self.AddData(QuantpediaFutures, symbol, Resolution.Daily)
        data.SetFeeModel(CustomFeeModel())
        data.SetLeverage(5)
        
        self.roc[symbol] = self.ROC(symbol, self.daily_period, Resolution.Daily)
        self.perf_data[symbol] = RollingWindow[float](self.period)
    self.recent_month = -1
def OnData(self, data):
    if self.IsWarmingUp:
        return
    # rebalance once a month
    if self.recent_month == self.Time.month:
        return
    self.recent_month = self.Time.month
    
    dependent_symbols = []  # dependent variables to count with
    self.x = []
    
    # store monthly performance and construct indepedend variable
    for symbol in self.symbols:
        if self.perf_data[symbol].IsReady and self.Securities[symbol].GetLastData() and self.Time.date() = count*2:
        sorted_by_pred_return = sorted(predicted_return.items(), key=lambda x: x[1], reverse=True)
        long = [x[0] for x in sorted_by_pred_return[:count]]
        short = [x[0] for x in sorted_by_pred_return[-count:]]
    # trade execution
    targets: List[PortfolioTarget] = []
    for i, portfolio in enumerate([long, short]):
        for symbol in portfolio:
            if symbol in data and data[symbol]:
                targets.append(PortfolioTarget(symbol, ((-1) ** i) / len(portfolio)))
    
    self.SetHoldings(targets, True)
def multiple_linear_regression(self, x, y):
    x = np.array(x).T
    x = sm.add_constant(x)
    result = sm.OLS(endog=y, exog=x).fit()
    return result
# Quantpedia data.
# NOTE: IMPORTANT: Data order must be ascending (datewise)
class QuantpediaFutures(PythonData):
_last_update_date:Dict[Symbol, datetime.date] = {}
@staticmethod
def get_last_update_date() -> Dict[Symbol, datetime.date]:
   return QuantpediaFutures._last_update_date
def GetSource(self, config, date, isLiveMode):
    return SubscriptionDataSource("data.quantpedia.com/backtesting_data/futures/{0}.csv".format(config.Symbol.Value), SubscriptionTransportMedium.RemoteFile, FileFormat.Csv)
def Reader(self, config, line, date, isLiveMode):
    data = QuantpediaFutures()
    data.Symbol = config.Symbol
    
    if not line[0].isdigit(): return None
    split = line.split(';')
    
    data.Time = datetime.strptime(split[0], "%d.%m.%Y") + timedelta(days=1)
    data['back_adjusted'] = float(split[1])
    data['spliced'] = float(split[2])
    data.Value = float(split[1])
    if config.Symbol.Value not in QuantpediaFutures._last_update_date:
        QuantpediaFutures._last_update_date[config.Symbol.Value] = datetime(1,1,1).date()
    if data.Time.date() > QuantpediaFutures._last_update_date[config.Symbol.Value]:
        QuantpediaFutures._last_update_date[config.Symbol.Value] = data.Time.date()
    return data
# Custom fee model.
class CustomFeeModel(FeeModel):
def GetOrderFee(self, parameters):
    fee = parameters.Security.Price * parameters.Order.AbsoluteQuantity * 0.00005
    return OrderFee(CashAmount(fee, "USD"))
class SymbolData():
def __init__(self, monthly_period: int):
    self.days_to_liquidate = days_to_liquidate
    self.long_flag = long_flag
