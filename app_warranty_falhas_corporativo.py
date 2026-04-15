
"""
App Streamlit - Classificação Corporativa de Falhas (Warranty / Qualidade)

Funcionalidades:
- Upload de arquivo Excel (.xlsx)
- Classificação automática de:
    * Modo de Falha (padrão corporativo)
    * Sistema (nível macro)
- 1 modo de falha por registro (regra de prioridade)
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
    page_title="Warranty – Classificação Corporativa de Falhas",
    layout="wide"
)

# =============================
# Padrão corporativo – Modo de Falha
# Ordem = PRIORIDADE
# =============================

MODO_FALHA_RULES = [
    ("Falha Elétrica", [
        "curto", "elétrico", "sensor", "não liga", "falha elétrica"
    ]),

    ("Falha de Pintura", [
        "descasc", "descascando", "bolha", "bolhas",
        "problema na pintura", "falha na pintura", "pintura"
    ]),

    ("Corrosão Prematura", [
        "ferrugem", "corrosão", "oxidação"
    ]),

    ("Defeito de Solda", [
        "solda", "trinca na solda", "solda fraca"
    ]),

    ("Falha de Montagem", [
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
# Sistema – nível corporativo
# =============================

SISTEMA_RULES = {
    "Elétrico": [
        "sensor", "motor elétrico", "elétrico", "painel", "chicote"
    ],
    "Hidráulico": [
        "bomba", "válvula", "mangueira", "óleo", "hidrául"
    ],
    "Estrutura": [
        "barra", "barras", "chassi", "estrutura", "suporte"
    ],
    "Mecânico": [
        "rolamento", "eixo", "engrenagem", "transmissão"
    ]
}

# =============================
# Funções de classificação
# =============================

def classificar_modo_falha(texto):
    if pd.isna(texto):
        return "Não identificado"

    texto = texto.lower()

    for modo, palavras in MODO_FALHA_RULES:
        for p in palavras:
            if p in texto:
                return modo

    return "Não identificado"


def classificar_sistema(texto):
    if pd.isna(texto):
        return "Não identificado"

    texto = texto.lower()

    for sistema, palavras in SISTEMA_RULES.items():
        for p in palavras:
            if p in texto:
                return sistema

    return "Não identificado"


def processar_dataframe(df):
    df = df.copy()

    # Remove colunas se já existirem (evita erro no Streamlit / Arrow)
    colunas_padrao = ["Modo de Falha", "Sistema"]
    df = df.drop(columns=[c for c in colunas_padrao if c in df.columns])

    df["Modo de Falha"] = df["Detalhes Adicionais de Falha"].apply(
        classificar_modo_falha
    )

    df["Sistema"] = df["Detalhes Adicionais de Falha"].apply(
        classificar_sistema
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

st.title("Classificação Corporativa de Falhas – Warranty / Qualidade")
st.markdown(
    "Classificação automática de **Modo de Falha** e **Sistema** "
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

    st.subheader("Resultado – Classificação Corporativa")
    st.dataframe(df_output.head(20), use_container_width=True)

    excel_buffer = gerar_excel_download(df_output)

    st.download_button(
        label="Download do Excel classificado",
        data=excel_buffer,
        file_name="outputdatawarranty.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
