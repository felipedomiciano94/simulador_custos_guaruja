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
# 2. Carregar custos de rota de CSV
# -----------------------------
# Atenção: aqui o nome 'rotas_embutidas.csv' deve bater exatamente com seu arquivo
df_custos = pd.read_csv("rotas_embutidas.csv")  # ou .txt coma tabulação: sep='\t'
# Normalizar texto
df_custos["ORIGEM"] = df_custos["ORIGEM"].apply(lambda x: unidecode(str(x).upper().strip()))
df_custos["DESTINO"] = df_custos["DESTINO"].apply(lambda x: unidecode(str(x).upper().strip()))
df_custos["CUSTO_FROTA"] = df_custos["CUSTO_FROTA"].astype(float)
df_custos["CUSTO_AGREGADO"] = df_custos["CUSTO_AGREGADO"].astype(float)

# Garantir colunas de lookup
df_custos["ORIGEM_NORM"] = df_custos["ORIGEM"]
df_custos["DESTINO_NORM"] = df_custos["DESTINO"]

# -----------------------------
# 3. Leitura da planilha de demandas e depara
# -----------------------------
df_demandas = pd.read_excel(arquivo, sheet_name="Base Importacao", skiprows=1)
df_depara   = pd.read_excel(arquivo, sheet_name="DEPARA")
df_depara.columns = df_depara.columns.str.upper()
df_demandas.columns = df_demandas.columns.str.upper()

# -----------------------------
# 4. Navegação de abas
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
        custo_frota   = rota["CUSTO_FROTA"].values[0]
        custo_agregado= rota["CUSTO_AGREGADO"].values[0]
        melhor_modal  = "Frota Própria" if custo_frota < custo_agregado else "Agregado"
        saving        = round(custo_agregado - custo_frota, 2) if melhor_modal == "Frota Própria" else 0

        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Custo Frota",      f"R$ {custo_frota:,.2f}")
        c2.metric("Custo Agregado",   f"R$ {custo_agregado:,.2f}")
        c3.metric("Melhor Custo",     melhor_modal)
        c4.metric("Saving Recuperado",f"R$ {saving:,.2f}")

# -----------------------------
# 6. Demandas do Dia + Sugestão
# -----------------------------
elif aba == "📋 Demandas do Dia":
    st.title("📋 Demandas do Dia + Sugestão de Alocação")

    # DEPARA das origens/destinos
    df_demandas["ORIGEM_MAPEADA"] = df_demandas["ORIGEM"].map(
        dict(zip(df_depara["ORIGEM PLANILHA"], df_depara["ORIGEM REAL"]))
    )
    df_demandas["DESTINO_MAPEADO"] = df_demandas["DESTINO"].map(
        dict(zip(df_depara["DESTINO PLANILHA"], df_depara["DESTINO REAL"]))
    )
    df_demandas["ORIGEM_NORM"] = df_demandas["ORIGEM_MAPEADA"].apply(lambda x: unidecode(str(x).upper().strip()))
    df_demandas["DESTINO_NORM"] = df_demandas["DESTINO_MAPEADO"].apply(lambda x: unidecode(str(x).upper().strip()))

    # Merge com custos
    df_merge = pd.merge(
        df_demandas,
        df_custos,
        on=["ORIGEM_NORM", "DESTINO_NORM"],
        how="left"
    )

    # Cálculo de sugestão
    df_merge["MELHOR CUSTO"] = df_merge.apply(
        lambda r: "Frota Própria" if r["CUSTO_FROTA"] < r["CUSTO_AGREGADO"] else "Agregado",
        axis=1
    )
    df_merge["SAVING RECUPERADO"] = df_merge.apply(
        lambda r: max(r["CUSTO_AGREGADO"] - r["CUSTO_FROTA"], 0),
        axis=1
    )

    colunas_exibir = [
        "SOLICITACAO_CARGA_ID","DATA","CLIENTE",
        "ORIGEM","DESTINO","HORARIO REQUERIDO","AGENDAMENTO",
        "CUSTO_AGREGADO","CUSTO_FROTA","MELHOR CUSTO","SAVING RECUPERADO"
    ]
    st.dataframe(df_merge[colunas_exibir], use_container_width=True)
