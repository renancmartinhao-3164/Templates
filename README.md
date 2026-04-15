# Warranty Failure Analyzer

App Streamlit para classificação automática de falhas a partir de texto livre.

## Funcionalidades
- Upload de arquivo Excel (.xlsx)
- Classificação automática de:
  - Modo de Falha (1 por prioridade)
  - Sistema
  - SubSistema
  - Componente
- Download do Excel processado
- Compatível com Streamlit Cloud

## Coluna obrigatória
O arquivo deve conter a coluna:
- Detalhes Adicionais de Falha

## Como rodar localmente
```bash
pip install -r requirements.txt
streamlit run app_analisar_falhas.py
