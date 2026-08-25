# Original QuantConnect / library Python
# locale=en slug="the-impact-of-turnovers-on-short-term-momentum-and-reversal"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

from AlgorithmImports import *
from typing import List, Dict, Tuple
from numpy import isnan
class TheImpactTurnoversShortTermMomentumReversal(QCAlgorithm):
def Initialize(self):
    self.SetStartDate(2000, 1, 1)  
    self.SetCash(100000) 
    self.exchange_codes:List[str] = ['NYS', 'NAS', 'ASE']
    market:Symbol = self.AddEquity('SPY', Resolution.Daily).Symbol
    
    self.leverage:int = 10
    self.quantile:int = 5
    self.share_min_price:int = 5
    self.period:int = 21
    self.fundamental_count:int = 500
    self.fundamental_sorting_key = lambda x: x.MarketCap
    
    # Price and volume daily data.
    self.data:Dict[Symbol, SymbolData] = {}
    self.weight:Dict[Symbol, float] = {}
    
    self.selection_flag:bool = False
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
            self.data[symbol].update(stock.AdjustedPrice, stock.Volume)
    if not self.selection_flag:
        return Universe.Unchanged
    # selected = [x.Symbol for x in fundamental if x.HasFundamentalData and x.Market == 'usa']
    selected:List[Fundamental] = [
        x for x in fundamental if x.HasFundamentalData and x.Price > self.share_min_price and x.Market == 'usa' and x.MarketCap != 0 \
        and not isnan(x.EarningReports.BasicAverageShares.ThreeMonths) and x.EarningReports.BasicAverageShares.ThreeMonths > 0 \
        and x.SecurityReference.ExchangeId in self.exchange_codes
    ]
        
    if len(selected) > self.fundamental_count:
        selected = [x for x in sorted(selected, key=self.fundamental_sorting_key, reverse=True)[:self.fundamental_count]]
    # Warmup price rolling windows.
    for stock in selected:
        symbol:Symbol = stock.Symbol
        if symbol in self.data:
            continue
        self.data[symbol] = SymbolData(self.period)
        history = self.History(symbol, self.period, Resolution.Daily)
        if history.empty:
            self.Log(f"Not enough data for {symbol} yet")
            continue
        if 'close' in history and 'volume' in history:
            closes:DataFrame = history.loc[symbol].close
            volumes:Series = history.loc[symbol].volume
            for (_, close), (_, volume) in zip(closes.items(), volumes.items()):
                self.data[symbol].update(close, volume)
    performance_turnover_market_cap:Dict[Symbol, Tuple[float]] = {}
    
    for stock in selected:
        symbol:Symbol = stock.Symbol
        if not self.data[symbol].is_ready():
            continue
        # Return calc.
        perf:float = self.data[symbol].performance()
        
        # Turnover calc.
        monthly_volume:float = self.data[symbol].monthly_volume()
        shares_outstanding:float = stock.EarningReports.BasicAverageShares.ThreeMonths
        turnover:float = monthly_volume / shares_outstanding
        # Market cap calc.
        market_cap:float = stock.MarketCap
            
        performance_turnover_market_cap[symbol] = (perf, turnover, market_cap)
            
    if len(performance_turnover_market_cap) != 0:
        # Return sorting.
        sorted_by_ret:List[Tuple[Symbol, Tuple[float]]] = sorted(performance_turnover_market_cap.items(), key = lambda x: x[1][0], reverse = True)
        quintile:int = int(len(sorted_by_ret) / self.quantile)
        
        high_ret:List[Tuple[Symbol, Tuple[float]]] = [x for x in sorted_by_ret[:quintile]]
        low_ret:List[Tuple[Symbol, Tuple[float]]] = [x for x in sorted_by_ret[-quintile:]]
        
        # Turnover sorting.
        sorted_by_turnover:List[Tuple[Symbol, Tuple[float]]] = sorted(performance_turnover_market_cap.items(), key = lambda x: x[1][1], reverse = True)
        high_turnover:List[Tuple[Symbol, Tuple[float]]] = [x for x in sorted_by_turnover[:quintile]]
        low_turnover:List[Tuple[Symbol, Tuple[float]]] = [x for x in sorted_by_turnover[-quintile:]]
        
        # Forming portfolios.
        long_first_portfolio:List[Tuple[Symbol, Tuple[float]]] = [x for x in low_ret if x in low_turnover]
        short_first_portfolio:List[Tuple[Symbol, Tuple[float]]] = [x for x in high_ret if x in low_turnover]

        long_second_portfolio:List[Tuple[Symbol, Tuple[float]]] = [x for x in high_ret if x in high_turnover]
        short_second_portfolio:List[Tuple[Symbol, Tuple[float]]] = [x for x in low_ret if x in high_turnover]
        
        # calculate weights
        for portfolio_lst in [[long_first_portfolio, short_first_portfolio], [long_second_portfolio, short_second_portfolio]]:
            for i, portfolio in enumerate(portfolio_lst):
                mc_sum:float = sum(list(map(lambda x: x[1][2], portfolio)))
                for symbol, perf_turnover_cap in portfolio:
                    self.weight[symbol] = (((-1)**i) * 0.5) * perf_turnover_cap[2] / mc_sum
    
    return [x[0] for x in self.weight.items()]

def OnData(self, data: Slice):
    if not self.selection_flag:
        return
    self.selection_flag = False
    
    # Trade execution.
    portfolio:List[PortfolioTarget] = [PortfolioTarget(symbol, w) for symbol, w in self.weight.items() if symbol in data and data[symbol]]
    self.SetHoldings(portfolio, True)
    
    self.weight.clear()
    
def Selection(self):
    self.selection_flag = True
    
class SymbolData():
def __init__(self, period:int):
    self.Closes:RollingWindow = RollingWindow[float](period)
    self.Volumes:RollingWindow = RollingWindow[float](period)
        
def update(self, close:float, volume:float):
    self.Closes.Add(close)
    self.Volumes.Add(volume)
        
def is_ready(self) -> bool:
    return self.Closes.IsReady and self.Volumes.IsReady
    
def performance(self) -> float:
    closes:List[float] = [x for x in self.Closes]
    return closes[0] / closes[-1] - 1 # Performance
    
def monthly_volume(self) -> float:
    volumes:List[float] = [x for x in self.Volumes]
    return sum(volumes)
    
    
class CustomFeeModel(FeeModel):
def GetOrderFee(self, parameters):
    fee = parameters.Security.Price * parameters.Order.AbsoluteQuantity * 0.00005
    return OrderFee(CashAmount(fee, "USD"))
