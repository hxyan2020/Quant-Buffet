# Original QuantConnect / library Python
# locale=en slug="dynamic-crude-oil-allocation-in-a-balanced-portfolio"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

from AlgorithmImports import *
import data_tools
#endregion
class DynamicCrudeOilAllocationinaBalancedPortfolio(QCAlgorithm):
def Initialize(self) -> None:
    self.SetStartDate(2009, 1, 1)
    self.SetCash(100_000)
    self.min_expiration_days: int = 2
    self.max_expiration_days: int = 360
    
    self.us_market: str = 'CME_ES1'   # E-mini S&P 500 Futures, Continuous Contract
    self.treasuries: str = 'CME_TY1'  # 10 Yr Note Futures, Continuous Contract
    self.oil: str = 'CME_CL1'         # Crude Oil Futures, Continuous Contract
    self.tickers:list[str] = [
        self.us_market,
        self.treasuries,
        self.oil
    ]
    for symbol in self.tickers:
        data: Security = self.AddData(data_tools.QuantpediaFutures, symbol, Resolution.Daily)
        data.SetFeeModel(data_tools.CustomFeeModel())
        data.SetLeverage(5)
    # QC Crude Oil future
    future: Future = self.AddFuture(Futures.Energies.CrudeOilWTI, Resolution.Daily, dataNormalizationMode=DataNormalizationMode.Raw)
    future.SetFilter(timedelta(days=self.min_expiration_days), timedelta(days=self.max_expiration_days))
    self.future_data: FuturesData = data_tools.FuturesData()
    self.crude_oil_futures_ticker: str = future.Symbol.Value
    
    self.last_update_date: None|datetime.date = None
    self.was_contango_before: bool = False   # flag to reduce trading and fees
def FindAndUpdateContracts(self, futures_chain) -> None:
    near_contract: None|FuturesContract = None
    dist_contract: None|FuturesContract = None
    if self.crude_oil_futures_ticker in futures_chain:
        contracts: List[FuturesContract] = [contract for contract in futures_chain[self.crude_oil_futures_ticker] if contract.Expiry.date() > self.Time.date()]
        if len(contracts) >= 2:
            contracts: List[FuturesContract] = sorted(contracts, key=lambda x: x.Expiry, reverse=False)
            near_contract = contracts[0]
            dist_contract = contracts[1]
    self.future_data.update_contracts(near_contract, dist_contract) 
    
def OnData(self, data: Slice) -> None:
    curr_date: datetime.date = self.Time.date()
    # handle missing data
    if any([self.securities[symbol].get_last_data() and self.time.date() > data_tools.QuantpediaFutures.get_last_update_date()[symbol] for symbol in self.tickers]):
        self.liquidate()
        return
    if data.FutureChains.Count > 0:
        if not self.future_data.is_initialized() or (self.future_data.is_initialized() and self.future_data.near_contract.Expiry.date() == curr_date):
            self.FindAndUpdateContracts(data.FutureChains)
        # update QC futures rolling return
        if self.future_data.is_initialized():
            near_c: FuturesContract = self.future_data.near_contract
            dist_c: FuturesContract = self.future_data.distant_contract
            if near_c.Symbol in data and data[near_c.Symbol] and dist_c.Symbol in data and data[dist_c.Symbol]:
                n_price: float = data[near_c.Symbol].Value * self.Securities[self.crude_oil_futures_ticker].SymbolProperties.PriceMagnifier
                d_price: float = data[dist_c.Symbol].Value * self.Securities[self.crude_oil_futures_ticker].SymbolProperties.PriceMagnifier
                contango: bool = d_price > n_price
            
                if not contango:
                    # Allocate 30% in E-Mini S&P 500 futures, 30% in Brent futures, and 40% in 10-Year Treasury futures if the previous 
                    # trading day’s Brent front-month-to-back-month spread is trading at a premium (backwardation).
                    self.SetHoldings(self.us_market, 0.3)
                    self.SetHoldings(self.oil, 0.3)
                    self.SetHoldings(self.treasuries, 0.4)
                    
                    self.was_contango_before = False
                else:
                    # market was in backwardation last time
                    if not self.was_contango_before:
                        self.Liquidate(self.oil)
                    
                    # Otherwise (contango), allocate 60% in E-Mini S&P 500 futures and 40% in 10-Year Treasury futures.
                    self.SetHoldings(self.us_market, 0.6)
                    self.SetHoldings(self.treasuries, 0.4)
                    
                    self.was_contango_before = True
