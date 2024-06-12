from flask import Flask, request, jsonify
from flask_cors import CORS
from TradingAutomation import auto_trading_bot, backtest_strategy
import threading

app = Flask(__name__)
CORS(app)

# Endpoint to start trading bot
@app.route('/start', methods=['POST'])
def trading_bot():
    data = request.json
    symbol = data['coin']
    interval = data['interval']
    trading_type = data['trading_type']
    threading.Thread(target=auto_trading_bot, args=(symbol, interval, trading_type)).start()
    return jsonify({"status": "Trading bot started for " + symbol + " with interval " + interval + " and strategy " + trading_type})

@app.route('/backtest', methods=['POST'])
def backtest():
    print("wow")
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