# Original QuantConnect / library Python
# locale=en slug="rebalancing-premium-in-cryptocurrencies-2"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

from AlgorithmImports import *

class RebalancingPremiumInCryptocurrencies(QCAlgorithm):

def Initialize(self):
    self.SetStartDate(2015, 1, 1)
    self.SetCash(100000000)
    
    self.cryptos = [
        "BTCUSD", 
        "BATUSD", 
        # "BTGUSD", 
        "DAIUSD",
        "DGBUSD", "EOSUSD",
        "ETHUSD", "FUNUSD",
        "LTCUSD", "NEOUSD",
        "OMGUSD", "SNTUSD",
        "TRXUSD", "XLMUSD",
        "XMRUSD", "XRPUSD",
        "XVGUSD", "ZECUSD",
        "ZRXUSD", "LRCUSD",
        "REQUSD", "SANUSD",
        "WAXUSD", "ZILUSD",
        "IOTAUSD", 
        "MANAUSD",
        "DATAUSD"
    ]

    self.short_side_percentage = 0.7
    self.data = {}
    self.SetBrokerageModel(BrokerageName.Bitfinex)
    
    for crypto in self.cryptos:
        # GDAX is coinmarket, but it doesn't support this many cryptos, so we choose Bitfinex
        data = self.AddCrypto(crypto, Resolution.Minute, Market.Bitfinex)
        data.SetFeeModel(CustomFeeModel())
        data.SetLeverage(10)
        
        self.data[crypto] = SymbolData()

    self.was_traded_already = False         # wait for the price data to come only once
    self.prev_short_portfolio_equity = 0    # short leg equity tracking

def OnData(self, data):
    if not (self.Time.hour == 9 and self.Time.minute == 30):
        return
    
    all_cryptos_are_ready = True       # data warmup flag

    # check if all cryptos has ready data
    for crypto in self.cryptos:
        if crypto in data and data[crypto]:
            # update crypto price for weight calculation
            self.data[crypto].last_price = data[crypto].Value
        # if there is at least one crypto, which doesn't have data, then don't trade and break cycle
        else:
            all_cryptos_are_ready = False
            break
    
    if all_cryptos_are_ready or self.was_traded_already:
        self.was_traded_already = True
        
        # long strategy equity calculation
        long_portfolio_equity = self.Portfolio.TotalPortfolioValue
        long_equity_to_trade = long_portfolio_equity / len(self.cryptos)
        
        # short strategy equity calculation
        short_portfolio_equity = self.Portfolio.TotalPortfolioValue * self.short_side_percentage
        short_equity_to_trade = short_portfolio_equity / len(self.cryptos)

        # trading/rebalance
        for crypto, symbol_obj in self.data.items():
            if crypto in data and data[crypto]:
                # short strategy
                if not self.Portfolio[crypto].Invested:
                    short_q = np.floor(short_equity_to_trade / symbol_obj.last_price)
                    if abs(short_q) >= self.Securities[crypto].SymbolProperties.MinimumOrderSize:
                        self.MarketOrder(crypto, -short_q)

                # long strategy
                long_q = np.floor(long_equity_to_trade / symbol_obj.last_price)
                # currency was traded before
                if symbol_obj.quantity is not None:
                    # calculate quantity difference
                    diff_q = long_q - symbol_obj.quantity
                
                    # rebalance position
                    if abs(diff_q) >= self.Securities[crypto].SymbolProperties.MinimumOrderSize:
                        self.MarketOrder(crypto, diff_q)
                        
                        # change new quantity
                        symbol_obj.quantity += diff_q
                else:
                    # rebalance position
                    if abs(long_q) >= self.Securities[crypto].SymbolProperties.MinimumOrderSize:
                        self.MarketOrder(crypto, long_q)
                    
                        # change new quantity
                        symbol_obj.quantity = long_q

class SymbolData():
def __init__(self):
    self.last_price = None
    self.quantity = None

# Custom fee model.
class CustomFeeModel(FeeModel):
def GetOrderFee(self, parameters):
    fee = parameters.Security.Price * parameters.Order.AbsoluteQuantity * 0.00005
    return OrderFee(CashAmount(fee, "USD"))
