# Original QuantConnect / library Python
# locale=en slug="通过金融市场不确定性预测加密货币回报策略"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

from AlgorithmImports import *
from collections import deque
from dateutil.relativedelta import relativedelta
from pandas.core.frame import DataFrame
import data_tools
import statsmodels.api as sm
# endregion

class FinancialUncertaintyExplainsCryptocurrencyReturns(QCAlgorithm):

def Initialize(self):
    self.SetStartDate(2015, 1, 1)
    self.SetCash(100000)

    self.period:int = 24
    self.portion:float = 0.1
    self.rebalance_hour:int = 0 # rebalance at 00:00
    self.portfolio_percentage:float = .1
    self.quantile:int = 3
    # self.leverage:int = 2

    self.cryptos:Dict[str, str] = {
        "XLMUSD": "XLM",    # Stellar
        "XMRUSD": "XMR",    # Monero
        "XRPUSD": "XRP",    # XRP
        "ADAUSD": "ADA",    # Cardano
        "DOTUSD": "DOT",    # Polkadot
        "UNIUSD": "UNI",    # Uniswap
        "LINKUSD": "LINK",  # Chainlink
        "ANTUSD": "ANT",    # Aragon
        "BATUSD": "BAT",    # Basic Attention Token
        "BTCUSD": "BTC",    # Bitcoin
        "BTGUSD": "BTG",    # Bitcoin Gold
        "DASHUSD": "DASH",  # Dash
        "DGBUSD": "DGB",    # Dogecoin
        "ETCUSD": "ETC",    # Ethereum Classic
        "ETHUSD": "ETH",    # Ethereum
        # "FUNUSD": "FUN",    # FUN Token
        "LTCUSD": "LTC",    # Litecoin
        "MKRUSD": "MKR",    # Maker
        "NEOUSD": "NEO",    # Neo
        "PAXUSD": "PAX",    # Paxful
        "SNTUSD": "SNT",    # Status
        "TRXUSD": "TRX",    # Tron
        "XRPUSD": "XRP",    # XRP
        "XTZUSD": "XTZ",    # Tezos
        "XVGUSD": "XVG",    # Verge
        "ZECUSD": "ZEC",    # Zcash
        "ZRXUSD": "ZRX"     # Ox
    }

    self.data:Dict[Symbol, SymbolData] = {}

    # data subscription
    for pair, ticker in self.cryptos.items():
        data = self.AddCrypto(pair, Resolution.Hour, Market.Bitfinex)
        data.SetFeeModel(data_tools.CustomFeeModel())
        # data.SetLeverage(self.leverage)
        network_data = self.AddData(data_tools.DailyCustomData, ticker, Resolution.Daily).Symbol

        self.data[data.Symbol] = data_tools.SymbolData(network_data, self.period)

    self.fin_uncertainty:Symbol = self.AddData(data_tools.FinancialUncertaintyIndex, 'FIN_UN', Resolution.Daily).Symbol

    self.rebalance_flag:bool = False
    self.Settings.MinimumOrderMarginPortfolioPercentage = 0.

    self.current_month:int = -1

def OnData(self, data: Slice):
    # monthly rebalance
    if self.Time.month == self.current_month:
        return

    if not self.Time.hour == self.rebalance_hour:
        return
    self.current_month = self.Time.month

    # update monthly price
    for symbol, symbol_data in self.data.items():
        network_symbol:Symbol = symbol_data._network_symbol

        if symbol in data and data[symbol]:
            self.data[symbol].update(data[symbol].Close, self.Time.date())

        if network_symbol in data and data[network_symbol]:
            cap_mrkt_cur_usd:float = data[network_symbol].Value
            self.data[symbol].update_cap(cap_mrkt_cur_usd, self.Time.date())

    network_data_last_update_date:Dict[Symbol, datetime.date] = data_tools.DailyCustomData.get_last_update_date()
    financial_uncertainty_last_update_date:datetime.date = data_tools.FinancialUncertaintyIndex.get_last_update_date()

    # custom data still comming in
    if all([self.Securities[x].GetLastData() for x in list(self.data.keys())]) and any([self.Time.date() >= network_data_last_update_date[x] for x in network_data_last_update_date]) \
        or self.Time.date() >= financial_uncertainty_last_update_date:
        self.Liquidate()
        return

    history_financial_uncertainty:DataFrame = self.History([self.fin_uncertainty], start=self.Time.date() - relativedelta(months=self.period), end=self.Time.date()).value.unstack(level=0)
    
    crypto_returns_dict:Dict[Symbol, np.ndarray] = {symbol : symbol_data.get_returns() for symbol, symbol_data in self.data.items() if symbol_data.is_ready()}
    crypto_returns:List[float] = list(zip(*[[i for i in x] for x in crypto_returns_dict.values()]))

    if len(crypto_returns) == 0:
        return

    # run stock regression
    y:np.ndarray = np.array(crypto_returns)
    x:np.ndarray = history_financial_uncertainty[1:].values
    model = self.multiple_linear_regression(x, y)
    beta_values:np.ndarray = model.params[1]

    # store betas
    beta_by_symbol:Dict[Symbol, float] = {sym : beta_values[n] for n, sym in enumerate(list(crypto_returns_dict.keys()))}

    long:List[Symbol] = []
    short:List[Symbol] = []

    # sort by beta and divide into quantiles
    if len(beta_by_symbol) >= self.quantile:
        sorted_gamma:List[Symbol] = sorted(beta_by_symbol.items(), key=lambda x:x[1])
        quantile:int = int(len(beta_by_symbol) / self.quantile)
        long = [symbol for symbol, beta in sorted_gamma][:quantile]
        short = [symbol for symbol, beta in sorted_gamma][-quantile:]

    # weight:Dict[Symbol, float] = {}

    # total_cap_long:float = sum([symbol_data._cap_mrkt_cur_usd for symbol, symbol_data in self.data.items() if symbol in long])
    # for symbol in long:
    #     weight[symbol] = self.data[symbol]._cap_mrkt_cur_usd / total_cap_long
    
    # total_cap_short:float = sum([symbol_data._cap_mrkt_cur_usd for symbol, symbol_data in self.data.items() if symbol in short])
    # for symbol in short:
    #     weight[symbol] = -self.data[symbol]._cap_mrkt_cur_usd / total_cap_short

    invested = [x.Key for x in self.Portfolio if x.Value.Invested]
    for symbol in invested:
        if symbol not in long + short:
            self.Liquidate(symbol)

    # trade execution
    # for symbol, w in weight.items():
    #     if symbol in data and data[symbol]:
    #         self.SetHoldings(symbol, self.portfolio_percentage * w)

    for symbol in long:
        if symbol in data and data[symbol]:
            self.SetHoldings(symbol, 1/len(long) * self.portfolio_percentage)
    
    for symbol in short:
        if symbol in data and data[symbol]:
            self.SetHoldings(symbol, -1/len(short) * self.portfolio_percentage)
    
def multiple_linear_regression(self, x:np.ndarray, y:np.ndarray):
    x = sm.add_constant(x, has_constant='add')
    result = sm.OLS(endog=y, exog=x).fit()
    return result
