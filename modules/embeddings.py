"""
embeddings.py
--------------
Módulo encargado de cargar el modelo de visión (MobileNetV3 Small),
preprocesar imágenes y generar embeddings normalizados para búsquedas
por similitud.

Responsabilidades:
- Lazy loading del modelo
- Transformación estándar de imágenes
- Generación de embeddings individuales y por lotes
"""

from pathlib import Path
from typing import List

import numpy as np
import torch
from PIL import Image
from torchvision import transforms, models
from torchvision.models import MobileNet_V3_Small_Weights


# ======================================================
# 1. CONFIGURACIÓN Y ESTADO DEL MODELO
# ======================================================

class EmbeddingModel:
    """
    Cache del modelo MobileNetV3 Small y sus transformaciones.
    Se carga solo una vez (lazy loading).
    """
    device = "cuda" if torch.cuda.is_available() else "cpu"
    model = None

    # Transformación estándar de ImageNet
    transform = transforms.Compose([
        transforms.Resize(256),
        transforms.CenterCrop(224),
        transforms.ToTensor(),
        transforms.Normalize(
            mean=[0.485, 0.456, 0.406],
            std=[0.229, 0.224, 0.225]
        )
    ])

    @classmethod
    def load_model(cls):
        """Carga MobileNetV3 Small si no está ya cargado."""
        if cls.model is not None:
            return cls.model

        weights = MobileNet_V3_Small_Weights.DEFAULT
        model = models.mobilenet_v3_small(weights=weights).to(cls.device)
        model.eval()

        cls.model = model
        return cls.model


# ======================================================
# 2. FUNCIONES AUXILIARES
# ======================================================

def _load_image(path: str) -> Image.Image:
    """Carga una imagen desde disco y la convierte a RGB."""
    path = Path(path)

    if not path.exists():
        raise FileNotFoundError(f"Imagen no encontrada: {path}")

    try:
        return Image.open(path).convert("RGB")
    except Exception as e:
        raise RuntimeError(f"No se pudo abrir la imagen {path}: {e}")


# ======================================================
# 3. EMBEDDING DE UNA SOLA IMAGEN
# ======================================================

def image_to_embedding(path: str) -> np.ndarray:
    """
    Convierte una imagen en un embedding L2-normalizado usando MobileNetV3 Small.

    Parámetros:
        path (str): Ruta al archivo de imagen.

    Devuelve:
        np.ndarray: Vector de características normalizado (float32).
    """
    model = EmbeddingModel.load_model()
    img = _load_image(path)

    tensor = EmbeddingModel.transform(img).unsqueeze(0).to(EmbeddingModel.device)

    with torch.no_grad():
        features = model.features(tensor)
        pooled = torch.nn.functional.adaptive_avg_pool2d(features, 1)
        emb = pooled.squeeze().cpu().numpy()

    # Normalización L2
    norm = np.linalg.norm(emb)
    if norm > 0:
        emb = emb / norm

    return emb.astype(np.float32)


# ======================================================
# 4. EMBEDDINGS POR LOTES
# ======================================================

def batch_images_to_embeddings(paths: List[str]) -> np.ndarray:
    """
    Procesa una lista de rutas de imagen y devuelve una matriz (N, D) float32.

    Parámetros:
        paths (List[str]): Lista de rutas de imágenes.

    Devuelve:
        np.ndarray: Matriz de embeddings normalizados (N, D).
    """
    model = EmbeddingModel.load_model()

    images = []
    for p in paths:
        try:
            img = _load_image(p)
            images.append(EmbeddingModel.transform(img))
        except Exception:
            # Si una imagen falla, se ignora
            continue

    if not images:
        return np.empty((0, 0), dtype=np.float32)

    tensor = torch.stack(images).to(EmbeddingModel.device)

    with torch.no_grad():
        features = model.features(tensor)
        pooled = torch.nn.functional.adaptive_avg_pool2d(features, 1)
        arr = pooled.squeeze(-1).squeeze(-1).cpu().numpy()

    # Normalización L2 por fila
    norms = np.linalg.norm(arr, axis=1, keepdims=True)
    norms[norms == 0] = 1.0
    arr = arr / norms

    return arr.astype(np.float32)
