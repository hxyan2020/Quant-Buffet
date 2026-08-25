# Original QuantConnect / library Python
# locale=en slug="categorization-effect-in-stocks"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

from AlgorithmImports import *
from typing import List, Dict
import pandas as pd
import numpy as np
# endregion
class CategorizationEffectInStocks(QCAlgorithm):
def Initialize(self) -> None:
    self.SetStartDate(2002, 1, 1)
    self.SetCash(100_000)
    self.UniverseSettings.Leverage = 5
    self.UniverseSettings.Resolution = Resolution.Daily
    self.AddUniverse(self.FundamentalSelectionFunction)
    self.Settings.MinimumOrderMarginPortfolioPercentage = 0.0
    self.settings.daily_precise_end_time = False
    
    self.exchange_codes: List[str] = ['NYS', 'NAS', 'ASE']
    self.week_period: int = 5
    self.quantile: int = 5
    self.selection_flag: bool = False
    
    self.prices: Dict[str, RollingWindow] = {}
    self.firm_similarity: Dict[int, Dict[str, Dict[str, float]]] = {}
    self.yearly_universes: Dict[int, List[str]] = {}
    self.long_symbols: List[Symbol] = []
    self.short_symbols: List[Symbol] = []
    csv: str = self.Download('data.quantpedia.com/backtesting_data/equity/industries/firm_similarity.csv')
    lines: List[str] = csv.split('\r\n')
    for line in lines[1:]: # Skip header
        if line == '':
            continue
        line_split: List[str] = line.split(';')
        year: int = int(line_split[0].split('-')[0])
        if year not in self.firm_similarity:
            self.firm_similarity[year]: Dict = {}
        if year not in self.yearly_universes:
            self.yearly_universes[year]: List = []
        industry_comp_ticker: str = line_split[1]
        if industry_comp_ticker not in self.firm_similarity[year]:
            self.firm_similarity[year][industry_comp_ticker]: Dict = {}
        if industry_comp_ticker not in self.yearly_universes[year]:
            self.yearly_universes[year].append(industry_comp_ticker)
        company_ticker: str = line_split[2]
        score: float = float(line_split[3])
        self.firm_similarity[year][industry_comp_ticker][company_ticker]: float = score
        self.yearly_universes[year].append(company_ticker)
    market: Symbol = self.AddEquity('SPY', Resolution.Daily).Symbol
    self.Schedule.On(
        self.DateRules.EveryDay(market), 
        self.TimeRules.BeforeMarketClose(market), 
        self.Selection)
def OnSecuritiesChanged(self, changes: SecurityChanges) -> None:
    for security in changes.AddedSecurities:
        security.SetFeeModel(CustomFeeModel())
def FundamentalSelectionFunction(self, fundamental: List[Fundamental]) -> List[Symbol]:
    # Update daily prices
    for f in fundamental:
        ticker: str = f.Symbol.Value
        if ticker in self.prices:
            self.prices[ticker].Add(f.Price)
    if not self.selection_flag:
        return Universe.Unchanged
    prev_year: int = self.Time.year - 1
    
    if prev_year not in self.firm_similarity:
        return Universe.Unchanged
    
    # Select universe
    curr_year_universe: List[str] = self.yearly_universes[prev_year]
    selected: List[Fundamental] = [f for f in fundamental if f.HasFundamentalData
                            and f.Symbol.Value in curr_year_universe
                            and f.SecurityReference.ExchangeId in self.exchange_codes
                            and not np.isnan(f.AssetClassification.MorningstarIndustryGroupCode)]
    
    warmed_up_stocks: List[Fundamental] = []
    # Warm up stock prices
    for f in selected:
        symbol: Symbol = f.Symbol
        ticker: str = symbol.Value
        if ticker not in self.prices:
            self.prices[ticker] = RollingWindow[float](self.week_period)
            history: pd.DataFrame = self.History(symbol, self.week_period, Resolution.Daily)
            if history.empty:
                continue
            closes: pd.Series = history.loc[symbol].close
            for _, close in closes.items():
                self.prices[ticker].Add(close)
        if self.prices[ticker].IsReady:
            warmed_up_stocks.append(f)
    csv_industries: Dict[str, Dict[str, float]] = self.firm_similarity[prev_year]
    industry_code_ticker: Dict[str, str] = {}
    industries_groups: Dict[str, List[Symbol]] = {}
    industry_diff_by_symbol: Dict[Symbol, float] = {}
    symbol_by_ticker: Dict[str, Symbol] = {}
    # Create industries groups
    for f in warmed_up_stocks:            
        symbol: Symbol = f.Symbol
        ticker: str = symbol.Value
        industry_group_code: str = f.AssetClassification.MorningstarIndustryGroupCode
        if ticker in csv_industries:
            # Create match of csv industry group with QC industry group
            industry_code_ticker[industry_group_code]: str = ticker
            # Create match between stock's ticker and it's symbol, because this stock can be traded 
            symbol_by_ticker[ticker] = symbol
        if industry_group_code not in industries_groups:
            industries_groups[industry_group_code]: List[Symbol] = []
        industries_groups[industry_group_code].append(f.Symbol)
    # Calculate difference between industry performances
    for industry_group_code, ticker in industry_code_ticker.items():
        industry_universe: List[Symbol] = industries_groups[industry_group_code]
        # Official industry performance calculation
        official_industry_perf: float = np.mean([self.Performance(self.prices[symbol.Value]) 
                                                    for symbol in industry_universe])
        
        # Fundamental industry performance calculation
        tickers_similarities: Dict[str, float] = self.firm_similarity[prev_year][ticker]
        fundamental_industry_perf: float = sum([self.Performance(self.prices[stock_ticker]) * similarity_score 
                                                for stock_ticker, similarity_score in tickers_similarities.items() 
                                                    if stock_ticker in self.prices and self.prices[stock_ticker].IsReady])
        total_industry_score: float = sum(list(tickers_similarities.values()))
        if fundamental_industry_perf != 0 and total_industry_score != 0:
            fundamental_industry_perf /= total_industry_score
            
            trade_symbol: Symbol = symbol_by_ticker[ticker]
            curr_industries_diff: float = official_industry_perf - fundamental_industry_perf
            industry_diff_by_symbol[trade_symbol] = fundamental_industry_perf
    # Make sure there are enough stocks for selection
    if len(industry_diff_by_symbol)  None:
    # Rebalance weekly
    if not self.selection_flag:
        return
    self.selection_flag = False
    
    # Trade execution
    targets: List[PortfolioTarget] = []
    for i, portfolio in enumerate([self.long_symbols, self.short_symbols]):
        for symbol in portfolio:
            if slice.ContainsKey(symbol) and slice[symbol] is not None:
                targets.append(PortfolioTarget(symbol, ((-1) ** i) / len(portfolio)))
    self.SetHoldings(targets, True)
    self.long_symbols.clear()
    self.short_symbols.clear()
def Performance(self, prices_roll_window: RollingWindow) -> float:
    return (prices_roll_window[0] / prices_roll_window[prices_roll_window.Count - 1]) - 1
def Selection(self) -> None:
    if self.Time.weekday() == 0:
        self.selection_flag = True
class CustomFeeModel(FeeModel):
def GetOrderFee(self, parameters: OrderFeeParameters) -> OrderFee:
    fee: float = parameters.Security.Price * parameters.Order.AbsoluteQuantity * 0.00005
    return OrderFee(CashAmount(fee, "USD"))
