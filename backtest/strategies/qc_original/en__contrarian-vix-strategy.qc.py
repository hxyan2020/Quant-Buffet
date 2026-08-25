# Original QuantConnect / library Python
# locale=en slug="contrarian-vix-strategy"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

from AlgorithmImports import *
# endregion

class ContrarianVIXstrategy(QCAlgorithm):

def Initialize(self):
    self.SetStartDate(2000, 1, 1)
    self.SetCash(100000)

    self.market:Symbol = self.AddEquity("SPY", Resolution.Daily).Symbol
    
    # Subscribe to VIX index data
    self.vix:Symbol = self.AddData(CBOE, "VIX").Symbol
 
    self.period:int = 120 * 21
    self.min_period:int = 12 * 21
    self.std_multiplier:int = 2
    self.buy_date:DateTime = None

    history:DataFrame = self.History(CBOE, self.vix, self.period, Resolution.Daily)['close']
    self.close_list:List[float] = history.values.tolist()

    self.SetPortfolioConstruction(EqualWeightingPortfolioConstructionModel())
    self.SetExecution(ImmediateExecutionModel())

def OnData(self, data:Slice) -> None:
    if self.vix in data and data[self.vix]:
        # store vix value
        self.close_list.append(data[self.vix].Close)

        if len(self.close_list) >= self.min_period:
            vix_mean:float = np.mean(self.close_list[:-1])
            vix_std:float = np.std(self.close_list[:-1])
            vix_yesterday:float = self.close_list[-2]
            
            if not self.Portfolio.Invested and vix_yesterday >= vix_mean + self.std_multiplier * vix_std:
                self.EmitInsights(Insight.Price(self.market, timedelta(days=22), InsightDirection.Up))
