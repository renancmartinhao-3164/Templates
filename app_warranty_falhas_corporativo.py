"""
App Streamlit - Classificação Corporativa de Defeitos (Warranty / Qualidade)

VERSÃO ROBUSTA

Funcionalidades:
- Upload de arquivo Excel (.xlsx)
- Classificação automática de:
    * Tipo de Defeito (padrão corporativo)
- Regra prioritária:
    * Se Labor/Peças = "Mão de obra" -> Tipo de Defeito = "N/A"
- 1 tipo de defeito por registro (ordem de prioridade)
- Processa 100% das linhas do arquivo
- Se houver texto sem regra definida, o app não generaliza:
    * exibe erro
    * mostra as linhas sem regra
    * permite baixar relatório de erros
- Compatível com Streamlit Cloud
"""

import re
import unicodedata
from io import BytesIO

import pandas as pd
import streamlit as st

# =============================
# Configuração da página
# =============================

st.set_page_config(
    page_title="Warranty – Classificação Corporativa de Defeitos",
    layout="wide"
)

# =============================
# Regras corporativas
# Ordem = PRIORIDADE
# Use padrões regex já pensando em texto normalizado
# =============================

TIPO_DEFEITO_RULES = [
    ("Ruído", [
        r"\bbarulho\b",
        r"\bruido\b",
        r"\bruidos\b",
        r"\bruido excessivo\b",
        r"\bruido anormal\b",
        r"\bruido estranho\b",
    ]),

    ("Trincado", [
        r"\btrinca\b",
        r"\btrincado\b",
        r"\btrincada\b",
        r"\btrincas\b",
    ]),

    ("Inoperante", [
        r"\binoperante\b",
        r"\bnao opera\b",
        r"\bnao funciona\b",
        r"\bsem funcionamento\b",
        r"\bparado\b",
    ]),

    ("Defeito Elétrico", [
        r"\bcurto\b",
        r"\beletrico\b",
        r"\bfalha eletrica\b",
        r"\bsensor\b",
        r"\bnao liga\b",
        r"\bsem energia\b",
        r"\bchicote\b",
        r"\bpainel\b",
    ]),

    ("Defeito de Pintura", [
        r"\bdescasc\w*\b",
        r"\bbolha\b",
        r"\bbolhas\b",
        r"\bproblema na pintura\b",
        r"\bfalha na pintura\b",
        r"\bpintura\b",
    ]),

    ("Corrosão Prematura", [
        r"\bferrugem\b",
        r"\bcorrosao\b",
        r"\boxidacao\b",
        r"\boxidado\b",
    ]),

    ("Defeito de Solda", [
        r"\bsolda\b",
        r"\btrinca na solda\b",
        r"\bsolda fraca\b",
        r"\bsolda quebrada\b",
    ]),

    ("Defeito de Montagem", [
        r"\bmontagem\b",
        r"\bmontado incorretamente\b",
        r"\bfalta de parafuso\b",
        r"\bparafuso solto\b",
        r"\btorque\b",
        r"\bmal montado\b",
    ]),

    ("Superaquecimento", [
        r"\bsuperaquec\w*\b",
        r"\btemperatura alta\b",
        r"\baquecimento excessivo\b",
        r"\besquentando\b",
    ]),

    ("Vazamento", [
        r"\bvazamento\b",
        r"\bgotejamento\b",
        r"\boleo\b",
        r"\bfluido\b",
        r"\bescorrimento\b",
    ]),

    ("Quebra Mecânica", [
        r"\bquebra\b",
        r"\bromp\w*\b",
        r"\bfratura\b",
        r"\bpartiu\b",
        r"\bquebrado\b",
        r"\bquebrada\b",
    ]),

    ("Desgaste Prematuro", [
        r"\bdesgaste\b",
        r"\bfolga\b",
        r"\bgasto\b",
        r"\bgasta\b",
        r"\bconsumo excessivo\b",
    ]),
]

# =============================
# Utilidades de normalização
# =============================

def remover_acentos(texto: str) -> str:
    """
    Remove acentos usando apenas biblioteca padrão.
    Ex.: 'Mão de obra' -> 'Mao de obra'
    """
    return "".join(
        c for c in unicodedata.normalize("NFKD", texto)
        if not unicodedata.combining(c)
    )


def normalizar_texto(valor) -> str:
    """
    Normaliza o texto para comparação:
    - trata nulos
    - converte para string
    - remove acentos
    - lowercase
    - remove espaços extras
    """
    if pd.isna(valor):
        return ""

    texto = str(valor).strip()
    texto = remover_acentos(texto)
    texto = texto.lower()
    texto = re.sub(r"\s+", " ", texto)

    return texto


# =============================
# Compilação das regras
# =============================

def compilar_regras(regras):
    regras_compiladas = []
    for tipo_defeito, padroes in regras:
        regex_compilados = [re.compile(padrao, flags=re.IGNORECASE) for padrao in padroes]
        regras_compiladas.append((tipo_defeito, regex_compilados))
    return regras_compiladas


TIPO_DEFEITO_RULES_COMPILED = compilar_regras(TIPO_DEFEITO_RULES)

# =============================
# Funções principais
# =============================

def classificar_tipo_defeito(texto):
    """
    Classifica o tipo de defeito com base em regras explícitas.
    Não usa fallback genérico.
    Se não encontrar regra, gera erro.
    """
    texto_norm = normalizar_texto(texto)

    if texto_norm == "":
        raise ValueError("Texto vazio em 'Detalhes Adicionais de Falha'")

    for tipo_defeito, padroes in TIPO_DEFEITO_RULES_COMPILED:
        for padrao in padroes:
            if padrao.search(texto_norm):
                return tipo_defeito

    raise ValueError(f"Sem regra para o texto: {texto}")


def validar_colunas(df, colunas_obrigatorias):
    colunas_faltantes = [c for c in colunas_obrigatorias if c not in df.columns]
    return colunas_faltantes


def processar_dataframe(df):
    """
    Processa todas as linhas do dataframe.
    Regra prioritária:
    - Labor/Peças = Mão de obra -> Tipo de Defeito = N/A
    Caso contrário:
    - classifica por 'Detalhes Adicionais de Falha'
    Se qualquer linha não tiver regra, retorna erro estruturado.
    """
    df = df.copy()

    if "Tipo de Defeito" in df.columns:
        df = df.drop(columns=["Tipo de Defeito"])

    erros = []

    def aplicar_classificacao(row):
        labor_pecas_norm = normalizar_texto(row["Labor/Peças"])
        detalhes = row["Detalhes Adicionais de Falha"]

        # Regra prioritária corporativa
        if labor_pecas_norm == "mao de obra":
            return "N/A"

        try:
            return classificar_tipo_defeito(detalhes)
        except ValueError as e:
            erros.append({
                "Linha Excel": row.name + 2,  # considera cabeçalho + índice base 0
                "Labor/Peças": row["Labor/Peças"],
                "Detalhes Adicionais de Falha": detalhes,
                "Detalhes Normalizados": normalizar_texto(detalhes),
                "Erro": str(e),
            })
            return None

    df["Tipo de Defeito"] = df.apply(aplicar_classificacao, axis=1)

    if erros:
        df_erros = pd.DataFrame(erros)
        raise RuntimeError(df_erros)

    return df


def gerar_excel_classificado(df):
    """
    Gera arquivo Excel classificado.
    """
    buffer = BytesIO()
    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Classificado")
    buffer.seek(0)
    return buffer


def gerar_excel_erros(df_erros):
    """
    Gera arquivo Excel com as linhas sem regra de classificação.
    """
    buffer = BytesIO()
    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        df_erros.to_excel(writer, index=False, sheet_name="Erros de Classificacao")
    buffer.seek(0)
    return buffer


def gerar_resumo_classificacao(df):
    """
    Retorna resumo de contagem por Tipo de Defeito.
    """
    resumo = (
        df["Tipo de Defeito"]
        .value_counts(dropna=False)
        .rename_axis("Tipo de Defeito")
        .reset_index(name="Quantidade")
    )
    return resumo


# =============================
# Interface Streamlit
# =============================

st.title("Classificação Corporativa de Defeitos – Warranty / Qualidade")
st.markdown(
    """
Classificação automática de **Tipo de Defeito** a partir da coluna
**Detalhes Adicionais de Falha**.

### Regras importantes
- Se **Labor/Peças = Mão de obra** → **Tipo de Defeito = N/A**
- Não há generalização
- Se uma linha não tiver regra explícita, o app mostra erro e lista as linhas
"""
)

uploaded_file = st.file_uploader(
    "Upload do arquivo Excel (.xlsx)",
    type=["xlsx"]
)

if uploaded_file:
    try:
        df_input = pd.read_excel(uploaded_file, engine="openpyxl")
    except Exception as e:
        st.error(f"Erro ao ler o arquivo Excel: {e}")
        st.stop()

    colunas_obrigatorias = ["Detalhes Adicionais de Falha", "Labor/Peças"]
    colunas_faltantes = validar_colunas(df_input, colunas_obrigatorias)

    if colunas_faltantes:
        st.error(
            "As seguintes colunas obrigatórias não foram encontradas: "
            + ", ".join(colunas_faltantes)
        )
        st.stop()

    st.success(f"Arquivo carregado com sucesso ({len(df_input):,} linhas).")

    st.subheader("Pré-visualização – Dados de entrada")
    st.caption("A visualização abaixo mostra apenas as primeiras linhas. O processamento considera 100% do arquivo.")
    st.dataframe(df_input.head(20), use_container_width=True)

    try:
        df_output = processar_dataframe(df_input)

        st.subheader("Resultado – Classificação por Tipo de Defeito")
        st.dataframe(df_output.head(20), use_container_width=True)

        st.subheader("Resumo da classificação")
        resumo = gerar_resumo_classificacao(df_output)
        st.dataframe(resumo, use_container_width=True)

        excel_buffer = gerar_excel_classificado(df_output)

        st.download_button(
            label="Download do Excel classificado",
            data=excel_buffer,
            file_name="output_tipo_defeito_warranty.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

    except RuntimeError as erro_classificacao:
        st.error("Existem linhas sem regra de classificação definida.")

        df_erros = erro_classificacao.args[0]

        st.subheader("Linhas que precisam de nova regra")
        st.dataframe(df_erros, use_container_width=True)

        st.warning(
            "Adicione novas regras em TIPO_DEFEITO_RULES para essas descrições antes de exportar o arquivo classificado."
        )

        excel_erros = gerar_excel_erros(df_erros)

        st.download_button(
            label="Download do relatório de erros",
            data=excel_erros,
            file_name="erros_classificacao_tipo_defeito.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
