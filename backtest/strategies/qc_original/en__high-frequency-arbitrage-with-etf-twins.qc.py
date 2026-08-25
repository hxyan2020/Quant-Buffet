# Original QuantConnect / library Python
# locale=en slug="high-frequency-arbitrage-with-etf-twins"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

from AlgorithmImports import *
from typing import List, Union
# endregion
class HighFrequencyArbitragewithETFTwins(QCAlgorithm):
def Initialize(self):
    self.SetStartDate(2000, 1, 1)
    self.SetCash(100000)
    self.spread_threshold:float = 1.002
    self.spy_voo_ratio:Union[None, float] = None
    self.voo_spy_ratio:Union[None, float] = None
    self.symbols:List[Symbol] = [self.AddEquity(x, Resolution.Minute).Symbol for x in ['SPY', 'VOO']]
    self.trade_direction_flag:Union[None, bool] = None
def OnData(self, data: Slice) -> None:
    if self.symbols[0] in data and data[self.symbols[0]] and self.symbols[1] in data and data[self.symbols[1]]:
        # get ratio of etfs
        if self.Time.hour == 9 and self.Time.minute == 35:
            self.spy_voo_ratio = self.Securities[self.symbols[0]].BidPrice / self.Securities[self.symbols[1]].AskPrice
            self.voo_spy_ratio = self.Securities[self.symbols[1]].BidPrice / self.Securities[self.symbols[0]].AskPrice
        if self.spy_voo_ratio is not None and self.voo_spy_ratio is not None and not self.Portfolio.Invested:
            # decide on trading direction
            self.trade_direction_flag = True \
                if (self.Securities[self.symbols[0]].BidPrice / self.Securities[self.symbols[1]].AskPrice) >= self.spy_voo_ratio * self.spread_threshold \
                else False \
                if (self.Securities[self.symbols[1]].BidPrice / self.Securities[self.symbols[0]].AskPrice) >= self.voo_spy_ratio * self.spread_threshold \
                else None
        
            # trade execution
            if self.trade_direction_flag is not None:
                self.SetHoldings(self.symbols[0], (-1 if self.trade_direction_flag else 1) * 1)
                self.SetHoldings(self.symbols[1], (-1 if self.trade_direction_flag else 1) * -1)
        # closing trade
        if self.Portfolio.Invested:
            if self.trade_direction_flag:
                if (self.Securities[self.symbols[0]].BidPrice / self.Securities[self.symbols[1]].AskPrice)
