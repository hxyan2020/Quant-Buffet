# Original QuantConnect / library Python
# locale=en slug="changes-in-ownership-breadth-predict-performance-of-equity-factors"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

from AlgorithmImports import *
from typing import Dict, List, Set
from data_tools import QuantpediaHegdeFunds, CustomFeeModel, SymbolData
# endregion

class ChangesInOwnershipBreadthPredictPerformanceOfEquityFactors(QCAlgorithm):

def Initialize(self):
    self.SetStartDate(2010, 1, 1)
    self.SetCash(100000)
    
    self.leverage:int = 5
    self.months_lag:int = 2

    self.breadth_selection_quantile:int = 3
    self.anomaly_selection_quantile:int = 5

    self.mom_period:int = 21
    self.total_assets_period:int = 2
    self.mean_weights_period:int = 2

    self.max_missing_days:int = 3 * 31
    self.last_hedge_funds_update:datetime.date|None = None
    
    self.quantities:Dict[Symbol, float] = {}
    self.tickers_with_data:Dict[str, List[float]] = []
    self.data:Dict[str, SymbolData] = {}

    self.exchanges:List[str] = ['NYS', 'NAS', 'ASE']
    self.anomalies_symbols:List[str] = ['AG', 'GP', 'MOM', 'ROA', 'NSI', 'NPAY', 'OA']

    self.market:Symbol = self.AddEquity('SPY', Resolution.Daily).Symbol

    self.hedge_funds_symbol:Symbol = self.AddData(QuantpediaHegdeFunds, 'hedge_funds_holdings.json', Resolution.Daily).Symbol

    self.selection_flag:bool = False
    self.rebalance_flag:bool = False
    self.UniverseSettings.Resolution = Resolution.Daily
    self.AddUniverse(self.CoarseSelectionFunction, self.FineSelectionFunction)

def OnSecuritiesChanged(self, changes:SecurityChanges) -> None:
    for security in changes.AddedSecurities:
        security.SetFeeModel(CustomFeeModel())
        security.SetLeverage(self.leverage)

def CoarseSelectionFunction(self, coarse:List[CoarseFundamental]) -> List[Symbol]:
    for equity in coarse:
        ticker:Symbol = equity.Symbol.Value

        if ticker in self.data:
            self.data[ticker].update_prices(equity.AdjustedPrice)

    if not self.selection_flag:
        return Universe.Unchanged
    self.selection_flag = False
    self.rebalance_flag = True
    
    # select only stocks, which have current and previous mean weight
    selected_stocks:List[Symbol] = []
    for stock in coarse:
        symbol:Symbol = stock.Symbol
        ticker:str = symbol.Value

        if ticker not in self.tickers_with_data:
            continue
        
        # warm up prices if needed
        if not self.data[ticker].prices_ready():
            history = self.History(symbol, self.mom_period, Resolution.Daily)
            if not history.empty:
                closes = history.loc[symbol].close
                
                for _, close in closes.iteritems():
                    self.data[ticker].update_prices(close)

        selected_stocks.append(stock.Symbol)

    self.tickers_with_data.clear()

    return selected_stocks

def FineSelectionFunction(self, fine:List[FineFundamental]) -> List[Symbol]:
    curr_date:datetime.date = self.Time.date()
    stocks_with_data:List[FineFundamental] = []

    for stock in fine:
        if stock.MarketCap != 0 and stock.SecurityReference.ExchangeId in self.exchanges and stock.FinancialStatements.BalanceSheet.TotalAssets.ThreeMonths != 0 \
            and stock.FinancialStatements.IncomeStatement.GrossProfit.ThreeMonths != 0 and stock.OperationRatios.ROA.ThreeMonths != 0 \
            and stock.FinancialStatements.CashFlowStatement.IssuanceOfCapitalStock.ThreeMonths != 0 and stock.FinancialStatements.CashFlowStatement.RepurchaseOfCapitalStock.ThreeMonths != 0 \
            and stock.ValuationRatios.TotalYield != 0 and stock.FinancialStatements.CashFlowStatement.CommonStockIssuance.ThreeMonths != 0 \
            and stock.FinancialStatements.BalanceSheet.CurrentAssets.Value != 0 and stock.FinancialStatements.BalanceSheet.CurrentLiabilities.Value != 0:

            ticker:str = stock.Symbol.Value
            stock_data:SymbolData = self.data[ticker]

            # make sure data are consecutive
            if not stock_data.anomaly_data_still_coming(curr_date, self.max_missing_days):
                # each anomaly's data will be reset except momentum
                stock_data.reset_anomalies_data()

            total_assets:float = stock.FinancialStatements.BalanceSheet.TotalAssets.ThreeMonths
            gross_profit:float = stock.FinancialStatements.IncomeStatement.GrossProfit.ThreeMonths
            roa:float = stock.OperationRatios.ROA.ThreeMonths

            issuance_of_stock:float = stock.FinancialStatements.CashFlowStatement.IssuanceOfCapitalStock.ThreeMonths
            repurchase_of_stock:float = stock.FinancialStatements.CashFlowStatement.RepurchaseOfCapitalStock.ThreeMonths
            net_stock_issuance:float = issuance_of_stock - repurchase_of_stock

            market_cap:float = stock.MarketCap
            total_yield:float = stock.ValuationRatios.TotalYield
            common_stock_issuance:float = stock.FinancialStatements.CashFlowStatement.CommonStockIssuance.ThreeMonths
            net_payout:float = (total_yield * market_cap) / (common_stock_issuance / market_cap)

            operating_assets:float = stock.FinancialStatements.BalanceSheet.CurrentAssets.Value
            operating_liabilities:float = stock.FinancialStatements.BalanceSheet.CurrentLiabilities.Value
            net_operating_assets:float = operating_assets - operating_liabilities

            operating_accruals:float = stock_data.update_operating_accruals(net_operating_assets, total_assets) \
                if stock_data.net_operating_assets_ready() else None

            stock_data.update_net_operating_assets(net_operating_assets)
            if operating_accruals != None:
                stock_data.update_operating_accruals(operating_accruals)

            # update stock's anomalies data
            stock_data.update_total_assets_values(total_assets)
            stock_data.update_gross_profit(gross_profit)
            stock_data.update_roa(roa)
            stock_data.update_net_stock_issuance(net_stock_issuance)
            stock_data.update_net_payout(net_payout)
            stock_data.set_last_anomalies_update(curr_date)

            if stock_data.is_ready():
                stocks_with_data.append(stock)
    
    # make sure there are enough stocks for both seletion
    if len(stocks_with_data)  None:
    curr_date:datetime.date = self.Time.date()

    if self.hedge_funds_symbol in data and data[self.hedge_funds_symbol]:
        stocks_data:Dict[str, List[float]] = data[self.hedge_funds_symbol].GetProperty('stocks_with_weights')

        for ticker, weights in stocks_data.items():
            mean_weight:float = np.mean(weights)

            if ticker not in self.data:
                self.data[ticker] = SymbolData(self.mom_period, self.total_assets_period, self.mean_weights_period)

            # make sure mean weight values are consecutive
            if not self.data[ticker].weight_data_still_coming(curr_date, self.max_missing_days):
                self.data[ticker].reset_weights()

            self.data[ticker].update_mean_weights(curr_date, mean_weight)

            # stock will be selected in CoarseSelectionFuction only, if it has mean values ready
            if self.data[ticker].mean_weight_values_ready():
                self.tickers_with_data.append(ticker)

        self.last_hedge_funds_update = curr_date
        self.selection_flag = True

    if self.last_hedge_funds_update != None and (curr_date - self.last_hedge_funds_update).days > self.max_missing_days:
        # liquidate portfolio, when data stop coming
        self.Liquidate()

    if not self.rebalance_flag:
        return
    self.rebalance_flag = False

    self.Liquidate()
            
    for symbol, quantity in self.quantities.items():
        if self.Securities[symbol].IsTradable and self.Securities[symbol].Price != 0:
            self.MarketOrder(symbol, quantity)
            
    self.quantities.clear()

def CalculateAnomalies(self, stocks:List[FineFundamental]) -> Dict[str, Dict[FineFundamental, float]]:
    anomalies_data:Dict[str, Dict[FineFundamental, float]] = { anomaly_symbol: {} for anomaly_symbol in self.anomalies_symbols }
    
    for stock in stocks:
        ticker:str = stock.Symbol.Value
        stock_data:SymbolData = self.data[ticker]

        anomalies_data['AG'][stock] = stock_data.get_asset_growth()
        anomalies_data['GP'][stock] = stock_data.get_gross_profit()
        anomalies_data['MOM'][stock] = stock_data.get_momentum()
        anomalies_data['ROA'][stock] = stock_data.get_roa()
        anomalies_data['NSI'][stock] = stock_data.get_net_stock_issuance()
        anomalies_data['NPAY'][stock] = stock_data.get_net_payout()
        anomalies_data['OA'][stock] = stock_data.get_operating_accruals()

    return anomalies_data
