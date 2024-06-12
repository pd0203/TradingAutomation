from flask import Flask, request, jsonify
from flask_cors import CORS
from TradingAutomation import trading_bot
import threading

app = Flask(__name__)
CORS(app)

# Endpoint to start trading bot
@app.route('/start', methods=['POST'])
def start_bot():
    data = request.json
    symbol = data['coin']
    interval = data['interval']
    threading.Thread(target=trading_bot, args=(symbol, interval)).start()
    return jsonify({"status": "Trading bot started for " + symbol + " with interval " + interval})

@app.route('/status', methods=['GET'])
def status():
    # Implement a way to check the status of the trading bot if needed
    return jsonify({"status": "Bot is running"})

if __name__ == "__main__":
    app.run(port=5000)