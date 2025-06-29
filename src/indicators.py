import traceback

import numpy as np
import pandas as pd

CLOSE_COLUMN = "close"
HIGH_COLUMN = "high"
LOW_COLUMN = "low"


def simple_moving_average(values, period):
    return [None if i < period - 1 else sum(values[i - period + 1:i + 1]) / period for i in range(len(values))]


def mean(values):
    return sum(values) / len(values) if values else None


def calculate_cci(highs, lows, closes, period=72):
    cci_values = []
    typical_prices = [(h + l + c) / 3 for h, l, c in zip(highs, lows, closes)]

    sma = simple_moving_average(typical_prices, period)

    for i in range(len(typical_prices)):
        if i < period - 1:
            cci_values.append(None)
        else:
            mean_tp = sma[i]
            window = typical_prices[i - period + 1:i + 1]
            mean_deviation = mean([abs(tp - mean_tp) for tp in window])
            if mean_deviation == 0:
                cci = 0
            else:
                cci = (typical_prices[i] - mean_tp) / (0.015 * mean_deviation)
            cci_values.append(cci)

    return cci_values


def calculate_bollinger_bands(df, price_column='Close', period=20, multiplier=2):
    """
    Calculate Bollinger Bands for a given price series.

    :param df: DataFrame containing price data.
    :param price_column: Name of the column with closing prices.
    :param period: Number of periods for moving average and standard deviation.
    :param multiplier: Standard deviation multiplier for the bands.
    :return: DataFrame with 'Upper Band', 'Middle Band', and 'Lower Band' columns.
    """
    df = df.copy()
    df['Middle Band'] = df[price_column].rolling(window=period).mean()
    df['Standard Deviation'] = df[price_column].rolling(window=period).std()
    df['Upper Band'] = df['Middle Band'] + (multiplier * df['Standard Deviation'])
    df['Lower Band'] = df['Middle Band'] - (multiplier * df['Standard Deviation'])
    df.fillna(0, inplace=True)  # Fill NaN values with 0
    return df[['Upper Band', 'Middle Band', 'Lower Band']]


def calculate_stochastic(df, k_period=14, d_period=3):
    try:
        if df is None:
            return None

        high = df[CLOSE_COLUMN]
        low = df[LOW_COLUMN]
        close = df[HIGH_COLUMN]

        lowest_low = low.rolling(window=k_period).min()
        highest_high = high.rolling(window=k_period).max()

        percent_k = 100 * ((close - lowest_low) / (highest_high - lowest_low))
        percent_d = percent_k.rolling(window=d_period).mean()

        df["stoch_k"] = percent_k
        df["stoch_d"] = percent_d
        df.fillna(0, inplace=True)  # Fill NaN values with 0
        return df

    except Exception as e:
        print(f"Error calculating STOCHASTIC: {e}")
        print(traceback.format_exc())
        return None


def calculate_rsi(df, length=14):
    try:
        if df is None:
            return None

        prices = df[CLOSE_COLUMN]
        delta = prices.diff()

        gain = np.where(delta > 0, delta, 0)
        loss = np.where(delta < 0, -delta, 0)

        avg_gain = pd.Series(gain).rolling(window=length).mean()
        avg_loss = pd.Series(loss).rolling(window=length).mean()

        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))

        df["rsi"] = pd.Series(rsi, index=prices.index)
        df.fillna(0, inplace=True)  # Fill NaN values with 0

        return df
    except Exception as e:
        print(f"Error calculating RSI: {e}")
        print(traceback.format_exc())
        return None


def calculate_ema(series, span):
    try:
        return series.ewm(span=span, adjust=False).mean()
    except Exception as e:
        print(f"Error calculating EMA: {e}")
        print(traceback.format_exc())
        return None


def calculate_macd(df, fast_period=12, slow_period=26, signal_period=9):
    try:
        if df is None:
            return None

        prices = df[CLOSE_COLUMN]
        ema_fast = calculate_ema(prices, span=fast_period)
        ema_slow = calculate_ema(prices, span=slow_period)
        macd_line = ema_fast - ema_slow
        signal_line = calculate_ema(macd_line, span=signal_period)
        histogram = macd_line - signal_line

        df["macd"] = macd_line
        df["macd_signal"] = signal_line
        df["macd_hist"] = histogram

        return df
    except Exception as e:
        print(f"Error calculating MACD: {e}")
        print(traceback.format_exc())
        return None