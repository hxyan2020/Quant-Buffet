# Original QuantConnect / library Python
# locale=en slug="market-neutral-strategy-based-on-share-buybacks"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

from QuantConnect.Data.Custom.SmartInsider import *
class MarketNeutralStrategyBasedShareBuybacks(QCAlgorithm):
def Initialize(self):
    # SmartInsider data starts in 2015 for most stocks.
    self.SetStartDate(2015, 1, 1)
    self.SetCash(100000) 
    data = self.AddEquity('IWM', Resolution.Daily)
    data.SetLeverage(10)
    self.symbol = data.Symbol
    
    self.course_count = 500
    self.last_course = []
    
    self.period = 3 * 30
    self.long = []
    
    self.selection_flag = False
    self.UniverseSettings.Resolution = Resolution.Daily
    self.AddUniverse(self.CoarseSelectionFunction)
    
    # Weekly rebalance.
    self.Schedule.On(self.DateRules.Every(DayOfWeek.Friday), self.TimeRules.BeforeMarketClose(self.symbol), self.Selection)
def OnSecuritiesChanged(self, changes):
    for security in changes.AddedSecurities:
        security.SetFeeModel(CustomFeeModel(self))
        security.SetLeverage(10)
def CoarseSelectionFunction(self, coarse):
    if not self.selection_flag:
        return Universe.Unchanged
    
    selected = sorted([x for x in coarse if x.HasFundamentalData and x.Market == 'usa' and x.Price > 5],
        key=lambda x: x.DollarVolume, reverse=True)
    
    self.last_course = [x.Symbol for x in selected[:self.course_count]]
    
    return self.last_course

def OnData(self, data):
    if not self.selection_flag:
        return
    self.selection_flag = False
    
    for symbol in self.last_course:
        # Add smart insider data.
        smart_insider_symbol = self.AddData(SmartInsiderTransaction, symbol, Resolution.Daily).Symbol
        
        # NOTE:
        # v.1 - Iterate over last transactions. There's a weird "lag" between actual date and last buyback date. 
        # - faster, not so precise I guess.
        transactions = self.Securities[symbol].Data.GetAll(SmartInsiderTransaction)
        if any(x.BuybackDate >= self.Time - timedelta(days = self.period) for x in transactions):
            self.long.append(symbol)
            
        # v.2 Get buyback history.
        # - slow due to History() call, more precise.
        # history = self.History(SmartInsiderTransaction, smart_insider_symbol, 60, Resolution.Daily)
        # if not history.empty:
        #     self.long.append(symbol)
    
    # Trade execution
    count = len(self.long)
    stocks_invested = [x.Key for x in self.Portfolio if x.Value.Invested]
    for symbol in stocks_invested:
        if symbol not in self.long:
            self.Liquidate(symbol)
    for symbol in self.long:
        self.SetHoldings(symbol, 1 / count)
    
    # Hedge with IWM with no leverage.
    self.SetHoldings(self.symbol, -1)
    self.long.clear()

def Selection(self):
    self.selection_flag = True
    
# Custom fee model
class CustomFeeModel(FeeModel):
def GetOrderFee(self, parameters):
    fee = parameters.Security.Price * parameters.Order.AbsoluteQuantity * 0.00005
    return OrderFee(CashAmount(fee, "USD"))
