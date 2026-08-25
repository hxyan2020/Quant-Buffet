# Original QuantConnect / library Python
# locale=zh slug="股份发行效应"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

from AlgorithmImports import *
from math import isnan
class ShareIssuanceEffect(QCAlgorithm):
def Initialize(self):
    self.SetStartDate(2000, 1, 1)
    self.SetCash(100000)
    
    self.long:List[Symbol] = []
    self.short:List[Symbol] = []
    self.shares_number:Dict[Symbol, RollingWindow] = {}
    self.leverage:int = 5
    self.min_share_price:float = 5.
    
    market:Symbol = self.AddEquity('SPY', Resolution.Daily).Symbol
    
    self.fundamental_count:int = 500
    self.fundamental_sorting_key = lambda x: x.DollarVolume
    self.record_shares_flag = False
    self.record_shares_flag_month:int = 6
    self.selection_flag = False
    self.selection_flag_month:int = 11
    self.UniverseSettings.Resolution = Resolution.Daily
    self.AddUniverse(self.FundamentalSelectionFunction)
    self.Settings.MinimumOrderMarginPortfolioPercentage = 0.
    self.Schedule.On(self.DateRules.MonthEnd(market), self.TimeRules.BeforeMarketClose(market), self.Selection)
    self.settings.daily_precise_end_time = False
def OnSecuritiesChanged(self, changes: SecurityChanges) -> None:
    for security in changes.AddedSecurities:
        security.SetFeeModel(CustomFeeModel())
        security.SetLeverage(self.leverage)
    
def FundamentalSelectionFunction(self, fundamental: List[Fundamental]) -> List[Symbol]:
    if not self.selection_flag and not self.record_shares_flag:
        return Universe.Unchanged
    selected:List[Fundamental] = [
        x for x in fundamental if x.HasFundamentalData and x.Market == 'usa' and x.Price >= self.min_share_price and \
        not isnan(x.FinancialStatements.BalanceSheet.OrdinarySharesNumber.ThreeMonths) and x.FinancialStatements.BalanceSheet.OrdinarySharesNumber.ThreeMonths > 0
    ]
    
    if len(selected) > self.fundamental_count:
        selected = [x for x in sorted(selected, key=self.fundamental_sorting_key, reverse=True)[:self.fundamental_count]]
    if self.record_shares_flag:
        for stock in selected:
            symbol:Symbol = stock.Symbol
        
            if symbol not in self.shares_number:
                self.shares_number[symbol] = RollingWindow[float](2)
            
            shares_number:float = stock.FinancialStatements.BalanceSheet.OrdinarySharesNumber.ThreeMonths
            self.shares_number[symbol].Add(shares_number)
        
        # NOTE: Get rid of old shares number records so we work with latest values.
        del_symbols:List[Symbol] = []
        for symbol in self.shares_number:
            if symbol not in [x.Symbol for x in selected]:
                del_symbols.append(symbol)
        for symbol in del_symbols:
            del self.shares_number[symbol]
        
        self.record_shares_flag = False
        
    elif self.selection_flag:
        net_issuance:Dict[Symbol, float] = {}
        
        for stock in selected:
            symbol:Symbol = stock.Symbol
            
            if symbol in self.shares_number and self.shares_number[symbol].IsReady:
                shares_values:List[float] = list(self.shares_number[symbol])
                net_issuance[symbol] = shares_values[0] / shares_values[-1] - 1
            
        if len(net_issuance) != 0:
            zero_net_issuance:List[float] = [x[0] for x in net_issuance.items() if x[1] == 0]
            
            pos_net_issuance:List = [x for x in net_issuance.items() if x[1] > 0]
            sorted_pos_by_net_issuance:List = sorted(pos_net_issuance, key = lambda x: x[1], reverse = True)
            quantile:int = int(len(sorted_pos_by_net_issuance)/5)
            pos_high:List[Symbol] = [x[0] for x in sorted_pos_by_net_issuance[:quantile]]
            
            neg_net_issuance:List = [x for x in net_issuance.items() if x[1]  None:
    if not self.selection_flag:
        return
    self.selection_flag = False
    # Trade execution and rebalance
    targets:List[PortfolioTarget] = []
    for i, portfolio in enumerate([self.long, self.short]):
        for symbol in portfolio:
            if symbol in data and data[symbol]:
                targets.append(PortfolioTarget(symbol, ((-1) ** i) / len(portfolio)))
    
    self.SetHoldings(targets, True)
    self.long.clear()
    self.short.clear()

def Selection(self) -> None:
    if self.Time.month == self.record_shares_flag_month:
        self.record_shares_flag = True
    elif self.Time.month == self.selection_flag_month:
        self.selection_flag = True
# Custom fee model.
class CustomFeeModel(FeeModel):
def GetOrderFee(self, parameters):
    fee = parameters.Security.Price * parameters.Order.AbsoluteQuantity * 0.00005
    return OrderFee(CashAmount(fee, "USD"))
