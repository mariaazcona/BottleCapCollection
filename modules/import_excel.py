"""
import_excel.py
----------------
Script para importar datos desde el archivo Excel maestro y sincronizarlos
con la base de datos SQLite. También calcula embeddings para las imágenes
que aún no los tienen.

Responsabilidades:
- Leer el Excel principal
- Validar rutas de imágenes
- Insertar o actualizar registros en la BD
- Calcular embeddings por lotes
"""

from pathlib import Path
from math import ceil
import sqlite3

import numpy as np
import pandas as pd

import services as fn
import embeddings as fm


# ======================================================
# 1. CONFIGURACIÓN
# ======================================================

PROJECT_ROOT = Path(__file__).resolve().parent.parent

EXCEL_PATH = PROJECT_ROOT / "assets" / "data" / "capcollection.xlsx"
IMAGES_DIR = PROJECT_ROOT / "assets" / "images"

BATCH_SIZE = 16  # Ajustable según recursos disponibles


# ======================================================
# 2. INICIALIZACIÓN DE LA BASE DE DATOS
# ======================================================

fn.create_database()
fn.ensure_embedding_column()


# ======================================================
# 3. CARGA DEL EXCEL
# ======================================================

if not EXCEL_PATH.exists():
    raise FileNotFoundError(f"No se encontró el archivo Excel: {EXCEL_PATH}")

df = pd.read_excel(EXCEL_PATH)

# Obtener rutas ya existentes en la BD
rows = fn.get_all_caps()
existing_paths = {r[3] for r in rows}  # columna 'imagen'


# ======================================================
# 4. PREPARAR LISTA DE ELEMENTOS A PROCESAR
# ======================================================

to_process = []

for _, row in df.iterrows():
    cap_id = row.get("id")
    image_name = row.get("imagen")

    if pd.isna(cap_id) or pd.isna(image_name):
        continue

    image_path = IMAGES_DIR / str(image_name)

    if not image_path.exists():
        print(f"[ADVERTENCIA] Imagen no encontrada: {image_path}")
        continue

    to_process.append((
        int(cap_id),
        row.get("marca", ""),
        row.get("tipo", ""),
        image_path
    ))


# ======================================================
# 5. DETERMINAR QUÉ IMÁGENES NECESITAN EMBEDDING
# ======================================================

with sqlite3.connect(fn.DB_PATH) as conn:
    cur = conn.cursor()
    cur.execute("SELECT imagen, embedding FROM capcollection")
    have_emb = {img: emb for img, emb in cur.fetchall() if emb is not None}

paths_to_compute = []
indexes_to_compute = []

for idx, item in enumerate(to_process):
    _, _, _, path = item
    if str(path) not in have_emb:
        paths_to_compute.append(path)
        indexes_to_compute.append(idx)


# ======================================================
# 6. CALCULAR EMBEDDINGS POR LOTES
# ======================================================

if paths_to_compute:
    n_batches = ceil(len(paths_to_compute) / BATCH_SIZE)

    for b in range(n_batches):
        start = b * BATCH_SIZE
        end = start + BATCH_SIZE

        batch_paths = paths_to_compute[start:end]

        # Embeddings float32 (N, D)
        emb_batch = fm.batch_images_to_embeddings(batch_paths)

        # Convertir a float16 para almacenamiento
        emb_batch_f16 = emb_batch.astype(np.float16)

        # Guardar en BD
        for j, path in enumerate(batch_paths):
            emb_bytes = emb_batch_f16[j].tobytes()
            idx = indexes_to_compute[start + j]

            cap_id, brand, cap_type, image_path = to_process[idx]
            fn.save_cap(cap_id, brand, cap_type, str(image_path), emb_bytes)


# ======================================================
# 7. ACTUALIZAR FILAS QUE YA TENÍAN EMBEDDING
# ======================================================

for cap_id, brand, cap_type, image_path in to_process:
    if str(image_path) in have_emb:
        fn.save_cap(cap_id, brand, cap_type, str(image_path), have_emb[str(image_path)])


print("Importación completada correctamente.")

# Recargar embeddings en RAM para búsquedas rápidas
fn.refresh_embeddings()
