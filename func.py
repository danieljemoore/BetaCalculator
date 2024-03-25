import numpy as np
import pandas as pd
import yfinance as yf
import requests
from bs4 import BeautifulSoup

def get_df_from_yf(ticker, sdate, edate):
    try:
        df = yf.download(ticker, start= sdate, end= edate, interval= '1mo')
    except FileNotFoundError:
        pass
        # print("Error")
    else:
        return df

def add_daily_return_to_df(df, ticker):
    df['Monthly_return'] = (np.log(df['Adj Close'] / df['Adj Close'].shift(1)))
    ##Save data to a CSV file
    #save_dataframe_to_csv(df, ticker)
    return df  

def merge_df_by_column_name(col_name, sdate, edate, *tickers):
    # Will hold data for all dataframes with the same column name
    mult_df = pd.DataFrame()
    
    for x in tickers:
        df = add_daily_return_to_df(get_df_from_yf(x, sdate, edate), x)
        
        # NEW Check if your dataframe has duplicate indexes
        if not df.index.is_unique:
            # Delete duplicates 
            df = df.loc[~df.index.duplicated(), :]
        
        mask = (df.index >= sdate) & (df.index <= edate)
        mult_df[x] = df.loc[mask][col_name]
        
    return mult_df

def find_beta(ticker, sdate, edate):
    # Tickers analyzed being the S&P and the stock passed
    por_list =['^GSPC']
    por_list.append(ticker)

    mult_df = merge_df_by_column_name('Monthly_return',  sdate, 
                                  edate, *por_list)
    
    # Provides the covariance between the securities
    cov = mult_df.cov() * 252
    
    # Get the covariance of the stock and the market
    cov_vs_market = cov.iloc[0,1]
    
    # Get annualized variance of the S&P
    sp_var = mult_df['^GSPC'].var() * 252
    
    # Beta is normally calculated over a 5 year period which is why you may see a difference
    beta = cov_vs_market / sp_var
    return beta

def get_risk_free():
    url = 'https://fred.stlouisfed.org/series/DGS10'
    html = requests.get(url)
    soup = BeautifulSoup(html.text, 'html.parser')
    price = soup.find(attrs={'class':"series-obs value"})
    price = float(price.get_text())

    return price