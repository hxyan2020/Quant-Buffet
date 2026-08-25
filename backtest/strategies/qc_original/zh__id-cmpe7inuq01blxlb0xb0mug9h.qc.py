# Original QuantConnect / library Python
# locale=zh slug="空头利率的意外变化"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

from AlgorithmImports import *
from io import StringIO
from typing import List, Dict
from pandas.core.frame import DataFrame
from numpy import isnan
class SurpriseinShortInterest(QCAlgorithm):
def Initialize(self) -> None:
    self.SetStartDate(2017, 1, 1)
    self.SetCash(100_000)
    self.period: int = 21
    self.std_period: int = 12
    self.leverage: int = 5
    self.quantile: int = 10
    
    market: int = self.AddEquity('SPY', Resolution.Daily).Symbol
    
    self.short_interest: Dict[Symbol, RollingWindow] = {}
    self.short_interest_ratio: Dict[Symbol, float] = {}
    self.short_interest_ratio_period: int = 12
    
    self.weight: Dict[Symbol, float] = {}
    # source: https://www.finra.org/finra-data/browse-catalog/equity-short-interest/data
    text: str = self.Download('data.quantpedia.com/backtesting_data/economic/short_volume.csv')
    self.short_volume_df: DataFrame = pd.read_csv(StringIO(text), delimiter=';')
    self.short_volume_df['date'] = pd.to_datetime(self.short_volume_df['date']).dt.date
    self.short_volume_df.set_index('date', inplace=True)
    self.fundamental_count: int = 3_000
    self.fundamental_sorting_key = lambda x: x.MarketCap
    self.selection_flag: bool = False
    self.UniverseSettings.Resolution = Resolution.Daily
    self.AddUniverse(self.FundamentalSelectionFunction)
    self.settings.daily_precise_end_time = False
    self.Settings.MinimumOrderMarginPortfolioPercentage = 0.
    self.Schedule.On(self.DateRules.MonthStart(market), self.TimeRules.AfterMarketOpen(market), self.Selection)
def OnSecuritiesChanged(self, changes: SecurityChanges) -> None:
    for security in changes.AddedSecurities:
        security.SetFeeModel(CustomFeeModel())
        security.SetLeverage(self.leverage)
def FundamentalSelectionFunction(self, fundamental: List[Fundamental]) -> List[Symbol]:
    # monthly rebalance
    if not self.selection_flag:
        return Universe.Unchanged

    # check last date on custom data
    if self.Time.date() > self.short_volume_df.index[-1] or self.Time.date()  self.fundamental_count:
        selected = [x for x in sorted(selected, key=self.fundamental_sorting_key, reverse=True)[:self.fundamental_count]]
    surprise: Dict[Fundamental, float] = {}
    for stock in selected:
        symbol: Symbol = stock.Symbol
        ticker: str = symbol.Value
        if symbol not in self.short_interest:
            # create RollingWindow for specific stock symbol
            self.short_interest[symbol] = RollingWindow[float](self.period)
        if not self.short_interest[symbol].IsReady:
            continue
        short_interest_values: List[float] = [x for x in self.short_interest[symbol]]
        mid_month_short_interest: float = short_interest_values[int(len(short_interest_values)/ 2)]
        short_interest_ratio: float = mid_month_short_interest / stock.EarningReports.BasicAverageShares.ThreeMonths
        
        # update monthly short interest ratio
        if symbol not in self.short_interest_ratio:
            self.short_interest_ratio[symbol] = RollingWindow[float](self.short_interest_ratio_period)
        self.short_interest_ratio[symbol].Add(short_interest_ratio)
        
        if self.short_interest_ratio[symbol].IsReady:
            short_interest_ratio_values: np.ndarray = np.array([x for x in self.short_interest_ratio[symbol]])
            si_mean: float = np.mean(short_interest_ratio_values)
            
            # Source paper: volatility of the ratio - In particular, we use the past twelve-month moving window standard deviation of the short interest ratio.
            si_volatility: float = np.std(short_interest_ratio_values) * np.sqrt(self.std_period)
            
            surprise[stock] = (short_interest_ratio_values[0] - si_mean) / si_volatility
                
    if len(surprise)  None:
    # monthly rebalance        
    if not self.selection_flag:
        return
    self.selection_flag = False
    
    # Trade execution
    portfolio: List[PortfolioTarget] = [PortfolioTarget(symbol, w) for symbol, w in self.weight.items() if symbol in data and data[symbol]]
    self.SetHoldings(portfolio, True)
    self.weight.clear()
        
def Selection(self) -> None:
    self.selection_flag = True
# Custom fee model
class CustomFeeModel(FeeModel):
def GetOrderFee(self, parameters: OrderFeeParameters) -> OrderFee: 
    fee: float = parameters.Security.Price * parameters.Order.AbsoluteQuantity * 0.00005
    return OrderFee(CashAmount(fee, "USD"))
