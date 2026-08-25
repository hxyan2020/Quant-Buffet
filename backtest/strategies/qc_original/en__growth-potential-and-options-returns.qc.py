# Original QuantConnect / library Python
# locale=en slug="growth-potential-and-options-returns"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

from AlgorithmImports import *
from numpy import isnan
class GrowthPotentialandOptionsReturns(QCAlgorithm):
def Initialize(self):
    self.SetStartDate(2010, 1, 1)
    self.SetCash(10_000_000)
    self.min_expiry: int = 20
    self.max_expiry: int = 30
    
    self.fundamental_count: int = 200
    self.fundamental_sorting_key = lambda x: x.DollarVolume
    self.subscribed_contracts: Dict[Symbol, Symbol] = {}
    
    self.period: int = 36 * 21
    self.percentage_traded: float = .01
    self.min_share_price: int = 5
    self.quantile: int = 5
    self.leverage: int = 40
    
    self.long_symbols: List[Symbol] = []
    self.short_symbols: List[Symbol] = []
        
    self.market: Symbol = self.AddEquity('SPY', Resolution.Minute).Symbol
    self.market_prices: RollingWindow = RollingWindow[float](self.period)
    
    self.recent_stock_price: Dict[Symbol, float] = {}            # whole stock universe recent adjusted prices
    self.recent_market_cap: Dict[Symbol, float] = {}             # currently selected universe market cap
    self.last_expiration_date: Union[None, datetime.date] = None # last expiry date of currently selected traded option universe 
    
    self.trade_flag: bool = False
    self.selection_flag: bool = False   
    self.UniverseSettings.Leverage = self.leverage
    self.UniverseSettings.Resolution = Resolution.Minute
    self.AddUniverse(self.FundamentalSelectionFunction)
    self.settings.daily_precise_end_time = False
    self.Settings.MinimumOrderMarginPortfolioPercentage = 0.
    self.SetSecurityInitializer(lambda x: x.SetDataNormalizationMode(DataNormalizationMode.Raw))
    self.UniverseSettings.DataNormalizationMode = DataNormalizationMode.Raw
def OnSecuritiesChanged(self, changes: SecurityChanges) -> None:
    for security in changes.AddedSecurities:
        security.SetFeeModel(CustomFeeModel())
        # security.SetMarketPrice(self.GetLastKnownPrice(security))
        
def FundamentalSelectionFunction(self, fundamental: List[Fundamental]) -> List[Symbol]:
    # store daily recent currently selected universe prices and SPY market price
    for stock in fundamental:
        symbol: Symbol = stock.Symbol
        # store market price history
        if symbol == self.market:
            self.market_prices.Add(stock.AdjustedPrice)
        else:
            # store recent stock price
            self.recent_stock_price[symbol] = stock.AdjustedPrice
            
    if self.last_expiration_date is not None and not self.trade_flag:
        # rebalance after every already traded option expired
        if self.last_expiration_date = self.min_share_price 
        and x.MarketCap != 0 
        and not isnan(x.FinancialStatements.CashFlowStatement.OperatingCashFlow.ThreeMonths) and x.FinancialStatements.CashFlowStatement.OperatingCashFlow.ThreeMonths != 0 
        and not isnan(x.FinancialStatements.BalanceSheet.TotalLiabilitiesAsReported.ThreeMonths) and x.FinancialStatements.BalanceSheet.TotalLiabilitiesAsReported.ThreeMonths != 0
    ]
    GO: Dict[Symbol, float] = {}
    for stock in selected:
        symbol: Symbol = stock.Symbol
        
        # calculate GO
        market_avg_perf: float = pd.Series([x for x in self.market_prices]).pct_change().dropna().mean()
        
        v: float = stock.MarketCap + stock.FinancialStatements.BalanceSheet.TotalLiabilitiesAsReported.ThreeMonths
        go_value: float = (v - (stock.FinancialStatements.CashFlowStatement.OperatingCashFlow.ThreeMonths / market_avg_perf))
        self.recent_market_cap[symbol] = stock.MarketCap
        GO[symbol] = go_value
    
    if len(GO)  None:
    if self.trade_flag:
        self.trade_flag = False
        
        long_count: int = len(self.long_symbols)
        short_count: int = len(self.short_symbols)
        
        if long_count == 0 or short_count == 0:
            return
        long_total_mc: float = sum([self.recent_market_cap[x] for x in self.long_symbols])
        short_total_mc: float = sum([self.recent_market_cap[x] for x in self.short_symbols])
    
        # trade execution
        for symbol in self.short_symbols + self.long_symbols:
            # atm call option contract of current stock might not be subscribed
            if symbol not in self.subscribed_contracts:
                continue
            
            # get atm call contract based on ticker
            atm_call: Symbol = self.subscribed_contracts[symbol]
            
            # make sure subscribed atm call option has data
            if slice.contains_key(atm_call) and slice[atm_call] and slice.contains_key(symbol) and slice[symbol]:
                stock_price: float = self.recent_stock_price[symbol] if symbol in self.recent_stock_price else .0
                
                if stock_price != 0:
                    if symbol in self.short_symbols:
                        # calculate atm call quantity
                        w: float = self.recent_market_cap[symbol] / long_total_mc
                        option_quantity: float = (self.Portfolio.TotalPortfolioValue * w * self.percentage_traded) / (stock_price*100)
                        if option_quantity  self.last_expiration_date else self.last_expiration_date) if self.last_expiration_date is not None else expiry
        
    # rebalance monthly
    if not self.selection_flag:
        return
    
    self.selection_flag = False
    self.subscribed_contracts.clear()
    
    # subscribe to stocks contracts
    for symbol in self.short_symbols + self.long_symbols:
        if symbol not in self.recent_stock_price:
            continue
        
        # subscribe to contract
        contracts: List[Symbol] = self.OptionChainProvider.GetOptionContractList(symbol, self.Time)
        
        # get current price for stock
        underlying_price: float = self.recent_stock_price[symbol]
        
        # get strikes from stock contracts
        strikes: List[float] = [i.ID.StrikePrice for i in contracts]
        
        # check if there is at least one strike    
        if len(strikes)  0:
            # sort by expiry
            atm_call: Symbol = sorted(atm_calls, key = lambda item: item.ID.Date, reverse=True)[0]
            subscriptions = self.SubscriptionManager.SubscriptionDataConfigService.GetSubscriptionDataConfigs(atm_call.Underlying)
            if subscriptions:
                option: Option = self.AddOptionContract(atm_call, Resolution.Minute, leverage=self.leverage)
                option.PriceModel = OptionPriceModels.crank_nicolson_fd()
                # store subscribed atm call contract keyed by it's ticker
                self.subscribed_contracts[atm_call.Underlying] = atm_call
        
    self.trade_flag = True
    if self.Portfolio.Invested:
        self.Liquidate()
    
# custom fee model
class CustomFeeModel(FeeModel):
def GetOrderFee(self, parameters: OrderFeeParameters) -> OrderFee:
    fee: float = parameters.Security.Price * parameters.Order.AbsoluteQuantity * 0.00005
    return OrderFee(CashAmount(fee, "USD"))
