# Original QuantConnect / library Python
# locale=en slug="股票中的内部交易效应"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

from AlgorithmImports import *
from typing import List, Dict, Tuple
from collections import deque
#endregion
class InsidersTradingEffectInStocks(QCAlgorithm):
def Initialize(self) -> None:
    self.SetStartDate(2020, 1, 1)
    self.SetCash(1_000_000)
    self.exchange_codes:List[str] = ['NYS', 'NAS', 'ASE']
    self.leverage:int = 10
    self.quantile:int = 10
    self.min_share_price:int = 2
    self.period:int = 6
    self.selection_month:int = 5
    self.months_to_collect_data:List[int] = [11, 12, 1, 2, 3, 4]
    self.insider_data:Dict[str, Tuple[str, float, float]] = {}
    self.last_shares_owned:Dict[str, deque(float, float)] = {}
    self.insider_buys:Dict[str, List[float]] = {}
    self.insider_sells:Dict[str, List[float]] = {}
    self.long:List[Symbol] = []
    self.short:List[Symbol] = []
    self.selection_flag:bool = False
    self.Settings.MinimumOrderMarginPortfolioPercentage = 0.
    self.UniverseSettings.Resolution = Resolution.Daily
    self.AddUniverse(self.FundamentalSelectionFunction)
    self.recent_month:int = -1
    self.settings.daily_precise_end_time = False
def OnSecuritiesChanged(self, changes:SecurityChanges) -> None:
    for security in changes.AddedSecurities:
        security.SetFeeModel(CustomFeeModel())
        security.SetLeverage(self.leverage)
        symbol:Symbol = security.Symbol
        dataset_symbol:Symbol = self.AddData(QuiverInsiderTrading, symbol).Symbol
def FundamentalSelectionFunction(self, fundamental: List[Fundamental]) -> List[Symbol]:
    # selection in beginning of May
    if self.Time.month == self.recent_month:
        return Universe.Unchanged
    self.recent_month = self.Time.month
    if self.Time.month != self.selection_month:
        return Universe.Unchanged
    self.selection_flag = True
    selected:List[Symbol] = [x for x in fundamental if x.HasFundamentalData and x.Price > self.min_share_price and x.MarketCap != 0 
                         and x.SecurityReference.ExchangeId in self.exchange_codes and not x.CompanyReference.IsREIT]
    net_purchase_ratio:Dict[Symbol, float] = {}
    for stock in selected:
        symbol:Symbol = stock.Symbol
        ticker:str = symbol.Value
        if ticker in set(list(self.insider_buys.keys()) + list(self.insider_sells.keys())):
            total_buys:float = self.insider_buys.get(ticker, [0])
            total_sells:float = self.insider_sells.get(ticker, [0])
            net_purchase_ratio_calculation:float = (len(total_buys) - len(total_sells)) / len(total_buys + total_sells)
            if net_purchase_ratio_calculation != 0:
                net_purchase_ratio[symbol] = net_purchase_ratio_calculation
    self.insider_buys.clear()
    self.insider_sells.clear()
    if len(net_purchase_ratio) >= self.quantile:
        sorted_ratio:List[Symbol] = sorted(net_purchase_ratio, key=net_purchase_ratio.get)
        quantile:int = len(sorted_ratio) // self.quantile
        self.long = sorted_ratio[-quantile:]
        self.short = sorted_ratio[:quantile]
    
    return list(map(lambda x:x.Symbol, selected))
def OnData(self, data:Slice) -> None:
    # store data of insider trades and calculate if trade was bought/sold
    for insider_trades in data.Get(QuiverInsiderTrading).values():
        for insider_trade in insider_trades:
            insider_name:str = insider_trade.Name
            stock_ticker:str = insider_trade.Symbol.Value
            
            if insider_name not in self.insider_data:
                self.insider_data[insider_name] = deque(maxlen=2)
            
            if insider_trade.SharesOwnedFollowing is not None:      
                self.insider_data[insider_name].append((stock_ticker, insider_trade.SharesOwnedFollowing, insider_trade.Shares))
            
            if len(self.insider_data[insider_name]) == self.insider_data[insider_name].maxlen and self.Time.month in self.months_to_collect_data:
                if self.insider_data[insider_name][0][1]  self.insider_data[insider_name][-1][1]:
                    if stock_ticker not in self.insider_sells:
                        self.insider_sells[stock_ticker] = []
                    self.insider_sells[stock_ticker].append(self.insider_data[insider_name][-1][2])
    # yearly rebalance
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
# Custom fee model
class CustomFeeModel(FeeModel):
def GetOrderFee(self, parameters):
    fee = parameters.Security.Price * parameters.Order.AbsoluteQuantity * 0.00005
    return OrderFee(CashAmount(fee, "USD"))
