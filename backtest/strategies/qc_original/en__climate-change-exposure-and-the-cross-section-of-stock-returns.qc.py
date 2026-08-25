# Original QuantConnect / library Python
# locale=en slug="climate-change-exposure-and-the-cross-section-of-stock-returns"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

from AlgorithmImports import *
import numpy as np
import statsmodels.api as sm
from typing import List, Dict
from pandas.core.frame import DataFrame
from pandas.core.series import Series
#endregion
class ClimateChangeExposureAndTheCrossSectionOfStockReturns(QCAlgorithm):
def Initialize(self) -> None:
    self.SetStartDate(2000, 1, 1)
    self.SetCash(100_000)
    
    self.exchange_codes: List[str] = ['NYS', 'NAS', 'ASE']    
    self.period: int = 60 # We need 60 months data of pdsi index
    self.month_period: int = 21
    self.quantile: int = 5
    self.leverage: int = 5
    self.min_share_price: int = 5
    self.percentile: float = 0.2
    
    self.data: Dict[Symbol, RollingWindow] = {}
    self.weight: Dict[Symbol, float] = {}
    
    market: Symbol = self.AddEquity('SPY', Resolution.Daily).Symbol
    self.pdsi_symbol: Symbol = self.AddData(QuantpediaPDSI, 'PDSI', Resolution.Daily).Symbol
    self.data[self.pdsi_symbol] = RollingWindow[float](self.period)
    self.fundamental_count: int = 500
    self.fundamental_sorting_key = lambda x: x.DollarVolume
    
    self.selection_flag: bool = False
    self.UniverseSettings.Leverage = self.leverage
    self.UniverseSettings.Resolution = Resolution.Daily
    self.AddUniverse(self.FundamentalSelectionFunction)
    self.settings.daily_precise_end_time = False
    self.Settings.MinimumOrderMarginPortfolioPercentage = 0.
    self.Schedule.On(self.DateRules.MonthStart(market), self.TimeRules.AfterMarketOpen(market), self.Selection)  
def OnSecuritiesChanged(self, changes: SecurityChanges) -> None:
    for security in changes.AddedSecurities:
        security.SetFeeModel(CustomFeeModel())
        
def FundamentalSelectionFunction(self, fundamental: List[Fundamental]) -> List[Symbol]:
    # If PDSI data aren't ready, don't update rolling windows or use history
    if not self.data[self.pdsi_symbol].IsReady:
        return Universe.Unchanged
        
    # Update rolling windows each day
    for stock in fundamental:
        symbol: Symbol = stock.Symbol
        
        if symbol in self.data:
            self.data[symbol].Add(stock.AdjustedPrice)
    
    # Rebalance monthly
    if not self.selection_flag:
        return Universe.Unchanged
    
    selected = [
        x for x in fundamental 
        if x.HasFundamentalData 
        and x.Market == 'usa' 
        and x.Price > self.min_share_price 
        and x.MarketCap != 0 
        and x.SecurityReference.ExchangeId in self.exchange_codes
    ]
    if len(selected) > self.fundamental_count:
        selected = [x for x in sorted(selected, key=self.fundamental_sorting_key, reverse=True)[:self.fundamental_count]]
    
    # Warmup price rolling windows.
    for stock in selected:
        symbol: Symbol = stock.Symbol
        if symbol in self.data:
            continue
        # Need self.period months of daily returns to calculate self.period months momentums
        self.data[symbol] = RollingWindow[float](self.period * self.month_period)
        history: DataFrame = self.History(symbol, self.period * self.month_period, Resolution.Daily)
        if history.empty:
            self.Log(f"Not enough data for {symbol} yet")
            continue
        closes: Series = history.loc[symbol].close
        for time, close in closes.items():
            self.data[symbol].Add(close)
    selected_ready: List[Fundamental] = [x for x in selected if self.data[x.Symbol].IsReady]
    pdsi_last_update_date: Dict[Symbol, datetime.date] = QuantpediaPDSI.get_last_update_date()
    # Check if data is still coming
    if not self.data[self.pdsi_symbol].IsReady or \
        (self.Securities[self.pdsi_symbol].GetLastData() and (self.Time.date() > pdsi_last_update_date[self.pdsi_symbol])):
        return Universe.Unchanged
    
    # Omit small caps
    sorted_by_cap: List[Fundamental] = [x for x in sorted(selected_ready, key=lambda stock: stock.MarketCap)]
    selected_ready = sorted_by_cap[int(len(sorted_by_cap) * 0.2):] # In the bottom 20% percentile are dropped
    
    # Create independent variable in regression
    x_regression: List[float] = [x for x in self.data[self.pdsi_symbol]]
    x_regression: np.ndarray = np.array(x_regression).T
    x_regression = sm.add_constant(x_regression) # Add constant to independent variable
    
    regression_betas: Dict[Fundamental, float] = {}
    
    for stock in selected_ready:
        symbol = stock.Symbol
        
        # Separate monthly prices
        daily_prices: List[float] = [x for x in self.data[symbol]]
        separate_months: List[float] = [daily_prices[x:x+self.month_period] for x in range(0, len(daily_prices),self.month_period)]
        
        # Create monthly returns as dependent variable
        y_regression: List[float] = []
        for month in separate_months:
            monthly_return: float = (month[0] - month[-1]) / month[-1] # Calculate monthly return
            y_regression.append(monthly_return) # Add monthly return to list
            
        # Get and store beta about each stock in universe from regression model
        regression_model: RegressionResultWrapper = sm.OLS(endog=y_regression, exog=x_regression).fit()
        
        # Store beta of this regression
        regression_betas[stock] = regression_model.params[1]
        
    # Check if enough stocks are picked
    if len(regression_betas)  None:
    # Check if there are pdsi data
    if self.pdsi_symbol in data and data[self.pdsi_symbol]:
        # Calculate pdsi index from pdsi values of all regions
        pdsi_values: List[float] = [x for x in data[self.pdsi_symbol].Pdsi_Values]
        pdsi_index: float = np.mean(pdsi_values)
        # Update rolling window for pdsi index
        self.data[self.pdsi_symbol].Add(pdsi_index)
    
    # Rebalance monthly
    if not self.selection_flag:
        return
    self.selection_flag = False
    
    # Trade execution
    portfolio: List[PortfolioTarget] = [PortfolioTarget(symbol, w) for symbol, w in self.weight.items() if symbol in data and data[symbol]]
    self.SetHoldings(portfolio, True)
    # clear dictiorany for new portfolio selection
    self.weight.clear()
    
def Selection(self) -> None:
    self.selection_flag = True
    
# Commitments of Traders data.
# Data description: https://commitmentsoftraders.org/wp-content/uploads/Static/CoTData/file_key.html
class QuantpediaPDSI(PythonData):
_last_update_date:Dict[Symbol, datetime.date] = {}
@staticmethod
def get_last_update_date() -> Dict[Symbol, datetime.date]:
   return QuantpediaPDSI._last_update_date
def GetSource(self, config: SubscriptionDataConfig, date: datetime, isLiveMode: bool) -> SubscriptionDataSource:
    return SubscriptionDataSource(f"data.quantpedia.com//backtesting_data/index/{config.Symbol.Value}.csv", SubscriptionTransportMedium.RemoteFile, FileFormat.Csv)
def Reader(self, config: SubscriptionDataConfig, line: str, date: datetime, isLiveMode: bool) -> BaseData:
    data = QuantpediaPDSI()
    data.Symbol = config.Symbol
    
    if not line[0].isdigit(): return None
    split = line.split(';')
    
    # Prevent lookahead bias.
    data.Time = datetime.strptime(split[0], "%d.%m.%Y") + timedelta(days=1)
    data['PDSI_VALUES'] = [float(x) for x in split[1:]]
    data.Value = float(split[1])
    if config.Symbol not in QuantpediaPDSI._last_update_date:
        QuantpediaPDSI._last_update_date[config.Symbol] = datetime(1,1,1).date()
    if data.Time.date() > QuantpediaPDSI._last_update_date[config.Symbol]:
        QuantpediaPDSI._last_update_date[config.Symbol] = data.Time.date()
    return data
    
# Custom fee model
class CustomFeeModel(FeeModel):
def GetOrderFee(self, parameters: OrderFeeParameters) -> OrderFee:
    fee: float = parameters.Security.Price * parameters.Order.AbsoluteQuantity * 0.00005
    return OrderFee(CashAmount(fee, "USD"))
