"""Datalyse · Gestão Executiva de Academia — app Streamlit.

Exibe o painel `dashboard_academia.html` (arquivo único, com os dados da planilha
embutidos) em tela cheia. Todo o cálculo acontece no próprio painel, em JavaScript;
o botão "Carregar planilha" dentro dele aceita uma versão atualizada do modelo .xlsx.
"""
from pathlib import Path

import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(
    page_title="Gestão Executiva · Academia | Datalyse",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# Remove o cromo do Streamlit e faz o painel ocupar a janela inteira
st.markdown(
    """
    <style>
      #MainMenu, header[data-testid="stHeader"], footer, [data-testid="stToolbar"],
      [data-testid="stDecoration"], [data-testid="stStatusWidget"] { display: none !important; }
      .stApp, .main, [data-testid="stAppViewContainer"] { background: #0B0B0C !important; }
      .block-container, [data-testid="stMainBlockContainer"] { padding: 0 !important; max-width: 100% !important; }
      [data-testid="stVerticalBlock"] { gap: 0 !important; }
      iframe { display: block; width: 100% !important; height: 100vh !important; border: 0; }
    </style>
    """,
    unsafe_allow_html=True,
)

html = (Path(__file__).parent / "dashboard_academia.html").read_text(encoding="utf-8")
components.html(html, height=900, scrolling=True)
