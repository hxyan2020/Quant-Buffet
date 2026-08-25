# Original QuantConnect / library Python
# locale=en slug="资产类别中的价值和动量因子"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

from AlgorithmImports import *
import data_tools
from typing import List, Tuple, Dict
from QuantConnect.Data.Market import TradeBar
from QuantConnect.Indicators import RollingWindow

class ValueMomentumAcrossAssets(QCAlgorithm):

def Initialize(self):
    self.SetStartDate(2010, 1, 1)
    self.SetCash(100000)
    self.assets = [
        ('SPY', 'SP500_EARNINGS_YIELD_MONTH', data_tools.QuantpediaMonthlyData, 0, True),
        ('MDY', 'MID_CAP_PE', data_tools.QuantpediaPERatio, 0, True),
        ('IYR', 'REITS_DIVIDEND_YIELD', data_tools.QuantpediaPERatio, -2, False),
        ('EWU', 'United Kingdom', None, 0, True),
        ('EWJ', 'Japan', None, 0, True),
        ('EEM', 'EMERGING_MARKET_PE', data_tools.QuantpediaPERatio, -1, True),
        ('LQD', 'ML/AAAEY', data_tools.QuandlAAAYield, -2, False),
        ('HYG', 'ML/USTRI', data_tools.QuandlHighYield, -6, False),
        ('CME_TY1', 'US10YT', data_tools.QuantpediaBondYield, -1, False),
        ('EUREX_FGBL1', 'DE10YT', data_tools.QuantpediaBondYield, -1, False),
        ('SGX_JB1', 'JP10YT', data_tools.QuantpediaBondYield, -1, False),
        ('BIL', 'IR3TIB01USM156N', data_tools.QuantpediaMonthlyData, 0, False)
    ]

    self.SetWarmUp(252)
    self.leverage = 5
    self.quantile = 4
    self.data = {}

    for symbol, _, data_type, _, _ in self.assets:
        if data_type:
            self.AddData(data_type, symbol, Resolution.Daily)
        else:
            self.AddEquity(symbol, Resolution.Daily).SetLeverage(self.leverage)
    
    self.Settings.MinimumOrderMarginPortfolioPercentage = 0.0
    self.last_month = -1

def OnData(self, data):
    if self.IsWarmingUp:
        return

    current_month = self.Time.month
    if current_month == self.last_month:
        return
    self.last_month = current_month

    performance_1m = {}
    performance_12m = {}
    valuation = {}

    for symbol, yield_symbol, data_type, yield_adj, reverse_flag in self.assets:
        if symbol not in self.data:
            self.data[symbol] = RollingWindow[float](252)
        if symbol in data:
            self.data[symbol].Add(data[symbol].Price)

    # Calculate performance and valuation

    for symbol in self.data:
        if self.data[symbol].IsReady:
            price_series = [x for x in self.data[symbol]]
            performance_1m[symbol] = price_series[0] / price_series[21] - 1
            performance_12m[symbol] = price_series[0] / price_series[-1] - 1
            # Add your valuation calculation here based on the asset type
            
    # Implement ranking and portfolio construction logic here

class CustomFeeModel(FeeModel):
def GetOrderFee(self, parameters: OrderFeeParameters):
    fee = parameters.Security.Price * parameters.Order.AbsoluteQuantity * 0.00005
    return OrderFee(CashAmount(fee, "USD"))
