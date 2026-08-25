# Original QuantConnect / library Python
# locale=en slug="期权交易与52周高点相比的回报"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

from AlgorithmImports import *
import data_tools
# endregion

class OptionTradingandReturnsversusthe52WeekHigh(QCAlgorithm):

def Initialize(self):
    self.SetStartDate(2010, 1, 1)
    self.SetCash(100000)

    self.leverage:int = 5
    self.quantile:int = 5
    self.portfolio_percentage:float = 1
    self.high_period:int = 52 * 5

    self.exchanges:list[str] = ['NYS', 'NAS', 'ASE']

    self.data:dict[Symbol, data_tools.SymbolData] = {}

    self.selected_symbols:list[Symbol] = []
    self.highest_PTH:List[Symbol] = []
    self.lowest_PTH:List[Symbol] = []

    self.market_symbol:Symbol = self.AddEquity('SPY', Resolution.Daily).Symbol

    # options storage
    self.min_expiry:int = 30
    self.max_expiry:int = 60
    self.subscribed_contracts:dict = {}      # subscribed option universe

    self.coarse_count:int = 500
    self.selection_flag:bool = False
    self.UniverseSettings.Resolution = Resolution.Daily
    self.AddUniverse(self.CoarseSelectionFunction)
    self.SetSecurityInitializer(lambda x: x.SetDataNormalizationMode(DataNormalizationMode.Raw))
    self.UniverseSettings.DataNormalizationMode = DataNormalizationMode.Raw

    self.Schedule.On(self.DateRules.MonthStart(self.market_symbol), self.TimeRules.BeforeMarketClose(self.market_symbol, 0), self.Selection)

def OnSecuritiesChanged(self, changes: SecurityChanges) -> None:
    for security in changes.AddedSecurities:
        security.SetFeeModel(data_tools.CustomFeeModel())
        security.SetLeverage(self.leverage)
        
        symbol:Symbol = security.Symbol
        if symbol not in self.data:
            self.data[symbol] = data_tools.SymbolData(self.high_period)
    
    for security in changes.RemovedSecurities:
        symbol:Symbol = security.Symbol
        if symbol in self.data:
            del self.data[symbol]

def CoarseSelectionFunction(self, coarse:List[CoarseFundamental]) -> List[Symbol]:
    if not self.selection_flag:
        return Universe.Unchanged
    
    selected:list = sorted([x for x in coarse if x.HasFundamentalData and x.Market == 'usa' and x.Price > 5],
        key=lambda x: x.DollarVolume, reverse=True)[:self.coarse_count]
    
    self.selected_symbols = list(map(lambda stock: stock.Symbol, selected))

    return self.selected_symbols
    
def OnData(self, data:Slice) -> None:
    if self.highest_PTH and self.lowest_PTH:
        oi_by_symbol:dict[Symobl, float] = {}

        # for each stock in the highest quintile, buy one call option and delta-hedge in the next month with daily rebalancing. Conversely, for each stock in the lowest quintile, sell one call option and delta-hedge in the next month.
        if self.subscribed_contracts:
            # store OI values
            if data.OptionChains.Count != 0:
                for kvp in data.OptionChains:
                    contract = list(kvp.Value)[0]
                    symbol:Symbol = contract.UnderlyingSymbol
                    open_interest:float = contract.OpenInterest

                    if open_interest != 0:
                        oi_by_symbol[symbol] = open_interest

            # trade options and hedge
            total_oi:float = sum([oi_by_symbol[x] for x in self.highest_PTH if x in oi_by_symbol])
            for symbol in self.highest_PTH:
                if symbol in data and data[symbol]:
                    if symbol in self.subscribed_contracts:
                        if symbol in oi_by_symbol:
                            price:float = data[symbol].Value
                            weight:float = oi_by_symbol[symbol] / total_oi
                            
                            equity:float = self.Portfolio.TotalPortfolioValue * weight
                            options_q:int = int(equity / (price * 100))

                            self.Buy(self.subscribed_contracts[symbol], options_q)
                            
            total_oi:float = sum([oi_by_symbol[x] for x in self.lowest_PTH if x in oi_by_symbol])
            for symbol in self.lowest_PTH:
                if symbol in data and data[symbol]:
                    if symbol in self.subscribed_contracts:
                        if symbol in oi_by_symbol:
                            price:float = data[symbol].Value
                            weight:float = oi_by_symbol[symbol] / total_oi
                            
                            equity:float = self.Portfolio.TotalPortfolioValue * weight
                            options_q:int = int(equity / (price * 100))

                            self.Sell(self.subscribed_contracts[symbol], options_q)
                            
        self.subscribed_contracts.clear()
        self.highest_PTH.clear()
        self.lowest_PTH.clear()

    # store daily prices
    for symbol in self.selected_symbols:
        if symbol in self.data:
            if symbol in data and data[symbol] and data[symbol].High != 0 and data[symbol].Value != 0:
                price:float = data[symbol].Value
                high:float = data[symbol].High

                self.data[symbol].update(price, high)

    # rebalance monthly
    if not self.selection_flag:
        return
    self.selection_flag = False

    # calculate PTH
    PTH:dict[Symbol, float] = { symbol : self.data[symbol].PTH() for symbol in self.selected_symbols if symbol in self.data and self.data[symbol].PTH_data_ready() }

    if len(PTH)  0:
                # sort by expiry
                atm_call = sorted(atm_calls, key = lambda x: x.ID.Date, reverse=True)[0]
                
                atm_call_subscriptions = self.SubscriptionManager.SubscriptionDataConfigService.GetSubscriptionDataConfigs(atm_call.Underlying)
                
                # check if stock's call contract was successfully subscribed
                if atm_call_subscriptions:
                    # add contract
                    option = self.AddOptionContract(atm_call, Resolution.Daily)
                    option.PriceModel = OptionPriceModels.CrankNicolsonFD()

                    # store contracts by stock's symbol
                    self.subscribed_contracts[symbol] = atm_call

def Selection(self) -> None:
    self.selection_flag = True
    self.Liquidate()
