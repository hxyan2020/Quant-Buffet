# Original QuantConnect / library Python
# locale=en slug="spin-off-anomaly"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

from AlgorithmImports import *
import numpy as np
from typing import List, Dict
#endregion
class SpinOffAnomaly(QCAlgorithm):
def Initialize(self) -> None:
    self.SetStartDate(2009, 1, 1) # spin off dates start at 2009
    self.SetCash(100_000)
    
    self.data: Dict[Symbol, SymbolData] = {}    # storing stocks sector
    self.tickers: List[str] = []                # storing tickers, which have spin offs
    self.selected_symbols: List[Symbol] = []    # storing stocks for trading
    self.managed_symbols: List[ManagedSymbol] = []
    
    self.holding_period: int = 6 * 21   # holding stocks and shorting ETF for n days
    self.max_traded_stocks: int = 25    # maximum number of trading max_traded_stocks
    self.leverage: int = 5
    
    self.etfs: Dict[int, str] = {
        104: 'VNQ',  # Vanguard Real Estate Index Fund
        311: 'XLK',  # Technology Select Sector SPDR Fund
        309: 'XLE',  # Energy Select Sector SPDR Fund
        206: 'XLV',  # Health Care Select Sector SPDR Fund
        103: 'XLF',  # Financial Select Sector SPDR Fund
        310: 'XLI',  # Industrials Select Sector SPDR Fund
        101: 'XLB',  # Materials Select Sector SPDR Fund
        205: 'XLY',  # Consumer Discretionary Select Sector SPDR Fund
        102: 'XLP',  # Consumer Staples Select Sector SPDR Fund
        207: 'XLU',  # Utilities Select Sector SPDR Fund    
        308: 'XLC'   # Communications Services
    }
    
    self.symbol: Symbol = self.AddEquity("SPY", Resolution.Daily).Symbol
    
    self.spin_offs: Symbol = self.AddData(QuantpediaSpinOffs, 'SPIN_OFFS', Resolution.Daily).Symbol
    
    for _, ticker in self.etfs.items():
        security = self.AddEquity(ticker, Resolution.Daily)
        security.SetFeeModel(CustomFeeModel())
        security.SetLeverage(self.leverage)
        
        # create SymbolData object for etf
        self.data[ticker] = SymbolData()
        
    self.selection_flag: bool = False
    self.Settings.MinimumOrderMarginPortfolioPercentage = 0.
    self.settings.daily_precise_end_time = False
    self.UniverseSettings.Resolution = Resolution.Daily
    self.AddUniverse(self.FundamentalSelectionFunction)
    
def OnSecuritiesChanged(self, changes: SecurityChanges) -> None:
    for security in changes.AddedSecurities:
        security.SetFeeModel(CustomFeeModel())
        security.SetLeverage(self.leverage)
        
def FundamentalSelectionFunction(self, fundamental: List[Fundamental]) -> List[Symbol]:
    # rebalance, when spin off tickers came
    if not self.selection_flag:
        return Universe.Unchanged
    self.selection_flag = False
    
    # select stocks, which had spin off
    selected: List[Symbol] = [x.Symbol for x in fundamental if x.HasFundamentalData and x.Symbol.Value in self.tickers and x.AssetClassification.MorningstarSectorCode] 
    
    etfs_tickers: List[str] = [ticker for _, ticker in self.etfs.items()]
    
    self.selected_symbols = []
    for stock in fundamental:
        symbol: Symbol = stock.Symbol
        ticker: str = symbol.Value
        
        # get last stock price for quantity calculation
        if symbol in selected:
            if symbol not in self.data:
                self.data[symbol] = SymbolData()
            
            self.data[symbol].update_price(stock.AdjustedPrice)
        
            # get stock's sector
            sector: str = stock.AssetClassification.MorningstarSectorCode
            # store stock's sector
            self.data[symbol].update_sector(sector)
            self.selected_symbols.append(symbol)
        # update etfs prices
        if ticker in etfs_tickers:
            self.data[ticker].update_price(stock.AdjustedPrice)
    return self.selected_symbols
def OnData(self, data: Slice) -> None:
    spin_offs_last_update_date: Dict[Symbol, datetime.date] = QuantpediaSpinOffs.get_last_update_date()
    if self.Securities[self.spin_offs].GetLastData() and self.Time.date() > spin_offs_last_update_date[self.spin_offs]:
        self.Liquidate()
        return
    if self.spin_offs in data and data[self.spin_offs]:
        self.tickers = [x for x in data[self.spin_offs].Tickers]
        self.selection_flag = True
     
    # storing managed symbols, which need to be removed from self.managed_symbols
    # and it's stock and ETF needs to be liquidated
    remove_managed_symbols: List[ManagedSymbol] = [] 
        
    for managed_symbol in self.managed_symbols:
        managed_symbol.holding_period += 1
        
        # stock has to be liquidate with it's ETF
        if managed_symbol.holding_period == self.holding_period:
            remove_managed_symbols.append(managed_symbol)
            
            # liquidate stock by selling it's quantity
            self.MarketOrder(managed_symbol.symbol, -managed_symbol.stock_quantity)
            # liquidate etf by buying it's quantity
            self.MarketOrder(managed_symbol.etf, managed_symbol.etf_quantity)
    
    # remove managed symbols from self.managed_symbols        
    for managed_symbol in remove_managed_symbols:
        self.managed_symbols.remove(managed_symbol)
    
    # trade only if there are some stocks selected from FineSelectionFunction
    if len(self.selected_symbols) == 0:
        return
    
    for symbol in self.selected_symbols:
        # check if there is a place for trading current stock
        if len(self.managed_symbols)  None:
    self.holding_period: int = 0
    self.symbol: Symbol = symbol
    self.etf: str = etf
    self.stock_quantity: int = stock_quantity
    self.etf_quantity: int = etf_quantity
    
class SymbolData():
def __init__(self) -> None:
    self.last_price: float = .0
    self.sector: int = 0
    
def update_price(self, price: float) -> None:
    self.last_price = price
def update_sector(self, sector: int) -> None:
    self.sector = sector
# Quantpedia data.
# NOTE: IMPORTANT: Data order must be ascending (datewise)
class QuantpediaSpinOffs(PythonData):
_last_update_date:Dict[Symbol, datetime.date] = {}
@staticmethod
def get_last_update_date() -> Dict[Symbol, datetime.date]:
   return QuantpediaSpinOffs._last_update_date
   
def GetSource(self, config: SubscriptionDataConfig, date: datetime, isLiveMode: bool) -> SubscriptionDataSource:
    return SubscriptionDataSource("data.quantpedia.com/backtesting_data/equity/{0}.csv".format(config.Symbol.Value), SubscriptionTransportMedium.RemoteFile, FileFormat.Csv)
def Reader(self, config: SubscriptionDataConfig, line: str, date: datetime, isLiveMode: bool) -> BaseData:
    data = QuantpediaSpinOffs()
    data.Symbol = config.Symbol
    
    if not line[0].isdigit(): return None
    split: str = line.split(';')
    
    data.Time = datetime.strptime(split[0], "%d.%m.%Y") + timedelta(days=1)
    data['tickers'] = split[1:]
    if config.Symbol not in QuantpediaSpinOffs._last_update_date:
        QuantpediaSpinOffs._last_update_date[config.Symbol] = datetime(1,1,1).date()
    if data.Time.date() > QuantpediaSpinOffs._last_update_date[config.Symbol]:
        QuantpediaSpinOffs._last_update_date[config.Symbol] = data.Time.date()
    return data
# custom fee model
class CustomFeeModel(FeeModel):
def GetOrderFee(self, parameters: OrderFeeParameters) -> OrderFee:
    fee: float = parameters.Security.Price * parameters.Order.AbsoluteQuantity * 0.00005
    return OrderFee(CashAmount(fee, "USD"))
