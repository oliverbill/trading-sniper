import configparser
import csv
import logging
import traceback
from datetime import datetime, time, timedelta

import pandas as pd
import pytz
import requests
from polygon import RESTClient

logging.getLogger("yfinance").setLevel(logging.CRITICAL)

config = configparser.ConfigParser()
config.read("../config.ini")
client = RESTClient(config["polygon"]["api_key"])


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
        if not data:
            print("no data for " + symbol)
        for candle in data:
            timestamp = datetime.fromtimestamp(candle[0] / 1000).strftime('%Y-%m-%d %H:%M')
            ohlc.append({
                "Date": timestamp,
                "Open": float(candle[1]),
                "High": float(candle[2]),
                "Low":  float(candle[3]),
                "Close": float(candle[4])
            })
    # Convert the list of dictionaries to a DataFrame
    df = pd.DataFrame(ohlc)
    return df


def read_crypto_symbols_from_csv(filepath="../quantfury_crypto_tickers.csv"):
    """
    Reads a CSV file and returns a dictionary of symbols grouped by broker.
    Expects columns: 'Ticker' and 'Broker', separated by a semicolon.
    """
    symbols = []
    try:
        with open(filepath, mode="r", encoding="utf-8") as f:
            reader = csv.DictReader(f, delimiter=";")  # Specify semicolon as the delimiter
            if not reader.fieldnames:
                raise ValueError("CSV file is empty or malformed.")

            for row in reader:
                ticker = row.get("Ticker", "").strip()
                if ticker:
                    symbols.append(ticker)

            return symbols

    except FileNotFoundError:
        print(f"Error: File not found at {filepath}")
    except Exception as e:
        print(f"Error reading CSV file: {e}")


def read_stocks_symbols_from_csv(filepath="../quantfury_tickers.csv"):
    """
    Reads a CSV file and returns a dictionary of symbols grouped by broker.
    Expects columns: 'Ticker' and 'Broker', separated by a semicolon.
    """
    broker_symbols = {}
    try:
        with open(filepath, mode="r", encoding="utf-8") as f:
            reader = csv.DictReader(f, delimiter=";")  # Specify semicolon as the delimiter
            if not reader.fieldnames:
                raise ValueError("CSV file is empty or malformed.")
            if "Ticker" not in reader.fieldnames or "Broker" not in reader.fieldnames:
                raise ValueError("CSV file must contain 'Ticker' and 'Broker' columns.")

            for row in reader:
                ticker = row.get("Ticker", "").strip()
                broker = row.get("Broker", "").strip()
                if ticker and broker and broker != "CboeEurope" and broker != "BMV":
                    broker_symbols.setdefault(broker, []).append(ticker)

            return broker_symbols

    except FileNotFoundError:
        print(f"Error: File not found at {filepath}")
    except Exception as e:
        print(f"Error reading CSV file: {e}")


def print_signaled_symbols(data_by_symbol):
    """
    Exibe os sinais únicos por estratégia para cada ativo.
    """
    if not data_by_symbol:
        print("📌 Nenhum sinal detectado para os ativos escolhidos\n")
        return

    print("📌 Ativos com sinal detectado:\n")

    for symbol, df in data_by_symbol.items():
        unique_signals = []

        if "signal_shadow" in df.columns:
            vals = df["signal_shadow"].dropna().unique()
            for val in vals:
                unique_signals.append(f"signal_shadow: {val}")

        if "signal_engulfing" in df.columns:
            vals = df["signal_engulfing"].dropna().unique()
            for val in vals:
                unique_signals.append(f"signal_engulfing: {val}")

        if "signal_insidebar" in df.columns:
            vals = df["signal_insidebar"].dropna().unique()
            for val in vals:
                unique_signals.append(f"signal_insidebar: {val}")

        if unique_signals:
            print(f"🔔 {symbol}:")
            for signal in unique_signals:
                print(f"   → {signal}")


def send_telegram_alert(text):
    config = configparser.ConfigParser()
    config.read("../config.ini")

    token = config.get("telegram", "token")
    chat_id = config.get("telegram", "chat_id")

    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "Markdown"
    }
    try:
        requests.post(url, json=payload)
    except Exception as e:
        print(f"Erro ao enviar para o Telegram: {e}")


def get_config(config_file="../config.ini"):
    config = configparser.ConfigParser()
    config.read(config_file)
    return config

# polygon.exceptions.BadResponse: {"status":"NOT_AUTHORIZED","request_id":"9ce9032ef0db67ec900eec7d0e0d17ff","message":"You are not entitled to this data. Please upgrade your plan at https://polygon.io/pricing"}
# def get_ohlc_polygon(ticker, from_date="", to_date="", multiplier="5", timespan="minute"):
#     try:
#         last_quote = client.get_last_quote(ticker)
#         ohlc  = []
#         for a in client.get_aggs(
#             ticker,
#             1,
#             "minute",
#             "2022-01-01",
#             "2023-02-03",
#             limit=50000,
#         ):
#             ohlc.append(a)
#
#     except Exception as e:
#         print(f"Erro ao obter dados OHLC para {ticker}: {e}")
#         print(traceback.print_exc())


def get_ohlc_polygon(ticker, from_date="", to_date="", multiplier="15", timespan="minute"):
    """
    Obtém dados OHLC da API da Polygon.io para o ticker fornecido.

    :param ticker: Símbolo do ativo (ex: 'AAPL')
    :param multiplier: Multiplicador do intervalo de tempo (ex: 1)
    :param timespan: Intervalo de tempo ('minute', 'hour', 'day', etc.)
    :param from_date: Data de início no formato 'YYYY-MM-DD'
    :param to_date: Data de término no formato 'YYYY-MM-DD'
    :param api_key: Chave de API da Polygon.io
    :return: DataFrame com os dados OHLC
    """
    today = datetime.now().date()

    #from_date = (today - timedelta(days=1)).strftime("%Y-%m-%d") if from_date == "" else from_date
    from_date = today.strftime("%Y-%m-%d") if to_date == "" else to_date
    to_date = today.strftime("%Y-%m-%d") if to_date == "" else to_date
    api_key = get_config()["polygon"]["api_key"]

    url_snapshot = f"https://api.polygon.io/v2/snapshot/locale/us/markets/stocks/tickers/{ticker}/range/{multiplier}/{timespan}/{from_date}/{to_date}?apiKey={api_key}"
    url = f"https://api.polygon.io/v2/aggs/ticker/{ticker}/range/{multiplier}/{timespan}/{from_date}/{to_date}?adjusted=true&sort=asc&limit=120&apiKey={api_key}"

    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
        results = data.get('results', [])
        if not results:
            print(f"Nenhum dado encontrado para o ticker {ticker} no período especificado.")
            return None
        else:
            print("Ticker processado:"+ticker)
        df = pd.DataFrame(results)
        df['t'] = pd.to_datetime(df['t'], unit='ms')
        df.rename(columns={
            't': 'timestamp',
            'o': 'open',
            'h': 'high',
            'l': 'low',
            'c': 'close',
            'v': 'volume'
        }, inplace=True)
        df.set_index('timestamp', inplace=True)
        return df[['open', 'high', 'low', 'close', 'volume']]
    except requests.exceptions.HTTPError as http_err:
        raise RuntimeError(f"Erro HTTP: {http_err}")
    except requests.exceptions.RequestException as req_err:
        raise RuntimeError(f"Erro na requisição: {req_err}")
    except Exception as e:
        raise RuntimeError(f"Erro inesperado: {e}")


def get_latest_quote_polygon(ticker, from_date="", to_date="", multiplier="15", timespan="minute"):
    today = datetime.now().date()

    api_key = get_config()["polygon"]["api_key"]

    url = f"https://api.polygon.io/v2/snapshot/locale/us/markets/stocks/tickers/{ticker}?apiKey={api_key}"

    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
        results = data['ticker']['min']
        if not results:
            print(f"Nenhum dado encontrado para o ticker {ticker} no período especificado.")
            return None
        df = pd.DataFrame({k: [v] for k, v in results.items()})
        df['t'] = pd.to_datetime(df['t'], unit='ms')
        df.rename(columns={
            't': 'timestamp',
            'o': 'open',
            'h': 'high',
            'l': 'low',
            'c': 'close',
            'v': 'volume'
        }, inplace=True)
        df.set_index('timestamp', inplace=True)
        return df[['open', 'high', 'low', 'close', 'volume']]
    except requests.exceptions.HTTPError as http_err:
        raise RuntimeError(f"Erro HTTP: {http_err}")
    except requests.exceptions.RequestException as req_err:
        raise RuntimeError(f"Erro na requisição: {req_err}")
    except Exception as e:
        raise RuntimeError(f"Erro inesperado: {e}")