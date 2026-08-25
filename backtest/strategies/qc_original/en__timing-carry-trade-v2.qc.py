# Original QuantConnect / library Python
# locale=en slug="timing-carry-trade-v2"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

from AlgorithmImports import *
import data_tools
import numpy as np
import pandas as pd
import statsmodels.formula.api as sm
#endregion
class TimingCarryTradeV2(QCAlgorithm):
def Initialize(self):
    self.SetStartDate(2009, 1, 1)
    self.SetCash(100000)
    self.tickers:dict[str, str] = {
        "CME_AD1" : Futures.Currencies.AUD, # Australian Dollar Futures, Continuous Contract #1
        "CME_BP1" : Futures.Currencies.GBP, # British Pound Futures, Continuous Contract #1
        "CME_CD1" : Futures.Currencies.CAD, # Canadian Dollar Futures, Continuous Contract #1
        "CME_EC1" : Futures.Currencies.EUR, # Euro FX Futures, Continuous Contract #1
        "CME_JY1" : Futures.Currencies.JPY, # Japanese Yen Futures, Continuous Contract #1
        "CME_MP1" : Futures.Currencies.MXN, # Mexican Peso Futures, Continuous Contract #1
        "CME_NE1" : Futures.Currencies.NZD, # New Zealand Dollar Futures, Continuous Contract #1
        "CME_SF1" : Futures.Currencies.CHF, # Swiss Franc Futures, Continuous Contract #1
    }
                    
    self.month_period:int = 21
    self.avg_vol_period:int = 4
    self.regression_period:int = 12
    self.max_missing_days:int = 5
    self.min_expiration_days:int = 2
    self.max_expiration_days:int = 360
    self.SetWarmUp(12 * self.month_period, Resolution.Daily) # one year warm up
    
    self.data:dict[Symbol, data_tools.SymbolData] = {}
    self.futures_data:dict[str, data_tools.FuturesData] = {}
    
    # Monthly average currency volatility.
    self.avg_vol:RollingWindow = RollingWindow[float](self.avg_vol_period)
    
    # MSCI world equity price index
    self.msci:Symbol = self.AddEquity('URTH',  Resolution.Daily).Symbol
    self.data[self.msci] = data_tools.SymbolData(4 * self.month_period) # 4 months
    
    # 12 months of regression data.
    self.regression_data:data_tools.RegressionData = data_tools.RegressionData(self.regression_period)
    
    # Raw Industrials Spot Commodity Index.
    self.dbb:Symbol = self.AddEquity('DBB',  Resolution.Daily).Symbol
    self.data[self.dbb] = data_tools.SymbolData(4 * self.month_period) # 4 months
    
    for qp_ticker, qc_ticker in self.tickers.items():
        security:Security = self.AddData(data_tools.QuantpediaFutures, qp_ticker, Resolution.Daily)
        security.SetFeeModel(data_tools.CustomFeeModel())
        security.SetLeverage(5)
        qp_symbol:Symbol = security.Symbol
        self.data[qp_symbol] = data_tools.SymbolData(12 * self.month_period) # one year
        # QC futures
        future:Future = self.AddFuture(qc_ticker, Resolution.Daily, dataNormalizationMode=DataNormalizationMode.Raw)
        future.SetFilter(timedelta(days=self.min_expiration_days), timedelta(days=self.max_expiration_days))
        self.futures_data[future.Symbol.Value] = data_tools.FuturesData(qp_symbol)
    self.recent_month:int = -1
    self.Settings.MinimumOrderMarginPortfolioPercentage = 0.
def FindAndUpdateContracts(self, futures_chain, ticker) -> None:
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
                    raw_price1:float = data[near_c.Symbol].Value * self.Securities[ticker].SymbolProperties.PriceMagnifier
                    raw_price2:float = data[dist_c.Symbol].Value * self.Securities[ticker].SymbolProperties.PriceMagnifier
                    if raw_price1 != 0 and raw_price2 != 0:
                        future_obj.update_roll_return(raw_price1, raw_price2, curr_date)
    # update daily prices of QP futures and indexes
    for symbol, symbol_obj in self.data.items():
        if symbol in data and data[symbol]:
            price:float = data[symbol].Value
            symbol_obj.update(price, curr_date)
    # rebalacne monthly
    if self.IsWarmingUp or (self.recent_month == self.Time.month):
        return
    self.recent_month = self.Time.month
    roll_return:dict[Symbol, float] = {}
    volatility:dict[Symbol, float] = {}
    last_update_date:Dict[str, datetime.date] = data_tools.QuantpediaFutures.get_last_update_date()
    for ticker, future_obj in self.futures_data.items():
        qp_symbol:Symbol = future_obj.quantpedia_future
        
        if qp_symbol.Value in last_update_date and self.Time.date()  0:
                Y:float = self.RegressionPrediction(
                    list_of_series=[msci_changes, vol_three_months_changes, monthly_returns],
                    columns=['msci_changes', 'vol_three_months_changes', 'monthly_returns'],
                    formula='monthly_returns ~ msci_changes + vol_three_months_changes',
                    X1=msci_change,
                    X2=vol_change_three_months
                )
                if Y > 0:
                    long_part.append(qp_symbol)
                
            else:
                Y:float = self.RegressionPrediction(
                    list_of_series=[dbb_changes, vol_two_months_changes, monthly_returns],
                    columns=['dbb_changes', 'vol_two_months_changes', 'monthly_returns'],
                    formula='monthly_returns ~ dbb_changes + vol_two_months_changes',
                    X1=dbb_change,
                    X2=vol_change_two_months
                )
                if Y  list:
    prices:list[float] = [x for x in prices_roll_window]
    monthly_returns:list[float] = [data_tools.Return(prices[x:x+self.month_period]) for x in range(0, len(prices), self.month_period)]
    return monthly_returns
def RegressionPrediction(self, list_of_series:list, columns:list, formula:str, X1:pd.Series, X2:pd.Series) -> float:
    data_frame:pd.DataFrame = pd.concat(list_of_series, axis=1).dropna()
    data_frame.columns = columns
    model = sm.ols(formula=formula, data=data_frame).fit()
    
    alpha:float = model.params[0]
    beta:float = model.params[1]
    
    # Expected symbol return.
    return alpha + (beta * X1) + (beta * X2)
