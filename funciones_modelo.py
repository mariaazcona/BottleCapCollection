# funciones_modelo.py
import torch
from torchvision import transforms, models
from torchvision.models import MobileNet_V3_Small_Weights
from PIL import Image
import numpy as np

device = "cuda" if torch.cuda.is_available() else "cpu"

# Lazy model holder
_model = None
_transform = transforms.Compose([
    transforms.Resize(256),
    transforms.CenterCrop(224),
    transforms.ToTensor(),
    transforms.Normalize(mean=[0.485,0.456,0.406], std=[0.229,0.224,0.225])
])

def _load_model():
    global _model
    if _model is not None:
        return _model
    # Loads MobileNetV3 Small with recommended weights
    weights = MobileNet_V3_Small_Weights.DEFAULT
    base = models.mobilenet_v3_small(weights=weights).to(device)
    base.eval()
    _model = base
    return _model

def imagen_a_embedding(path):
    """
    Devuelve embedding L2-normalizado como numpy float32 vector (1d).
    """
    model = _load_model()
    img = Image.open(path).convert("RGB")
    x = _transform(img).unsqueeze(0).to(device)  # 1,C,H,W
    with torch.no_grad():
        # forward through features, then global avg pool
        features = model.features(x)  # N, C, H, W
        pooled = torch.nn.functional.adaptive_avg_pool2d(features, 1).squeeze(-1).squeeze(-1)  # N, C
        emb = pooled.cpu().numpy().reshape(-1)
    # normalize
    norm = np.linalg.norm(emb)
    if norm > 0:
        emb = emb / norm
    return emb.astype(np.float32)

def batch_imagenes_a_embeddings(paths):
    """
    Procesa una lista de rutas en batches y devuelve matriz (N, D) float32.
    """
    model = _load_model()
    batch_tensors = []
    device_local = device
    import torch
    imgs = []
    for p in paths:
        img = Image.open(p).convert("RGB")
        imgs.append(_transform(img))
    if not imgs:
        return np.empty((0,0), dtype=np.float32)
    tensor = torch.stack(imgs).to(device_local)  # N,C,H,W
    with torch.no_grad():
        features = model.features(tensor)
        pooled = torch.nn.functional.adaptive_avg_pool2d(features, 1).squeeze(-1).squeeze(-1)
        arr = pooled.cpu().numpy()
    # normalize per-row
    norms = np.linalg.norm(arr, axis=1, keepdims=True)
    norms[norms==0] = 1.0
    arr = arr / norms
    return arr.astype(np.float32)
