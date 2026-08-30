"""
services.py
------------
Módulo principal de lógica de negocio para CapCollection.

Responsabilidades:
- Acceso a base de datos SQLite
- Gestión de embeddings en memoria
- Búsqueda por marca y por imagen
- Exportación de datos a Excel
"""

import sqlite3
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd


# ======================================================
# 1. RUTAS Y CONFIGURACIÓN
# ======================================================

PROJECT_ROOT = Path(__file__).resolve().parent.parent

DB_PATH = PROJECT_ROOT / "assets" / "data" / "capcollection.db"
IMAGES_DIR = PROJECT_ROOT / "assets" / "images"
EXPORT_DIR = PROJECT_ROOT / "assets" / "data" / "exports"

EMBEDDING_DTYPE = np.float16
DEFAULT_IMAGE = IMAGES_DIR / "default.png"


# ======================================================
# 2. ESTADO INTERNO DE EMBEDDINGS (CACHE)
# ======================================================

class EmbeddingCache:
    """Cache en memoria para acelerar búsquedas por imagen."""
    loaded = False
    matrix = None      # Matriz numpy (N, D)
    ids = None         # Lista de tuplas (id, marca, tipo, imagen)
    paths = None       # Lista de rutas de imagen


# ======================================================
# 3. UTILIDADES DE BASE DE DATOS
# ======================================================

def create_database():
    """Crea la base de datos y la tabla principal si no existen."""
    with sqlite3.connect(DB_PATH) as conn:
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
    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.cursor()
        cur.execute("PRAGMA table_info(capcollection)")
        columnas = [r[1] for r in cur.fetchall()]

        if "embedding" not in columnas:
            cur.execute("ALTER TABLE capcollection ADD COLUMN embedding BLOB")


def save_cap(cap_id, brand, cap_type, image_path, embedding_blob=None):
    """
    Inserta o actualiza una chapa en la base de datos.
    """
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("""
            INSERT OR REPLACE INTO capcollection (id, marca, tipo, imagen, embedding)
            VALUES (?, ?, ?, ?, ?)
        """, (cap_id, brand, cap_type, image_path, embedding_blob))


def get_all_caps():
    """Devuelve todas las chapas almacenadas."""
    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.cursor()
        cur.execute("""
            SELECT id, marca, tipo, imagen, embedding
            FROM capcollection
            ORDER BY id
        """)
        return cur.fetchall()


# ======================================================
# 4. GESTIÓN DE EMBEDDINGS EN MEMORIA
# ======================================================

def _load_embeddings():
    """Carga los embeddings desde la base de datos a memoria (lazy loading)."""
    if EmbeddingCache.loaded:
        return

    rows = get_all_caps()

    if not rows:
        EmbeddingCache.matrix = np.empty((0, 0), dtype=np.float32)
        EmbeddingCache.ids = []
        EmbeddingCache.paths = []
        EmbeddingCache.loaded = True
        return

    embeddings = []
    ids_list = []
    paths = []

    for cap_id, brand, cap_type, image_path, blob in rows:
        ids_list.append((cap_id, brand, cap_type, image_path))
        paths.append(image_path)

        if blob is None:
            embeddings.append(None)
        else:
            arr = np.frombuffer(blob, dtype=EMBEDDING_DTYPE).astype(np.float32)
            embeddings.append(arr)

    valid_embeddings = [e for e in embeddings if e is not None]

    EmbeddingCache.matrix = (
        np.vstack(valid_embeddings)
        if valid_embeddings else np.empty((0, 0), dtype=np.float32)
    )

    EmbeddingCache.ids = [
        ids_list[i] for i, e in enumerate(embeddings) if e is not None
    ]
    EmbeddingCache.paths = [
        paths[i] for i, e in enumerate(embeddings) if e is not None
    ]

    EmbeddingCache.loaded = True


def refresh_embeddings():
    """Fuerza recarga de embeddings desde la base de datos."""
    EmbeddingCache.loaded = False
    _load_embeddings()


# ======================================================
# 5. BÚSQUEDAS
# ======================================================

def search_by_brand(text):
    """Busca chapas por coincidencia parcial en la marca."""
    text = text.lower()

    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.cursor()
        cur.execute("""
            SELECT id, marca, tipo, imagen
            FROM capcollection
            WHERE LOWER(marca) LIKE ?
            ORDER BY id
        """, (f"%{text}%",))
        return cur.fetchall()


def get_types():
    """Devuelve la lista de tipos distintos presentes en la colección."""
    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.cursor()
        cur.execute("""
            SELECT DISTINCT tipo
            FROM capcollection
            WHERE tipo IS NOT NULL AND tipo <> ''
            ORDER BY tipo
        """)
        return [r[0] for r in cur.fetchall()]


def search_by_image(image, top_k=8):
    """
    Busca las chapas más similares a una imagen.

    Acepta una ruta en disco o un archivo en memoria (st.file_uploader).
    Devuelve: [(row_tuple, similarity_score), ...]
    """
    # Import diferido: evita cargar torch hasta la primera búsqueda por imagen.
    from modules import embeddings

    _load_embeddings()

    if EmbeddingCache.matrix.size == 0:
        return []

    query_emb = embeddings.image_to_embedding(image).astype(np.float32)

    sims = (EmbeddingCache.matrix @ query_emb).astype(np.float32)

    idxs = np.argsort(sims)[::-1][:top_k]

    return [(EmbeddingCache.ids[i], float(sims[i])) for i in idxs]


def search_by_image_simple(image, top_k=5):
    """Versión simplificada: devuelve solo las filas sin score."""
    return [row for row, _ in search_by_image(image, top_k)]


# ======================================================
# 6. RUTAS DE IMÁGENES
# ======================================================

def resolve_image_path(stored_path):
    """
    Traduce la ruta guardada en la base de datos a una ruta válida local.

    La base de datos puede contener rutas absolutas de otra máquina
    (por ejemplo de Windows), así que el nombre de archivo se vuelve a
    resolver dentro de assets/images.
    """
    if not stored_path:
        return None

    normalized = Path(str(stored_path).replace("\\", "/"))

    candidate = IMAGES_DIR / normalized.name
    if candidate.exists():
        return candidate

    if normalized.is_absolute() and normalized.exists():
        return normalized

    candidate = PROJECT_ROOT / normalized
    return candidate if candidate.exists() else None


# ======================================================
# 7. EXPORTACIÓN
# ======================================================

def export_to_excel():
    """Exporta la colección a un archivo Excel con timestamp."""
    EXPORT_DIR.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    file_path = EXPORT_DIR / f"capcollection_{timestamp}.xlsx"

    with sqlite3.connect(DB_PATH) as conn:
        df = pd.read_sql_query("""
            SELECT id, marca, tipo, imagen
            FROM capcollection
            ORDER BY id
        """, conn)

    df.to_excel(file_path, index=False)
    return file_path
