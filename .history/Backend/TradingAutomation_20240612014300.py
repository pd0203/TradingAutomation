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

def get_formatted_interval(interval):
    intervals = {
        "1m": "1",
        "3m": "3",
        "5m": "5",
        "15m": "15",
        "30m": "30",
        "1h": "60",
        "2h": "120",
        "4h": "240",
        "6h": "360",
        "12h": "720",
        "1d": "D"
      }
    formatted_interval = intervals.get(interval)

    if formatted_interval is None:
        raise ValueError("Invalid interval")
    
    return formatted_interval

# Fetch historical data
def fetch_historical_data(symbol, interval):
    formatted_interval = get_formatted_interval(interval)
    # 24 hours of data for 00 minute intervals
    limit = 43200 / int(formatted_interval) if interval != "1d" else 200
    now = int(time.time())
    since = now - (86400*100) # From 100 days ago
    response = session.query_kline(symbol=symbol, interval=formatted_interval, limit=limit, from_time=since)
    data = response['result']
    df = pd.DataFrame(data)
    df['timestamp'] = pd.to_datetime(df['open_time'], unit='s')
    df.set_index('timestamp', inplace=True)
    print("interval : ", interval, "length of df : ", len(df))
    return df

# Calculate technical indicators
def fetch_indicators(df):
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

def triple_rsi_strategy(df):
    while True:
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

# Triple RSI Strategy
def triple_rsi_strategy_backtest(df):
    initial_balance = 10000  # Starting with $10,000
    balance = initial_balance
    position = 0
    for i in range(1, len(df)):
        # df = data frame (historical chart data + indicators(EMA,RSI,ADX) data)
        # iloc = index (integer location)
        current = df.iloc[i]

        if (current['close'] > current['ema_50'] and
            current['rsi_7'] > current['rsi_14'] and
            current['rsi_14'] > current['rsi_21'] and
            current['rsi_7'] > 50 and
            current['rsi_14'] > 50 and
            current['rsi_21'] > 50 and
            current['adx'] > 20 and
            position == 0):
            # Buy signal
            position = balance / current['close']
            balance = 0
            print(f"Buy at {current['close']} on {current.name}")

        elif (current['close'] < current['ema_50'] or
              current['rsi_7'] < current['rsi_14'] or
              current['rsi_14'] < current['rsi_21'] or
              current['rsi_7'] < 50 or
              current['rsi_14'] < 50 or
              current['rsi_21'] < 50 or
              current['adx'] < 20) and position > 0:
            # Sell signal
            balance = position * current['close']
            position = 0
            print(f"Sell at {current['close']} on {current.name}")

    # If still in position, sell at the last price
    if position > 0:
        balance = position * df.iloc[-1]['close']

    profit = balance - initial_balance
    return {"initial_balance": initial_balance, "final_balance": balance, "profit": profit}

def backtest_strategy(symbol, interval, trading_type):
    df = fetch_historical_data(symbol, interval)
    df = fetch_indicators(df)

    if trading_type == "triple_rsi":
        result = triple_rsi_strategy_backtest(df)
    else:
        result = {"error": "Unknown trading type"}
    print("<result> ", result)
    return result

# Main trading function
def auto_trading_bot(symbol, interval, trading_type):
    while True:
        df = fetch_historical_data(symbol, interval)
        df = fetch_indicators(df)

        if trading_type == "triple_rsi":
            result = triple_rsi_strategy(df)
        else:
            result = {"error": "Unknown trading type"}

        print(result)