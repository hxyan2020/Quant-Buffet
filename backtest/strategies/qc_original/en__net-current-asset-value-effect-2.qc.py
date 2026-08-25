# Original QuantConnect / library Python
# locale=en slug="net-current-asset-value-effect-2"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

from AlgoLib import *
import numpy as np

class NetCurrentAssetValueStrategy(XXX):

def Initialize(self):
    self.SetStartDate(2000, 1, 1)
    self.SetCash(100000)
    
    self.UniverseSettings.Leverage = 3
    self.UniverseSettings.Resolution = Resolution.Daily
    self.AddUniverse(self.SelectStocks)
    self.Settings.MinimumOrderMarginPortfolioPercentage = 0.0

    # Stock Selection Criteria
    self.max_stocks = 3000
    self.market = 'usa'
    self.exclude_fin_sector = 103
    self.ncav_ratio_min = 1.5
    
    self.target_stocks = []

    self.rebalance_period = 7
    self.should_rebalance = True

    self.spy = self.AddEquity('SPY', Resolution.Daily).Symbol
    self.Schedule.On(self.DateRules.MonthStart(self.spy), 
                     self.TimeRules.AfterMarketOpen(self.spy), 
                     self.RebalancePortfolio)

def SelectStocks(self, fundamental_data: List[Fundamental]) -> List[Symbol]:
    if not self.should_rebalance:
        return Universe.Unchanged

    qualified_stocks = [f for f in fundamental_data if f.HasFundamentalData and
                        f.Market == self.market and
                        f.AssetClassification.MorningstarSectorCode != self.exclude_fin_sector and
                        not np.isnan(f.MarketCap) and f.MarketCap > 0 and
                        not np.isnan(f.ValuationRatios.WorkingCapitalPerShare) and
                        f.ValuationRatios.WorkingCapitalPerShare > 0]

    qualified_stocks = sorted(qualified_stocks, 
                              key=lambda x: x.MarketCap)[:self.max_stocks]

    self.target_stocks = [stock.Symbol for stock in qualified_stocks if
                          ((stock.ValuationRatios.WorkingCapitalPerShare * 
                            stock.EarningReports.BasicAverageShares.TwelveMonths) /
                           stock.MarketCap) > self.ncav_ratio_min]

    return self.target_stocks

def OnData(self, data: Slice):
    if not self.should_rebalance:
        return
    
    self.should_rebalance = False

    if len(self.target_stocks) > 0:
        weight = 1 / len(self.target_stocks)
        for stock in self.target_stocks:
            if data.ContainsKey(stock):
                self.SetHoldings(stock, weight)
        self.target_stocks.clear()

def RebalancePortfolio(self):
    if self.Time.month == self.rebalance_period:
        self.should_rebalance = True

def OnSecuritiesChanged(self, changes: SecurityChanges):
    for security in changes.AddedSecurities:
        security.SetFeeModel(CustomFeeModel())

class CustomFeeModel(FeeModel):
def GetOrderFee(self, parameters: OrderFeeParameters) -> OrderFee:
    fee = parameters.Security.Price * parameters.Order.AbsoluteQuantity * 0.00005
    return OrderFee(CashAmount(fee, "USD"))
