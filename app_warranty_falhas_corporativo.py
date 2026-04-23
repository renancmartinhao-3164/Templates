"""
App Streamlit - Classificação Corporativa de Defeitos (Warranty / Qualidade)

Funcionalidades:
- Upload de arquivo Excel (.xlsx)
- Classificação automática de:
    * Tipo de Defeito (padrão corporativo)
- 1 tipo de defeito por registro (regra de prioridade)
- Download do Excel processado

Compatível com Streamlit Cloud
"""

import streamlit as st
import pandas as pd
from io import BytesIO

# =============================
# Configuração da página
# =============================

st.set_page_config(
    page_title="Warranty – Classificação Corporativa de Defeitos",
    layout="wide"
)

# =============================
# Padrão corporativo – Tipo de Defeito
# Ordem = PRIORIDADE
# =============================

TIPO_DEFEITO_RULES = [
    ("Defeito Elétrico", [
        "curto", "elétrico", "sensor", "não liga", "falha elétrica"
    ]),

    ("Defeito de Pintura", [
        "descasc", "descascando", "bolha", "bolhas",
        "problema na pintura", "falha na pintura", "pintura"
    ]),

    ("Corrosão Prematura", [
        "ferrugem", "corrosão", "oxidação"
    ]),

    ("Defeito de Solda", [
        "solda", "trinca na solda", "solda fraca"
    ]),

    ("Defeito de Montagem", [
        "montagem", "montado incorretamente",
        "falta de parafuso", "parafuso solto", "torque"
    ]),

    ("Superaquecimento", [
        "superaquec", "temperatura alta", "aquecimento excessivo"
    ]),

    ("Vazamento", [
        "vazamento", "gotejamento", "óleo", "fluido"
    ]),

    ("Quebra Mecânica", [
        "quebra", "romp", "fratura", "partiu"
    ]),

    ("Desgaste Prematuro", [
        "desgaste", "folga", "gasto"
    ])
]

# =============================
# Funções de classificação
# =============================

def classificar_tipo_defeito(texto):
    if pd.isna(texto):
        return "Não identificado"

    texto = texto.lower()

    for tipo, palavras in TIPO_DEFEITO_RULES:
        for p in palavras:
            if p in texto:
                return tipo

    return "Não identificado"


def processar_dataframe(df):
    df = df.copy()

    # Remove coluna se já existir
    coluna_padrao = ["Tipo de Defeito"]
    df = df.drop(columns=[c for c in coluna_padrao if c in df.columns])

    df["Tipo de Defeito"] = df["Detalhes Adicionais de Falha"].apply(
        classificar_tipo_defeito
    )

    return df


def gerar_excel_download(df):
    buffer = BytesIO()
    with pd.ExcelWriter(buffer) as writer:
        df.to_excel(writer, index=False)
    buffer.seek(0)
    return buffer

# =============================
# Interface Streamlit
# =============================

st.title("Classificação Corporativa de Defeitos – Warranty / Qualidade")
st.markdown(
    "Classificação automática de **Tipo de Defeito** "
    "a partir de texto livre (padrão corporativo)."
)

uploaded_file = st.file_uploader(
    "Upload do arquivo Excel (.xlsx)",
    type=["xlsx"]
)

if uploaded_file:
    try:
        df_input = pd.read_excel(uploaded_file)
    except Exception as e:
        st.error(f"Erro ao ler o arquivo Excel: {e}")
        st.stop()

    if "Detalhes Adicionais de Falha" not in df_input.columns:
        st.error(
            "A coluna obrigatória **'Detalhes Adicionais de Falha'** não foi encontrada."
        )
        st.stop()

    st.success("Arquivo carregado com sucesso.")

    st.subheader("Pré-visualização – Dados de entrada")
    st.dataframe(df_input.head(20), use_container_width=True)

    df_output = processar_dataframe(df_input)

    st.subheader("Resultado – Classificação por Tipo de Defeito")
    st.dataframe(df_output.head(20), use_container_width=True)

    excel_buffer = gerar_excel_download(df_output)

    st.download_button(
        label="Download do Excel classificado",
        data=excel_buffer,
        file_name="output_tipo_defeito_warranty.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
