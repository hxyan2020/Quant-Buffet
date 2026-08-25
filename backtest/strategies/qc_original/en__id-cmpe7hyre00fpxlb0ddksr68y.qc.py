# Original QuantConnect / library Python
# locale=en slug="股票中的专利强度因子策略"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

from AlgorithmImports import *
from data_tools import CustomFeeModel
# endregion

class PatentIntensityFactorInEquities(QCAlgorithm):

def Initialize(self):
    self.SetStartDate(2000, 1, 1)
    self.SetCash(100000)
    
    self.leverage:int = 5
    self.quantile:int = 4
    self.rebalance_month:int = 6
    
    self.weights:Dict[Symbol, float] = {}

    self.patents_granted:Dict[str, int] = {}
    self.patents:Dict[str, Dict[str, Dict[str, int]]] = {}

    self.market_symbol:Symbol = self.AddEquity('SPY', Resolution.Daily).Symbol

    patents_csv:str = self.Download('data.quantpedia.com/backtesting_data/economic/patents.csv')
    lines:List[str] = patents_csv.split('\r\n')
    header:str = lines.pop(0)
    self.tickers:List[str] = header.split(';')[1:]

    for line in lines:
        if line == '':
            continue

        split:List[str] = line.split(';')
        date:str = split.pop(0)
        date_split:List[str] = date.split('.')
        month:int = int(date_split[1])
        year:int = int(date_split[-1])

        if year not in self.patents:
            self.patents[year] = {}

        if month not in self.patents[year]:
            self.patents[year][month] = {}

        for i, total_patents in enumerate(split):
            if total_patents == '0.0':
                continue

            ticker:str = self.tickers[i]
            total_patents = int(float(total_patents))

            if ticker not in self.patents[year][month]:
                self.patents[year][month][ticker] = 0

            self.patents[year][month][ticker] += total_patents

    self.selection_flag:bool = False
    self.UniverseSettings.Resolution = Resolution.Daily
    self.AddUniverse(self.CoarseSelectionFunction, self.FineSelectionFunction)
    
    self.Schedule.On(self.DateRules.MonthEnd(self.market_symbol), self.TimeRules.BeforeMarketClose(self.market_symbol, 0), self.Selection)

def OnSecuritiesChanged(self, changes:SecurityChanges) -> None:
    for security in changes.AddedSecurities:
        security.SetFeeModel(CustomFeeModel())
        security.SetLeverage(self.leverage)

def CoarseSelectionFunction(self, coarse:List[CoarseFundamental]) -> List[Symbol]:
    if not self.selection_flag:
        return Universe.Unchanged

    selected_symbols:List[Symbol] = [x.Symbol for x in coarse if x.Symbol.Value in self.patents_granted]

    return selected_symbols 

def FineSelectionFunction(self, fine:List[FineFundamental]) -> List[Symbol]:
    PI_values:Dict[Symbol, int] = {}
    for stock in fine:
        market_cap:float = stock.MarketCap

        if market_cap == 0:
            continue

        symbol:Symbol = stock.Symbol
        total_patents:int = self.patents_granted[symbol.Value]
        PI_values[symbol] = total_patents / market_cap

    self.patents_granted.clear()

    if len(PI_values)
