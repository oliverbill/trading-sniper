import unittest
import pandas as pd
import numpy as np
from signals import calculate, calculate

class TestCalculateSignals(unittest.TestCase):

    def setUp(self):
        # Cria um DataFrame com dados simulados de candles
        self.df = pd.DataFrame({
            "Open": np.linspace(10, 12, 50),
            "High": np.linspace(10.5, 12.5, 50),
            "Low": np.linspace(9.5, 11.5, 50),
            "Close": np.linspace(10.2, 12.2, 50)
        })
        self.ticker = "TEST"

    def test_calculate_indicators_returns_valid_df(self):
        df_ind = calculate(self.df.copy(), self.ticker)
        self.assertIn("rsi", df_ind.columns)
        self.assertIn("stoch_k", df_ind.columns)
        self.assertIn("stoch_d", df_ind.columns)
        self.assertIn("macd", df_ind.columns)
        self.assertIn("macd_signal", df_ind.columns)
        self.assertFalse(df_ind.isnull().any().any())

    def test_calculate_signal_returns_expected_structure(self):
        df_ind = calculate(self.df.copy(), self.ticker)
        row = df_ind.iloc[-1]
        signal, strategy, entry, stop_loss, take_profit = calculate(row, self.ticker)

        self.assertIn(signal, ["BUY", "SELL", "WAIT"])
        self.assertIsInstance(strategy, str)
        if signal != "WAIT":
            self.assertIsInstance(entry, float)
            self.assertIsInstance(stop_loss, float)
            self.assertIsInstance(take_profit, float)

if __name__ == "__main__":
    unittest.main()