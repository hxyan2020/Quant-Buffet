# Original QuantConnect / library Python
# locale=zh slug="投资-动量策略"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

from AlgorithmImports import *
from pandas.core.frame import DataFrame
from numpy import isnan
class InvestmentMomentumStrategy(QCAlgorithm):
def Initialize(self):
    self.SetStartDate(2000, 1, 1)
    self.SetCash(100000)
    
    self.SetSecurityInitializer(lambda x: x.SetMarketPrice(self.GetLastKnownPrice(x)))
    market:Symbol = self.AddEquity("SPY", Resolution.Daily).Symbol
    
    self.long:List[Symbol] = []
    self.short:List[Symbol] = []
    
    self.data:Dict[Symbol, SymbolData] = {}
    self.period:int = 6 * 21
    self.leverage:int = 5
    self.quantile:int = 5
    
    self.fundamental_count:int = 500
    self.fundamental_sorting_key = lambda x: x.DollarVolume
    self.months:int = 0
    self.selection_flag = True
    self.UniverseSettings.Resolution = Resolution.Daily
    self.Settings.MinimumOrderMarginPortfolioPercentage = 0.
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
            self.data[symbol].update_price(stock.AdjustedPrice)
    if not self.selection_flag:
        return Universe.Unchanged
    selected:List[Fundamental] = [x for x in fundamental if x.HasFundamentalData and x.Market == 'usa' and \
        not isnan(x.FinancialStatements.BalanceSheet.GrossPPE.TwelveMonths) and x.FinancialStatements.BalanceSheet.GrossPPE.TwelveMonths != 0 and \
        not isnan(x.FinancialStatements.BalanceSheet.Inventory.TwelveMonths) and x.FinancialStatements.BalanceSheet.Inventory.TwelveMonths != 0 and \
        not isnan(x.FinancialStatements.BalanceSheet.TangibleBookValue.ThreeMonths) and x.FinancialStatements.BalanceSheet.TangibleBookValue.ThreeMonths != 0
    ]
    if len(selected) > self.fundamental_count:
        selected = [x for x in sorted(selected, key=self.fundamental_sorting_key, reverse=True)[:self.fundamental_count]]
    
    selected_symbols:List[Symbol] = [x.Symbol for x in selected]
    
    momentum:Dict[Symbol, float] = {} 
    ia_ratio:Dict[Symbol, float] = {}
    # Warmup price rolling windows.
    for stock in selected:
        symbol:Symbol = stock.Symbol
        if symbol not in self.data:
            self.data[symbol] = SymbolData(self.period)
            history:DataFrame = self.History(symbol, self.period, Resolution.Daily)
            if history.empty:
                self.Log(f"Not enough data for {symbol} yet.")
                continue
            closes:pd.Series = history.loc[symbol].close
            for time, close in closes.items():
                self.data[symbol].update_price(close)
        
        if self.data[symbol].is_ready():
            momentum[symbol] = self.data[symbol].performance()
        
            ppe:float = stock.FinancialStatements.BalanceSheet.GrossPPE.TwelveMonths
            inv:float = stock.FinancialStatements.BalanceSheet.Inventory.TwelveMonths
            book_value:float = stock.FinancialStatements.BalanceSheet.TangibleBookValue.ThreeMonths
        
            if self.data[symbol]._inventory == 0 or self.data[symbol]._PPE == 0 or self.data[symbol]._book_value == 0:
                self.data[symbol].update_data(ppe, inv, book_value)
                continue
        
            ppe_change:float = ppe - self.data[symbol]._PPE
            inv_change:float = inv - self.data[symbol]._inventory
        
            # IA calc
            ia_ratio[symbol] = (ppe_change + inv_change) / book_value
            self.data[symbol].update_data(ppe, inv, book_value)
    
    # Reset not updated symbols.
    for symbol in self.data:
        if symbol not in selected_symbols:
            self.data[symbol].update_data(0,0,0)
    
    if len(momentum) >= self.quantile:
        # Momentum sorting
        sorted_by_mom:List[Symbol] = sorted(momentum, key = momentum.get, reverse = True)
        quantile:int = int(len(sorted_by_mom) / self.quantile)
        high_by_mom:List[Symbol] = sorted_by_mom[:quantile]
        low_by_mom:List[Symbol] = sorted_by_mom[-quantile:]
        # IA sorting
        sorted_by_ia:List[Symbol] = sorted(ia_ratio, key = ia_ratio.get, reverse = True)
        quantile = int(len(sorted_by_ia) / self.quantile)
        high_by_ia:List[Symbol] = sorted_by_ia[:quantile]
        low_by_ia:List[Symbol] = sorted_by_ia[-quantile:]
        
        self.long = [x for x in high_by_mom if x in low_by_ia]
        self.short = [x for x in low_by_mom if x in high_by_ia]
    
    return self.long + self.short
    
def OnData(self, data: Slice) -> None:
    if not self.selection_flag:
        return
    self.selection_flag = False
    # order execution
    targets:List[PortfolioTarget] = []
    for i, portfolio in enumerate([self.long, self.short]):
        for symbol in portfolio:
            if symbol in data and data[symbol]:
                targets.append(PortfolioTarget(symbol, ((-1) ** i) / len(portfolio)))
    
    self.SetHoldings(targets, True)
    self.long.clear()
    self.short.clear()
        
def Selection(self) -> None:
    if self.months == 0 or self.months == 5:
        self.selection_flag = True
        
    self.months += 1
    if self.months == 6:
        self.months = 0
class SymbolData():
def __init__(self, period:int):
    self._price:RollingWindow = RollingWindow[float](period)
    self._PPE:float = 0.
    self._inventory:float = 0.
    self._book_value:float = 0.
    
def update_data(self, ppe:float, inv:float, book_value:float) -> None:
    self._PPE = ppe
    self._inventory = inv
    self._book_value = book_value
    
def update_price(self, price:float) -> None:
    self._price.Add(price)

def is_ready(self) -> bool:
    return self._price.IsReady
    
def performance(self, values_to_skip = 0) -> float:
    return self._price[values_to_skip] / self._price[self._price.Count - 1] - 1
# Custom fee model.
class CustomFeeModel(FeeModel):
def GetOrderFee(self, parameters):
    fee = parameters.Security.Price * parameters.Order.AbsoluteQuantity * 0.00005
    return OrderFee(CashAmount(fee, "USD"))
