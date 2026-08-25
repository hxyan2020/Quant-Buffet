# Original QuantConnect / library Python
# locale=zh slug="流动性增长因子"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

from AlgorithmImports import *
import pandas as pd
from collections import deque
import data_tools
#endregion
class LiquidityGrowthFactor(QCAlgorithm):
def Initialize(self):
    self.SetStartDate(2002, 1, 1)
    self.SetCash(100_000)
    
    market: Symbol = self.AddEquity("SPY", Resolution.Daily).Symbol
    
    self.fundamental_count: int = 1_000
    self.fundamental_sorting_key = lambda x: x.DollarVolume
    
    self.data: Dict[Symbol, data_tools.SymbolData] = {}
    self.weight: Dict[Symbol, float] = {}
    
    self.monthly_period: int = 12
    self.daily_period: int = 30
    self.volume_period: int = 21
    self.leverage: int = 5
    self.exchange_codes: List[str] = ['NYS', 'NAS', 'ASE']
    
    self.selection_flag: bool = False
    self.UniverseSettings.Resolution = Resolution.Daily
    self.AddUniverse(self.FundamentalSelectionFunction)
    self.Settings.MinimumOrderMarginPortfolioPercentage = 0.
    self.settings.daily_precise_end_time = False
    self.Schedule.On(self.DateRules.MonthEnd(market), self.TimeRules.AfterMarketOpen(market), self.Selection)

def OnSecuritiesChanged(self, changes: SecurityChanges) -> None:
    for security in changes.AddedSecurities:
        security.SetFeeModel(data_tools.CustomFeeModel())
        security.SetLeverage(self.leverage)
        
def FundamentalSelectionFunction(self, fundamental: List[Fundamental]) -> List[Symbol]:
    for stock in fundamental:
        symbol: Symbol = stock.Symbol
        if symbol in self.data:
            # store price and volume and dollar volume every day
            self.data[symbol].update_price(stock.AdjustedPrice)
            self.data[symbol].update_volume(stock.Volume)
            self.data[symbol].update_dollar_volume(stock.DollarVolume)
            if self.selection_flag and self.data[symbol].volume_is_ready() and self.data[symbol].price_is_ready():
                # store monthly liquidity
                liquidity: float = self.data[symbol].monthly_liquidity()
                if liquidity != 0:
                    self.data[symbol].update_liquidity(liquidity, self.Time)
    
    if not self.selection_flag:
        return Universe.Unchanged
        
    selected: List[Fundamental] = [
        f for f in fundamental if f.HasFundamentalData 
        and f.Market == 'usa'
        and f.SecurityReference.ExchangeId in self.exchange_codes
    ]
    
    if len(selected) > self.fundamental_count:
        selected = [x for x in sorted(selected, key=self.fundamental_sorting_key, reverse=True)[:self.fundamental_count]]
    liquidity: Dict[Symbol, float] = {}
    liquidity_growth: Dict[Symbol, float] = {}
    # warmup price rolling windows
    for stock in selected:
        symbol: Symbol = stock.Symbol
        if symbol not in self.data:
            self.data[symbol] = data_tools.SymbolData(self.monthly_period+1, self.monthly_period+1, self.volume_period)
            
            history: DataFrame = self.History(symbol, self.monthly_period*self.daily_period, Resolution.Daily)
            if history.empty:
                self.Log(f"Not enough data for {symbol} yet.")
                continue
            
            if 'close' in history and 'volume' in history:
                closes: Series = history.loc[symbol]['close']
                volumes: Series = history.loc[symbol]['volume']
                
                # find monthly closes and update rolling window
                closes_len: int = len(closes.keys())
                for index, time_close in enumerate(closes.items()):
                    # index out of bounds check
                    if index + 1 = min_stock_cnt and len(liquidity_growth) >= min_stock_cnt:
        sorted_by_liq = sorted(liquidity, key = liquidity.get, reverse = True)
        half: int = int(len(sorted_by_liq) / 2)
        liquid: List[Symbol] = sorted_by_liq[:half]
        iliquid: List[Symbol] = sorted_by_liq[-half:]
        
        percentile: int = int(len(liquid) * 0.3)
        liquid_by_growth: List[Symbol] = sorted(liquid, key = lambda x: liquidity_growth[x], reverse = True)
        high_liquid: List[Symbol] = liquid_by_growth[:percentile]
        low_liquid: List[Symbol] = liquid_by_growth[-percentile:]
        iliquid_by_growth: List[Symbol] = sorted(iliquid, key = lambda x: liquidity_growth[x], reverse = True)
        high_iliquid: List[Symbol] = iliquid_by_growth[:percentile]
        low_iliquid: List[Symbol] = iliquid_by_growth[-percentile:]
        
        long = high_liquid + high_iliquid
        short = low_liquid + low_iliquid
    
    # dollar volume weighting
    for i, portfolio in enumerate([long, short]):
        total_dollar_vol: float = sum([self.data[x].monthly_dollar_volume() for x in portfolio])
        for stock in portfolio:
            self.weight[symbol] = ((-1) ** i) * (self.data[symbol].monthly_dollar_volume() / total_dollar_vol)
    return list(self.weight.keys())
    
def OnData(self, slice: Slice) -> None:
    if not self.selection_flag:
        return
    self.selection_flag = False
    
    # trade execution
    portfolio: List[PortfolioTarget] = [
        PortfolioTarget(symbol, w) for symbol, w in self.weight.items() if slice.contains_key(symbol) and slice[symbol]
    ]
    
    self.SetHoldings(portfolio, True)
    self.weight.clear()
    
def Selection(self):
    self.selection_flag = True
