from flask import Flask, request, jsonify
from flask_cors import CORS
from TradingAutomation import auto_trading_bot, backtest_strategy
import threading

app = Flask(__name__)
CORS(app)

# Endpoint to start trading bot
@app.route('/start', methods=['POST'])
def trading_bot():
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
        "1d": "D",
        "1w": "W",
        "1M": "M"
      }
    formatted_interval = intervals.get(data['interval'])
    if formatted_interval is None:
        raise ValueError("Invalid interval")
    
    data = request.json
    symbol = data['coin']
    interval = formatted_interval
    trading_type = data['trading_type']
    threading.Thread(target=auto_trading_bot, args=(symbol, interval, trading_type)).start()
    return jsonify({"status": "Trading bot started for " + symbol + " with interval " + interval + " and strategy " + trading_type})

@app.route('/backtest', methods=['POST'])
def backtest():
    data = request.json
    symbol = data['coin']
    interval = data['interval']
    trading_type = data['trading_type']
    result = backtest_strategy(symbol, interval, trading_type)
    return jsonify(result)

@app.route('/status', methods=['GET'])
def status():
    # Implement a way to check the status of the trading bot if needed
    return jsonify({"status": "Bot is running"})

if __name__ == "__main__":
    app.run(port=5000)