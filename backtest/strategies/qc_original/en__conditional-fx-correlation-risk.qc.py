# Original QuantConnect / library Python
# locale=en slug="conditional-fx-correlation-risk"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

from AlgorithmImports import *
import data_tools
import statsmodels.api as sm
# endregion

class ConditionalFXCorrelationRisk(QCAlgorithm):

def Initialize(self):
    self.SetStartDate(2000, 7, 1)
    self.SetCash(100000)

    self.quantpedia_futures:bool = False
    self.leverage:int = 5

    self.tickers:list[str] = [
        'CME_AD1', 'CME_BP1', 'CME_NE1',
        'CME_CD1', 'CME_SF1', 'CME_JY1'
    ]

    if not self.quantpedia_futures:
        self.tickers = [
            'AUDUSD', 'GBPUSD', 'NZDUSD', 'USDCAD',
            'USDCHF', 'USDCNH', 'USDCZK', 'USDDKK',
            'USDHUF', 'USDINR', 'USDJPY', 'USDNOK',
            'USDPLN', 'USDSAR', 'USDSEK', 'USDTHB',
            'USDTRY',
        ]

    self.corr_period:int = 66 + 1       # need n days of daily closes
    self.regression_period:int = 36     # need m monthly values
    self.min_prices:int = 15            # need l daily prices in one month
    self.max_missing_days:int = 15

    self.quantile:int = 10
    self.traded_currency_count:int = 2

    self.fxc_beta_index:int = 1
    self.prev_fxc:float = None
    self.fxc_delta_values:RollingWindow = RollingWindow[float](self.regression_period)
    self.data:dict[Symbol, SymbolData] = {}

    for ticker in self.tickers:
        security = self.AddData(data_tools.QuantpediaFutures, ticker, Resolution.Daily) if self.quantpedia_futures \
                else self.AddForex(ticker, Resolution.Daily, Market.Oanda)
        
        if self.quantpedia_futures:
            security.SetFeeModel(data_tools.CustomFeeModel())
        security.SetLeverage(self.leverage)
        
        symbol:Symbol = security.Symbol
        self.data[symbol] = data_tools.SymbolData(self.corr_period, self.regression_period)

    self.recent_month:int = -1

def OnData(self, data: Slice):
    curr_date:datetime.date = self.Time.date()

    # update daily prices
    for symbol, symbol_obj in self.data.items():
        if symbol in data and data[symbol] and data[symbol].Value != 0:
            symbol_obj.update_prices(data[symbol].Value, curr_date)

    # rebalance monthly
    if self.recent_month == self.Time.month:
        return
    self.recent_month = self.Time.month

    corr_ready_currencies:list[Symbol] = []
    for symbol, symbol_obj in self.data.items():
        # reset currencies, which prices stopped coming, because data are required consecutive
        if symbol_obj.data_still_coming(curr_date, self.max_missing_days) and symbol_obj.curr_monthly_prices_ready(self.min_prices):
            symbol_obj.update_monthly_returns()
        else:
            # monthly prices have to be consecutive for regression
            symbol_obj.reset_prices_and_monthly_returns()

        # filter only currencies, which prices are ready for correlation calculation
        if symbol_obj.correlation_prices_ready():
            corr_ready_currencies.append(symbol)

        symbol_obj.reset_curr_month_prices()

    total_ready_currencies:int = len(corr_ready_currencies)
    correlations:list[float] = []

    for i in range(total_ready_currencies):
        symbol1:Symbol = corr_ready_currencies[i]
        returns1:list[float] = self.data[symbol1].get_daily_returns()

        for j in range(i + 1, total_ready_currencies, 1):
            symbol2:Symbol = corr_ready_currencies[j]
            returns2:list[float] = self.data[symbol2].get_daily_returns()

            correlation:float = np.corrcoef(returns1, returns2)[0][1]
            correlations.append(correlation)

    if len(correlations)
