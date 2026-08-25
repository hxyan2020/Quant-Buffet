# Original QuantConnect / library Python
# locale=en slug="industry-herding-and-momentum"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

from AlgorithmImports import *
import numpy as np
from typing import List, Dict, Tuple
class IndustryHerdingandMomentum(QCAlgorithm):

def Initialize(self):
    self.SetStartDate(2003, 1, 1)
    self.SetCash(100000)
    self.period:int = 7 * 21
    self.leverage:int = 5
    self.min_share_price:int = 5
    self.min_stocks:int = 5
    # Daily price data.
    self.data:Dict[Symbol, SymbolData] = {}
    
    market:Symbol = self.AddEquity('SPY', Resolution.Daily).Symbol
    
    self.long:List[Symbol] = []
    self.short:List[Symbol] = []
    
    # Historical industry CSSD data.
    self.industry_CSSD:Dict[str, float] = {}
    self.cssd_period:int = 3    # Minimum cssd data period.
    
    self.fundamental_count:int = 1000
    self.fundamental_sorting_key = lambda x: x.DollarVolume
    self.selection_flag:bool = True
    self.Settings.MinimumOrderMarginPortfolioPercentage = 0.
    self.UniverseSettings.Resolution = Resolution.Daily
    self.AddUniverse(self.FundamentalSelectionFunction)
    self.Schedule.On(self.DateRules.MonthEnd(market), self.TimeRules.AfterMarketOpen(market), self.Selection)
    self.settings.daily_precise_end_time = False
def OnSecuritiesChanged(self, changes: SecurityChanges) -> None:
    for security in changes.AddedSecurities:
        security.SetFeeModel(CustomFeeModel())
        security.SetLeverage(self.leverage)
            
def FundamentalSelectionFunction(self, fundamental: List[Fundamental]) -> List[Symbol]:
    # Update the rolling window every day.
    for stock in fundamental:
        symbol:Symbol = stock.Symbol
        # Store monthly price.
        if symbol in self.data:
            self.data[symbol].update(stock.AdjustedPrice)
    if not self.selection_flag:
        return Universe.Unchanged
    selected:List[Fundamental] = [
        x for x in fundamental if x.HasFundamentalData and x.Market == 'usa' and x.Price >= self.min_share_price and x.MarketCap != 0
    ]
    if len(selected) > self.fundamental_count:
        selected = [x for x in sorted(selected, key=self.fundamental_sorting_key, reverse=True)[:self.fundamental_count]]
    industry_group:Dict[str, List[Symbol]] = {}
    # Warmup price rolling windows.
    for stock in selected:
        symbol:Symbol = stock.Symbol
        if symbol not in self.data:
            self.data[symbol] = SymbolData(self.period)
            history:DataFrame = self.History(symbol, self.period, Resolution.Daily)
            if history.empty:
                self.Log(f"Not enough data for {symbol} yet")
                continue
            closes:Series = history.loc[symbol].close
            for time, close in closes.items():
                self.data[symbol].update(close)
        if not self.data[symbol].is_ready():
            continue

        # Adding stocks in groups
        industry_group_code:str = stock.AssetClassification.MorningstarIndustryGroupCode
        
        if industry_group_code == 0: continue
        
        if not industry_group_code in industry_group:
            industry_group[industry_group_code] = []
        industry_group[industry_group_code].append(symbol)
    
    # CSSD calc.
    cssd_performance_data:Dict[str, Tuple[float]] = {}
    for group_code, group_symbols in industry_group.items():
        # Groups with at least 5 stocks, so CSSD is worth to calculate.
        if len(group_symbols) >= self.min_stocks:
            # Calculate CSSD.
            performance_1M:List[float] = []      # Last month's performance to calculate CSSD.
            performance_6M:List[float] = []      # 6M momentum.
            
            for symbol in group_symbols:
                performances:Tuple[float] = self.data[symbol].performances()
                performance_1M.append(performances[0]) # Last month performance
                performance_6M.append(performances[1]) # First six months performance
                    
            if len(performance_1M) >= self.min_stocks and len(performance_1M) == len(performance_6M):
                avg_return:float = np.mean(performance_1M)
                cssd:float = sqrt( ( sum([(x-avg_return)**2 for x in performance_1M]) / (len(performance_1M)-1) ) )
                
                if group_code not in self.industry_CSSD:
                    self.industry_CSSD[group_code] = []
                
                if len(self.industry_CSSD[group_code]) >= self.cssd_period:
                    normalized_cssd:float = (cssd - np.mean(self.industry_CSSD[group_code])) / np.std(self.industry_CSSD[group_code])
                    avg_momentum:float = np.mean(performance_6M)  # Group average momentum for last 6 months. (skipped last one)
                    
                    cssd_performance_data[group_code] = (normalized_cssd, avg_momentum)
                    
                self.industry_CSSD[group_code].append(cssd)
    
    if len(cssd_performance_data) != 0:
        sorted_by_cssd:List[Tuple[str, float]] = sorted(cssd_performance_data.items(), key = lambda x: x[1][0], reverse = True)
        count:int = int(len(sorted_by_cssd) * 0.3)
        low_herding:List[Tuple[str, float]] = [x for x in sorted_by_cssd[:count]]
        
        sorted_by_momentum:List[Tuple[str, float]] = sorted(low_herding, key = lambda x: x[1][1], reverse = True)
        count:int = int(len(sorted_by_momentum) * 0.5)
        long_groups:List[str] = [x[0] for x in sorted_by_momentum[:count]]
        short_groups:List[str] = [x[0] for x in sorted_by_momentum[-count:]]
        
        self.long:List[Symbol] = [symbol for x in long_groups for symbol in industry_group[x]]
        self.short:List[Symbol] = [symbol for x in short_groups for symbol in industry_group[x]]
    
    return self.long + self.short
                    
def Selection(self) -> None:
    self.selection_flag = True

def OnData(self, data: Slice) -> None:
    if not self.selection_flag:
        return
    self.selection_flag = False
    # Trade execution.
    targets:List[PortfolioTarget] = []
    for i, portfolio in enumerate([self.long, self.short]):
        for symbol in portfolio:
            if symbol in data and data[symbol]:
                targets.append(PortfolioTarget(symbol, ((-1) ** i) / len(portfolio)))
    
    self.SetHoldings(targets, True)
    
    self.long.clear()
    self.short.clear()
    
class SymbolData():
def __init__(self, period:int):
    self._monthly_closes:RollingWindow = RollingWindow[float](period)
    
def update(self, close:float) -> None:
    self._monthly_closes.Add(close)
    
def is_ready(self) -> bool:
    return self._monthly_closes.IsReady
    
def performances(self) -> Tuple[float]:
    monthly_closes:List[float] = list(self._monthly_closes)
    last_month:List[float] = monthly_closes[:21]
    first_six_months:List[float] = monthly_closes[21:]
    
    last_month_performance:float = last_month[0] / last_month[-1] - 1
    first_months_performance:float = first_six_months[0] / first_six_months[-1] - 1
    
    return (last_month_performance, first_months_performance)
    
# Custom fee model
class CustomFeeModel(FeeModel):
def GetOrderFee(self, parameters):
    fee = parameters.Security.Price * parameters.Order.AbsoluteQuantity * 0.00005
    return OrderFee(CashAmount(fee, "USD"))
