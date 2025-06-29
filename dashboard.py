import streamlit as st
import pandas as pd
import plotly.express as px
import subprocess

st.set_page_config(page_title="Trading Sniper Dashboard", layout="wide")
st.title("📈 Dashboard de Sinais de Trading")

# Botão para atualizar sinais
if st.button("🔄 Atualizar Sinais Agora"):
    with st.spinner("Executando análise..."):
        result = subprocess.run(["python3", "signal_monitor.py"], capture_output=True, text=True)
        if result.returncode == 0:
            st.success("Sinais atualizados com sucesso!")
        else:
            st.error("Erro ao atualizar os sinais.")
            st.text(result.stderr)

# Carregamento dos dados
try:
    df = pd.read_csv("last_signals.csv")
except FileNotFoundError:
    st.warning("Nenhum arquivo 'last_signals.csv' encontrado.")
    st.stop()

# Filtros
with st.sidebar:
    st.header("🔎 Filtros")
    ativos = st.multiselect("Filtrar Ativos", df["ativo"].unique(), default=list(df["ativo"].unique()))
    sinais = st.multiselect("Filtrar Sinais", ["BUY", "SELL"], default=["BUY", "SELL"])
    estrategias = st.multiselect("Filtrar Estratégias", df["strategy"].unique(), default=list(df["strategy"].unique()))

# Aplicar filtros
filtro = df[
    df["ativo"].isin(ativos) &
    df["signal"].isin(sinais) &
    df["strategy"].isin(estrategias)
]

st.subheader("📋 Últimos Sinais Gerados")
st.dataframe(filtro.sort_values("timestamp", ascending=False), use_container_width=True)

# Gráfico interativo
if not filtro.empty:
    st.subheader("📊 Evolução das Entradas")
    fig = px.scatter(
        filtro,
        x="timestamp",
        y="entry",
        color="signal",
        hover_data=["ativo", "strategy", "entry", "stop_loss", "take_profit"],
        title="Sinais por Entrada"
    )
    st.plotly_chart(fig, use_container_width=True)
else:
    st.info("Nenhum dado para exibir com os filtros atuais.")