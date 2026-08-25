# Original QuantConnect / library Python
# locale=zh slug="股票与信用违约掉期（cds）动量组合"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

from AlgorithmImports import *
import data_tools
from typing import List, Dict
#endregion
class CombinedStockandCDSMomentum(QCAlgorithm):
def Initialize(self) -> None:
    self.SetStartDate(2005, 1, 1)
    self.SetCash(100_000)
    self.stock_period: int = 12 * 21
    self.cds_period: int = 4 * 21
    self.quantile: int = 5
    self.leverage: int = 5
    
    market: Symbol = self.AddEquity('SPY', Resolution.Daily).Symbol
    self.cds: Symbol = self.AddData(data_tools.EquityCDS5Y, 'CDS', Resolution.Daily).Symbol
    
    # data yet to be initialized
    self.tickers: List[str] = []       # CDS universe tickers
    self.data: Dict[str, data_tools.SymbolData] = {}         # equity symbol data
    
    self.quantity: Dict[Symbol, float] = {}      # traded monthly quantity
    self.weight: Dict[Symbol, float] = {}
    
    self.selection_flag: bool = False
    self.UniverseSettings.Leverage = self.leverage
    self.UniverseSettings.Resolution = Resolution.Daily
    self.AddUniverse(self.FundamentalSelectionFunction)
    self.settings.daily_precise_end_time = False
    self.Settings.MinimumOrderMarginPortfolioPercentage = 0.
    self.Schedule.On(self.DateRules.MonthStart(market), self.TimeRules.AfterMarketOpen(market), self.Selection)
def OnSecuritiesChanged(self, changes: SecurityChanges) -> None:
    for security in changes.AddedSecurities:
        security.SetFeeModel(data_tools.CustomFeeModel())
def FundamentalSelectionFunction(self, fundamental: List[Fundamental]) -> List[Symbol]:
    # Update the rolling window every day.
    if self.Securities.ContainsKey(self.cds):
        cds_data = self.Securities[self.cds].GetLastData()        
        if cds_data:
            # data has not been initialized yet
            if len(self.data) == 0:
                self.tickers = list([x.upper() for x in cds_data.GetStorageDictionary().Keys])
                self.data = { x : data_tools.SymbolData(self.stock_period, self.cds_period) for x in self.tickers }
            
            for stock in fundamental:
                ticker: str = stock.Symbol.Value

                # Store daily price and cds.
                if ticker in self.data:
                    cds_price: float = cds_data[ticker]
                    self.data[ticker].update(stock.AdjustedPrice, cds_price)
    
    if not self.selection_flag:
        return Universe.Unchanged
    
    # cds data probably ended
    custom_data_last_update_date: datetime.date = data_tools.EquityCDS5Y.get_last_update_date()
    if self.Securities[self.cds].GetLastData() and self.Time.date() > custom_data_last_update_date:
        return Universe.UNCHANGED
    selected: List[Fundamental] = [x for x in fundamental if x.HasFundamentalData and x.Symbol.Value in self.tickers]
    market_cap: Dict[Symbol, float] = {}
    price_momentum: Dict[Symbol, float] = {}
    cds_momentum: Dict[Symbol, float] = {}
    
    for stock in selected:
        symbol: Symbol = stock.Symbol
        ticker: str = symbol.Value
        if not self.data[ticker].is_ready():
            continue
        if stock.MarketCap == 0:
            continue
        market_cap[symbol] = stock.MarketCap
        price_momentum[symbol] = self.data[ticker].price_momentum()
        cds_momentum[symbol] = self.data[ticker].cds_momentum()
    
    if len(price_momentum) > self.quantile:
        sorted_by_price_momentum: List[Symbol] = [x[0] for x in sorted(price_momentum.items(), key=lambda item:item[1], reverse=True)]
        quantile: int = int(len(sorted_by_price_momentum) / self.quantile)
        top_by_momentum: List[Symbol] = sorted_by_price_momentum[:quantile]
        bottom_by_momentum: List[Symbol] = sorted_by_price_momentum[-quantile:]
        sorted_by_cds_momentum: List[Symbol] = [x[0] for x in sorted(cds_momentum.items(), key=lambda item:item[1], reverse=True)]
        quantile: int = int(len(sorted_by_cds_momentum) / self.quantile)
        top_by_cds_momentum: List[Symbol] = sorted_by_cds_momentum[:quantile]
        bottom_by_cds_momentum: List[Symbol] = sorted_by_cds_momentum[-quantile:]
        
        # Joint momentum
        joint_long: List[Symbol] = [x for x in top_by_momentum if x in top_by_cds_momentum]
        joint_short: List[Symbol] = [x for x in bottom_by_momentum if x in bottom_by_cds_momentum]
        
        # Contrarian strategy
        contrarian_long: List[Symbol] = [x for x in bottom_by_momentum if x in top_by_cds_momentum]
        contrarian_short: List[Symbol] = [x for x in top_by_momentum if x in bottom_by_cds_momentum]
        
        # Strategy weighting
        portfolio_weight: float = 0.5 # two-strategy portfolio adjustment
        for i, portfolio in enumerate([[joint_long, contrarian_long], [joint_short, contrarian_short]]):
            for subportfolio in portfolio:
                mc_sum: float = sum(list(map(lambda x: market_cap[x], subportfolio)))
                for symbol in subportfolio:
                    w: float = ((-1)**i) * (market_cap[symbol] / mc_sum) * portfolio_weight
                    q: float = (self.Portfolio.TotalPortfolioValue * w) / self.data[symbol.Value].price[0]
                    self.quantity[symbol] = q
        
    return list(self.quantity.keys())

def OnData(self, slice: Slice) -> None:
    if not self.selection_flag: 
        return
    self.selection_flag = False
    self.Liquidate()
            
    for symbol, q in self.quantity.items():
        if slice.contains_key(symbol) and slice[symbol]:
            self.MarketOrder(symbol, q)
    
    self.quantity.clear()
    
def Selection(self) -> None:
    self.selection_flag = True
