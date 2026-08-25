# Original QuantConnect / library Python
# locale=en slug="switching-between-momentum-and-reversal-strategies-based-on-market-volatility"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

from AlgorithmImports import *
from pandas.core.frame import DataFrame
from typing import List, Dict
from dateutil.relativedelta import relativedelta
# endregion

class SwitchingBetweenMomentumandReversalStrategiesBasedonMarketVolatility(QCAlgorithm):

def Initialize(self):
    self.SetStartDate(2005, 1, 1) 
    self.SetCash(100000)
 
    self.market:Symbol = self.AddEquity('SPY', Resolution.Daily).Symbol

    self.period:int = 60

    self.weight:Dict[Symbol, float] = {}
    self.quantile:int = 10
    self.min_share_price:int = 5

    self.leverage:int = 5
    self.fundamental_count:int = 500
    self.selection_flag:bool = False
    self.UniverseSettings.Resolution = Resolution.Daily
    self.Settings.MinimumOrderMarginPortfolioPercentage = 0.
    self.AddUniverse(self.FundamentalSelectionFunction)
    self.Schedule.On(self.DateRules.MonthStart(self.market), self.TimeRules.AfterMarketOpen(self.market), self.Selection)

def OnSecuritiesChanged(self, changes:SecurityChanges) -> None:
    for security in changes.AddedSecurities:
        security.SetFeeModel(CustomFeeModel())
        security.SetLeverage(self.leverage)

def FundamentalSelectionFunction(self, fundamental: List[Fundamental]) -> List[Symbol]:
    # monthly selection
    if not self.selection_flag:
        return Universe.Unchanged

    selected:Dict[Symbol, Fundamental] = { x.Symbol : x
        for x in sorted([x for x in fundamental if x.HasFundamentalData and x.Market == 'usa' and x.AdjustedPrice > x.AdjustedPrice >= self.min_share_price and 
        (x.SecurityReference.ExchangeId == 'NYS') or (x.SecurityReference.ExchangeId == 'NAS') or (x.SecurityReference.ExchangeId == 'ASE') and x.MarketCap != 0], 
        key = lambda x: x.DollarVolume, reverse = True)[:self.fundamental_count] } 

    # call history on assets
    history:DataFrame = self.History(list(selected.keys()) + [self.market], start=self.Time.date() - relativedelta(months=self.period), end=self.Time.date())['close'].unstack(level=0)
    market_volatility:DataFrame = history[self.market].pct_change().rolling(window='21D').std().dropna() * np.sqrt(252)
    market_volatility = market_volatility.resample('M').last()

    # check market volatility and set strategy
    low_vol_flag = False
    if market_volatility.iloc[-1] = self.quantile:
        sorted_assets:List[Fundamental] = sorted(stocks_returns, key=stocks_returns.get, reverse=low_vol_flag)
        quantile:int = int(len(sorted_assets) / self.quantile)
        long:List[Fundamental] = sorted_assets[:quantile]
        short:List[Fundamental] = sorted_assets[-quantile:]

        # calculate weights based on values
        for i, portfolio in enumerate([long, short]):
            mc_sum:float = sum([x.MarketCap for x in portfolio])
            for stock in portfolio:
                self.weight[stock.Symbol] = ((-1) ** i) * (stock.MarketCap / mc_sum)

    return list(self.weight.keys())

def OnData(self, data: Slice) -> None:
    # monthly rebalance
    if not self.selection_flag:
        return
    self.selection_flag = False

    portfolio:List[PortfolioTarget] = [PortfolioTarget(symbol, w) for symbol, w in self.weight.items() if symbol in data and data[symbol]]
    self.SetHoldings(portfolio, True)

    self.weight.clear()
    
def Selection(self) -> None:
    self.selection_flag = True

# Custom fee model.
class CustomFeeModel(FeeModel):
def GetOrderFee(self, parameters):
    fee = parameters.Security.Price * parameters.Order.AbsoluteQuantity * 0.00005
    return OrderFee(CashAmount(fee, "USD"))
