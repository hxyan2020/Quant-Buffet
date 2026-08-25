# Original QuantConnect / library Python
# locale=en slug="fibonacci-supports-and-resistances-in-cross-sectional-stock-trading"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

from AlgorithmImports import *
from data_tools import CustomFeeModel, SymbolData
from datetime import date
from pandas.core.frame import DataFrame
# endregion

class FibonacciSupportsAndResistancesInCrossSectionalStockTrading(QCAlgorithm):

def Initialize(self):
    self.SetStartDate(2000, 1, 1)
    self.SetCash(100000)
    
    self.history_start:datetime.date = date(1999, 1, 1)

    self.leverage:int = 5
    self.quantile:int = 5
    self.total_portfolio_parts:int = 2  # long + short

    # fibinacci levels: 0, 0.381, 0.5, 0.612, 1
    self.fibonacci_levels:List[float] = [0.5]
    
    self.data:Dict[Symbol, SymbolData] = {}
    self.managed_queue:List[List[Symbol, float]] = []
    self.prev_managed_queue:List[List[Symbol, float]] = []

    self.market_symbol:Symbol = self.AddEquity('SPY', Resolution.Daily).Symbol

    self.coarse_count:int = 500
    self.selection_flag:bool = False
    self.UniverseSettings.Resolution = Resolution.Daily
    self.AddUniverse(self.FundamentalSelectionFunction)
    self.Settings.MinimumOrderMarginPortfolioPercentage = 0.
    self.Schedule.On(self.DateRules.WeekStart(self.market_symbol), self.TimeRules.BeforeMarketClose(self.market_symbol, 0), self.Selection)

def OnSecuritiesChanged(self, changes: SecurityChanges) -> None:
    for security in changes.AddedSecurities:
        security.SetFeeModel(CustomFeeModel())
        security.SetLeverage(self.leverage)

def FundamentalSelectionFunction(self, fundamental: List[Fundamental]) -> List[Symbol]:
    for equity in fundamental:
        symbol:Symbol = equity.Symbol

        if symbol in self.data:
            self.data[symbol].update(equity.AdjustedPrice)

    if not self.selection_flag:
        return Universe.Unchanged
    
    selected:List[Fundamental] = sorted([x for x in fundamental if x.HasFundamentalData and \
        x.SecurityReference.ExchangeId == 'NYS' and x.MarketCap != 0],
            key=lambda x: x.DollarVolume, reverse=True)[:self.coarse_count]

    warm_up_period:int = (self.Time.date() - self.history_start).days
    approach_values:Dict[float, Dict[Symbol, float]] = { fibonacci_level: {} for fibonacci_level in self.fibonacci_levels }

    for stock in selected:
        symbol:Symbol = stock.Symbol

        if symbol not in self.data:
            self.data[symbol] = SymbolData()

            history:DataFrame = self.History(symbol, warm_up_period, Resolution.Daily)
            if history.empty:
                continue
            
            closes:pd.Series = history.loc[symbol].close

            for _, close in closes.items():
                self.data[symbol].update(close)

        if self.data[symbol].ath_atl_ready():
            for fibonacci_level in self.fibonacci_levels:
                fib_level_value:float = self.data[symbol].get_fibonacci_level_value(fibonacci_level)
                approach_value:float = self.data[symbol].get_approach_value(fib_level_value)

                approach_values[fibonacci_level][symbol] = approach_value

    if len(list(approach_values.values())[0])  0, lowest_quantile))
        short:List[Symbol] = list(filter(lambda symbol: approach_value_by_symbol[symbol]  0 and len(short) > 0:
            for i, portfolio in enumerate([long, short]):
                w:float = self.Portfolio.TotalPortfolioValue / total_fibonacci_levels / self.total_portfolio_parts / len(portfolio)
                for symbol in portfolio:
                    selected_symbols.add(symbol)
                    quantity:float = ((-1) ** i) * np.floor(w / self.data[symbol].get_latest_price())
                    self.managed_queue.append([symbol, quantity])

    return list(selected_symbols)
    
def OnData(self, data: Slice) -> None:
    # rebalance monthly
    if not self.selection_flag:
        return
    self.selection_flag = False
    
    # liquidate prev month trades
    for symbol, quantity in self.prev_managed_queue:
        if self.Securities[symbol].Invested:
            self.MarketOrder(symbol, -quantity)

    for symbol, quantity in self.managed_queue:
        if symbol in data and data[symbol]:
            self.MarketOrder(symbol, quantity)

    self.prev_managed_queue = self.managed_queue
    self.managed_queue = []
    
def Selection(self) -> None:
    self.selection_flag = True
