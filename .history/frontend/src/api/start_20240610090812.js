import axios from "axios";

export default async function handler(req, res) {
  if (req.method === "POST") {
    const { coin, interval, trading_type } = req.body;

    try {
      const response = await axios.post("http://127.0.0.1:5000/start", {
        coin,
        interval,
        trading_type,
      });
      res.status(200).json(response.data);
    } catch (error) {
      res.status(500).json({ error: "Error starting trading bot" });
    }
  } else {
    res.status(405).json({ error: "Method not allowed" });
  }
}
