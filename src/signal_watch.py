
import time
import datetime
import pandas as pd
import os
import json

import pygame

from utils import (
    load_data_yfinance, get_binance_ohlc,
    apply_macd_histogram_strategy, apply_strategy, is_market_open_now, read_symbols_from_csv
)

LAST_SEEN_FILE = "../last_signals.json"

def play_alert_sound():
    pygame.mixer.init()
    pygame.mixer.music.load("../money.mp3")
    pygame.mixer.music.play()

def load_last_signals():
    if os.path.exists(LAST_SEEN_FILE):
        with open(LAST_SEEN_FILE, "r") as f:
            return json.load(f)
    return {}

def save_last_signals(signals):
    with open(LAST_SEEN_FILE, "w") as f:
        json.dump(signals, f)

def run_signal_scan(strategy_params):
    now = datetime.datetime.now()
    print(f"⏰ {now.strftime('%H:%M:%S')} – Scanning for signals...")
    crypto_tickers = read_symbols_from_csv("../quantfury_crypto_tickers.csv")
    tickers = read_symbols_from_csv("../quantfury_tickers.csv")

    triggered = []
    updated_signals = load_last_signals()

    if is_market_open_now():
        for symbol in tickers:
            data = load_data_yfinance(symbol, period="30d", interval="15m")
            if not data:
                continue
            detect_signals(data, now, symbol, triggered, updated_signals, strategy_params)

    for symbol in crypto_tickers:
        data = get_binance_ohlc(symbol, interval="15m")
        if not data:
            continue
        detect_signals(data, now, symbol, triggered, updated_signals, strategy_params)

    if triggered:
        for sym, sig, dt in triggered:
            print(f"🔔 {dt} – {sym}: {sig}")
        print("🔔 Playing alert...")
        play_alert_sound()
    else:
        print("🚫 No new signals.")

    save_last_signals(updated_signals)


def detect_signals(data, now, symbol, triggered, updated_signals, strategy_params):
    apply_strategy(data=data,**strategy_params)
    last_bar = data[-1]
    signal = last_bar.get("signal")
    if signal:
        last_date = last_bar.get("Date") or last_bar.get("date") or now.strftime("%Y-%m-%d %H:%M")
        previous = updated_signals.get(symbol)
        if previous != last_date:
            print(f"✅ New signal for {symbol}: {signal} @ {now.strftime("%Y-%m-%d %H:%M")}")
            triggered.append((symbol, signal, last_date))
            updated_signals[symbol] = last_date


def main_loop(strategy_params):
    while True:
        run_signal_scan(strategy_params=strategy_params)
        print("⏳ Waiting 2 minutes...\n")
        time.sleep(120)  # wait 2 minutes


if __name__ == "__main__":
    strategy_params = {
        "macd": False,
        "one23_setup": True,
        "stochastic": False,
        "use_rsi": True
    }
    main_loop(strategy_params=strategy_params)
