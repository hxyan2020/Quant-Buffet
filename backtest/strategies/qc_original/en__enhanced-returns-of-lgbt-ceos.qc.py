# Original QuantConnect / library Python
# locale=en slug="enhanced-returns-of-lgbt-ceos"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

from AlgorithmImports import *
import data_tools
# endregion

class EnhancedReturnsOfLGBTCEOs(QCAlgorithm):

def Initialize(self):
    self.SetStartDate(2000, 1, 1)
    self.SetCash(100000)

    self.equally_weighted_flag:bool = False     # False - VW; True - EW

    self.leverage:int = 5

    self.universe:list[str] = []
    self.selected_symbols:list[Symbol] = []     # currently actively traded stocks
    self.market_cap:dict[Symbol, float] = {}

    self.market_symbol:Symbol = self.AddEquity('SPY', Resolution.Daily).Symbol

    self.LGBT_CEO_symbol:Symbol = self.AddData(data_tools.QuantpediaLGBT, 'LGBT_CEO', Resolution.Daily).Symbol

    self.selection_flag:bool = False
    self.UniverseSettings.Resolution = Resolution.Daily
    self.AddUniverse(self.CoarseSelectionFunction, self.FineSelectionFunction)       

def OnSecuritiesChanged(self, changes):
    for security in changes.AddedSecurities:
        security.SetFeeModel(data_tools.CustomFeeModel())
        security.SetLeverage(self.leverage)

def CoarseSelectionFunction(self, coarse):
    if not self.selection_flag:
        return Universe.Unchanged
    
    selected_symbols:list[Symbol] = [equity.Symbol for equity in coarse if equity.Symbol.Value in self.universe]

    return selected_symbols

def FineSelectionFunction(self, fine):
    if self.equally_weighted_flag:
        self.selected_symbols = list(map(lambda stock: stock.Symbol, fine))

        return self.selected_symbols
    else:
        self.market_cap.clear()

        for stock in fine:
            market_cap:float = stock.MarketCap

            if market_cap == 0:
                continue

            symbol:Symbol = stock.Symbol
            self.market_cap[symbol] = market_cap
    
        return list(self.market_cap.keys())

def OnData(self, data: Slice):
    if self.selection_flag:
        # rebalance whole active selection
        if self.equally_weighted_flag:
            length:int = len(self.selected_symbols)

            for symbol in self.selected_symbols:
                self.SetHoldings(symbol, 1 / length)
        else:
            total_cap:float = sum([x[1] for x in self.market_cap.items()])

            for symbol, market_cap in self.market_cap.items():
                self.SetHoldings(symbol, market_cap / total_cap)

        self.selection_flag = False

    if self.LGBT_CEO_symbol in data and data[self.LGBT_CEO_symbol]:
        stocks:list = data[self.LGBT_CEO_symbol].GetProperty('stocks')

        for stock in stocks:
            ticker:str = stock['ticker']
            status:str = stock['status']

            if status == 'start':
                self.universe.append(ticker)
            elif status == 'end' and ticker in self.universe:
                self.universe.remove(ticker)
                self.Liquidate(ticker)

        # rebalance once the new data comes in
        self.selection_flag = True
