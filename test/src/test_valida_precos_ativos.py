import unittest
import pandas as pd
from strategy_utils import load_data_yfinance, get_binance_ohlc

class TestPrecosReais(unittest.TestCase):

    def test_precos_acoes_b3(self):
        ativos = ["PETR4.SA", "VALE3.SA", "ITUB4.SA", "WEGE3.SA", "B3SA3.SA"]
        for ativo in ativos:
            with self.subTest(ativo=ativo):
                df = load_data_yfinance(ativo)
                self.assertIsInstance(df, pd.DataFrame)
                self.assertGreater(len(df), 0)
                self.assertIn("Close", df.columns)
                preco = float(df["Close"].iloc[-1])
                print(f"{ativo}: R$ {preco:.2f}")
                self.assertGreater(preco, 1)

    def test_precos_cripto_binance(self):
        ativos = ["BTCUSDT", "ETHUSDT", "BNBUSDT", "SOLUSDT", "XRPUSDT"]
        for ativo in ativos:
            with self.subTest(ativo=ativo):
                df = get_binance_ohlc(ativo, interval="15m", limit=5)
                self.assertIsInstance(df, pd.DataFrame)
                self.assertGreater(len(df), 0)
                self.assertIn("Close", df.columns)
                preco = float(df["Close"].iloc[-1])
                print(f"{ativo}: US$ {preco:.2f}")
                self.assertGreater(preco, 0)

if __name__ == "__main__":
    unittest.main()