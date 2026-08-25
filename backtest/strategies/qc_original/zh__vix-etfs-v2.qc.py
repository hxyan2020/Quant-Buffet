# Original QuantConnect / library Python
# locale=zh slug="交易vix-etfs-v2"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

from QuantConnect.Python import PythonQuandl
from AlgorithmImports import *
class TradingVIXETFsv2(QCAlgorithm):
def Initialize(self):
    self.SetStartDate(2010, 1, 1)
    self.SetCash(100000)
    self.vixy = self.AddEquity('VIXY', Resolution.Minute).Symbol
    
    # Vix futures data.
    self.vix_future = self.AddFuture(Futures.Indices.VIX, Resolution.Minute)
    # Vix spot.
    self.vix_spot = self.AddData(CBOE, 'VIX', Resolution.Daily).Symbol
    
    self.vix_future.SetFilter(timedelta(0), timedelta(30))
    
    # Vix futures active contract updated on expiration.
    self.active_contract = None
    
    self.Schedule.On(self.DateRules.EveryDay(self.vixy), self.TimeRules.AfterMarketOpen(self.vixy, 1), self.Rebalance)
def Rebalance(self):
    # split data error prevention
    if self.Time.year == 2021 and self.Time.month == 5:
        self.Liquidate()
        return
        
    if self.active_contract:
        if self.Securities.ContainsKey(self.vix_spot):
            spot_price = self.Securities[self.vix_spot].Price
            vix_future_price = self.active_contract.LastPrice
            if spot_price == 0 or vix_future_price == 0: 
                return
            
            relative_basis = vix_future_price / spot_price
            
            # BU 8%, SU 6%, BL -8%, SL -6% thresholds.
            # Short volatility.
            if relative_basis > 1.08:
                if not self.Portfolio[self.vixy].IsShort and self.Securities[self.vixy].Price != 0:
                    self.SetHoldings(self.vixy, -1)
            
            if relative_basis >= 1.06 and relative_basis  0.94:
                if self.Portfolio[self.vixy].Invested:
                    self.Liquidate(self.vixy)
            
            if relative_basis = 0.92 and self.Portfolio[self.vixy].IsShort:
                self.Liquidate(self.vixy)
            
            # Long volatility.
            if not self.Portfolio[self.vixy].IsLong and relative_basis  0:
        cl_chain = chains[0]
    else:
        return
    
    if cl_chain.Value.Contracts.Count >= 1:
        contracts = [i for i in cl_chain.Value]
        contracts = sorted(contracts, key = lambda x: x.Expiry)
        near_contract = contracts[0]
        self.active_contract = near_contract
