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

session = st.session_state
session.setdefault("resultados", [])
session.setdefault("selected_cap", None)
session.setdefault("modo_anterior", None)

# ======================================================
# TÍTULO SIN ENLACE
# ======================================================

st.markdown(""" 
    <div style='font-size: 42px; font-weight: 700; margin-bottom: 0;'> 
        CapCollection 
    </div> 
""", unsafe_allow_html=True) 

st.caption("Colección de chapas de Maria A.G.")

# ======================================================
# TEMA CLARO/OSCURO (debajo del título)
# ======================================================

tema_claro = st.toggle("Tema claro", value=False)

THEME_LIGHT = """
<style>
:root {
    --bg-main: #ffffff;
    --bg-card: #f3f3f3;
    --text-main: #222222;
    --text-muted: #555555;
}
</style>
"""

THEME_DARK = """
<style>
:root {
    --bg-main: #1e1e1e;
    --bg-card: #2a2a2a;
    --text-main: #eeeeee;
    --text-muted: #bbbbbb;
}
</style>
"""

st.markdown(THEME_LIGHT if tema_claro else THEME_DARK, unsafe_allow_html=True)

# ======================================================
# OPCIONES DE NAVEGACIÓN (debajo del tema)
# ======================================================

modo = st.radio(
    "Selecciona un modo",
    ["Buscar por marca", "Buscar por imagen", "Mostrar todas"],
    horizontal=True
)

# Reset automático al cambiar de modo
if modo != session.modo_anterior:
    session.resultados = []
    session.selected_cap = None

session.modo_anterior = modo



# ======================================================
# FUNCIONES AUXILIARES
# ======================================================

def normalizar_imagen(path_str: str) -> Path:
    ruta = Path(str(path_str).replace("\\", "/"))
    return ruta if ruta.is_absolute() else PROJECT_ROOT / ruta


def tarjeta_chapa(r):
    id_, marca, tipo, imagen, *_ = r
    img_file = normalizar_imagen(imagen)

    st.markdown("<div class='cap-card'>", unsafe_allow_html=True)

    if img_file.exists():
        st.image(str(img_file), width=150)
    else:
        st.markdown("<div style='color: var(--text-muted); font-size: 13px;'>Sin imagen</div>", unsafe_allow_html=True)

    st.markdown(f"<div class='cap-title'>{marca}</div>", unsafe_allow_html=True)
    st.markdown(f"<div class='cap-subtitle'>{tipo}</div>", unsafe_allow_html=True)

    st.markdown("</div>", unsafe_allow_html=True)


def mostrar_galeria(resultados):
    cols = st.columns(3)
    for i, r in enumerate(resultados):
        with cols[i % 3]:
            tarjeta_chapa(r)


def mostrar_lista(resultados):
    cols = st.columns(3)
    for i, r in enumerate(resultados):
        with cols[i % 3]:
            tarjeta_chapa(r)


def mostrar_ficha(chapa):
    if not chapa:
        return

    id_, marca, tipo, imagen, *_ = chapa
    img_file = normalizar_imagen(imagen)

    st.markdown("---")
    st.markdown("### Ficha de la chapa seleccionada")

    col1, col2 = st.columns([1, 2])

    with col1:
        if img_file.exists():
            st.image(str(img_file), width=250)
        else:
            st.info("Sin imagen")

    with col2:
        st.markdown(f"**Marca:** {marca}")
        st.markdown(f"**Tipo:** {tipo}")
        st.markdown(f"**ID:** `{id_}`")

    if st.button("Cerrar ficha"):
        session.selected_cap = None


# ======================================================
# CONTENIDO PRINCIPAL
# ======================================================

# ------------------ Buscar por marca ------------------
if modo == "Buscar por marca":
    st.markdown(
        "<div style='font-size:26px; font-weight:600; margin-top:20px;'>Buscar por marca</div>",
        unsafe_allow_html=True
    )   

    marca = st.text_input("Introduce una marca")

    if marca:
        session.resultados = fn.search_by_brand(marca)
        st.success(f"{len(session.resultados)} resultados encontrados")

    mostrar_lista(session.resultados)

# ------------------ Buscar por imagen ------------------
elif modo == "Buscar por imagen":
    st.markdown(
        "<div style='font-size:26px; font-weight:600; margin-top:20px;'>Buscar por imagen</div>",
        unsafe_allow_html=True
    )   

    uploaded = st.file_uploader("Sube una imagen", type=["png", "jpg", "jpeg"])

    if uploaded:
        session.resultados = fn.search_by_image_simple(uploaded, top_k=5)
        st.success(f"{len(session.resultados)} coincidencias encontradas")

    mostrar_lista(session.resultados)

# ------------------ Mostrar todas ------------------
else:
    st.markdown(
        "<div style='font-size:26px; font-weight:600; margin-top:20px;'>Todas las chapas</div>",
        unsafe_allow_html=True
    )   

    session.resultados = fn.get_all_caps()
    st.success(f"{len(session.resultados)} chapas en la colección")

    mostrar_galeria(session.resultados)

# ------------------ Ficha ------------------
if session.selected_cap:
    mostrar_ficha(session.selected_cap)
