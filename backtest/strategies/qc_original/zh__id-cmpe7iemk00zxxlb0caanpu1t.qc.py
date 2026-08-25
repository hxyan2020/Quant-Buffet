# Original QuantConnect / library Python
# locale=zh slug="抄底坠刀股票策略"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

from AlgorithmImports import *
from typing import List, Dict
import numpy as np
from numpy import isnan
class CatchingFallingKnifeStocks(QCAlgorithm):
def Initialize(self):
    self.SetStartDate(2000, 1, 1)
    self.SetCash(100000)
    self.fundamental_sorting_key = lambda x: x.MarketCap
    self.fundamental_count:int = 3000
    self.period:int = 500
    
    self.long:List[Symbol] = []
    # Daily data
    self.data:Dict[Symbol, SymbolData] = {}
    self.min_share_price:int = 5
    self.leverage:int = 3
    
    self.symbol:Symbol = self.AddEquity('SPY', Resolution.Daily).Symbol
    if self.symbol not in self.data:
        self.data[self.symbol] = SymbolData(self.symbol, self.period)
        history:DataFrame = self.History(self.symbol, self.period, Resolution.Daily)
        if history.empty:
            self.Log(f"Note enough data for {symbol} yet")
        else:
            closes:Series = history.loc[self.symbol].close[:-1]
            for time, close in closes.items():
                self.data[self.symbol].update(close)
    
    self.last_month:int = -1
    self.selection_flag:bool = True
    self.settings.daily_precise_end_time = False
    self.settings.minimum_order_margin_portfolio_percentage = 0.
    self.UniverseSettings.Resolution = Resolution.Daily
    self.AddUniverse(self.FundamentalSelectionFunction)
    self.market: Symbol = self.AddEquity('SPY', Resolution.Daily).Symbol
    self.schedule.on(self.date_rules.month_start(self.market),
                    self.time_rules.after_market_open(self.market),
                    self.selection)
    
def OnSecuritiesChanged(self, changes: SecurityChanges) -> None:
    for security in changes.AddedSecurities:
        security.SetFeeModel(CustomFeeModel())
        security.SetLeverage(self.leverage)
def FundamentalSelectionFunction(self, fundamental: List[Fundamental]) -> List[Symbol]:
    for stock in fundamental:
        symbol:Symbol = stock.Symbol
        
        # Store daily price.
        if symbol in self.data:
            self.data[symbol].update(stock.AdjustedPrice)
    if not self.selection_flag:
        return Universe.Unchanged
    selected:List[Fundamental] = [
        x for x in fundamental if x.HasFundamentalData and x.Market == 'usa' and x.Price > self.min_share_price and x.MarketCap != 0 \
        and not isnan(x.OperationRatios.TotalDebtEquityRatio.ThreeMonths) and x.OperationRatios.TotalDebtEquityRatio.ThreeMonths > 0 \
        and not isnan(x.AssetClassification.MorningstarIndustryGroupCode) and x.AssetClassification.MorningstarIndustryGroupCode != 0
    ]
    
    if len(selected) > self.fundamental_count:
        selected = [x for x in sorted(selected, key=self.fundamental_sorting_key, reverse=True)[:self.fundamental_count]]
    group:Dict[str, List[Symbol]] = {}
    # Warmup price rolling windows.
    for stock in selected:
        symbol:Symbol = stock.Symbol
        if symbol not in self.data:
            self.data[symbol] = SymbolData(symbol, self.period)
            history = self.History(symbol, self.period, Resolution.Daily)
            if history.empty:
                self.Log(f"Not enough data for {symbol} yet")
                continue
            closes = history.loc[symbol].close
            for time, close in closes.items():
                self.data[symbol].update(close)
        if not self.data[symbol].is_ready():
            continue
        industry_group_code = stock.AssetClassification.MorningstarIndustryGroupCode
        # Debt to equity ratio.
        debt_to_equity = stock.OperationRatios.TotalDebtEquityRatio.ThreeMonths
        self.data[symbol]._debt_to_equity = debt_to_equity
        
        # Adding stocks in groups
        if not industry_group_code in group:
            group[industry_group_code] = []
        
        group[industry_group_code].append(self.data[symbol])
    
    if self.symbol in self.data and self.data[self.symbol].is_ready():
        spy_ret:float = self.data[self.symbol].performance()
                
        for industry_code in group:
            industry_debt_to_equity_10th_percentile:float = np.percentile([symbol_data._debt_to_equity for symbol_data in group[industry_code]], 10)
                
            # Stocks that suffered losses of 50 percent or more than s&p
            # and
            # stocks that have a Debt/Equity ratio within at least 10% of the lowest in the industry
            long:List[Symbol] = [symbol_data._symbol for symbol_data in group[industry_code] if symbol_data.performance()  None:
    if not self.selection_flag: 
        return
    self.selection_flag = False
    
    # Trade execution.        
    targets:List[PortfolioTarget] = []
    for symbol in self.long:
        if symbol in data and data[symbol]:
            targets.append(PortfolioTarget(symbol, 1 / len(self.long)))
    
    self.SetHoldings(targets, True)
    self.long.clear()
def selection(self) -> None:
    self.selection_flag = True
class SymbolData():
def __init__(self, symbol:Symbol, period:int) -> None:
    self._symbol:Symbol = symbol
    self._price:RollingWindow = RollingWindow[float](period)
    self._debt_to_equity:float = 0.

def is_ready(self) -> bool:
    return self._price.IsReady

def update(self, close:float) -> None:
    self._price.Add(close)
    
def performance(self) -> float:
    return (self._price[0] / self._price[self._price.Count - 1] - 1)
# Custom fee model.
class CustomFeeModel(FeeModel):
def GetOrderFee(self, parameters):
    fee = parameters.Security.Price * parameters.Order.AbsoluteQuantity * 0.00005
    return OrderFee(CashAmount(fee, "USD"))
