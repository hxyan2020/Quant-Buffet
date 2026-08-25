# Original QuantConnect / library Python
# locale=en slug="期货市场的隔夜-日内反转策略"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

from AlgorithmImports import *
# endregion

class OvernightIntradayReversalinFutures(QCAlgorithm):

def Initialize(self):
    self.SetStartDate(2015, 1, 1)
    self.SetCash(100000)

    self.traded_percentage:float = 0.1
    self.futures:List[Symbol] = []
    self.last_close:Dict[Symbol, float] = {}
    self.traded_count:int = 2

    symbols:List[str] = [
        Futures.Indices.SP400MidCapEmini,
        Futures.Indices.SP500EMini,
        Futures.Indices.MicroDow30EMini,
        Futures.Indices.NASDAQ100EMini,
        Futures.Indices.Nikkei225Dollar,
    ]

    for symbol in symbols:
        future:Future = self.AddFuture(symbol, Resolution.Minute, dataNormalizationMode=DataNormalizationMode.BackwardsRatio, contractDepthOffset=0)
        self.futures.append(future.Symbol)

    self.day_close_flag:bool = False
    self.day_open_flag:bool = False

    self.Schedule.On(self.DateRules.EveryDay(self.futures[1]), self.TimeRules.BeforeMarketClose(self.futures[1], 1), self.DayClose)
    self.Schedule.On(self.DateRules.EveryDay(self.futures[1]), self.TimeRules.AfterMarketOpen(self.futures[1], 1), self.DayOpen)

def OnData(self, data: Slice) -> None:
    if self.day_open_flag:
        self.day_open_flag = False

        returns:Dict[Symbol, float] = {symbol: data[symbol].Open / self.last_close[symbol] - 1 for symbol in self.futures if symbol in self.last_close and symbol in data and data[symbol]}
        self.last_close.clear()

        traded_count:int = self.traded_count if len(returns) >= len(self.futures) else 1
        sorted_returns:List[Symbol] = sorted(returns, key=returns.get)
        long:List[Symbol] = sorted_returns[:traded_count]
        short:List[Symbol] = sorted_returns[-traded_count:]
        
        for i, portfolio in enumerate([long, short]):
            for symbol in portfolio:
                self.SetHoldings(self.Securities[symbol].Mapped, ((-1) ** i) / len(portfolio) * self.traded_percentage)

    if self.day_close_flag:
        self.day_close_flag = False

        self.Liquidate()
        self.last_close = { symbol: data[symbol].Close for symbol in self.futures if symbol in data and data[symbol] }

def DayClose(self) -> None:
    self.day_close_flag = True

def DayOpen(self) -> None:
    self.day_open_flag = True
