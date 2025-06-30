import streamlit as st
import pandas as pd
from unidecode import unidecode

# -----------------------------
# 1. Upload do arquivo de demandas
# -----------------------------
arquivo = st.file_uploader(
    "📂 Faça o upload do arquivo base_importacao_guaruja.xlsx",
    type="xlsx"
)
if not arquivo:
    st.warning("⚠️ Aguarde o upload do arquivo para continuar.")
    st.stop()

# -----------------------------
# 2. Carregar custos de rota via CSV tab-delimitado
# -----------------------------
try:
    df_custos = pd.read_csv(
        "rotas_embutidas.csv",
        sep="\t",                       # usa tabulação como separador
        dtype={"CUSTO_FROTA": float, "CUSTO_AGREGADO": float}
    )
except FileNotFoundError:
    st.error("❌ Arquivo 'rotas_embutidas.csv' não encontrado. Verifique o nome e o caminho.")
    st.stop()

# Padronizar nomes de colunas
df_custos.columns = df_custos.columns.str.upper().str.strip()

# Validar colunas essenciais
required = {"ORIGEM", "DESTINO", "CUSTO_FROTA", "CUSTO_AGREGADO"}
if not required.issubset(df_custos.columns):
    faltam = required - set(df_custos.columns)
    st.error(f"❌ Colunas ausentes em rotas_embutidas.csv: {faltam}")
    st.stop()

# Normalizar para lookup
df_custos["ORIGEM_NORM"] = df_custos["ORIGEM"].apply(lambda x: unidecode(str(x).upper().strip()))
df_custos["DESTINO_NORM"] = df_custos["DESTINO"].apply(lambda x: unidecode(str(x).upper().strip()))


# -----------------------------
# 3. Leitura da planilha de demandas e De-Para
# -----------------------------
df_demandas = pd.read_excel(arquivo, sheet_name="Base Importacao", skiprows=1)
df_depara   = pd.read_excel(arquivo, sheet_name="DEPARA")

# Padronizar cabeçalhos
df_depara.columns   = df_depara.columns.str.upper().str.strip()
df_demandas.columns = df_demandas.columns.str.upper().str.strip()

# -----------------------------
# 4. Menu de abas
# -----------------------------
aba = st.sidebar.radio(
    "Escolha a aba:",
    ["🚛 Simulador por Rota", "📋 Demandas do Dia"]
)

# -----------------------------
# 5. Simulador por Rota
# -----------------------------
if aba == "🚛 Simulador por Rota":
    st.title("🚛 Simulador por Rota - Guarujá")

    origem = st.selectbox("Escolha a origem", df_custos["ORIGEM"].unique())
    destino = st.selectbox("Escolha o destino", df_custos["DESTINO"].unique())

    rota = df_custos[
        (df_custos["ORIGEM"] == origem) &
        (df_custos["DESTINO"] == destino)
    ]
    if rota.empty:
        st.error("❌ Rota não encontrada nos custos carregados.")
    else:
        custo_frota    = rota["CUSTO_FROTA"].values[0]
        custo_agregado = rota["CUSTO_AGREGADO"].values[0]
        melhor_modal   = "Frota Própria" if custo_frota < custo_agregado else "Agregado"
        saving         = round(custo_agregado - custo_frota, 2) if melhor_modal == "Frota Própria" else 0

        c1, c2, c3, c4 = st.columns(4)
        c1.metric("💰 Custo Frota",       f"R$ {custo_frota:,.2f}")
        c2.metric("🚛 Custo Agregado",    f"R$ {custo_agregado:,.2f}")
        c3.metric("📌 Melhor Custo",      melhor_modal)
        c4.metric("✅ Saving Recuperado", f"R$ {saving:,.2f}")

# -----------------------------
# 6. Demandas do Dia + Sugestão
# -----------------------------
elif aba == "📋 Demandas do Dia":
    st.title("📋 Demandas do Dia + Sugestão de Alocação")

    # Mapear ORIGEM e DESTINO via DEPARA
    mapeia_orig   = dict(zip(df_depara["ORIGEM PLANILHA"], df_depara["ORIGEM REAL"]))
    mapeia_dest   = dict(zip(df_depara["DESTINO PLANILHA"], df_depara["DESTINO REAL"]))

    df_demandas["ORIGEM_MAPEADA"] = df_demandas["ORIGEM"].map(mapeia_orig)
    df_demandas["DESTINO_MAPEADO"] = df_demandas["DESTINO"].map(mapeia_dest)

    # Normalizar para merge
    df_demandas["ORIGEM_NORM"]  = df_demandas["ORIGEM_MAPEADA"].apply(lambda x: unidecode(str(x).upper().strip()))
    df_demandas["DESTINO_NORM"] = df_demandas["DESTINO_MAPEADO"].apply(lambda x: unidecode(str(x).upper().strip()))

    # Cruzar com custos carregados
    df_merge = pd.merge(
        df_demandas,
        df_custos,
        on=["ORIGEM_NORM", "DESTINO_NORM"],
        how="left"
    )

    # Calcular sugestão
    df_merge["MELHOR CUSTO"] = df_merge.apply(
        lambda r: "Frota Própria" if r["CUSTO_FROTA"] < r["CUSTO_AGREGADO"] else "Agregado",
        axis=1
    )
    df_merge["SAVING RECUPERADO"] = df_merge.apply(
        lambda r: max(r["CUSTO_AGREGADO"] - r["CUSTO_FROTA"], 0),
        axis=1
    )

    # Colunas finais
    mostrar = [
        "DEMANDA KMM", "DATA", "CLIENTE",
        "ORIGEM", "DESTINO","HORÁRIO REQUERIDO","AGENDAMENTO",
        "CUSTO_AGREGADO","CUSTO_FROTA","MELHOR CUSTO","SAVING RECUPERADO"
    ]
    st.dataframe(df_merge[mostrar], use_container_width=True)
