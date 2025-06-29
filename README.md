# Simulador de Custos - Guarujá

Este projeto Streamlit é um simulador de custos de transporte com foco na operação do terminal de Guarujá.

## 🔧 Funcionalidades

- Simulação de custo por rota entre Frota Própria e Agregado
- Sugestão da modalidade com menor custo
- Aba dinâmica de **Sugestão de Alocação**
- Cálculo de Saving por rota
- Interface 100% interativa via upload de planilha base

## 📁 Como utilizar

1. Faça o upload da planilha `base_importacao_guaruja.xlsx`
2. Navegue entre as abas:
   - 🔍 Simulador por Rota
   - 📋 Demandas do Dia
   - 🚚 Sugestão de Alocação
3. Visualize os resultados diretamente no navegador

## 🚀 Execução local

```bash
pip install -r requirements.txt
streamlit run simulador_guaruja_formulario.py
```

## 📦 Deploy

Este projeto pode ser publicado facilmente no [Streamlit Cloud](https://streamlit.io/cloud).
