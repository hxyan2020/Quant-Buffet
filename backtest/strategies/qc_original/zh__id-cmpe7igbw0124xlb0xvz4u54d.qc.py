# Original QuantConnect / library Python
# locale=zh slug="押注正确的半贝塔多头与空头"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

from AlgorithmImports import *
from data_tools import CustomFeeModel, SymbolData
# endregion
class BettingOnAndAgainstTheRightSemibetas(QCAlgorithm):
def Initialize(self) -> None:
    self.SetStartDate(2015, 1, 1)
    self.SetCash(100_000)
    
    self.leverage:int = 5
    self.quantile:int = 10
    self.min_share_price:int = 5
    self.neg_beta_trade_flag:bool = False
    self.pos_beta_trade_flag:bool = True
    self.portfolio_parts:int = 2 if self.neg_beta_trade_flag and self.pos_beta_trade_flag else 1
    self.period:int = 26
    self.minutes_interval:int = 15
    self.trade_hour:int = 15
    self.trade_minute:int = 45
    
    self.data:dict[Symbol, SymbolData] = {}
    self.market_symbol:Symbol = self.AddEquity('SPY', Resolution.Minute).Symbol
    self.market_data:Symbol = SymbolData(self.period, None)
    MarketOnCloseOrder.SubmissionTimeBuffer = timedelta(minutes=15)
    self.fundamental_count:int = 500
    self.fundamental_sorting_key = lambda x: x.DollarVolume
    self.UniverseSettings.Leverage = self.leverage
    self.UniverseSettings.Resolution = Resolution.Minute
    self.AddUniverse(self.FundamentalSelectionFunction)
    self.settings.daily_precise_end_time = False
    self.Settings.MinimumOrderMarginPortfolioPercentage = 0.
def OnSecuritiesChanged(self, changes: SecurityChanges) -> None:
    for security in changes.AddedSecurities:
        security.SetFeeModel(CustomFeeModel())
        # security.SetLeverage(self.leverage)
def FundamentalSelectionFunction(self, fundamental: List[Fundamental]) -> List[Symbol]:
    selected:list = [
        x for x in fundamental 
        if x.HasFundamentalData 
        and x.Market == 'usa' and 
        x.Price > self.min_share_price
    ]
    if len(selected) > self.fundamental_count:
        selected = [x for x in sorted(selected, key=self.fundamental_sorting_key, reverse=True)[:self.fundamental_count]]
    self.data.clear()
    self.market_data = SymbolData(self.period, None)
    for stock in selected:
        market_cap:float = stock.MarketCap
        if market_cap == 0:
            continue
        symbol:Symbol = stock.Symbol
        self.data[symbol] = SymbolData(self.period, market_cap)
    return list(self.data.keys())
    
def OnData(self, data: Slice) -> None:
    # NOTE: first price comes at 9:31 not at 9:30, when market opens
    if (self.Time.hour != 0 and self.Time.hour != 16) and ((self.Time.minute % self.minutes_interval == 0) or (self.Time.hour == 9 and self.Time.minute == 31)) \
        and not(self.Time.hour >= self.trade_hour and self.Time.minute > self.trade_minute): 
        self.UpdateData(data)
    if self.Time.hour == self.trade_hour and self.Time.minute == self.trade_minute:
        self.UpdateData(data)
        self.Liquidate()
        if not self.market_data.performances_ready():
            return
        market_positive_vector, market_negative_vector = self.market_data.get_vectors()
        sum_pow_neg_market_vect:float = sum(np.power(market_negative_vector, 2))
        if sum_pow_neg_market_vect == 0:
            return
        negative_semibeta:dict[Symbol, float] = {}
        positive_semibeta:dict[Symbol, float] = {}
        for symbol, symbol_data in self.data.items():
            if not symbol_data.performances_ready():
                continue
            _, stock_negative_vector = symbol_data.get_vectors()
            negative_semibeta_value:float = sum(stock_negative_vector * market_negative_vector) / sum_pow_neg_market_vect
            positive_semibeta_value:float = sum(stock_negative_vector * market_positive_vector) / sum_pow_neg_market_vect
            if negative_semibeta_value != 0:
                negative_semibeta[symbol] = negative_semibeta_value
            
            if positive_semibeta_value != 0:
                positive_semibeta[symbol] = positive_semibeta_value
        if len(negative_semibeta)  None:
    for symbol, symbol_data in self.data.items():
        if symbol in data and data[symbol]:
            price:float = data[symbol].Value
            if symbol_data.prev_price_ready():
                symbol_data.update_performances(price)
            symbol_data.set_prev_price(price)
    if data.ContainsKey(self.market_symbol):
        price:float = data[self.market_symbol].Value
        if self.market_data.prev_price_ready():
            self.market_data.update_performances(price)
        self.market_data.set_prev_price(price)
def PerformTrade(self, weight:float, symbols:list, long_flag:bool) -> None:
    total_cap:float = sum(list(map(lambda symbol: self.data[symbol].get_market_cap(), symbols)))
    for symbol in symbols:
        market_cap:float = self.data[symbol].get_market_cap()
        price:float = self.data[symbol].get_prev_price() # prev price is currently the latest one
        quantity:int = np.floor((weight * (market_cap / total_cap)) / price)
        quantity = quantity if long_flag else -quantity
        self.MarketOnCloseOrder(symbol, quantity)
        # holding_value:float = market_cap / total_cap if long_flag else -market_cap / total_cap
        # self.SetHoldings(symbol, holding_value / self.portfolio_parts)
