# app.py
# Streamlit web interface for CapCollection

import streamlit as st
import pathlib
import sys
import sqlite3
import pandas as pd
import datetime

# --------------------------------------------------
# Importar la lógica del proyecto principal
# --------------------------------------------------
BASE_DIR = pathlib.Path(__file__).parent.parent
sys.path.append(str(BASE_DIR))

import services as fn

# --------------------------------------------------
# Configuración básica de la app
# --------------------------------------------------
st.set_page_config(
    page_title="CapCollection",
    layout="wide"
)

st.title("Maria's Collection")
st.caption("La colección de chapas de botella de Maria A.G.")
st.markdown("""
<style>
/* Quitar iconos/enlaces de anclaje en títulos */
h1 a, h2 a, h3 a, h4 a {
    display: none !important;
}
</style>
""", unsafe_allow_html=True)
st.sidebar.header("Opciones")

# --------------------------------------------------
# Funciones
# --------------------------------------------------
def mostrar_resultados(resultados):
    IMAGES_DIR = BASE_DIR / "images"

    for r in resultados:
        col1, col2 = st.columns([1, 3])

        img_name = pathlib.Path(r[3]).name
        img_file = IMAGES_DIR / img_name

        if img_file.exists():
            col1.image(str(img_file), width=100)
        else:
            col1.text("No hay imagen.")

        col2.markdown(f"**Marca:** {r[1]}")
        col2.markdown(f"**Tipo:** {r[2]}")
        col2.markdown("---")

# Show All
if st.sidebar.button("Mostrar Todas"):
    resultados = fn.obtener_todas_chapas()
    if not resultados:
        st.info("No hay chapas en la colección.")
    else:
        st.success(f"{len(resultados)} resultados encontrados")
        mostrar_resultados(resultados)

# Reiniciar
if st.sidebar.button("Borrar Todas"):
    # Limpiar resultados y inputs
    st.session_state.resultados = []
    st.session_state.marca = ""
    st.session_state.uploaded_file = None

# Buscar por marca
st.subheader("Buscar por Marca")
marca = st.text_input(
    "Marca",
    placeholder="p. ej. Coca-Cola, Heineken..."
)

if marca:
    resultados = fn.buscar_por_marca(marca)
    if not resultados:
        st.info("No se han encontrado resultados.")
    else:
        st.success(f"{len(resultados)} resultados encontrados")
        mostrar_resultados(resultados)

# Buscar por imagen
st.subheader("Buscar por Imagen")
uploaded_file = st.file_uploader("Sube una imagen", type=["png", "jpg", "jpeg"])

if uploaded_file is not None:
    resultados = fn.buscar_por_imagen_simple(uploaded_file, top_k=5)
    if not resultados:
        st.info("No se han encontrado coincidencias.")
    else:
        st.success(f"{len(resultados)} resultados encontrados")
        mostrar_resultados(resultados)

st.write("Archivos en images/:")
for p in (BASE_DIR / "images").glob("*"):
    st.write(p.name)
