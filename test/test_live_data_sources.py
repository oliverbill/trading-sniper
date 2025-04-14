import configparser
import unittest
from src import utils as controller


class TestLiveDataSources(unittest.TestCase):
    config = configparser.ConfigParser()
    config_values = config.read("../config.ini")

    def test_yfinance_download(self):
        data = controller.load_data_yfinance("AAPL", period="5d", interval="1h")
        self.assertIsInstance(data, list)
        self.assertGreaterEqual(len(data), 1)
        self.assertIn("Open", data[0])
        self.assertIn("Close", data[0])

    def test_binance_download(self):
        data = controller.get_binance_ohlc("BTCUSDT", interval="1h", limit=5)
        self.assertIsInstance(data, list)
        self.assertEqual(len(data), 5)
        self.assertIn("Open", data[0])
        self.assertIn("Close", data[0])

    def test_polygon_load_data(self):
        api_key = self.config["polygon"]["api_key"]
        data = controller.load_data_polygon(api_key,"AAPL", interval="1h", limit=10)
        self.assertIsInstance(data, list)
        self.assertGreaterEqual(len(data), 1)
        self.assertIn("Open", data[0])
        self.assertIn("Close", data[0])

if __name__ == "__main__":
    unittest.main()
