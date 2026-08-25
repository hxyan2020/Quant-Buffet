# Original QuantConnect / library Python
# locale=en slug="产生更高收益且风险较低的股票交易规则"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

from AlgorithmImports import *
import math
# endregion

class StockTradingRuleThatProducesHigherReturnsWithLowerRisk(QCAlgorithm):

def Initialize(self):
    self.SetStartDate(2000, 1, 1)
    self.SetCash(100000)

    self.curr_month:int = -1
    self.long_period:int = 9 * 21
    self.short_period:int = 2 * 21

    # market data
    security:Equity = self.AddEquity("SPY", Resolution.Minute)
    security.SetFeeModel(CustomFeeModel())
    security.SetLeverage(5)
    self.spy_symbol:Symbol = security.Symbol

    # bills data
    security:Equity = self.AddEquity("BIL", Resolution.Minute)
    security.SetFeeModel(CustomFeeModel())
    security.SetLeverage(5)
    self.bil_symbol:Symbol = security.Symbol

    # sma data objects
    self.long_SMA_data:SMAData = SMAData(self, self.spy_symbol, self.long_period)
    self.short_SMA_data:SMAData = SMAData(self, self.spy_symbol, self.short_period)

    self.SetWarmup(self.long_period, Resolution.Daily)
    
    # placing MOC orders is allowed 15,5 minutes before market close
    self.Schedule.On(self.DateRules.EveryDay(self.spy_symbol), self.TimeRules.BeforeMarketClose(self.spy_symbol, 16), self.EveryDayBeforeMarketClose)

def EveryDayBeforeMarketClose(self):
    # update sma each day
    if self.long_SMA_data.sma_is_ready() and self.short_SMA_data.sma_is_ready():
        # store sma values to internal list
        self.long_SMA_data.update_values()
        self.short_SMA_data.update_values()

    # wait until warmup is done and rebalance monthly
    if self.IsWarmingUp or (self.curr_month == self.Time.month):
        return
    self.curr_month = self.Time.month

    # storage of SMA values is ready
    if self.long_SMA_data.is_ready() and self.short_SMA_data.is_ready():
        long_SMA_slope:float = self.long_SMA_data.calc_slope()
        short_SMA_slope:float = self.short_SMA_data.calc_slope()

        long_SMA_value:float = self.long_SMA_data.SMA.Current.Value
        short_SMA_value:float = self.short_SMA_data.SMA.Current.Value

        # tangent
        tan_353:float = math.tan(math.pi * (353 / 180))
        tan_355:float = math.tan(math.pi * (355 / 180))
        tan_5:float = math.tan(math.pi * (5 / 180))

        # if the derivative is negative, the slope of the nine-month SMA is lower or equal to the tangent of 355°, the slope of the two-month SMA is lower or equal to the tangent of 353°
        if long_SMA_slope  0 and (long_SMA_slope >= tan_5):
            # buy signal close BIL and buy S&P
            if self.Portfolio[self.bil_symbol].Invested:
                self.MarketOnCloseOrder(self.bil_symbol, -self.Portfolio[self.bil_symbol].Quantity)

            # self.SetHoldings(self.spy_symbol, 1)
            if self.Securities.ContainsKey(self.spy_symbol) and self.Securities[self.spy_symbol].Price != 0:
                q:int = int(self.Portfolio.MarginRemaining / self.Securities[self.spy_symbol].Price)
                # q = self.CalculateOrderQuantity(self.spy_symbol, 1)
                self.MarketOnCloseOrder(self.spy_symbol, q - self.Portfolio[self.spy_symbol].Quantity)

class SMAData:
def __init__(self, algorithm:QCAlgorithm, symbol:Symbol, period:float) -> None:
    self.SMA_period:float = period
    self.SMA:SimpleMovingAverage = algorithm.SMA(symbol, period, Resolution.Daily)
    self.SMA_values:RollingWindow = RollingWindow[float](period)

def update_values(self) -> None:
    self.SMA_values.Add(self.SMA.Current.Value)

def sma_is_ready(self) -> bool:
    return self.SMA.IsReady

def is_ready(self) -> bool:
    return self.SMA_values.IsReady

def calc_slope(self) -> float:
    delta_SMA:float = self.SMA_values[0] - self.SMA_values[self.SMA_period-1]

    # return slope
    return delta_SMA / self.SMA_period

# Custom fee model
class CustomFeeModel(FeeModel):
def GetOrderFee(self, parameters):
    fee = parameters.Security.Price * parameters.Order.AbsoluteQuantity * 0.00005
    return OrderFee(CashAmount(fee, "USD"))
