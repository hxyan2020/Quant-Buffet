# Original QuantConnect / library Python
# locale=en slug="hedging-factor-in-cryptocurrencies"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

from AlgorithmImports import *
import numpy as np
from data_tools import CommitmentsOfTraders, CryptoCotPair
from typing import Tuple, List
import statsmodels.api as sm
#endregion

class HedgingFactorinCryptocurrencies(QCAlgorithm):

def Initialize(self):
    self.SetStartDate(2015, 1, 1)
    self.SetCash(1000000)

    self.leverage:int = 5

    # subscribe crypto and COT data
    data:Crypto = self.AddCrypto('BTCUSD', Resolution.Minute, Market.Bitfinex)
    data.SetLeverage(self.leverage)
    crypto_symbol:Symbol = data.Symbol

    cot_symbol:Symbol = self.AddData(CommitmentsOfTraders, 'QBT', Resolution.Daily).Symbol

    data:Equity = self.AddEquity('BIL', Resolution.Minute)
    data.SetLeverage(self.leverage)
    self.t_bill:Symbol = data.Symbol

    self.risk_aversion:float = 3.
    self.allocation_limits:List[float] = [-0.5, 1.5]
    
    # weekly hedging factor data
    hedging_factor_w_period:int = 8
    price_w_period:int = hedging_factor_w_period + 1
    self.SetWarmup(max(price_w_period, hedging_factor_w_period) * 7, Resolution.Daily)

    max_missing_crypto_days:int = 5
    max_missing_cot_days:int = 7

    self.crypto_cot_pair:CryptoCotPair = CryptoCotPair(crypto_symbol,               \
                                                        cot_symbol,                 \
                                                        price_w_period,             \
                                                        hedging_factor_w_period,    \
                                                        max_missing_crypto_days,    \
                                                        max_missing_cot_days
                                                        )

def OnData(self, data:Slice) -> None:
    # COT data is present in the algo
    if self.crypto_cot_pair._cot_symbol in data and data[self.crypto_cot_pair._cot_symbol] and \
        self.crypto_cot_pair._crypto_symbol in data and data[self.crypto_cot_pair._crypto_symbol]:

        # update weekly COT data
        cot_data = data[self.crypto_cot_pair._cot_symbol]
        comm_hedgers_interest:float = cot_data.GetProperty("COMMERCIAL_HEDGER_LONG") + cot_data.GetProperty("COMMERCIAL_HEDGER_SHORT")
        if comm_hedgers_interest != 0:
            hedging_factor_value:float = cot_data.GetProperty("COMMERCIAL_HEDGER_SHORT") / comm_hedgers_interest

            price:float = data[self.crypto_cot_pair._crypto_symbol].Value

            self.crypto_cot_pair.update_data(price, hedging_factor_value)

            if self.crypto_cot_pair.is_ready():
                x:Tuple[np.ndarray, np.ndarray] = self.crypto_cot_pair.get_regression_data()
                model = self.multiple_linear_regression(x[1][:-1], x[0][1:])
                forecast_return:float = model.predict([1, x[1][-1]])[0]
                forecast_variance:float = np.std(x[0]) ** 2 # * np.sqrt(52)
                w_t:float = (1. / self.risk_aversion) * (forecast_return / forecast_variance)
                w_t = min(max(w_t, self.allocation_limits[0]), self.allocation_limits[1])
                t_bill_w:float = 1. - w_t

                self.SetHoldings(self.crypto_cot_pair._crypto_symbol, w_t)
                self.SetHoldings(self.t_bill, t_bill_w)
    else:
        # COT data is still comming in
        if not self.crypto_cot_pair.cot_updated(self):
            self.crypto_cot_pair.reset_data()
            self.Liquidate()

def multiple_linear_regression(self, x:np.ndarray, y:np.ndarray):
    x = np.array(x).T
    x = sm.add_constant(x)
    result = sm.OLS(endog=y, exog=x).fit()
    return result
