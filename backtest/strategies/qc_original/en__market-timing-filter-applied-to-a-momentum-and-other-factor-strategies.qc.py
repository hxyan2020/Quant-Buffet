# Original QuantConnect / library Python
# locale=en slug="market-timing-filter-applied-to-a-momentum-and-other-factor-strategies"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

from AlgorithmImports import *
import numpy as np
from numpy import isnan
class MarketTimingFilterAppliedMomentumOtherFactorStrategies(QCAlgorithm):
def Initialize(self):
    self.SetStartDate(2000, 1, 1)
    self.SetCash(100000)
    market:Symbol = self.AddEquity('SPY', Resolution.Daily).Symbol
    
    self.SMA_period:int = 24
    self.period:int = 13
    self.quantile:int = 10
    self.leverage:int = 5
    self.fundamental_count:int = 500
    self.fundamental_sorting_key = lambda x: x.DollarVolume
    # Equity holdings value.
    self.mimic_equity_value = self.Portfolio.TotalPortfolioValue
    self.holdings_value:Dict[Symbol, List[float]] = {}
    self.equity_sma = SimpleMovingAverage(self.SMA_period)
    
    # Monthly close data.
    self.data:Dict[Symbol, SymbolData] = {}
    self.weight:Dict[Symbol, float] = {}
    
    self.plot = Chart('Strategy EQ')
    self.plot.AddSeries(Series('EQ', SeriesType.Line, 0))
    
    self.selection_flag:bool = False
    self.Settings.MinimumOrderMarginPortfolioPercentage = 0.
    self.UniverseSettings.Resolution = Resolution.Daily
    self.AddUniverse(self.FundamentalSelectionFunction)
    self.Schedule.On(self.DateRules.MonthEnd(market), self.TimeRules.AfterMarketOpen(market), self.Selection)
    self.settings.daily_precise_end_time = False
def OnSecuritiesChanged(self, changes: SecurityChanges) -> None:
    for security in changes.AddedSecurities:
        security.SetSlippageModel(CustomSlippageModel())
        security.SetFeeModel(CustomFeeModel())
        security.SetLeverage(self.leverage)
    
def FundamentalSelectionFunction(self, fundamental: List[Fundamental]) -> List[Symbol]:
    if not self.selection_flag:
        return Universe.Unchanged
    # Update the rolling window every month.
    for stock in fundamental:
        symbol:Symbol = stock.Symbol
        # Store monthly price.
        if symbol in self.data:
            self.data[symbol].update(stock.AdjustedPrice)
        
    selected:List[Funamental] = [
        x for x in fundamental if x.HasFundamentalData and x.Market == 'usa' \
        and not isnan(x.EarningReports.BasicAverageShares.ThreeMonths) and x.EarningReports.BasicAverageShares.ThreeMonths > 0 \
        and not isnan(x.EarningReports.BasicEPS.TwelveMonths) and x.EarningReports.BasicEPS.TwelveMonths > 0 \
        and not isnan(x.ValuationRatios.PERatio) and x.ValuationRatios.PERatio > 0
    ]
    if len(selected) > self.fundamental_count:
        selected = [x for x in sorted(selected, key=self.fundamental_sorting_key, reverse=True)[:self.fundamental_count]]
        
    performance_market_cap:Dict[Symbol, List[float]] = {}
    # Warmup price rolling windows.
    for stock in selected:
        symbol:Symbol = stock.Symbol
        if symbol not in self.data: 
            self.data[symbol] = SymbolData(self.period)
            history:DataFrame = self.History(symbol, self.period*30, Resolution.Daily)
            if history.empty:
                self.Log(f"Not enough data for {symbol} yet.")
                continue
            closes:Series = history.loc[symbol].close
            
            closes_len:int = len(closes.keys())
            # Find monthly closes.
            for index, time_close in enumerate(closes.items()):
                # index out of bounds check.
                if index + 1  None:
    if not self.selection_flag:
        return
    self.selection_flag = False
    
    # Trade execution
    if len(self.weight) == 0: 
        self.Liquidate()
        return
    stocks_invested:List[Symbol] = [x.Key for x in self.Portfolio if x.Value.Invested]
    for symbol in stocks_invested:
        if symbol not in self.weight:
            self.Liquidate(symbol)
    
    # Calculate symbol equity. - mimic trading.
    for symbol, holdings in self.holdings_value.items():
        curr_price:float = self.Securities[symbol].Price
        
        holdings_price:float = holdings[0]
        holdings_q:float = holdings[1]
        fee:float = holdings_price * abs(holdings_q) * 0.00005
        slippage:float = curr_price * float(0.0001 * np.log10(2*float(abs(holdings_q))))
        
        last_holdings_value:float = holdings_price * holdings_q - fee - slippage
        new_holdings_value:float = (curr_price * holdings_q)
        trade_pl:float = (new_holdings_value - last_holdings_value)
        self.mimic_equity_value += trade_pl
    self.equity_sma.Update(self.Time, self.mimic_equity_value)
    self.Plot("Strategy EQ", "EQ", self.mimic_equity_value)
    # self.Log('Real portfolio value: {0}; Alternative portfolio value: {1}'.format(self.Portfolio.TotalPortfolioValue, self.mimic_equity_value))
    self.holdings_value.clear()
    
    for symbol, w in self.weight.items():
        if symbol in data and data[symbol]:
            # Store symbol equity holdings. - mimic trading.
            curr_price:float = data[symbol].Value
            if curr_price != 0:
                q:float = (self.mimic_equity_value * w) / curr_price
                
                self.holdings_value[symbol] = [curr_price, q]
                if self.equity_sma.IsReady:
                    if self.mimic_equity_value > self.equity_sma.Current.Value:
                        self.SetHoldings(symbol, w)
                else:
                    continue
                
    self.weight.clear()
def Selection(self) -> None:
    self.selection_flag = True
                
class SymbolData():
def __init__(self, period: int) -> None:
    self.Closes:RollingWindow = RollingWindow[float](period)
    
def update(self, close: float) -> None:
    self.Closes.Add(close)
    
def is_ready(self) -> bool:
    return self.Closes.IsReady
    
def performance(self) -> float:
    closes = [x for x in self.Closes][1:]   # skip last month
    return (closes[0] - closes[-1]) / closes[-1]
                
# Custom fee model.
class CustomFeeModel(FeeModel):
def GetOrderFee(self, parameters):
    fee = parameters.Security.Price * parameters.Order.AbsoluteQuantity * 0.00005
    return OrderFee(CashAmount(fee, "USD"))
    
# Custom slippage model.
class CustomSlippageModel:
def GetSlippageApproximation(self, asset, order):
    # custom slippage math
    slippage = asset.Price * float(0.0001 * np.log10(2*float(order.AbsoluteQuantity)))
    return slippage
