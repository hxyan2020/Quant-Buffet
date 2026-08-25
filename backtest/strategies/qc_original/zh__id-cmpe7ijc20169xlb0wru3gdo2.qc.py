# Original QuantConnect / library Python
# locale=zh slug="不同到期时间的股票期权的错误定价"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

from AlgorithmImports import *
#endregion
class MispricingofxOptionsWithDifferentTimeToMaturity(QCAlgorithm):
def Initialize(self):
    self.SetStartDate(2015, 1, 1)
    self.SetCash(1000000)
    
    self.min_share_price:int = 5
    self.min_expiry:int = 18
    self.max_expiry:int = 22
    self.percentage_traded:float = 1
    self.selected_symbols:list[Symbol] = {}
    self.subscribed_contracts:dict[Symbol, Contracts] = {}
    
    self.weeks_counter:int = 0
    self.rebalance_period:int = 3
    self.weekday_num:int = 3 # represents thursday
    self.market_symbol:Symbol = self.AddEquity('SPY', Resolution.Minute).Symbol
    self.recent_day:int = -1
    self.recent_month:int = -1
    self.fundamental_sorting_key = lambda x: x.DollarVolume
    self.fundamental_count:int = 100
    self.selection_flag:bool = False
    self.settings.daily_precise_end_time = False
    self.Settings.MinimumOrderMarginPortfolioPercentage = 0.
    self.UniverseSettings.Resolution = Resolution.Minute
    self.AddUniverse(self.FundamentalSelectionFunction)
    self.SetSecurityInitializer(lambda x: x.SetDataNormalizationMode(DataNormalizationMode.Raw))
    self.UniverseSettings.DataNormalizationMode = DataNormalizationMode.Raw
def FundamentalSelectionFunction(self, fundamental: List[Fundamental]) -> List[Symbol]:
    # rebalance, when contracts expiried
    if not self.selection_flag:
        return Universe.Unchanged
    
    selected:list = [
        x for x in fundamental if x.HasFundamentalData and x.Market == 'usa' and x.Price >= self.min_share_price
    ]
    if len(selected) > self.fundamental_count:
        selected = [x for x in sorted(selected, key=self.fundamental_sorting_key, reverse=True)[:self.fundamental_count]]
    self.selected_symbols = list(map(lambda stock: stock.Symbol, selected))
    
    return self.selected_symbols
def OnData(self, data: Slice):
    curr_date:datetime.date = self.Time.date()
    # execute once a day
    if self.recent_day != curr_date.day:
        self.recent_day = curr_date.day
        if self.recent_month != curr_date.month:
            self.recent_month = curr_date.month
            self.weeks_counter = 0
        
        # check if any of the subscribed contracts expired
        for symbol in self.selected_symbols:
            if symbol in self.subscribed_contracts and self.subscribed_contracts[symbol].expiry_date  0:
        # sort by expiry
        result = sorted(atm_calls, key = lambda item: item.ID.Date, reverse=True)[0]
    return result
    
def AddContract(self, contract) -> None:
    ''' subscribe option contract, set price mondel and normalization mode '''
    option = self.AddOptionContract(contract, Resolution.Minute)
    option.PriceModel = OptionPriceModels.BlackScholes()
    
class Contracts():
def __init__(self, expiry_date, underlying_price, contracts):
    self.expiry_date = expiry_date
    self.underlying_price = underlying_price
    self.contracts = contracts
