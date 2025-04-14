#!/usr/bin/env python3
import configparser
import csv
import matplotlib.pyplot as plt
import logging
import os
from datetime import datetime, time, timedelta
from os import environ

import mplfinance as mpf
import pandas as pd
import pytz
import requests

import yfinance as yf
import math

from polygon import RESTClient

logging.getLogger("yfinance").setLevel(logging.CRITICAL)

def is_market_open_now():
    """
    Returns True if current time is within US stock market hours (9:30am–4:00pm ET),
    """
    # Check current time in US/Eastern
    eastern = pytz.timezone("US/Eastern")
    now_et: datetime = datetime.now(eastern)

    # Weekday (Monday=0, Sunday=6)
    if now_et.weekday() >= 5:  # Saturday or Sunday
        return False

    market_open = time(9, 30)
    market_close = time(16, 0)

    return market_open <= now_et.time() <= market_close


def plot_strategy(data, symbol="SYMBOL", save=False, window=None):
    os.makedirs("../charts", exist_ok=True)

    df = pd.DataFrame(data)
    df["Date"] = pd.to_datetime(df["Date"])
    df.set_index("Date", inplace=True)

    if window:
        df = df.tail(window)

    df_candles = df[["Open", "High", "Low", "Close"]]

    plots = []
    panel_index = 1

    # Add SMAs (no panel needed)
    for col, color in [("SMA21", "orange"), ("SMA50", "blue"), ("SMA200", "purple")]:
        if col in df.columns and df[col].dropna().any():
            plots.append(mpf.make_addplot(df[col], color=color, width=1.0))

    # Add RSI
    if "RSI" in df.columns and df["RSI"].dropna().any():
        plots.append(mpf.make_addplot(df["RSI"], panel=panel_index, color="red", ylabel="RSI"))
        panel_index += 1

    # Add MACD panel
    macd_present = (
        "MACD" in df.columns and df["MACD"].dropna().any() and
        "SignalLine" in df.columns and df["SignalLine"].dropna().any() and
        "MACD_Hist" in df.columns and df["MACD_Hist"].dropna().any()
    )
    if macd_present:
        plots.append(mpf.make_addplot(df["MACD"], panel=panel_index, color="blue", ylabel="MACD"))
        plots.append(mpf.make_addplot(df["SignalLine"], panel=panel_index, color="orange"))
        plots.append(mpf.make_addplot(df["MACD_Hist"], panel=panel_index, type='bar', color="gray", alpha=0.4))
        panel_index += 1

    plot_kwargs = dict(
        type="candle",
        style="yahoo",
        title=f"{symbol} Strategy",
        volume=False,
        addplot=plots,
        figratio=(16, 9),
        figscale=1.2,
        warn_too_much_data=10000
    )

    if save:
        filename = f"charts/{symbol}_strategy.png"
        plot_kwargs["savefig"] = filename
        print(f"📈 Chart saved: {filename}")

    mpf.plot(df_candles, **plot_kwargs)
    # Adicionar sinais separados por estratégia
    if "signal_rsi" in df.columns:
        s_signal_rsi = pd.Series(index=df.index, dtype='float64')
        s_signal_rsi[df["signal_rsi"] == 'BUY'] = df["Low"] * 0.97
        plots.append(mpf.make_addplot(s_signal_rsi, type='scatter', marker='^', color='blue', markersize=80))
    if "signal_123" in df.columns:
        s_signal_123 = pd.Series(index=df.index, dtype='float64')
        s_signal_123[df["signal_123"] == 'BUY'] = df["Low"] * 0.97
        plots.append(mpf.make_addplot(s_signal_123, type='scatter', marker='^', color='green', markersize=80))
    if "signal_macd" in df.columns:
        s_signal_macd = pd.Series(index=df.index, dtype='float64')
        s_signal_macd[df["signal_macd"] == 'BUY'] = df["Low"] * 0.97
        plots.append(mpf.make_addplot(s_signal_macd, type='scatter', marker='^', color='orange', markersize=80))
    if "signal_stochastic" in df.columns:
        s_signal_stochastic = pd.Series(index=df.index, dtype='float64')
        s_signal_stochastic[df["signal_stochastic"] == 'BUY'] = df["Low"] * 0.97
        plots.append(mpf.make_addplot(s_signal_stochastic, type='scatter', marker='^', color='purple', markersize=80))
    plt.close()


def load_data_polygon(api_key, symbol, interval="1h", limit=300):
    """
    Loads OHLCV data for a stock from Polygon.io
    interval: '1d', '1h', '30m', etc.
    """
    client = RESTClient(api_key, trace=True)
    # Determine multiplier and timespan
    multiplier = 1
    timespan = "day" if interval == "1d" else "hour"

    # Date range: fetch enough for SMA200
    end = datetime.today()
    start = end - timedelta(days=365)
    from_str = start.strftime("%Y-%m-%d")
    to_str = end.strftime("%Y-%m-%d")

    try:
        response = client.get_aggs(
            ticker=symbol,
            multiplier=multiplier,
            timespan=timespan,
            from_=from_str,
            to=to_str,
            limit=limit,
            sort="asc"
        )
    except Exception as e:
        print(f"❌ Polygon error for {symbol}: {e}")
        return []

    ohlc_data = []
    for bar in response:
        dt = datetime.fromtimestamp(bar.timestamp / 1000)
        ohlc_data.append({
            "Date": dt.strftime("%Y-%m-%d %H:%M") if timespan == "hour" else dt.strftime("%Y-%m-%d"),
            "Open": bar.open,
            "High": bar.high,
            "Low":  bar.low,
            "Close": bar.close
        })

    return ohlc_data


def get_binance_ohlc(symbol, interval='1h', limit=1000):
    url = "https://api.binance.com/api/v3/klines"
    symbol_only = symbol.replace("-","")
    params = {
        "symbol": symbol_only,
        "interval": interval,
        "limit": limit
    }
    r = requests.get(url, params=params)
    ohlc = []
    if r.status_code == 200:
        data = r.json()
        for candle in data:
            timestamp = datetime.fromtimestamp(candle[0] / 1000).strftime('%Y-%m-%d %H:%M')
            ohlc.append({
                "Date": timestamp,
                "Open": float(candle[1]),
                "High": float(candle[2]),
                "Low":  float(candle[3]),
                "Close": float(candle[4])
            })

    return ohlc


def load_data_yfinance(symbol, period, interval='1h'):
    # 1) Download data with yfinance
    df = yf.download(tickers=symbol, period=period, interval=interval, progress=False)
    if df.empty:
        df = yf.download(tickers=symbol+".SA", period=period, interval=interval, progress=False)
        if df.empty:
            return []

    # yfinance's DataFrame has a DatetimeIndex. We'll convert it to ascending (oldest->newest).
    df.sort_index(inplace=True)

    # 2) Convert to a list of dicts
    data_list = []
    for dt, row in df.iterrows():
        # Some rows may have NaN; skip them
        if any(math.isnan(val) for val in [row["Open"].iloc[0],
                                           row["High"].iloc[0],
                                           row["Low"].iloc[0],
                                           row["Close"].iloc[0]]):

            continue

        # dt is a pandas Timestamp. Convert to "YYYY-MM-DD" string
        date_str = dt.strftime("%Y-%m-%d")

        data_list.append({
            "Date": date_str,
            "Open": float(row["Open"].iloc[0]),
            "High": float(row["High"].iloc[0]),
            "Low": float(row["Low"].iloc[0]),
            "Close": float(row["Close"].iloc[0])
        })

    return data_list


def simple_moving_average(values, period):
    """
    Compute SMA for each index in a list of floats.
    If not enough data, returns None for that index.
    """
    sma_list = []
    running_sum = 0.0
    window = []

    for i, val in enumerate(values):
        window.append(val)
        running_sum += val
        if i >= period:
            # Remove the oldest value
            running_sum -= window.pop(0)

        if i < period - 1:
            sma_list.append(None)
        else:
            sma_list.append(running_sum / period)
    return sma_list


def stochastic_k(data, period):
    """
    Calculates Stochastic %K for a list of OHLC data over a given period.
    Each item in `data` must be a dict with keys: "High", "Low", "Close".
    Returns a list of %K values (floats or None).
    """
    k_values = []
    d = range(len(data))
    for i in range(len(data)):
        if i + 1 < period:
            # Not enough data yet
            k_values.append(None)
            continue

        window = data[i + 1 - period : i + 1]  # slice from i-period+1 to i
        high_vals = [bar["High"] for bar in window]
        low_vals = [bar["Low"] for bar in window]
        close = data[i]["Close"]

        hh = max(high_vals)
        ll = min(low_vals)

        if hh == ll:
            k = 50.0  # Avoid division by zero
        else:
            k = (close - ll) / (hh - ll) * 100

        k_values.append(k)

    return k_values


def moving_average(values, period):
    """
    Minimal moving average function for Stochastic %D.
    If not enough data, store None.
    """
    ma_list = []
    window = []
    sum_window = 0.0

    for i, val in enumerate(values):
        if val is None:
            ma_list.append(None)
            window.append(0.0)
            continue

        window.append(val)
        sum_window += val

        if i >= period:
            sum_window -= window.pop(0)

        # Check if we have enough (non-zero) values in the current window
        valid_count = len([v for v in window if v != 0.0])
        if valid_count < period:
            ma_list.append(None)
        else:
            ma_list.append(sum_window / period)

    return ma_list


def crossover(prev_a, a, prev_b, b):
    """
    Return True if 'a' just crossed above 'b' on this bar:
    prev_a <= prev_b AND a > b
    """
    if any(x is None for x in (prev_a, a, prev_b, b)):
        return False
    return (prev_a <= prev_b) and (a > b)


def crossunder(prev_a, a, prev_b, b):
    """
    Return True if 'a' just crossed below 'b' on this bar:
    prev_a >= prev_b AND a < b
    """
    if any(x is None for x in (prev_a, a, prev_b, b)):
        return False
    return (prev_a >= prev_b) and (a < b)


def signal_by_setup123(data):
    for i in range(4, len(data)):
        p1 = data[i - 3]
        p2 = data[i - 2]
        p3 = data[i - 1]
        p4 = data[i]

        if (p1["Low"] < p2["Low"] and p2["High"] > p3["High"] and
            p3["Low"] > p1["Low"] and p4["Close"] > p2["High"]):
            data[i]["pattern123"] = "123buy"
        elif (p1["High"] > p2["High"] and p2["Low"] < p3["Low"] and
              p3["High"] < p1["High"] and p4["Close"] < p2["Low"]):
            data[i]["pattern123"] = "123sell"
        else:
            data[i]["pattern123"] = None

    # 🔁 Aplicar sinais após analisar todos os padrões
    for k in range(len(data)):
        signal = None
        pattern = data[k].get("pattern123")
        if data[k].get("bullCondition") and pattern == "123buy":
            signal = "BUY"
        elif data[k].get("bearCondition") and pattern == "123sell":
            signal = "SELL"
        data[k]["signal_123"] = signal

    return data


def calculate_macd(close_prices, fast=12, slow=26, signal=9):
    import pandas as pd
    close_series = pd.Series(close_prices)
    ema_fast = close_series.ewm(span=fast, adjust=False).mean()
    ema_slow = close_series.ewm(span=slow, adjust=False).mean()
    macd_line = ema_fast - ema_slow
    signal_line = macd_line.ewm(span=signal, adjust=False).mean()
    histogram = macd_line - signal_line
    return macd_line, signal_line, histogram


def calculate_rsi(closes, period=14):
    rsi = []
    gains, losses = [], []

    for i in range(1, len(closes)):
        change = closes[i] - closes[i - 1]
        gains.append(max(change, 0))
        losses.append(max(-change, 0))

    prev_avg_gain=0
    prev_avg_loss=0
    for i in range(len(closes)):
        if i < period:
            rsi.append(None)
        elif i == period:
            avg_gain = sum(gains[:period]) / period
            avg_loss = sum(losses[:period]) / period
            rs = avg_gain / avg_loss if avg_loss != 0 else float("inf")
            rsi.append(100 - (100 / (1 + rs)))
            prev_avg_gain = avg_gain
            prev_avg_loss = avg_loss
        else:
            change = closes[i] - closes[i - 1]
            gain = max(change, 0)
            loss = max(-change, 0)
            avg_gain = (prev_avg_gain * (period - 1) + gain) / period
            avg_loss = (prev_avg_loss * (period - 1) + loss) / period
            rs = avg_gain / avg_loss if avg_loss != 0 else float("inf")
            rsi.append(100 - (100 / (1 + rs)))
            prev_avg_gain = avg_gain
            prev_avg_loss = avg_loss

    return rsi


def apply_macd_histogram_strategy(data):
    closes = [bar["Close"] for bar in data]
    macd_line, signal_line, histogram = calculate_macd(closes,fast=144,slow=244,signal=12)

    for i in range(len(data)):
        data[i]["MACD"] = macd_line[i] if i < len(macd_line) else None
        data[i]["SignalLine"] = signal_line[i] if i < len(signal_line) else None
        data[i]["MACD_Hist"] = histogram[i] if i < len(histogram) else None
        data[i]["signal_macd"] = None  # <== ensures the key always exists

        if i >= 1:
            curr_hist = histogram[i]
            prev_hist = histogram[i - 1]

            # BUY condition: both negative and current bar is closer to zero (shrinking red)
            if prev_hist < 0 and curr_hist < 0 and curr_hist > prev_hist:
                data[i]["signal_macd"] = "BUY"
            if prev_hist > 0 and curr_hist > 0 and curr_hist < prev_hist:
                data[i]["signal_macd"] = "SELL"

    return data


def calculate_trend_by_sma(data):
    smaLen1, smaLen2, smaLen3 = 21, 50, 200
    closes = [bar["Close"] for bar in data]
    sma1 = simple_moving_average(closes, smaLen1)
    sma2 = simple_moving_average(closes, smaLen2)
    sma3 = simple_moving_average(closes, smaLen3)

    for i in range(len(data)):
        data[i]["SMA21"] = sma1[i]
        data[i]["SMA50"] = sma2[i]
        data[i]["SMA200"] = sma3[i]

    # --- C) Slope + Order + Signals
    for i in range(len(data)):
        if i == 0:
            data[i]["bullCondition"] = False
            data[i]["bearCondition"] = False
            continue

        prev21 = data[i - 1]["SMA21"]
        prev50 = data[i - 1]["SMA50"]
        prev200 = data[i - 1]["SMA200"]
        curr21 = data[i]["SMA21"]
        curr50 = data[i]["SMA50"]
        curr200 = data[i]["SMA200"]

        # If any are None, can't do slope checks
        if (prev21 is None or prev50 is None or prev200 is None or
                curr21 is None or curr50 is None or curr200 is None):
            data[i]["bullCondition"] = False
            data[i]["bearCondition"] = False
            continue

        # rising/falling
        sma1_rising = (curr21 > prev21)
        sma2_rising = (curr50 > prev50)
        sma3_rising = (curr200 > prev200)

        sma1_falling = (curr21 < prev21)
        sma2_falling = (curr50 < prev50)
        sma3_falling = (curr200 < prev200)

        # ascending/descending
        ascendingOrder = (curr21 > curr50) and (curr50 > curr200)
        descendingOrder = (curr21 < curr50) and (curr50 < curr200)

        # combine
        bullCondition = sma1_rising and sma2_rising and sma3_rising and ascendingOrder
        bearCondition = sma1_falling and sma2_falling and sma3_falling and descendingOrder

        data[i]["bullCondition"] = bullCondition
        data[i]["bearCondition"] = bearCondition
    return data


def apply_strategy(data, one23_setup=True, stochastic=True, use_rsi=True, macd=False):
    """
    data: list of dicts {"Date","Open","High","Low","Close"}
    """
    data = calculate_trend_by_sma(data)
    if stochastic:
        data = signal_stochastic(data)

    if use_rsi:
        data = signal_rsi(data)

    if one23_setup:
        data = signal_by_setup123(data)

    if macd:
        data = apply_macd_histogram_strategy(data)

    return data


def signal_rsi(data):
    closes = [bar["Close"] for bar in data]
    rsi_values = calculate_rsi(closes)
    for i in range(len(data)):
        data[i]["RSI"] = rsi_values[i] if i < len(rsi_values) else None
    for i in range(len(data)):
        if data[i].get("RSI") is not None:
            # check SMA trend direction
            if data[i].get("bearCondition"):
                adjusted_oversold = 40
                adjusted_overbought = 80
            else:
                adjusted_oversold = 30
                adjusted_overbought = 70

            if data[i]["RSI"] < adjusted_oversold:
                data[i]["signal_rsi"] = "BUY"
            elif data[i]["RSI"] > adjusted_overbought:
                data[i]["signal_rsi"] = "SELL"
    return data


def signal_stochastic(data):
    k_len, d_len = 8, 3
    # --- A) Stochastic
    k_values = stochastic_k(data, k_len)
    d_values = moving_average(k_values, d_len)
    # Store them
    for i in range(len(data)):
        data[i]["%K"] = k_values[i]
        data[i]["%D"] = d_values[i]
    overbought_list = []
    oversold_list = []
    for i in range(len(data)):
        if i == 0:
            overbought_list.append(False)
            oversold_list.append(False)
            continue

        prev_d = data[i - 1]["%D"]
        curr_d = data[i]["%D"]

        # Overbought = crossing from <=90 to >90
        is_overbought = False
        if (prev_d is not None and curr_d is not None):
            is_overbought = (prev_d <= 90) and (curr_d > 90)

        # Oversold = crossing from >=10 to <10
        is_oversold = False
        if (prev_d is not None and curr_d is not None):
            is_oversold = (prev_d >= 10) and (curr_d < 10)

        overbought_list.append(is_overbought)
        oversold_list.append(is_oversold)
    for i in range(len(data)):
        data[i]["overbought"] = overbought_list[i]
        data[i]["oversold"] = oversold_list[i]
        signal = None

    for i in range(len(data)):
        if data[i].get("bullCondition") and data[i].get("oversold"):
            signal = "BUY"

        elif data[i].get("bearCondition") and data[i].get("overbought"):
            signal = "SELL"

        data[i]["signal_stochastic"] = signal

    return data


def read_symbols_from_csv(filepath):
    """
    Expects a CSV file with at least one column named 'Symbol'.
    Returns a list of symbol strings.
    """
    symbols = []
    with open(filepath, mode="r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            sym = row.get("Ticker", "").strip()
            if sym:
                symbols.append(sym)
    return symbols


def main(mode="ALL", one23_setup=False, stochastic=False, macd_only=False, use_rsi=True):
    config = configparser.ConfigParser()
    config.read("../config.ini")
    api_key = config["polygon"]["api_key"]
    data = []
    tickers_with_signals = []
    if mode == "CRYPTO":
        symbols = read_symbols_from_csv("../quantfury_crypto_tickers.csv")
        i = 0
        for s in symbols:
            i += 1
            data = get_binance_ohlc(s,interval='1h')
            if not data:
                print("no data for "+s)
                continue
            apply_strategy_plot(data, s, tickers_with_signals, one23_setup, stochastic, macd_only, use_rsi)
    else:
        symbols = read_symbols_from_csv("../quantfury_tickers.csv")
        i = 0
        for s in symbols:
            i += 1
            if is_market_open_now():
                data = load_data_yfinance(symbol=s, period="30d", interval="1h")
                if not data:
                    data = load_data_polygon(api_key, s)
                    if not data:
                        continue
                apply_strategy_plot(data, s, tickers_with_signals, one23_setup, stochastic, macd_only, use_rsi)

    print("tickers with signals: " + str(tickers_with_signals))

def apply_strategy_plot(data, s, tickers_with_signals, one23_setup=True, stochastic=True, macd_only=False, use_rsi=True):
    if macd_only:
        data = apply_macd_histogram_strategy(data)
    else:
        data = apply_strategy(data, one23_setup, stochastic, macd_only, use_rsi)
    bars_with_signals = list(filter(lambda item: item["signal"] is not None, data))
    if len(bars_with_signals) > 0:
        #plot_strategy(data, symbol=s)
        tickers_with_signals.append(s)
    else:
        print("no signals for " + s)


if __name__ == "__main__":
    main("CRYPTO")