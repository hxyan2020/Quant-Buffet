# Original QuantConnect / library Python
# locale=zh slug="在股票中的动量效应应用违约风险过滤"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

from AlgorithmImports import *
import numpy as np
import statsmodels.api as sm
from typing import List, Dict
#endregion
class DefaultRiskFilterAppliedOnMomentumEffectWithinStocks(QCAlgorithm):
def Initialize(self) -> None:
    self.SetStartDate(2010, 1, 1)
    self.SetCash(100000)
    
    self.exchange_codes:List[str] = ['NYS', 'NAS', 'ASE']
    self.symbol: Symbol  = self.AddEquity("SPY", Resolution.Daily).Symbol
    
    self.data: Dict[Symbol, SymbolData] = {}
    self.managed_queue: List[RebalanceQueueItem] = []
    
    self.period: int = 6 * 21    # Storing prices for 6 months
    self.holding_months: int = 6 # Holding 1/6 of whole portfolio for six months
    self.month_period: int = 21
    self.leverage: int = 5
    self.quantile: int = 10
    self.min_share_price: int = 1
    
    self.regression_period: int = 21 * 3 # Three months of DEFt daily data
    self.regression_data: RollingWindow = RollingWindow[float](self.regression_period)
    
    self.DEFt: Symbol = self.AddData(QuantpediaBAMLH0A3HYC, 'BAMLH0A3HYC', Resolution.Daily).Symbol
    self.default_shock: RollingWindow = RollingWindow[float](12 * 5)   # Each month stores residual from regression for 5 years.
    
    self.fundamental_count: int = 500
    self.fundamental_sorting_key = lambda x: x.DollarVolume
    self.stop_trading: bool = False
    self.selection_flag: bool = False
    self.Settings.MinimumOrderMarginPortfolioPercentage = 0.
    self.settings.daily_precise_end_time = False
    self.UniverseSettings.Resolution = Resolution.Daily
    self.AddUniverse(self.FundamentalSelectionFunction)
    self.Schedule.On(self.DateRules.MonthEnd(self.symbol), self.TimeRules.AfterMarketOpen(self.symbol), self.Selection)
def OnSecuritiesChanged(self, changes: SecurityChanges) -> None:
    for security in changes.AddedSecurities:
        security.SetFeeModel(CustomFeeModel())
        security.SetLeverage(self.leverage)
        
def FundamentalSelectionFunction(self, fundamental: List[Fundamental]) -> List[Symbol]:
    # update the rolling window every day
    for stock in fundamental:
        symbol: Symbol = stock.Symbol
        # store monthly price
        if symbol in self.data:
            self.data[symbol].update(stock.AdjustedPrice)
    if not self.selection_flag:
        return Universe.Unchanged
    selected: List[Fundamental] = [
        x for x in fundamental if x.HasFundamentalData and x.Market == 'usa' and x.Price > self.min_share_price and \
        x.SecurityReference.ExchangeId in self.exchange_codes
    ]
    if len(selected) > self.fundamental_count:
        selected = [x for x in sorted(selected, key=self.fundamental_sorting_key, reverse=True)[:self.fundamental_count]]
    six_months_momentum = {}
    # warmup price rolling windows
    for stock in selected:
        symbol: Symbol = stock.Symbol
        if symbol not in self.data:
            self.data[symbol] = SymbolData(self.period)
            history = self.History(symbol, self.period, Resolution.Daily)
            if history.empty:
                self.Log(f"Not enough data for {symbol} yet")
                continue
            closes = history.loc[symbol].close
            for time, close in closes.items():
                self.data[symbol].update(close)
        if not self.data[symbol].is_ready():
            continue
    
        six_months_closes: List[float] = [x for x in self.data[symbol]._closes][:self.month_period] # Skip last month according to strategy
        six_months_return: float = (six_months_closes[0] - six_months_closes[-1]) / six_months_closes[-1] 
        
        six_months_momentum[symbol] = six_months_return
    
    long: List[Symbol] = []
    short: List[Symbol] = []
    
    # continue only if we have enough stocks for decile selection
    if len(six_months_momentum) >= self.quantile:
        quantile: int = int(len(six_months_momentum) / self.quantile)
        sorted_by_momentum: List[Symbol] = [x[0] for x in sorted(six_months_momentum.items(), key=lambda item: item[1])]
        
        long = sorted_by_momentum[-quantile:] # top decile are winners
        short = sorted_by_momentum[:quantile] # bottom decile are losers
        
        long_w: float = self.Portfolio.TotalPortfolioValue / self.holding_months / len(long)
        short_w: float = self.Portfolio.TotalPortfolioValue / self.holding_months / len(short)
        
        # symbol/quantity collection
        long_symbol_q: List[Tuple[Symbol, int]] = [(x, np.floor(long_w / self.data[x]._last_price)) for x in long]
        short_symbol_q: List[Tuple[Symbol, int]] = [(x, -np.floor(short_w / self.data[x]._last_price)) for x in short]
        
        self.managed_queue.append(RebalanceQueueItem(long_symbol_q + short_symbol_q))
    
    return long + short
def OnData(self, data: Slice) -> None:
    if self.DEFt in data:
        if data[self.DEFt]:
            price: float = data[self.DEFt].Value
            if price != 0:
                self.regression_data.Add(price)
    
    # make sure DEFt data is still comming in
    DEFt_last_update_date: Dict[Symbol, datetime.date] = QuantpediaBAMLH0A3HYC.get_last_update_date()
    if self.Securities[self.DEFt].GetLastData() and self.Time.date() > DEFt_last_update_date[self.DEFt]:
        self.stop_trading = True
        if self.Portfolio.Invested:
            self.Liquidate()
        return
    
    if not self.selection_flag:
        return
    self.selection_flag = False
    
    current_residual: Union[None, float] = None
    if self.regression_data.IsReady:
        regression_data: List[float] = [x for x in self.regression_data]
        Y: List[float] = regression_data[:self.month_period] # Current month data
        X: List[float] = [
            regression_data[self.month_period:self.month_period * 2], # Month before
            regression_data[-self.month_period:] # Month which was 2 Months before
        ]
        
        regression_model: RegressionResultWrapper = self.MultipleLinearRegression(X, Y)
        
        # store last residual
        current_residual = regression_model.resid[-1]
        self.default_shock.Add(current_residual)
    
    invest_flag: bool = False
    
    if self.default_shock.IsReady and current_residual:
        residuals_median: float = np.median([x for x in self.default_shock])
        
        parts_to_remove: List[RebalanceQueueItem] = []
        
        # go through each part of portfolio 
        for portfolio_part in self.managed_queue:
            # liquidate stocks with 6 months holding
            if portfolio_part.holding_time == 6:
                for symbol, quantity in portfolio_part.symbol_q:
                    if self.Portfolio[symbol].Invested:
                        # liquidate long and short stocks in this part of portfolio
                        self.MarketOrder(symbol, -quantity)
                
                parts_to_remove.append(portfolio_part)
            
            # Increment holding time of 1/6 portfolio    
            portfolio_part.holding_time += 1
        
        for part_to_remove in parts_to_remove:
            # Remove portfolio part, because we held it for 6 months
            self.managed_queue.remove(part_to_remove)
    
        # Check if we invest or liquidate
        if current_residual > residuals_median:
            invest_flag = True
    
    # Default shock data aren't ready, so we have to remove portofolio part, which was added.   
    elif len(self.managed_queue) > 0:
        self.managed_queue.pop()
    
    # Trade execution
    if invest_flag:
        # We either hold portfolio and invest into the new part of it
        # Or invest into whole portfolio, because we liquidated it
        
        if self.Portfolio.Invested:
            # Get portfolio part, which was lastly added
            portfolio_part = self.managed_queue[-1]
            # We keep holding old parts of portfolio and we invest into the new one
            open_symbol_q = []
            for symbol, quantity in portfolio_part.symbol_q:
                if symbol in data and data[symbol]:
                    self.MarketOrder(symbol, quantity)
                    open_symbol_q.append((symbol, quantity))
            portfolio_part.symbol_q = open_symbol_q
        else:
            # We need to invest into whole portfolio, because we liquidated it
            for portfolio_part in self.managed_queue:
                # Go long and short stocks in this part of portofolio
                open_symbol_q = []
                for symbol, quantity in portfolio_part.symbol_q:
                    if symbol in data and data[symbol]:
                        self.MarketOrder(symbol, quantity)
                        open_symbol_q.append((symbol, quantity))
                portfolio_part.symbol_q = open_symbol_q
                        
    else: # Signal is to Liquidate whole portfolio
        self.Liquidate()
   
def MultipleLinearRegression(self, x, y):
    x = np.array(x).T
    x = sm.add_constant(x)
    result: RegressionResultWrapper = sm.OLS(endog=y, exog=x).fit()
    return result

def Selection(self) -> None:
    if not self.stop_trading:
        self.selection_flag = True
    
class RebalanceQueueItem():
def __init__(self, symbol_q: List[Symbol]) -> None:
    self.symbol_q: List[Symbol] = symbol_q
    self.holding_time: int = 0 # Holding in months
    
class SymbolData():
def __init__(self, period: int) -> None:
    self._last_price: Union[None, float] = None
    self._closes: RollingWindow = RollingWindow[float](period)

def update(self, close: float) -> None:
    self._closes.Add(close)
    self._last_price = close
    
def is_ready(self) -> bool:
    return self._closes.IsReady
# Custom fee model
class CustomFeeModel(FeeModel):
def GetOrderFee(self, parameters: OrderFeeParameters) -> OrderFee:
    fee: float = parameters.Security.Price * parameters.Order.AbsoluteQuantity * 0.00005
    return OrderFee(CashAmount(fee, "USD"))
    
# Quantpedia data.
# NOTE: IMPORTANT: Data order must be ascending (datewise)
class QuantpediaBAMLH0A3HYC(PythonData):
_last_update_date:Dict[Symbol, datetime.date] = {}
@staticmethod
def get_last_update_date() -> Dict[Symbol, datetime.date]:
   return QuantpediaBAMLH0A3HYC._last_update_date
def GetSource(self, config: SubscriptionDataConfig, date: datetime, isLiveMode: bool) -> SubscriptionDataSource:
    return SubscriptionDataSource("data.quantpedia.com/backtesting_data/index/{0}.csv".format(config.Symbol.Value), SubscriptionTransportMedium.RemoteFile, FileFormat.Csv)
def Reader(self, config: SubscriptionDataConfig, line: str, date: datetime, isLiveMode: bool) -> BaseData:
    data = QuantpediaBAMLH0A3HYC()
    data.Symbol = config.Symbol
    
    if not line[0].isdigit(): return None
    split: str = line.split(';')
    
    if split[1] != '.':
        data.Time = datetime.strptime(split[0], "%Y-%m-%d") + timedelta(days=1)
        value = float(split[1])
        data.Value = value
        if config.Symbol not in QuantpediaBAMLH0A3HYC._last_update_date:
            QuantpediaBAMLH0A3HYC._last_update_date[config.Symbol] = datetime(1,1,1).date()
        if data.Time.date() > QuantpediaBAMLH0A3HYC._last_update_date[config.Symbol]:
            QuantpediaBAMLH0A3HYC._last_update_date[config.Symbol] = data.Time.date()
    return data
