# Original QuantConnect / library Python
# locale=zh slug="小型行业溢价"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

from AlgorithmImports import *
import data_tools
# endregion
class SmallIndustryPremia(QCAlgorithm):
def Initialize(self) -> None:
    self.SetStartDate(2000, 1, 1)
    self.SetCash(100000)
    
    self.min_share_price:int = 5
    self.period:int = 60
    self.leverage:int = 5
    self.weights:dict = {}
    self.data:dict = {}
    self.prev_industry_country_ids:list[str] = []
    market_symbol:Symbol = self.AddEquity('SPY', Resolution.Daily).Symbol
    self.selection_flag:bool = False
    self.Settings.MinimumOrderMarginPortfolioPercentage = 0.
    self.UniverseSettings.Resolution = Resolution.Daily
    self.AddUniverse(self.FundamentalSelectionFunction)
    self.Schedule.On(self.DateRules.MonthStart(market_symbol), self.TimeRules.BeforeMarketClose(market_symbol), self.Selection)
    self.settings.daily_precise_end_time = False
def OnSecuritiesChanged(self, changes: SecurityChanges) -> None:
    for security in changes.AddedSecurities:
        security.SetFeeModel(CustomFeeModel())
        security.SetLeverage(self.leverage)
def FundamentalSelectionFunction(self, fundamental: List[Fundamental]) -> List[Symbol]:
    if not self.selection_flag:
        return Universe.Unchanged
    
    selected:list[Fundamental] = [x for x in fundamental if x.HasFundamentalData and x.Price >= self.min_share_price]
    stocks_by_industry_id:dict = {}
    for stock in selected:
        market_cap:float = stock.MarketCap
        country_id:str = stock.CompanyReference.BusinessCountryID
        sector:str = str(stock.AssetClassification.MorningstarSectorCode)
        if not country_id or not sector or market_cap == 0:
            continue
        
        industry_id:str = country_id + sector
        if industry_id not in stocks_by_industry_id:
            stocks_by_industry_id[industry_id] = []
        stocks_by_industry_id[industry_id].append(stock)
    
    # store not adjusted MV value
    for industry_id, stocks in stocks_by_industry_id.items():
        MV_value:float = np.mean(list(map(lambda stock: stock.MarketCap, stocks)))
        if industry_id not in self.data or industry_id not in self.prev_industry_ids: # require consecutive data
            self.data[industry_id] = data_tools.IndustryData(self.period)
        self.data[industry_id].update_MV_values(MV_value)
    MV_by_industry_id:dict = { industry_id: industry_obj.get_MV() \
         for industry_id, industry_obj in self.data.items() if industry_obj.is_ready() }
    mean_MV:float = np.mean(list(MV_by_industry_id.values()))
    # MV difference from mean
    long_mean_diff:dict = { industry_id : MV - mean_MV for industry_id, MV in MV_by_industry_id.items() if MV > mean_MV }
    short_mean_diff:dict = { industry_id : MV - mean_MV for industry_id, MV in MV_by_industry_id.items() if MV  None:
    # rebalance monthly
    if not self.selection_flag:
        return
    self.selection_flag = False
    
    # trade execution
    portfolio:List[PortfolioTarget] = [PortfolioTarget(symbol, w) for symbol, w in self.weights.items() if symbol in data and data[symbol]]
    self.SetHoldings(portfolio, True)
    self.weights.clear()
    
def Selection(self) -> None:
    self.selection_flag = True
    
# Custom fee model
class CustomFeeModel(FeeModel):
def GetOrderFee(self, parameters):
    fee = parameters.Security.Price * parameters.Order.AbsoluteQuantity * 0.00005
    return OrderFee(CashAmount(fee, "USD"))
