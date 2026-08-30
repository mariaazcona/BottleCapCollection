"""
app.py
------
Interfaz web en Streamlit para CapCollection.

Responsabilidades:
- Navegación principal
- Búsqueda por marca
- Búsqueda por imagen
- Visualización en lista y galería
- Ficha detallada de una chapa
"""

import streamlit as st
from pathlib import Path

import modules.services as fn
from modules.ui_theme import load_theme

PROJECT_ROOT = Path(__file__).resolve().parent

st.set_page_config(
    page_title="CapCollection",
    layout="wide"
)

load_theme()


# ======================================================
# TÍTULO PRINCIPAL
# ======================================================

st.set_page_config(page_title="Maria's Collection", layout="wide")

st.markdown("<h1 class='main-title'>CROWN CAP COLLECTION</h1>", unsafe_allow_html=True)
st.markdown("<p class='subtext'>Base funcional lista.</p>", unsafe_allow_html=True)


# ======================================================
# OPCIONES DE NAVEGACIÓN
# ======================================================
session = st.session_state
session.setdefault("resultados", [])
session.setdefault("selected_cap", None)
session.setdefault("modo_anterior", None)

modo = st.radio(
    " ",
    ["Buscar por marca", "Buscar por imagen", "Mostrar todas"],
    horizontal=True
)

# Reset automático al cambiar de modo
if modo != session.modo_anterior:
    session.resultados = []
    session.selected_cap = None

session.modo_anterior = modo



# ======================================================
#auxiliars

def show_results(resultados):
    for item in resultados:
        st.markdown("<div class='cap-card'>", unsafe_allow_html=True)

        # Imagen con Streamlit (mejor que HTML)
        st.image(item["imagen"], use_column_width=True)

        # Título con HTML
        st.markdown(
            f"<div class='cap-title'>{item['marca']}</div>",
            unsafe_allow_html=True
        )

        st.markdown("</div>", unsafe_allow_html=True)









# ======================================================
# CONTENIDO PRINCIPAL
# ======================================================

# ------------------ Buscar por marca ------------------
if modo == "Buscar por marca":
    st.markdown("<h2 class='section-title'>Buscar por marca</h2>", unsafe_allow_html=True)
    marca = st.text_input(" ", placeholder="Escribe una marca...")

    if marca:
        session.resultados = fn.search_by_brand(marca)
    
        if not session.resultados:
            st.info("No se encontraron resultados.")
        else: 
            st.success(f"{len(session.resultados)} resultados encontrados")
            
    show_results(session.resultados)
           

# ------------------ Buscar por imagen ------------------
elif modo == "Buscar por imagen":
    st.markdown("<h2 class='section-title'>Toda la colección</h2>", unsafe_allow_html=True)

    uploaded = st.file_uploader("Sube una imagen", type=["png", "jpg", "jpeg"])

    if uploaded:
        resultados = fn.search_by_image_simple(uploaded, top_k=5)
        st.success(f"{len(resultados)} coincidencias encontradas")

        show_results(resultados)


# ------------------ Mostrar todas ------------------
else:
    st.markdown("<h2 class='section-title'>Toda la colección</h2>", unsafe_allow_html=True)
    resultados = fn.get_all_caps()
    st.success(f"{len(resultados)} resultados encontrados")     
    show_results(resultados)

