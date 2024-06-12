import axios from "axios";

export default async function handler(req, res) {
  if (req.method === "POST") {
    const { coin, interval, trading_type } = req.body;

    try {
      const response = await axios.post("http://127.0.0.1:5000/backtest", {
        coin,
        interval,
        trading_type,
      });
      res.status(200).json(response.data);
    } catch (error) {
      console.error("Error running backtest:", error);
      res.status(500).json({ error: "Error running backtest" });
    }
  } else {
    res.status(405).json({ error: "Method not allowed" });
  }
}
