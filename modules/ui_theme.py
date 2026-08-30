"""
ui_theme.py
------------
Módulo encargado de cargar el archivo CSS personalizado para aplicar
estilos a la interfaz de Streamlit.

Responsabilidades:
- Localizar el archivo styles.css
- Inyectar el CSS en la aplicación
"""

from pathlib import Path
import streamlit as st


# ======================================================
# 1. CONFIGURACIÓN
# ======================================================

PROJECT_ROOT = Path(__file__).resolve().parent.parent
CSS_PATH = PROJECT_ROOT / "assets" / "styles.css"


# ======================================================
# 2. FUNCIÓN PRINCIPAL
# ======================================================

def load_theme() -> None:
    """
    Carga el archivo CSS personalizado e inyecta su contenido en Streamlit.

    Si el archivo no existe, no genera error; simplemente no aplica estilos.
    Los colores base del tema se configuran en .streamlit/config.toml.
    """
    if not CSS_PATH.exists():
        return

    try:
        css = CSS_PATH.read_text(encoding="utf-8")
        st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)
    except OSError as e:
        st.warning(f"No se pudo cargar el tema CSS: {e}")
