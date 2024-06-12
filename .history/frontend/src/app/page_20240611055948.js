"use client";

import { useState, useEffect } from "react";
import axios from "axios";

const coins = ["BTCUSDT", "ETHUSDT", "SOLUSDT", "DOGEUSDT"];
const intervals = ["1m", "5m", "15m", "30m", "1h", "4h", "1d"];
const tradingTypes = ["triple_rsi"]; // Add more trading strategies as needed

export default function Home() {
  const [prices, setPrices] = useState({});
  const [selectedCoin, setSelectedCoin] = useState(coins[0]);
  const [selectedInterval, setSelectedInterval] = useState(intervals[0]);
  const [selectedTradingType, setSelectedTradingType] = useState(
    tradingTypes[0]
  );
  const [tradingStatus, setTradingStatus] = useState("stopped");
  const [backtestResult, setBacktestResult] = useState(null);

  useEffect(() => {
    const fetchPrices = async () => {
      const priceData = await Promise.all(
        coins.map(async (coin) => {
          const response = await axios.get(
            `https://api.bybit.com/v2/public/tickers?symbol=${coin}`
          );
          return { coin, price: response.data.result[0].last_price };
        })
      );
      const newPrices = {};
      priceData.forEach(({ coin, price }) => {
        newPrices[coin] = price;
      });
      setPrices(newPrices);
    };

    fetchPrices();
    const intervalId = setInterval(fetchPrices, 10000); // Update prices every 10 seconds

    return () => clearInterval(intervalId);
  }, []);

  const startTrading = async () => {
    try {
      await axios.post("/api/start", {
        coin: selectedCoin,
        interval: selectedInterval[1],
        trading_type: selectedTradingType,
      });
      setTradingStatus("running");
    } catch (error) {
      console.error("Error starting trading:", error);
      setTradingStatus("error");
    }
  };

  const runBacktest = async () => {
    try {
      const response = await axios.post("/api/backtest", {
        coin: selectedCoin,
        interval: selectedInterval,
        trading_type: selectedTradingType,
      });
      setBacktestResult(response.data);
    } catch (error) {
      console.error("Error running backtest:", error);
    }
  };

  return (
    <main className="flex flex-col items-center justify-center min-h-screen p-10 bg-black text-yellow-400">
      <h1 className="text-4xl mb-10">Trading Dashboard</h1>
      <div className="grid grid-cols-2 gap-4 mb-10">
        {coins.map((coin) => (
          <div key={coin} className="p-4 bg-gray-800 rounded-lg">
            <h2 className="text-xl">{coin}</h2>
            <p className="text-2xl">{prices[coin] || "Loading..."}</p>
          </div>
        ))}
      </div>
      <div className="flex flex-col items-center">
        <div className="mb-5">
          <label className="mr-2">Select Coin:</label>
          <select
            value={selectedCoin}
            onChange={(e) => setSelectedCoin(e.target.value)}
            className="p-2 bg-gray-800 text-yellow-400 rounded"
          >
            {coins.map((coin) => (
              <option key={coin} value={coin}>
                {coin}
              </option>
            ))}
          </select>
        </div>
        <div className="mb-5">
          <label className="mr-2">Select Interval:</label>
          <select
            value={selectedInterval}
            onChange={(e) => setSelectedInterval(e.target.value)}
            className="p-2 bg-gray-800 text-yellow-400 rounded"
          >
            {intervals.map((interval) => (
              <option key={interval} value={interval}>
                {interval}
              </option>
            ))}
          </select>
        </div>
        <div className="mb-5">
          <label className="mr-2">Select Trading Strategy:</label>
          <select
            value={selectedTradingType}
            onChange={(e) => setSelectedTradingType(e.target.value)}
            className="p-2 bg-gray-800 text-yellow-400 rounded"
          >
            {tradingTypes.map((type) => (
              <option key={type} value={type}>
                {type}
              </option>
            ))}
          </select>
        </div>
        <button
          onClick={startTrading}
          className="p-4 bg-yellow-400 text-black rounded-lg mb-5"
        >
          Start Trading
        </button>
        <button
          onClick={runBacktest}
          className="p-4 bg-yellow-400 text-black rounded-lg"
        >
          Run Backtest
        </button>
        <p className="mt-4">{`Trading Status: ${tradingStatus}`}</p>
      </div>
      {backtestResult && (
        <div className="mt-10 p-4 bg-gray-800 rounded-lg text-yellow-400">
          <h2 className="text-2xl mb-4">Backtest Results</h2>
          <p>Initial Balance: ${backtestResult.initial_balance}</p>
          <p>Final Balance: ${backtestResult.final_balance}</p>
          <p>Profit: ${backtestResult.profit}</p>
        </div>
      )}
    </main>
  );
}
