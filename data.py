import pandas as pd

# source: https://fred.stlouisfed.org/series/SP500
data = pd.read_csv('SP500.csv', parse_dates=['observation_date'])
data['observation_date'] = pd.to_datetime(data['observation_date'])
# Drop missing values
data = data.dropna()
data.to_csv('SP500.csv', index=False)
