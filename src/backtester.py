# backtester.py
import pandas as pd
from fpdf import FPDF
from concurrent.futures import ProcessPoolExecutor
from strategy_runner import apply_strategy
from strategy_utils import read_stocks_symbols_from_csv, is_market_open_now, load_data_yfinance, \
    read_crypto_symbols_from_csv, get_binance_ohlc
import os

def backtest_symbol(df, symbol, timeout=7):
    trades = []
    in_position = False
    entry_price = 0
    entry_index = None
    entry_strategy = None

    for i in range(len(df)):
        row = df.iloc[i]
        signal = None
        strategy_used = None

        for strategy in ["signal_shadow", "signal_engulfing", "signal_insidebar", "signal_stochastic"]:
            if row.get(strategy) == "BUY":
                signal = "BUY"
                strategy_used = strategy
                break
            elif row.get(strategy) == "SELL":
                signal = "SELL"
                strategy_used = strategy
                break

        if not in_position and signal == "BUY":
            in_position = True
            entry_price = row["Close"]
            entry_index = i
            entry_strategy = strategy_used

        elif in_position:
            timeout_reached = i - entry_index >= timeout
            exit_signal = signal == "SELL"
            if timeout_reached or exit_signal:
                exit_price = row["Close"]
                trades.append({
                    "symbol": symbol,
                    "strategy": entry_strategy,
                    "entry_index": entry_index,
                    "exit_index": i,
                    "entry_price": entry_price,
                    "exit_price": exit_price,
                    "bars_held": i - entry_index,
                    "return_%": round((exit_price - entry_price) / entry_price * 100, 2),
                    "exit_reason": "timeout" if timeout_reached else "signal"
                })
                in_position = False

    return trades

def save_pdf_report(trades_df, filename="backtest_report.pdf"):
    if trades_df.empty:
        print("⚠️ No trades to report.")
        return

    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    pdf.set_font("Arial", "B", 14)
    pdf.cell(0, 10, "Resumo por Ativo e Estratégia", ln=True)

    grouped = trades_df.groupby(["symbol", "strategy"]).agg(
        win_rate=("return_%", lambda x: round((x > 0).mean() * 100, 2)),
        avg_return=("return_%", "mean"),
        total_trades=("return_%", "count")
    ).reset_index()

    pdf.set_font("Arial", "", 12)
    for _, row in grouped.iterrows():
        pdf.cell(0, 10,
                 f"{row['symbol']} ({row['strategy']}): {row['total_trades']} trades | "
                 f"Win Rate: {row['win_rate']}% | Avg Return: {round(row['avg_return'], 2)}%",
                 ln=True)

    pdf.output(filename)
    print(f"✅ Relatório gerado: {filename}")

def load_and_backtest(args):
    symbol, broker, params = args
    symbol_tag = symbol + ".SA" if broker == "B3" else symbol
    if broker == "CRYPTO":
        df = get_binance_ohlc(symbol_tag, interval="15m", limit=params["binance_limit"])
    else:
        df = load_data_yfinance(symbol=symbol_tag, period=params['period'])

    if df is None or df.empty:
        return []

    df = apply_strategy(df=df, params=params)
    return backtest_symbol(df, symbol_tag)

def run_backtest_parallel(params):
    args_list = []

    if params["ignore_market_open"] or is_market_open_now():
        stocks = read_stocks_symbols_from_csv()
        for broker, symbols in stocks.items():
            for symbol in symbols:
                args_list.append((symbol, broker, params))

    cryptos = read_crypto_symbols_from_csv()
    for symbol in cryptos:
        args_list.append((symbol, "CRYPTO", params))

    all_trades = []
    with ProcessPoolExecutor(max_workers=4) as executor:
        results = executor.map(load_and_backtest, args_list)
        for trades in results:
            all_trades.extend(trades)

    trades_df = pd.DataFrame(all_trades)
    save_pdf_report(trades_df)

if __name__ == "__main__":
    print("🚀 Running multithreaded backtester...")

    run_backtest_parallel({
        "signal_stochastic": True,
        "shadow_reversal": True,
        "engulfing": True,
        "ignore_market_open": True,
        "mode": "STOCKS",
        "print_signals": False,
        "full_scan": True,
        "period": "30d",
        "binance_limit": 500
    })
