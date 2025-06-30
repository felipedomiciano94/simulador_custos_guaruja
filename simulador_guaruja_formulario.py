import streamlit as st
import pandas as pd
from unidecode import unidecode

st.set_page_config(page_title="Simulador Guarujá", layout="wide")
st.image("logo.png", width=150)
st.title("🚛 Simulador de custos Transporte - Guarujá")


# Upload base
arquivo = st.file_uploader("📂 Faça o upload do arquivo base_importacao_guaruja.xlsx", type="xlsx")
if not arquivo:
    st.warning("⚠️ Aguarde o upload do arquivo para continuar.")
    st.stop()

# Leitura e padronização do CSV de custos
try:
    df_custos = pd.read_csv("custos_consolidados.csv", sep=",")
    df_custos.columns = df_custos.columns.str.upper().str.strip()
except FileNotFoundError:
    st.error("❌ Arquivo 'custos_consolidados.csv' não encontrado.")
    st.stop()

# Verificação das colunas obrigatórias
required = {"ORIGEM", "DESTINO", "CUSTO_FROTA", "CUSTO_AGREGADO"}
if not required.issubset(set(df_custos.columns)):
    st.error(f"❌ Colunas faltando em custos_consolidados.csv: {required - set(df_custos.columns)}")
    st.stop()

# Normalização
df_custos["ORIGEM_NORM"] = df_custos["ORIGEM"].apply(lambda x: unidecode(str(x).upper().strip()))
df_custos["DESTINO_NORM"] = df_custos["DESTINO"].apply(lambda x: unidecode(str(x).upper().strip()))

# Abas
aba = st.sidebar.radio("Escolha a aba:", ["🚛 Simulador de Rota", "📋 Demandas do Dia"])

# -------------------- ABA 1 - SIMULADOR DE ROTA --------------------
if aba == "🚛 Simulador de Rota":
    st.title("🚛 Simulador por Rota - Guarujá")

    origem = st.selectbox("Escolha a origem", sorted(df_custos["ORIGEM"].unique()))
    destino = st.selectbox("Escolha o destino", sorted(df_custos["DESTINO"].unique()))

    origem_norm = unidecode(origem.upper().strip())
    destino_norm = unidecode(destino.upper().strip())

    rota = df_custos[
        (df_custos["ORIGEM_NORM"] == origem_norm) &
        (df_custos["DESTINO_NORM"] == destino_norm)
    ]

    if rota.empty:
        st.error("❌ Rota não encontrada nos custos.")
    else:
        custo_frota = float(rota["CUSTO_FROTA"].values[0])
        custo_agregado = float(rota["CUSTO_AGREGADO"].values[0])
        melhor_modal = "Frota Própria" if custo_frota < custo_agregado else "Agregado"
        saving = round(custo_agregado - custo_frota, 2) if melhor_modal == "Frota Própria" else 0

        col1, col2, col3, col4 = st.columns(4)
        col1.metric("💰 Custo Frota", f"R$ {custo_frota:,.2f}")
        col2.metric("🚛 Custo Agregado", f"R$ {custo_agregado:,.2f}")
        col3.metric("📌 Melhor Custo", melhor_modal)
        col4.metric("✅ Saving Recuperado", f"R$ {saving:,.2f}")

# -------------------- ABA 2 - DEMANDAS DO DIA --------------------
elif aba == "📋 Demandas do Dia":
    st.title("📋 Demandas do Dia + Sugestão de Alocação")

    df_demandas = pd.read_excel(arquivo, sheet_name="Base Importacao", skiprows=1)
    df_depara = pd.read_excel(arquivo, sheet_name="DEPARA")

    df_demandas.columns = df_demandas.columns.str.upper().str.strip()
    df_depara.columns = df_depara.columns.str.upper().str.strip()

    mapeia_orig = dict(zip(df_depara["LOCAL_ORIGEM_RAW"], df_depara["ORIGEM (CIDADE/UF)"]))
    df_demandas["ORIGEM_MAPEADA"] = df_demandas["ORIGEM"].map(mapeia_orig)
    df_demandas["DESTINO_MAPEADO"] = df_demandas["DESTINO"]

    df_demandas["ORIGEM_NORM"] = df_demandas["ORIGEM_MAPEADA"].apply(lambda x: unidecode(str(x).upper().strip()))
    df_demandas["DESTINO_NORM"] = df_demandas["DESTINO_MAPEADO"].apply(lambda x: unidecode(str(x).upper().strip()))

    df_merge = pd.merge(df_demandas, df_custos, on=["ORIGEM_NORM", "DESTINO_NORM"], how="left")

    df_merge["MELHOR CUSTO"] = df_merge.apply(
        lambda r: "Frota Própria" if r["CUSTO_FROTA"] < r["CUSTO_AGREGADO"] else "Agregado", axis=1
    )
    df_merge["SAVING RECUPERADO"] = df_merge.apply(
        lambda r: max(r["CUSTO_AGREGADO"] - r["CUSTO_FROTA"], 0), axis=1
    )

    mostrar = [
        "DEMANDA KMM", "DATA", "CLIENTE", "ORIGEM_MAPEADA", "DESTINO_MAPEADO",
        "HORÁRIO REQUERIDO", "AGENDAMENTO",
        "CUSTO_AGREGADO", "CUSTO_FROTA", "MELHOR CUSTO", "SAVING RECUPERADO"
    ]
    st.dataframe(df_merge[mostrar], use_container_width=True)
