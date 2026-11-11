"""
AgroGuard AI v4.0 — Model utilities
"""

import os, json
import numpy as np
import streamlit as st
from config import MODEL_PATH, CLASS_INDICES_PATH, IMG_SIZE


CLASS_NAME_MAP = {
    "Pepper__bell___Bacterial_spot": "Pepper__bell___Bacterial_spot",
    "Pepper__bell___healthy": "Pepper__bell___healthy",
    "Potato___Early_blight": "Potato___Early_blight",
    "Potato___Late_blight": "Potato___Late_blight",
    "Potato___healthy": "Potato___healthy",
    "Tomato_Bacterial_spot": "Tomato___Bacterial_spot",
    "Tomato_Early_blight": "Tomato___Early_blight",
    "Tomato_Late_blight": "Tomato___Late_blight",
    "Tomato_Leaf_Mold": "Tomato___Leaf_Mold",
    "Tomato_Septoria_leaf_spot": "Tomato___Septoria_leaf_spot",
    "Tomato_Spider_mites_Two_spotted_spider_mite": "Tomato___Spider_mites Two-spotted_spider_mite",
    "Tomato__Target_Spot": "Tomato___Target_Spot",
    "Tomato__Tomato_YellowLeaf__Curl_Virus": "Tomato___Tomato_Yellow_Leaf_Curl_Virus",
    "Tomato__Tomato_mosaic_virus": "Tomato___Tomato_mosaic_virus",
    "Tomato_healthy": "Tomato___healthy",
}


def normalize_class_name(name: str) -> str:
    """Returns canonical normalized class name matching TREATMENT_DB keys."""
    if not name:
        return name
    return CLASS_NAME_MAP.get(name, name)


@st.cache_resource(show_spinner="Loading AI model…")
def load_model_assets():
    try:
        import tensorflow as tf
    except ImportError:
        st.error("TensorFlow not installed. Run: pip install tensorflow")
        return None, None

    if not os.path.exists(MODEL_PATH) or not os.path.exists(CLASS_INDICES_PATH):
        return None, None

    try:
        model = tf.keras.models.load_model(MODEL_PATH)
        with open(CLASS_INDICES_PATH) as f:
            raw = json.load(f)

        if isinstance(raw, dict):
            if all(str(k).isdigit() for k in raw.keys()):
                class_names = [raw[str(i)] for i in range(len(raw))]
            else:
                class_names = [None] * len(raw)
                for name, idx in raw.items():
                    class_names[idx] = name
        else:
            class_names = list(raw)

        class_names = [normalize_class_name(name) for name in class_names]
        return model, class_names
    except Exception as e:
        st.error(f"Model load error: {e}")
        return None, None


def preprocess_image(img):
    from PIL import Image
    if img.mode != "RGB":
        img = img.convert("RGB")
    img = img.resize(IMG_SIZE, Image.Resampling.LANCZOS)
    arr = np.array(img, dtype=np.float32) / 127.5 - 1.0
    return np.expand_dims(arr, axis=0)


def predict_with_confidence(model, img_array, class_names):
    try:
        raw = model.predict(img_array, verbose=0)[0]
    except Exception as e:
        raise RuntimeError(f"Model prediction failed: {e}") from e

    # Fix double softmax: if output is already probabilities (in [0, 1] and sums to ~1), do not re-apply softmax.
    is_prob = np.all(raw >= 0.0) and np.all(raw <= 1.0) and np.isclose(float(np.sum(raw)), 1.0, atol=1e-2)
    if is_prob:
        probs = np.array(raw, dtype=np.float32)
    else:
        # Numerically stable NumPy softmax (avoiding redundant TensorFlow re-invocations)
        shift_raw = raw - np.max(raw)
        exp_raw = np.exp(shift_raw)
        probs = np.array(exp_raw / np.sum(exp_raw), dtype=np.float32)

    best_idx   = int(np.argmax(probs))
    confidence = float(probs[best_idx] * 100.0)
    best_class = class_names[best_idx]
    top5 = [(class_names[i], float(probs[i] * 100.0))
            for i in np.argsort(probs)[-5:][::-1]]
    return best_class, confidence, top5, probs
