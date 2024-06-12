from flask import Flask, jsonify
import threading
import os
from pybit.inverse_perpetual import HTTP
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

def triple_rsi_strategy(df, position, leverage, interval):
    while True:
        latest = df.iloc[-1]

        # Check Conditions for Long Position
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
            # Place long order
            session.place_active_order(
                symbol=latest["symbol"],
                side='Buy',
                order_type='Market',
                qty=1,  # Adjust quantity
                leverage=leverage,
                time_in_force='GoodTillCancel'
            )
            print(f"Long position opened with leverage {leverage}")
        
        # Check Conditions for Short Position
        if (
            latest['close'] < latest['ema_50'] and
            latest['rsi_7'] < latest['rsi_14'] and
            latest['rsi_14'] < latest['rsi_21'] and
            latest['rsi_7'] < 50 and
            latest['rsi_14'] < 50 and
            latest['rsi_21'] < 50 and
            latest['adx'] > 20
        ):
            send_email("Sell Signal", "Conditions met for a sell signal.")
            print("Sell signal sent.")
            # Place short order
            session.place_active_order(
                symbol=latest['symbol'],
                side='Sell',
                order_type='Market',
                qty=1,  # Adjust quantity
                leverage=leverage,
                time_in_force='GoodTillCancel'
            )
            print(f"Short position opened with leverage {leverage}")
        
        # Check conditions to close long position
        elif position == 1 and (
            latest['close'] < latest['ema_50'] or
            latest['rsi_7'] < latest['rsi_14'] or
            latest['rsi_14'] < latest['rsi_21'] or
            latest['rsi_7'] < 50 or
            latest['rsi_14'] < 50 or
            latest['rsi_21'] < 50 or
            latest['adx'] < 20
        ):
            # Close long position
            session.place_active_order(
                symbol=latest["symbol"],
                side='Sell',
                order_type='Market',
                qty=1,  # Adjust quantity
                leverage=leverage,
                time_in_force='GoodTillCancel'
            )
            print(f"Long position closed with leverage {leverage}")
            position = 0
        
        # Check conditions to close short position
        elif position == -1 and (
            latest['close'] > latest['ema_50'] or
            latest['rsi_7'] > latest['rsi_14'] or
            latest['rsi_14'] > latest['rsi_21'] or
            latest['rsi_7'] > 50 or
            latest['rsi_14'] > 50 or
            latest['rsi_21'] > 50 or
            latest['adx'] < 20
        ):
            # Close short position
            session.place_active_order(
                symbol=latest["symbol"],
                side='Buy',
                order_type='Market',
                qty=1,  # Adjust quantity
                leverage=leverage,
                time_in_force='GoodTillCancel'
            )
            print(f"Short position closed with leverage {leverage}")
            position = 0

        # Convert interval to seconds
        formatted_interval = int(get_formatted_interval(interval)) if interval != "1d" else 1440
        interval_seconds = formatted_interval * 60
        time.sleep(interval_seconds)

# Triple RSI Strategy Backtest
def triple_rsi_strategy_backtest(df, position, leverage):
    initial_balance = 10000  # Starting with $10,000
    balance = initial_balance
    position = 0
    total_trades = 0
    winning_trades = 0
    losing_trades = 0
    maker_fee = 0.00025  # 0.025%
    taker_fee = 0.00075  # 0.075%
    current_position = None

    for i in range(1, len(df)):
        # df = data frame (historical chart data + indicators(EMA,RSI,ADX) data)
        # iloc = index (integer location)
        current = df.iloc[i]

        # Long Position
        if (current['close'] > current['ema_50'] and
            current['rsi_7'] > current['rsi_14'] and
            current['rsi_14'] > current['rsi_21'] and
            current['rsi_7'] > 50 and
            current['rsi_14'] > 50 and
            current['rsi_21'] > 50 and
            current['adx'] > 20 and
            position == 0):
            position = (balance / current['close']) * (1 - taker_fee) * leverage
            balance = 0
            total_trades += 1
            current_position = 'Long'
            print(f"Buy at {current['close']} on {current.name}")
        
        # Short position
        elif (current['close'] < current['ema_50'] and
              current['rsi_7'] < current['rsi_14'] and
              current['rsi_14'] < current['rsi_21'] and
              current['rsi_7'] < 50 and
              current['rsi_14'] < 50 and
              current['rsi_21'] < 50 and
              current['adx'] > 20 and
              position == 0):
            position = (balance / current['close']) * (1 - taker_fee) * leverage
            balance = 0
            total_trades += 1
            current_position = 'short'
            print(f"Sell at {current['close']} on {current.name}")

        # Close Long Position
        elif current_position == 'long' and (
              current['close'] < current['ema_50'] or
              current['rsi_7'] < current['rsi_14'] or
              current['rsi_14'] < current['rsi_21'] or
              current['rsi_7'] < 50 or
              current['rsi_14'] < 50 or
              current['rsi_21'] < 50 or
              current['adx'] < 20) and position > 0:
            balance = (position * current['close']) * (1 - taker_fee)
            profit_loss = balance - initial_balance
            if profit_loss > 0:
                winning_trades += 1
            else:
                losing_trades += 1
            position = 0
            current_position = None
            print(f"Sell at {current['close']} on {current.name}")
        
        # Close Short Position
        elif current_position == 'short' and (
              current['close'] > current['ema_50'] or
              current['rsi_7'] > current['rsi_14'] or
              current['rsi_14'] > current['rsi_21'] or
              current['rsi_7'] > 50 or
              current['rsi_14'] > 50 or
              current['rsi_21'] > 50 or
              current['adx'] < 20):
            balance = initial_balance - (position * current['close']) * (1 - taker_fee)
            profit_loss = balance - initial_balance
            if profit_loss > 0:
                winning_trades += 1
            else:
                losing_trades += 1
            position = 0
            current_position = None
            print(f"Buy at {current['close']} on {current.name}")


    # If still in position, sell at the last price
    if position > 0:
        if current_position == 'long':
            balance = (position * df.iloc[-1]['close']) * (1 - taker_fee)
        else:  # short position
            balance = initial_balance - (position * df.iloc[-1]['close']) * (1 - taker_fee)
        profit_loss = balance - initial_balance
        if profit_loss > 0:
            winning_trades += 1
        else:
            losing_trades += 1

    profit = balance - initial_balance
    win_rate = (winning_trades / total_trades) * 100 if total_trades > 0 else 0

    return {"initial_balance": initial_balance, "final_balance": balance, "profit": profit, "total_trades": total_trades, "winning_trades": winning_trades, "losing_trades": losing_trades, "win_rate": win_rate}

def backtest_strategy(symbol, interval, trading_type, position, leverage):
    df = fetch_historical_data(symbol, interval)
    df = fetch_indicators(df)
    print("df: ", df)
    if trading_type == "triple_rsi":
        result = triple_rsi_strategy_backtest(df, position, leverage)
    else:
        result = {"error": "Unknown trading type"}
    print("<result> ", result)
    return result

# Main trading function
def auto_trading_bot(symbol, interval, trading_type, position, leverage):
    while True:
        df = fetch_historical_data(symbol, interval)
        df = fetch_indicators(df)
 
        if trading_type == "triple_rsi":
            result = triple_rsi_strategy(df, position, leverage, interval)
        else:
            result = {"error": "Unknown trading type"}

        print(result)