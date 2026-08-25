# Original QuantConnect / library Python
# locale=en slug="return-range-predicts-stock-returns"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

from AlgorithmImports import *
from functools import reduce
#endregion

class ReturnRangePredictsStockReturns(QCAlgorithm):

def Initialize(self):
    self.SetStartDate(2010, 1, 1)
    self.SetCash(100000)
    
    self.period:int = 22        # need n daily prices
    self.cap_quantile:int = 5
    self.range_quantile:int = 5
    self.leverage:int = 5
    self.min_share_price:float = 5.

    self.prices:Dict[Symbol, RollingWindow] = {}
    self.weight:Dict[Symbol, float] = {}

    self.countries_ISO:List[str] = [
        'AUS', 'AUT', 'BEL', 'CAN', 'DNK', 'FIN', 'FRA', 'DEU', 'GRC', 'HKG', 'IRL', 'ITA',
        'JPN', 'NLD', 'NZL', 'NOR', 'PRT', 'SGP', 'ESP', 'SWE', 'CHE', 'GBR', 'USA', 'ARG',
        'BRA', 'CHL', 'CHN', 'IND', 'KOR', 'MYS', 'MEX', 'PHL', 'POL', 'ZAF', 'TWN', 'THA', 'TUR'
    ]

    self.market_symbol:Symbol = self.AddEquity('SPY', Resolution.Daily).Symbol

    self.fundamental_count:int = 3000
    self.fundamental_sorting_key = lambda x: x.MarketCap

    self.selection_flag:bool = False
    self.UniverseSettings.Resolution = Resolution.Daily
    self.AddUniverse(self.FundamentalSelectionFunction)
    self.Settings.MinimumOrderMarginPortfolioPercentage = 0
    self.Schedule.On(self.DateRules.MonthStart(self.market_symbol), self.TimeRules.BeforeMarketClose(self.market_symbol, 0), self.Selection)

def OnSecuritiesChanged(self, changes: SecurityChanges) -> None:
    for security in changes.AddedSecurities:
        security.SetFeeModel(CustomFeeModel())
        security.SetLeverage(self.leverage)
        
def FundamentalSelectionFunction(self, fundamental: List[Fundamental]) -> None:
    # daily update stock prices
    for stock in fundamental:
        symbol:Symbol = stock.Symbol

        if symbol in self.prices:
            self.prices[symbol].update(stock.AdjustedPrice)

    if not self.selection_flag:
        return Universe.Unchanged

    selected:List[Fundamental] = [x for x in fundamental if x.HasFundamentalData and x.MarketCap != 0 and \
        x.AdjustedPrice >= self.min_share_price and x.CompanyReference.BusinessCountryID in self.countries_ISO]
    if len(selected) > self.fundamental_count:
        selected = [x for x in sorted(selected, key=self.fundamental_sorting_key, reverse=True)[:self.fundamental_count]]
        
    stocks_bucket:Dict[str, List[Fundamental]] = {}

    for stock in selected:
        country_ISO:str = stock.CompanyReference.BusinessCountryID 
        sector:str = str(stock.AssetClassification.MorningstarSectorCode)
        bucket_identificator:str = country_ISO + '+' + sector

        if bucket_identificator not in stocks_bucket:
            stocks_bucket[bucket_identificator] = []

        stocks_bucket[bucket_identificator].append(stock)

    # make sure there are enough buckets
    if len(stocks_bucket)  None:
    # rebalance monthly
    if not self.selection_flag:
        return
    self.selection_flag = False
    
    # trade execution
    portfolio:List[PortfolioTarget] = [PortfolioTarget(symbol, w) for symbol, w in self.weight.items() if symbol in data and data[symbol]]
    self.SetHoldings(portfolio, True)

    self.weight.clear()

def SelectLowAndHighRangeStocks(self, stocks:List) -> (List, List):
    stocks_ranges:Dict[Symbol, float] = {}

    for stock in stocks:
        symbol:Symbol = stock.Symbol

        if symbol not in self.prices:
            history = self.History(symbol, self.period, Resolution.Daily)
            if history.empty or len(history)  None:
    self.selection_flag = True

class SymbolData:
def __init__(self, period: int):
    self.prices:RollingWindow = RollingWindow[float](period)

def update(self, price: float) -> None:
    self.prices.Add(price)

def get_range(self) -> float:
    daily_prices:np.array = np.array([x for x in self.prices])
    daily_returns:List[float] = list((daily_prices[:-1] - daily_prices[1:]) / daily_prices[1:])

    daily_max_return:float = max(daily_returns)
    daily_min_return:float = min(daily_returns)

    return daily_max_return - daily_min_return

def is_ready(self) -> bool:
    return self.prices.IsReady

# Custom fee model
class CustomFeeModel(FeeModel):
def GetOrderFee(self, parameters):
    fee = parameters.Security.Price * parameters.Order.AbsoluteQuantity * 0.00005
    return OrderFee(CashAmount(fee, "USD"))
