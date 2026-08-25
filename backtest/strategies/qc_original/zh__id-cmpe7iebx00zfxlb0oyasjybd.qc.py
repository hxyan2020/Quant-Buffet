# Original QuantConnect / library Python
# locale=zh slug="大宗商品中的波动率风险溢价策略"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

from AlgorithmImports import *
class VolatilityRiskPremiuminCommodities(QCAlgorithm):
def Initialize(self):
    self.SetStartDate(2000, 1, 1)
    self.SetCash(100000)
    
    self.min_expiry = 30
    self.max_expiry = 45
    
    self.symbols = []
    self.contracts = {}
    
    tickers = ['USO', 'GLD', 'UNG']
    
    for ticker in tickers:
        # equity data
        data = self.AddEquity(ticker, Resolution.Daily)
        data.SetLeverage(10)
        data.SetFeeModel(CustomFeeModel())
        
        # change normalization to raw to allow adding etf contracts
        data.SetDataNormalizationMode(DataNormalizationMode.Raw)
        
        self.symbols.append(data.Symbol)
    self.settings.daily_precise_end_time = False
    self.settings.minimum_order_margin_portfolio_percentage = 0.
    self.last_day:int = -1
    self.trade_flag = False
def OnData(self, data):
    # check once a day
    if self.Time.day == self.last_day:
        return
    self.last_day = self.Time.day
    
    # trade option contracts after selection and make sure, they are ready
    if self.trade_flag and data.OptionChains.Count != 0:
        # next rebalance will be after next selection
        self.trade_flag = False
        
        # sell atm straddle of subscribed contracts
        for symbol, contract_obj in self.contracts.items():
            # get call and put contract
            call, put = contract_obj.contracts
            
            # get underlying price
            underlying_price = contract_obj.underlying_price
            
            options_q = int((self.Portfolio.TotalPortfolioValue / len(self.symbols)) / (underlying_price * 100))
            
            self.Sell(call, options_q)
            self.Sell(put, options_q)
            
            # delta hedge
            self.MarketOrder(symbol, options_q*50)
    # check contracs expiration
    for symbol in self.symbols:
        # close trade once option is 
        if symbol in self.contracts and self.contracts[symbol].expiry_date-timedelta(days=1)
