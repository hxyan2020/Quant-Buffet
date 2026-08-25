# Original QuantConnect / library Python
# locale=en slug="加密货币中的月末效应"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

from AlgorithmImports import *
# endregion

class TurnOfTheMonthEffectInCryptocurencies(QCAlgorithm):

def Initialize(self):
    self.SetStartDate(2015, 1, 1)
    self.SetCash(100000)

    self.portfolio_percentage:float = 1.
    self.days_offset:int = 2

    self.SetBrokerageModel(BrokerageName.Bitfinex)
    self.SetTimeZone('UTC')

    self.btc:Symbol = self.AddCrypto('BTCUSD', Resolution.Minute, Market.Bitfinex).Symbol

    self.Schedule.On(self.DateRules.MonthEnd(self.days_offset), self.TimeRules.Midnight, self.Buy)
    self.Schedule.On(self.DateRules.MonthStart(self.days_offset), self.TimeRules.Midnight, self.Sell)

def Buy(self) -> None:
    self.SetHoldings(self.btc, 1 * self.portfolio_percentage)

def Sell(self) -> None:
    self.Liquidate()
