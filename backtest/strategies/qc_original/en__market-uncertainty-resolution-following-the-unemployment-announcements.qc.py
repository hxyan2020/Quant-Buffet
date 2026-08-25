# Original QuantConnect / library Python
# locale=en slug="market-uncertainty-resolution-following-the-unemployment-announcements"
# Extracted from Strategy.pythonCodeHtml — NOT modified.

from AlgorithmImports import *
#endregion

class MarketUncertaintyResolutionFollowingTheUnemploymentAnnouncements(QCAlgorithm):

def Initialize(self):
    self.SetStartDate(2011, 1, 1) # VIX starts from 2011
    self.SetCash(100000)

    self.unemployment_rate_dates:list[datetime.datetime] = []

    csv:str = self.Download('data.quantpedia.com/backtesting_data/economic/UNEMPLOYMENT_RATE.csv')
    lines:list[str] = csv.split('\r\n')

    for line in lines[1:]: # skip header
        if line == '':
            continue

        split:list[str] = line.split(';')
        date_str:str = split[0]
        date:datetime.date = datetime.strptime(date_str, '%d.%m.%Y').date()
        self.unemployment_rate_dates.append(date)
    
    # subscribe vix
    self.continuous_contract:Future = self.AddFuture(Futures.Indices.VIX, resolution = Resolution.Minute,
                                              dataNormalizationMode = DataNormalizationMode.BackwardsRatio,
                                              dataMappingMode = DataMappingMode.FirstDayMonth,
                                              contractDepthOffset = 0)

def OnData(self, data: Slice):
    curr_time:datetime.datetime = self.Time
    curr_date:datetime.date = curr_time.date()
    next_day:datetime.date = curr_date + timedelta(days=1)

    # NOTE The futures listed in CME or CBOT have their data set in Chicago Time
    # EST -> Chicago time conversion
    if next_day in self.unemployment_rate_dates and curr_time.hour == 15 and curr_time.minute == 15:
        # buy VIX contract
        mapped_contract_symbol:Symbol = self.Securities[self.continuous_contract.Mapped].Symbol
        self.SetHoldings(mapped_contract_symbol, 1)

    elif curr_date in self.unemployment_rate_dates and curr_time.hour == 15 and curr_time.minute == 15:
        # sell VIX contract
        self.Liquidate()
