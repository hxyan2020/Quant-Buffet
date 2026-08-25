# Original QuantConnect / library Python
# locale=zh slug="协整加密货币投资组合"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

from AlgorithmImports import *
import numpy as np
import statsmodels.api as sm
#endregion
class CointegratedCryptocurrencyPortfolios(QCAlgorithm):
def Initialize(self):
    self.SetStartDate(2015, 1, 1)
    self.SetCash(100000)
    
    self.cryptos = [
        "BTCUSD", # Bitcoin
        "ETHUSD", # Ethereum
        # "BCHUSD", # Bitcoin cash  # bchusd bitfinex quantconnect price ends in 2018.
        "LTCUSD", # Litecoin
    ]
    
    self.data = {}
    self.spread = []
    
    self.c = 0.5 # Constant for this strategy, however there are other possible values in source paper
    self.period = 21
    
    self.last_day = -1
    self.invested_long = None
    
    self.SetBrokerageModel(BrokerageName.Bitfinex)
    
    for crypto in self.cryptos:
        data = self.AddCrypto(crypto, Resolution.Daily, Market.Bitfinex)
        data.SetFeeModel(CustomFeeModel())
        data.SetLeverage(5)
        
        self.data[crypto] = RollingWindow[float](self.period)
def OnData(self, data):
    if self.last_day == self.Time.day: return
    self.last_day = self.Time.day
    
    for crypto in self.cryptos:
        if crypto in data.Bars:
            if data[crypto]:
                price = data.Bars[crypto].Value
                self.data[crypto].Add(price)
    
    used_cryptos = []            
    bitcoin_prices = None
    other_currencies_prices = []
    for crypto in self.cryptos:
        if not self.data[crypto].IsReady:
            return
        else:
            if crypto is "BTCUSD":
                bitcoin_prices = np.array([x for x in self.data[crypto]])
            else:
                crypto_prices = [x for x in self.data[crypto]]
                
                if not crypto_prices[1:] == crypto_prices[:-1]: # If values in one list aren't same, then it can be use in MultipleLinearRegression
                    other_currencies_prices.append([x for x in self.data[crypto]])
                    used_cryptos.append(crypto)
                    
    if len(other_currencies_prices) == 0:
        self.Liquidate()
        return
    
    regression_model = self.MultipleLinearRegression(other_currencies_prices, bitcoin_prices)
    
    alpha = regression_model.params[0]
    betas = [regression_model.params[index] for index in range(len(regression_model.params)) if index != 0]
    
    beta_index = 0
    current_spread_value = 0
    for crypto in self.cryptos:
        if crypto is "BTCUSD":
            current_spread_value = current_spread_value + self.data[crypto][0]
        elif crypto in used_cryptos:
            current_speard_value = self.data[crypto][0] * betas[beta_index]
            beta_index = beta_index + 1
            
    self.spread.append(current_spread_value)
    
    if len(self.spread)  threshold_short: # short or exit long
            self.InvestShort(betas, used_cryptos)
            self.invested_long = False
    else:
        if current_spread_value  threshold_short and not self.invested_long: # short or exit long
            self.invested_long = False
            self.InvestShort(betas, used_cryptos)
  
def InvestLong(self, betas, used_cryptos):
    beta_index = 0
    for crypto in self.cryptos:
        if self.Portfolio[crypto].Invested:
            self.Liquidate(crypto)
        if crypto is "BTCUSD":
            self.MarketOrder(crypto, 1)
        elif crypto in used_cryptos:
            self.MarketOrder(crypto, betas[beta_index])
            beta_index = beta_index + 1

def InvestShort(self, betas, used_cryptos):
    beta_index = 0
    for crypto in self.cryptos:
        if self.Portfolio[crypto].Invested:
            self.Liquidate(crypto)
        if crypto is "BTCUSD":
            self.MarketOrder(crypto, -1)
        elif crypto in used_cryptos:
            self.MarketOrder(crypto, -betas[beta_index])
            beta_index = beta_index + 1
    
def MultipleLinearRegression(self, x, y):
    x = np.array(x).T
    x = sm.add_constant(x)
    result = sm.OLS(endog=y, exog=x).fit()
    return result  
                        
# Custom fee model.
class CustomFeeModel(FeeModel):
def GetOrderFee(self, parameters):
    fee = parameters.Security.Price * parameters.Order.AbsoluteQuantity * 0.00005
    return OrderFee(CashAmount(fee, "USD"))
