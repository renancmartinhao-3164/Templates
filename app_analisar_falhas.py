
"""
Streamlit App: app_analisar_falhas.py
Objetivo:
- Upload de arquivo Excel (.xlsx)
- Classificar 1 modo de falha (prioridade)
- Identificar Sistema > SubSistema > Componente
- Permitir download do Excel processado

Compatível com Streamlit Cloud
"""

import streamlit as st
import pandas as pd
import re
from io import BytesIO

st.set_page_config(page_title="Warranty Failure Analyzer", layout="wide")

# =============================
# Regras de classificação
# =============================

MODO_FALHA_RULES = [
    ("Falha Elétrica", ["curto", "elétrico", "sem energia", "sensor"]),
    ("Superaquecimento", ["superaquec", "aquec", "temperatura alta"]),
    ("Vazamento", ["vazamento", "gotejamento", "óleo", "fluido"]),
    ("Quebra Mecânica", ["quebra", "romp", "fratura", "partiu"]),
    ("Desgaste", ["desgaste", "folga"]),
]

SISTEMA_RULES = {
    "Hidráulico": {
        "Bombas": {"Bomba Hidráulica": ["bomba hidráulica", "bomba"]},
        "Atuadores": {"Cilindro": ["cilindro", "atuador"]},
        "Linhas": {"Mangueira": ["mangueira", "linha hidráulica"]},
    },
    "Elétrico": {
        "Potência": {"Motor Elétrico": ["motor elétrico", "motor"]},
        "Comando": {
            "Sensor": ["sensor", "encoder"],
            "Painel": ["painel", "clp"],
        },
    },
    "Mecânico": {
        "Transmissão": {
            "Rolamento": ["rolamento"],
            "Engrenagem": ["engrenagem"],
        }
    },
}

# =============================
# Funções
# =============================

def classificar_modo_falha(texto):
    if pd.isna(texto):
        return "Não identificado"
    texto = texto.lower()
    for modo, palavras in MODO_FALHA_RULES:
        for p in palavras:
            if re.search(rf"\b{p}", texto):
                return modo
    return "Não identificado"


def classificar_sistema(texto):
    if pd.isna(texto):
        return "Não identificado", "Não identificado", "Não identificado"
    texto = texto.lower()
    for sistema, subsistemas in SISTEMA_RULES.items():
        for subsistema, componentes in subsistemas.items():
            for componente, palavras in componentes.items():
                for p in palavras:
                    if re.search(rf"\b{p}", texto):
                        return sistema, subsistema, componente
    return "Não identificado", "Não identificado", "Não identificado"


def processar_dataframe(df):
    df = df.copy()
    df['Modo de Falha'] = df['Detalhes Adicionais de Falha'].apply(classificar_modo_falha)

    sistema_cols = df['Detalhes Adicionais de Falha'].apply(
        lambda x: pd.Series(classificar_sistema(x), index=['Sistema', 'SubSistema', 'Componente'])
    )
    return pd.concat([df, sistema_cols], axis=1)


def gerar_excel_download(df):
    buffer = BytesIO()
    with pd.ExcelWriter(buffer) as writer:
        df.to_excel(writer, index=False)
    buffer.seek(0)
    return buffer

# =============================
# Interface Streamlit
# =============================

st.title("Warranty / Failure Mode Analyzer")
st.markdown("Classificação automática de **Modo de Falha** e **Hierarquia de Sistemas**")

uploaded_file = st.file_uploader(
    "Upload do arquivo Excel (inputdatawarranty.xlsx)", type="xlsx"
)

if uploaded_file:
    try:
        df_input = pd.read_excel(uploaded_file)
    except Exception as e:
        st.error(f"Erro ao ler o arquivo: {e}")
        st.stop()

    if 'Detalhes Adicionais de Falha' not in df_input.columns:
        st.error("A coluna 'Detalhes Adicionais de Falha' não foi encontrada.")
        st.stop()

    st.success("Arquivo carregado com sucesso!")

    st.subheader("Pré-visualização dos dados originais")
    st.dataframe(df_input.head(20), use_container_width=True)

    df_output = processar_dataframe(df_input)

    st.subheader("Resultado após classificação")
    st.dataframe(df_output.head(20), use_container_width=True)

    excel_buffer = gerar_excel_download(df_output)

    st.download_button(
        label="Download do Excel processado",
        data=excel_buffer,
        file_name="outputdatawarranty.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )
