import os
import streamlit as st
import pandas as pd
import yfinance as yf
from datetime import datetime, timedelta
import plotly.express as px
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv() 

openai_api_key = os.getenv('openai_key')

# Configuration du style de l'application
st.markdown("""
    <style>
    .main {
        background-color: #E0FFFF; /* Couleur bleu ciel pour le fond */
    }
    </style>
    """, unsafe_allow_html=True)

def dataframe_to_text(df):
    text = ""
    # Vérifiez si df est un DataFrame et non une Series
    if isinstance(df, pd.DataFrame):
        for column in df.columns:
            text += f"{column}: \n"
            # Utiliser iterrows() pour itérer sur les lignes si c'est un DataFrame
            for index, row in df.iterrows():
                text += f" - {index}: {row[column]}\n"
    elif isinstance(df, pd.Series):
        # Gérer le cas où df est une Series
        text += f"{df.name}: \n"
        for index, value in df.items():
            text += f" - {index}: {value}\n"
    return text


# Fonction pour l'analyse financière
def financial_analysis(df):
    client = OpenAI(api_key=openai_api_key)  # Remplacez par votre clé API

    financial_data_text = dataframe_to_text(df)
    response = client.chat.completions.create(
        messages=[
            {
                "role": "system",
                "content": "As an expert financial analyst, build a strong financial analysis and make future prediction:",
            },
            {
                "role": "user",
                "content": financial_data_text,
            }
        ],
        model="gpt-4",
    )
    return response.choices[0].message.content

# Fonctions pour l'application
def check_ticker(ticker):
    stock_info = yf.Ticker(ticker)
    try:
        _ = stock_info.info
        return True
    except:
        return False

def get_financials(ticker):
    stock = yf.Ticker(ticker)
    return stock.financials

def get_historical_data(ticker, start_date, end_date, interval='1wk'):
    data = yf.download(ticker, start=start_date, end=end_date, interval=interval)
    return data

def get_news(ticker):
    stock = yf.Ticker(ticker)
    news = stock.news
    news_df = pd.DataFrame(news)

    # Créer des chaînes Markdown pour chaque nouvelle
    news_links = []
    for _, row in news_df.iterrows():
        title = row['title']
        link = row['link']
        markdown_string = f"[{title}]({link})"
        news_links.append(markdown_string)

    return news_links


def plot_historical_data(data):
    fig = px.line(data, x=data.index, y='Close', title='Historical Closing Prices')
    return fig

# Streamlit app layout
col1, col2 = st.columns([1, 6])
with col1:
    st.image('bluegpt.png')  
with col2:
    st.title('BlueAI')

ticker = st.text_input('Ticker', 'AAPL').upper()
today = datetime.today().strftime('%Y-%m-%d')
date = st.text_input('Date', today)
n_weeks = st.slider('Information of the past n weeks will be utilized', 1, 10, 3)
use_financials = st.checkbox('Use Latest Basic Financials')
use_news = st.checkbox('Show Latest News')
submit_button = st.button('Submit')

if submit_button:
    if check_ticker(ticker):
        start_date = (datetime.strptime(date, '%Y-%m-%d') - pd.Timedelta(weeks=n_weeks)).strftime('%Y-%m-%d')
        end_date = date

        historical_data = get_historical_data(ticker, start_date, end_date)

        tab1, tab2, tab3, tab4 = st.tabs(["Historical Data", "Financial Data", "News", "Financial Analysis"])
        
        with tab1:
            st.plotly_chart(plot_historical_data(historical_data))

        with tab2:
            if use_financials:
                financials = get_financials(ticker)
                st.dataframe(financials)

        with tab3:
            if use_news:
                news_links = get_news(ticker)
                for markdown_string in news_links:
                    st.markdown(markdown_string)  


        with tab4:
            if use_financials:
                financials = get_financials(ticker)
                analysis_result = financial_analysis(financials)
                st.text(analysis_result)
    else:
        st.error('Invalid ticker. Please enter a valid ticker.')

