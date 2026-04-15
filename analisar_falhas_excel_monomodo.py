
"""
Script: analisar_falhas_excel_monomodo.py
Objetivo:
- Ler arquivo Excel padrão: inputdatawarranty.xlsx
- Classificar APENAS UM modo de falha (regra de prioridade)
- Aplicar hierarquia: Sistema > SubSistema > Componente

Uso típico: Warranty, KPIs de Qualidade, Pareto clássico
"""

import pandas as pd
import re

# =============================
# Regras de classificação
# Ordem define PRIORIDADE
# =============================

MODO_FALHA_RULES = [
    ("Falha Elétrica", ["curto", "elétrico", "sem energia", "sensor"]),
    ("Superaquecimento", ["superaquec", "aquec", "temperatura alta"]),
    ("Vazamento", ["vazamento", "gotejamento", "óleo", "fluido"]),
    ("Quebra Mecânica", ["quebra", "romp", "fratura", "partiu"]),
    ("Desgaste", ["desgaste", "folga"])
]

SISTEMA_RULES = {
    "Hidráulico": {
        "Bombas": {
            "Bomba Hidráulica": ["bomba hidráulica", "bomba"]
        },
        "Atuadores": {
            "Cilindro": ["cilindro", "atuador"]
        },
        "Linhas": {
            "Mangueira": ["mangueira", "linha hidráulica"]
        }
    },
    "Elétrico": {
        "Potência": {
            "Motor Elétrico": ["motor elétrico", "motor"]
        },
        "Comando": {
            "Sensor": ["sensor", "encoder"],
            "Painel": ["painel", "clp"]
        }
    },
    "Mecânico": {
        "Transmissão": {
            "Rolamento": ["rolamento"],
            "Engrenagem": ["engrenagem"]
        }
    }
}

# =============================
# Funções auxiliares
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

# =============================
# Execução principal
# =============================

def processar_excel(input_file="inputdatawarranty.xlsx",
                     output_file="outputdatawarranty.xlsx"):

    df = pd.read_excel(input_file, engine='openpyxl')

    df['Modo de Falha'] = df['Detalhes Adicionais de Falha'].apply(
        classificar_modo_falha
    )

    sistema_cols = df['Detalhes Adicionais de Falha'].apply(
        lambda x: pd.Series(
            classificar_sistema(x),
            index=['Sistema', 'SubSistema', 'Componente']
        )
    )

    df = pd.concat([df, sistema_cols], axis=1)

    df.to_excel(output_file, index=False, engine='openpyxl')
    print(f"Arquivo processado com sucesso: {output_file}")


if __name__ == "__main__":
    processar_excel()
