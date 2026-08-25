# Original QuantConnect / library Python
# locale=en slug="hazard-fear-in-commodity-markets"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

from AlgorithmImports import *
import numpy as np
import statsmodels.api as sm
#endregion
class HazardFearInCommodityMarkets(QCAlgorithm):
def Initialize(self):
    
    # TODO put these into csv
    file_names = ['ADVERSE_WEATHER', 'ADVERSE_WEATHER_CONDITIONS', 'ADVERSE_WEATHER_WARNING', 'BLIZZARD', 'BLIZZARD_RISK', 'BLIZZARD_WARNING', 'CATASTROPHIC_EVENTS', 'CATASTROPHIC_WEATHER', 'CATASTROPHIC_WEATHER_EVENTS', 'CLIMATE_CHANGE', 'CLIMATE_DISTURBANCE', 'COLD', 'COLD_SPELL', 'COLD_WEATHER', 'CYCLOGENESIS', 'CYCLONE', 'CYCLONE_RISK', 'CYCLONE_WARNING', 'DROUGHT', 'DROUGHT_RISK', 'DROUGHT_WARNING', 'DROUGHTS', 'DRY_WEATHER', 'EL_NINO_WEATHER', 'EXTREME_COLD', 'EXTREME_COLD_TEMPERATURES', 'EXTREME_HEAT', 'EXTREME_RAIN', 'EXTREME_TEMPERATURES', 'EXTREME_WEATHER', 'EXTREME_WIND', 'FLOOD', 'FLOOD_RISK', 'FLOOD_WARNING', 'FLOODING', 'FLOODS', 'FOREST_FIRE', 'FOREST_FIRES', 'FREEZE_WARNING', 'FROST', 'FROST_RISK', 'FROST_WARNING', 'FROSTS', 'GLOBAL_WARMING', 'GUST', 'GUSTS', 'HAIL', 'HAIL_DAMAGE', 'HAIL_RISK', 'HAIL_STORM', 'HAIL_STORM_WARNING', 'HAIL_WARNING', 'HARMATTAN_WIND', 'HEAT', 'HEAT_WAVE', 'HEAT_WAVES', 'HEATWAVE', 'HEATWAVES', 'HEAVY_RAIN', 'HEAVY_RAIN_FALL', 'HEAVY_RAIN_RISK', 'HEAVY_RAIN_WARNING', 'HIGH_TEMPERATURE', 'HIGH_TEMPERATURES', 'HOT_WEATHER', 'HURRICANE', 'HURRICANE_RISK', 'HURRICANE_WARNING', 'HURRICANES', 'NATURAL_DISASTER', 'NATURAL_HAZARD', 'RAIN', 'SEVERE_HEAT', 'SEVERE_WEATHER', 'SEVERE_WEATHER_RISK', 'SNOW', 'SNOW_RISK', 'SNOW_STORM_WARNING', 'SNOW_WARNING', 'STORM', 'STORM_RISK', 'STORM_WARNING', 'STRONG_WIND', 'STRONG_WIND_GUST', 'TORNADO', 'TORNADO_RISK', 'TORNADO_WARNING', 'TORRENTIAL_RAIN', 'TROPICAL_CYCLONE', 'TROPICAL_CYCLONE_RISK', 'TROPICAL_CYCLONE_WARNING', 'TROPICAL_STORM', 'TROPICAL_STORM_RISK', 'TROPICAL_STORM_WARNING', 'TROPICAL_WEATHER', 'TYPHOON', 'TYPHOON_RISK', 'TYPHOON_WARNING', 'WEATHER_BLIZZARD_WARNING', 'WEATHER_RISK', 'WEATHER_WARNING', 'WET_WEATHER', 'WILDFIRE', 'WILDFIRE_RISK', 'WILDFIRE_WARNING', 'WILDFIRES', 'WIND', 'WIND_GUST', 'WIND_GUSTS', 'WIND_RISK', 'WIND_SPEED', 'WIND_STORM', 'WIND_WARNING', 'CROP_DISEASES', 'CROP_PEST', 'CROP_PEST_RISK', 'CROP_PESTS', 'EBOLA', 'INSECT_PEST', 'LA_ROYA', 'PEST_CONTROL', 'PEST_RISK', 'RUST_COFFE', 'AFRICA_INSTABILITY', 'AFRICA_TERRORISM', 'LIBYAN_CRISIS', 'MIDDLE_EAST_CONFLICT', 'MIDDLE_EAST_INSTABILITY', 'MIDDLE_EAST_TERRORISM', 'OIL_CRISIS', 'OIL_EMBARGO', 'OIL_OUTAGE', 'RUSSIAN_CRISIS', 'SYRIAN_WAR', 'TERRORISM', 'TERRORIST_ATTACK', 'TERRORIST_ATTACKS', 'CRISIS', 'ECONOMIC_CRISIS', 'ECONOMIC_RECESSION', 'FINANCIAL_CRISIS', 'RECESSION', 'RECESSION_2008', 'RECESSION_DEPRESSION', 'THE_RECESSION', 'UNEMPLOYMENT', 'UNEMPLOYMENT_RATE', 'US_RECESSION', 'US_UNEMPLOYMENT']
    
    self.SetStartDate(2004, 1, 1) # Google search data are since 2004
    self.SetCash(100000)
    
    self.months = 36
    self.quantile = 5
    self.max_missing_days = 31
    
    self.data = {} # Storing commodities prices
    self.google_search_values = {} # Storing seach values for each search
    
    self.symbols = [
                    "CME_S1", # Soybean Futures, Continuous Contract
                    "CME_W1", # Wheat Futures, Continuous Contract
                    "CME_SM1", # Soybean Meal Futures, Continuous Contract
                    "CME_BO1", # Soybean Oil Futures, Continuous Contract
                    "CME_C1", # Corn Futures, Continuous Contract
                    "CME_O1", # Oats Futures, Continuous Contract
                    "CME_LC1", # Live Cattle Futures, Continuous Contract
                    "CME_FC1", # Feeder Cattle Futures, Continuous Contract
                    "CME_LN1", # Lean Hog Futures, Continuous Contract
                    "CME_GC1", # Gold Futures, Continuous Contract
                    "CME_SI1", # Silver Futures, Continuous Contract
                    "CME_PL1", # Platinum Futures, Continuous Contract
                    "CME_CL1", # Crude Oil Futures, Continuous Contract
                    "CME_HG1", # Copper Futures, Continuous Contract
                    "CME_LB1", # Random Length Lumber Futures, Continuous Contract
                    "CME_NG1", # Natural Gas (Henry Hub) Physical Futures, Continuous Contract
                    "CME_PA1", # Palladium Futures, Continuous Contract
                    "CME_RR1", # Rough Rice Futures, Continuous Contract
                    "CME_DA1", # Class III Milk Futures
                    
                    "ICE_CC1", # Cocoa Futures, Continuous Contract
                    "ICE_CT1", # Cotton No. 2 Futures, Continuous Contract
                    "ICE_KC1", # Coffee C Futures, Continuous Contract
                    "ICE_O1", # Heating Oil Futures, Continuous Contract
                    "ICE_OJ1", # Orange Juice Futures, Continuous Contract
                    "ICE_SB1", # Sugar No. 11 Futures, Continuous Contract
                    "ICE_TF1" # ICE Endex Dutch TTF 1-Month Calendar Spread Options
                    "ICE_RS1",  # Canola Futures, Continuous Contract
                    "ICE_GO1",  # Gas Oil Futures, Continuous Contract
                    "ICE_WT1",  # WTI Crude Futures, Continuous Contract
                    "CME_RB2",  # Gasoline Futures, Continuous Contract
                    "CME_KW2",  # Wheat Kansas, Continuous Contract
    ]
        
    # Subscribe to all symbols
    for symbol in self.symbols:
        data = self.AddData(QuantpediaFutures, symbol, Resolution.Daily)
        data.SetFeeModel(CustomFeeModel())
        data.SetLeverage(5)
        
        self.data[symbol] = SymbolData(self.months)
    
    for search_value in file_names:
        # Subscribe to QuantpediaGoogleSearch with csv name
        symbol = self.AddData(QuantpediaGoogleSearch, search_value, Resolution.Daily).Symbol
        
        # Add subscribed symbol to self.google_search_values
        self.google_search_values[symbol] = GoogleSearchValues(self.months)
    
    self.symbol = self.AddEquity('SPY', Resolution.Daily).Symbol
    
    self.selection_flag = False
    self.Schedule.On(self.DateRules.MonthStart(self.symbol), self.TimeRules.AfterMarketOpen(self.symbol), self.Selection)
def OnData(self, data):
    # Google search data comes at the start of each month
    for symbol in self.google_search_values:
        if symbol in data and data[symbol]:
            value = data[symbol].Value
            self.google_search_values[symbol].update(value, self.Time.date())
    
    # Rebalance monthly
    if not self.selection_flag:
        return
    self.selection_flag = False
    
    # Calculate and store monthly return for each Quantpedia Future
    for symbol in self.data:
        if symbol in data and data[symbol]:
            value = data[symbol].Value
            
            # Calculate monthly return, if last_price is ready
            if self.data[symbol].last_price != 0:
                self.data[symbol].update(value)
                
            # Initialize new last_price for next monthly return calculation
            self.data[symbol].last_price = value
    
    # Check if at least one monthly returns for Quantpedia Futures are ready.
    if not self.data[self.symbols[0]].is_ready():
        return
    
    # Nextly, calculate the weekly(monthly in our case) log change in the Google search volume
    # for each keyword and divide it by the standard deviation of search volume for each keyword.
    
    keywords_std = []
    keywords_monthly_changes = {}
    
    # Calculate std for each google search value,
    # which has enough data and they aren't only zeros
    for symbol, google_search in self.google_search_values.items():
        # Check if google search value is ready
        if google_search.is_ready(self.Time.date(), self.max_missing_days):
            search_values = [x for x in google_search.n_search_values][::-1]  # normalized search volumes
            
            # Calculate std for current google search value
            google_search_std = np.std(search_values)
            keywords_std.append(google_search_std)
            
            # Calculate monthly changes for each google search
            monthly_changes = self.CalculateMonthlyChanges(search_values)
            
            # Store monthly changes of google search under it's symbol
            keywords_monthly_changes[symbol] = monthly_changes  
    
    # We can't perform regression, because monhtly changes for any keyword aren't ready        
    if len(keywords_monthly_changes) == 0:
        self.Liquidate()
        return
                
    # Standard deviation of search volume for each keyword
    sum_keywords_std = sum(keywords_std)
    
    # regression_x dictionary has stored x regression value for each keyword
    regression_x = self.CreateRegressionXForEachKeyWord(
        keywords_monthly_changes,
        sum_keywords_std
    )
    
    # Storing CFEAR as value under commodity symbol as a key
    CFEAR = {}
    
    # Calculation for each commodity
    for symbol, symbol_data in self.data.items():
        # Make regression only if commodity has ready data
        if not symbol_data.is_ready():
            continue
        
        significant_betas = [] 
        monthly_returns = [x for x in symbol_data.monthly_returns][::-1]
        
        # Make regression for each keyword
        for google_search_symbol, x in regression_x.items():
            regression_model = self.MultipleLinearRegression(x, monthly_returns)
            
            # Get regression beta and t-stat for this beta from regression model of this keyword
            beta = regression_model.params[-1]
            t_stat_beta = regression_model.tvalues[-1]
            
            # Store betas, which t-stat is statistically significant
            if abs(t_stat_beta) > 0.8:
                significant_betas.append(beta)
        
        if len(significant_betas) != 0:
            # CFEAR = sum of all significant betas for each keyword
            CFEAR[symbol] = sum(significant_betas)
    
    # Continue only if we will have enough data for quintile selection
    if len(CFEAR) = self.period:
        max_search_vol = max(self.search_values)
        if max_search_vol != 0:
            n_search_vol = search_value / max_search_vol
        else:
            n_search_vol = 0
        self.n_search_values.Add(n_search_vol)
    
def is_ready(self, curr_date, max_missing_days):
    return self.n_search_values.IsReady and (curr_date - self.last_update_time).days
