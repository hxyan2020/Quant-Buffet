# Original QuantConnect / library Python
# locale=en slug="vwap日内交易策略"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

from AlgorithmImports import *
import numpy as np
# endregion

class VolumeWeightedAveragePriceVWAPAsPreciseTrendFollowingIndicatorForDayTraders(QCAlgorithm):

def Initialize(self) -> None:
    self.SetStartDate(2018, 1, 1)
    self.SetCash(100000)

    self.symbol: Symbol = self.AddEquity("QQQ", Resolution.Minute).Symbol
    self.Securities[self.symbol].SetFeeModel(ConstantFeeModel(0))
    # self.SetBrokerageModel(BrokerageName.InteractiveBrokersBrokerage, AccountType.Margin)

    self.VWAP: IntradayVwap = IntradayVwap(self.symbol)

    self.traded_weight: float = 1.
    self.trade_flag: bool = False
    self.Settings.MinimumOrderMarginPortfolioPercentage = 0.
    self.Schedule.On(self.DateRules.EveryDay(self.symbol), self.TimeRules.AfterMarketOpen(self.symbol), self.OnMarketOpen)
    self.Schedule.On(self.DateRules.EveryDay(self.symbol), self.TimeRules.BeforeMarketClose(self.symbol, 1), self.BeforeMarketClose)

def OnData(self, data: Slice) -> None:
    # trading allowed only after open market
    if not self.trade_flag:
        return

    # update VWAP indicator
    bar: TradeBar = data.Bars.get(self.symbol)
    self.VWAP.Update(bar)
            
    # trade execution
    if self.VWAP.IsReady:
        if data[self.symbol].Close > self.VWAP.Current.Value:
            if not self.Portfolio[self.symbol].IsLong:
                self.SetHoldings(self.symbol, self.traded_weight)
        else:
            if not self.Portfolio[self.symbol].IsShort:
                self.SetHoldings(self.symbol, -self.traded_weight)

def OnMarketOpen(self) -> None:
    self.trade_flag = True

def BeforeMarketClose(self) -> None:
    self.Liquidate()
    self.VWAP.Reset()
    self.trade_flag = False
