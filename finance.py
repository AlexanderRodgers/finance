import bs4 as bs
from alpha_vantage.timeseries import TimeSeries as ts
import datetime as dt
import time
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
        ticker = ticker.replace('.', '-')
        if not os.path.exists('stock_dfs/{}.csv'.format(ticker)):
            data, metadata = series.get_daily_adjusted(symbol=ticker, outputsize='full')
            data.to_csv('stock_dfs/{}.csv'.format(ticker))

        else:
            print('Already have {}'.format(ticker))

def compile_data():
    with open("sp500tickers.pickle", "rb") as f:
        tickers = pickle.load(f)
        print(tickers)

    main_df = pd.DataFrame()

    for count,ticker in enumerate(tickers):
        ticker = ticker.replace('.', '-')
        #Creates a pandas dataframe from previously downloaded file
        df = pd.read_csv('stock_dfs/{}.csv'.format(ticker))
        #sets the dataframe index to the date
        df.set_index('date', inplace=True)
        #renames the adjusted close column to the name of the ticker
        df.rename(columns = {'5. adjusted close': ticker}, inplace=True)
        #drops whatever isn't the adjusted close column
        df.drop(['1. open', '2. high', '3. low', '4. close', '6. volume', '7. dividend amount', '8. split coefficient'], 1, inplace=True)

        if main_df.empty:
            main_df = df
        else:
            main_df = main_df.join(df, how='outer')

        if count % 10 == 0:
            print(count)

    print(main_df.head())
    main_df.to_csv('sp500_joined_closes.csv')

def append_data():
    #Opens the list of stocks on the S&P 500
    with open('sp500tickers.pickle', 'rb') as f:
        tickers = pickle.load(f)

    #Creates a new dataframe
    append_df = pd.DataFrame()
    #Gets the current date
    now = dt.datetime.now()

    #Loops through the tickers in the list and checks to see if there
    #is any data file on that stock and writes it to csv if there is none
    for ticker in tickers:
        ticker = ticker.replace('.', '-')
        if not os.path.exists('stock_dfs/{}.csv'.format(ticker)):
            print(ticker,'not in file')
            data, metadata = series.get_daily_adjusted(symbol=ticker, outputsize='full')
            data.to_csv('stock_dfs/{}.csv'.format(ticker))

        #append_df is the dataframe of all the stocks in the folder
        append_df = pd.read_csv('stock_dfs/{}.csv'.format(ticker))
        append_df.set_index('date', inplace=True)
        #Gets the last value that was part of the query
        last_entry = append_df.index.values[-1]
        #Dates will never align if not a trading day.
        if last_entry != now.strftime('%Y-%m-%d'):
            #Pulls the stock information
            updated_data, metadata = series.get_daily_adjusted(symbol=ticker, outputsize='compact')
            i = -1

            #Loops until the entry from the last date of the file matches
            #the date of the file that was just pulled.
            while last_entry != updated_data.index.values[i]:
                i = i - 1

            #Combines the frame of the old file and the updated data from new file.
            frames = [append_df, updated_data[i+1:]]
            result = pd.concat(frames)

            #Converts that new dataframe to a csv file and overwrites the old one.
            result.to_csv('stock_dfs/{}.csv'.format(ticker))

            print('updated file: ',ticker)
        #used to make sure we don't go over the # of requests/sec
        time.sleep(1)

    print('update finished')

#save_sp500_tickers()
#get_data()
#compile_data()
append_data()
