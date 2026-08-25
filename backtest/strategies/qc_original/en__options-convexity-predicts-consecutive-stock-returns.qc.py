# Original QuantConnect / library Python
# locale=en slug="options-convexity-predicts-consecutive-stock-returns"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

import numpy as np
from AlgorithmImports import *
from typing import Dict, List, Tuple
class OptionsConvexityPredictsConsecutiveStockReturns(QCAlgorithm):
def Initialize(self) -> None:
    self.SetStartDate(2015, 1, 1)
    self.SetCash(100000)
    
    self.min_expiry: int = 25
    self.max_expiry: int = 35
    self.quantile: int = 5
    self.leverage: int = 5
    self.min_share_price: int = 5
    self.contracts_count: int = 3
    self.thresholds: List[int] = [0.95, 1.05]
    self.next_expiry: Union[None, datetime.date] = None
    
    self.fundamental_count: int = 100
    self.fundamental_sorting_key = lambda x: x.DollarVolume
    self.selection_flag: bool = False
    self.stock_universe: List[Symbol] = []
    self.option_universe: Dict[Symbol, List[Symbol]] = {}
    self.contracts_expiry: Dict[Symbol, datetime.date] = {} # storing contracts expiry date under symbols
    self.settings.daily_precise_end_time = False
    self.Settings.MinimumOrderMarginPortfolioPercentage = 0.
    self.UniverseSettings.Resolution = Resolution.Minute
    self.AddUniverse(self.FundamentalSelectionFunction)
    self.SetSecurityInitializer(lambda x: x.SetDataNormalizationMode(DataNormalizationMode.Raw))
    self.UniverseSettings.DataNormalizationMode = DataNormalizationMode.Raw
    self.current_day: int = -1
    symbol: Symbol = self.AddEquity("SPY", Resolution.Daily).Symbol
    self.Schedule.On(self.DateRules.MonthStart(symbol), self.TimeRules.AfterMarketOpen(symbol), self.Selection)

def OnSecuritiesChanged(self, changes: SecurityChanges) -> None:
    for security in changes.AddedSecurities:
        security.SetFeeModel(CustomFeeModel())
        security.SetLeverage(self.leverage)
    # remove old option contracts
    for security in changes.RemovedSecurities:
        symbol = security.Symbol
        if symbol in self.option_universe:
            for option in self.option_universe[symbol]:
                self.RemoveSecurity(option)
            del self.option_universe[symbol]
            self.Liquidate(symbol)
def FundamentalSelectionFunction(self, fundamental: List[Fundamental]) -> List[Symbol]:
    # new symbol selection once a quarter
    if not self.selection_flag:
        return Universe.Unchanged
    selected: List[Fundamental] = [
        x for x in fundamental 
        if x.HasFundamentalData 
        and x.Market == 'usa' 
        and x.Price > self.min_share_price
    ]
    if len(selected) > self.fundamental_count:
        selected = [
        x for x in sorted(
            selected, 
            key=self.fundamental_sorting_key, 
            reverse=True)[:self.fundamental_count]
            ]     
    
    self.stock_universe = [x.Symbol for x in selected]
    return self.stock_universe
    
def Selection(self) -> None:
    if self.Time.month % 3 == 0:
        self.selection_flag = True
        self.Liquidate()

def OnData(self, data: Slice) -> None:
    # rebalance daily
    if self.current_day == self.Time.day:
        return
    self.current_day = self.Time.day
    
    if self.next_expiry and self.Time.date() >= self.next_expiry.date():
        for symbol in self.option_universe:
            for option in self.option_universe[symbol]:
                self.RemoveSecurity(option)
        self.Liquidate()
    # for symbol in self.option_universe:
    #     # subscribe to new contracts, because current ones has expiried
    #     if symbol not in self.contracts_expiry or self.contracts_expiry[symbol]  0:
                atm_strike: float = min(strikes, key=lambda x: abs(x-underlying_price))
                itm_strike: float = min(strikes, key=lambda x: abs(x-(underlying_price*min(self.thresholds))))
                otm_strike: float = min(strikes, key=lambda x: abs(x-(underlying_price*max(self.thresholds))))
                
                atm_calls: List[Symbol] = [i for i in contracts if i.ID.OptionRight == OptionRight.Call and 
                                                     i.ID.StrikePrice == atm_strike and 
                                                     self.min_expiry  0 and len(itm_puts) > 0 and len(otm_puts) > 0:
                    # sort by expiry
                    atm_call: List[Symbol] = sorted(atm_calls, key = lambda x: x.ID.Date)[0]
                    itm_put: List[Symbol] = sorted(itm_puts, key = lambda x: x.ID.Date)[0]
                    otm_put: List[Symbol] = sorted(otm_puts, key = lambda x: x.ID.Date)[0]
                    
                    # store expiry date
                    # self.contracts_expiry[symbol] = itm_put.ID.Date.date()
                    self.next_expiry = atm_call.ID.Date
                    # add contracts
                    option: Option = self.AddOptionContract(atm_call, Resolution.Minute)
                    option.PriceModel = OptionPriceModels.CrankNicolsonFD()
                    
                    option: Option = self.AddOptionContract(itm_put, Resolution.Minute)
                    option.PriceModel = OptionPriceModels.CrankNicolsonFD()
                    
                    option: Option = self.AddOptionContract(otm_put, Resolution.Minute)
                    option.PriceModel = OptionPriceModels.CrankNicolsonFD()
                    
                    options: List[Symbol] = [atm_call, itm_put, otm_put]
                    self.option_universe[symbol] = options           
        
        iv_convexity: Dict[Symbol, float] = {} 
        if data.OptionChains.Count != 0:
            for kvp in data.OptionChains:
                chain: OptionChain = kvp.Value
                contracts: List[Symbol] = [x for x in chain]
                if len(contracts) == self.contracts_count:
                    atm_call_iv: Union[None, float] = None
                    itm_put_iv: Union[None, float] = None
                    otm_put_iv: Union[None, float] = None
                    symbol: Symbol = chain.Underlying.Symbol
                    for c in contracts:
                        if c.Right == OptionRight.Call:
                            # found atm call
                            atm_call_iv = c.ImpliedVolatility
                        else:
                            # found put option
                            underlying_price:float = self.Securities[c.UnderlyingSymbol].Price
                            if c.Strike = self.quantile:
            sorted_by_convexity: List[Tuple[Symbol, float]] = sorted(iv_convexity.items(), key = lambda x: x[1], reverse = True)
            quantile: int = int(len(sorted_by_convexity) / self.quantile)
            long = [x[0] for x in sorted_by_convexity[-quantile:]]
            short = [x[0] for x in sorted_by_convexity[:quantile]]
        
        # trade execution
        targets: List[PortfolioTarget] = []
        for i, portfolio in enumerate([long, short]):
            for symbol in portfolio:
                if symbol in data and data[symbol]:
                    targets.append(PortfolioTarget(symbol, ((-1) ** i) / len(portfolio)))
        self.SetHoldings(targets, True)
# custom fee model
class CustomFeeModel(FeeModel):
def GetOrderFee(self, parameters: OrderFeeParameters) -> OrderFee:
    fee: float = parameters.Security.Price * parameters.Order.AbsoluteQuantity * 0.00005
    return OrderFee(CashAmount(fee, "USD"))
