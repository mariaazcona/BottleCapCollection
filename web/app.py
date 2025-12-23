# app.py
# Streamlit web interface for CapCollection

import streamlit as st
import sys
import os
import pathlib

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
st.markdown("<style> .stImage img {border-radius: 8px;} </style>", unsafe_allow_html=True)

# --------------------------------------------------
# Buscar por marca
# --------------------------------------------------
st.subheader("Búsqueda por Marca")

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
        for r in resultados:
            col1, col2 = st.columns([1, 3])
            print(r[0])
            print(r[1])
            print(r[2])
            print(r[3])
            
            # Imagen
            img_file = BASE_DIR/r[3]
            if img_file.exists():
                col1.image(str(img_file), width=100)
            else:
                col1.text("No hay imagen.")
            
            # Info
            col2.markdown(f"**Marca:** {r[1]}")  # índice 1 = marca
            col2.markdown(f"**Tipo:** {r[2]}")   # índice 2 = tipo
            col2.markdown("---")
