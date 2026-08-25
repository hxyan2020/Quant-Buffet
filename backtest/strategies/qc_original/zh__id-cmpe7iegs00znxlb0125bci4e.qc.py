# Original QuantConnect / library Python
# locale=zh slug="股票中的特质因子动量效应"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

from scipy import stats
from AlgorithmImports import *
from typing import List, Deque, Tuple
from collections import deque
class IdiosyncraticMomentumStocks(QCAlgorithm):
def Initialize(self) -> None:
    self.SetStartDate(2000, 1, 1)
    self.SetCash(100000) 
    # Daily price data.
    self.data:Dict[Symbol, RollingWindow] = {}
    self.period:int = 21
    self.quantile:int = 5
    self.leverage:int = 5
    self.exchange_codes:List[str] = ['NYS', 'NAS', 'ASE']
    self.symbol:Symbol = self.AddEquity('SPY', Resolution.Daily).Symbol
    self.data[self.symbol] = RollingWindow[float](self.period)
    self.regression_period:int = 36
    self.regression_data:Dict[Symbol, Tuple] = {}
    
    # Monthly residuals for stocks.
    self.residuals_period:int = 12
    self.residual:Dict[Symbol, RollingWindow] = {}
    
    self.long:List[Symbol] = []
    self.short:List[Symbol] = []
    
    self.fundamental_count:int = 1000
    self.fundamental_sorting_key = lambda x: x.DollarVolume
    self.selection_flag:bool = False
    self.UniverseSettings.Resolution = Resolution.Daily
    self.AddUniverse(self.FundamentalSelectionFunction)
    self.settings.daily_precise_end_time = False
    self.settings.minimum_order_margin_portfolio_percentage = 0.
    self.Schedule.On(self.DateRules.MonthEnd(self.symbol), self.TimeRules.AfterMarketOpen(self.symbol), self.Selection)            
def OnSecuritiesChanged(self, changes: SecurityChanges) -> None:
    for security in changes.RemovedSecurities:
        symbol:Symbol = security.Symbol
        
        if symbol in self.regression_data:
            del self.regression_data[symbol]
            
        if symbol in self.residual:
            del self.residual[symbol]
            
    for security in changes.AddedSecurities:
        symbol:Symbol = security.Symbol
        security.SetFeeModel(CustomFeeModel())
        security.SetLeverage(self.leverage)
        
def FundamentalSelectionFunction(self, fundamental: List[Fundamental]) -> List[Symbol]:
    # Update the rolling window every day.
    for stock in fundamental:
        symbol:Symbol = stock.Symbol
        # Store daily price.
        if symbol in self.data:
            self.data[symbol].Add(stock.AdjustedPrice)
    if not self.selection_flag:
        return Universe.Unchanged
    # selected = [x.Symbol for x in fundamental if x.HasFundamentalData and x.Market == 'usa']
    selected:List[Fundamental] = [x for x in fundamental if x.HasFundamentalData and x.Market == 'usa' and x.SecurityReference.ExchangeId in self.exchange_codes]
    if len(selected) > self.fundamental_count:
        selected = [x for x in sorted(selected, key=self.fundamental_sorting_key, reverse=True)[:self.fundamental_count]]
    idiosyncratic_momentum:Dict[Symbol, float] = {}
    
    # Warmup price rolling windows.
    for stock in selected:
        symbol:Symbol = stock.Symbol
        if symbol not in self.data:
            self.data[symbol] = RollingWindow[float](self.period)
            history:DataFrame = self.History(symbol, self.period, Resolution.Daily)
            if history.empty:
                self.Log(f"Not enough data for {symbol} yet.")
                continue
            closes:Series = history.loc[symbol].close
            for time, close in closes.items():
                self.data[symbol].Add(close)
    
        # Market data is not ready.
        if not self.data[self.symbol].IsReady: 
            continue
        market_excess_return:float = self.data[self.symbol][0] / self.data[self.symbol][self.period-1] - 1
    
        if not self.data[symbol].IsReady:
            continue
        stock_excess_return:float = self.data[symbol][0] / self.data[symbol][self.period-1] - 1
        
        # store regression data
        if symbol not in self.regression_data:
            self.regression_data[symbol] = deque(maxlen = self.regression_period)
        self.regression_data[symbol].append((market_excess_return, stock_excess_return))
        # Regression.
        if len(self.regression_data[symbol]) == self.regression_data[symbol].maxlen:
            # Y = α + (β ∗ X)
            # intercept = alpha
            # slope = beta
            market_excess_returns:List[float] = [x[0] for x in self.regression_data[symbol]]
            stock_excess_returns:List[float] = [x[1] for x in self.regression_data[symbol]]
            
            slope, intercept, r_value, p_value, std_err = stats.linregress(market_excess_returns, stock_excess_returns)
            
            # Calculate every residual for recent months.
            # residuals = []
            # for idx, x in enumerate(market_excess_returns):
            #     yfit = intercept + (slope * x)
            #     residuals.append(yfit - stock_excess_returns[idx])
            # idiosyncratic_momentum[symbol] = sum(residuals[:-2])
            
            # Calculate only latest residual.
            actual_value:float = stock_excess_returns[-1]
            estimate_value:float = intercept + (slope * market_excess_returns[-1])
            residual:float = actual_value - estimate_value
            
            # store residual data
            if symbol not in self.residual:
                self.residual[symbol] = RollingWindow[float](self.residuals_period)
            
            if self.residual[symbol].IsReady:
                # idiosyncratic_momentum[symbol] = self.residual[symbol][1] / self.residual[symbol][self.residuals_period-1] - 1
                idiosyncratic_momentum[symbol] = sum([x for x in self.residual[symbol]][1:])
            
            self.residual[symbol].Add(residual)

    if len(idiosyncratic_momentum) >= self.quantile:
        sorted_by_idiosyncratic_momentum:List[Tuple[Symbol, float]] = sorted(idiosyncratic_momentum.items(), key = lambda x: x[1], reverse = True)
        quintile:int = int(len(sorted_by_idiosyncratic_momentum) / 5)
        self.long:List[Symbol] = [x[0] for x in sorted_by_idiosyncratic_momentum[:quintile]]
        self.short:List[Symbol] = [x[0] for x in sorted_by_idiosyncratic_momentum[-quintile:]]
    
    return self.long + self.short
    
def OnData(self, data: Slice) -> None:
    if not self.selection_flag:
        return
    self.selection_flag = False        
    # Trade execution.
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
# Custom fee model
class CustomFeeModel(FeeModel):
def GetOrderFee(self, parameters):
    fee = parameters.Security.Price * parameters.Order.AbsoluteQuantity * 0.00005
    return OrderFee(CashAmount(fee, "USD"))
