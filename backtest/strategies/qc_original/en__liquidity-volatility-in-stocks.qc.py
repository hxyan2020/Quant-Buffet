# Original QuantConnect / library Python
# locale=en slug="liquidity-volatility-in-stocks"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

from AlgorithmImports import *
from typing import List, Dict
import data_tools
from dateutil.relativedelta import relativedelta
# endregion

class LiquidityVolatilityinStocks(QCAlgorithm):

def Initialize(self):
    self.SetStartDate(2000, 1, 1)
    self.SetCash(100000)

    self.market:Symbol = self.AddEquity("SPY", Resolution.Daily).Symbol
 
    self.tickers_to_ignore:List[str] = ['KELYB', 'BRKB', 'SGA']

    self.fundamental_count:int = 500
    self.fundamental_sorting_key = lambda x: x.DollarVolume
    
    self.leverage:int = 5
    self.first_quantile:int = 3
    self.second_quantile:int = 5
    self.short_period:int = 12
    self.long_period:int = 36

    self.data:Dict[Symbol, SymbolData] = {}
    self.weight:Dict[Symbol, float] = {}

    self.single_sort_flag:bool = False
    self.selection_flag:bool = False
    self.Settings.MinimumOrderMarginPortfolioPercentage = 0.
    self.UniverseSettings.Resolution = Resolution.Daily
    self.AddUniverse(self.FundamentalSelectionFunction)
    self.Schedule.On(self.DateRules.MonthStart(self.market), self.TimeRules.AfterMarketOpen(self.market), self.Selection)

def OnSecuritiesChanged(self, changes: SecurityChanges) -> None:
    for security in changes.AddedSecurities:
        security.SetFeeModel(data_tools.CustomFeeModel())
        security.SetLeverage(self.leverage)

def FundamentalSelectionFunction(self, fundamental: List[Fundamental]) -> List[Symbol]:
    # store daily stock prices
    for stock in fundamental:
        symbol:Symbol = stock.Symbol
        if stock.Volume != 0:
            volume:float = stock.Volume
        else:
            continue

        if symbol in self.data:
            self.data[symbol].update_daily_data(stock.AdjustedPrice, volume)

    # monthly selection
    if not self.selection_flag:
        return Universe.Unchanged

    selected:List[Fundamental] = [x for x in fundamental if x.HasFundamentalData and x.MarketCap != 0 and x.Market == 'usa' \
                            and ((x.SecurityReference.ExchangeId == "NYS") or (x.SecurityReference.ExchangeId == "NAS") or (x.SecurityReference.ExchangeId == "ASE")) \
                            and x.Symbol.Value not in self.tickers_to_ignore]

    if len(selected) > self.fundamental_count:
        selected = [x for x in sorted(selected, key=self.fundamental_sorting_key, reverse=True)[:self.fundamental_count]]

    liquidity_level:Dict[Symbol, float] = {}
    coefficient_variation:Dict[Symbol, float] = {}

    # price warmup
    for stock in selected:
        symbol:Symbol = stock.Symbol
        if symbol not in self.data:
            self.data[symbol] = data_tools.SymbolData(self.short_period, self.long_period)
            history:DataFrame = self.History(symbol, start=self.Time.date() - relativedelta(months=1), end=self.Time.date())
            if history.empty:
                self.Log(f"Not enough data for {symbol} yet.")
                continue
            data:pd.DataFrame = history.loc[symbol]
            for time, row in data.iterrows():
                if 'volume' not in row:
                    continue
                self.data[symbol].update_daily_data(row.close, row.volume)

        if self.data[symbol].is_ready():
            coeff_variation:float = self.data[symbol].coefficient_variation_calculation()
            if coeff_variation is not None:
                liquidity_level[stock] = self.data[symbol].get_liquidity_level()
                coefficient_variation[stock] = coeff_variation

    if len(coefficient_variation) == 0 or len(liquidity_level) == 0:
        return Universe.Unchanged

    liquidity_portfolios:List[Tuple[List[Fundamental]]] = []

    if len(liquidity_level) >= self.first_quantile * self.second_quantile:
        # single sort by coefficient of variation
        if self.single_sort_flag:
            sorted_liquidity_symbols = sorted(coefficient_variation, key=coefficient_variation.get)
            quantile:int = int(len(sorted_liquidity_symbols) / self.second_quantile)
            long:List[Fundamental] = sorted_liquidity_symbols[:quantile]
            short:List[Fundamental] = sorted_liquidity_symbols[-quantile:]

            liquidity_portfolios.append((long, short))

        # double sort by liquidity level and coefficient of variation
        else:
            sorted_liquidity_symbols:List[Fundamental] = sorted(liquidity_level, key=liquidity_level.get)
            quantile:int = int(len(sorted_liquidity_symbols) / self.first_quantile)
            first_group:List[Fundamental] = list(sorted_liquidity_symbols)[:quantile]
            second_group:List[Fundamental] = list(sorted_liquidity_symbols)[quantile:-quantile]
            third_group:List[Fundamental] = list(sorted_liquidity_symbols)[-quantile:]

            for group in [first_group, second_group, third_group]:
                sorted_group = sorted({symbol: value for symbol, value in coefficient_variation.items() if symbol in group}.items(), key=lambda x: x[1])
                quantile:int = int(len(sorted_group) / self.second_quantile)
                liquidity_portfolios.append(([x[0] for x in sorted_group[:quantile]], [x[0] for x in sorted_group[-quantile:]]))

        # calculate weights based on market cap
        for group in liquidity_portfolios:
            for i, portfolio in enumerate(group):
                mc_sum:float = sum(list(map(lambda stock: stock.MarketCap , portfolio)))
                for stock in portfolio:
                    self.weight[stock.Symbol] = (((-1)**i) * stock.MarketCap / mc_sum) * (1 / len(liquidity_portfolios))
        
    return list(self.weight.keys())

def OnData(self, data: Slice) -> None:
    if not self.selection_flag:
        return
    self.selection_flag = False

    # trade execution
    portfolio:List[PortfolioTarget] = [PortfolioTarget(symbol, w) for symbol, w in self.weight.items() if symbol in data and data[symbol]]
    self.SetHoldings(portfolio, True)

    self.weight.clear()

def Selection(self) -> None:
    self.selection_flag = True
