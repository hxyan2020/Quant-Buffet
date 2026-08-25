# Original QuantConnect / library Python
# locale=en slug="patent-to-market-equity-factor"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

from AlgorithmImports import *
from enum import Enum
from dateutil.relativedelta import relativedelta
from pandas.tseries.offsets import BDay
from collections import deque
from typing import List, Dict
#endregion
class PortfolioWeighting(Enum):
EQUALLY_WEIGHTED = 1
VALUE_WEIGHTED = 2
INVERSE_VOLATILITY_WEIGHTED = 3
class PatentToMarketEquityFactor(QCAlgorithm):
def Initialize(self) -> None:
    self.SetStartDate(2005, 1, 1)
    self.SetCash(100_000)
    
    # parameters
    self.reaction_period_after_patent: int = 2  # check for reaction of n days after patent grant
    self.d_period_after_patent: int = self.reaction_period_after_patent + 1 # n of needed daily prices for performance after patent grant calculation
    self.d_volatility_period: int = 60       # daily volatility calculation period
    self.m_cumulative_period: int = 12       # calculate CPM value using n-month cumulative patent performance history
    self.m_rebalance_period: int = 12        # rebalance once a n months
    self.quantile: int = 10                  # portfolio percentile selection (3-tercile; 4-quartile; 5-quintile; 10-decile and so on)
    self.leverage: int = 20
    self.portfolio_weighting: PortfolioWeighting = PortfolioWeighting.EQUALLY_WEIGHTED
    # assign larger daily period if volatility weighting is set
    if self.portfolio_weighting == PortfolioWeighting.INVERSE_VOLATILITY_WEIGHTED:
        self.max_period: int = max(self.d_volatility_period, self.d_period_after_patent)
    else:
        self.max_period: int = self.d_period_after_patent
    self.required_exchanges: List[str] = ['NYS', 'NAS', 'ASE']
    self.CMPs: Dict[str, float] = {}                                              # recent CPM value storage
    self.weights: Dict[Symbol, float] = {}                                        # recent portfolio selection traded weights
    self.patent_dates: Dict[datetime.datetime, list[str]] = {}                    # storing list of stocks keyed by their patent date
    self.market_moves: Dict[str, list[tuple(float, datetime.datetime.date)]] = {} # storing all market moves in one year keyed by stock's ticker
    
    # Source: https://companyprofiles.justia.com/companies
    csv_string_file: str = self.Download('data.quantpedia.com/backtesting_data/economic/patents.csv')
    lines: List[str] = csv_string_file.split('\r\n')
    
    # select header, then exclude 'date'
    tickers: List[str] = lines[0].split(';')[1:]
    
    # store RollingWindow object keyed by stock ticker 
    self.prices: Dict[str, deque] = { ticker : deque(maxlen=self.max_period) for ticker in tickers }
    
    for line in lines[1:]:
        if line == '':
            continue
        
        line_split: List[str] = line.split(';')
        date: datetime.date = datetime.strptime(line_split[0], "%d.%m.%Y").date()
        
        # initialize empty list for stock's tickers, which have patent in current date
        self.patent_dates[date] = []
        
        length: int = len(line_split)
        
        for index in range(1, length):
            # store stock's ticker into list, when stock has patent in current date
            if line_split[index] != '0.0' and line_split[index] != '0':
                self.patent_dates[date].append(tickers[index - 1])
            
    self.market: Symbol = self.AddEquity('SPY', Resolution.Daily).Symbol
    
    # add market to prices dictionary
    self.prices[self.market.Value] = deque(maxlen=self.max_period)
    self.symbol_by_ticker:dict[str, Symbol] = {}
    self.month_counter: int = 0
    self.selection_flag: bool = False
    self.settings.daily_precise_end_time = False
    self.Settings.MinimumOrderMarginPortfolioPercentage = 0.
    self.UniverseSettings.Resolution = Resolution.Daily
    self.AddUniverse(self.FundamentalSelectionFunction)
    self.Schedule.On(self.DateRules.MonthEnd(self.market), self.TimeRules.BeforeMarketClose(self.market), self.Selection)
def OnSecuritiesChanged(self, changes: SecurityChanges) -> None:
    for security in changes.AddedSecurities:
        security.SetFeeModel(CustomFeeModel())
        security.SetLeverage(self.leverage)
def FundamentalSelectionFunction(self, fundamental: List[Fundamental]) -> List[Symbol]:
    # update daily prices
    for stock in fundamental:
        ticker:str = stock.Symbol.Value
        
        if ticker in self.prices:
            self.symbol_by_ticker[ticker] = stock.Symbol
            if stock.AdjustedPrice != 0:
                self.prices[ticker].append((self.Time.date(), stock.AdjustedPrice))
    
    days_before: datetime.datetime = (self.Time - BDay(self.reaction_period_after_patent)).date()
    # check if there was any patent granted in d_period_after_patent days before todays date
    # market has to have price data ready
    if days_before in self.patent_dates and len(self.prices[self.market.Value]) == self.prices[self.market.Value].maxlen:
        if self.prices[self.market.Value][-self.d_period_after_patent][0] == days_before:
            # calculate market's return for last d_period_after_patent days
            market_return: float = self.prices[self.market.Value][-1][1] / self.prices[self.market.Value][-self.d_period_after_patent][1] - 1
            tickers: List[str] = self.patent_dates[days_before]
            
            # calc market moves
            for ticker in tickers:
                # if not self.prices[ticker].IsReady:
                if len(self.prices[ticker]) != self.prices[ticker].maxlen:
                    continue
                
                if self.prices[ticker][-self.d_period_after_patent][0] == days_before:
                    # calc stock's return for last d_period_after_patent days
                    stock_return: float = self.prices[ticker][-1][1] / self.prices[ticker][-self.d_period_after_patent][1] - 1
                    
                    # calc excess market move value
                    market_move_value: float = stock_return - market_return
                    
                    if ticker not in self.market_moves:
                        self.market_moves[ticker] = []
                    self.market_moves[ticker].append((days_before, market_move_value))
    
    # rebalance yearly    
    if not self.selection_flag:
        return Universe.Unchanged
    
    # select stocks, which has at least one market move value
    selected: List[Fundamental] = [
        x for x in fundamental 
        if x.MarketCap != 0 
        and x.SecurityReference.ExchangeId in self.required_exchanges 
        and x.CompanyReference.IsREIT != 1
        and x.Symbol.Value in self.market_moves
        ]
    
    PMT:dict[Fundamental, float] = {}   # stores stock's PMT value keyed by stock's object
    volatility:dict[Symbol, float] = {}     # stores volatility values for each symbol in current selection
    
    for stock in selected:
        symbol: Symbol = stock.Symbol
        ticker: str = symbol.Value
        market_cap: float = stock.MarketCap
        
        # fetch only market moves stored within cumulative period window
        sum_market_move: float = sum([x[1] for x in self.market_moves[ticker] if x[0] >= (self.Time - relativedelta(months=self.m_cumulative_period)).date()])
        
        # in case there isn't last_CMP use formula: CMP = MP / (g + gama), otherwise use formula: # CMP = (1 - gama) * last_CMP + MP
        curr_CMP_value: float = 0.85 * self.CMPs[ticker] + sum_market_move if ticker in self.CMPs else sum_market_move / (0.20 + 0.15)
        
        # store new current CMP value keyed by stock's ticker
        self.CMPs[ticker] = curr_CMP_value
        
        # calc stock's PMT value
        PMT_value: float = curr_CMP_value / market_cap
        
        # store stock's PMT value keyed by stock's object
        PMT[stock] = PMT_value
        
        # volatility calculation - self.d_volatility_period
        daily_prices: np.ndarray = np.array([x[1] for x in self.prices[ticker]][-self.d_volatility_period:])
        daily_returns: np.ndarray =  daily_prices[1:] / daily_prices[:-1] - 1
        volatility[symbol] = np.std(daily_returns) * np.sqrt(252) # annualized volatility
        
    # make sure, there are enough stocks for selection
    if len(PMT)  None:
    # wait for selection flag to be set
    if not self.selection_flag:
        return
    self.selection_flag = False
    
    # trade execution
    portfolio: List[PortfolioTarget] = [PortfolioTarget(symbol, w) for symbol, w in self.weights.items() if symbol in data and data[symbol]]
    self.SetHoldings(portfolio, True)
    self.weights.clear()
    
def Selection(self) -> None:
    # wait for self.m_cumulative_period months to elapse from the start of the algorithm before first selection. It gives the chance to self.market_moves to potentially fill up.
    if self.Time.date()  OrderFee:
    fee: float = parameters.Security.Price * parameters.Order.AbsoluteQuantity * 0.00005
    return OrderFee(CashAmount(fee, "USD"))
