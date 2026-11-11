"""
AgroGuard AI — Experimental Patch-Wise Analysis Module
Splits image into a 3x3 grid of tiles and evaluates per-tile disease prediction.

CAVEAT:
Patch-wise grid tiles are outside the model's single-leaf training distribution.
This feature is EXPERIMENTAL and NOT validated for field accuracy.
"""

from typing import Dict, Any, List
import numpy as np
from PIL import Image


def analyze_image_patches(
    pil_image: Image.Image,
    model: Any,
    class_names: List[str],
    conf_threshold: float = 60.0
) -> Dict[str, Any]:
    """
    Splits pil_image into a 3x3 grid (9 patches) and predicts condition for each patch.
    
    Returns:
        dict: {
            "grid_size": (3, 3),
            "tiles": [
                {
                    "row": int, "col": int,
                    "best_class": str,
                    "confidence": float,
                    "is_diseased": bool,
                    "is_confident": bool
                }
            ],
            "diseased_tile_count": int,
            "experimental_note": "Experimental patch-wise analysis (unvalidated, outside training distribution)"
        }
    """
    if pil_image is None or model is None or not class_names:
        return {
            "grid_size": (3, 3),
            "tiles": [],
            "diseased_tile_count": 0,
            "experimental_note": "Experimental patch-wise analysis unavailable (missing image/model)"
        }

    from model_utils import preprocess_image, predict_with_confidence

    w, h = pil_image.size
    tile_w = w // 3
    tile_h = h // 3

    tiles = []
    diseased_count = 0

    for r in range(3):
        for c in range(3):
            left = c * tile_w
            upper = r * tile_h
            right = (c + 1) * tile_w if c < 2 else w
            lower = (r + 1) * tile_h if r < 2 else h

            crop_box = (left, upper, right, lower)
            tile_img = pil_image.crop(crop_box)
            
            arr = preprocess_image(tile_img)
            best_class, conf, top5, probs = predict_with_confidence(model, arr, class_names)

            is_diseased = "healthy" not in best_class.lower()
            is_conf = conf >= conf_threshold

            if is_diseased and is_conf:
                diseased_count += 1

            tiles.append({
                "row": r + 1,
                "col": c + 1,
                "best_class": best_class,
                "confidence": conf,
                "is_diseased": is_diseased,
                "is_confident": is_conf
            })

    return {
        "grid_size": (3, 3),
        "tiles": tiles,
        "diseased_tile_count": diseased_count,
        "experimental_note": "Experimental patch-wise analysis (unvalidated, outside training distribution)"
    }
