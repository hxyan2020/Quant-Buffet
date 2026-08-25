# Original QuantConnect / library Python
# locale=en slug="growth-of-addresses-with-balance-factor-in-cryptos"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

from AlgorithmImports import *
from typing import List, Dict
#endregion

import data_tools

class CrosssectionalMomentumInLargeCryptos(QCAlgorithm):

def Initialize(self) -> None:
    self.SetStartDate(2015, 1, 1)
    self.SetCash(1_000_000)
    
    self.period: int = 7         # need n of daily addresses
    self.quantile: int = 5
    self.portfolio_percentage: float = .1
    self.leverage: int = 10

    self.cryptos: List[str] = [
        "ANT",  # Aragon
        "BAT",  # Basic Attention Token
        "BTC",  # Bitcoin
        "DAI",  # Dai
        "DASH", # Dash
        "DOGE", # Dogecoin
        "EOS",  # EOS
        "ETH",  # Ethereum
        "FUN",  # FUN Token
        "LTC",  # Litecoin
        "MKR",  # Maker
        "OMG",  # OMG Network
        "SNT",  # Status
        "ZEC",  # Zcash
        "ZRX"   # Ox
    ]
    
    self.data: Dict[str, data_tools.SymbolData] = {}
    self.weight: Dict[str, float] = {}
    self.SetBrokerageModel(BrokerageName.Bitfinex)
    
    for crypto in self.cryptos:
        crypto_symbol: str = crypto + 'USD'
        data: Securities = self.AddCrypto(crypto_symbol, Resolution.Daily, Market.Bitfinex)
        data.SetLeverage(self.leverage)
        
        network_symbol: Symbol = self.AddData(data_tools.CryptoNetworkData, crypto, Resolution.Daily).Symbol
        address_symbol: Symbol = self.AddData(data_tools.CryptoAddressesData, crypto, Resolution.Daily).Symbol
        self.data[crypto_symbol] = data_tools.SymbolData(network_symbol, address_symbol, self.period)

    self.rebalance_flag: bool = False
    self.Settings.MinimumOrderMarginPortfolioPercentage = 0.
    self.Schedule.On(self.DateRules.WeekStart("BTCUSD"), self.TimeRules.At(9, 30), self.Rebalance)

def OnData(self, data: Slice) -> None:
    curr_date: datetime.date = self.Time.date()
    
    # daily updating of crypto prices and market capitalization(CapMrktCurUSD)
    for crypto, symbol_obj in self.data.items():
        network_symbol: Symbol = symbol_obj.network_symbol
        address_symbol: Symbol = symbol_obj.address_symbol
        
        if network_symbol in data and data[network_symbol]:
            # get market capitalization
            cap_mrkt_cur_usd: float = data[network_symbol].Value
            if cap_mrkt_cur_usd != 0.:
                self.data[crypto].update_cap(cap_mrkt_cur_usd, curr_date)
            
        if address_symbol in data and data[address_symbol]:
            # get value of total with balance addresses 
            addresses_count: int = data[address_symbol].Value
            if addresses_count != 0.:
                self.data[crypto].update_addresses_count_values(addresses_count, curr_date)

    if not self.rebalance_flag:
        return

    # trade execution
    invested: List[str] = [x.Key.Value for x in self.Portfolio if x.Value.Invested]
    for ticker in invested:
        if ticker not in self.weight:
            self.Liquidate(ticker)

    for ticker, w in self.weight.items():
        if ticker in data and data[ticker]:
            self.SetHoldings(ticker, w * self.portfolio_percentage)

    self.rebalance_flag = False
    self.weight.clear()

def Rebalance(self) -> None:
    self.rebalance_flag = True

    curr_date: datetime.date = self.Time.date()
    crypto_data_last_update_date: Dict[Symbol, datetime.date] = data_tools.CryptoNetworkData.get_last_update_date()
    crypto_addresses_last_update_date: Dict[Symbol, datetime.date] = data_tools.CryptoAddressesData.get_last_update_date()
    
    address_growth: Dict[str, float] = {}
    
    for crypto, symbol_obj in self.data.items():
        network_symbol: Symbol = symbol_obj.network_symbol
        address_symbol: Symbol = symbol_obj.address_symbol

        if network_symbol not in crypto_data_last_update_date or address_symbol not in crypto_addresses_last_update_date:
            continue

        # crypto doesn't have enough data
        if self.Securities[network_symbol].GetLastData() and self.Time.date() > crypto_data_last_update_date[network_symbol] or \
            self.Securities[address_symbol].GetLastData() and self.Time.date() > crypto_addresses_last_update_date[address_symbol]:
            continue

        if symbol_obj.is_ready():
            # calculate address growth for current crypto
            if symbol_obj.cap_mrkt_cur_usd != 0:
                address_growth[crypto] = symbol_obj.address_growth()
    
    # not enough cryptos for selection    
    if len(address_growth)
