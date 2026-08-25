# Original QuantConnect / library Python
# locale=en slug="股票中的动量因子效应"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

class NetCurrentAssetValueEffect(XXX):

def Initialize(self):
    self.SetStartDate(2000, 1, 1)  
    self.SetCash(100000) 

    self.symbol = self.AddEquity('SPY', Resolution.Daily).Symbol
    
    self.coarse_count = 3000  
    
    self.long = []
    
    self.selection_flag = False
    self.UniverseSettings.Resolution = Resolution.Daily
    self.AddUniverse(self.CoarseSelectionFunction, self.FineSelectionFunction)
 
    self.Schedule.On(self.DateRules.MonthEnd(self.symbol), self.TimeRules
.AfterMarketOpen(self.symbol), self.Selection)

def OnSecuritiesChanged(self, changes):
    for security in changes.AddedSecurities:
        security.SetFeeModel(CustomFeeModel())
        security.SetLeverage(10)

def CoarseSelectionFunction(self, coarse):
    if not self.selection_flag:
        return Universe.Unchanged
    
    selected = [x.Symbol for x in coarse if x.HasFundamentalData and x.Market == 'usa']
    return selected

def FineSelectionFunction(self, fine):
    fine = [x for x in fine if x.EarningReports.BasicAverageShares.ThreeMonths > 0 
and x.MarketCap != 0 and x.ValuationRatios.WorkingCapitalPerShare != 0]
    sorted_by_market_cap = sorted(fine, key = lambda x:x.MarketCap, reverse=True)
    top_by_market_cap = [x for x in sorted_by_market_cap[:self.coarse_count]] 
    
    self.long = [x.Symbol for x in top_by_market_cap if ((x.ValuationRatios
.WorkingCapitalPerShare * x.EarningReports.BasicAverageShares.ThreeMonths) / x.MarketCap) > 1.5]
    
    return self.long

def OnData(self, data):
    if not self.selection_flag:
        return
    self.selection_flag = False

    stocks_invested = [x.Key for x in self.Portfolio if x.Value.Invested]
    for symbol in stocks_invested:
        if symbol not in self.long:
            self.Liquidate(symbol)

    for symbol in self.long:
        if symbol in data and data[symbol]:
            self.SetHoldings(symbol, 1 / len(self.long))  

    self.long.clear()

## only select the ones in June
def Selection(self):
    if self.Time.month == 6:
        self.selection_flag = True

class CustomFeeModel(FeeModel):
def GetOrderFee(self, parameters):
    fee = parameters.Security.Price * parameters.Order.AbsoluteQuantity * 0.00005
    return OrderFee(CashAmount(fee, "USD"))
