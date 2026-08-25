# Original QuantConnect / library Python
# locale=zh slug="封闭式基金均值回归交易"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

from AlgorithmImports import *
#endregion
class ClosedEndFundMeanReversionTrading(QCAlgorithm):
def Initialize(self):
    self.SetStartDate(2000, 1, 1)
    self.SetCash(100000)
    
    self.symbol_count: int = 100     # due to QC limitation, maximum amount of 100 individual custom data series can be loaded
    self.quantile: int = 5
    self.leverage: int = 3
    self.CEF_data: Dict[Symbol, CEFData] = {}  # CEF NAV and price storage
    
    # load csv with CEF tickers
    # source: https://stockanalysis.com/list/closed-end-funds/
    csv_string_file: str = self.Download('data.quantpedia.com/backtesting_data/equity/CEFs/CEFs.csv')
    line: str = csv_string_file.split('\r\n')
    line_split: List[str] = line[0].split(';')
    
    for ticker in line_split[:self.symbol_count]:
        stock_symbol: Symbol = self.AddEquity(ticker, Resolution.Daily).Symbol
        # subscribe to QuantpediaCEF with csv name
        cef_symbol: Symbol = self.AddData(QuantpediaCEF, ticker, Resolution.Daily).Symbol
        # create object for each subscribed symbol
        self.CEF_data[stock_symbol] = CEFData(cef_symbol)
    
    self.recent_month: int = -1
    self.Settings.MinimumOrderMarginPortfolioPercentage = 0.
    
def OnSecuritiesChanged(self, changes: SecurityChanges) -> None:
    for security in changes.AddedSecurities:
        security.SetFeeModel(CustomFeeModel())
        security.SetLeverage(self.leverage)
				
def OnData(self, slice: Slice) -> None:
    rebalance_flag: bool = False
    discount: Dict[Symbol, float] = {}
    last_update_date: Dict[str, datetime.date] = QuantpediaCEF.get_last_update_date()
    # update NAV values for each CEF
    for stock_symbol, CEF_data in self.CEF_data.items():
        cef_symbol: Symbol = CEF_data.get_CEF_symbol()
        if cef_symbol in slice and slice[cef_symbol]:
            # update CEF's NAV
            nav: float = slice[cef_symbol].Value
            CEF_data.update_NAV(nav)
        if stock_symbol in slice and slice[stock_symbol]:
            # update CEF stock price
            stock_price: float = slice[stock_symbol].Value
            CEF_data.update_price(stock_price)
            if self.recent_month != self.Time.month:
                rebalance_flag = True
            
            # calculate discount
            if rebalance_flag:
                if CEF_data.is_ready() and stock_symbol.Value in last_update_date and self.Time.date()  None:
    self._cef_symbol: Symbol = cef_symbol
    self._NAV: float = -1
    self._price: float = -1

def get_CEF_symbol(self) -> Symbol:
    return self._cef_symbol
def update_NAV(self, nav: float) -> None:
    self._NAV = nav
    
def update_price(self, price: float) -> None:
    self._price = price
    
def is_ready(self) -> bool:
    return self._NAV != -1 and self._price != -1
    
def discount(self) -> float:
    # Difference between log market price and log NAV, which is the price premium in relative terms. 
    # In this framework, discounts are negative premiums.
    return np.log(self._price) - np.log(self._NAV)
    
# Quantpedia data
# NOTE: IMPORTANT: Data order must be ascending (datewise)
# NOTE: IMPORTANT: Name of the csv file has to be upper case
class QuantpediaCEF(PythonData):
_last_update_date:Dict[str, datetime.date] = {}
@staticmethod
def get_last_update_date() -> Dict[str, datetime.date]:
   return QuantpediaCEF._last_update_date
# Source: https://finance.yahoo.com/quote/XGDLX?p=XGDLX
def GetSource(self, config, date, isLiveMode):
    return SubscriptionDataSource("data.quantpedia.com/backtesting_data/equity/CEFs/X{0}X.csv".format(config.Symbol.Value), SubscriptionTransportMedium.RemoteFile, FileFormat.Csv)
def Reader(self, config, line, date, isLiveMode):
    data = QuantpediaCEF()
    data.Symbol = config.Symbol
    
    if not line[0].isdigit(): return None
    split = line.split(';')
    
    data.Time = datetime.strptime(split[0], "%d.%m.%Y") + timedelta(days=1)
    data.Value = float(split[1])
    # store last update date
    if config.Symbol.Value not in QuantpediaCEF._last_update_date:
        QuantpediaCEF._last_update_date[config.Symbol.Value] = datetime(1,1,1).date()
    if data.Time.date() > QuantpediaCEF._last_update_date[config.Symbol.Value]:
        QuantpediaCEF._last_update_date[config.Symbol.Value] = data.Time.date()
    return data
# Custom fee model
class CustomFeeModel(FeeModel):
def GetOrderFee(self, parameters):
    fee = parameters.Security.Price * parameters.Order.AbsoluteQuantity * 0.00005
    return OrderFee(CashAmount(fee, "USD"))
