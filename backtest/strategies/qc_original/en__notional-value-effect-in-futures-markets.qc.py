# Original QuantConnect / library Python
# locale=en slug="notional-value-effect-in-futures-markets"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

from AlgorithmImports import *
import numpy as np
import pandas as pd
#endregion
class NotionalValueEffectInFuturesMarkets(QCAlgorithm):
def Initialize(self):
    self.SetStartDate(2015, 1, 1)
    self.SetCash(100000)
    self.symbols = [
                    ("CME_S1", "Futures.Grains.Soybeans", 1), # Soybean Futures, Continuous Contract
                    ("CME_W1", "Futures.Grains.SRWWheat", 1), # Wheat Futures, Continuous Contract
                    ("CME_SM1", "Futures.Grains.SoybeanMeal", 1), # Soybean Meal Futures, Continuous Contract
                    ("CME_BO1", "Futures.Grains.SoybeanOil", 1), # Soybean Oil Futures, Continuous Contract
                    ("CME_C1", "Futures.Grains.Corn", 1), # Corn Futures, Continuous Contract
                    ("CME_O1", "Futures.Grains.Oats", 1), # Oats Futures, Continuous Contract
                    ("CME_LC1", "Futures.Meats.LiveCattle", 1), # Live Cattle Futures, Continuous Contract
                    ("CME_FC1", "Futures.Meats.FeederCattle", 1), # Feeder Cattle Futures, Continuous Contract
                    ("CME_GC1", "Futures.Metals.Gold", 1), # Gold Futures, Continuous Contract
                    ("CME_SI1", "Futures.Metals.Silver", 1), # Silver Futures, Continuous Contract
                    ("CME_PL1", "Futures.Metals.Platinum", 1), # Platinum Futures, Continuous Contract
                    ("CME_CL1", "Futures.Energies.CrudeOilWTI", 1), # Crude Oil Futures, Continuous Contract
                    ("CME_HG1", "Futures.Metals.Copper", 1), # Copper Futures, Continuous Contract
                    ("CME_LB1", "Futures.Forestry.RandomLengthLumber", 1), # Random Length Lumber Futures, Continuous Contract
                    ("CME_NG1", "Futures.Energies.NaturalGasHenryHubLastDayFinancial", 1), # Natural Gas (Henry Hub) Physical Futures, Continuous Contract
                    ("CME_PA1", "Futures.Metals.Palladium", 1), # Palladium Futures, Continuous Contract 
                    # ("CME_CU1", "Futures.Energies.ChicagoEthanolPlatts", 1), # Chicago Ethanol (Platts) Futures
                    ("CME_DA1", "Futures.Dairy.ClassIIIMilk", 1), # Class III Milk Futures
                    ("CME_RB2", "Futures.Energies.GulfCoastCBOBGasolineA2PlattsVsRBOBGasoline", 1), # Gasoline Futures, Continuous Contract
                    
                    ("ICE_CC1", "Futures.Softs.Cocoa", 1), # Cocoa Futures, Continuous Contract 
                    ("ICE_O1", "Futures.Energies.HeatingOil", 1), # Heating Oil Futures, Continuous Contract
                    ("ICE_GO1", "Futures.Energies.SingaporeGasoilPlattsVsLowSulphurGasoilFutures", 1),  # Gas Oil Futures, Continuous Contract
                    ("ICE_WT1", "Futures.Energies.WTIHoustonCrudeOil", 1), # WTI Crude Futures, Continuous Contract
                                            
                    ("CME_AD1", "Futures.Currencies.AUD", 2), # Australian Dollar Futures, Continuous Contract #1
                    ("CME_BP1", "Futures.Currencies.GBP", 2), # British Pound Futures, Continuous Contract #1
                    ("CME_CD1", "Futures.Currencies.CAD", 2), # Canadian Dollar Futures, Continuous Contract #1
                    ("CME_EC1", "Futures.Currencies.EUR", 2), # Euro FX Futures, Continuous Contract #1
                    ("CME_JY1", "Futures.Currencies.AUDJPY", 2), # Japanese Yen Futures, Continuous Contract #1
                    ("CME_MP1", "Futures.Currencies.MXN", 2), # Mexican Peso Futures, Continuous Contract #1
                    ("CME_NE1", "Futures.Currencies.AUDNZD", 2), # New Zealand Dollar Futures, Continuous Contract #1
                    ("CME_SF1", "Futures.Currencies.CHF", 2), # Swiss Franc Futures, Continuous Contract #1
                
                    ("CME_NQ1", "Futures.Indices.NASDAQ100EMini", 3), # E-mini NASDAQ 100 Futures, Continuous Contract #1
                    ("CME_ES1", "Futures.Indices.SP500EMini", 3), # E-mini S&P 500 Futures, Continuous Contract #1
                    ("SGX_NK1", "Futures.Indices.Nikkei225Yen", 3), # SGX Nikkei 225 Index Futures, Continuous Contract #1
                    ("CME_MD1", "Futures.Indices.SP400MidCapEmini", 3), # E-mini S&P MidCap 400 Futures
                    
                    ("CME_TY1", "Futures.Financials.Y10TreasuryNote", 4), # 10 Yr Note Futures, Continuous Contract #1
                    ("CME_FV1", "Futures.Financials.Y5TreasuryNote", 4), # 5 Yr Note Futures, Continuous Contract #1
                    ("CME_TU1", "Futures.Financials.Y2TreasuryNote", 4), # 2 Yr Note Futures, Continuous Contract #1
                    ("SGX_JB1", "Futures.Currencies.JapaneseYenEmini", 4) # SGX 10-Year Mini Japanese Government Bond Futures
                ]
                
    self.period = 3 * 21 # Three months of daily data.
    self.volatility_target = 0.1
    self.leverage_cap = 5
    
    self.data = {}
    
    for symbol_tuple in self.symbols:
        quantpedia_future = symbol_tuple[0]
        qc_future = symbol_tuple[1]
        asset_group = symbol_tuple[2]
        # Back adjusted and spliced data import.
        data = self.AddData(QuantpediaFutures, quantpedia_future, Resolution.Daily)
        
        data.SetFeeModel(CustomFeeModel())
        data.SetLeverage(10)
        
        data = self.AddFuture(qc_future, Resolution.Daily)
        contract_multiplier = data.SymbolProperties.ContractMultiplier
        
        self.data[quantpedia_future] = SymbolData(self.period, contract_multiplier, asset_group)
def OnData(self, data):
    indexes = {} # asset_group = 3
    currencies = {} # asset_group = 2
    commodities = {} # asset_group = 1
    goverment_bonds = {} # asset_group = 4
    
    for symbol_tuple in self.symbols:
        symbol = symbol_tuple[0]
        
        if symbol in data and data[symbol]:
            price = data[symbol].Value
            self.data[symbol].update(price)
            
        if self.data[symbol].is_ready():
            asset_group = self.data[symbol].AssetGroup
            
            # notional value = asset price * contract multiplier
            notional_value = self.data[symbol].LastPrice * self.data[symbol].ContractMultiplier
            
            if asset_group == 1:
                commodities[symbol] = notional_value
            elif asset_group == 2:
                currencies[symbol] = notional_value
            elif asset_group == 3:
                indexes[symbol] = notional_value
            elif asset_group == 4:
                goverment_bonds[symbol] = notional_value
                
    self.Liquidate()
            
    if len(indexes) or len(commodities) or len(goverment_bonds) or len(currencies):
        # First element in sorted list has the first rank in it's rank list,
        # because future with highest notional value has lowest rank.
        sorted_indexes = [x[0] for x in sorted(indexes.items(), key = lambda item: item[1], reverse=True)]
        sorted_commodities = [x[0] for x in sorted(commodities.items(), key = lambda item: item[1], reverse=True)]
        sorted_goverment_bonds = [x[0] for x in sorted(goverment_bonds.items(), key = lambda item: item[1], reverse=True)]
        sorted_currencies = [x[0] for x in sorted(currencies.items(), key = lambda item: item[1], reverse=True)]
        
        indexes_avg_rank = np.mean([x[1] for x in indexes.items()])
        commodities_avg_rank = np.mean([x[1] for x in commodities.items()])
        goverment_bonds_avg_rank = np.mean([x[1] for x in goverment_bonds.items()])
        currencies_avg_rank = np.mean([x[1] for x in currencies.items()])
        
        indexes_notional_values = [x[1] for x in sorted(indexes.items(), key = lambda item: item[1], reverse=True)]
        commodities_notional_values = [x[1] for x in sorted(commodities.items(), key = lambda item: item[1], reverse=True)]
        goverment_bonds_notional_values = [x[1] for x in sorted(goverment_bonds.items(), key = lambda item: item[1], reverse=True)]
        currencies_notional_values = [x[1] for x in sorted(currencies.items(), key = lambda item: item[1], reverse=True)]
        
        # The weight of particular contract is determined as its rank minus the average rank of all contracts from this asset class
        # multiplied by a constant to ensure that the weights of long (short) sum to 1 (-1).
        indexes_weights = self.CreateWeights(sorted_indexes, indexes_notional_values, indexes_avg_rank)
        
        commodities_weights = self.CreateWeights(sorted_commodities, commodities_notional_values, commodities_avg_rank)
        
        goverment_bonds_weights = self.CreateWeights(sorted_goverment_bonds, goverment_bonds_notional_values, goverment_bonds_avg_rank)
        
        currencies_weights = self.CreateWeights(sorted_currencies, currencies_notional_values, currencies_avg_rank)
        
        # Calculate portfolio volatilty for each asset class
        indexes_vol = self.AnnualPortfolioVolatility(indexes_weights)
        commodities_vol = self.AnnualPortfolioVolatility(commodities_weights)
        goverment_bonds_vol = self.AnnualPortfolioVolatility(goverment_bonds_weights)
        currencies_vol = self.AnnualPortfolioVolatility(currencies_weights)
        
        # Calculate asset class weights.
        # List returned from self.AssetClassWeights:
        # [indexes_ac_weight, commodities_ac_weight, govermnet_bonds_ac_weight, currencies_ac_weight]
        ac_weights = self.AssetClassWeights(indexes_vol, commodities_vol, goverment_bonds_vol, currencies_vol)
        
        if len(ac_weights) == 0:
            return
        
        # Trade execution.
        for symbol, weight in indexes_weights:
            leverage = self.volatility_target / indexes_vol
            leverage = min(leverage, self.leverage_cap)
            self.SetHoldings(symbol, weight * ac_weights[0] * leverage)    
            
        for symbol, weight in commodities_weights:
            leverage = self.volatility_target / commodities_vol
            leverage = min(leverage, self.leverage_cap)
            self.SetHoldings(symbol, weight * ac_weights[1] * leverage) 
            
        for symbol, weight in goverment_bonds_weights:
            leverage = self.volatility_target / goverment_bonds_vol
            leverage = min(leverage, self.leverage_cap)
            self.SetHoldings(symbol, weight * ac_weights[2] * leverage)
            
        for symbol, weight in currencies_weights:
            leverage = self.volatility_target / currencies_vol
            leverage = min(leverage, self.leverage_cap)
            self.SetHoldings(symbol, weight * ac_weights[3] * leverage)
                
def CreateWeights(self, symbols, notional_values, avg_rank):
    long = []
    short = []
    
    # Split symbols into long an short based on their rank.
    for symbol, notional_value in zip(symbols, notional_values):
        symbol_rank = notional_value - avg_rank
        
        if symbol_rank > 0:
            long.append([symbol, symbol_rank])
        elif symbol_rank
