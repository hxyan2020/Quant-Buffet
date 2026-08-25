# Original QuantConnect / library Python
# locale=en slug="cold-ipos-effect"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

from AlgorithmImports import *
from typing import List, Dict, Union, Tuple
from dateutil.relativedelta import relativedelta
from dataclasses import dataclass
import numpy as np
import datetime
#endregion
class ColdIPOsEffect(QCAlgorithm):
def Initialize(self) -> None:
    self.SetStartDate(2010, 1, 1)
    self.SetCash(100_000)
    tickers_to_ignore: List[str] = ['EVOK', 'SGNL', 'VRDN', 'NRBO', 'GEMP', 'CCCR']
    self.UniverseSettings.Leverage = 10
    self.UniverseSettings.Resolution = Resolution.Daily
    self.AddUniverse(self.FundamentalSelectionFunction)
    self.Settings.MinimumOrderMarginPortfolioPercentage = 0.0
    self.settings.daily_precise_end_time = False
    
    self.holding_period: int = 6 # Months
    self.min_ipo_price: int = 5
    self.selection_flag: bool = False
    self.last_update_date: datetime.date = datetime.date(1700, 1, 1)
    self.traded_percentage: float = 0.3
    
    self.etf_symbols: List[Symbol] = []
    # Tuple (stock_ticker: str, is_cold_IPO: bool) in a list keyed by date
    self.ipo_dates: Dict[datetime.date, List[Tuple[str, bool]]] = {}        
    self.price_data: Dict[Symbol, float] = {}
    self.rebalancing_queue: List[RebalanceQueueItem] = []
    self.sector_etfs: Dict[int, Union[str, Symbol]] = {
        104: 'VNQ',  # Vanguard Real Estate Index Fund
        311: 'XLK',  # Technology Select Sector SPDR Fund
        309: 'XLE',  # Energy Select Sector SPDR Fund
        206: 'XLV',  # Health Care Select Sector SPDR Fund
        103: 'XLF',  # Financial Select Sector SPDR Fund
        310: 'XLI',  # Industrials Select Sector SPDR Fund
        101: 'XLB',  # Materials Select Sector SPDR Fund
        102: 'XLY',  # Consumer Discretionary Select Sector SPDR Fund
        105: 'XLP',  # Consumer Staples Select Sector SPDR Fund
        207: 'XLU'   # Utilities Select Sector SPDR Fund    
    }
    
    # Subscribe sector ETFs
    for sector_num, ticker in self.sector_etfs.items():
        security = self.AddEquity(ticker, Resolution.Daily)
        security.SetFeeModel(CustomFeeModel())
        
        # Change sector etf's ticker to sector etf's symbols
        self.sector_etfs[sector_num] = security.Symbol
        self.etf_symbols.append(security.Symbol)
    
    csv_string: str = self.Download('data.quantpedia.com/backtesting_data/equity/cold_ipos_formatted.csv')
    lines: List[str] = csv_string.split('\r\n') 
    # Skip csv header
    lines = lines[1:]
    
    for line in lines:
        if line == '': continue
        
        splitted_line: List[str] = line.split(';')
        
        # csv header: date;ticker;offer_price;opening_price
        date: datetime.date = datetime.datetime.strptime(splitted_line[0], "%d.%m.%Y").date()
        ticker: str = splitted_line[1]
        if ticker in tickers_to_ignore:
            continue
        offer_price: float = float(splitted_line[2])
        opening_price: float = float(splitted_line[3])
        if offer_price  self.last_update_date:
            self.last_update_date = date
            
        # Check if stock has cold IPO (offering price is greater than opening price)
        if offer_price > opening_price:
            self.ipo_dates[date].append((ticker, True))
        else:
            self.ipo_dates[date].append((ticker, False))
    
    market: Symbol = self.AddEquity('SPY', Resolution.Daily).Symbol
    self.Schedule.On(self.DateRules.MonthStart(market), 
                    self.TimeRules.BeforeMarketClose(market), 
                    self.Selection)
def OnSecuritiesChanged(self, changes: SecurityChanges) -> None:
    for security in changes.AddedSecurities:
        security.SetFeeModel(CustomFeeModel())
def FundamentalSelectionFunction(self, fundamental: List[Fundamental]) -> List[Symbol]:
    # Rebalance monthly
    if not self.selection_flag:
        return Universe.Unchanged
    
    current_date: datetime.date = self.Time.date()
    prev_month_date: datetime.date = current_date - relativedelta(months=1)
    
    cold_IPO_tickers: List[str] = []
    
    for date in self.ipo_dates:
        if date >= prev_month_date and date  0:
        portfolio_portion: float = (self.Portfolio.TotalPortfolioValue * self.traded_percentage) / self.holding_period / len(cold_IPOs_stocks_symbols)
        long_symbol_q: List[Tuple[Symbol, float]] = [
            (symbol, np.floor(portfolio_portion / self.price_data[symbol])) for symbol in cold_IPOs_stocks_symbols
        ]
        
        total_cold_IPOs_count: int = sum(list(sectors_total_cold_IPOs.values()))
        
        for sector_num, total_sector_IPOs_count in sectors_total_cold_IPOs.items():
            sector_symbol: Symbol = self.sector_etfs[sector_num]
            price: float = self.price_data[sector_symbol]
            
            # Calculate sector weight:
            # Divide weight by sector price, then multiply it by total count of cold IPO 
            # stocks in this sector. This makes sure, that sectors are equally weigted based 
            # on number of stocks, which had cold IPO in specific sector.
            sector_weight: float = -np.floor((portfolio_portion / price) * (total_sector_IPOs_count / total_cold_IPOs_count))
            
            short_symbol_q.append((sector_symbol, sector_weight))
        
    self.rebalancing_queue.append(RebalanceQueueItem(long_symbol_q + short_symbol_q))
    
    self.price_data.clear()
    
    return cold_IPOs_stocks_symbols + self.etf_symbols
    
def OnData(self, slice: Slice) -> None:
    if not self.selection_flag:
        return
    self.selection_flag = False
    if self.Time.date() > self.last_update_date + relativedelta(months=self.holding_period):
        self.Liquidate()
    
    # Rebalance portfolio
    for item in self.rebalancing_queue:
        if item.holding_period == self.holding_period:
            for symbol, quantity in item.opened_symbol_quantity:
                self.MarketOrder(symbol, -quantity)
        
        # Trade execution    
        if item.holding_period == 0:
            opened_symbol_quantity: List[Tuple[Symbol, float]] = []
            
            for symbol, quantity in item.opened_symbol_quantity:
                if slice.contains_key(symbol) and slice[symbol] is not None:
                    self.MarketOrder(symbol, quantity)
                    opened_symbol_quantity.append((symbol, quantity))
                        
            # only opened orders will be closed        
            item.opened_symbol_quantity = opened_symbol_quantity
            
        item.holding_period += 1
        
    # Remove closed part of portfolio after loop
    self.rebalancing_queue = [
        item for item in self.rebalancing_queue if item.holding_period  None:
    self.selection_flag = True
@dataclass
class RebalanceQueueItem:
opened_symbol_quantity: List[Tuple[Symbol, float]]
holding_period: int = 0
    
class CustomFeeModel(FeeModel):
def GetOrderFee(self, parameters: OrderFeeParameters) -> OrderFee:
    fee: float = parameters.Security.Price * parameters.Order.AbsoluteQuantity * 0.00005
    return OrderFee(CashAmount(fee, "USD"))
