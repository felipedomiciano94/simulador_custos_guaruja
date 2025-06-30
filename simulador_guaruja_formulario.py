import streamlit as st
import pandas as pd
from unidecode import unidecode

# -----------------------------
# 1. Upload do arquivo
# -----------------------------
arquivo = st.file_uploader("📂 Faça o upload do arquivo base_importacao_guaruja.xlsx", type="xlsx")

if not arquivo:
    st.warning("⚠️ Aguarde o upload do arquivo para continuar.")
    st.stop()

# -----------------------------
# 2. Custos embutidos no código
# -----------------------------
ROTAS_CUSTOS = [
    {"ORIGEM": "SANTOS", "DESTINO": "JUNDIAÍ", "CUSTO_FROTA": 950, "CUSTO_AGREGADO": 1200},
    {"ORIGEM": "SANTOS", "DESTINO": "SUMARÉ", "CUSTO_FROTA": 1050, "CUSTO_AGREGADO": 1300},
    {"ORIGEM": "GUARUJÁ", "DESTINO": "SÃO PAULO", "CUSTO_FROTA": 980, "CUSTO_AGREGADO": 1250},
    {"ORIGEM": "GUARUJÁ", "DESTINO": "CAMPINAS", "CUSTO_FROTA": 1020, "CUSTO_AGREGADO": 1280},
    {"ORIGEM": "GUARUJÁ", "DESTINO": "JUNDIAÍ", "CUSTO_FROTA": 990, "CUSTO_AGREGADO": 1220},
]

df_rotas = pd.DataFrame(ROTAS_CUSTOS)

# Normalização de textos
df_rotas["ORIGEM_NORM"] = df_rotas["ORIGEM"].apply(lambda x: unidecode(x.upper().strip()))
df_rotas["DESTINO_NORM"] = df_rotas["DESTINO"].apply(lambda x: unidecode(x.upper().strip()))

# -----------------------------
# 3. Leitura da planilha
# -----------------------------
df_demandas = pd.read_excel(arquivo, sheet_name="25-06", skiprows=1)
df_depara = pd.read_excel(arquivo, sheet_name="DEPARA")

# -----------------------------
# 4. Aba de navegação lateral
# -----------------------------
aba = st.sidebar.radio("Escolha a aba:", ["🚛 Simulador por Rota", "📋 Demandas do Dia"])

# -----------------------------
# 5. Simulador por rota
# -----------------------------
if aba == "🚛 Simulador por Rota":
    st.title("🚛 Simulador por Rota - Guarujá")

    origem = st.selectbox("Escolha a origem", df_rotas["ORIGEM"].unique())
    destino = st.selectbox("Escolha o destino", df_rotas["DESTINO"].unique())

    rota_filtrada = df_rotas[(df_rotas["ORIGEM"] == origem) & (df_rotas["DESTINO"] == destino)]

    if rota_filtrada.empty:
        st.error("❌ Rota não encontrada nos custos embutidos.")
    else:
        custo_frota = rota_filtrada["CUSTO_FROTA"].values[0]
        custo_agregado = rota_filtrada["CUSTO_AGREGADO"].values[0]

        melhor_modal = "Frota Própria" if custo_frota < custo_agregado else "Agregado"
        saving = round(custo_agregado - custo_frota, 2) if melhor_modal == "Frota Própria" else 0

        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Custo Frota", f"R$ {custo_frota}")
        col2.metric("Custo Agregado", f"R$ {custo_agregado}")
        col3.metric("Melhor Custo", melhor_modal)
        col4.metric("Saving", f"R$ {saving}")

# -----------------------------
# 6. Demandas do Dia (com sugestão de alocação)
# -----------------------------
elif aba == "📋 Demandas do Dia":
    st.title("📋 Demandas do Dia + Sugestão de Alocação")

    # Mapeamento DEPARA
    df_depara.columns = df_depara.columns.str.upper()
    df_demandas.columns = df_demandas.columns.str.upper()

    df_demandas["ORIGEM_MAPEADA"] = df_demandas["ORIGEM"].map(
        dict(zip(df_depara["ORIGEM PLANILHA"], df_depara["ORIGEM REAL"]))
    )
    df_demandas["DESTINO_MAPEADO"] = df_demandas["DESTINO"].map(
        dict(zip(df_depara["DESTINO PLANILHA"], df_depara["DESTINO REAL"]))
    )

    df_demandas["ORIGEM_NORM"] = df_demandas["ORIGEM_MAPEADA"].apply(lambda x: unidecode(str(x).upper().strip()))
    df_demandas["DESTINO_NORM"] = df_demandas["DESTINO_MAPEADO"].apply(lambda x: unidecode(str(x).upper().strip()))

    # Mesclando com os custos
    df_merge = pd.merge(df_demandas, df_rotas, on=["ORIGEM_NORM", "DESTINO_NORM"], how="left")

    # Calculando sugestões
    df_merge["MELHOR CUSTO"] = df_merge.apply(
        lambda row: "Frota Própria" if row["CUSTO_FROTA"] < row["CUSTO_AGREGADO"] else "Agregado", axis=1
    )
    df_merge["SAVING RECUPERADO"] = df_merge.apply(
        lambda row: row["CUSTO_AGREGADO"] - row["CUSTO_FROTA"]
        if row["MELHOR CUSTO"] == "Frota Própria" else 0,
        axis=1
    )

    # Exibindo resultado final
    colunas_exibir = [
        "SOLICITACAO_CARGA_ID", "DATA", "CLIENTE", "ORIGEM", "DESTINO",
        "HORARIO REQUERIDO", "AGENDAMENTO", "CUSTO_AGREGADO", "CUSTO_FROTA",
        "MELHOR CUSTO", "SAVING RECUPERADO"
    ]

    st.dataframe(df_merge[colunas_exibir], use_container_width=True)


