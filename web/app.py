# app.py
# Streamlit web interface for CapCollection

import streamlit as st
import sys
import os
import pathlib

# --------------------------------------------------
# Importar la lógica del proyecto principal
# --------------------------------------------------
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(BASE_DIR)

import services as fn

# --------------------------------------------------
# Configuración básica de la app
# --------------------------------------------------
st.set_page_config(
    page_title="CapCollection",
    layout="wide"
)

st.title("🍺 CapCollection")
st.caption("Web version of your bottle cap collection")
st.markdown("<style> .stImage img {border-radius: 8px;} </style>", unsafe_allow_html=True)

# --------------------------------------------------
# Buscar por marca
# --------------------------------------------------
st.subheader("Search by brand")

marca = st.text_input(
    "Brand name",
    placeholder="e.g. Coca-Cola, Heineken..."
)

if marca:
    resultados = fn.buscar_por_marca(marca)

    if not resultados:
        st.info("No results found.")
    else:
        st.success(f"{len(resultados)} result(s) found")
        for r in resultados:
            col1, col2 = st.columns([1, 3])
            
            # Imagen
            image_path = pathlib.Path(r[3])  # índice 3 = imagen_path
            if image_path.exists():
                col1.image(str(image_path), width=100)
            else:
                col1.text("No image")
            
            # Info
            col2.markdown(f"**Marca:** {r[1]}")  # índice 1 = marca
            col2.markdown(f"**Tipo:** {r[2]}")   # índice 2 = tipo
            col2.markdown("---")
