# Original QuantConnect / library Python
# locale=en slug="inventory-mispricing-predicts-oil-returns"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

from AlgorithmImports import *
#endregion
import data_tools
EXPIRY_MIN_DAYS = TimeSpan.FromDays(5)
EXPIRY_MAX_DAYS = TimeSpan.FromDays(35)
class InventoryMispricingPredictsOilReturns(QCAlgorithm):
def Initialize(self):
    self.SetStartDate(2012, 3, 27)
    self.SetCash(100000)
    self.max_missing_days = 14
    future = self.AddFuture(Futures.Energies.CrudeOilWTI, Resolution.Minute)
    future.SetFilter(EXPIRY_MIN_DAYS, EXPIRY_MAX_DAYS)
    
    self.active_future = None
    self.symbol = future.Symbol
    
    self.api_report = self.AddData(data_tools.APIOilReport, 'APIOilReport', Resolution.Daily).Symbol   # API data comes one day before EIAOilReport
    self.api_report_date = None
    self.eia_report = self.AddData(data_tools.EIAOilReport, 'EIAOilReport', Resolution.Daily).Symbol
    
def OnData(self, slice):
    # check if contract isn't None and if it is about to expire in 1 day
    if self.active_future and self.active_future.Expiry.date() - timedelta(days=1) = 29) or (self.Time.hour > 10)):
        self.Liquidate()
    
    # day after api report        
    if self.api_report_date and self.Time.date() == self.api_report_date:
        if self.active_future:
            
            # active contract is available
            # if  and self.Securities.ContainsKey(self.api_report) and self.Securities.ContainsKey(self.eia_report):
            if self.Time.hour == 9 and self.Time.minute == 31:
                
                api_actual = None
                eia_prior = None
                inv_level = None
                
                api_report = self.Securities[self.api_report].GetLastData()
                if api_report:
                    api_actual = api_report['actual']
                
                eia_report = self.Securities[self.eia_report].GetLastData()    # at 9:31 EIA report 'survey' and 'prior' columns should be available
                if eia_report:
                    eia_survey = eia_report['survey'] # Bloomberg median consensus
                    inv_level = eia_report['prior']
                
                if api_actual is not None and \
                    eia_survey is not None and \
                    inv_level is not None and \
                    inv_level != 0:
                    
                    # predictor = (api_actual - eia_survey) / inv_level
                    predictor = api_actual - (eia_survey / inv_level)
                    
                    # Sell (buy) WTI futures contracts 60 minutes before the EIA announcement and close the position 1 minute before the EIA announcement if the predictor is positive (negative).
                    if self.Securities[self.active_future.Symbol].IsTradable:
                        if predictor > 0:
                            self.SetHoldings(self.active_future.Symbol, -0.5)
                        else:
                            self.SetHoldings(self.active_future.Symbol, 0.5)
    else:
        if not all(self.Securities[x].GetLastData() and (self.Time.date() - self.Securities[x].GetLastData().Time.date()).days
