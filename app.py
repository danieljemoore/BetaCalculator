import pandas as pd
import datetime as dt 
import time
import yfinance as yf


import streamlit as st
from streamlit_extras.mandatory_date_range import date_range_picker

import plotly.express as px
import plotly.graph_objects as go

from bs4 import BeautifulSoup
import requests

from func import * 

pd.options.plotting.backend = "plotly"

## Page Metadata
st.set_page_config(
    page_title="Risk Calculator",
    page_icon="📈",
    #layout="wide",
    #initial_sidebar_status="expanded",
    menu_items={'Get Help' : "https://www.danieljemoore.com"})

## Page Heder
st.title("Beta Calculator")
st.markdown('''
<style>
[data-testid="stMarkdownContainer"] 
ul{padding-left:20px;}
</style>
''', unsafe_allow_html=True)

##FRED 10-YR Treasury Yield as RiskFree
url = 'https://fred.stlouisfed.org/series/DGS10'
html = requests.get(url)
soup = BeautifulSoup(html.text, 'html.parser')
price = soup.find(attrs={'class':"series-obs value"})
rfdate = soup.find(attrs={'align':"right"})
rfdate = str(rfdate.get_text())
risk_free_rate = float(price.get_text())

## Sidebar
with st.sidebar:
    st.title("Settings")
    size = st.slider("Portfolio Size", 1, 20, value = 1, step = 1)
    st.markdown("## Ticker List")
    prompts = []
    for i in range(1, size+1):
        prompts += [f"Ticker {i}"]
    tickers = [st.text_input(x) for x in prompts]
    st.markdown("### Date Range")
    dates = date_range_picker("Select a date range", 
                              min_date= dt.date(1974, 12, 31), max_date = dt.date.today(), 
                              default_start=dt.date(2019, 1, 1), default_end=dt.date.today(), 
                              error_message="Please Select a Start and End Date")

## Reformat the input dates
start = dates[0].strftime("%Y-%m-%d")
end = dates[1].strftime("%Y-%m-%d")

element = st.empty()
try:
    #Calculate Beta
    beta = []
    for i in range(len(tickers)):
        try:
            element.write(f"{tickers[i]} Beta: {(find_beta(tickers[i], start, end)):.3f}")
            #time.sleep(.5)
            beta += [find_beta(tickers[i], start, end)]
        except:
            element.error("Error!")
            break

    #Calculate Monthly Returns
    if beta:
        Monthly = []
        mult_df = merge_df_by_column_name('Monthly_return',  start, 
                                        end, *tickers)
    for i in range(len(tickers)):
        try:
            element.write(f"{tickers[i]} Monthly Return: {mult_df[tickers[i]].sum():.3f}%")
            #time.sleep(.5)
            Monthly += [mult_df[tickers[i]].sum()]
        except:
            element.error("No chart to display! Please enter your portfolio in the sidebar.")
    element.success("Finished!")
except:
    st.error("No chart to display! Please enter your portfolio in the sidebar.")
#Set Variables for Chart
try:
    beta = pd.DataFrame({'Beta': beta}, index = tickers)
    Monthly = pd.DataFrame({'Monthly Return(%)': Monthly}, index = tickers)
    datao = pd.concat([beta ,Monthly], axis=1)
    datao.index.name='Stocks'
    betamin = min(datao["Beta"])
    betamax = max(datao["Beta"])
    x1 = 0
    y1 = ((risk_free_rate / 12) + ((0) * (1 - (risk_free_rate /12)))) 
    x2 = betamax + .9
    y2 = ((risk_free_rate / 12) + ((betamax + .9) * (1 - (risk_free_rate / 12))))
except:
    st.error("No chart to display! Please finish entering your portfolio in the sidebar.")

#The Chart Itself
try:
    fig1 = px.scatter(data_frame=datao, x = "Beta", y ="Monthly Return(%)", color=datao.index)
    fig1.update_traces(marker_size=10)

    # Add line
    x_coords = [x1, x2]  # replace with your x coordinates
    y_coords = [y1, y2]  # replace with your y coordinates
    fig1.add_trace(go.Scatter(x=x_coords, y=y_coords, mode='lines', name='SML', line=dict(color='black'), fillcolor='#000000'))
    
    # Set x-axis bounds
    fig1.update_xaxes(range=[betamin - .1, betamax + .1])
    
    #Post
    st.plotly_chart(fig1)
    
    # Summary
    st.write(f"From {dates[0].strftime('%m/%d/%Y')}-{dates[1].strftime('%m/%d/%Y')}:")
    st.write(datao)
    st.write(f"10 Year Yield as of {str(rfdate)} {str(risk_free_rate)}%")
except:
    pass
