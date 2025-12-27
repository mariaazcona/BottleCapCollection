# import_excel.py
# Importa datos desde el Excel maestro a la base de datos SQLite.

import os
import sqlite3
import numpy as np
import pandas as pd
from math import ceil

import embeddings as fm
import services as fn

from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

EXCEL_FILE = BASE_DIR / "assets" / "data" / "capcollection.xlsx"
IMAGES_DIR = BASE_DIR / "assets" / "images"

BATCH_SIZE = 16  # Ajustar según recursos disponibles


# --------------------------------------------------
# Inicialización de la base de datos
# --------------------------------------------------
fn.crear_bd()
fn.ensure_embedding_column()


# --------------------------------------------------
# Cargar datos desde Excel
# --------------------------------------------------
df = pd.read_excel(EXCEL_FILE)

# Obtener rutas ya existentes en la BD
rows = fn.obtener_todas_chapas()
existing_paths = {r[3] for r in rows}  # columna imagen


# --------------------------------------------------
# Preparar lista de elementos a procesar
# --------------------------------------------------
to_process = []

for _, row in df.iterrows():
    if pd.isna(row.get("id")) or pd.isna(row.get("imagen")):
        continue

    imagen_name = str(row["imagen"])
    imagen_path = IMAGES_DIR / imagen_name

    if not os.path.exists(imagen_path):
        print(f"Imagen no encontrada: {imagen_path}")
        continue

    to_process.append((
        int(row["id"]),
        row.get("marca", ""),
        row.get("tipo", ""),
        imagen_path
    ))


# --------------------------------------------------
# Determinar qué imágenes necesitan embedding
# --------------------------------------------------
with sqlite3.connect(fn.DB_FILE) as conn:
    cur = conn.cursor()
    cur.execute("SELECT imagen, embedding FROM capcollection")
    have_emb = {img: emb for img, emb in cur.fetchall() if emb is not None}

paths_to_compute = []
indexes_to_compute = []

for idx, item in enumerate(to_process):
    _, _, _, path = item
    if path not in have_emb:
        paths_to_compute.append(path)
        indexes_to_compute.append(idx)


# --------------------------------------------------
# Calcular embeddings por lotes
# --------------------------------------------------
if paths_to_compute:
    n_batches = ceil(len(paths_to_compute) / BATCH_SIZE)

    for b in range(n_batches):
        start = b * BATCH_SIZE
        end = start + BATCH_SIZE

        batch_paths = paths_to_compute[start:end]
        emb_batch = fm.batch_imagenes_a_embeddings(batch_paths)  # float32 (N, D)

        # Convertir a float16 para almacenamiento
        emb_batch_f16 = emb_batch.astype(np.float16)

        # Guardar en BD
        for j, path in enumerate(batch_paths):
            emb_bytes = emb_batch_f16[j].tobytes()
            idx = indexes_to_compute[start + j]

            id_, marca, tipo, imagen_path = to_process[idx]
            fn.insertar_chapa(id_, marca, tipo, str(imagen_path), emb_bytes)


# --------------------------------------------------
# Insertar o actualizar filas que ya tenían embedding
# --------------------------------------------------
for id_, marca, tipo, imagen_path in to_process:
    if imagen_path in have_emb:
        fn.insertar_chapa(id_, marca, tipo, str(imagen_path), have_emb[imagen_path])
    # Si no estaba en have_emb, ya se insertó en el paso anterior


print("Importación completada.")

# Recargar embeddings en RAM para búsquedas rápidas
fn.reload_embeddings()