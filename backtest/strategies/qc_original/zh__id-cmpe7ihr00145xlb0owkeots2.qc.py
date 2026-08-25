# Original QuantConnect / library Python
# locale=zh slug="多资产市场广度动量"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

from AlgorithmImports import *
from collections import deque
class MultiAssetMarketBreadthMomentum(QCAlgorithm):
def Initialize(self):
    self.SetStartDate(2008, 1, 1)
    self.SetCash(100_000)
    
    self.symbols: List[str] = [
        'SPY', 'QQQ', 'IWM', 'VGK', 'EWJ', 'EEM', 'GSG', 'GLD', 'IYR', 'HYG', 'LQD', 'TLT'
    ]
    self.safe_bond: str = 'IEF'
    
    period: int = 12 * 21
    self.data: Dict[str, deque] = {}
    self.sma: Dict[str, SimpleMovingAverage]  = {}
    
    for symbol in self.symbols:
        self.AddEquity(symbol, Resolution.Daily)
        self.data[symbol] = deque(maxlen = period)
        self.sma[symbol] = self.SMA(symbol, period, Resolution.Daily)
            
        history: DataFrame = self.History(self.Symbol(symbol), period, Resolution.Daily)
        if not history.empty:
            closes: Series = history.loc[symbol].close
            for time, close in closes.items():
                self.sma[symbol].Update(time, close)
    
    self.AddEquity(self.safe_bond, Resolution.Daily)
    self.last_month: int = -1

def OnData(self, slice: Slice) -> None:
    if self.last_month == self.Time.month:
        return
    self.last_month = self.Time.month
    
    mom: Dict[str, float] = {}
    for symbol in self.symbols:
        symbol_obj: Symbol = self.Symbol(symbol)
        # SMA data is ready.
        if self.sma[symbol].IsReady:
            if symbol_obj in slice.Bars:
                price: float = slice.Bars[symbol_obj].Value
                if price != 0:
                    mom[symbol] = price / self.sma[symbol].Current.Value - 1
        else:
            return  # Wait for every asset.
            
    if len(mom) != 0:
        # Bond fraction calc.
        good_assets: List = sorted([x[0] for x in mom.items() if x[1] > 0], key = lambda x: x[1], reverse = True)[:6]
        N: int = len(self.symbols)
        n: int = len(good_assets)
        a: int = 2
        n1: float = a*N/4
        BF: float = (N-n)/(N-n1)
        
        bond_share: float = (1-BF)/BF
        # Trade execution.
        self.Liquidate()
        
        # Risky part.
        # "leverage" ratio in case there's two parts of portfolio - risky as well as safe part.
        ratio: float = 0.5 if bond_share != 0 else 1
        
        for symbol in good_assets:
            self.SetHoldings(symbol, ratio * (1/n))
        
        # Bond part.
        self.SetHoldings(self.safe_bond, ratio * bond_share)
