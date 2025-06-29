import datetime

import pandas as pd

from candlestickpattern.candlestick import Candlestick
from candlestickpattern.abstract_candlestick_pattern import CandlestickPattern

"""
This class implements the OneTwoThree candlestick pattern.
"""
class OneTwoThreePattern(CandlestickPattern):
    def __init__(self, dataframe:pd.DataFrame, trades:list, candles:tuple=None):
        self.trades = trades
        if candles is not None and len(candles) != 3:
            raise ValueError("Exactly three candles are required for the 1-2-3 pattern.")
        else:
            self.dataframe = self.to_dataframe(candles)

        if dataframe is not None:
            self.dataframe = self.to_dataframe(self.candles)


    def validate(self):
        # Extract the first three rows as Candlestick objects
        candles = []
        for i in range(3):
            row = self.dataframe.iloc[i]
            candles.append(Candlestick(
                open_price=row["open"],
                close_price=row["close"],
                high_price=row["high"],
                low_price=row["low"]
            ))

        def is_buy_123_pattern() -> bool:
            return (
                    candles[0].is_bearish() and
                    candles[1].low < candles[0].low and candles[1].is_bullish() and
                    candles[2].high > candles[1].high
            )

        def is_sell_123_pattern() -> bool:
            return (
                    candles[0].is_bullish() and
                    candles[1].high > candles[0].high and candles[1].is_bearish() and
                    candles[2].low < candles[1].low
            )


        if is_buy_123_pattern:
            self.trades.append({
                "date": datetime.datetime.now(),
                "entry": candles[2].high,
                "stop_loss": candles[1].low + ((candles[1].low * 0.1)/100),
                "signal": "BUY",
                "strategy": "123_buy"
            })

        if is_sell_123_pattern:
            self.trades.append({
                "date": datetime.datetime.now(),
                "entry": candles[2].high,
                "stop_loss": candles[1].low + ((candles[1].low * 0.1) / 100),
                "signal": "SELL",
                "strategy": "123_buy"
            })


    def buildExample(self):
        candle1 = Candlestick(open_price=100, close_price=200, high_price=300, low_price=50)
        candle2 = Candlestick(open_price=100, close_price=200, high_price=300, low_price=50)
        candle3 = Candlestick(open_price=100, close_price=200, high_price=300, low_price=50)
        self.candles = (candle1, candle2, candle3)


    def to_dataframe(self, candles:tuple):
        """
        Converts the candles into a pandas DataFrame.
        """
        import pandas as pd

        data = [
            {
                "open": candle.open,
                "close": candle.close,
                "high": candle.high,
                "low": candle.low
            }
            for candle in candles
        ]
        return pd.DataFrame(data)