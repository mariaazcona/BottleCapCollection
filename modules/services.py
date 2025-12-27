# services.py
# Lógica principal: acceso a base de datos, embeddings, búsqueda y exportación.

import sqlite3
import os
import numpy as np
from datetime import datetime
import pandas as pd

from pathlib import Path

# BASE_DIR = carpeta raíz del proyecto (donde está app.py)
BASE_DIR = Path(__file__).resolve().parent.parent

DB_FILE = BASE_DIR / "assets" / "data" / "capcollection.db"
IMAGES_DIR = BASE_DIR / "assets" / "images"

# Estado interno para embeddings cargados en RAM
_EMBEDDINGS_LOADED = False
_emb_matrix = None        # Matriz numpy float32 (N, D)
_emb_ids = None           # Lista de tuplas (id, marca, tipo, imagen)
_emb_paths = None         # Lista de rutas de imagen
_emb_dtype = np.float16   # Tipo de almacenamiento en BLOB


# --------------------------------------------------
# Utilidades de Base de Datos
# --------------------------------------------------
def crear_bd():
    """Crea la base de datos si no existe."""
    with sqlite3.connect(DB_FILE) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS capcollection (
                id INTEGER PRIMARY KEY,
                marca TEXT,
                tipo TEXT,
                imagen TEXT,
                embedding BLOB
            )
        """)


def ensure_embedding_column():
    """Añade la columna 'embedding' si no existe."""
    with sqlite3.connect(DB_FILE) as conn:
        cur = conn.cursor()
        cur.execute("PRAGMA table_info(capcollection)")
        columnas = [r[1] for r in cur.fetchall()]

        if "embedding" not in columnas:
            cur.execute("ALTER TABLE capcollection ADD COLUMN embedding BLOB")


def insertar_chapa(id_, marca, tipo, imagen_path, emb_bytes=None):
    """
    Inserta o reemplaza una chapa en la BD.
    emb_bytes debe ser None o un BLOB generado con np.array.tobytes().
    """
    with sqlite3.connect(DB_FILE) as conn:
        conn.execute("""
            INSERT OR REPLACE INTO capcollection (id, marca, tipo, imagen, embedding)
            VALUES (?, ?, ?, ?, ?)
        """, (id_, marca, tipo, imagen_path, emb_bytes))


def obtener_todas_chapas():
    """Devuelve todas las chapas almacenadas."""
    with sqlite3.connect(DB_FILE) as conn:
        cur = conn.cursor()
        cur.execute("SELECT id, marca, tipo, imagen, embedding FROM capcollection ORDER BY id")
        return cur.fetchall()


# --------------------------------------------------
# Gestión de Embeddings en Memoria (Lazy Loading)
# --------------------------------------------------
def _load_embeddings_to_ram():
    """Carga los embeddings desde la BD a memoria solo una vez."""
    global _EMBEDDINGS_LOADED, _emb_matrix, _emb_ids, _emb_paths

    if _EMBEDDINGS_LOADED:
        return

    rows = obtener_todas_chapas()

    if not rows:
        _emb_matrix = np.empty((0, 0), dtype=np.float32)
        _emb_ids = []
        _emb_paths = []
        _EMBEDDINGS_LOADED = True
        return

    embeddings = []
    ids_list = []
    paths = []

    for id_, marca, tipo, imagen, blob in rows:
        ids_list.append((id_, marca, tipo, imagen))
        paths.append(imagen)

        if blob is None:
            embeddings.append(None)
        else:
            arr = np.frombuffer(blob, dtype=_emb_dtype).astype(np.float32)
            embeddings.append(arr)

    # Filtrar embeddings válidos
    valid_embeddings = [e for e in embeddings if e is not None]

    _emb_matrix = (
        np.vstack(valid_embeddings) if valid_embeddings
        else np.empty((0, 0), dtype=np.float32)
    )

    # Asociar filas solo con embeddings válidos
    _emb_ids = [ids_list[i] for i, e in enumerate(embeddings) if e is not None]
    _emb_paths = [paths[i] for i, e in enumerate(embeddings) if e is not None]

    _EMBEDDINGS_LOADED = True


def reload_embeddings():
    """Fuerza recarga de embeddings desde la BD."""
    global _EMBEDDINGS_LOADED
    _EMBEDDINGS_LOADED = False
    _load_embeddings_to_ram()


# --------------------------------------------------
# Búsquedas
# --------------------------------------------------
def buscar_por_marca(texto):
    """Busca chapas por coincidencia parcial en la marca."""
    texto = texto.lower()

    with sqlite3.connect(DB_FILE) as conn:
        cur = conn.cursor()
        cur.execute("""
            SELECT id, marca, tipo, imagen
            FROM capcollection
            WHERE LOWER(marca) LIKE ?
        """, (f"%{texto}%",))
        return cur.fetchall()


def buscar_por_imagen(path_query, top_k=8):
    """
    Busca las chapas más similares a una imagen.
    Devuelve: [(row_tuple, similarity_score), ...]
    """
    _load_embeddings_to_ram()

    import modules.embeddings as fm

    # Si no hay embeddings almacenados
    if _emb_matrix.size == 0:
        fm.imagen_a_embedding(path_query)  # Se calcula pero no se usa
        return []

    # Embedding de la imagen de consulta
    emb_q = fm.imagen_a_embedding(path_query).astype(np.float32)

    # Producto punto = similitud coseno (ya normalizado)
    sims = (_emb_matrix @ emb_q).astype(np.float32)

    # Top K
    idxs = np.argsort(sims)[::-1][:top_k]

    return [( _emb_ids[i], float(sims[i]) ) for i in idxs]


def buscar_por_imagen_simple(path_query, top_k=5):
    """Versión simplificada: devuelve solo las filas sin score."""
    resultados = buscar_por_imagen(path_query, top_k)
    return [row for row, _ in resultados]


# --------------------------------------------------
# Exportación a Excel
# --------------------------------------------------
def exportar_a_excel_version():
    """Exporta la colección a un Excel con timestamp."""
    os.makedirs("data/exports", exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    archivo = f"data/exports/capcollection_{timestamp}.xlsx"

    with sqlite3.connect(DB_FILE) as conn:
        df = pd.read_sql_query("""
            SELECT id, marca, tipo, imagen
            FROM capcollection
            ORDER BY id
        """, conn)

    df.to_excel(archivo, index=False)
    return archivo
