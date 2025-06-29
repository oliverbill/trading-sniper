import unittest

from candlestickpattern.one_two_three_pattern import OneTwoThreePattern
from candlestickpattern.candlestick import Candlestick

class TestOneTwoThreePattern(unittest.TestCase):

    def setUp(self):
        self.pattern = OneTwoThreePattern()

    def test_valid_123_pattern(self):
        candle1 = Candlestick(open_price=10, close_price=20, high_price=30, low_price=5)  # Bullish
        candle2 = Candlestick(open_price=15, close_price=12, high_price=25, low_price=10)  # Bearish
        candle3 = Candlestick(open_price=12, close_price=22, high_price=32, low_price=8)  # Bullish
        self.assertTrue(self.pattern.validate((candle1, candle2, candle3)))

    def test_invalid_123_pattern_same_type(self):
        candle1 = Candlestick(open_price=10, close_price=20, high_price=30, low_price=5)  # Bullish
        candle2 = Candlestick(open_price=12, close_price=18, high_price=28, low_price=8)  # Bullish
        candle3 = Candlestick(open_price=15, close_price=25, high_price=35, low_price=10)  # Bullish
        self.assertFalse(self.pattern.validate((candle1, candle2, candle3)))

    def test_invalid_123_pattern_out_of_range(self):
        candle1 = Candlestick(open_price=10, close_price=20, high_price=30, low_price=5)  # Bullish
        candle2 = Candlestick(open_price=15, close_price=12, high_price=35, low_price=4)  # Bearish
        candle3 = Candlestick(open_price=12, close_price=22, high_price=32, low_price=8)  # Bullish
        self.assertFalse(self.pattern.validate((candle1, candle2, candle3)))

    def test_invalid_candle_count(self):
        candle1 = Candlestick(open_price=10, close_price=20, high_price=30, low_price=5)  # Bullish
        candle2 = Candlestick(open_price=15, close_price=12, high_price=25, low_price=10)  # Bearish
        with self.assertRaises(ValueError):
            self.pattern.validate((candle1, candle2))  # Only two candles

if __name__ == "__main__":
    unittest.main()