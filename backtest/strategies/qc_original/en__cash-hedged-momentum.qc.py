# Original QuantConnect / library Python
# locale=en slug="cash-hedged-momentum"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

from AlgorithmImports import *
from pandas.core.frame import DataFrame
# endregion

class CashHedgedMomentum(QCAlgorithm):

def Initialize(self):
    self.SetStartDate(2000, 1, 1)
    self.SetCash(100000)
    
    self.weight:dict[Symbol, float] = {}
    self.price_data:dict[Symbol, RollingWindow] = {}
    self.period:int = 12 * 21

    self.market:Symbol = self.AddEquity('SPY', Resolution.Daily).Symbol
    self.momentum_quantile:int = 10
    self.cash_hedged_quantile:int = 25

    self.percentage_traded:float = .9
    self.min_share_price:float = 1.

    self.fundamental_count:int = 3000
    self.fundamental_sorting_key = lambda x: x.MarketCap

    self.selection_flag:bool = False
    self.UniverseSettings.Resolution = Resolution.Daily
    self.AddUniverse(self.FundamentalSelectionFunction)
    self.Settings.MinimumOrderMarginPortfolioPercentage = 0.
    self.Schedule.On(self.DateRules.MonthStart(self.market), self.TimeRules.BeforeMarketClose(self.market, 0), self.Selection)

def OnSecuritiesChanged(self, changes: SecurityChanges) -> None:
    for security in changes.AddedSecurities:
        security.SetFeeModel(CustomFeeModel())

def FundamentalSelectionFunction(self, fundamental: List[Fundamental]) -> List[Symbol]:
    # update the rolling window
    for stock in fundamental:
        symbol = stock.Symbol

        # Store monthly price.
        if symbol in self.price_data:
            self.price_data[symbol].Add(stock.AdjustedPrice)

    if not self.selection_flag:
        return Universe.Unchanged
    
    selected:List[Fundamental] = sorted([x for x in fundamental if x.HasFundamentalData and x.Market == 'usa' and x.MarketCap != 0 and x.AdjustedPrice >= self.min_share_price and \
            ((x.SecurityReference.ExchangeId == "NYS") or (x.SecurityReference.ExchangeId == "NAS") or (x.SecurityReference.ExchangeId == "ASE")) and \
            x.FinancialStatements.BalanceSheet.CashAndCashEquivalents.ThreeMonths != 0 and not np.isnan(x.FinancialStatements.BalanceSheet.CashAndCashEquivalents.ThreeMonths) and \
            x.FinancialStatements.BalanceSheet.TotalAssets.ThreeMonths != 0 and not np.isnan(x.FinancialStatements.BalanceSheet.TotalAssets.ThreeMonths)],
            key=lambda x: x.DollarVolume, reverse=True)

    if len(selected) > self.fundamental_count:
        selected = [x for x in sorted(selected, key=self.fundamental_sorting_key, reverse=True)[:self.fundamental_count]]

    momentum:dict[Symbol, float] = {}
    cash_hedged:dict[Symbol, float] = {}

    # warmup price rolling windows
    for stock in selected:
        symbol:Symbol = stock.Symbol

        if symbol not in self.price_data:
            self.price_data[symbol] = RollingWindow[float](self.period)

            history:DataFrame = self.History(symbol, self.period, Resolution.Daily)
            if history.empty:
                self.Log(f"Not enough data for {symbol} yet.")
                continue
            closes:pd.Series = history.loc[symbol].close
            for time, close in closes.items():
                self.price_data[symbol].Add(close)
        
        if self.price_data[symbol].IsReady:
            cash_hedged[stock] = 1 - (stock.FinancialStatements.BalanceSheet.CashAndCashEquivalents.ThreeMonths / stock.FinancialStatements.BalanceSheet.TotalAssets.ThreeMonths)
            momentum[stock] = self.price_data[symbol][0] / self.price_data[symbol][self.period - 1] - 1

    if len(momentum)  None:
    if not self.selection_flag:
        return
    self.selection_flag = False
    
    # trade execution
    portfolio:List[PortfolioTarget] = [PortfolioTarget(symbol, w) for symbol, w in self.weight.items() if symbol in data and data[symbol]]
    self.SetHoldings(portfolio, True)

    self.weight.clear()
            
def Selection(self) -> None:
    self.selection_flag = True

# Custom fee model
class CustomFeeModel(FeeModel):
def GetOrderFee(self, parameters):
    fee = parameters.Security.Price * parameters.Order.AbsoluteQuantity * 0.00005
    return OrderFee(CashAmount(fee, "USD"))
