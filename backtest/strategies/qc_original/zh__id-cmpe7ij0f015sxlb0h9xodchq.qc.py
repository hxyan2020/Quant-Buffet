# Original QuantConnect / library Python
# locale=zh slug="外汇市场中的均值-方差市场时机选择"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

from AlgorithmImports import *
import data_tools
from scipy.optimize import minimize
from enum import Enum
# endregion
class TradedUniverse(Enum):
FX = 1
FX_FUTURES = 2
class MeanVarianceMarketTimingInTheFXMarket(QCAlgorithm):
def initialize(self) -> None:
    self.set_start_date(2000, 1, 1)
    self.set_cash(1_000_000)
    self._us_ir: Symbol = self.AddData(data_tools.InterestRate3M, 'IR3TIB01USM156N', Resolution.Daily).Symbol
    self._traded_universe: TradedUniverse = TradedUniverse.FX_FUTURES
    period: int = 6
    self._min_weight: float = .01
    self._EWMA_lambda: float = .95
    self._data: Dict[Symbol, data_tools.SymbolData] = {}
    # Cash rate source: https://fred.stlouisfed.org/series/IR3TIB01USM156N
    if self._traded_universe == TradedUniverse.FX:
        symbols: Dict[str, str] = {
            "AUDUSD" : "IR3TIB01AUM156N",   # Australian Dollar Futures, Continuous Contract #1
            "GBPUSD" : "LIOR3MUKM",         # British Pound Futures, Continuous Contract #1
            "CADUSD" : "IR3TIB01CAM156N",   # Canadian Dollar Futures, Continuous Contract #1
            "EURUSD" : "IR3TIB01EZM156N",   # Euro FX Futures, Continuous Contract #1
            "JPYUSD" : "IR3TIB01JPM156N",   # Japanese Yen Futures, Continuous Contract #1
            "MXNUSD" : "IR3TIB01MXM156N",   # Mexican Peso Futures, Continuous Contract #1
            "NZDUSD" : "IR3TIB01NZM156N",   # New Zealand Dollar Futures, Continuous Contract #1
            "CHFUSD" : "IR3TIB01CHM156N"    # Swiss Franc Futures, Continuous Contract #1
        }
    elif self._traded_universe == TradedUniverse.FX_FUTURES:
        symbols: Dict[str, str] = {
            "CME_AD1" : "IR3TIB01AUM156N",   # Australian Dollar Futures, Continuous Contract #1
            "CME_BP1" : "LIOR3MUKM",         # British Pound Futures, Continuous Contract #1
            "CME_CD1" : "IR3TIB01CAM156N",   # Canadian Dollar Futures, Continuous Contract #1
            "CME_EC1" : "IR3TIB01EZM156N",   # Euro FX Futures, Continuous Contract #1
            "CME_JY1" : "IR3TIB01JPM156N",   # Japanese Yen Futures, Continuous Contract #1
            "CME_MP1" : "IR3TIB01MXM156N",   # Mexican Peso Futures, Continuous Contract #1
            "CME_NE1" : "IR3TIB01NZM156N",   # New Zealand Dollar Futures, Continuous Contract #1
            "CME_SF1" : "IR3TIB01CHM156N"    # Swiss Franc Futures, Continuous Contract #1
        }
    # data subscription
    for symbol, rate_symbol in symbols.items():
        if self._traded_universe == TradedUniverse.FX:
            data: Security = self.add_forex(symbol, Resolution.MINUTE, Market.OANDA)
        elif self._traded_universe == TradedUniverse.FX_FUTURES:
            data: Security = self.add_data(data_tools.QuantpediaFutures, symbol, Resolution.DAILY)
        data.set_fee_model(data_tools.CustomFeeModel())
        ir_symbol: Symbol = self.add_data(data_tools.InterestRate3M, rate_symbol, Resolution.DAILY).symbol
        self._data[data.symbol] = data_tools.SymbolData(period, ir_symbol)
    self.settings.daily_precise_end_time = False
    self.settings.minimum_order_margin_portfolio_percentage = 0.
    self._recent_month: int = -1
def on_data(self, slice: Slice) -> None:
    if slice.contains_key(self._us_ir) and slice[self._us_ir]:
        for symbol, symbol_data in self._data.items():
            if slice.contains_key(symbol_data._ir_symbol) and slice[symbol_data._ir_symbol]:
                symbol_data.update_values(
                    slice[symbol_data._ir_symbol].value - slice[self._us_ir].value, slice[symbol_data._ir_symbol].value
                )
    if self._traded_universe == TradedUniverse.FX:
        if not self.securities[list(self._data.keys())[0]].exchange.hours.is_open(self.time, extended_market_hours=False):
            return
    # monthly rebalance
    if self._recent_month == self.time.month:
        return
    self._recent_month = self.time.month
    last_update_date: Dict[str, datetime.date] = data_tools.QuantpediaFutures.get_last_update_date()
    
    EWMA: Dict[Symbol, float] = {
        symbol: data_tools.EWMA_Volatility(symbol_data.get_rate_diff(), self._EWMA_lambda) 
        for symbol, symbol_data in self._data.items() 
        if symbol_data.is_ready()
        and (symbol.value in last_update_date and last_update_date[symbol.value] > self.time.date() if self._traded_universe == TradedUniverse.FX_FUTURES else True)
    }
    
    if len(EWMA) == 0:
        self.log('Not enough data for further calculation.')
        return
    
    expected_ret_df: DataFrame = pd.concat(
        [symbol_data.get_expected_returns() for _, symbol_data in self._data.items() if symbol_data.is_ready()], axis=1
    )
    port_opt = data_tools.PortfolioOptimization(expected_ret_df, 0, len(expected_ret_df.columns), np.mean(list(EWMA.values())))
    w: np.ndarray = port_opt.opt_portfolio()
    targets: List[PortfolioTarget] = []
    for i, symbol in enumerate(EWMA):
        if w[i] > self._min_weight:
            if slice.contains_key(symbol) and slice[symbol]:
                targets.append(PortfolioTarget(symbol, w[i]))
    
    self.set_holdings(targets, True)
