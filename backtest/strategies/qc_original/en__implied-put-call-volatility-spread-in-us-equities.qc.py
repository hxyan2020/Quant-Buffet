# Original QuantConnect / library Python
# locale=en slug="implied-put-call-volatility-spread-in-us-equities"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

from AlgorithmImports import *
from typing import List, Dict
# endregion

class ImpliedPutCallVolatilitySpreadinUSEquities(QCAlgorithm):

def Initialize(self):
    self.SetStartDate(2015, 1, 1)
    self.SetCash(100000)
    
    self.leverage:int = 5
    self.quantile:int = 5

    self.min_contracts:int = 3 # number of nearest options
    self.one_stock_contracts:int = self.min_contracts * 6 # 2 ATM, 2 ITM and 2 OTM options time self.min_contracts expiries

    self.min_expiry:int = 35
    self.max_expiry:int = 360

    self.exchanges:List[str] = ['NYS', 'NAS', 'ASE']

    self.subscribed_options:Dict[str, List[OptionContract]] = {}
    self.symbols_by_tickers:Dict[str, Symbol] = {}
    self.selected_universe:List[Symbol] = []
    self.daily_VS:Dict[str, List[float]] = {}

    self.market:Symbol = self.AddEquity('SPY', Resolution.Daily).Symbol

    self.coarse_count:int = 100
    self.selection_flag:bool = False
    self.UniverseSettings.Resolution = Resolution.Daily
    self.AddUniverse(self.CoarseSelectionFunction, self.FineSelectionFunction)
    self.UniverseSettings.DataNormalizationMode = DataNormalizationMode.Raw
    self.Schedule.On(self.DateRules.MonthStart(self.market), self.TimeRules.BeforeMarketClose(self.market, 0), self.Selection)

def OnSecuritiesChanged(self, changes:SecurityChanges) -> None:
    for security in changes.AddedSecurities:
        security.SetFeeModel(CustomFeeModel())
        security.SetLeverage(self.leverage)

def CoarseSelectionFunction(self, coarse:List[CoarseFundamental]) -> List[Symbol]:
    if not self.selection_flag:
        return Universe.Unchanged
    
    selected:List[CoarseFundamental] = sorted([x for x in coarse if x.HasFundamentalData and x.AdjustedPrice >= 5],
            key=lambda x: x.DollarVolume, reverse=True)[:self.coarse_count]
    
    return list(map(lambda stock: stock.Symbol, selected))

def FineSelectionFunction(self, fine:List[FineFundamental]) -> List[Symbol]:
    fine:List[FineFundamental] = [x.Symbol for x in fine if x.MarketCap != 0 and x.SecurityReference.ExchangeId in self.exchanges]
    self.selected_universe = fine
    return self.selected_universe
    
def OnData(self, data:Slice) -> None:
    # store VS every day
    if len(self.subscribed_options) != 0 and data.OptionChains.Count != 0:
        for kvp in data.OptionChains:
            chain:OptionChain = kvp.Value
            ticker:str = chain.Underlying.Symbol.Value
            if ticker not in self.subscribed_options:
                continue
            
            # calculate VS
            contracts:List[OptionContract] = [x for x in chain]
            sorted_contracts:List[OptionContract] = sorted(contracts, key=lambda item: (item.Right, item.Expiry, item.Strike))
            calls:List[OptionContract] = sorted_contracts[:self.one_stock_contracts // 2]
            puts:List[OptionContract] = sorted_contracts[-self.one_stock_contracts // 2:]

            VS:float = np.sum(np.array(list(map(lambda c_p: (c_p[0].OpenInterest + c_p[1].OpenInterest) / 2, zip(calls, puts)))) * (np.array(list(map(lambda c: c.ImpliedVolatility, calls))) - np.array(list(map(lambda p: p.ImpliedVolatility, puts)))))

            # store VS
            if ticker not in self.daily_VS:
                self.daily_VS[ticker] = []
            self.daily_VS[ticker].append(VS)
            
    if self.selection_flag:
        self.selection_flag = False
        self.Liquidate()

        # VS sort
        monthly_VS:Dict[Symbol, float] = {}
        for ticker, VS_list in self.daily_VS.items():
            if len(VS_list) != 0:
                if ticker in self.symbols_by_tickers:
                    symbol:Symbol = self.symbols_by_tickers[ticker]
                    monthly_VS[symbol] = np.mean(VS_list)
        
        # order execution
        if len(monthly_VS) >= self.quantile:
            quantile:int = len(monthly_VS) // self.quantile
            sorted_by_monthly_VS:List[Symbol] = sorted(monthly_VS, key=monthly_VS.get, reverse=True)
            long_leg:List[Symbol] = sorted_by_monthly_VS[:quantile]
            short_leg:List[Symbol] = sorted_by_monthly_VS[-quantile:]

            for symbol in long_leg:
                self.SetHoldings(symbol, 1 / len(long_leg))

            for symbol in short_leg:
                self.SetHoldings(symbol, -1 / len(short_leg))

        # remove old option contracts
        for ticker in self.subscribed_options:
            for option in self.subscribed_options[ticker]:
                self.RemoveOptionContract(option.Symbol)
        
        # reset last month's data
        self.subscribed_options.clear()
        self.daily_VS.clear()
        self.symbols_by_tickers.clear()

        for symbol in self.selected_universe:
            # subscribe to contract
            contracts:List[Symbol] = self.OptionChainProvider.GetOptionContractList(symbol, self.Time)
            underlying_price:float = self.Securities[symbol].Price
            
            strikes:List[float] = [i.ID.StrikePrice for i in contracts]
            
            if len(strikes) = self.min_contracts for x in [atm_calls, atm_puts, itm_calls, itm_puts, otm_calls, otm_puts]):
                continue
            
            # store stock's symbol under it's ticker, because it is the only possibility how to access it from option contract
            self.symbols_by_tickers[symbol.Value] = symbol

            # sort by expiry and subscribe n nearest contracts
            subscriptions = self.SubscriptionManager.SubscriptionDataConfigService.GetSubscriptionDataConfigs(atm_calls[0].Underlying)
            if subscriptions:
                if self.Securities[symbol].DataNormalizationMode == DataNormalizationMode.Raw:
                    for selected_contracts in [atm_calls, atm_puts, itm_calls, itm_puts, otm_calls, otm_puts]:
                        nearest_contracts:List[Symbol] = sorted(selected_contracts, key=lambda item: item.ID.Date)[:self.min_contracts]

                        for contract in nearest_contracts:
                            option:OptionContract = self.AddOptionContract(contract, Resolution.Daily)
                            option.PriceModel = OptionPriceModels.CrankNicolsonFD()

                            # after trade execution subscribed options will be unsubscribed,
                            # to stop receiving unncessary data, which slows down strategy
                            if symbol.Value not in self.subscribed_options:
                                self.subscribed_options[symbol.Value] = []

                            self.subscribed_options[symbol.Value].append(option)

def select_contracts(self, contracts:List[Symbol], option_right:int, strike:float) -> List:
    return [i for i in contracts if i.ID.OptionRight == option_right \
        and i.ID.StrikePrice == strike and self.min_expiry  None:
    self.selection_flag = True

# Custom fee model
class CustomFeeModel(FeeModel):
def GetOrderFee(self, parameters):
    fee = parameters.Security.Price * parameters.Order.AbsoluteQuantity * 0.00005
    return OrderFee(CashAmount(fee, "USD"))
