# Original QuantConnect / library Python
# locale=zh slug="隔夜-日内大宗商品日内反转"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

from AlgorithmImports import *
#endregion
class OvernightIntradayDailyReversalinCommodities(QCAlgorithm):
def Initialize(self):
    self.SetStartDate(2015, 1, 1)
    self.SetCash(1000000)
    symbols:List[str] = [
        Futures.Grains.Corn,
        Futures.Meats.LeanHogs,
        Futures.Meats.LiveCattle,
        Futures.Forestry.Lumber,
        Futures.Grains.Oats,
        Futures.Grains.SoybeanMeal,
        Futures.Grains.Soybeans,
        Futures.Grains.Wheat,
    ]
    self.traded_percentage:float = 0.2
    self.futures:List[Symbol] = []
    self.recent_close:Dict[Symbol, float] = {}
    
    for symbol in symbols:
        future = self.AddFuture(symbol, Resolution.Minute, dataNormalizationMode=DataNormalizationMode.BackwardsRatio, contractDepthOffset=0)
        self.futures.append(future.Symbol)
    self.day_close_flag:bool = False
    self.day_open_flag:bool = False
    self.Schedule.On(self.DateRules.EveryDay(self.futures[3]), self.TimeRules.BeforeMarketClose(self.futures[3], 1), self.DayClose)
    self.Schedule.On(self.DateRules.EveryDay(self.futures[3]), self.TimeRules.AfterMarketOpen(self.futures[3], 1), self.DayOpen)
def OnData(self, data: Slice) -> None:
    if self.day_open_flag:
        self.day_open_flag = False
        returns:Dict[Symbol, float] = { symbol : data[symbol].Open / self.recent_close[symbol] - 1 for symbol in self.futures if symbol in self.recent_close and symbol in data and data[symbol] }
        self.recent_close.clear()
        long:List[Symbol] = [x[0] for x in returns.items() if x[1]  0]
        
        for i, portfolio in enumerate([long, short]):
            for symbol in portfolio:
                # notional value = asset price * contract multiplier
                notional_value:float = (self.Securities[symbol].Price * self.Securities[symbol].SymbolProperties.ContractMultiplier)
                quantity:int = int((((-1) ** i) * self.Portfolio.TotalPortfolioValue) / len(portfolio) * self.traded_percentage) // notional_value
                self.MarketOrder(self.Securities[symbol].Mapped, quantity)
    if self.day_close_flag:
        self.day_close_flag = False
        self.Liquidate()
        self.recent_close = { symbol : data[symbol].Close for symbol in self.futures if symbol in data and data[symbol] }
def DayClose(self) -> None:
    self.day_close_flag = True

def DayOpen(self) -> None:
    self.day_open_flag = True
