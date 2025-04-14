
import unittest
from src.utils import apply_strategy,apply_macd_histogram_strategy


class TestStrategySignalsExtended(unittest.TestCase):

    def setUp(self):
        # Simple uptrend and downtrend prices
        self.uptrend_data = [
            {"Open": 100 + i - 1, "High": 100 + i + 1, "Low": 100 + i - 2, "Close": 100 + i}
            for i in range(300)
        ]
        self.downtrend_data = [
            {"Open": 200 - i + 1, "High": 200 - i + 2, "Low": 200 - i - 1, "Close": 200 - i}
            for i in range(300)
        ]

    def test_signal_field_exists_all_cases(self):
        for dataset in [self.uptrend_data, self.downtrend_data]:
            result = apply_strategy(dataset.copy())
            self.assertTrue(all("signal" in bar for bar in result))

    def test_rsi_signal_trigger(self):
        # Induce RSI drop
        data = [{"Close": 100 - i * 0.5} for i in range(50)]
        result = apply_strategy(data, stochastic=False, one23_setup=False, use_rsi=True)
        signals = [bar["signal"] for bar in result if bar.get("signal") == "BUY"]
        self.assertTrue(len(signals) > 0)

    def test_macd_crossover_signal(self):
        # Build a sequence that first trends down, then sharply up
        prices = [100 - 0.5 * i for i in range(30)]  # falling prices
        prices += [85 + i * 2 for i in range(15)]  # sharp rise to force crossover

        data = [{"Close": p} for p in prices]
        result = apply_macd_histogram_strategy(data)

        buy_signals = [bar for bar in result if bar.get("signal") == "BUY"]

        self.assertTrue(len(buy_signals) > 0, "Expected MACD crossover to trigger BUY signal.")


    def test_macd_histogram_shrink_signal(self):
        # Create histogram bar shrinking upward (bearish weakening)
        prices = [100 - 0.5 * i for i in range(30)]
        prices += [85 + 0.1 * i for i in range(30)]  # slowing drop = histogram rise
        data = [{"Close": p} for p in prices]
        result = apply_macd_histogram_strategy(data)
        signals = [bar for bar in result if bar.get("signal") == "BUY"]
        self.assertTrue(len(signals) > 0)


if __name__ == "__main__":
    unittest.main()
