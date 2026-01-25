# app.py
# Interfaz web en Streamlit para CapCollection

import streamlit as st
import pathlib
from pathlib import Path

import modules.services as fn
from modules.ui_theme import load_theme

BASE_DIR = pathlib.Path(__file__).resolve().parent

# --------------------------------------------------
# Configuración básica
# --------------------------------------------------
st.set_page_config(page_title="CapCollection", layout="wide")
load_theme()

st.title("Maria's Collection")
st.caption("La colección de chapas de botella de Maria A.G.")

# --------------------------------------------------
# Estado inicial
# --------------------------------------------------
if "resultados" not in st.session_state:
    st.session_state.resultados = []
if "modo_anterior" not in st.session_state:
    st.session_state.modo_anterior = None
if "selected_cap" not in st.session_state:
    st.session_state.selected_cap = None

# --------------------------------------------------
# Toggle de tema (claro / oscuro)
# --------------------------------------------------
col_tema, _ = st.columns([1, 5])
with col_tema:
    tema_claro = st.toggle("Tema claro", value=False)

if tema_claro:
    st.markdown(
        """
        <style>
        :root {
            --bg-main: #ffffff !important;
            --bg-card: #f3f3f3 !important;
            --text-main: #222222 !important;
            --text-muted: #555555 !important;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )
else:
    st.markdown(
        """
        <style>
        :root {
            --bg-main: #1e1e1e !important;
            --bg-card: #2a2a2a !important;
            --text-main: #eeeeee !important;
            --text-muted: #bbbbbb !important;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

# --------------------------------------------------
# Navegación principal (arriba, horizontal)
# --------------------------------------------------
st.markdown("### Navegación")
modo = st.radio(
    "",
    ["Buscar por marca", "Buscar por imagen", "Mostrar todas"],
    horizontal=True,
    label_visibility="collapsed",
)

# Reset automático de resultados y selección al cambiar modo
if modo != st.session_state.modo_anterior:
    st.session_state.resultados = []
    st.session_state.selected_cap = None
st.session_state.modo_anterior = modo

# --------------------------------------------------
# Funciones auxiliares
# --------------------------------------------------
def normalizar_imagen(imagen):
    ruta = str(imagen).replace("\\", "/")
    img_file = Path(ruta)
    if not img_file.is_absolute():
        img_file = BASE_DIR / img_file
    return img_file


def mostrar_resultados_lista(resultados):
    """Lista vertical de resultados (para buscar por marca / imagen)."""
    if not resultados:
        st.info("No se han encontrado resultados.")
        return

    for r in resultados:
        id_, marca, tipo, imagen, *_ = r
        img_file = normalizar_imagen(imagen)

        st.markdown("<div class='cap-card cap-card-list'>", unsafe_allow_html=True)
        col1, col2 = st.columns([1.2, 3.8])

        with col1:
            if img_file.exists():
                st.image(str(img_file), use_column_width=True)
            else:
                st.info("Sin imagen")

        with col2:
            st.markdown(
                f"<div class='cap-title'>Marca: <strong>{marca}</strong></div>",
                unsafe_allow_html=True,
            )
            st.markdown(
                f"<div class='cap-subtitle'>Tipo: {tipo}</div>",
                unsafe_allow_html=True,
            )
            st.markdown(
                f"<div class='cap-meta'>ID: {id_}</div>",
                unsafe_allow_html=True,
            )
            if st.button("Ver ficha", key=f"ver_{id_}"):
                st.session_state.selected_cap = r
        st.markdown("</div>", unsafe_allow_html=True)


def mostrar_galeria(resultados):
    """Cuadrícula fija (mostrar todas)."""
    if not resultados:
        st.info("No hay chapas en la colección.")
        return

    cols = st.columns(4)
    i = 0

    for r in resultados:
        id_, marca, tipo, imagen, *_ = r
        img_file = normalizar_imagen(imagen)

        with cols[i % 4]:
            st.markdown("<div class='cap-card cap-card-grid'>", unsafe_allow_html=True)
            if img_file.exists():
                st.image(str(img_file), use_column_width=True)
            else:
                st.info("Sin imagen")

            st.markdown(
                f"<div class='cap-title cap-title-center'>{marca}</div>",
                unsafe_allow_html=True,
            )
            st.markdown(
                f"<div class='cap-subtitle cap-subtitle-center'>{tipo}</div>",
                unsafe_allow_html=True,
            )
            st.markdown(
                f"<div class='cap-meta cap-meta-center'>ID: {id_}</div>",
                unsafe_allow_html=True,
            )
            if st.button("Ver ficha", key=f"ver_grid_{id_}"):
                st.session_state.selected_cap = r
            st.markdown("</div>", unsafe_allow_html=True)

        i += 1


def mostrar_ficha(chapa):
    """Ficha detallada de una chapa."""
    if not chapa:
        return

    id_, marca, tipo, imagen, *_ = chapa
    img_file = normalizar_imagen(imagen)

    st.markdown("---")
    st.markdown("### Ficha de la chapa seleccionada")

    col1, col2 = st.columns([1.2, 1.8])

    with col1:
        if img_file.exists():
            st.image(str(img_file), use_column_width=True)
        else:
            st.info("Sin imagen")

    with col2:
        st.markdown(f"**Marca:** {marca}")
        st.markdown(f"**Tipo:** {tipo}")
        st.markdown(f"**ID:** `{id_}`")

    if st.button("Cerrar ficha"):
        st.session_state.selected_cap = None


# --------------------------------------------------
# MODO: Buscar por marca
# --------------------------------------------------
if modo == "Buscar por marca":
    st.subheader("Buscar por marca")

    marca = st.text_input(
        "Marca",
        placeholder="p. ej. Coca-Cola, Heineken...",
        label_visibility="visible",
    )

    if marca:
        resultados = fn.buscar_por_marca(marca)
        st.session_state.resultados = resultados

        if resultados:
            st.success(f"{len(resultados)} resultados encontrados")

        mostrar_resultados_lista(resultados)

# --------------------------------------------------
# MODO: Buscar por imagen
# --------------------------------------------------
elif modo == "Buscar por imagen":
    st.subheader("Buscar por imagen")

    uploaded_file = st.file_uploader(
        "Sube una imagen",
        type=["png", "jpg", "jpeg"],
    )

    if uploaded_file:
        resultados = fn.buscar_por_imagen_simple(uploaded_file, top_k=5)
        st.session_state.resultados = resultados

        if resultados:
            st.success(f"{len(resultados)} coincidencias encontradas")

        mostrar_resultados_lista(resultados)

# --------------------------------------------------
# MODO: Mostrar todas
# --------------------------------------------------
else:
    st.subheader("Todas las chapas")

    resultados = fn.obtener_todas_chapas()
    st.session_state.resultados = resultados

    if resultados:
        st.success(f"{len(resultados)} chapas en la colección")

    mostrar_galeria(resultados)

# --------------------------------------------------
# Ficha seleccionada (si la hay)
# --------------------------------------------------
if st.session_state.selected_cap is not None:
    mostrar_ficha(st.session_state.selected_cap)
