# Original QuantConnect / library Python
# locale=en slug="公司文件与股票回报的积极相似性-2"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

from AlgoLib import *
# endregion

class ThePositiveSimilarityOfCompanyFilingsAndStockReturns(XXX):

def Initialize(self):
    self.SetStartDate(2009, 1, 1) # first metric data come in 2009
    self.SetCash(100000)
            
    self.leverage:int = 5
    self.quantile:int = 10

    self.metric_symbols:dict[Symbol, Symbol] = {}
    self.positive_similarities:dict[Symbol, float] = {}

    self.market:Symbol = self.AddEquity('SPY', Resolution.Daily).Symbol

    self.coarse_count:int = 1000
    self.pick_largest:bool = True

    self.selection_flag:bool = False
    self.UniverseSettings.Resolution = Resolution.Daily
    self.AddUniverse(self.CoarseSelectionFunction, self.FineSelectionFunction)
    self.Schedule.On(self.DateRules.MonthStart(self.market), self.TimeRules.BeforeMarketClose(self.market, 0), self.Selection)

def OnSecuritiesChanged(self, changes):
    for security in changes.AddedSecurities:
        security.SetFeeModel(CustomFeeModel())
        security.SetLeverage(self.leverage)

def CoarseSelectionFunction(self, coarse):
    if not self.selection_flag:
        return Universe.Unchanged
    
    if self.coarse_count  self.coarse_count or self.pick_largest:
        sorted_by_cap:list = sorted(fine, key=lambda stock: stock.MarketCap)
        fine = sorted_by_cap[-self.coarse_count:]
    
    return list(map(lambda stock: stock.Symbol, fine)) 
    
def OnData(self, data):
    if self.selection_flag:
        self.selection_flag = False

        filtered_positive_similarity:dict[Symbol, float] = { symbol: pos_sim for symbol, pos_sim in self.positive_similarities.items() \
            if symbol in data and data[symbol] }

        self.positive_similarities.clear()

        if len(filtered_positive_similarity)
