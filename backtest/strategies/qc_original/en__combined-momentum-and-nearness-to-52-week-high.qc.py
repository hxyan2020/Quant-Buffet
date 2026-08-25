# Original QuantConnect / library Python
# locale=en slug="combined-momentum-and-nearness-to-52-week-high"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

from AlgorithmImports import *
import data_tools
# endregion

class CombinedMomentumAndNearnessTo52WeekHigh(QCAlgorithm):

def Initialize(self):
    self.SetStartDate(2000, 1, 1)
    self.SetCash(100000)

    self.leverage:int = 5
    self.quantile:int = 5
    self.total_portfolios:int = 2
    self.portfolio_percentage:float = 1

    self.min_price_period:int = 15
    self.min_volume_period:int = 15
    self.min_share_price:float = 1.
    self.high_period:int = 52 * 5

    self.exchanges:List[str] = ['NYS', 'NAS', 'ASE']

    self.data:Dict[Symbol, data_tools.SymbolData] = {}
    self.weight:Dict[Symbol, float] = {}
    self.selected_symbols:List[Symbol] = []

    self.fundamental_count:int = 500
    self.fundamental_sorting_key = lambda x: x.DollarVolume

    self.market_symbol:Symbol = self.AddEquity('SPY', Resolution.Daily).Symbol

    self.selection_flag:bool = False
    self.UniverseSettings.Resolution = Resolution.Daily
    self.AddUniverse(self.FundamentalSelectionFunction)
    self.Settings.MinimumOrderMarginPortfolioPercentage = 0.
    self.Schedule.On(self.DateRules.MonthStart(self.market_symbol), self.TimeRules.BeforeMarketClose(self.market_symbol, 0), self.Selection)

def OnSecuritiesChanged(self, changes: SecurityChanges) -> None:
    for security in changes.AddedSecurities:
        security.SetFeeModel(data_tools.CustomFeeModel())
        security.SetLeverage(self.leverage)

def FundamentalSelectionFunction(self, fundamental: List[Fundamental]) -> List[Symbol]:
    if not self.selection_flag:
        return Universe.Unchanged
    
    selected:List[Fundamental] = [x for x in fundamental if x.HasFundamentalData and x.Market == 'usa' and x.AdjustedPrice >= self.min_share_price and x.MarketCap != 0 and \
        not np.isnan(x.EarningReports.BasicAverageShares.ThreeMonths) and x.EarningReports.BasicAverageShares.ThreeMonths != 0 and x.SecurityReference.ExchangeId in self.exchanges]

    if len(selected) > self.fundamental_count:
        selected = [x for x in sorted(selected, key=self.fundamental_sorting_key, reverse=True)[:self.fundamental_count]]
    
    self.selected_symbols.clear()
    
    for stock in selected:
        symbol:Symbol = stock.Symbol
        self.selected_symbols.append(symbol)

        if symbol not in self.data:
            self.data[symbol] = data_tools.SymbolData(self.high_period)

        self.data[symbol].update_shares_outstanding(stock.EarningReports.BasicAverageShares.ThreeMonths)
        self.data[symbol].update_market_cap(stock.MarketCap)

    symbols_to_delete:List[Symbol] = list(filter(lambda symbol: symbol not in self.selected_symbols, self.data))
    for symbol in symbols_to_delete:
        del self.data[symbol]
    
    return self.selected_symbols

def OnData(self, data: Slice) -> None:
    for symbol in self.selected_symbols:
        if symbol in data and data[symbol] and data[symbol].High != 0 and \
         data[symbol].Price != 0 and data[symbol].Volume != 0:
            high:float = data[symbol].High
            volume:float = data[symbol].Volume
            price:float = data[symbol].Price

            self.data[symbol].update(price, volume, high)

    if not self.selection_flag:
        return
    self.selection_flag = False

    performance:Dict[Symbol, float] = {}
    turnover:Dict[Symbol, float] = {}
    PTH:Dict[Symbol, float] = {}

    for symbol in self.selected_symbols:
        symbol_obj:data_tools.SymbolData = self.data[symbol]

        if symbol_obj.PTH_data_ready():
            symbol_obj.update_PTH_values()
        else:
            symbol_obj.reset_PTH_values()

        if symbol_obj.is_ready(self.min_price_period, self.min_volume_period):
            performance[symbol] = symbol_obj.get_performance()
            turnover[symbol] = symbol_obj.get_turnover()
            PTH[symbol] = symbol_obj.get_prev_PTH_value()

        symbol_obj.reset_prices()
        symbol_obj.reset_volumes()
    
    if len(performance)  None:
    for i, portfolio in enumerate([long_leg, short_leg]):
        mc_sum:float = sum(list(map(lambda symbol: self.data[symbol].get_market_cap(), portfolio)))
        for symbol in portfolio:
            self.weight[symbol] = ((self.data[symbol].get_market_cap() / mc_sum) / self.total_portfolios) * self.portfolio_percentage
    
def Selection(self) -> None:
    self.selection_flag = True
