class Candlestick:
    def __init__(self, open_price, close_price, high_price, low_price):
        self.open = open_price
        self.close = close_price
        self.high = high_price
        self.low = low_price

    def is_bullish(self):
        return self.close > self.open

    def is_bearish(self):
        return self.close < self.open

    def is_doji(self):
        return abs(self.close - self.open) <= 0.01 * (self.high - self.low)

    def is_the_opposite_type(self, other):
        if not isinstance(other, Candlestick):
            return NotImplemented

        return ((self.is_bullish() and other.is_bearish()) or
            (self.is_bearish() and other.is_bullish()))

    def is_same_pattern(self, other):
        if not isinstance(other, Candlestick):
            return NotImplemented

        return ((self.is_bullish() and other.is_bullish()) or
                (self.is_bearish() and other.is_bearish()))
