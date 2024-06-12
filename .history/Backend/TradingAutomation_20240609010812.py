from flask import Flask, jsonify
import threading
import os
from pybit import HTTP
from dotenv import load_dotenv
import pandas as pd
import ta
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import time

# .env 파일 로드
load_dotenv()

# 환경 변수에서 API 키와 시크릿 키 가져오기
bybit_api_key = os.getenv('BYBIT_API_KEY')
bybit_api_secret = os.getenv('BYBIT_API_SECRET')
email_user = os.getenv('EMAIL_USER')
email_password = os.getenv('EMAIL_PASSWORD')
email_send = os.getenv('EMAIL_SEND')

# Connect to Bybit API
session = HTTP("https://api.bybit.com",
               api_key=bybit_api_key,
               api_secret=bybit_api_secret)

# Fetch historical data
def fetch_historical_data(symbol, interval, limit=200):
    response = session.query_kline(symbol=symbol, interval=interval, limit=limit)
    data = response['result']
    df = pd.DataFrame(data)
    df['timestamp'] = pd.to_datetime(df['open_time'], unit='s')
    df.set_index('timestamp', inplace=True)
    return df

# Calculate technical indicators
def calculate_indicators(df):
    df['ema_50'] = ta.trend.EMAIndicator(df['close'], window=50).ema_indicator()
    df['rsi_7'] = ta.momentum.RSIIndicator(df['close'], window=7).rsi()
    df['rsi_14'] = ta.momentum.RSIIndicator(df['close'], window=14).rsi()
    df['rsi_21'] = ta.momentum.RSIIndicator(df['close'], window=21).rsi()
    df['adx'] = ta.trend.ADXIndicator(df['high'], df['low'], df['close']).adx()
    df['ema_14'] = ta.trend.EMAIndicator(df['close'], window=14).ema_indicator()
    df['ema_21'] = ta.trend.EMAIndicator(df['close'], window=21).ema_indicator()
    return df

# Send email
def send_email(subject, body):
    msg = MIMEMultipart()
    msg['From'] = email_user
    msg['To'] = email_send
    msg['Subject'] = subject

    msg.attach(MIMEText(body, 'plain'))

    server = smtplib.SMTP('smtp.gmail.com', 587)
    server.starttls()
    server.login(email_user, email_password)
    text = msg.as_string()
    server.sendmail(email_user, email_send, text)
    server.quit()

# Main trading function
def auto_trading_bot(symbol, interval):
    while True:
        df = fetch_historical_data(symbol, interval)
        df = calculate_indicators(df)
        latest = df.iloc[-1]

        # Check conditions
        if (
            latest['close'] > latest['ema_50'] and
            latest['rsi_7'] > latest['rsi_14'] and
            latest['rsi_14'] > latest['rsi_21'] and
            latest['rsi_7'] > 50 and
            latest['rsi_14'] > 50 and
            latest['rsi_21'] > 50 and
            latest['adx'] > 20
        ):
            send_email("Buy Signal", "Conditions met for a buy signal.")
            print("Buy signal sent.")
            # Place buy order (mockup)
            # order = session.place_active_order(
            #     symbol=symbol,
            #     side='Buy',
            #     order_type='Market',
            #     qty=1,  # Adjust quantity
            #     time_in_force='GoodTillCancel'
            # )
            # print(order)

        # Check every 5 minutes
        time.sleep(300)


