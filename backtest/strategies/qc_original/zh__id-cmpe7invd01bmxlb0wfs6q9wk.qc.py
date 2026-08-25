# Original QuantConnect / library Python
# locale=zh slug="长期机构交易与收益的横截面分析"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

from AlgorithmImports import *
from dateutil.relativedelta import relativedelta
#endregion
class LongTermInstitutionalTradesAndTheCrossSectionOfReturns(QCAlgorithm):
def Initialize(self):
    self.SetStartDate(2005, 1, 1) # institutional ownership data starts at 2005
    self.SetCash(100_000)
    
    self.period: int = 10 # need n data points of institutional ownership data
    self.quantile: int = 10
    self.leverage: int = 5
    
    self.weight: Dict[Symbol, float] = {}
    self.institutional_data: Dict[str, RollingWindow] = {}
        
    market: Symbol = self.AddEquity('SPY', Resolution.Daily).Symbol
    # subscribe to Quantpedia institutional ownership data   
    self.institutional_symbol: Symbol = self.AddData(QuantpediaInstitutionalOwnership, 'INSTITUTIONAL_OWNERSHIP_IN_PERCENTS', Resolution.Daily).Symbol
    
    self.selection_flag: bool = False
    self.settings.daily_precise_end_time = False
    self.Settings.MinimumOrderMarginPortfolioPercentage = 0.
    self.UniverseSettings.Resolution = Resolution.Daily
    self.AddUniverse(self.FundamentalSelectionFunction)
    self.Schedule.On(self.DateRules.MonthStart(market), self.TimeRules.AfterMarketOpen(market), self.Selection)
    
def OnSecuritiesChanged(self, changes: SecurityChanges) -> None:
    for security in changes.AddedSecurities:
        security.SetFeeModel(CustomFeeModel())
        security.SetLeverage(self.leverage)

def FundamentalSelectionFunction(self, fundamental: List[Fundamental]) -> List[Symbol]:
    # monthly rebalance
    if not self.selection_flag:
        return Universe.Unchanged
    if self.Time.date() > QuantpediaInstitutionalOwnership.get_last_update_date():
        return Universe.Unchanged
    selected: List[Fundamental] = [
        x for x in fundamental 
        if x.Symbol.Value in self.institutional_data
        and x.MarketCap != 0
    ]
    LIT: Dict[Fundamental, float] = {
        stock: self.CalculateLIT(self.institutional_data[stock.Symbol.Value]) 
        for stock in selected if self.institutional_data[stock.Symbol.Value].IsReady}
    
    # not enough stocks for decile selection
    if len(LIT)  None:
    if self.institutional_symbol in data and data[self.institutional_symbol]:
        # get objects with tickers and their values from data object
        tickers_values_objects: List = [x for x in data[self.institutional_symbol].GetProperty('Tickers_Values')]
        # update LIT rolling window for each stock ticker
        self.UpdateInstitutionalDataRollingWindow(tickers_values_objects)
    
    # monthly rebalance
    if not self.selection_flag:
        return
    self.selection_flag = False
    
    # trade execution
    portfolio: List[PortfolioTarget] = [
        PortfolioTarget(symbol, w) for symbol, w in self.weight.items() if symbol in data and data[symbol]
    ]
    self.SetHoldings(portfolio, True)
    self.weight.clear()
    
def UpdateInstitutionalDataRollingWindow(self, tickers_values_objects: List[float]) -> None:
    ''' update rolling window for each stock in self.institutional_data with new institutional data point '''
    ''' if rolling window doesn't exists it will be created '''
    
    for ticker_value in tickers_values_objects:
        # create list from ticker and value object
        ticker_value = [x for x in ticker_value]
        # get ticker from list
        ticker: str = ticker_value[0]
        # get value from list
        value: float = ticker_value[1]
        
        # initialize rolling window for institutional data for specific stock ticker
        if ticker not in self.institutional_data:
            self.institutional_data[ticker] = RollingWindow[float](self.period)
        
        # make sure value isn't missing
        if value:
            self.institutional_data[ticker].Add(value)
            
def CalculateLIT(self, institutional_data_rolling_window: RollingWindow) -> float:
    ''' calculates and returns stock's LIT(total change of institutional ownership data) '''
    
    institutional_data: List[float] = list(institutional_data_rolling_window)
    
    prev_data_point: float = institutional_data[0]
    total_change: float = 0
    
    for data_point in institutional_data[1:]: # offset first data point
        # increase of institutional data
        if prev_data_point  None:
    self.selection_flag = True
    
# custom fee model
class CustomFeeModel(FeeModel):
def GetOrderFee(self, parameters):
    fee = parameters.Security.Price * parameters.Order.AbsoluteQuantity * 0.00005
    return OrderFee(CashAmount(fee, "USD"))
    
# Quantpedia data.
# NOTE: IMPORTANT: Data order must be ascending (datewise)
# Name of the csv file has to be in uppercase
class QuantpediaInstitutionalOwnership(PythonData):
_last_update_date: datetime.date = datetime(1,1,1).date()
@staticmethod
def get_last_update_date() -> datetime.date:
   return QuantpediaInstitutionalOwnership._last_update_date
def __init__(self):
    self.header = None

def GetSource(self, config, date, isLiveMode):
    return SubscriptionDataSource("data.quantpedia.com/backtesting_data/economic/institutional_ownership/{0}.csv".format(config.Symbol.Value), SubscriptionTransportMedium.RemoteFile, FileFormat.Csv)
def Reader(self, config, line, date, isLiveMode):
    data = QuantpediaInstitutionalOwnership()
    data.Symbol = config.Symbol
    
    # initialize header with stock tickers from csv files
    if not self.header:
        # split header of csv file
        line_split = line.split(',')
        
        # store stock tickers in header list
        self.header = [ticker for ticker in line_split[1:]] # exclude 'date'
        
    if not line[0].isdigit():
        return None
        
    line_split = line.split(',')
    # make two months lag of data
    data.Time = datetime.strptime(line_split[0], '%Y-%m-%d') + relativedelta(months=2)
    # store last update date
    if data.Time.date() > QuantpediaInstitutionalOwnership._last_update_date:
        QuantpediaInstitutionalOwnership._last_update_date = data.Time.date()
    tickers_values = []
    # store values with their tickers
    for (ticker), (value) in zip(self.header, line_split[1:]):
        if value == '':
            tickers_values.append([ticker, None])
        else:
            tickers_values.append([ticker, float(value)])
            
    data['tickers_values'] = tickers_values
    
    return data
