import unittest
from datetime import datetime
from unittest.mock import patch, MagicMock
import pandas_ta as ta

from strategy_utils import read_stocks_symbols_from_csv, get_ohlc_polygon, get_latest_quote_polygon
import pandas as pd
import os

class TestStrategyUtils(unittest.TestCase):

    def setUp(self):
        self.test_filepath = "test_symbols.csv"
        pd.DataFrame({
            "Ticker": ["AAPL", "MSFT"],
            "Broker": ["IB", "IB"]
        }).to_csv(self.test_filepath, index=False, sep=";")

        self.crypto_filepath = "../test_crypto.csv"
        pd.DataFrame({
            "Ticker": ["BTC-USDT", "ETH-USDT"],
        }).to_csv(self.crypto_filepath, index=False, sep=";")

    def tearDown(self):
        os.remove(self.test_filepath)

    def test_read_stocks_symbols_from_csv(self):
        symbols = read_stocks_symbols_from_csv(self.test_filepath)

        self.assertIsInstance(symbols, dict)
        self.assertIn("IB", symbols)
        self.assertIsInstance(symbols["IB"], list)
        self.assertIn("AAPL", symbols["IB"])

    def test_get_ohlc_polygon(self):
        ticker = "AAPL"
        df = get_ohlc_polygon(ticker, multiplier=1)
        self.assertIsInstance(df, pd.DataFrame)
        self.assertEqual(len(df), 120)
        self.assertIn("close", df.columns)
        self.assertIn("low", df.columns)
        self.assertIn("high", df.columns)

    def test_get_polygon(self):
        ticker = "AAPL"
        df = get_latest_quote_polygon(ticker)
        self.assertIsInstance(df, pd.DataFrame)
        self.assertEqual(len(df), 1)
        self.assertIn("close", df.columns)
        self.assertIn("low", df.columns)
        self.assertIn("high", df.columns)