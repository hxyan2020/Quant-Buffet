# Original QuantConnect / library Python
# locale=zh slug="气候情绪、碳价与排放减去清洁投资组合"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

from AlgorithmImports import *
from data_tools import QuantpediaClimateChange, QuantpediaFutures, ClimateChangeData, CarbonFutureData, CustomFeeModel, LastDateHandler
from typing import Dict, List
# endregion
class ClimateSentimentCarbonPricesAndEmissionMinusCleanPortfolio(QCAlgorithm):
def Initialize(self) -> None:
    self.SetStartDate(2007, 1, 1)   # climate change data starts in 2004 and carbon future data starts in 2007
    self.SetCash(100_000)
    
    self.leverage: int = 5
    self.carbon_max_missing_days:int = 5
    self.climate_max_missing_days:int = 40
    self.min_prices: int = 15
    
    self.weights: Dict[Symbol, float] = {}
    self.high_emission_industries: List[MorningstarIndustryGroupCode] = [
        MorningstarIndustryGroupCode.Agriculture,
        MorningstarIndustryGroupCode.BuildingMaterials,
        MorningstarIndustryGroupCode.Chemicals,
        MorningstarIndustryGroupCode.Construction,
        MorningstarIndustryGroupCode.FarmAndHeavyConstructionMachinery,
        MorningstarIndustryGroupCode.ForestProducts,
        MorningstarIndustryGroupCode.HomebuildingAndConstruction,
        MorningstarIndustryGroupCode.MetalsAndMining,
        MorningstarIndustryGroupCode.OilAndGas,
        MorningstarIndustryGroupCode.Steel,
        MorningstarIndustryGroupCode.Transportation,
    ]
    self.market_symbol: Symbol = self.AddEquity('SPY', Resolution.Daily).Symbol
    self.climate_change: Symbol = self.AddData(QuantpediaClimateChange, 'CLIMATE_CHANGE', Resolution.Daily).Symbol
    self.climate_change_data: ClimateChangeData = ClimateChangeData()
    self.carbon_future: Symbol = self.AddData(QuantpediaFutures, 'ICE_EUA1', Resolution.Daily).Symbol
    self.carbon_future_data: CarbonFutureData = CarbonFutureData()
    self.fundamental_count: int = 500
    self.fundamental_sorting_key = lambda x: x.DollarVolume
    self.selection_flag: bool = False
    self.UniverseSettings.Leverage = self.leverage
    self.UniverseSettings.Resolution = Resolution.Daily
    self.AddUniverse(self.FundamentalSelectionFunction)
    self.settings.daily_precise_end_time = False
    self.Settings.MinimumOrderMarginPortfolioPercentage = 0.
    self.Schedule.On(self.DateRules.MonthStart(self.market_symbol), self.TimeRules.BeforeMarketClose(self.market_symbol, 0), self.Selection)
def OnSecuritiesChanged(self, changes: SecurityChanges) -> None:
    for security in changes.AddedSecurities:
        security.SetFeeModel(CustomFeeModel())
def FundamentalSelectionFunction(self, fundamental: List[Fundamental]) -> List[Symbol]:
    if not self.selection_flag:
        return Universe.Unchanged
    curr_date: datetime.date = self.Time.date()
    custom_data_last_update_date: Dict[Symbol, datetime.date] = LastDateHandler.get_last_update_date()
    if any((self.securities[symbol].get_last_data() and self.time.date() > custom_data_last_update_date[symbol]) for symbol in [self.climate_change, self.carbon_future]):
        self.Liquidate()
        return Universe.UNCHANGED
    # if not self.climate_change_data.data_still_coming(curr_date, self.climate_max_missing_days):
    #     self.climate_change_data.reset()
    # if not self.carbon_future_data.data_still_coming(curr_date, self.carbon_max_missing_days):
    #     self.carbon_future_data.reset()
    if not self.climate_change_data.is_ready() or not self.carbon_future_data.prices_ready(self.min_prices):
        self.carbon_future_data.reset()
        return Universe.Unchanged
    
    selected: List[Fundamental] = [
        x for x in fundamental 
        if x.HasFundamentalData 
        and x.MarketCap != 0
        and x.AssetClassification.MorningstarIndustryGroupCode 
    ]
    if len(selected) > self.fundamental_count:
        selected = [x for x in sorted(selected, key=self.fundamental_sorting_key, reverse=True)[:self.fundamental_count]]
    high_emission_stocks: List[Fundamental] = []
    clean_stocks: List[Fundamental] = []
    for stock in selected:
        industry_group_code: int = stock.AssetClassification.MorningstarIndustryGroupCode
        if industry_group_code in self.high_emission_industries:
            high_emission_stocks.append(stock)
        else:
            clean_stocks.append(stock)
    
    long_leg: List[Fundamental] = []
    short_leg: List[Fundamental] = []
    climate_monthly_change: float = self.climate_change_data.get_monthly_change()
    carbon_monthly_change: float = self.carbon_future_data.get_monthly_change()
    if climate_monthly_change > 0 and carbon_monthly_change  0:
        long_leg = clean_stocks
        short_leg = high_emission_stocks
    if len(long_leg) != 0 and len(short_leg) != 0:
        for i, portfolio in enumerate([long_leg, short_leg]):
            mc_sum: float = sum(list(map(lambda stock: stock.MarketCap, portfolio)))
            for stock in portfolio:
                self.weights[stock.Symbol] = ((-1)**i) * stock.MarketCap / mc_sum
    return list(self.weights.keys())
    
def OnData(self, slice: Slice) -> None:
    curr_date:datetime.date = self.Time.date()
    if slice.contains_key(self.climate_change) and slice[self.climate_change]:
        search_value: float = slice[self.climate_change].Value
        self.climate_change_data.update(curr_date, search_value)
    if slice.contains_key(self.carbon_future) and slice[self.carbon_future]:
        price: float = slice[self.carbon_future].Value
        self.carbon_future_data.update(curr_date, price)
    # rebalance monthly
    if not self.selection_flag:
        return
    self.selection_flag = False
    
    # trade execution
    portfolio: List[PortfolioTarget] = [PortfolioTarget(symbol, w) for symbol, w in self.weights.items() if slice.contains_key(symbol) and slice[symbol]]
    self.SetHoldings(portfolio, True)
    self.weights.clear()
    
def Selection(self) -> None:
    self.selection_flag = True
