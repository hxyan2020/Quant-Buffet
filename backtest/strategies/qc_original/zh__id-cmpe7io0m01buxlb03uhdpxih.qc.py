# Original QuantConnect / library Python
# locale=zh slug="新兴市场中的方差缩放动量策略"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

from AlgorithmImports import *
import numpy as np
from pandas.core.frame import DataFrame
class VarianceScaledMomentumInEmergingMarkets(QCAlgorithm):
def Initialize(self):
    self.SetStartDate(2010, 1, 1)
    self.SetCash(100000)
    self.period:int = 13                    # need n monthly prices
    self.volatility_period:int = 126        # n daily prices for volatility targeting
    self.target_volatility:float = 0.10     # 10% of volatility targeting
    self.data:Dict[Symbol, SymbolData] = {} # storing objects of SymbolData for each stock
    self.weight:Dict[Symbol, float] = {}    # storing stock weights after volatility targeting calculation
    self.business_countries_IDs:List[str] = ['BRA', 'TCD', 'CHN', 'GRC', 'IND', 'MEX', 'ZAF', 'KOR', 'TWN', 'MYS', 'IDN', 'PAK', 'POL', 'RUS', 'THA', 'TUR']
    self.min_share_price:float = 1.
    self.quantile:int = 5
    self.leverage:int = 5
    market:Symbol = self.AddEquity("SPY", Resolution.Daily).Symbol
    self.selection_flag:int = False
    self.UniverseSettings.Resolution = Resolution.Daily
    self.settings.daily_precise_end_time = False
    self.Settings.MinimumOrderMarginPortfolioPercentage = 0.
    self.AddUniverse(self.FundamentalSelectionFunction)
    self.Schedule.On(self.DateRules.MonthStart(market), self.TimeRules.AfterMarketOpen(market), self.Selection)
def OnSecuritiesChanged(self, changes: SecurityChanges) -> None:
    for security in changes.AddedSecurities:
        security.SetFeeModel(CustomFeeModel())
        security.SetLeverage(self.leverage)
def FundamentalSelectionFunction(self, fundamental: List[Fundamental]) -> List[Symbol]:
    # updating daily and monthly prices
    for stock in fundamental:
        symbol:Symbol = stock.Symbol
        if symbol in self.data:
            # update daily prices
            self.data[symbol].update_daily_closes(stock.AdjustedPrice)
            # update monthly prices on selection
            if self.selection_flag:
                self.data[symbol].update_monthly_closes(stock.AdjustedPrice)
    # monthly rebalance
    if not self.selection_flag:
        return Universe.Unchanged
    selected:List[Fundamental] = [
        x for x in fundamental if x.HasFundamentalData and 
        x.CompanyReference.BusinessCountryID in self.business_countries_IDs and x.Price >= self.min_share_price
    ]
    countries_with_stocks = {} # storing stocks under BusinessCountryID
    # warm up prices
    for stock in selected:
        symbol:Symbol = stock.Symbol
        if symbol not in self.data:
            self.data[symbol] = SymbolData(self.period, self.volatility_period)
            history:DataFrame = self.History(symbol, self.period * 21, Resolution.Daily)
            if history.empty:
                continue
            day_counter:int = 1
            closes:pd.Series = history.loc[symbol].close
            for time, close in closes.items():
                # update daily prices
                self.data[symbol].update_daily_closes(close)
                # update monthly prices
                if day_counter == 1 or day_counter % 21 == 0:
                    self.data[symbol].update_monthly_closes(close)
        if self.data[symbol].is_ready():
            country_id = stock.CompanyReference.BusinessCountryID
            # check if budiness country id has it's own list in dictionary
            if not country_id in countries_with_stocks:
                # create list for business country id
                countries_with_stocks[country_id] = []
            # add stock to business country id
            countries_with_stocks[country_id].append(symbol)
    # can't perform quantile selection
    if len(countries_with_stocks)  None:
    if not self.selection_flag:
        return
    self.selection_flag = False
    # Trade execution.
    portfolio:List[PortfolioTarget] = [PortfolioTarget(symbol, w) for symbol, w in self.weight.items() if symbol in data and data[symbol]]
    self.SetHoldings(portfolio, True)
    self.weight.clear()
def Selection(self) -> None:
    self.selection_flag = True
def CalculateAverageCountryMomentum(self, countries_with_stocks) -> Dict:
    ''' calculate and return average momentum for each stock in country based on business country id '''
    countries_with_avg_mom = {}
    for business_id, stock_symbols in countries_with_stocks.items():
        # exclude country if it doesn't have enough stocks
        if len(stock_symbols)  Dict:
    ''' select long and short countries, then select and return long and short countries stocks from them '''
    countries_stocks = {}
    for business_id, stock_symbols in countries_with_stocks.items():
        # add to long countries with stocks
        if business_id in long_quintile or business_id in short_quintile:
            # get long and short stocks for current country
            long_stocks, short_stocks = self.SelectLongAndShort(stock_symbols)
            countries_stocks[business_id] = [long_stocks, short_stocks]
    return countries_stocks
def SelectLongAndShort(self, stock_symbols):
    ''' select and return long and short stocks from country '''
    # sort country stocks by their momentum
    sorted_by_mom = [x for x in sorted(stock_symbols, key=lambda x: self.data[x].last_month_skip_perf())]
    # perform quintile selection
    if len(stock_symbols) >= 5:
        quintile = int(len(stock_symbols) / 5)
        # select long and short stocks
        long_stocks = sorted_by_mom[-quintile:]
        short_stocks = sorted_by_mom[:quintile]
    # select one top stock and one bottom stock
    else:
        # select long and short stocks
        long_stocks = sorted_by_mom[-1:]
        short_stocks = sorted_by_mom[:1]
    return long_stocks, short_stocks
def CalculateVolatilityTargeting(self, countries_stocks) -> Dict:
    ''' calculate weights of long and short stock and store them in self.weight dictionary '''
    # equally weighted countries
    length = len(countries_stocks)
    result_weight:Dict = {}
    # make variance weighting
    for _, long_short in countries_stocks.items():
        long = long_short[0]
        short = long_short[1]
        # calculate volatility targeting for current country
        df = pd.DataFrame()
        weights = []
        # get daily prices for long part of current country
        for symbol in long:
            df[str(symbol)] = [x for x in self.data[symbol].daily_closes]
            weights.append(1 / len(long) / length)
        # get daily prices for short part of current country
        for symbol in short:
            df[str(symbol)] = [x for x in self.data[symbol].daily_closes]
            weights.append(1 / len(short) / length)
        weights = np.array(weights)
        daily_returns = df.pct_change()
        portfolio_vol = np.sqrt(np.dot(weights.T, np.dot(daily_returns.cov() * self.volatility_period, weights.T)))
        leverage = self.target_volatility / portfolio_vol
        # equally weighted long part of current country
        for symbol in long:
            result_weight[symbol] = (1 / len(long) / length) * leverage
        # equally weighted short part of current country
        for symbol in short:
            result_weight[symbol] = (1 / len(short) / length) * leverage
    return result_weight
class SymbolData():
def __init__(self, monthly_period, daily_period):
    # storing monthly prices for performance calcutation
    self.monthly_closes = RollingWindow[float](monthly_period)
    # storing daily prices for volatility targeting calculation
    self.daily_closes = RollingWindow[float](daily_period)
def update_daily_closes(self, close):
    self.daily_closes.Add(close)
def update_monthly_closes(self, close):
    self.monthly_closes.Add(close)
def is_ready(self):
    return self.monthly_closes.IsReady and self.daily_closes.IsReady
def last_month_skip_perf(self):
    monthly_closes = np.array([x for x in self.monthly_closes][1:])
    monthly_returns = (monthly_closes[:-1] - monthly_closes[1:]) / monthly_closes[1:]
    return np.mean(monthly_returns)
# Custom fee model
class CustomFeeModel(FeeModel):
def GetOrderFee(self, parameters):
    fee = parameters.Security.Price * parameters.Order.AbsoluteQuantity * 0.00005
    return OrderFee(CashAmount(fee, "USD"))
