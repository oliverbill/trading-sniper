import unittest
import pandas as pd
import numpy as np
from indicators import (
    calculate_bollinger_bands,
    calculate_stochastic,
    calculate_rsi,
    calculate_macd,
)

class TestIndicators(unittest.TestCase):

    def setUp(self):
        # Create a sample DataFrame for testing
        self.df = pd.DataFrame({
            "close": np.linspace(10, 20, 50),
            "high": np.linspace(12, 22, 50),
            "low": np.linspace(8, 18, 50),
        })

    def test_calculate_bollinger_bands(self):
        result = calculate_bollinger_bands(self.df, price_column="close")
        self.assertIn("Upper Band", result.columns)
        self.assertIn("Middle Band", result.columns)
        self.assertIn("Lower Band", result.columns)
        self.assertFalse(result.isnull().any().any())
        # import matplotlib.pyplot as plt
        # plt.figure(figsize=(14, 7))
        # plt.plot(self.df['close'], label='Closing Price', color='blue')
        # plt.plot(result['Upper Band'], label='Upper Band', color='red', linestyle='--')
        # plt.plot(result['Middle Band'], label='Middle Band', color='black', linestyle='--')
        # plt.plot(result['Lower Band'], label='Lower Band', color='green', linestyle='--')
        # plt.title('Bollinger Bands')
        # plt.xlabel('Date')
        # plt.ylabel('Price')
        # plt.legend()
        # plt.show()

    def test_calculate_stochastic(self):
        result = calculate_stochastic(self.df)
        self.assertIn("stoch_k", result.columns)
        self.assertIn("stoch_d", result.columns)
        self.assertFalse(result.isnull().any().any())

    def test_calculate_rsi(self):
        result = calculate_rsi(self.df)
        self.assertIn("rsi", result.columns)
        self.assertFalse(result.isnull().any().any())

    def test_calculate_macd(self):
        result = calculate_macd(self.df)
        self.assertIn("macd", result.columns)
        self.assertIn("macd_signal", result.columns)
        self.assertIn("macd_hist", result.columns)
        self.assertFalse(result.isnull().any().any())

if __name__ == "__main__":
    unittest.main()