# Original QuantConnect / library Python
# locale=en slug="the-halloween-effect-within-long-term-reversal"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

from AlgorithmImports import *
# endregion

class TheHalloweenEffectWithinLongtermReversal(QCAlgorithm):

def Initialize(self):
    self.SetStartDate(2000, 1, 1)
    self.SetCash(100000)

    self.quantile:int = 6
    self.liquidate_month:int = 4
    self.trading_months:List[int] = [10, 11, 12, 1, 2, 3]
    self.period:int = 60 * 21 # need five years of daily data
    self.leverage:int = 3
    
    self.prices:Dict[Symbol, RollingWindow] = {}
    self.weight:Dict[Symbol, float] = {}

    self.symbol:Symbol = self.AddEquity('SPY', Resolution.Daily).Symbol

    self.fundamental_count:int = 3000
    self.fundamental_sorting_key = lambda x: x.MarketCap

    self.selection_flag:bool = False
    self.UniverseSettings.Resolution = Resolution.Daily
    self.AddUniverse(self.FundamentalSelectionFunction)
    self.Settings.MinimumOrderMarginPortfolioPercentage = 0
    self.Schedule.On(self.DateRules.MonthEnd(self.symbol), self.TimeRules.BeforeMarketClose(self.symbol, 0), self.Selection)

def OnSecuritiesChanged(self, changes: SecurityChanges) -> None:
    for security in changes.AddedSecurities:
        security.SetFeeModel(CustomFeeModel())
        security.SetLeverage(self.leverage)

def FundamentalSelectionFunction(self, fundamental: List[Fundamental]) -> None:
    # update prices on daily basis
    for stock in fundamental:
        symbol:Symbol = stock.Symbol

        if symbol in self.prices:
            self.prices[symbol].Add(stock.AdjustedPrice)

    if not self.selection_flag:
        return Universe.Unchanged

    selected:List[Fundamental] = [x for x in fundamental if x.HasFundamentalData and x.Market == 'usa' and x.MarketCap != 0 and \
        ((x.SecurityReference.ExchangeId == "NYS") or (x.SecurityReference.ExchangeId == "NAS") or (x.SecurityReference.ExchangeId == "ASE"))
    ]

    if len(selected) > self.fundamental_count:
        selected = [x for x in sorted(selected, key=self.fundamental_sorting_key, reverse=True)[:self.fundamental_count]]
    
    performance:Dict[Fundamental, float] = {}

    # warm up stock prices
    for stock in selected:
        symbol:Symbol = stock.Symbol
        
        if symbol not in self.prices:
            self.prices[symbol] = RollingWindow[float](self.period)
            history = self.History(symbol, self.period, Resolution.Daily)
            if history.empty:
                continue

            closes:List = history.loc[symbol].close

            for time, close in closes.items():
                self.prices[symbol].Add(close)
            
        if self.prices[symbol].IsReady:
            performance[stock] = self.prices[symbol][0] / self.prices[symbol][self.period - 1] - 1

    if len(performance)  None:
    # rebalance monthly
    if not self.selection_flag:
        return
    self.selection_flag = False
    
    # trade execution
    portfolio:List[PortfolioTarget] = [PortfolioTarget(symbol, w) for symbol, w in self.weight.items() if symbol in data and data[symbol]]
    self.SetHoldings(portfolio, True)

    self.weight.clear()
    
def Selection(self) -> None:
    if self.Time.month in self.trading_months:
        self.selection_flag = True
    elif self.Time.month == self.liquidate_month:
        # liquidate portfolio at the end of the April
        self.Liquidate()
    
# Custom fee model
class CustomFeeModel(FeeModel):
def GetOrderFee(self, parameters):
    fee = parameters.Security.Price * parameters.Order.AbsoluteQuantity * 0.00005
    return OrderFee(CashAmount(fee, "USD"))
