# Original QuantConnect / library Python
# locale=en slug="capturing-energy-risk-premia"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

from AlgorithmImports import *
import data_tools
from typing import Dict
#endregion
class HedgersEffectCommodities(QCAlgorithm):

def Initialize(self):
    self.SetStartDate(2005, 1, 1)
    self.SetCash(100000)
 
    tickers:Dict[str, str] = {
        'CME_CL1' : Futures.Energies.CrudeOilWTI,   # Crude Oil Futures, Continuous Contract
        'CME_NG1' : Futures.Energies.NaturalGas,    # Natural Gas (Henry Hub) Physical Futures, Continuous Contract
        'ICE_O1'  : Futures.Energies.HeatingOil,    # Heating Oil Futures, Continuous Contract
        'CME_CU1' : Futures.Energies.Ethanol,       # Chicago Ethanol (Platts) Futures
    }
    # Weekly hedging pressure data.
    self.data:Dict[Symbol, data_tools.SymbolData] = {}
    self.futures_data:Dict[str, data_tools.FuturesData] = {}
    
    min_expiration_days:int = 0
    max_expiration_days:int = 360
    self.min_futures:int = 2
    self.leverage:int = 5
    self.total_portfolios:int = 7
    self.one_year_period:int = 252
    self.period:int = int(252 * 5.5)
    self.cot_period:int = 52
    self.volume_period:int = 42
    for qp_ticker, qc_ticker in tickers.items():
        # Add quantpedia back-adjusted data.
        security = self.AddData(data_tools.QuantpediaFutures, qp_ticker, Resolution.Daily)
        security.SetFeeModel(data_tools.CustomFeeModel())
        security.SetLeverage(self.leverage)
        qp_symbol:Symbol = security.Symbol
        
        cot_ticker:str = 'Q' + qp_ticker.split('_')[1][:-1]
        cot_symbol:Symbol = self.AddData(data_tools.CommitmentsOfTraders, cot_ticker, Resolution.Daily).Symbol
        # QC futures
        future:Future = self.AddFuture(qc_ticker, Resolution.Daily, dataNormalizationMode=DataNormalizationMode.Raw)
        future.SetFilter(timedelta(days=min_expiration_days), timedelta(days=max_expiration_days))
        future_ticker:str = future.Symbol.Value
        self.futures_data[future_ticker] = data_tools.FuturesData(self.one_year_period, self.volume_period)
        self.data[qp_symbol] = data_tools.SymbolData(cot_symbol, future_ticker,
            self.period, self.cot_period)
    self.recent_month:int = -1
    self.settings.daily_precise_end_time = False
    self.settings.minimum_order_margin_portfolio_percentage = 0.
def FindAndUpdateContracts(self, futures_chain, ticker:str) -> None:
    near_contract:FuturesContract = None
    dist_contract:FuturesContract = None
    if ticker in futures_chain:
        contracts:list[:FuturesContract] = [contract for contract in futures_chain[ticker] if contract.Expiry.date() > self.Time.date()]
        if len(contracts) >= 2:
            contracts:list[:FuturesContract] = sorted(contracts, key=lambda x: x.Expiry, reverse=False)
            near_contract = contracts[0]
            dist_contract = contracts[1]
    self.futures_data[ticker].update_contracts(near_contract, dist_contract)
    
def OnData(self, data):
    curr_date:datetime.date = self.Time.date()
    for qp_symbol, symbol_obj in self.data.items():
        # store daily price
        if qp_symbol in data and data[qp_symbol]:
            price:float = data[qp_symbol].Value
            symbol_obj.update_qp_prices(price)
        cot_symbol:Symbol = symbol_obj.cot_symbol
        if cot_symbol in data and data[cot_symbol]:
            speculator_long_count:float = data[cot_symbol].GetProperty('LARGE_SPECULATOR_LONG')
            speculator_short_count:float = data[cot_symbol].GetProperty('LARGE_SPECULATOR_SHORT')
            hedgers_long_count:float = data[cot_symbol].GetProperty('COMMERCIAL_HEDGER_LONG')
            hedgers_short_count:float = data[cot_symbol].GetProperty('COMMERCIAL_HEDGER_SHORT')
            
            if speculator_long_count != 0 and speculator_short_count != 0 and hedgers_long_count != 0 and hedgers_short_count != 0:
                hedging_pressure_value:float = (hedgers_short_count - hedgers_long_count) / (hedgers_long_count + hedgers_short_count)
                speculative_pressure_value:float = (speculator_long_count - speculator_short_count) / (speculator_long_count + speculator_short_count)
                
                symbol_obj.update_pressures(hedging_pressure_value, speculative_pressure_value)
     # daily update qc future data
    if data.FutureChains.Count > 0:
        for ticker, future_obj in self.futures_data.items():
            # check if near contract is expired or is not initialized
            if not future_obj.is_initialized() or \
                (future_obj.is_initialized() and future_obj.near_contract.Expiry.date() == curr_date):
                self.FindAndUpdateContracts(data.FutureChains, ticker)
            # update QC futures rolling return
            if future_obj.is_initialized():
                near_c:FuturesContract = future_obj.near_contract
                dist_c:FuturesContract = future_obj.distant_contract
                if near_c.Symbol in data and data[near_c.Symbol] and dist_c.Symbol in data and data[dist_c.Symbol]:
                    near_price:float = data[near_c.Symbol].Value * self.Securities[ticker].SymbolProperties.PriceMagnifier
                    dist_price:float = data[dist_c.Symbol].Value * self.Securities[ticker].SymbolProperties.PriceMagnifier
                    volume:float = near_c.Volume
                    if near_price != 0 and dist_price != 0 and volume != 0:
                        future_obj.update_prices_and_volumes(near_price, dist_price, volume)
    if self.recent_month == curr_date.month:
        return
    self.recent_month = curr_date.month
    self.Liquidate()
    last_qp_price_by_symbol:Dict[Symbol, float] = {}
    portfolios:list[Dict[Symbol, float]] = [
        {} for i in range(self.total_portfolios)
    ]
    for qp_symbol, symbol_obj in self.data.items():
        future_ticker:str = symbol_obj.future_ticker
        if any([self.securities[symbol].get_last_data() and self.time.date() > data_tools.LastDateHandler.get_last_update_date()[symbol] for symbol in [qp_symbol, symbol_obj.cot_symbol]]):
            self.liquidate()
            return
            
        if symbol_obj.qp_prices_ready() and symbol_obj.pressures_ready() and self.futures_data[future_ticker].prices_and_volumes_ready():
            latest_near_contract_price:float = self.futures_data[future_ticker].get_latest_near_contract_price()
            near_contract_volumes:list[float] = self.futures_data[future_ticker].get_near_contract_volumes()
            portfolios[0][qp_symbol] = self.futures_data[future_ticker].get_roll_yield()
            portfolios[1][qp_symbol] = symbol_obj.get_hedging_pressure()
            portfolios[2][qp_symbol] = symbol_obj.get_speculative_pressure()
            portfolios[3][qp_symbol] = symbol_obj.get_momentum(self.one_year_period)
            portfolios[4][qp_symbol] = symbol_obj.get_value(self.one_year_period, latest_near_contract_price)
            portfolios[5][qp_symbol] = symbol_obj.get_liquidity(near_contract_volumes)
            portfolios[6][qp_symbol] = symbol_obj.get_skewness(self.one_year_period)
            last_qp_price_by_symbol[qp_symbol] = symbol_obj.get_last_price()
    if len(portfolios[0])  0]
        short_leg = [x for x in portfolio.items() if x[1]
