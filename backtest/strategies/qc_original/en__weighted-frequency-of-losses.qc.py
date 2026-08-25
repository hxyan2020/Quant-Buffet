# Original QuantConnect / library Python
# locale=en slug="weighted-frequency-of-losses"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

from AlgorithmImports import *
from pandas.core.frame import DataFrame
from typing import List, Dict
import numpy as np
from collections import deque
# endregion

class WeightedFrequencyofLosses(QCAlgorithm):

def Initialize(self) -> None:
    self.SetStartDate(2000, 1, 1)
    self.SetCash(100000)  

    self.market:Symbol = self.AddEquity("SPY", Resolution.Daily).Symbol
    self.tickers_to_ignore:List[str] = ['CDLB']

    self.weight:Dict[Symbol, float] = {}
    self.data:Dict[Symbol, deque] = {}

    self.r:float = 0.13
    self.quantile:int = 10
    self.leverage:int = 5
    self.period = 30

    self.fundamental_count:int = 3000
    self.selection_flag:bool = False
    self.UniverseSettings.Resolution = Resolution.Daily
    self.Settings.MinimumOrderMarginPortfolioPercentage = 0
    self.AddUniverse(self.FundamentalSelectionFunction)
    self.Schedule.On(self.DateRules.MonthStart(self.market), self.TimeRules.AfterMarketOpen(self.market), self.Selection)

def OnSecuritiesChanged(self, changes:SecurityChanges) -> None:
    for security in changes.AddedSecurities:
        security.SetLeverage(self.leverage)
        security.SetFeeModel(CustomFeeModel())

def FundamentalSelectionFunction(self, fundamental: List[Fundamental]) -> List[Symbol]:
    # update the rolling window every day
    for stock in fundamental:
        symbol:Symbol = stock.Symbol

        # store monthly price
        if symbol in self.data:
            self.data[symbol].append((self.Time, stock.AdjustedPrice))

    if not self.selection_flag:
        return Universe.Unchanged

    selected:List[Fundamental] = [x for x in fundamental if x.HasFundamentalData and x.Market == 'usa' and x.Symbol.Value not in self.tickers_to_ignore and x.MarketCap != 0 and \
            (x.SecurityReference.ExchangeId == 'NYS') or (x.SecurityReference.ExchangeId == 'NAS') or (x.SecurityReference.ExchangeId == 'ASE')]
    # selected:List[Fundamental] = [x
    #     for x in sorted([x for x in fundamental if x.HasFundamentalData and x.Market == 'usa' and x.Symbol.Value not in self.tickers_to_ignore],
    #         key = lambda x: x.DollarVolume, reverse = True)[:self.fundamental_count]]
    
    # warmup price rolling windows
    for stock in selected:
        symbol:Symbol = stock.Symbol
        if symbol in self.data:
            continue
        
        self.data[symbol] = deque(maxlen=self.period)
        history:DataFrame = self.History(symbol, self.period, Resolution.Daily)
        if history.empty:
            self.Log(f"Not enough data for {symbol} yet.")
            continue
        closes:pd.Series = history.loc[symbol].close
        for time, close in closes.items():
            self.data[symbol].append((time, close))

    # selected = [x for x in selected if x.MarketCap != 0 and \
    #         (x.SecurityReference.ExchangeId == 'NYS') or (x.SecurityReference.ExchangeId == 'NAS') or (x.SecurityReference.ExchangeId == 'ASE')]

    if len(selected) > self.fundamental_count:
        selected = sorted(selected, key=lambda x: x.MarketCap, reverse=True)[:self.fundamental_count]

    selected:Dict[Symbol, Fundamental] = {x.Symbol: x for x in selected if len(self.data[x.Symbol]) == self.data[x.Symbol].maxlen}

    if len(selected) != 0:
        # create dataframe from saved prices
        selected_stocks:Dict[Symbol, List[float]] = {symbol: [i[1] for i in value] for symbol, value in self.data.items() if symbol in selected.keys()}
        df_stocks:DataFrame = pd.DataFrame(selected_stocks, index=[i[0] for i in list(self.data.values())[0]])
        
        # trim dataframe to most recent month period
        last_month_start:datetime.date = (self.Time.date() - timedelta(self.Time.day + 1)).replace(day=1)
        df_stocks = df_stocks.pct_change()
        df_stocks = df_stocks[df_stocks.index.date >= last_month_start]
        
        # indicator function
        df_stocks[df_stocks >= 0.] = 0.
        df_stocks[df_stocks = self.quantile:
            sorted_VFL:List[Symbol] = sorted(VFL, key=VFL.get, reverse=True)
            quantile:int = int(len(sorted_VFL) / self.quantile)
            long:List[Symbol] = sorted_VFL[:quantile]
            short:List[Symbol] = sorted_VFL[-quantile:]

            # calculate weights based on marketcap
            for i, portfolio in enumerate([long, short]):
                mc_sum:float = sum([selected[x].MarketCap for x in portfolio])
                for symbol in portfolio:
                    self.weight[symbol] = ((-1) ** i) * (selected[symbol].MarketCap / mc_sum)

    return list(self.weight.keys())

def OnData(self, data: Slice) -> None:
    # monthly rebalance
    if not self.selection_flag:
        return
    self.selection_flag = False

    # trade execution
    portfolio:List[PortfolioTarget] = [PortfolioTarget(symbol, w) for symbol, w in self.weight.items() if symbol in data and data[symbol]]
    self.SetHoldings(portfolio, True)

    self.weight.clear()

def Selection(self) -> None:
    self.selection_flag = True

# custom fee model
class CustomFeeModel(FeeModel):
def GetOrderFee(self, parameters):
    fee = parameters.Security.Price * parameters.Order.AbsoluteQuantity * 0.00005
    return OrderFee(CashAmount(fee, "USD"))
