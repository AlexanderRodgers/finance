from alpha_vantage.timeseries import TimeSeries as ts
import bs4 as bs
import datetime as dt
import matplotlib.pyplot as plt
from matplotlib import style
import numpy as np
import os
import json
import pandas as pd
import pandas_datareader.data as web
import pickle
import requests
import csv
from pprint import pprint

# Setting up API
series = ts(key='I67BO05UHWQOTS4E', output_format='pandas', indexing_type='date')
data, metadata = series.get_daily_adjusted(symbol='MSFT', outputsize='full')
#pprint(data.head(5))

#Getting S&P ticker symbols
def save_sp500_tickers():
    resp = requests.get('https://en.wikipedia.org/wiki/List_of_S%26P_500_companies')
    soup = bs.BeautifulSoup(resp.text, 'lxml')
    table = soup.find('table', {'class': 'wikitable sortable'})
    tickers = []
    for row in table.findAll('tr')[1:]:
        ticker = row.findAll('td')[0].text
        tickers.append(ticker)

    with open('sp500tickers.pickle', 'wb') as f:
        pickle.dump(tickers, f)

        print(tickers)
        return tickers

def get_data(reload_sp500=False):
    if reload_sp500:
        tickers = save_sp500_tickers()

    else:
        with open('sp500tickers.pickle', 'rb') as f:
            tickers = pickle.load(f)

    if not os.path.exists('stock_dfs'):
        os.makedirs('stock_dfs')

    for ticker in tickers:
        print(ticker)
        ticker.replace('.', '-')
        if not os.path.exists('stock_dfs/{}.csv'.format(ticker)):
            data.to_csv('stock_dfs/{}.csv'.format(ticker))

        else:
            print('Already have {}'.format(ticker))

#does not work
def compile_data():
    with open("sp500tickers.pickle", "rb") as f:
        tickers = pickle.load(f)

    main_df = pd.DataFrame()

    for count,ticker in enumerate(tickers):
        df = pd.read_csv('stock_dfs/{}.csv'.format(ticker))
        df.set_index('date', inplace=True)

        df.rename(columns = {'Adj Close': ticker}, inplace=True)
        df.drop(['Open', 'High', 'Low', 'Close', 'Volume'], 1, inplace=True)

        if main_df.empty:
            main_df = df
        else:
            main_df = main_df.merge(df, how='outer')

        if count % 10 == 0:
            print(count)

    print(main_df.head())
    main_df.to_csv('sp500_joined_closed.csv')

#save_sp500_tickers()
#get_data()
compile_data()
