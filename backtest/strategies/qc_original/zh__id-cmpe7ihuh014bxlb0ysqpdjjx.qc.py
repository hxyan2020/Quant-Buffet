# Original QuantConnect / library Python
# locale=zh slug="总部位置动量"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

from AlgorithmImports import *
import numpy as np
from collections import deque
from data_tools import CustomFeeModel, Return
from numpy import isnan
#endregion
class HeadquarterLocationMomentum(QCAlgorithm):
def Initialize(self) -> None:
    self.SetStartDate(2000, 1, 1)
    self.SetCash(100_000)
    market: Symbol = self.AddEquity('SPY', Resolution.Daily).Symbol
    self.quantile: int = 5
    
    # Daily close data.
    self.data: Dict[Symbol, Deque[float]] = {}
    self.period: int = 21
    self.leverage: int = 10
    # SP 500 headquarters data.
    self.headquarters: Dict[str, str] = {}
    
    self.symbols: List[Symbol] = []
    
    # Import headquarters data.
    # Source: https://en.wikipedia.org/wiki/List_of_S%26P_500_companies
    csv_string_file: str = self.Download('data.quantpedia.com/backtesting_data/economic/sp_headquarters.csv')
    lines: List[str] = csv_string_file.split('\r\n')
    for line in lines[1:]:
        line_split: List[str] = line.split(';')
        location: str = line_split[1]
        ticker: str = line_split[0]
        
        if location not in self.headquarters:
            self.headquarters[location] = []
        self.headquarters[location].append(ticker)
        
        self.symbols.append(ticker)
        
    self.long: List[Symbol] = []
    self.short: List[Symbol] = []
    self.selection_flag: bool = False
    self.UniverseSettings.Leverage = self.leverage
    self.UniverseSettings.Resolution = Resolution.Daily
    self.AddUniverse(self.FundamentalSelectionFunction)
    self.settings.daily_precise_end_time = False
    self.Settings.MinimumOrderMarginPortfolioPercentage = 0.
    self.Schedule.On(self.DateRules.MonthStart(market), self.TimeRules.BeforeMarketClose(market), self.Selection)
def OnSecuritiesChanged(self, changes: SecurityChanges) -> None:
    for security in changes.AddedSecurities:
        security.SetFeeModel(CustomFeeModel())
        
def FundamentalSelectionFunction(self, fundamental: List[Fundamental]) -> List[Symbol]:
    # update price
    for stock in fundamental:
        symbol: Symbol = stock.Symbol
        # store daily price
        if symbol in self.data:
            self.data[symbol].append(stock.AdjustedPrice)
    if not self.selection_flag:
        return Universe.Unchanged
    
    selected: List[Fundamental] = [
        x for x in fundamental 
        if x.Symbol.Value in self.symbols
        and not isnan(x.AssetClassification.MorningstarSectorCode) and x.AssetClassification.MorningstarSectorCode != 0]
    # warmup price rolling windows
    for stock in selected:
        symbol: Symbol = stock.Symbol
        if symbol in self.data:
            continue
        
        self.data[symbol] = deque(maxlen = self.period)
        history: DataFrame = self.History(symbol, self.period, Resolution.Daily)
        if history.empty:
            self.Log(f"Not enough data for {symbol} yet.")
            continue
        closes: Series = history.loc[symbol].close
        for time, close in closes.items():
            self.data[symbol].append(close)
        
    # Average lagged return of firms headquartered in the same region.
    momentum: Dict[Symbol, float] = {}
    
    for area in self.headquarters:
        area_stocks: List[Fundamental] = [x for x in selected if x.Symbol.Value in area]
        
        for stock in area_stocks:
            symbol = stock.Symbol
            if not len(self.data[symbol]) == self.period:
                continue
            symbols_sector = stock.AssetClassification.MorningstarSectorCode
            
            area_performances: List[float] = [Return(self.data[x.Symbol]) for x in area_stocks if x.Symbol != symbol and 
                                        (x.AssetClassification.MorningstarSectorCode != symbols_sector) and
                                        (x.Symbol in self.data and len(self.data[x.Symbol]) == self.data[x.Symbol].maxlen) 
                                        ]
    
            if len(area_performances) != 0:
                momentum[symbol] = np.mean(area_performances)
        
    # Momentum sorting.
    if len(momentum) >= self.quantile:
        sorted_by_momentum: List[Tuple[Symbol, float]] = sorted(momentum.items(), key = lambda x: x[1], reverse = True)
        quantile: int = int(len(sorted_by_momentum) / self.quantile)
        self.long: List[Symbol] = [x[0] for x in sorted_by_momentum][:quantile]
        self.short: List[Symbol] = [x[0] for x in sorted_by_momentum][-quantile:]
    
    return self.long + self.short
def OnData(self, slice: Slice) -> None:
    if not self.selection_flag:
        return
    self.selection_flag = False
    
    # Trade execution.
    targets: List[PortfolioTarget] = []
    for i, portfolio in enumerate([self.long, self.short]):
        for symbol in portfolio:
            if slice.contains_key(symbol) and slice[symbol]:
                targets.append(PortfolioTarget(symbol, ((-1) ** i) / len(portfolio)))
    
    self.SetHoldings(targets, True)
    self.long.clear()
    self.short.clear()
def Selection(self):
    self.selection_flag = True
