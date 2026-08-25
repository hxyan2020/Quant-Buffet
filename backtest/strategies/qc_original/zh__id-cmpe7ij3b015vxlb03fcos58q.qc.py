# Original QuantConnect / library Python
# locale=zh slug="美国股市的价格缺口策略"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

import numpy as np
from AlgorithmImports import *
class PriceGapStrategy(QCAlgorithm):
def initialize(self) -> None:
    self.set_start_date(2000, 1, 1)
    self.set_cash(100000)
    self.symbol: Symbol = self.add_equity('SPY', Resolution.MINUTE).symbol
    
    self.close_price: float = 0    # recent close price
    self.gaps: List[float] = []          # daily gaps
    self.min_gap_count: int = 100
    
    self.schedule.on(self.date_rules.every_day(self.symbol), self.time_rules.before_market_close(self.symbol, 1), self.close)
    self.schedule.on(self.date_rules.every_day(self.symbol), self.time_rules.after_market_open(self.symbol, 1), self.open)
    
def open(self) -> None:
    if self.securities.contains_key(self.symbol):
        if self.close_price != 0:
            # Store recent gap.
            open: float = self.securities[self.symbol].open
            self.gaps.append((open / self.close_price) - 1)
            self.close_price = 0
            
            if len(self.gaps)  gaps_mean + 2 * gaps_std:
                self.set_holdings(self.symbol, 1)

def close(self) -> None:
    self.liquidate(self.symbol)
    
    if self.securities.contains_key(self.symbol):
        close: float = self.securities[self.symbol].close
        if close != 0:
            self.close_price = close
