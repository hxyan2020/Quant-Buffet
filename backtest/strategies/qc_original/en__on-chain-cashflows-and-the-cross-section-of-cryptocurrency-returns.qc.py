# Original QuantConnect / library Python
# locale=en slug="on-chain-cashflows-and-the-cross-section-of-cryptocurrency-returns"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

from AlgorithmImports import *
from io import StringIO
from pandas.core.frame import DataFrame
from typing import List, Dict
import pandas as pd
# endregion

class OnChainCashflowsandtheCrossSectionofCryptocurrencyReturns(QCAlgorithm):

def Initialize(self):
    self.SetStartDate(2015, 1, 1)
    self.SetCash(100000)

    self.leverage:int = 2
    self.quantile:int = 3
    self.traded_percentage:float = 0.1
    self.rebalance_hour:int = 3 # rebalance at 03:00

    self.crypto_tickers:Dict[str, str] = { 
        'Bitcoin': 'BTCUSD', 'Ethereum': 'ETHUSD', 'Solana': 'SOLUSD', 'Cardano': 'ADAUSD', 'XRP': 'XRPUSD', 
        'Polkadot': 'DOTUSD', 'Dogecoin': 'DOGEUSD', 'Terra': 'LUNAUSD', 'Avalanche': 'AVAXUSD', 'Uniswap': 'UNIUSD', 
        'Chainlink': 'LINKUSD', 'Litecoin': 'LTCUSD', 'Bitcoin Cash ABC': 'BCHABCUSD', 'Bitcoin SV': 'BSVUSD', 
        'Filecoin': 'FILUSD', 'Stellar': 'XLMUSD', 'Tezos': 'XTZUSD', 'NEO': 'NEOUSD', 'Cosmos Hub': 'ATOMUSD', 
        'IOTA': 'IOTAUSD', 'Ethereum Classic': 'ETCUSD', 'Dash': 'DASHUSD', 'Elrond': 'EGLDUSD', 'Aave': 'AAVEUSD', 
        'Enjin Coin': 'ENJUSD', 'EOS': 'EOSUSD', 'MakerDAO': 'MKRUSD', 'Decentraland': 'MANAUSD', 'Synthetix': 'SNXUSD', 
        'FTX Token': 'FTTUSD', 'OMG Network': 'OMGUSD', 'SushiSwap': 'SUSHIUSD', 'yearn.finance': 'YFIUSD', 
        'Wrapped Bitcoin': 'WBTCUSD', 'Monero': 'XMRUSD', 'Zcash': 'ZECUSD', '0x': 'ZRXUSD', 'XRP (Avalanche C-Chain)': 'XRAUSD', 
        'Ampleforth': 'AMPLUSD', 'The Graph': 'GRTUSD', 'DigiByte': 'DGBUSD','1inch': '1INCHUSD', 'Tron': 'TRXUSD'
        }

    # source: https://tokenterminal.com/terminal/metrics/fees
    crypto_fees:str = self.Download('data.quantpedia.com/backtesting_data/crypto/crypto_fees/crypto_fees.csv')
    self.crypto_fees_df:DataFrame = pd.read_csv(StringIO(crypto_fees), delimiter=';')
    self.crypto_fees_df['date'] = pd.to_datetime(self.crypto_fees_df['date']).dt.date
    self.crypto_fees_df.set_index('date', inplace=True)
    self.last_date:DateTime = self.crypto_fees_df.index[-1]

    # data subscription
    for ticker in list(self.crypto_tickers.values()):
        data = self.AddCrypto(ticker, Resolution.Hour, Market.Bitfinex)
        data.SetLeverage(self.leverage)
        data.SetFeeModel(CustomFeeModel())

    self.Settings.MinimumOrderMarginPortfolioPercentage = 0.

def OnData(self, data: Slice) -> None:
    # rebalance at specific hour
    if not self.Time.hour == self.rebalance_hour:
        return

    # check on custom data date
    if self.Time.date() > self.last_date:
        self.Liquidate()
        return

    selected_crypto_fees:DataFrame = self.crypto_fees_df[[col for col in self.crypto_fees_df.columns if self.crypto_tickers[col] in data and data[self.crypto_tickers[col]]]]

    if not self.Time.date() in selected_crypto_fees.index:
        return

    # sort selected crypto fees
    sorted_current_fees:List[str] =  list(map(lambda x: self.crypto_tickers[x], list(selected_crypto_fees.loc[selected_crypto_fees.index = self.quantile:
        quantile:int = len(sorted_current_fees) // self.quantile
        long = list(sorted_current_fees)[:quantile]
        short = list(sorted_current_fees)[-quantile:]

    # trade execution
    stocks_invested:List[Symbol] = [x.Key.Value for x in self.Portfolio if x.Value.Invested]
    for ticker in stocks_invested:
        if ticker not in long + short:
            self.Liquidate(ticker)

    for ticker in long:
        if ticker in data and data[ticker]:
            self.SetHoldings(ticker, 1/len(long) * self.traded_percentage)

    for ticker in short:
        if ticker in data and data[ticker]:
            self.SetHoldings(ticker, -1/len(short) * self.traded_percentage)

# custom fee model
class CustomFeeModel(FeeModel):
def GetOrderFee(self, parameters):
    fee = parameters.Security.Price * parameters.Order.AbsoluteQuantity * 0.00005
    return OrderFee(CashAmount(fee, "USD"))
