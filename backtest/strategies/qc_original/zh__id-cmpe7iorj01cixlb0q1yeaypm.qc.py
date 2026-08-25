# Original QuantConnect / library Python
# locale=zh slug="总统经济支持率与股票横截面收益率"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

from AlgorithmImports import *
import numpy as np
import statsmodels.api as sm
#endregion
class PresidentialEconomicApprovalRatingAndTheCrossSectionOfStockReturns(QCAlgorithm):
def Initialize(self) -> None:
    self.SetStartDate(2001, 1, 1) # First presidential economic approval ratings are in 2001
    self.SetCash(100_000)
    self.exchange_codes: List[str] = ['NYS', 'NAS', 'ASE']    
    self.period: int = 60 # Need n values for regression
    self.wait_days: int = 3 # When data comes wait n + 1 days before trade
    self.quantile: int = 10
    self.leverage: int = 10
    self.min_share_price: int = 1
    self.max_missing_days = 6 * 31
    
    self.data: Dict[Symbol, RollingWindow] = {} # Storing stock prices for regression
    self.weight: Dict[Symbol, float] = {} # Storing weights of selected stocks
    
    self.economic_approval_ratings: Symbol = self.AddData(QuantpediaEconomicApprovalRatings, 'ECONOMIC_APPROVAL_RATINGS', Resolution.Daily).Symbol
    
    # Need n + 2 data in RollingWindow, beacause after CreateRegressionX both variables will have n length
    self.economic_approval_ratings_values: RollingWindow = RollingWindow[float](self.period + 2)
    
    self.fundamental_count: int = 3_000
    self.fundamental_sorting_key = lambda x: x.MarketCap
    self.count_days: int = 0
    self.trade_flag: bool = False
    self.selection_flag: bool = False
    self.UniverseSettings.Leverage = self.leverage
    self.UniverseSettings.Resolution = Resolution.Daily
    self.AddUniverse(self.FundamentalSelectionFunction)
    self.settings.daily_precise_end_time = False
    self.Settings.MinimumOrderMarginPortfolioPercentage = 0.
def OnSecuritiesChanged(self, changes: SecurityChanges) -> None:
    for security in changes.AddedSecurities:
        security.SetFeeModel(CustomFeeModel())

def FundamentalSelectionFunction(self, fundamental: List[Fundamental]) -> List[Symbol]:
    # Select stock on monthly basis
    if not self.selection_flag:
        return Universe.Unchanged
        
    # Store prices only on selection
    for stock in fundamental:
        symbol = stock.Symbol
        
        if symbol in self.data:
            self.data[symbol].Add(stock.AdjustedPrice)
    
    selected: List[Fundamental] = [
        x for x in fundamental 
        if x.HasFundamentalData 
        and x.MarketCap != 0
        and x.Market == 'usa' 
        and x.Price > self.min_share_price 
        and x.SecurityReference.ExchangeId in self.exchange_codes
        and x.AssetClassification.MorningstarSectorCode != MorningstarSectorCode.Utilities
        and x.AssetClassification.MorningstarSectorCode != MorningstarSectorCode.FinancialServices
    ]
    if len(selected) > self.fundamental_count:
        selected = [x for x in sorted(selected, key=self.fundamental_sorting_key, reverse=True)[:self.fundamental_count]]
    
    # Store last price of currently selected stocks
    for stock in selected:
        symbol: Symbol = stock.Symbol
        
        if symbol in self.data:
            continue
        
        # Need n + 1 values, because after performance calculation there will be n results
        self.data[symbol] = RollingWindow[float](self.period + 1)
        
        # Get last day prices
        history: DataFrame = self.History(symbol, 1, Resolution.Daily)
        
        if history.empty:
            self.Log(f"Not enough data for {symbol} yet")
            continue
        
        closes: Series = history.loc[symbol].close
        for _, close in closes.items():
            # Store yesterday's close for current stock
            self.data[symbol].Add(close)
    # Change selection_flag to prevent next day selection
    self.selection_flag = False
    
    # Give signal for trading 
    # NOTE: There will be only liquidation, if stocks weren't selected
    self.trade_flag = True
    
    # Create regression x only if economic approval ratings values have enough data
    if not self.economic_approval_ratings_values.IsReady:
        return Universe.Unchanged
        
    # Create regression x based on economic approval ratings values
    regression_x: List[List[float]] = self.CreateRegressionX(self.economic_approval_ratings_values)
    
    # Storing value of stock's beta for each stock, which has ready data
    stocks_beta: Dict[Symbol, float] = {}
    market_cap = {}
    
    for stock in selected:
        symbol: Symbol = stock.Symbol
        
        # Continue only if stock's prices are ready for regression
        if not self.data[symbol].IsReady:
            continue
        
        # Update market capitalization for stock
        market_cap[symbol] = stock.MarketCap
        
        # Create regression y based on stock's close prices
        regression_y: List[float] = self.StockPerformances(self.data[symbol])
        
        # Calculate regression
        regression_model = self.MultipleLinearRegression(regression_x, regression_y)
        
        # Calculate stocks beta
        stocks_beta[stock] = sum(regression_model.params)
    
    # Make sure we have enough stocks for decile selection
    if len(stocks_beta)  None:
    ear_last_date_update: datetime.date = QuantpediaEconomicApprovalRatings.get_last_update_date()
    if self.economic_approval_ratings in data and data[self.economic_approval_ratings]:
        # Firstly add new value of economic approval rating
        value: float = data[self.economic_approval_ratings].Value
        self.economic_approval_ratings_values.Add(value)
        
        # Start selection, because data comes
        self.selection_flag = True
    else:
        if self.Securities[self.economic_approval_ratings].GetLastData() and self.Time.date() > ear_last_date_update:
            self.Liquidate()
    
    # Trade after data comes        
    if self.trade_flag:
        # Wait n days before trade
        if self.count_days != self.wait_days:
            self.count_days += 1
            
        else:
            # Trade execution
            portfolio: List[PortfolioTarget] = [PortfolioTarget(symbol, w) for symbol, w in self.weight.items() if symbol in data and data[symbol]]
            self.SetHoldings(portfolio, True)
            # Clear old rebalance
            self.weight.clear()
            
            # Hold up trades
            self.trade_flag = False
            self.count_days = 0

def CreateRegressionX(self, rolling_window: RollingWindow) -> List[List[np.ndarray]]:
    values: np.ndarray = np.array([x for x in rolling_window])
    performances: np.ndarray = (values[:-1] - values[1:]) / values[1:]
    # For first variable in regression x get all performances except the last one
    first_variable: np.ndarray = performances[:-1]
    # For second variable in regression x get all performances except the first one
    second_variable: np.ndarray = performances[1:]
    # Return regression x
    return [first_variable, second_variable]
def StockPerformances(self, rolling_window: RollingWindow) -> np.ndarray:
    closes: np.ndarray = np.array([x for x in rolling_window])
    return (closes[:-1] - closes[1:]) / closes[1:]
def MultipleLinearRegression(self, x: np.ndarray, y: np.ndarray):
    x: np.ndarray = np.array(x).T
    # NOTE: Need to change regression_model.params to regression_model.params[1:] after adding constant
    # x = sm.add_constant(x)
    result: ReggresionResultWrapper = sm.OLS(endog=y, exog=x).fit()
    return result

# Quantpedia data.
# NOTE: IMPORTANT: Data order must be ascending (datewise)
class QuantpediaEconomicApprovalRatings(PythonData):
_last_update_date: datetime.date = datetime(1,1,1).date()
@staticmethod
def get_last_update_date() -> Dict[Symbol, datetime.date]:
   return QuantpediaEconomicApprovalRatings._last_update_date
def GetSource(self, config: SubscriptionDataConfig, date: datetime, isLiveMode: bool) -> SubscriptionDataSource:
    return SubscriptionDataSource(
        "data.quantpedia.com/backtesting_data/economic/{0}.csv".format(config.Symbol.Value),
        SubscriptionTransportMedium.RemoteFile,
        FileFormat.Csv
    )
# Header of csv file: date;approved;disapproved;no_opinion
def Reader(self, config: SubscriptionDataConfig, line: str, date: datetime, isLiveMode: bool) -> BaseData:
    data = QuantpediaEconomicApprovalRatings()
    data.Symbol = config.Symbol
    
    if not line[0].isdigit(): return None
    split = line.split(';')
    
    data.Time = datetime.strptime(split[0], "%d.%m.%Y") + timedelta(days=1)
    data['approved'] = float(split[1])
    data.Value = float(split[1])
    if data.Time.date() > QuantpediaEconomicApprovalRatings._last_update_date:
        QuantpediaEconomicApprovalRatings._last_update_date = data.Time.date()
    return data

# Custom fee model.
class CustomFeeModel(FeeModel):
def GetOrderFee(self, parameters: OrderFeeParameters) -> OrderFee:
    fee: float = parameters.Security.Price * parameters.Order.AbsoluteQuantity * 0.00005
    return OrderFee(CashAmount(fee, "USD"))
