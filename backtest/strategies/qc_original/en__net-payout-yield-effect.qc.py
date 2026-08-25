# Original QuantConnect / library Python
# locale=en slug="net-payout-yield-effect"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

from AlgoLib import *
import numpy as np

class NetPayoutYieldEffect(XXX):

def Initialize(self):
    self.SetStartDate(2000, 1, 1)  
    self.SetCash(100_000) 

    self.UniverseSettings.Leverage = 5
    self.UniverseSettings.Resolution = Resolution.Daily
    self.AddUniverse(self.FundamentalFunction)
    self.Settings.MinimumOrderMarginPortfolioPercentage = 0.0
    
    # Fundamental Filter Parameters
    self.exchange_codes = ['NYS', 'NAS', 'ASE']
    self.fundamental_count = 500
    self.quantile = 10

    self.long_symbols = []
    
    self.rebalancing_month = 6
    self.selection_flag = True

    self.exchange = self.AddEquity('SPY', Resolution.Daily).Symbol
    self.Schedule.On(self.DateRules.MonthEnd(self.exchange), 
                    self.TimeRules.AfterMarketOpen(self.exchange), 
                    self.Selection)

def FundamentalFunction(self, fundamental):
    if not self.selection_flag:
        return Universe.Unchanged

    filtered = [f for f in fundamental if f.HasFundamentalData
                and f.SecurityReference.ExchangeId in self.exchange_codes
                and not np.isnan(f.MarketCap)
                and f.MarketCap !=0
                and not np.isnan(f.ValuationRatios.TotalYield)
                and f.ValuationRatios.TotalYield != 0
                and not np.isnan(f.FinancialStatements.CashFlowStatement.CommonStockIssuance.TwelveMonths)
                and f.FinancialStatements.CashFlowStatement.CommonStockIssuance.TwelveMonths != 0]
    
    top_by_dollar_volume = sorted(filtered, 
                                    key=lambda x: x.DollarVolume, 
                                    reverse=True)[:self.fundamental_count]

    payout_yield = lambda x: ((x.ValuationRatios.TotalYield * (x.MarketCap)) - \
                (x.FinancialStatements.CashFlowStatement.CommonStockIssuance.TwelveMonths / (x.MarketCap)))
    
    sorted_by_payout = sorted(top_by_dollar_volume, key = payout_yield, reverse=True)

    if len(sorted_by_payout) >= self.quantile:
        quantile = int(len(sorted_by_payout) / self.quantile)
        self.long_symbols = [x.Symbol for x in sorted_by_payout[:quantile]]

    return self.long_symbols

def OnData(self, slice):
    if not self.selection_flag:
        return
    self.selection_flag = False

    # Trade Execution
    portfolio = [PortfolioTarget(symbol, 1 / len(self.long_symbols)) 
                                        for symbol in self.long_symbols 
                                        if slice.ContainsKey(symbol) and slice[symbol] is not None]

    self.SetHoldings(portfolio, True)
    self.long_symbols.clear()

def Selection(self):
    if self.Time.month == self.rebalancing_month:
        self.selection_flag = True

def OnSecuritiesChanged(self, changes):
    for security in changes.AddedSecurities:
        security.SetFeeModel(CustomFeeModel())

# Custom fee model
class CustomFeeModel(FeeModel):
def GetOrderFee(self, parameters):
    fee = parameters.Security.Price * parameters.Order.AbsoluteQuantity * 0.00005
    return OrderFee(CashAmount(fee, "USD"))
