import configparser

import pandas as pd
from polygon.rest import RESTClient

config = configparser.ConfigParser()
config.read("../config.ini")
client = RESTClient(config["polygon"]["api_key"])

def get_macd(ticker):
    macd = client.get_macd(
        ticker=ticker,
        timespan="day",
        adjusted=True,
        short_window=12,
        long_window=26,
        signal_window=9,
        series_type="close",
        order="desc",
    )
    if macd is None:
        return None
    else:
        return macd.values


def get_rsi(ticker):
    rsi = client.get_rsi(
        ticker=ticker,
        timespan="day",
        adjusted=True,
        window=14,
        series_type="close",
        order="desc",
    )
    if rsi is None:
        return None
    else:
        return rsi

def get_sma(ticker):
    sma = client.get_sma(
        ticker="AAPL",
        timespan="day",
        adjusted="true",
        window="50",
        series_type="close",
        order="desc",
    )
    if sma is None:
        return None
    else:
        return sma