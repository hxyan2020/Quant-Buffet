# Original QuantConnect / library Python
# locale=en slug="earnings-announcements-combined-with-stock-repurchases-2"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

from AlgorithmImports import *
import numpy as np
from typing import List, Dict
from dataclasses import dataclass
from pandas.tseries.offsets import BDay
#endregion
class EarningsAnnouncementsCombinedWithStockRepurchases(QCAlgorithm):
def Initialize(self) -> None:
    self.SetStartDate(2015, 1, 1)
    self.SetCash(100_000) 
    
    self.exchange_codes:List[str] = ['NYS', 'NAS', 'ASE']	
    self.selected: Dict[str, Symbol] = {}
    self.price: Dict[str, float] = {}
    self.managed_symbols: List[ManagedSymbol] = []
    self.earnings_universe: List[str] = []
    
    self.earnings: Dict[datetime.date, str] = {}
    self.buybacks: Dict[datetime.date, str] = {}
    
    self.max_traded_stocks: int = 40 # maximum number of trading stocks
    self.quantile: int = 4
    self.leverage: int = 5
    self.open_trade_offset: int = 10
    self.close_trade_offset: int = 15
    self.announcement_lookback: List[int] = [30, 15]
    self.earnings_last_date: Union[None, datetime.date] = None
    self.buybacks_last_date: Union[None, datetime.date] = None
    
    symbol: Symbol = self.AddEquity("SPY", Resolution.Daily).Symbol
    
    # self.first_date:datetime.date|None = None
    earnings_data: str = self.Download('data.quantpedia.com/backtesting_data/economic/earnings_dates_eps.json')
    earnings_data_json: List[dict] = json.loads(earnings_data)
    
    for obj in earnings_data_json:
        date: datetime.date = datetime.strptime(obj['date'], "%Y-%m-%d").date()
        self.earnings_last_date = date
        self.earnings[date] = []
        
        # if not self.first_date: self.first_date = date
        for stock_data in obj['stocks']:
            ticker: str = stock_data['ticker']
            self.earnings[date].append(ticker)
            
            if ticker not in self.earnings_universe:
                self.earnings_universe.append(ticker)
    
    # load buyback dates
    csv_data: str = self.Download('data.quantpedia.com/backtesting_data/equity/BUY_BACKS.csv')
    lines: str = csv_data.split('\r\n')
    
    for line in lines[1:]: # skip header
        line_split: str = line.split(';')
        date: str = line_split[0]
        
        if date == '':
            continue
        
        date: datetime.date = datetime.strptime(date, "%d.%m.%Y").date()
        self.buybacks_last_date =  date
        self.buybacks[date] = []
        
        for ticker in line_split[1:]: # skip date in current line
            self.buybacks[date].append(ticker)
    
    self.months_counter: int = 0
    self.selection_flag: bool = False
    self.settings.daily_precise_end_time = False
    self.Settings.MinimumOrderMarginPortfolioPercentage = 0.
    self.UniverseSettings.Resolution = Resolution.Daily
    self.AddUniverse(self.FundamentalSelectionFunction)
    self.Schedule.On(self.DateRules.MonthStart(symbol), self.TimeRules.AfterMarketOpen(symbol), self.Selection)
    
def OnSecuritiesChanged(self, changes: SecurityChanges) -> None:
    for security in changes.AddedSecurities:
        security.SetFeeModel(CustomFeeModel())
        security.SetLeverage(self.leverage)
        
def FundamentalSelectionFunction(self, fundamental: List[Fundamental]) -> List[Symbol]:        
    # update stocks last prices
    for stock in fundamental:
        ticker: str = stock.Symbol.Value
        
        if ticker in self.earnings_universe:
            # store stock's last price
            self.price[ticker] = stock.AdjustedPrice
    
    # rebalance quarterly
    if not self.selection_flag:
        return Universe.Unchanged
    self.selection_flag = False
    
    # select stocks, which had spin off
    selected: List[Fundamental] = [
        x for x in fundamental if x.MarketCap != 0 \
        and x.SecurityReference.ExchangeId in self.exchange_codes \
        and x.Symbol.Value in self.earnings_universe
    ]
    if len(selected)  None:
    remove_managed_symbols: List[ManagedSymbol] = []
    # check last date on custom data
    if any([self.Time.date() > date for date in [self.earnings_last_date, self.buybacks_last_date]]):
        self.Liquidate()
        return
            
    # check if bought stocks have 15 days after earnings annoucemnet
    for managed_symbol in self.managed_symbols:
        if (managed_symbol.earnings_date + BDay(self.close_trade_offset)).date() = buyback_start and buyback_date  None:
    # quarterly selection
    if self.months_counter % 3 == 0:
        self.selection_flag = True
    self.months_counter += 1
    
@dataclass
class ManagedSymbol():
symbol: Symbol
earnings_date: datetime.date
quantity: int
    
# Custom fee model.
class CustomFeeModel(FeeModel):
def GetOrderFee(self, parameters: OrderFeeParameters) -> OrderFee:
    fee: float = parameters.Security.Price * parameters.Order.AbsoluteQuantity * 0.00005
    return OrderFee(CashAmount(fee, "USD"))
