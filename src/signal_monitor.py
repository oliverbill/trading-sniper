import configparser
import os
import time
import traceback
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime

import pandas as pd
import pytz
from pandas import to_datetime
from streamlit import empty

from indicators import calculate_rsi, calculate_stochastic, calculate_macd
from investment_strategy import InvestmentStrategy
from strategy_profile_enum import StrategyProfileEnum
from strategy_utils import read_crypto_symbols_from_csv, read_stocks_symbols_from_csv, get_binance_ohlc, \
    get_ohlc_polygon, send_telegram_alert

MAX_WORKERS=30

def format_signal(asset, signal, strategy, entry, sl, tp, row):
    now = datetime.now()
    debug_info = (
        f"\n📊 Indicadores:\n"
        f"   • Stoch %K: {row['stoch_k']:.2f}\n"
        f"   • Stoch %D: {row['stoch_d']:.2f}\n"
        f"   • RSI: {row['rsi']:.2f}\n"
        f"   • MACD: {row['macd']:.2f}\n"
        f"   • MACD Signal: {row['macd_signal']:.2f}"
    )

    if signal == "WAIT":
        return
    else:
        return (
            f"📈 Ativo: {asset}\n"
            f"🧭 Sinal: {signal}\n"
            f"📚 Estratégia: {strategy}\n"
            f"📌 Entry: {entry} | SL: {sl} | TP: {tp}\n"
            f"🕒 Horário: {now.strftime('%Y-%m-%d %H:%M:%S')}{debug_info}"
        )

def check_signals(ticker, broker):
    try:
        df_ohlc = None
        if broker == "BINANCE":
            df_ohlc = get_binance_ohlc(ticker, interval="15m")
        elif broker == "B3":
            return None
        else:
            df_ohlc = get_ohlc_polygon(ticker, multiplier="1")

        if df_ohlc is None or df_ohlc.empty:
            return None

        if isinstance(df_ohlc.columns, pd.MultiIndex):
            df_ohlc.columns = [col[0] if isinstance(col, tuple) else col for col in df_ohlc.columns]

        if len(df_ohlc) < 26:
            print(f"Dados insuficientes para calcular indicadores (mínimo: 26 linhas): {len(df_ohlc)}")
            return None
        else:
            df_ohlc = calculate_rsi(df_ohlc)
            df_ohlc = calculate_macd(df_ohlc)
            df_ohlc = calculate_stochastic(df_ohlc)

        if df_ohlc is None:
            return None
        else:

            latest = df_ohlc.iloc[-1]
            investimentStrategy = InvestmentStrategy(StrategyProfileEnum.DAYTRADE, latest, [])
            trades = investimentStrategy.apply()

            if trades is empty:
                return None
            else:
                for trade in trades:
                    signal = trade["signal"]
                    strategy = trade["strategy"]
                    entry = trade["entry"]
                    sl = trade["stop_loss"]
                    tp = trade["take_profit"]

                    msg = format_signal(ticker, signal, strategy, entry, sl, tp, latest)
                    print(msg)
                    print("-" * 10)

                    send_telegram_alert(msg)

                    return {
                        "ativo": ticker,
                        "signal": signal,
                        "strategy": strategy,
                        "entry": entry,
                        "stop_loss": sl,
                        "take_profit": tp,
                        "rsi": latest["rsi"],
                        "stoch_k": latest["stoch_k"],
                        "stoch_d": latest["stoch_d"],
                        "macd": latest["macd"],
                        "macd_signal": latest["macd_signal"],
                        "timestamp": to_datetime(latest.name).strftime("%Y-%m-%d %H:%M:%S")
                    }

    except Exception as e:
        print(f"⚠️ Erro ao analisar {ticker}: {e}")
        print(traceback.format_exc())
        return None


def search_for_signals(export_file="last_signals.csv", ignore_market_hours=False):

    print("✅ Executando análise durante o pregão...")

    if not os.path.exists(export_file):
        pd.DataFrame(columns=[
            "ativo", "signal", "strategy", "entry", "stop_loss", "take_profit",
            "rsi", "stoch_k", "stoch_d", "macd", "macd_signal", "timestamp"
        ]).to_csv(export_file, index=False)

    assets = []
    stocks = read_stocks_symbols_from_csv("../quantfury_tickers.csv")
    for broker, symbols in stocks.items():
        for s in symbols:
            assets.append((s, broker))

    cryptos = read_crypto_symbols_from_csv("../quantfury_crypto_tickers.csv")
    for s in cryptos:
        assets.append((s, "BINANCE"))

    all_results = []

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = [executor.submit(check_signals, s, b) for s, b in assets]
        for future in as_completed(futures):
            result = future.result()
            if result:
                all_results.append(result)

    if all_results:
        pd.DataFrame(all_results).to_csv(export_file, mode='a', header=False, index=False)
        print(f"📁 {len(all_results)} sinais exportados para {export_file}")
    else:
        print("⚠️ Nenhum sinal gerado nesta rodada.")


def main_loop():
    while True:
        print(f"⏱️ Executando análise às {datetime.now().strftime('%H:%M:%S')}...")

        search_for_signals(ignore_market_hours=True)

        INTERVALO_MINUTOS = 15
        print(f"⏳ Aguardando {INTERVALO_MINUTOS} minuto(s) para a próxima execução...")
        time.sleep(INTERVALO_MINUTOS * 60)

if __name__ == "__main__":
    main_loop()