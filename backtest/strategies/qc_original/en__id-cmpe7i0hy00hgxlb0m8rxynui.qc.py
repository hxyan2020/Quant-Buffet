# Original QuantConnect / library Python
# locale=en slug="用便宜期权对冲尾部风险策略"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

from AlgorithmImports import *
from typing import List, Dict
# endregion
class TailRiskHedgingwithCheapOptions(QCAlgorithm):
def Initialize(self):
    self.SetStartDate(2010, 1, 1)
    self.SetCash(1_000_000)
    seeder = FuncSecuritySeeder(self.GetLastKnownPrices)
    self.SetSecurityInitializer(lambda security: seeder.SeedSecurity(security))
    self.leverage: int = 5
    self.quantile: int = 5
    self.min_expiry: int = 6 * 30
    self.max_expiry: int = 12 * 30
    self.min_delta: float = 0.1
    self.exchanges: List[str] = ['NYS', 'NAS', 'ASE']
    self.active_stock_universe: List[Symbol] = []
    self.monthly_subscribed_contracts: List[OptionContract] = []
    self.market: Symbol = self.AddEquity('SPY', Resolution.Daily).Symbol
    self.option_port_weight: float = 0.02
    self.market_port_weight: float = 0.98
    self.fundamental_count: int = 100
    self.fundamental_sorting_key = lambda x: x.MarketCap
    self.selection_flag: bool = False
    self.rebalance_flag: bool = False
    self.UniverseSettings.Resolution = Resolution.Daily
    self.AddUniverse(self.FundamentalSelectionFunction)
    self.Settings.MinimumOrderMarginPortfolioPercentage = 0.
    self.UniverseSettings.DataNormalizationMode = DataNormalizationMode.Raw
    self.Schedule.On(self.DateRules.MonthStart(self.market), self.TimeRules.BeforeMarketClose(self.market, 0), self.Selection)
def OnSecuritiesChanged(self, changes: SecurityChanges) -> None:
    for security in changes.AddedSecurities:
        security.SetFeeModel(CustomFeeModel())
        security.SetLeverage(self.leverage)
def FundamentalSelectionFunction(self, fundamental: List[Fundamental]) -> List[Symbol]:
    if not self.selection_flag:
        return Universe.Unchanged
    selected: List[Fundamental] = [
        f for f in fundamental if f.HasFundamentalData and \
        f.MarketCap != 0 and \
        f.SecurityReference.ExchangeId in self.exchanges
    ]
    if len(selected) > self.fundamental_count:
        selected = [x for x in sorted(selected, key=self.fundamental_sorting_key, reverse=True)[:self.fundamental_count]]
    self.monthly_subscribed_contracts.clear()
    self.active_stock_universe = list(map(lambda stock: stock.Symbol, selected))
    return self.active_stock_universe
def OnData(self, slice: Slice) -> None:
    if self.selection_flag:
        self.selection_flag = False
        for symbol in self.active_stock_universe:
            # subscribe to contract
            contracts: List[Symbol] = self.OptionChainProvider.GetOptionContractList(symbol, self.Time)
            underlying_price: float = self.Securities[symbol].Price
            
            strikes: List[float] = [i.ID.StrikePrice for i in contracts]
            
            if len(strikes)  0:
                # sort by expiry and subscribe nearest contract
                nearest_contracts: Symbol = sorted(otm_puts, key=lambda item: item.ID.Date)[0]
                
                option: OptionContract = self.AddOptionContract(nearest_contracts, Resolution.Daily)
                option.PriceModel = OptionPriceModels.CrankNicolsonFD()
                self.monthly_subscribed_contracts.append(option)
        
        self.rebalance_flag = True
    if len(self.monthly_subscribed_contracts) != 0 and slice.OptionChains.Count != 0 and self.rebalance_flag:
        self.rebalance_flag = False
        
        option_price: Dict[Symbol, float] = {
            c.Symbol : c.AskPrice for c in self.monthly_subscribed_contracts
        }
        if len(option_price)  List[Symbol]:
    return [i for i in contracts if i.ID.OptionRight == option_right \
        and i.ID.StrikePrice == strike and self.min_expiry  None:
    self.selection_flag = True
# Custom fee model
class CustomFeeModel(FeeModel):
def GetOrderFee(self, parameters):
    fee = parameters.Security.Price * parameters.Order.AbsoluteQuantity * 0.00005
    return OrderFee(CashAmount(fee, "USD"))
