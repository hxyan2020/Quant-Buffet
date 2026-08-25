# Original QuantConnect / library Python
# locale=en slug="esg-exclusion-premium-factor"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

from AlgorithmImports import *
from datetime import datetime
from data_tools import CustomFeeModel, QuantpediaESGExclusion, SymbolData
from scipy import stats
# endregion

class ESGExclusionPremiumFactor(QCAlgorithm):

def Initialize(self):
    self.SetStartDate(2005, 1, 1) # ESG exclusion starts in 2005
    self.SetCash(100000)

    self.leverage:int = 5

    self.period:int = 12 * 21

    self.max_missing_days:int = 15

    self.data:dict[Symbol, SymbolData] = {}
    self.weights:dict[Symbol, float] = {}
    self.excluded_stocks:list[str] = []

    self.esg_exclusion_symbol:Symbol = self.AddData(QuantpediaESGExclusion, 'esg_exclusion', Resolution.Daily).Symbol

    security = self.AddEquity('ACWI', Resolution.Daily)
    security.SetFeeModel(CustomFeeModel())
    security.SetLeverage(self.leverage)
    self.market:Symbol = security.Symbol

    self.data[self.market] = SymbolData(self.period)
    history = self.History(self.market, self.period, Resolution.Daily)
    if not history.empty:
        closes = history.loc[symbol].close

        for time, close in closes.iteritems():
            self.data[symbol].update(time.date(), close)

    self.rebalance_flag:bool = False
    self.selection_flag:bool = False
    self.UniverseSettings.Resolution = Resolution.Daily
    self.AddUniverse(self.CoarseSelectionFunction, self.FineSelectionFunction)

def OnSecuritiesChanged(self, changes):
    for security in changes.AddedSecurities:
        security.SetFeeModel(CustomFeeModel())
        security.SetLeverage(self.leverage)

def CoarseSelectionFunction(self, coarse):
    curr_date:datetime.date = self.Time.date()

    for equity in coarse:
        symbol:Symbol = equity.Symbol

        if symbol in self.data:
            self.data[symbol].update(curr_date, equity.AdjustedPrice)

    if not self.selection_flag or not self.data[self.market].is_ready():
        return Universe.Unchanged
    
    if not self.data[self.market].data_still_coming(curr_date, self.max_missing_days):
        self.data[self.market].reset_data()
    self.selection_flag = False

    warmed_up_symbols:list[Symbol] = []
    for equity in coarse:
        if not equity.Symbol.Value in self.excluded_stocks:
            continue

        symbol:Symbol = equity.Symbol

        if symbol not in self.data:                
            self.data[symbol] = SymbolData(self.period)
            history = self.History(symbol, self.period, Resolution.Daily)
            if history.empty:
                continue

            closes = history.loc[symbol].close

            for time, close in closes.iteritems():
                self.data[symbol].update(time.date(), close)

        if self.data[symbol].is_ready():
            warmed_up_symbols.append(symbol)

    self.rebalance_flag = True

    return warmed_up_symbols

def FineSelectionFunction(self, fine):
    fine:list[FineFundamental] = list(filter(lambda stock: stock.MarketCap != 0, fine))
    
    total_cap:float = sum(list(map(lambda stock: stock.MarketCap, fine)))

    market_daily_returns:list[float] = self.data[self.market].get_daily_returns()
    beta_values:list[float] = []

    for stock in fine:
        symbol:Symbol = stock.Symbol

        stock_daily_returns:list[float] = self.data[stock.Symbol].get_daily_returns()

        slope, intercept, r_value, p_value, std_err = stats.linregress(market_daily_returns, stock_daily_returns)

        beta_values.append(slope)

        self.weights[symbol] = stock.MarketCap / total_cap

    self.weights[self.market] = -np.average(beta_values)

    return list(self.weights.keys())

def OnData(self, data: Slice):
    if self.esg_exclusion_symbol in data and data[self.esg_exclusion_symbol]:
        self.selection_flag = True
        excluded_tickers:list[str] = [x for x in data[self.esg_exclusion_symbol].GetProperty('tickers')]
        self.excluded_stocks += excluded_tickers

    if not self.rebalance_flag:
        return
    self.rebalance_flag = False

    invested:list[Symbol] = [x.Key for x in self.Portfolio if x.Value.Invested]
    for symbol in invested:
        if symbol not in self.weights:
            self.Liquidate(symbol)
            
    for symbol, w in self.weights.items():
        if symbol in data and data[symbol]:
            self.SetHoldings(symbol, w)

    self.weights.clear()
