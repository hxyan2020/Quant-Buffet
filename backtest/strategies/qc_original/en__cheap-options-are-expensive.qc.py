# Original QuantConnect / library Python
# locale=en slug="cheap-options-are-expensive"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

from AlgorithmImports import *
from typing import List, Dict, Tuple
#endregion
class CheapOptionsAreExpensive(QCAlgorithm):
def Initialize(self):
    self.SetStartDate(2016, 1, 1)
    self.SetCash(1000000)
    
    self.min_expiry: int = 35
    self.max_expiry: int = 60
    self.leverage: int = 5
    self.min_share_price: int = 5
    self.subscribed_contracts_treshold: int = 10
    self.quantile: int = 10
    
    self.subscribed_contracts: Dict[str, Symbol] = {}
    self.tickers_symbols: Dict[str, Symbol] = {}
    
    self.day: int = -1
    self.fundamental_count: int = 100
    self.fundamental_sorting_key = lambda x: x.DollarVolume
    self.opened_position_with_expiry: List[Tuple[Symbol, Symbol, datetime.date]] = []   # stock symbol, contract symbol, option expiry
    self.settings.daily_precise_end_time = False
    self.Settings.MinimumOrderMarginPortfolioPercentage = 0.
    self.UniverseSettings.Resolution = Resolution.Minute
    self.AddUniverse(self.FundamentalSelectionFunction)
    self.SetSecurityInitializer(lambda x: x.SetDataNormalizationMode(DataNormalizationMode.Raw))
    self.UniverseSettings.DataNormalizationMode = DataNormalizationMode.Raw
def OnSecuritiesChanged(self, changes: SecurityChanges) -> None:
    for security in changes.AddedSecurities:
        security.SetFeeModel(CustomFeeModel())
        security.SetLeverage(self.leverage)
def FundamentalSelectionFunction(self, fundamental: List[Fundamental]) -> List[Symbol]:
    # rebalance on contract expirations
    if len(self.tickers_symbols) != 0:
        return Universe.Unchanged
    
    # select top n stocks by dollar volume with price higher than 5
    selected: List[Fundamental] = [
        x for x in fundamental 
        if x.HasFundamentalData 
        and x.Market == 'usa' 
        and x.Price > self.min_share_price
    ]
    if len(selected) > self.fundamental_count:
        selected = [x for x in sorted(selected, key=self.fundamental_sorting_key, reverse=True)[:self.fundamental_count]]
    self.tickers_symbols = {x.Symbol.Value: x.Symbol for x in selected}
    
    # return symbols of selected stocks
    return [x.Symbol for x in selected]
    
def OnData(self, data: Slice) -> None:
    # on next DataBar(1 minute after subscription) after contracts subscription trade selected contracts and their stocks
    if len(self.subscribed_contracts) >= self.subscribed_contracts_treshold:
        stock_prices: Dict[str, float] = {} # storing stock prices keyed by atm call contracts
        
        for ticker, contract_symbol in self.subscribed_contracts.items():
            if ticker in self.tickers_symbols:
                stock_symbol: Symbol = self.tickers_symbols[ticker]
                # make sure, there are DataBars for stock and atm contract
                if stock_symbol in data and data[stock_symbol] and contract_symbol in data and data[contract_symbol]:
                    underlying_price: float = data[stock_symbol].Value
                    # store stock underlying price keyed by ticker
                    stock_prices[ticker] = underlying_price
        traded: bool = False
        # make sure, there are enough data for quantile selection
        if len(stock_prices) >= self.quantile:
            # sorting by underlying stock price
            quantile: int = int(len(stock_prices) / self.quantile)
            sorted_by_price = sorted(stock_prices.items(), key = lambda x: x[1], reverse=True)
            long: List[Symbol] = sorted_by_price[:quantile]
            short: List[Symbol] = sorted_by_price[-quantile:]
            
            long_w: float = 1 / len(long)
            short_w: float = 1 / len(short)
            
            for ticker, price in long:
                # retrieve atm contract symbol based on ticker
                contract_symbol: Symbol = self.subscribed_contracts[ticker]
                # retrieve stock symbol based on ticker
                stock_symbol: Symbol = self.tickers_symbols[ticker]
                
                equity: float = self.Portfolio.TotalPortfolioValue * long_w
                options_q: int = int(equity / (price * 100))
                # buy contract
                self.Securities[contract_symbol].MarginModel = BuyingPowerModel(2)
                if contract_symbol in data and data[contract_symbol] and stock_symbol in data and data[stock_symbol]:
                    self.Buy(contract_symbol, options_q)
                    self.Sell(stock_symbol,options_q * 50)  # initial delta hedge
                
                    self.opened_position_with_expiry.append((stock_symbol, contract_symbol, contract_symbol.ID.Date.date()))
                    traded = True

            for ticker, price in short:
                # retrieve atm contract symbol based on ticker
                contract_symbol = self.subscribed_contracts[ticker]
                # retrieve stock symbol based on ticker
                stock_symbol = self.tickers_symbols[ticker]
                
                equity = self.Portfolio.TotalPortfolioValue * short_w
                options_q = int(equity / (price * 100))
                # sell contract
                self.Securities[contract_symbol].MarginModel = BuyingPowerModel(2)
                if contract_symbol in data and data[contract_symbol] and stock_symbol in data and data[stock_symbol]:
                    self.Sell(contract_symbol, options_q)
                    self.Buy(stock_symbol, options_q * 50)  # initial delta hedge
                    
                    self.opened_position_with_expiry.append((stock_symbol, contract_symbol, contract_symbol.ID.Date.date()))
                    traded = True
        
        if traded:
            # clear dictionary and wait for next selection and contracts subscription    
            self.subscribed_contracts.clear()
    
    # check if contracts expiries once in a day
    if self.day == self.Time.day:
        return
    self.day = self.Time.day
    
    # positions are opened
    if len(self.opened_position_with_expiry) != 0:
        positions_to_remove: List[Tuple[Symbol, Symbol, datetime.date]] = []
        for opened_position_with_expiry in self.opened_position_with_expiry:
            stock_symbol: Symbol = opened_position_with_expiry[0]
            contract_symbol: Symbol = opened_position_with_expiry[1]
            exp: datetime.date = opened_position_with_expiry[2]
            if exp  0:
                # sort by expiry
                atm_call: Symbol = sorted(atm_calls, key = lambda item: item.ID.Date, reverse=True)[0]
                
                # add contract
                option: Option = self.AddOptionContract(atm_call, Resolution.Minute)
                option.SetDataNormalizationMode(DataNormalizationMode.Raw)
                
                # store subscribed atm call contract keyed by it's ticker
                self.subscribed_contracts[atm_call.Underlying.Value] = atm_call
    else:
        if len(self.opened_position_with_expiry) == 0:
            self.Liquidate()
            
# Custom fee model.
class CustomFeeModel(FeeModel):
def GetOrderFee(self, parameters: OrderFeeParameters) -> OrderFee:
    fee: float = parameters.Security.Price * parameters.Order.AbsoluteQuantity * 0.00005
    return OrderFee(CashAmount(fee, "USD"))
