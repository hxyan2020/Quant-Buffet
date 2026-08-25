# Original QuantConnect / library Python
# locale=en slug="剩余动量因子"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

import numpy as np
from AlgoLib import *
import statsmodels.api as sm

class ResidualMomentumFactor(XXX):

def Initialize(self):
    self.SetStartDate(2000, 1, 1)
    self.SetCash(100000)

    # Monthly price data.
    self.data:Dict[Symbol, RollingWindow] = {}
    self.period:int = 37

    # Warmup market monthly data.
    self.symbol:Symbol = self.AddEquity('SPY', Resolution.Daily).Symbol
    self.data[self.symbol] = RollingWindow[float](self.period)
    
    history = self.History(self.symbol, self.period * 21, Resolution.Daily)
    if history.empty:
        self.Log(f"Not enough data for {self.symbol} yet.")
    else:    
        closes = history.loc[self.symbol].close
        closes_len = len(closes.keys())
        # Find monthly closes.
        for index, time_close in enumerate(closes.items()):
            # index out of bounds check.
            if index + 1  None:
    for security in changes.AddedSecurities:
        security.SetLeverage(self.leverage)
        security.SetFeeModel(CustomFeeModel())

def FundamentalSelectionFunction(self, fundamental: List[Fundamental]) -> List[Symbol]:
    if not self.selection_flag:
        return Universe.Unchanged

    # Update the rolling window every month.
    for stock in fundamental:
        symbol = stock.Symbol
        
        # Store monthly market price.
        if symbol == self.symbol:
            self.data[self.symbol].Add(stock.AdjustedPrice)
        else:
            # Store monthly stock price.
            if symbol in self.data:
                self.data[symbol].Add(stock.AdjustedPrice)

    selected:List[Fundamental] = [x for x in fundamental if x.HasFundamentalData and x.Market == 'usa' and x.MarketCap != 0 and x.CompanyReference.IsREIT == 0 and \
        ((x.SecurityReference.ExchangeId == "NYS") or (x.SecurityReference.ExchangeId == "NAS") or (x.SecurityReference.ExchangeId == "ASE"))
        ]

    if len(selected) > self.fundamental_count:
        selected = [x for x in sorted(selected, key=self.fundamental_sorting_key, reverse=True)[:self.fundamental_count]]
        
    # Warmup price rolling windows.
    for stock in selected:
        symbol:Symbol = stock.Symbol
        
        if symbol in self.data: continue

        self.data[symbol] = RollingWindow[float](self.period)
        history = self.History(symbol, self.period * 21, Resolution.Daily)
        if history.empty:
            self.Log(f"Not enough data for {symbol} yet.")
            continue
        closes = history.loc[symbol].close
        
        closes_len = len(closes.keys())
        # Find monthly closes.
        for index, time_close in enumerate(closes.items()):
            # index out of bounds check.
            if index + 1  None:
    if self.Time.month != self.last_month:
        self.last_month = self.Time.month
        self.selection_flag = True
        return
    
    if not self.selection_flag:
        return
    self.selection_flag = False
    
    # Trade execution.
    targets:List[PortfolioTarget] = []
    for i, portfolio in enumerate([self.long, self.short]):
        for symbol in portfolio:
            if symbol in data and data[symbol]:
                targets.append(PortfolioTarget(symbol, ((-1) ** i) / len(portfolio)))
    
    self.SetHoldings(targets, True)

    self.long.clear()
    self.short.clear()

def CalculateFactorPerformance(self, data, factor_symbols) -> float:
    monthly_return = 0
    if len(factor_symbols) != 0:
        for symbol, long_flag in factor_symbols:
            if symbol in data and data[symbol].Count >= 2:
                closes = [x for x in data[symbol]]
                if long_flag:
                    monthly_return += ((closes[0] / closes[1] - 1) / len(factor_symbols))
                else:
                    monthly_return -= ((closes[0] / closes[1] - 1) / len(factor_symbols))

    return monthly_return

def MultipleLinearRegression(self, x, y):
    x = np.array(x).T
    x = sm.add_constant(x)
    result = sm.OLS(endog=y, exog=x).fit()
    return result

# Custom fee model.
class CustomFeeModel(FeeModel):
def GetOrderFee(self, parameters):
    fee = parameters.Security.Price * parameters.Order.AbsoluteQuantity * 0.00005
    return OrderFee(CashAmount(fee, "USD"))
