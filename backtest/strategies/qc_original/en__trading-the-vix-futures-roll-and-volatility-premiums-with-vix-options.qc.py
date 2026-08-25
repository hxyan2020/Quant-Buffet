# Original QuantConnect / library Python
# locale=en slug="trading-the-vix-futures-roll-and-volatility-premiums-with-vix-options"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

from AlgorithmImports import *
class TradingTheVIXFuturesRollAndVolatilityPremiumsWithVIXOptions(QCAlgorithm):
def Initialize(self):
    self.SetStartDate(2010, 1, 1)
    self.SetCash(1000000)
    
    self.holding_period = 5         # holding each option contract for n days
    self.trade_percentage = 0.05    # each option contract has 5% of portfolio weight
    
    self.managed_queue = []
    
    index_symbol = self.AddIndex('VIX').Symbol
    option = self.AddIndexOption(index_symbol)
    option.SetFilter(-5, 5, 25, 35)
    self.vix_option_symbol = option.Symbol
    
    self.AddFuture(Futures.Indices.VIX).SetFilter(timedelta(0), timedelta(90))
    
    self.vix_symbol = self.AddData(CBOE, 'VIX').Symbol
    self.vix_price = None
    
    self.symbol = self.AddEquity('SPY', Resolution.Daily).Symbol
    
    self.Schedule.On(self.DateRules.EveryDay(self.symbol), self.TimeRules.AfterMarketOpen(self.symbol), self.Rebalance)
def OnData(self, data):
    # vix data comes each day at 00:00
    if self.vix_symbol in data:
        # get VIX CBOE price
        vix_data = data.Get(CBOE, self.vix_symbol)
        self.vix_price = vix_data.Value
        
    option_chain = data.OptionChains.get(self.vix_option_symbol)
    # check if all needed data are ready
    if option_chain and self.vix_price and data.FuturesChains.Count != 0:
        last_spot_vix_price = self.vix_price
        self.vix_price = None # make sure daily selection
        
        # get contract with nearest expiration
        futures_chain = [x for x in data.FuturesChains.Values][0]
        futures_chain = [c for c in futures_chain.Contracts.Values]
        
        # make sure, there is future contract
        if len(futures_chain) == 0:
            return
        
        nearest_expiration_contract = sorted(futures_chain, key=lambda c: c.Expiry)[0]
        
        last_vix_future_price = nearest_expiration_contract.LastPrice
        
        # get contract expiration and today date
        expiry_date = nearest_expiration_contract.Expiry.date()
        today = self.Time.date()
        
        # calculate days to contract expiration
        days_to_expiration = (expiry_date - today).days
        
        # can't perform division by zero
        if days_to_expiration == 0:
            return
        
        # calculate spread according to strategy description
        spread = (last_vix_future_price - last_spot_vix_price) / days_to_expiration
        
        contract_type = None
        
        # determinate if contract should by put or call type
        if spread  0.10:
            contract_type = 0
        
        # make sure contract type is valid
        if contract_type != None:
            contracts = [contract for contract in option_chain if contract.Right == contract_type]
            # filter ATM contract with latest expiration
            contracts = sorted(contracts, key=lambda contract: abs(option_chain.Underlying.Price - contract.Strike))
            # sort the ATM contracts by their expiration dates
            contracts = sorted(contracts, key=lambda x:x.Expiry, reverse=True)
        
            # make sure there is at least one ATM contract with needed type
            if len(contracts) > 0:
                nearest_expiration_contract = contracts[0]
                # add option contract with it's weight to managed queue
                underlying_symbol = nearest_expiration_contract.UnderlyingSymbol
                self.managed_queue.append(RebalanceItem(nearest_expiration_contract, underlying_symbol))
                    
def Rebalance(self):
    remove_item = None
    
    for rebalance_item in self.managed_queue:
        # trade new contract
        if rebalance_item.holding_period == 0:
            option_contract_symbol = rebalance_item.option_contract.Symbol
            underlying_symbol = rebalance_item.underlying_symbol
            if self.Securities.ContainsKey(option_contract_symbol) and self.Securities.ContainsKey(underlying_symbol):
                if self.Securities[option_contract_symbol].Price != 0 and self.Securities[option_contract_symbol].IsTradable and self.Securities[underlying_symbol].Price != 0:
                    # calculate contract quantity
                    underlying_price = self.Securities[underlying_symbol].Price
                    quantity = self.Portfolio.TotalPortfolioValue / self.holding_period
                    quantity = np.floor((quantity / (underlying_price*100)) * self.trade_percentage)
                    
                    # buy contract
                    self.MarketOrder(option_contract_symbol, quantity)
                    rebalance_item.quantity = quantity
        
        # liquidate option contract
        elif rebalance_item.holding_period == self.holding_period:
            option_contract_symbol = rebalance_item.option_contract.Symbol
            quantity = rebalance_item.quantity
            
            # liquidate only opened positions
            if quantity != 0 and self.Portfolio[option_contract_symbol].Invested:
                self.MarketOrder(option_contract_symbol, -quantity)
                
            remove_item = rebalance_item
            
        rebalance_item.holding_period += 1
    
    # remove liquidated option contract from managed queue    
    if remove_item:
        self.managed_queue.remove(remove_item)
                
class RebalanceItem():
def __init__(self, option_contract, underlying_symbol):
    self.quantity = 0
    self.holding_period = 0
    self.option_contract = option_contract
    self.underlying_symbol = underlying_symbol
# Custom fee model
class CustomFeeModel(FeeModel):
def GetOrderFee(self, parameters):
    fee = parameters.Security.Price * parameters.Order.AbsoluteQuantity * 0.00005
    return OrderFee(CashAmount(fee, "USD"))
