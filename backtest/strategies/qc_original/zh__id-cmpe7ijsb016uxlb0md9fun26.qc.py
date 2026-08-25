# Original QuantConnect / library Python
# locale=zh slug="基于日内收益的月度反转和-或动量策略"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

from AlgorithmImports import *
from typing import List, Dict
class MonthlyReversalMomentumBasedIntradayReturns(QCAlgorithm):
def Initialize(self):
    self.SetStartDate(2010, 1, 1)
    self.SetCash(100000)
    self.min_share_price:int = 5
    self.leverage:int = 5
    self.quantile:int = 10
    self.days_to_lookup:int = 21
    self.period:int = self.days_to_lookup * 7
    
    market:Symbol = self.AddEquity('SPY', Resolution.Daily).Symbol
    
    self.fundamental_sorting_key = lambda x: x.DollarVolume
    self.fundamental_count:int = 300
    self.exchange_codes:List[str] = ['NYS', 'NAS', 'ASE']
    
    self.last_course:List[Symbol] = []
    
    # Relevant hourly closes (at 14 and 16)
    self.daily_return:Dict[Symbol, float] = {}
    self.price_14:Dict[Symbol, float] = {}
    
    self.settings.daily_precise_end_time = False
    self.Settings.MinimumOrderMarginPortfolioPercentage = 0.
    self.UniverseSettings.Resolution = Resolution.Hour
    self.AddUniverse(self.FundamentalSelectionFunction)
    self.selection_flag:bool = False
    
    self.Schedule.On(self.DateRules.MonthEnd(market), self.TimeRules.AfterMarketOpen(market), self.Selection)

def OnSecuritiesChanged(self, changes: SecurityChanges) -> None:
    for security in changes.AddedSecurities:
        security.SetFeeModel(CustomFeeModel())
        security.SetLeverage(self.leverage)
        
def FundamentalSelectionFunction(self, fundamental: List[Fundamental]) -> List[Symbol]:
    if not self.selection_flag:
        return Universe.Unchanged
    
    self.selection_flag = False
    selected:List[Fundamental] = [
        x for x in fundamental if x.HasFundamentalData and x.Price > self.min_share_price and \
        x.Market == 'usa' and x.SecurityReference.ExchangeId in self.exchange_codes\
    ]
        
    if len(selected) > self.fundamental_count:
        selected = [x for x in sorted(selected, key=self.fundamental_sorting_key, reverse=True)[:self.fundamental_count]]
    self.last_course = [x.Symbol for x in selected[:self.fundamental_count]]
    
    return self.last_course
    
def OnData(self, data: Slice):
    # Store 14h price to calculate daily return.
    if self.Time.hour == 14:
        for symbol in self.last_course:
            if symbol in data and data[symbol]:
                price_14:float = data[symbol].Value
                if price_14 != 0:
                    # 14h price value.
                    self.price_14[symbol] = price_14
    
    # Calculate daily return.
    if self.Time.hour == 16:
        
        accumulated_returns:Dict[Symbol, float] = {}
        for symbol in self.last_course:
            if symbol in self.price_14 and symbol in data and data[symbol]:
                price_16:float = data[symbol].Value
                if price_16 != 0:
                    # Calculate intraday return.
                    price_14 = self.price_14[symbol] # 14h price
                    ret:float = price_16 / price_14 - 1
                        
                    if symbol not in self.daily_return:
                        self.daily_return[symbol] = RollingWindow[float](21) # One month of daily returns
                    self.daily_return[symbol].Add(ret)
                        
                    # Month worth of daily return is ready.
                    if self.daily_return[symbol].IsReady:
                        acc_ret:float = sum([x for x in self.daily_return[symbol]])
                        accumulated_returns[symbol] = acc_ret
        if len(accumulated_returns) == 0:
            return
        # Sort by daily accumulated returns.
        sorted_by_return:List[Tuple[Symbol, float]] = sorted(accumulated_returns.items(), key = lambda x: x[1], reverse = True)
        quantile:int = int(len(sorted_by_return) / self.quantile)
        long:List[Symbol] = [x[0] for x in sorted_by_return[-quantile:]]
        short:List[Symbol] = [x[0] for x in sorted_by_return[:quantile]]
        # Trade execution
        targets:List[PortfolioTarget] = []
        for i, portfolio in enumerate([long, short]):
            for symbol in portfolio:
                if symbol in data and data[symbol]:
                    targets.append(PortfolioTarget(symbol, ((-1) ** i) / len(portfolio)))
        
        self.SetHoldings(targets, True)
        self.daily_return.clear()
        
def Selection(self):
    self.selection_flag = True
    
# Custom fee model
class CustomFeeModel(FeeModel):
def GetOrderFee(self, parameters):
    fee = parameters.Security.Price * parameters.Order.AbsoluteQuantity * 0.00005
    return OrderFee(CashAmount(fee, "USD"))
