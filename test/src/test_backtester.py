import unittest
import pandas as pd
from backtester import run_backtest, save_pdf_report


class TestBacktester(unittest.TestCase):

    def setUp(self):
        # Simula um dataset com sinais válidos para testar
        self.sample_data = {
            "FAKE": pd.DataFrame([
                {"Close": 100, "Low": 98, "signal_shadow": "BUY"},
                {"Close": 102, "Low": 100},
                {"Close": 105, "Low": 103},
                {"Close": 106, "Low": 104, "signal_shadow": "SELL"},
                {"Close": 107, "Low": 105}
            ])
        }

    def test_backtest_produces_trades(self):
        trades_df = run_backtest(self.sample_data)
        save_pdf_report(trades_df)
        self.assertFalse(trades_df.empty)
        self.assertIn("symbol", trades_df.columns)
        self.assertIn("return_%", trades_df.columns)
        self.assertGreaterEqual(len(trades_df), 1)

    def test_return_format(self):
        trades_df = run_backtest(self.sample_data)
        for col in ["symbol", "strategy", "entry_price", "exit_price", "return_%"]:
            self.assertIn(col, trades_df.columns)

if __name__ == "__main__":
    unittest.main()
