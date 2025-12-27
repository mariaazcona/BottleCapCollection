# app.py
# Interfaz web en Streamlit para CapCollection

import streamlit as st
import pathlib
import modules.services as fn

from pathlib import Path

# Ruta base del proyecto
BASE_DIR = pathlib.Path(__file__).resolve().parent


# --------------------------------------------------
# Configuración básica de la aplicación
# --------------------------------------------------
st.set_page_config(
    page_title="CapCollection",
    layout="wide"
)

st.title("Maria's Collection")
st.caption("La colección de chapas de botella de Maria A.G.")

# Ocultar iconos de anclaje en los títulos
st.markdown("""
<style>
h1 a, h2 a, h3 a, h4 a {
    display: none !important;
}
</style>
""", unsafe_allow_html=True)

st.sidebar.header("Opciones")


# --------------------------------------------------
# Funciones auxiliares
# --------------------------------------------------
def mostrar_resultados(resultados):
    """Muestra una lista de chapas con su imagen, marca y tipo."""

    for r in resultados:
        col1, col2 = st.columns([1, 3])

        img_file = Path(r[3].replace("\\", "/"))
        if not img_file.is_absolute():
            img_file = BASE_DIR / img_file

        if img_file.exists():
            col1.image(str(img_file), width=100)
        else:
            st.info(f"No se encontró la imagen: {r[3]}")

        col2.markdown(f"**Marca:** {r[1]}")
        col2.markdown(f"**Tipo:** {r[2]}")
        col2.markdown("---")


# --------------------------------------------------
# Mostrar todas las chapas
# --------------------------------------------------
if st.sidebar.button("Mostrar Todas"):
    resultados = fn.obtener_todas_chapas()

    if not resultados:
        st.info("No hay chapas en la colección.")
    else:
        st.success(f"{len(resultados)} resultados encontrados")
        mostrar_resultados(resultados)


# --------------------------------------------------
# Reiniciar búsqueda
# --------------------------------------------------
if st.sidebar.button("Borrar Todas"):
    st.session_state.resultados = []
    st.session_state.marca = ""
    st.session_state.uploaded_file = None


# --------------------------------------------------
# Búsqueda por marca
# --------------------------------------------------
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


# --------------------------------------------------
# Búsqueda por imagen
# --------------------------------------------------
st.subheader("Buscar por Imagen")

uploaded_file = st.file_uploader(
    "Sube una imagen",
    type=["png", "jpg", "jpeg"]
)

if uploaded_file is not None:
    resultados = fn.buscar_por_imagen_simple(uploaded_file, top_k=5)

    if not resultados:
        st.info("No se han encontrado coincidencias.")
    else:
        st.success(f"{len(resultados)} resultado(s) encontrado(s)")
        mostrar_resultados(resultados)
