
import pandas as pd
from fpdf import FPDF

from src.utils import (
    load_data_yfinance, get_binance_ohlc,apply_strategy
)


def generate_pdf_from_trades(all_trades, strategy_name, filename="backtest_report.pdf"):
    df = pd.DataFrame(all_trades)
    df.sort_values(by=["symbol"], inplace=True)

    pdf = FPDF(orientation='L', unit='mm', format='A4')
    pdf.set_auto_page_break(auto=True, margin=10)
    pdf.add_page()

    pdf.set_font("Arial", 'B', 16)
    pdf.cell(0, 10, "Relatório de Posições por Ativo", ln=True, align="C")
    pdf.ln(5)

    pdf.set_font("Arial", 'B', 12)
    pdf.set_fill_color(200, 220, 255)
    headers = ["Ativo", "Entrada", "Saída", "Retorno %", "Saída por"]
    widths = [40, 40, 40, 40, 50]

    for i, h in enumerate(headers):
        pdf.cell(widths[i], 10, h, border=1, align="C", fill=True)
    pdf.ln()

    pdf.set_font("Arial", '', 11)
    for _, row in df.iterrows():
        pdf.cell(widths[0], 8, str(row["symbol"]), border=1)
        pdf.cell(widths[1], 8, f'{row["entry_price"]:.2f}', border=1, align='C')
        pdf.cell(widths[2], 8, f'{row["exit_price"]:.2f}', border=1, align='C')
        pdf.cell(widths[3], 8, f'{row["return_%"]:.2f}', border=1, align='C')
        pdf.cell(widths[4], 8, str(row["exit_reason"]), border=1, align='C')
        pdf.ln()

    # Adicionar resumo consolidado por ativo
    pdf.add_page()
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(0, 10, "Resumo Consolidado por Ativo", ln=True, align="C")
    pdf.ln(5)

    summary = df.groupby("symbol").agg(
        num_trades=("return_%", "count"),
        win_rate=("return_%", lambda x: (x > 0).mean() * 100)
    ).reset_index()
    summary["estrategias"] = strategy_name
    pdf.set_font("Arial", 'B', 12)
    headers = ["Ativo", "Trades", "Win Rate %", "Estratégias"]
    widths = [40, 30, 40, 80]

    for i, h in enumerate(headers):
        pdf.cell(widths[i], 10, h, border=1, align="C", fill=True)
    pdf.ln()

    pdf.set_font("Arial", '', 11)
    for _, row in summary.iterrows():
        pdf.cell(widths[3], 8, row["estrategias"], border=1, align="L")
        pdf.cell(widths[0], 8, row["symbol"], border=1)
        pdf.cell(widths[1], 8, f"{int(row['num_trades'])}", border=1, align="C")
        pdf.cell(widths[2], 8, f"{row['win_rate']:.1f}%", border=1, align="C")
        pdf.ln()

    pdf.output(filename)
    print(f"📄 PDF gerado com sucesso: {filename}")


def backtest_ticker(symbol, strategy_params, interval="1h", max_hold=7, crypto_only=False):
    if crypto_only:
        data = get_binance_ohlc(symbol=symbol, interval=interval, limit=500)
    else:
        data = load_data_yfinance(symbol=symbol, period="90d", interval=interval)

    if not data:
        return []

    apply_strategy(data, **strategy_params)

    trades = []
    in_trade = False
    entry_price = entry_index = None

    for i, bar in enumerate(data):

        # Determinar qual campo de sinal usar
        signal = None

        if strategy_params.get("use_rsi"):
            signal = bar.get("signal_rsi")
        elif strategy_params.get("macd"):
            signal = bar.get("signal_macd")
        elif strategy_params.get("one23_setup"):
            signal = bar.get("signal_123")
        elif strategy_params.get("stochastic"):
            signal = bar.get("signal_stochastic")

        if not in_trade and signal == "BUY":
            entry_price = bar["Close"]
            entry_index = i
            in_trade = True
            continue

        if in_trade:
            exit_due_to_signal = signal == "SELL"
            exit_due_to_time = (i - entry_index) >= max_hold

            if exit_due_to_signal or exit_due_to_time:
                exit_price = bar["Close"]
                change = (exit_price - entry_price) / entry_price * 100
                trades.append({
                    "symbol": symbol,
                    "entry_price": round(entry_price, 4),
                    "exit_price": round(exit_price, 4),
                    "return_%": round(change, 2),
                    "exit_reason": "signal" if exit_due_to_signal else "timeout"
                })
                in_trade = False
                entry_price = entry_index = None

    return trades

def save_simplified_report(all_trades, filename="backtest_report_simplified.csv"):
    simplified = [
        {
            "symbol": t["symbol"],
            "entry_price": t["entry_price"],
            "exit_price": t["exit_price"],
            "return_%": t["return_%"],
            "exit_reason": t["exit_reason"]
        }
        for t in all_trades
    ]
    df = pd.DataFrame(simplified)
    df.to_csv(filename, index=False)
    print(f"✅ Simplified report saved to {filename}")
    return df

def run_batch_backtest(tickers, strategy_params, crypto_only):
    strategy_name = ", ".join([k for k, v in strategy_params.items() if v])
    all_trades = []
    for symbol in tickers:
        print(f"🔍 Backtesting {symbol}...")
        trades = backtest_ticker(symbol=symbol, strategy_params=strategy_params, crypto_only=crypto_only)
        all_trades.extend(trades)

    if all_trades:
        generate_pdf_from_trades(all_trades, strategy_name)
        df_simplified = save_simplified_report(all_trades)

        print("\n📊 Summary by symbol:")
        print(df_simplified.groupby("symbol")["return_%"].describe())

        print("\n🔁 Summary by exit reason:")
        print(df_simplified.groupby("exit_reason")["return_%"].describe())
    else:
        print("⚠️ No trades executed.")


if __name__ == "__main__":
    crypto_tickers = pd.read_csv("../quantfury_crypto_tickers.csv")["Ticker"].tolist()
    tickers = pd.read_csv("../quantfury_tickers.csv")["Ticker"].tolist()
    strategy_params = {
        "macd": False,
        "one23_setup": True,
        "stochastic": False,
        "use_rsi": True
    }
    run_batch_backtest(crypto_tickers, strategy_params, crypto_only=True)



