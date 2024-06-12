from flask import Flask, jsonify
from TradingAutomation import trading_bot()
import threading

app = Flask(__name__)

# Endpoint to start trading bot
@app.route('/start', methods=['GET'])
def start_bot():
    threading.Thread(target=trading_bot).start()
    return jsonify({"status": "Trading bot started"})

# Endpoint to check bot status
@app.route('/status', methods=['GET'])
def status():
    return jsonify({"status": "Bot is running"})

if __name__ == "__main__":
    app.run(port=5000)
