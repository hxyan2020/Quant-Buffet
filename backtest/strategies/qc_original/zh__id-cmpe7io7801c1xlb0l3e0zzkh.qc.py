# Original QuantConnect / library Python
# locale=zh slug="中国的趋势因子"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

from AlgorithmImports import *
import statsmodels.api as sm
from pandas.core.frame import DataFrame
class TrendFactorInChina(QCAlgorithm):
def Initialize(self):
    self.SetStartDate(2000, 1, 1)
    self.SetCash(100000)
    
    self.data:Dict[Symbol, SymbolData] = {}
    self.long:List[Symbol] = []
    self.short:List[Symbol] = []
    self.chinese_stocks:List[Symbol] = []
    
    self.period:int = 12
    self.max_moving_average_period:int = 400
    self.quantile:int = 5
    self.leverage:int = 5
    self.min_share_price: float = 5.
    
    self.symbol:Symbol = self.AddEquity("SPY", Resolution.Daily).Symbol
    
    self.current_year:int = -1
    self.selection_flag:bool = False
    self.UniverseSettings.Resolution = Resolution.Daily
    self.Settings.MinimumOrderMarginPortfolioPercentage = 0.
    self.AddUniverse(self.FundamentalSelectionFunction)
    self.Schedule.On(self.DateRules.MonthEnd(self.symbol), self.TimeRules.AfterMarketOpen(self.symbol), self.Selection)
    self.settings.daily_precise_end_time = False
def OnSecuritiesChanged(self, changes: SecurityChanges) -> None:
    for security in changes.AddedSecurities:
        security.SetFeeModel(CustomFeeModel())
        security.SetLeverage(self.leverage)
        
def FundamentalSelectionFunction(self, fundamental: List[Fundamental]) -> List[Symbol]:
    for stock in fundamental:
        symbol:Symbol = stock.Symbol
        
        # We keep updating and normalizing each chinese stock, which was once selected in fine.
        if symbol in self.data:
            self.data[symbol].update(self.Time, stock.AdjustedPrice, stock.Volume)
            
            if self.selection_flag and self.data[symbol].moving_average_ready():
                self.data[symbol].normalize(stock.AdjustedPrice)
    
    if not self.selection_flag:
        return Universe.Unchanged
        
    if len(self.chinese_stocks) == 0 or self.current_year != self.Time.year:
        selected: List[Fundamental] = [
            x for x in fundamental if x.HasFundamentalData and x.CompanyReference.BusinessCountryID == 'CHN' and x.Price >= self.min_share_price
        ]
    # We are changing universe only each year, due to time complexity.
    if self.current_year != self.Time.year:
        # Filter chinese stocks by CountryId 
        # fine = [x for x in fine if x.CompanyReference.BusinessCountryID == 'CHN']
        
        # Exclude 30% of lowest stocks by MarketCap
        sorted_by_market_cap:List = sorted(selected, key = lambda x: x.MarketCap)
        stocks_after_exclusion:List = sorted_by_market_cap[int(len(sorted_by_market_cap) * 0.3):]
          
        # Stocks are firstly sorted by size into five quintile groups. From now on, consider only the highest size quintile.
        quantile:int = int(len(stocks_after_exclusion) / self.quantile)
        self.chinese_stocks = stocks_after_exclusion[-quantile:]
        
        self.current_year = self.Time.year
    
    expected_return:Dict[Symbol, float] = {}
    
    for stock in self.chinese_stocks:
        symbol:Symbol = stock.Symbol
        
        if symbol not in self.data:
            # Fill moving averages of selected chinese stocks.
            self.data[symbol] = SymbolData(self.period)
            
            # If need we can warmup whole regression data.
            history:DataFrame = self.History(symbol, self.max_moving_average_period, Resolution.Daily)
            
            if history.empty:
                self.Log(f"Not enough data for {symbol} yet")
                continue
            
            last_close:float = None
            closes:pd.Series = history.loc[symbol].close
            volumes:pd.Series = history.loc[symbol].volume
            
            for (time, close), (_, volume) in zip(closes.items(), volumes.items()):
                self.data[symbol].update(time, close, volume)
                last_close = close
            
            # After history we can normalize data because moving averages are filled.
            self.data[symbol].normalize(last_close)
        
        if self.data[symbol].is_ready():
            x_train, y_train = self.data[symbol].get_regression_data()
            
            regression_model = self.MultipleLinearRegression(x_train, y_train)
            
            x_predict = self.data[symbol].get_predict_data() 
            
            expected_return[symbol] = self.MultipleLinearRegressionPredict(regression_model, x_predict)
    
    if len(expected_return) == 0:
        return Universe.Unchanged
        
    # Among the highest size decile, long the highest trend quintile and short the lowest trend quintile.
    sorted_by_expected_return:List[Symbol] = [x[0] for x in sorted(expected_return.items(), key=lambda item: item[1])]
    quantile:int = int(len(sorted_by_expected_return) / self.quantile)
    
    self.long = sorted_by_expected_return[-quantile:]
    self.short = sorted_by_expected_return[:quantile]
    
    return self.long + self.short
def OnData(self, data: Slice) -> None:
    if not self.selection_flag:
        return
    self.selection_flag = False
    
    # order execution
    targets:List[PortfolioTarget] = []
    for i, portfolio in enumerate([self.long, self.short]):
        for symbol in portfolio:
            if symbol in data and data[symbol]:
                targets.append(PortfolioTarget(symbol, ((-1) ** i) / len(portfolio)))
    
    self.SetHoldings(targets, True)
        
    self.long.clear()
    self.short.clear()
    
def Selection(self) -> None:
    self.selection_flag = True
    
def MultipleLinearRegression(self, x, y):
    x = np.array(x).T
    x = sm.add_constant(x)
    result = sm.OLS(endog=y, exog=x).fit()
    return result
    
def MultipleLinearRegressionPredict(self, model, x):
    x = [1] + x # Manually adding constant
    x = np.array(x).T
    result = model.predict(x)
    return result[0]
    
class SymbolData():
def __init__(self, period):
    self.Closes:RollingWindow = RollingWindow[float](period)
    # Normalize volume moving averages for regession
    self.SMA_Volume_Regression:List = []
    
    self.SMA_Volume:List[float] = []
    
    # Normalized price moving averages for regression
    self.SMA_Price_Regression:List = []
    
    self.SMA_Price:List[float] = []

    # 3-, 5-, 10-, 20-, 50-, 100-, 200-, 300-, and 400-days data
    for period_number in [3, 5, 10, 20, 50, 100, 200, 300, 400]:
        self.SMA_Volume_Regression.append(RollingWindow[float](period))
        self.SMA_Volume.append(SimpleMovingAverage(period_number))
        
        self.SMA_Price_Regression.append(RollingWindow[float](period))
        self.SMA_Price.append(SimpleMovingAverage(period_number))
    
def update(self, time, close:float, volume:float) -> None:
    for sma_volume, sma_price in zip(self.SMA_Volume, self.SMA_Price):
        sma_volume.Update(time, volume)
        sma_price.Update(time, close)
    
def is_ready(self) -> bool:
    # Data for regression are updating at the same time so we need to check only one RollingWindow
    return self.Closes.IsReady and self.SMA_Price_Regression[0].IsReady and self.SMA_Volume_Regression[0].IsReady
            
def moving_average_ready(self) -> bool:
    # Moving averages are updating at the same time, so we need to check only the ones with biggest period
    return self.SMA_Volume[-1].IsReady and self.SMA_Price[-1].IsReady 
            
def normalize(self, price) -> None:
    self.Closes.Add(price)
    
    for sma_volume_regression, sma_volume in zip(self.SMA_Volume_Regression, self.SMA_Volume):
        sma_volume_regression.Add(sma_volume.Current.Value / price)
        
    for sma_price_regression, sma_price in zip(self.SMA_Price_Regression, self.SMA_Price):
        sma_price_regression.Add(sma_price.Current.Value / price)
    
def get_regression_data(self):
    regression_data = []
    
    for sma_volume_regression, sma_price_regression in zip(self.SMA_Volume_Regression, self.SMA_Price_Regression):
        regression_data.append([x for x in sma_volume_regression][1:]) # Last value is used for predict not for train.
        regression_data.append([x for x in sma_price_regression][1:]) # Last value is used for predict not for train.
        
    return (regression_data, [x for x in self.Closes][1:])
    
def get_predict_data(self):
    regression_data = []
    
    for sma_volume_regression, sma_price_regression in zip(self.SMA_Volume_Regression, self.SMA_Price_Regression):
        regression_data.append([x for x in sma_volume_regression][0]) # Using last value for predicting the return.
        regression_data.append([x for x in sma_price_regression][0]) # Using last value for predicting the return.c
    
    return regression_data
    
# Custom fee model
class CustomFeeModel(FeeModel):
def GetOrderFee(self, parameters):
    fee = parameters.Security.Price * parameters.Order.AbsoluteQuantity * 0.00005
    return OrderFee(CashAmount(fee, "USD"))
