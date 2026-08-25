# Original QuantConnect / library Python
# locale=en slug="robust-quality-in-stocks"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

from AlgorithmImports import *
from scipy import stats
from typing import List, Dict
from numpy import isnan
#endregion
class RobustQualityInStocks(QCAlgorithm):
def Initialize(self) -> None:
    self.SetStartDate(2000, 1, 1)
    self.SetCash(100_000)
    self.period: int = 4 # need n of quarterly data
    self.leverage: int = 10
    self.quantile: int = 5
    self.min_share_price: int = 5
    self.data: Dict[Symbol, SymbolData] = {}
    self.weights: Dict[Symbol, float] = {}
    self.last_selection: List[Symbol] = []
    market: Symbol = self.AddEquity('SPY', Resolution.Daily).Symbol
    self.months_counter: int = 0
    self.selection_flag: bool = False
    self.UniverseSettings.Leverage = self.leverage
    self.UniverseSettings.Resolution = Resolution.Daily
    self.AddUniverse(self.FundamentalSelectionFunction)
    self.Settings.MinimumOrderMarginPortfolioPercentage = 0.
    self.Schedule.On(self.DateRules.MonthStart(market), self.TimeRules.BeforeMarketClose(market, 0), self.Selection)
    self.settings.daily_precise_end_time = False
def OnSecuritiesChanged(self, changes: SecurityChanges) -> None:
    for security in changes.AddedSecurities:
        security.SetFeeModel(CustomFeeModel())
def FundamentalSelectionFunction(self, fundamental: List[Fundamental]) -> List[Symbol]:
    # quarterly rebalance
    if not self.selection_flag:
        return Universe.Unchanged
    selected = [
        x for x in fundamental 
        if x.HasFundamentalData 
        and x.Market == 'usa' 
        and x.Price > self.min_share_price
        and x.MarketCap != 0
        and not isnan(x.FinancialStatements.IncomeStatement.GrossProfit.ThreeMonths) and x.FinancialStatements.IncomeStatement.GrossProfit.ThreeMonths != 0 
        and not isnan(x.FinancialStatements.BalanceSheet.TotalAssets.ThreeMonths) and x.FinancialStatements.BalanceSheet.TotalAssets.ThreeMonths != 0 
        and not isnan(x.FinancialStatements.BalanceSheet.WorkingCapital.ThreeMonths) and x.FinancialStatements.BalanceSheet.WorkingCapital.ThreeMonths != 0 
        and not isnan(x.FinancialStatements.CashFlowStatement.CapExReported.ThreeMonths) and x.FinancialStatements.CashFlowStatement.CapExReported.ThreeMonths != 0 
        and not isnan(x.FinancialStatements.IncomeStatement.TotalRevenue.ThreeMonths) and x.FinancialStatements.IncomeStatement.TotalRevenue.ThreeMonths != 0
        and not isnan(x.OperationRatios.ROIC.OneYear) and x.OperationRatios.ROIC.OneYear != 0 
        and not isnan(x.OperationRatios.LongTermDebtEquityRatio.OneYear) and x.OperationRatios.LongTermDebtEquityRatio.OneYear != 0 
        and not isnan(x.OperationRatios.TotalAssetsGrowth.OneYear) and x.OperationRatios.TotalAssetsGrowth.OneYear != 0 
        # and not isnan(x.FinancialStatements.CashFlowStatement.ChangeInOtherCurrentAssets.ThreeMonths) and x.FinancialStatements.CashFlowStatement.ChangeInOtherCurrentAssets.ThreeMonths != 0 
        # and not isnan(x.FinancialStatements.CashFlowStatement.ChangeInInventory.ThreeMonths) and x.FinancialStatements.CashFlowStatement.ChangeInInventory.ThreeMonths != 0 
        # and not isnan(x.FinancialStatements.CashFlowStatement.ChangeInReceivables.ThreeMonths) and x.FinancialStatements.CashFlowStatement.ChangeInReceivables.ThreeMonths != 0 
        # and not isnan(x.OperationRatios.TotalLiabilitiesGrowth.OneYear) and x.OperationRatios.TotalLiabilitiesGrowth.OneYear != 0 
        # and not isnan(x.FinancialStatements.IncomeStatement.Depreciation.TwelveMonths) and x.FinancialStatements.IncomeStatement.Depreciation.TwelveMonths != 0
        and not isnan(x.FinancialStatements.IncomeStatement.NetIncome.TwelveMonths) and x.FinancialStatements.IncomeStatement.NetIncome.TwelveMonths != 0 
        and not isnan(x.FinancialStatements.CashFlowStatement.OperatingCashFlow.TwelveMonths) and x.FinancialStatements.CashFlowStatement.OperatingCashFlow.TwelveMonths != 0 
        and not isnan(x.FinancialStatements.CashFlowStatement.InvestingCashFlow.TwelveMonths) and x.FinancialStatements.CashFlowStatement.InvestingCashFlow.TwelveMonths != 0 
        and not isnan(x.FinancialStatements.BalanceSheet.Cash.ThreeMonths) and x.FinancialStatements.BalanceSheet.Cash.ThreeMonths != 0 
        and not isnan(x.FinancialStatements.BalanceSheet.TotalLiabilitiesAsReported.ThreeMonths) and x.FinancialStatements.BalanceSheet.TotalLiabilitiesAsReported.ThreeMonths != 0 
        and not isnan(x.FinancialStatements.BalanceSheet.CurrentDebt.ThreeMonths) and x.FinancialStatements.BalanceSheet.CurrentDebt.ThreeMonths != 0 
        and not isnan(x.FinancialStatements.BalanceSheet.LongTermDebt.ThreeMonths) and x.FinancialStatements.BalanceSheet.LongTermDebt.ThreeMonths != 0
    ]
    market_cap: Dict[Symbol, float] = {} # storing stocks market capitalization keyed by stocks symbols
    # storing metrics values keyed by stock symbols
    GPA: Dict[Symbol, float] = {} # GrossProfit / TotalAssets
    CFROIC: Dict[Symbol, float] = {} # ROIC.TwelveMonths
    LTDE: Dict[Symbol, float] = {} # LongTermDebtEquityRatio.TwelveMonths
    AG1Y: Dict[Symbol, float] = {} # TotalAssetsGrowth.TwelveMonths
    WCA: Dict[Symbol, float] = {} # WorkingCapital / TotalAssets
    Capex: Dict[Symbol, float] = {} # CapExReported / TotalRevenue
    # WCAcc: Dict[Symbol, float] = {} # (ChangeInOtherCurrentAssets + ChangeInInventor + ChangeInReceivables) / mean TA - TotalLiabilitiesGrowth / mean TA - Depreciation / mean TA
    AccCF: Dict[Symbol, float] = {} # 
    for stock in selected:
        symbol: Symbol = stock.Symbol
        total_assets: float = stock.FinancialStatements.BalanceSheet.TotalAssets.ThreeMonths # TA
        gross_profit: float = stock.FinancialStatements.IncomeStatement.GrossProfit.ThreeMonths
        working_capital: float = stock.FinancialStatements.BalanceSheet.WorkingCapital.ThreeMonths
        cap_ex_reported: float = stock.FinancialStatements.CashFlowStatement.CapExReported.ThreeMonths
        total_revenue: float = stock.FinancialStatements.IncomeStatement.TotalRevenue.ThreeMonths
        # get all needed values for NOA calculation
        cash: float = stock.FinancialStatements.BalanceSheet.Cash.ThreeMonths # CHEi in formula for NOA
        total_liabilities_as_reported: float = stock.FinancialStatements.BalanceSheet.TotalLiabilitiesAsReported.ThreeMonths  # LT in formula for NOA
        current_debt: float = stock.FinancialStatements.BalanceSheet.CurrentDebt.ThreeMonths # DLC in formula for NOA
        long_term_debt: float = stock.FinancialStatements.BalanceSheet.LongTermDebt.ThreeMonths # DLTT in formula for NOA
        # make sure data are consecutive
        if symbol not in self.last_selection:
            self.data[symbol] = SymbolData(self.period)
        # calculate NOA for this quarter
        # NOA = mean(TA - CHEi) - mean(LT-DLC-DLTT)
        mean_TA_CHEi: float = np.mean([total_assets, cash])
        mean_LT_DLC_DLTT: float = np.mean([total_liabilities_as_reported, current_debt, long_term_debt])
        noa_value: float = mean_TA_CHEi - mean_LT_DLC_DLTT
        # update NOA values
        self.data[symbol].update_NOA(noa_value)
        # update quarterly values
        self.data[symbol].update_total_assets(total_assets)
        gpa_value: float = gross_profit / total_assets
        self.data[symbol].update_GPA(gpa_value)
        wca_value: float = working_capital / total_assets
        self.data[symbol].update_WCA(wca_value)
        capex_value: float = cap_ex_reported / total_revenue
        self.data[symbol].update_Capex(capex_value)
        # check if all quarterly data are ready for metrics calculations
        if not self.data[symbol].are_quarterly_data_ready():
            continue
        # data for each metric are ready
        # calculate and store metrics
        GPA[symbol] = self.data[symbol].calculate_GPA()
        CFROIC[symbol] = stock.OperationRatios.ROIC.OneYear
        LTDE[symbol] = stock.OperationRatios.LongTermDebtEquityRatio.OneYear
        AG1Y[symbol] = stock.OperationRatios.TotalAssetsGrowth.OneYear
        WCA[symbol] = self.data[symbol].calculate_WCA()
        Capex[symbol] = self.data[symbol].calculate_Capex()
        # # get all needed values for WCAcc metric
        # change_in_other_current_assets = stock.FinancialStatements.CashFlowStatement.ChangeInOtherCurrentAssets.ThreeMonths
        # change_in_inventory = stock.FinancialStatements.CashFlowStatement.ChangeInInventory.ThreeMonths
        # change_in_receivables = stock.FinancialStatements.CashFlowStatement.ChangeInReceivables.ThreeMonths
        # total_liabilities = stock.OperationRatios.TotalLiabilitiesGrowth.OneYear / 4
        # depreciation = stock.FinancialStatements.IncomeStatement.Depreciation.TwelveMonths
        # mean_total_assets = self.data[symbol].mean_total_assets()
        # # calculate parts of WCAcc formula
        # first_formula_part = (change_in_other_current_assets + change_in_inventory + change_in_receivables) / mean_total_assets
        # second_formula_part = total_liabilities / mean_total_assets
        # third_formula_part = depreciation / mean_total_assets
        # # calculate WCAcc value
        # wcacc_value = first_formula_part - second_formula_part - third_formula_part
        # # store WCAcc metric value keyed by stock's symbol
        # WCAcc[symbol] = wcacc_value
        # get all needed values for AccCF
        net_income: float = stock.FinancialStatements.IncomeStatement.NetIncome.TwelveMonths
        operating_cashflow: float = stock.FinancialStatements.CashFlowStatement.OperatingCashFlow.TwelveMonths
        investing_cashflow: float = stock.FinancialStatements.CashFlowStatement.InvestingCashFlow.TwelveMonths
        # get NOA values for specific quarters
        current_quarter_NOA, fourth_quarter_NOA = self.data[symbol].get_NOA_values()
        # calculate NOA formula part for AccCF formula
        NOA_formula_part: float = (current_quarter_NOA + fourth_quarter_NOA) / 2
        # calculate AccCF value
        acccf_value: float = (net_income - (operating_cashflow + investing_cashflow)) / NOA_formula_part
        # store AccCF value keyed by stock's symbol
        AccCF[symbol] = acccf_value
        # store stock's market capitalization
        market_cap[symbol] = stock.MarketCap
    # change last_selection for consecutive data
    self.last_selection = [x.Symbol for x in selected]
    # make sure, there are enough data for quintile selection
    if len(GPA)  None:
    if not self.selection_flag:
        return
    self.selection_flag = False
    # trade exectuion
    portfolio: List[PortfolioTarget] = [PortfolioTarget(symbol, w) for symbol, w in self.weights.items() if slice.contains_key(symbol) and slice[symbol]]
    self.SetHoldings(portfolio, True)
    self.weights.clear()
def CalculatePercentiles(self, metric_dict: Dict[Symbol, float]) -> Dict[Symbol, float]:
    ''' create and return dictionary with percentile values of metric keyed by stock symbol '''
    # return dict of stocks percentiles values keyed by their symbols    
    metric_percentiles: Dict[Symbol, float] = { x[0] : stats.percentileofscore(list(metric_dict.values()), x[1]) for x in metric_dict.items() }
    return metric_percentiles
def CalculateDimensionValues(self, 
                            metric1_percentiles: Dict[Symbol, float], 
                            metric2_percentiles: Dict[Symbol, float]) -> Dict[Symbol, float]:
    ''' create and return dictionary of dimension values keyed by stocks symbols '''
    dimension_values: Dict[Symbol, float] = {} # storing dimension values keyed by stocks symbols
    # calculate and store stock dimension values
    for stock_symbol, stock_percentile_1 in metric1_percentiles.items():
        if len(metric2_percentiles) > 0:
            # get stock's percentile from second metric in current dimension
            stock_percentile_2: float = metric2_percentiles[stock_symbol]
            # calculate dimension value
            # dimension value = mean of stock's percentile from first and second metric in current division
            dimension_value: float = np.mean([stock_percentile_1, stock_percentile_2])
            # store stock's dimension value keyed by stock's symbol
            dimension_values[stock_symbol] = dimension_value
        else:
            # store stock's dimension value keyed by stock's symbol
            dimension_values[stock_symbol] = stock_percentile_1
    # return dictionary of dimension values keyed by stocks symbols
    return dimension_values
def CalculateDimensionZScore(self, dimension_dict: Dict[Symbol, float]) -> Dict[Symbol, float]:
    ''' create and return dictionary of z-score values for each stock in dimension keyed by their symbols '''
    dimension_values: List[float] = [value for _, value in dimension_dict.items()]
    dimension_mean: float = np.mean(dimension_values)
    dimension_std: float = np.std(dimension_values)
    dimension_z_score: Dict[Symbol, float] = {} # storing stocks z-score values keyed by their symbols
    # calculate and store z-score for each stock in dimension
    for stock_symbol, value in dimension_dict.items():
        z_score: float = (value - dimension_mean) / dimension_std
        # store stock's z-score keyed by stock's symbol
        dimension_z_score[stock_symbol] = z_score
    # return dictionary with stocks z-scores keyed by their symbols
    return dimension_z_score
def CalculateQualityFactor(self, 
                        dimension_dict1: Dict[Symbol, float], 
                        dimension_dict2: Dict[Symbol, float], 
                        dimension_dict3: Dict[Symbol, float], 
                        dimension_dict4: Dict[Symbol, float]) -> Dict[Symbol, float]:
    ''' create and return dictionary of quality factor values keyed by stocks symbols '''
    quality_factor: Dict[Symbol, float] = {} # storing quality factor values keyed by stocks symbols
    for stock_symbol, z_score1 in dimension_dict1.items():
        z_score2: float = dimension_dict2[stock_symbol]
        z_score3: float = dimension_dict3[stock_symbol]
        z_score4: float = dimension_dict4[stock_symbol]
        # calculate stock's quality factor based on dimensions z-scores
        quality_factor_value: float = np.mean([z_score1, z_score2, z_score3, z_score4])
        # store stock's quality factore keyed by stock's symbols
        quality_factor[stock_symbol] = quality_factor_value
    # return dictionary of quality factor values keyed by stocks symbols
    return quality_factor
def Selection(self) -> None:
    # quarterly rebalance
    if self.months_counter % 3 == 0:
        self.selection_flag = True
    self.months_counter += 1
class SymbolData():
def __init__(self, period: int) -> None:
    self.GPA: RollingWindow = RollingWindow[float](period)
    self.WCA: RollingWindow = RollingWindow[float](period)
    self.Capex: RollingWindow = RollingWindow[float](period)
    self.total_assets: RollingWindow = RollingWindow[float](period)
    self.NOA: RollingWindow = RollingWindow[float](period)
def update_NOA(self, noa_value: float) -> None:
    self.NOA.Add(noa_value)
def update_total_assets(self, total_assets_value: float) -> None:
    self.total_assets.Add(total_assets_value)
def update_GPA(self, gpa_value: float) -> None:
    self.GPA.Add(gpa_value)
def update_WCA(self, wca_value: float) -> None:
    self.WCA.Add(wca_value)
def update_Capex(self, capex_value: float) -> None:
    self.Capex.Add(capex_value)
def are_quarterly_data_ready(self) -> bool:
    return self.GPA.IsReady and self.WCA.IsReady and self.Capex.IsReady and self.total_assets.IsReady and self.NOA.IsReady
def mean_total_assets(self) -> float:
    total_assets_values = [x for x in self.total_assets]
    return np.mean(total_assets_values)
def get_NOA_values(self) -> float:
    noa_values = [x for x in self.NOA]
    # return NOA values in quartet t and quarter t-4
    return noa_values[0], noa_values[-1]
def calculate_GPA(self) -> float:
    gpa_values = [x for x in self.GPA]
    return sum(gpa_values)
def calculate_WCA(self) -> float:
    wca_values = [x for x in self.WCA]
    return sum(wca_values)
def calculate_Capex(self) -> float:
    capex_values = [x for x in self.Capex]
    return sum(capex_values)
# Custom fee model.
class CustomFeeModel(FeeModel):
def GetOrderFee(self, parameters: OrderFeeParameters) -> OrderFee:
    fee: float = parameters.Security.Price * parameters.Order.AbsoluteQuantity * 0.00005
    return OrderFee(CashAmount(fee, "USD"))
