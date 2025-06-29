import streamlit as st
import pandas as pd

def aplicar_depara(df, depara_df, col, chave_origem='ORIGEM', chave_destino='PADRONIZADO'):
    """Aplica DEPARA para uma coluna específica"""
    mapa = dict(zip(depara_df[chave_origem], depara_df[chave_destino]))
    return df[col].map(mapa).fillna(df[col])

def render_sugestao_alocacao(upload_base=None, upload_precos=None):
    st.subheader("🚚 Sugestão de Alocação de Frota / Agregado")

    # Uploads (integração com Streamlit principal)
   # Precificação embutida no código
precos_df = pd.DataFrame([
    {'ORIGEM': 'GUARUJÁ/SP', 'DESTINO': 'ADAMANTINA/SP', 'CUSTO_AGREGADO': 8856.75, 'CUSTO_FROTA': 11480.85},
    {'ORIGEM': 'GUARUJÁ/SP', 'DESTINO': 'ADOLFO/SP', 'CUSTO_AGREGADO': 7424.97, 'CUSTO_FROTA': 10010.23},
    # Adicione mais linhas conforme necessário
])


    if upload_precos is not None:
        precos_df = pd.read_excel(upload_precos, sheet_name='Precificacao_guaruja')
    else:
        st.warning("Nenhum arquivo de precificação importado.")
        return

    # Aplicar DEPARA em ORIGEM e DESTINO
    aba_demanda['ORIGEM_CORRIGIDA'] = aplicar_depara(aba_demanda, aba_depara, 'ORIGEM')
    aba_demanda['DESTINO_CORRIGIDA'] = aplicar_depara(aba_demanda, aba_depara, 'DESTINO')

    # Exibir dados tratados
    st.markdown("### 📌 Origem/Destino com DEPARA aplicado")
    st.dataframe(aba_demanda[['ORIGEM', 'ORIGEM_CORRIGIDA', 'DESTINO', 'DESTINO_CORRIGIDA']])

    # Agrupamento por rota tratada
    rotas = aba_demanda.groupby(['ORIGEM_CORRIGIDA', 'DESTINO_CORRIGIDA']).size().reset_index(name='Demandas')
    st.markdown("### 📈 Quantidade de demandas por rota (tratada):")
    st.dataframe(rotas)

    # Merge entre rotas tratadas e tabela de precos
    rotas_precificadas = pd.merge(rotas,
                                  precos_df,
                                  how='left',
                                  left_on=['ORIGEM_CORRIGIDA', 'DESTINO_CORRIGIDA'],
                                  right_on=['ORIGEM', 'DESTINO'])

    # Lógica de sugestão e cálculo de saving
    def sugerir_modal(row):
        if pd.isna(row['CUSTO_FROTA']) or pd.isna(row['CUSTO_AGREGADO']):
            return "Indefinido"
        return "Frota Própria" if row['CUSTO_FROTA'] < row['CUSTO_AGREGADO'] else "Agregado"

    def calcular_saving(row):
        if row['SUGESTAO'] == "Frota Própria":
            return row['CUSTO_AGREGADO'] - row['CUSTO_FROTA']
        return 0

    rotas_precificadas['SUGESTAO'] = rotas_precificadas.apply(sugerir_modal, axis=1)
    rotas_precificadas['SAVING'] = rotas_precificadas.apply(calcular_saving, axis=1)

    # Resultado final
    st.markdown("### 🧠 Sugestão de Alocação com Custo")
    st.dataframe(rotas_precificadas[[
        'ORIGEM_CORRIGIDA', 'DESTINO_CORRIGIDA', 'Demandas',
        'CUSTO_FROTA', 'CUSTO_AGREGADO', 'SUGESTAO', 'SAVING'
    ]])
