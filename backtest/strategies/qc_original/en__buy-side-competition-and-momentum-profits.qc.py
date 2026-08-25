# Original QuantConnect / library Python
# locale=en slug="buy-side-competition-and-momentum-profits"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

from AlgorithmImports import *
import data_tools
from typing import List, Dict, Set
from itertools import combinations
from pandas.core.frame import DataFrame
from pandas.core.series import Series
import numpy as np
# endregion
class BuySideCompetitionandMomentumProfits(QCAlgorithm):
def Initialize(self):
    self.SetStartDate(2010, 1, 1)
    self.SetCash(100000)
    self.exchange_codes:List[str] = ['NYS', 'NAS', 'ASE']
    self.market: Symbol = self.AddEquity('SPY', Resolution.Daily).Symbol
    self.competition_quantile: int = 3
    self.momentum_quantile: int = 5
    self.leverage: int = 5
    self.month_period: int = 21
    self.period: int = 12
    self.competition_period: int = 9
    self.target_granularity: float = 0.08858
    self.min_share_price: int = 1
    self.fundamental_count: int = 1000
    self.fundamental_sorting_key = lambda x: x.DollarVolume
    self.data: Dict[Symbol, SymbolData] = {}
    self.weight: Dict[Symbol, float] = {} 
    self.stock_competition: Dict[str, RollingWindow] = {}
    self.holdings_by_fund: Dict[str, FundHoldings] = {}
    self.ticker_universe: Set = set()  # every ticker stored in hedge fund holdings data
    self.funds_tickers: Dict[str, dict[datetime.date, list]] = {}
    hedge_fund_file_content: str = self.Download('data.quantpedia.com/backtesting_data/equity/hedge_fund_holdings/hedge_funds_holdings.json')
    hedge_funds_data: List[Dict[str, Dict[str, str]]] = json.loads(hedge_fund_file_content)
    for hedge_fund_data in hedge_funds_data:
        hedge_fund_names: List[str] = list(hedge_fund_data.keys())
        hedge_fund_names.remove('date')
        date: datetime.date = datetime.strptime(hedge_fund_data['date'], '%d.%m.%Y').date()
        for hedge_fund_name in hedge_fund_names:
            if hedge_fund_name not in self.holdings_by_fund:
                self.holdings_by_fund[hedge_fund_name] = data_tools.FundHoldings(hedge_fund_name)
            holding_list: List[StockHolding] = []
            holdings: List[dict] = hedge_fund_data[hedge_fund_name]['stocks']
            for holding in holdings:
                ticker: str = holding['ticker']
                number_of_shares: int = int(holding['#_of_shares'])
                weight: float = float(holding['weight'])
                self.ticker_universe.add(ticker)
                if ticker not in self.funds_tickers:
                    # initialize dictionary for stock's ticker
                    self.funds_tickers[ticker] = {}
                if date not in self.funds_tickers[ticker]:
                    # initialize list, where will be all funds, which hold this stock in this date
                    self.funds_tickers[ticker][date] = []
                
                # add fund with stock weight in that fund to list == tuple (hedge_fund_name, weight)
                self.funds_tickers[ticker][date].append((hedge_fund_name, weight))
                holding_list.append(data_tools.StockHolding(ticker, number_of_shares, weight))
            
            self.holdings_by_fund[hedge_fund_name].holdings_by_date[date] = holding_list
    self.last_date: datetime.date = max([max(x.holdings_by_date) for x in self.holdings_by_fund.values()])
    self.selection_flag: bool = False
    self.settings.daily_precise_end_time = False
    self.Settings.MinimumOrderMarginPortfolioPercentage = 0.
    self.UniverseSettings.Resolution = Resolution.Daily
    self.AddUniverse(self.FundamentalSelectionFunction)
    self.Schedule.On(self.DateRules.MonthStart(self.market), self.TimeRules.AfterMarketOpen(self.market), self.Selection)
def OnSecuritiesChanged(self, changes: SecurityChanges) -> None:
    for security in changes.AddedSecurities:
        security.SetFeeModel(data_tools.CustomFeeModel())
        security.SetLeverage(self.leverage)
    
    for security in changes.RemovedSecurities:
        if security.Symbol in self.data:
            self.data.pop(security.Symbol)
def FundamentalSelectionFunction(self, fundamental: List[Fundamental]) -> List[Symbol]:
    # monthly selection
    if not self.selection_flag:
        return Universe.Unchanged
    # update the rolling window every month
    for stock in fundamental:
        symbol: Symbol = stock.Symbol
        if symbol in self.data:
            self.data[symbol].update_data(stock.AdjustedPrice)
    selected: List[Fundamental] = [
        x for x in fundamental 
        if x.HasFundamentalData 
        and x.Market == 'usa' 
        and x.MarketCap != 0 
        and x.Price >= self.min_share_price 
        and x.Symbol.Value in self.ticker_universe 
        and x.AssetClassification.MorningstarSectorCode != MorningstarSectorCode.FinancialServices 
        and x.SecurityReference.ExchangeId in self.exchange_codes
    ]
    if len(selected) > self.fundamental_count:
        selected = [x for x in sorted(selected, key=self.fundamental_sorting_key, reverse=True)[:self.fundamental_count]]
    
    # warmup price rolling windows
    for stock in selected:
        symbol: Symbol = stock.Symbol
        if symbol in self.data:
            continue
        
        self.data[symbol] = data_tools.SymbolData(self.period)
        history: DataFrame = self.History(symbol, self.period * self.month_period, Resolution.Daily)
        if history.empty:
            self.Log(f"Not enough data for {symbol} yet.")
            continue
        closes: Series = history.loc[symbol].close.groupby(pd.Grouper(freq='M')).last()
        for time, close in closes.items():
            self.data[symbol].update_data(close)
    selected_dict: Dict[Symbol, Fundamental] = {x.Symbol.Value: x for x in selected if self.data[x.Symbol].is_ready()}
    stock_z_score: Dict[str, float] = {}
    fund_z_score: Dict[str, float] = {}
    if len(selected_dict) != 0:
        cross_mean: float = np.mean([sym_data.get_momentum() for sym, sym_data in self.data.items() if sym.Value in selected_dict and sym_data.is_ready()])
        cross_std: float = np.std([sym_data.get_momentum() for sym, sym_data in self.data.items() if sym.Value in selected_dict and sym_data.is_ready()])
        
        # calculate z-score of stocks
        stock_z_score: Dict[str, float] = {ticker: (self.data[selected_dict[ticker].Symbol].get_momentum() - cross_mean) / cross_std for ticker in self.ticker_universe \
            if ticker in selected_dict and self.data[selected_dict[ticker].Symbol].is_ready()}
        # calculate z-score of funds
        for fund, fund_data in self.holdings_by_fund.items():
            last_date: List[datetime.date] = [x for x in list(fund_data.holdings_by_date.keys()) if x  0 else None
            if last_date is None:
                continue
            
            if len(date[last_date]) > 1:
                fund_competition: List[float] = []
                for fund, weight in date[last_date]:
                    fund_competition.append(sum([normalization_constant - abs(fund_z_score[fund] - fund_z_score[x]) for x, w in date[last_date] \
                        if x != fund and abs(fund_z_score[fund] - fund_z_score[x])  2 and sum(fund_competition) != 0:
                    COMP[selected_dict[ticker].Symbol] = np.mean(fund_competition)
                    # if ticker not in self.stock_competition:
                    #     self.stock_competition[ticker] = RollingWindow[float](self.competition_period)
                    # self.stock_competition[ticker].Add(np.mean(fund_competition))  
                    # if self.stock_competition[ticker].IsReady:
                    #     COMP[selected_dict[ticker].Symbol] = np.mean(list(self.stock_competition[ticker])[::-1][:5])
        
        # remove keys with duplicate COMP values for the sake of not random backtest
        COMP_no_repl: Dict[float, Symbol] = {}
        for key, val in COMP.items():
            COMP_no_repl.setdefault(val, key)
        COMP_no_repl: Dict[Symbol, float] = dict((v, k) for k, v in COMP_no_repl.items())
            
        # sort and divide to quantiles
        if len(COMP_no_repl) >= self.competition_quantile * self.momentum_quantile:
            sorted_stock_level_competitions: List[Symbol] = sorted(COMP_no_repl, key=COMP_no_repl.get)
            quantile: int = int(len(sorted_stock_level_competitions) / self.competition_quantile)
            lowest_competition: List[Symbol] = sorted_stock_level_competitions[:quantile]
            # get momemtum for second sorting
            lowest_competitions: Dict[Symbol, float] = {sym: sym_data.get_momentum() for sym, sym_data in self.data.items() if sym in lowest_competition and sym.Value in selected_dict}
            sorted_lowest_competitions: List[Symbol] = sorted(lowest_competitions, key=lowest_competitions.get, reverse=True)
            quantile: int = int(len(sorted_lowest_competitions) / self.momentum_quantile)
            long: List[Symbol] = sorted_lowest_competitions[:quantile]
            short: List[Symbol] = sorted_lowest_competitions[-quantile:]
            # calculate weights based on values
            for i, portfolio in enumerate([long, short]):
                mc_sum: float = sum(list(map(lambda symbol: selected_dict[symbol.Value].MarketCap, portfolio)))
                for symbol in portfolio:
                    self.weight[symbol] = ((-1)**i) * selected_dict[symbol.Value].MarketCap / mc_sum
    return list(self.weight.keys())
def OnData(self, data: Slice) -> None:
    # rebalance monthly
    if not self.selection_flag:
        return
    self.selection_flag = False
    # trade execution
    portfolio: List[PortfolioTarget] = [PortfolioTarget(symbol, w) for symbol, w in self.weight.items() if symbol in data and data[symbol]]
    
    self.SetHoldings(portfolio, True)
    self.weight.clear()
def Selection(self) -> None:
    if self.Time.date() > self.last_date:
        self.Liquidate()
        return
    self.selection_flag = True
