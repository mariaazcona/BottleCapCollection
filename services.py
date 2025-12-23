# services.py
# Core business logic: database access, image processing, embeddings and search functions.
import sqlite3
import os
import numpy as np
from datetime import datetime
import pandas as pd

DB_FILE = "data/capcollection.db"
IMAGES_DIR = "images"
_EMBEDDINGS_LOADED = False
_emb_matrix = None      # numpy float32 (N, D)
_emb_ids = None         # list of row tuples (id, marca, tipo, imagen)
_emb_paths = None       # list of image paths
_emb_dtype = np.float16 # storage dtype

# ----------------- DB helpers -----------------
def crear_bd():
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    cur.execute("""
    CREATE TABLE IF NOT EXISTS capcollection (
        id INTEGER PRIMARY KEY,
        marca TEXT,
        tipo TEXT,
        imagen TEXT,
        embedding BLOB
    )
    """)
    conn.commit()
    conn.close()

def ensure_embedding_column():
    # safe add column if not exists (sqlite doesn't support IF NOT EXISTS for ALTER)
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    cur.execute("PRAGMA table_info(capcollection)")
    cols = [r[1] for r in cur.fetchall()]
    if "embedding" not in cols:
        cur.execute("ALTER TABLE capcollection ADD COLUMN embedding BLOB")
        conn.commit()
    conn.close()

def insertar_chapa(id_, marca, tipo, imagen_path, emb_bytes=None):
    """
    inserta o reemplaza. emb_bytes es None o blob (np.array.tobytes of float16)
    """
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    cur.execute("""
        INSERT OR REPLACE INTO capcollection (id, marca, tipo, imagen, embedding)
        VALUES (?, ?, ?, ?, ?)
    """, (id_, marca, tipo, imagen_path, emb_bytes))
    conn.commit()
    conn.close()

def obtener_todas_chapas():
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    cur.execute("SELECT id, marca, tipo, imagen, embedding FROM capcollection ORDER BY id")
    datos = cur.fetchall()
    conn.close()
    return datos

# ----------------- Embeddings in-memory (lazy) -----------------
def _load_embeddings_to_ram():
    global _EMBEDDINGS_LOADED, _emb_matrix, _emb_ids, _emb_paths
    if _EMBEDDINGS_LOADED:
        return
    rows = obtener_todas_chapas()
    if not rows:
        _emb_matrix = np.empty((0,0), dtype=np.float32)
        _emb_ids = []
        _emb_paths = []
        _EMBEDDINGS_LOADED = True
        return
    embs = []
    ids_list = []
    paths = []
    for r in rows:
        id_, marca, tipo, imagen, blob = r
        ids_list.append((id_, marca, tipo, imagen))
        paths.append(imagen)
        if blob is None:
            embs.append(None)
        else:
            arr = np.frombuffer(blob, dtype=np.float16).astype(np.float32)
            embs.append(arr)
    # Filter only non-None embeddings
    valid = [e for e in embs if e is not None]
    if valid:
        _emb_matrix = np.vstack(valid)  # float32
    else:
        _emb_matrix = np.empty((0,0), dtype=np.float32)
    # We keep mapping of ids to embeddings by index: we'll rebuild index list of rows that have embedding
    # Build a parallel list of rows that correspond to rows with embeddings
    rows_with_emb = []
    paths_with_emb = []
    idx = 0
    for i, e in enumerate(embs):
        if e is not None:
            rows_with_emb.append(ids_list[i])
            paths_with_emb.append(paths[i])
            idx += 1
    _emb_ids = rows_with_emb
    _emb_paths = paths_with_emb
    _EMBEDDINGS_LOADED = True

def reload_embeddings():
    global _EMBEDDINGS_LOADED
    _EMBEDDINGS_LOADED = False
    _load_embeddings_to_ram()

# ----------------- Search utilities -----------------
def buscar_por_marca(texto):
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    cur.execute("SELECT id, marca, tipo, imagen FROM capcollection WHERE LOWER(marca) LIKE ?", (f"%{texto.lower()}%",))
    datos = cur.fetchall()
    conn.close()
    return datos

def buscar_por_imagen(path_query, top_k=8):
    """
    Retorna lista [(row_tuple, similarity_score), ...], score in [0,1], sorted desc
    """
    # lazy load embeddings
    _load_embeddings_to_ram()
    import funciones_modelo as fm
    if _emb_matrix.size == 0:
        # No embeddings in DB yet: fallback to compute embedding and return empty
        emb_q = fm.imagen_a_embedding(path_query).astype(np.float32)
        return []
    # compute query embedding
    emb_q = fm.imagen_a_embedding(path_query).astype(np.float32)
    # emb_q normalized in model function
    # compute dot product with matrix (vectorized). _emb_matrix is float32 shape (N,D)
    sims = (_emb_matrix @ emb_q)  # because vectors are L2-normalized -> dot = cos similarity
    # clamp
    sims = sims.astype(np.float32)
    # get top indices
    idxs = np.argsort(sims)[::-1][:top_k]
    results = []
    for i in idxs:
        row = _emb_ids[i]  # (id, marca, tipo, imagen)
        score = float(sims[i])
        results.append((row, score))
    return results

def buscar_por_imagen_simple(path_query, top_k=5):
    """
    Retorna SOLO filas:
    (id, marca, tipo, imagen_path)
    """
    resultados_con_score = buscar_por_imagen(path_query, top_k)

    # Quitar el score
    return [row for row, score in resultados_con_score]

# ----------------- Export to Excel (timestamped) -----------------
def exportar_a_excel_version():
    os.makedirs("data/exports", exist_ok=True)
    fecha_hora = datetime.now().strftime("%Y%m%d_%H%M%S")
    archivo = os.path.join("data/exports", f"capcollection_{fecha_hora}.xlsx")
    conn = sqlite3.connect(DB_FILE)
    df = pd.read_sql_query("SELECT id, marca, tipo, imagen FROM capcollection ORDER BY id", conn)
    conn.close()
    df.to_excel(archivo, index=False)
    return archivo
