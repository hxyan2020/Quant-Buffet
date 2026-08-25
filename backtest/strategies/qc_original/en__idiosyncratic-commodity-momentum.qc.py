# Original QuantConnect / library Python
# locale=en slug="idiosyncratic-commodity-momentum"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

from AlgorithmImports import *
import data_tools
import statsmodels.api as sm
import numpy as np
#endregion

class IdiosyncraticCommodityMomentum(QCAlgorithm):

def Initialize(self):
    self.SetStartDate(2004, 1, 1)
    self.SetCash(100000)
   
    tickers:dict[str, str] = {
        "CME_S1" : Futures.Grains.Soybeans,         # Soybean Futures, Continuous Contract
        "CME_W1" : Futures.Grains.Wheat,            # Wheat Futures, Continuous Contract
        "CME_SM1" : Futures.Grains.SoybeanMeal,     # Soybean Meal Futures, Continuous Contract
        "CME_BO1" : Futures.Grains.SoybeanOil,      # Soybean Oil Futures, Continuous Contract
        "CME_C1" : Futures.Grains.Corn,             # Corn Futures, Continuous Contract
        "CME_O1" : Futures.Grains.Oats,             # Oats Futures, Continuous Contract
        "CME_LC1" : Futures.Meats.LiveCattle,       # Live Cattle Futures, Continuous Contract
        "CME_FC1" : Futures.Meats.FeederCattle,     # Feeder Cattle Futures, Continuous Contract
        "CME_LN1" : Futures.Meats.LeanHogs,         # Lean Hog Futures, Continuous Contract
        "CME_GC1" : Futures.Metals.Gold,            # Gold Futures, Continuous Contract
        "CME_SI1" : Futures.Metals.Silver,          # Silver Futures, Continuous Contract
        "CME_PL1" : Futures.Metals.Platinum,        # Platinum Futures, Continuous Contract
        "CME_HG1" : Futures.Metals.Copper,          # Copper Futures, Continuous Contract
        "CME_LB1" : Futures.Forestry.RandomLengthLumber,  # Random Length Lumber Futures, Continuous Contract
        "CME_PA1" : Futures.Metals.Palladium,       # Palladium Futures, Continuous Contract
        "CME_DA1" : Futures.Dairy.ClassIIIMilk,     # Class III Milk Futures
        "CME_RB1" : Futures.Energies.Gasoline,      # Gasoline Futures, Continuous Contract
        "ICE_CC1" : Futures.Softs.Cocoa,            # Cocoa Futures, Continuous Contract 
        "ICE_CT1" : Futures.Softs.Cotton2,          # Cotton No. 2 Futures, Continuous Contract #1
        "ICE_KC1": Futures.Softs.Coffee,            # Coffee C Futures, Continuous Contract #1
        "ICE_O1" : Futures.Energies.HeatingOil,     # Heating Oil Futures, Continuous Contract
        "ICE_OJ1": Futures.Softs.OrangeJuice,       # Orange Juice Futures, Continuous Contract #1
        "ICE_SB1" : Futures.Softs.Sugar11CME,       # Sugar No. 11 Futures, Continuous Contract
    }
    
    self.ranking_period:int = 3
    self.month_period:int = 21
    self.one_year_period:int = 12 * self.month_period
    self.period:int = 5.5 * self.one_year_period

    self.leverage:int = 5
    self.trade_count:int = 4
    self.percentage_from_total_count:float = 0.15
    self.min_prices:int = 15
    self.wanted_monthly_returns:int = 1
    self.qp_max_missing_days:int = 5
    self.cot_max_missing_days:int = 10
    self.futures_max_missing_days:int = 5

    self.hedging_pressure_factor_symbols:list[Symbol, bool] = []
    self.hedging_pressure_factor_vector:list[float] = []

    self.term_structure_factor_symbols:list[Symbol, bool] = []
    self.term_structure_factor_vector:list[float] = []

    self.value_factor_symbols:list[Symbol, bool] = []
    self.value_factor_vector:list[float] = []

    self.data:dict[Symbol, data_tools.Symbol] = {}
    self.futures_data:dict[str, data_tools.FuturesData] = {}

    min_expiration_days:int = 0
    max_expiration_days:int = 360
    
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
        self.futures_data[future_ticker] = data_tools.FuturesData(self.ranking_period)

        self.data[qp_symbol] = data_tools.SymbolData(cot_symbol, future_ticker,
            self.ranking_period * 4, self.period)
    
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
            spliced:float = data[qp_symbol].GetProperty('spliced')

            symbol_obj.update_prices(price)

        cot_symbol:Symbol = symbol_obj.cot_symbol
        if cot_symbol in data and data[cot_symbol]:
            speculator_long_count:float = data[cot_symbol].GetProperty('LARGE_SPECULATOR_LONG')
            speculator_short_count:float = data[cot_symbol].GetProperty('LARGE_SPECULATOR_SHORT')
            
            if speculator_long_count != 0 and speculator_short_count != 0:
                hedging_pressure_value:float = speculator_long_count / (speculator_long_count + speculator_short_count)
                symbol_obj.update_hedging_pressure_values(hedging_pressure_value)

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

                    if near_price != 0 and dist_price != 0:
                        roll_yield:float = near_price / dist_price
                        future_obj.update_roll_yields(roll_yield)

    # rebalance monthly
    if self.Time.month == self.recent_month:
        return
    self.recent_month = self.Time.month
    
    # Factor calculation data.
    hedging_pressure:dict[Symbol, float] = {}
    roll_yield:dict[Symbol, float] = {}
    value:dict[Symbol, float] = {}
    custom_data_last_update_date: Dict[Symbol, datetime.date] = data_tools.LastDateHandler.get_last_update_date()

    for qp_symbol, symbol_obj in self.data.items():
        future_ticker:str = symbol_obj.future_ticker

        # check if data is still coming
        if any([self.securities[symbol].get_last_data() and self.time.date() > custom_data_last_update_date[symbol] for symbol in [qp_symbol, symbol_obj.cot_symbol]]):
            self.liquidate(qp_symbol)
            continue

        if symbol_obj.monthly_prices_ready(self.min_prices):
            symbol_obj.update_monthly_returns()
            symbol_obj.reset_monthly_prices()

        # update metrics
        if symbol_obj.prices_for_value_factor_ready():
            value[qp_symbol] = symbol_obj.get_value(self.one_year_period) # The average spot price from 4.5 to 5.5 years ago divided by most recent spot price.
         
        if symbol_obj.hedging_pressure_values_ready():
            hedging_pressure[qp_symbol] = symbol_obj.get_mean_hedging_pressure_values()

        if self.futures_data[future_ticker].roll_yields_ready():
            roll_yield[qp_symbol] = self.futures_data[future_ticker].get_mean_roll_yields()

    if int(len(hedging_pressure) * self.percentage_from_total_count) >= 1:
        factor_return:float = self.CalcFactorReturn(self.hedging_pressure_factor_symbols, self.wanted_monthly_returns)

        if factor_return != 0:
            self.hedging_pressure_factor_vector.append(factor_return)
        else:
            self.hedging_pressure_factor_vector.clear()

        self.hedging_pressure_factor_symbols = self.GetNewFactorSymbols(hedging_pressure)
    else:
        # require consecutive data in regression
        self.hedging_pressure_factor_symbols.clear()
        self.hedging_pressure_factor_vector

    if int(len(roll_yield) * self.percentage_from_total_count) >= 1:
        factor_return:float = self.CalcFactorReturn(self.term_structure_factor_symbols, self.wanted_monthly_returns)

        if factor_return != 0:
            self.term_structure_factor_vector.append(factor_return)
        else:
            self.term_structure_factor_vector.clear()

        self.term_structure_factor_symbols = self.GetNewFactorSymbols(roll_yield)
    else:
        # require consecutive data in regression
        self.term_structure_factor_symbols.clear()
        self.term_structure_factor_vector.clear()

    if int(len(value) * self.percentage_from_total_count) >= 1:
        factor_return:float = self.CalcFactorReturn(self.value_factor_symbols, self.wanted_monthly_returns)

        if factor_return != 0:
            self.value_factor_vector.append(factor_return)
        else:
            self.value_factor_vector.clear()

        self.value_factor_symbols = self.GetNewFactorSymbols(roll_yield)
    else:
        # require consecutive data in regression
        self.value_factor_symbols.clear()
        self.value_factor_vector.clear()

    min_len:int = min(len(self.hedging_pressure_factor_vector), len(self.term_structure_factor_vector), len(self.value_factor_vector))

    # all vectors are filled
    if min_len  float:
    factor_return:float = 0
    for symbol, long_flag in factor_symbols:
        if self.data[symbol].monthly_returns_ready(period):
            commodity_returns = self.data[symbol].get_last_n_monthly_returns(period)
            
            for commodity_return in commodity_returns:
                factor_return += commodity_return if long_flag else -commodity_return

    return factor_return

def GetNewFactorSymbols(self, value_by_symbol:dict) -> list:
    sorted_by_value:dict[Symbol, float] = sorted(value_by_symbol.items(), key=lambda x: x[1])
    count:int = int(len(sorted_by_value) * self.percentage_from_total_count)
    long_leg:list[list[Symbol, bool]] = [(x[0], True) for x in sorted_by_value[-count:]]
    short_leg:list[list[Symbol, bool]] = [(x[0], False) for x in sorted_by_value[:count]]

    return long_leg + short_leg
