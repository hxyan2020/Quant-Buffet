# Original QuantConnect / library Python
# locale=en slug="market-breadth-in-global-equities"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

from AlgorithmImports import *
from pandas.core.frame import DataFrame
class MarketBreadthInGlobalEquities(QCAlgorithm):
def Initialize(self):
    self.SetStartDate(2000, 1, 1)
    self.SetCash(100000)
    
    etf_tickers: List[Tuple[str, str]] = [
        # (CountryId, ticker)
        ("AUS", "EWA"), # iShares MSCI Australia Index ETF
        ("BRA", "EWZ"),  # iShares MSCI Brazil Index ETF
        ("CAN", "EWC"),  # iShares MSCI Canada Index ETF
        ("CHN", "FXI"),  # iShares China Large-Cap ETF
        ("FRA", "EWQ"),  # iShares MSCI France Index ETF
        ("DEU", "EWG"),  # iShares MSCI Germany ETF
        ("HKG", "EWH"),  # iShares MSCI Hong Kong Index ETF
        ("JPN", "EWJ"),  # iShares MSCI Japan Index ETF
        ("MEX", "EWW"),  # iShares MSCI Mexico Inv. Mt. Idx
        ("NLD", "EWN"),  # iShares MSCI Netherlands Index ETF
        ("SGP", "EWS"),  # iShares MSCI Singapore Index ETF
        ("KOR", "EWY"),  # iShares MSCI South Korea ETF
        ("CHE", "EWL"),  # iShares MSCI Switzerland Index ETF
        ("GBR", "EWU"),  # iShares MSCI United Kingdom Index ETF
        ("USA", "SPY"),  # SPDR S&P 500 ETF
        ("IRL", "EIRL"),  # iShares MSCI Ireland ETF
        ("ISR", "EIS"),  # iShares MSCI Israel ETF    
    ]
    
    self.data: Dict[Symbol, SymbolData] = {}
    self.etf_by_country: Dict[str, Symbol] = {}
    
    self.long: Dict[Symbol] = []
    self.short: Dict[Symbol] = []
    
    self.period: int = 2 * 12 * 21 # 2 years of daily closes
    self.count_to_invest: int = 2 # We go 2 etfs long and 2 etfs short, because our universe consists of country ETF from 17 countries.
    self.leverage: int = 3
    
    for country_id, ticker in etf_tickers:
        security: Security = self.AddEquity(ticker, Resolution.Daily)
        security.SetFeeModel(CustomFeeModel())
        security.SetLeverage(self.leverage)
        
        self.etf_by_country[country_id] = security.Symbol
        
    market: Symbol = self.AddEquity("SPY", Resolution.Daily).Symbol
    
    self.selection_flag: bool = False
    self.UniverseSettings.Resolution = Resolution.Daily
    self.Settings.MinimumOrderMarginPortfolioPercentage = 0.
    self.AddUniverse(self.FundamentalSelectionFunction)
    self.Schedule.On(self.DateRules.MonthStart(market), self.TimeRules.AfterMarketOpen(market), self.Selection)
    self.settings.daily_precise_end_time = False
def FundamentalSelectionFunction(self, fundamental: List[Fundamental]) -> List[Symbol]:
    for stock in fundamental:
        symbol: Symbol = stock.Symbol
        
        if symbol in self.data:
            self.data[symbol].update(stock.AdjustedPrice)
    
    if not self.selection_flag:
        return Universe.Unchanged
    
    selected: List[Fundamental] = [x for x in fundamental if x.HasFundamentalData and x.CompanyReference.BusinessCountryID in self.etf_by_country]
    
    country_stocks: Dict[str, CountryStocks] = {}
    for stock in selected:
        symbol: Symbol = stock.Symbol
        if symbol not in self.data:
            self.data[symbol] = SymbolData(self.period)
            history: DataFrame = self.History(symbol, self.period, Resolution.Daily)
            if history.empty:
                self.Log(f"Not enough data for {symbol} yet")
                continue
            closes: pd.Series = history.loc[symbol].close
            for time, close in closes.items():
                self.data[symbol].update(close)
        
        if self.data[symbol].is_ready():
            country_id: str = stock.CompanyReference.BusinessCountryID
            performance: float = self.data[symbol].performance()
        
            if country_id not in country_stocks:
                country_stocks[country_id] = CountryStocks()
            
            if performance > 0.:
                country_stocks[country_id].increase_rising()
            else:
                country_stocks[country_id].increase_falling()
            
    if len(country_stocks) == 0:
        return Universe.Unchanged
        
    sorted_by_market_breadth: List[str] = [x[0] for x in sorted(country_stocks.items(), key=lambda item: item[1].market_breadth())]
    
    self.long = [self.etf_by_country[country_id] for country_id in sorted_by_market_breadth[-self.count_to_invest:]]
    self.short = [self.etf_by_country[country_id] for country_id in sorted_by_market_breadth[:self.count_to_invest]]
        
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
    
class SymbolData():
def __init__(self, period: int):
    self._closes:RollingWindow = RollingWindow[float](period)
    
def update(self, close: float) -> None:
    self._closes.Add(close)
    
def is_ready(self) -> bool:
    return self._closes.IsReady
    
def performance(self) -> float:
    return self._closes[0] / self._closes[self._closes.Count - 1] - 1
    
class CountryStocks():
def __init__(self):
    self._rising_stocks_count: int = 0
    self._falling_stocks_count: int = 0
    
def increase_rising(self) -> None:
    self._rising_stocks_count += 1
    
def increase_falling(self) -> None:
    self._falling_stocks_count += 1
    
def market_breadth(self) -> float:
    result: float = (self._rising_stocks_count - self._falling_stocks_count) / (self._rising_stocks_count + self._falling_stocks_count)
    return result 
    
# Custom fee model.
class CustomFeeModel(FeeModel):
def GetOrderFee(self, parameters):
    fee = parameters.Security.Price * parameters.Order.AbsoluteQuantity * 0.00005
    return OrderFee(CashAmount(fee, "USD"))
