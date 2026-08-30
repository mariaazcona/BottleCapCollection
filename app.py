"""
app.py
------
Interfaz web en Streamlit para CapCollection.

Responsabilidades:
- Filtros de la colección (marca y tipo)
- Búsqueda por imagen
- Galería paginada de chapas
"""

import streamlit as st

import modules.services as fn
from modules.ui_theme import load_theme

TITLE = "Maria's CapCollection"
PAGE_SIZE = 36
GRID_COLUMNS = 6
CARD_HEIGHT = 250
SEARCH_RESULTS = 12

st.set_page_config(
    page_title=TITLE,
    layout="wide",
)

load_theme()

st.markdown("""
<style>
[data-testid="collapsedControl"] {
    visibility: visible !important;
    display: block !important;
}
[data-testid="stAppDeployButton"] {
    display: none;
}
#MainMenu {
    visibility: hidden;
}
button[aria-label="Fullscreen"] { 
    display: none; 
}
button[kind="header"] {
    display: none;
}
</style>
""", unsafe_allow_html=True)

session = st.session_state
session.setdefault("page", 0)
session.setdefault("filters", None)


# ======================================================
# DATOS
# ======================================================

@st.cache_data(show_spinner=False)
def load_caps():
    """Devuelve la colección completa como lista de diccionarios."""
    return [
        {"id": cap_id, "marca": marca or "", "tipo": tipo or "", "imagen": imagen}
        for cap_id, marca, tipo, imagen, _ in fn.get_all_caps()
    ]


def filter_caps(caps, brand, types):
    """Filtra la colección por texto de marca y por tipos seleccionados."""
    brand = brand.strip().lower()

    return [
        cap for cap in caps
        if (not brand or brand in cap["marca"].lower())
        and (not types or cap["tipo"] in types)
    ]


def search_similar(uploaded_file, top_k):
    """Devuelve las chapas más parecidas a la imagen subida, con su similitud."""
    results = fn.search_by_image(uploaded_file, top_k=top_k)

    return [
        ({"id": cap_id, "marca": marca or "", "tipo": tipo or "", "imagen": imagen},
         score)
        for (cap_id, marca, tipo, imagen), score in results
    ]


# ======================================================
# COMPONENTES
# ======================================================

def cap_image(cap, width="stretch"):
    """Muestra la imagen de una chapa, o un aviso si no está disponible."""
    path = fn.resolve_image_path(cap["imagen"])

    if path is None:
        st.caption("Sin imagen")
        return

    st.image(str(path), width=width)


def cap_card(cap, score=None):
    """Tarjeta compacta con la imagen y el nombre de la chapa."""
    height = CARD_HEIGHT + (50 if score is not None else 0)

    with st.container(border=True, height=height):
        cap_image(cap)
        st.markdown(f"**{cap['marca'] or 'Sin marca'}**")

        if score is not None:
            st.progress(max(0.0, min(1.0, score)), text=f"{score:.0%} de parecido")


def cap_grid(items):
    """Galería de tarjetas en una rejilla responsive."""
    with st.container(key="cap_grid"):
        for item in items:
            cap, score = item if isinstance(item, tuple) else (item, None)
            cap_card(cap, score)


def paginate(items):
    """Recorta la lista a la página actual y dibuja el navegador de páginas."""
    total_pages = max(1, -(-len(items) // PAGE_SIZE))
    session.page = min(session.page, total_pages - 1)

    start = session.page * PAGE_SIZE
    page_items = items[start:start + PAGE_SIZE]

    if total_pages > 1:
        previous, indicator, following = st.columns([1, 2, 1])

        with previous:
            if st.button("Anterior", disabled=session.page == 0, width="stretch"):
                session.page -= 1
                st.rerun()

        with indicator:
            st.markdown(
                f"<p class='pager'>Página {session.page + 1} de {total_pages}</p>",
                unsafe_allow_html=True,
            )

        with following:
            if st.button("Siguiente", disabled=session.page >= total_pages - 1,
                         width="stretch"):
                session.page += 1
                st.rerun()

    return page_items


# ======================================================
# BARRA LATERAL
# ======================================================

caps = load_caps()

with st.sidebar:
    st.header(f"{len(caps)} chapas en la colección")

    st.subheader("Filtros")
    brand_query = st.text_input("Marca", placeholder="Ej. Estrella Damm")
    selected_types = st.multiselect("Tipo", fn.get_types(), placeholder="Escoge uno o varios tipos")

    st.subheader("Buscar por imagen")
    uploaded = st.file_uploader("Sube una foto de una chapa",
                                type=["png", "jpg", "jpeg"])


# ======================================================
# CONTENIDO PRINCIPAL
# ======================================================

st.title(TITLE, anchor=False)

if uploaded:
    st.subheader("Chapas más parecidas", anchor=False)

    preview, _ = st.columns([1, 3])
    with preview:
        st.image(uploaded, caption="Imagen de referencia", width=180)

    with st.spinner("Comparando con la colección..."):
        matches = search_similar(uploaded, SEARCH_RESULTS)

    if matches:
        cap_grid(matches)
    else:
        st.info("Todavía no hay embeddings en la base de datos.")
else:
    filters = (brand_query, tuple(selected_types))
    if filters != session.filters:
        session.filters = filters
        session.page = 0

    results = filter_caps(caps, brand_query, selected_types)

    st.subheader(f"{len(results)} chapas encontradas", anchor=False)

    if results:
        cap_grid(paginate(results))
    else:
        st.info("Ninguna chapa coincide con los filtros.")
