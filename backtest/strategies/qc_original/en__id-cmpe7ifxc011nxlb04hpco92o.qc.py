# Original QuantConnect / library Python
# locale=en slug="波动率风险溢价和危机阿尔法策略"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

from AlgorithmImports import *
from data_tools import SymbolData, EWMParamType, halflife, annual_port_vol, round_float
import itertools
import numpy as np
# endregion

class HarvestingVolatilityRiskPremiaandCrisisAlphaviaETFs(QCAlgorithm):

def Initialize(self):
    self.SetStartDate(2010, 1, 1)
    self.SetCash(100000)

    # VRP symbols
    self.long_vol_symbol: Symbol = self.AddEquity('VIXY', Resolution.Daily).Symbol
    self.short_vol_symbol: Symbol = self.AddEquity('SVXY', Resolution.Daily).Symbol

    self.slope_symbols: List[Symbol] = [
        self.AddData(CBOE, 'VIX', Resolution.Daily).Symbol, 
        self.AddData(CBOE, 'VIX3M', Resolution.Daily).Symbol
    ]

    self.min_model_period: int = 2 * 12 * 21

    self.slope_threshold: float = 0.
    self.VRP_vol_target: float = 0.2
    self.CTA_vol_target: float = 0.15
    self.CTA_final_vol_period: int = 252

    # VRP params
    self.center_of_mass: int = 63 

    # CTA params (Risk Adjusted Momentum, EMA Crossover, EMA Breakout)
    self.n: List[int] = [21, 63, 252]
    self.crossover_s: List[int] = [5, 10, 20]
    self.crossover_n: List[int] = [20, 40, 80]

    self.symbol_data: Dict[Union[Symbol, str], SymbolData] = {symbol : SymbolData(self.min_model_period) for symbol in [self.long_vol_symbol, self.short_vol_symbol]}
    self.symbol_data['slope'] = SymbolData(self.min_model_period)

    # CTA symbols
    self.CTA_commodities: List[str] = ['UGL', 'USO', 'USL', 'UNG', 'SOYB']   # 'JJC' (history since 2018)
    self.gross_weight_commodities: float = 0.1

    self.CTA_bonds: List[str] = ['TMF', 'TYD']
    self.gross_weight_bonds: float = 0.2

    self.CTA_symbols: List[Symbol] = [self.AddEquity(ticker, Resolution.Daily).Symbol for ticker in self.CTA_commodities + self.CTA_bonds]
    
    for symbol in self.CTA_symbols:
        self.symbol_data[symbol] = SymbolData(self.min_model_period)
    
    [self.Securities[s].SetLeverage(3) for s in self.symbol_data if s != 'slope']
    
    self.SetWarmup(self.min_model_period, Resolution.Daily)
    self.Settings.MinimumOrderMarginPortfolioPercentage = 0.

def OnData(self, slice: Slice) -> None:
    # store price data
    for symbol in self.symbol_data:
        if symbol == 'slope': continue

        if slice.ContainsKey(symbol) and slice[symbol] is not None:
            self.symbol_data[symbol].update(slice[symbol].Value)

    # store VIX data
    if all(slice.ContainsKey(symbol) and slice[symbol] is not None for symbol in self.slope_symbols):
        self.symbol_data['slope'].update(slice[self.slope_symbols[1]].Value - slice[self.slope_symbols[0]].Value)
    
    if self.IsWarmingUp: return
    
    if all(self.symbol_data[symbol].is_ready() for symbol in self.symbol_data):

        # VRP strategy
        slope_data: SymbolData = self.symbol_data['slope']
        # calculate two latest values of slope z-score; 
        # index: 0-latest, 1-one day lag
        z_score_values: List[float] = [(slope_data.get_latest_value(lag) - slope_data.value_EWMA(EWMParamType.SPAN, self.center_of_mass, lag + 1)) \
            / slope_data.value_EWSD(EWMParamType.SPAN, self.center_of_mass, lag + 1) \
            for lag in range(2)]
        
        # long-short trading signal
        VRP_traded_symbol: Union[Symbol, None] = None

        if slope_data.get_latest_value() > self.slope_threshold and z_score_values[0] > 0:
            VRP_traded_symbol = self.short_vol_symbol
        
        elif slope_data.get_latest_value() > self.slope_threshold and z_score_values[0]  self.slope_threshold and z_score_values[1]  -1):
            VRP_traded_symbol = self.short_vol_symbol
        
        if VRP_traded_symbol is not None:
            VRP_symbol_volatility: float = self.symbol_data[VRP_traded_symbol].return_EWSD(self.center_of_mass)
            
            # scaled volatility
            VRP_weight: float = round_float(self.VRP_vol_target / VRP_symbol_volatility)
        
            # CTA strategy
            # 1. Risk Adjusted Momentum
            risk_adjusted_momentum: Dict[Symbol, List[float]] = {
                symbol : [self.symbol_data[symbol].compounded_return(lookback) / self.symbol_data[symbol].scaled_volatility(lookback) for lookback in self.n]
                for symbol in self.CTA_symbols
            }

            # 2. EMA Crossover
            EMA_crossover: Dict[Symbol, List[float]] = {
                symbol : [(self.symbol_data[symbol].value_EWMA(EWMParamType.HALFLIFE, halflife(s)) - self.symbol_data[symbol].value_EWMA(EWMParamType.HALFLIFE, halflife(n))) / self.symbol_data[symbol].value_EWSD(EWMParamType.HALFLIFE, halflife(n)) \
                for s, n in list(zip(self.crossover_s, self.crossover_n))]
                for symbol in self.CTA_symbols
            }

            # 3. EMA Breakout
            EMA_breakout: Dict[Symbol, List[float]] = {
                symbol : [(self.symbol_data[symbol].get_latest_value() - self.symbol_data[symbol].value_EWMA(EWMParamType.SPAN, lookback)) / self.symbol_data[symbol].value_EWSD(EWMParamType.SPAN, lookback) for lookback in self.n]
                for symbol in self.CTA_symbols
            }

            # update x_n
            for symbol in self.CTA_symbols:
                x_n: np.ndarray = np.array([risk_adjusted_momentum[symbol], EMA_crossover[symbol], EMA_breakout[symbol]])
                self.symbol_data[symbol].update_x_n(x_n)

            if all(self.symbol_data[symbol].x_n_is_ready() for symbol in self.CTA_symbols):
                # calculate CTA weights
                n: np.ndarray = [
                    self.n,
                    self.crossover_n,
                    self.n
                ]
                
                CTA_weight: float = 1. - VRP_weight
                
                CTA_gross_weight: Dict[Symbol, float] = {
                    symbol : self.gross_weight_commodities if symbol.Value in self.CTA_commodities else self.gross_weight_bonds for symbol in self.CTA_symbols
                }

                # signal strength
                CTA_x_n_weight: Dict[Symbol, float] = {
                    symbol : self.symbol_data[symbol].get_weight(n, 252) for symbol in self.CTA_symbols
                }
                
                CTA_volatility_weight: Dict[Symbol, float] = {
                    symbol : (self.CTA_vol_target / self.symbol_data[symbol].return_EWSD(self.center_of_mass)) ** 2 for symbol in self.CTA_symbols
                }
                
                CTA_asset_weight: Dict[Symbol, float] = {
                    symbol : CTA_gross_weight[symbol] * CTA_x_n_weight[symbol] * CTA_volatility_weight[symbol] for symbol in self.CTA_symbols
                }

                # instantaneous portfolio volatility
                returns: np.ndarray = np.array([self.symbol_data[symbol].get_daily_returns()[-self.CTA_final_vol_period:] for symbol in self.CTA_symbols])
                weights: np.ndarray = abs(np.array(list(CTA_x_n_weight.values())))
                CTA_portfolio_volatility: float = annual_port_vol(returns, weights)

                final_CTA_weight: float = round_float(self.CTA_vol_target / CTA_portfolio_volatility)

                # concat final VRP and CTA portfolio assets
                targets: List[PortfolioTarget] = [
                    PortfolioTarget(symbol, round_float(CTA_weight * final_CTA_weight * CTA_asset_weight[symbol])) for symbol in self.CTA_symbols
                ] + [PortfolioTarget(VRP_traded_symbol, VRP_weight)]

                self.SetHoldings(targets, True)
