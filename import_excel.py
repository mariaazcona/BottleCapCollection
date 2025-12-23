# import_excel.py
import sqlite3
import pandas as pd
import os
import numpy as np
from math import ceil
import funciones_modelo as fm
import services as fn

EXCEL_FILE = "data/capcollection.xlsx"
IMAGES_DIR = "images"
BATCH_SIZE = 16  # ajustar según memoria/CPU

# Ensure DB + column
fn.crear_bd()
fn.ensure_embedding_column()

# Read excel
df = pd.read_excel(EXCEL_FILE)

# Get set of already stored image paths to avoid recalculating
rows = fn.obtener_todas_chapas()
existing_paths = set(r[3] for r in rows)  # imagen column

# Prepare list of new items to insert (or update) with embedding
to_process = []
for _, row in df.iterrows():
    if pd.isna(row.get("id")) or pd.isna(row.get("imagen")):
        continue
    imagen_name = str(row["imagen"])
    imagen_path = os.path.join(IMAGES_DIR, imagen_name)
    if not os.path.exists(imagen_path):
        print("Imagen no encontrada:", imagen_path)
        continue
    # If image already exists and has an embedding, skip compute; but we will still ensure DB row exists
    to_process.append((int(row["id"]), row["marca"], row["tipo"], imagen_path))

# Process in batches: compute embeddings only for items that don't already have embedding
# We'll query DB for embedding presence
conn = sqlite3.connect(fn.DB_FILE)
cur = conn.cursor()
cur.execute("SELECT imagen, embedding FROM chapas")
have_emb = {r[0]: r[1] for r in cur.fetchall() if r[1] is not None}
conn.close()

# Build list of paths to compute
paths_to_compute = []
indexes_to_compute = []  # indexes in to_process
for idx, item in enumerate(to_process):
    _, _, _, p = item
    if p not in have_emb:
        paths_to_compute.append(p)
        indexes_to_compute.append(idx)

# Batch compute embeddings
if paths_to_compute:
    n_batches = ceil(len(paths_to_compute) / BATCH_SIZE)
    for b in range(n_batches):
        start = b*BATCH_SIZE
        end = start + BATCH_SIZE
        batch_paths = paths_to_compute[start:end]
        emb_batch = fm.batch_imagenes_a_embeddings(batch_paths)  # float32 (n,D)
        # convert to float16 for storage
        emb_batch_f16 = emb_batch.astype(np.float16)
        # write to DB per item
        for j, path in enumerate(batch_paths):
            emb_bytes = emb_batch_f16[j].tobytes()
            # find corresponding to_process index
            idx = indexes_to_compute[start + j]
            id_, marca, tipo, imagen_path = to_process[idx]
            fn.insertar_chapa(id_, marca, tipo, imagen_path, emb_bytes)

# For items that had embeddings already or remained, ensure rows exist/updated
for id_, marca, tipo, imagen_path in to_process:
    if imagen_path in have_emb:
        # re-insert preserving existing embedding
        emb_blob = have_emb[imagen_path]
        fn.insertar_chapa(id_, marca, tipo, imagen_path, emb_blob)
    else:
        # already inserted when computing batch
        pass

print("Importación completada.")
# reload embeddings into RAM for fast search
fn.reload_embeddings()
