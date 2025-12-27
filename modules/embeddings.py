# embeddings.py
# Carga del modelo, preprocesado de imágenes y generación de embeddings.

import torch
from torchvision import transforms, models
from torchvision.models import MobileNet_V3_Small_Weights
from PIL import Image
import numpy as np

# Selección automática de dispositivo
device = "cuda" if torch.cuda.is_available() else "cpu"

# Modelo cargado de forma perezosa (lazy loading)
_model = None

# Transformación estándar para MobileNetV3
_transform = transforms.Compose([
    transforms.Resize(256),
    transforms.CenterCrop(224),
    transforms.ToTensor(),
    transforms.Normalize(
        mean=[0.485, 0.456, 0.406],
        std=[0.229, 0.224, 0.225]
    )
])


# --------------------------------------------------
# Carga del modelo (lazy)
# --------------------------------------------------
def _load_model():
    """Carga MobileNetV3 Small con pesos preentrenados si no está ya cargado."""
    global _model

    if _model is not None:
        return _model

    weights = MobileNet_V3_Small_Weights.DEFAULT
    model = models.mobilenet_v3_small(weights=weights).to(device)
    model.eval()

    _model = model
    return _model


# --------------------------------------------------
# Embedding de una sola imagen
# --------------------------------------------------
def imagen_a_embedding(path):
    """
    Devuelve un embedding L2-normalizado como vector numpy float32 (1D).
    """
    model = _load_model()

    img = Image.open(path).convert("RGB")
    tensor = _transform(img).unsqueeze(0).to(device)  # (1, C, H, W)

    with torch.no_grad():
        features = model.features(tensor)  # (1, C, H, W)
        pooled = torch.nn.functional.adaptive_avg_pool2d(features, 1)
        emb = pooled.squeeze().cpu().numpy()  # (C,)

    # Normalización L2
    norm = np.linalg.norm(emb)
    if norm > 0:
        emb = emb / norm

    return emb.astype(np.float32)


# --------------------------------------------------
# Embeddings por lotes (batch)
# --------------------------------------------------
def batch_imagenes_a_embeddings(paths):
    """
    Procesa una lista de rutas de imagen y devuelve una matriz (N, D) float32.
    """
    model = _load_model()

    # Cargar imágenes
    imgs = []
    for p in paths:
        img = Image.open(p).convert("RGB")
        imgs.append(_transform(img))

    if not imgs:
        return np.empty((0, 0), dtype=np.float32)

    tensor = torch.stack(imgs).to(device)  # (N, C, H, W)

    with torch.no_grad():
        features = model.features(tensor)
        pooled = torch.nn.functional.adaptive_avg_pool2d(features, 1)
        arr = pooled.squeeze(-1).squeeze(-1).cpu().numpy()  # (N, D)

    # Normalización L2 por fila
    norms = np.linalg.norm(arr, axis=1, keepdims=True)
    norms[norms == 0] = 1.0
    arr = arr / norms

    return arr.astype(np.float32)
