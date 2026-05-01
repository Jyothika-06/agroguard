"""
AgroGuard AI v5.0 - Model utilities
Includes a DEMO-MODE fallback so the UI runs even without the trained model.
"""

import os
import json
import random
import numpy as np
import streamlit as st
from config import MODEL_PATH, CLASS_INDICES_PATH, IMG_SIZE

# A safe default class list when class_indices.json is missing, for demo mode
_DEMO_CLASSES = [
    "Tomato___Bacterial_spot",
    "Tomato___Early_blight",
    "Tomato___Late_blight",
    "Tomato___Leaf_Mold",
    "Tomato___Septoria_leaf_spot",
    "Tomato___Spider_mites",
    "Tomato___Target_Spot",
    "Tomato___Tomato_Yellow_Leaf_Curl_Virus",
    "Tomato___Tomato_mosaic_virus",
    "Tomato___healthy",
    "Potato___Early_blight",
    "Potato___Late_blight",
    "Potato___healthy",
    "Pepper__bell___Bacterial_spot",
    "Pepper__bell___healthy",
]

def load_model_assets():
    """
    Load the trained model and class indices, or fall back to demo mode.
    Returns: (model, class_names, mode)
    - mode: "real" if model loaded successfully, "demo" if fallback
    """
    try:
        # Try to load the Keras model
        from tensorflow.keras.models import load_model
        model = load_model(MODEL_PATH)
    except Exception as e:
        # Model failed to load (missing/corrupt/TF error) — fall back to demo
        st.warning(f"Model load failed ({MODEL_PATH}) — running in demo mode.")
        # Log to console for debugging
        try:
            print("Model load error:", str(e))
        except:  # pragma: no cover - defensive
            pass
        model = None

    # Load class indices — support both dict (name->idx) and list formats
    class_names = None
    try:
        if os.path.isfile(CLASS_INDICES_PATH):
            with open(CLASS_INDICES_PATH, 'r', encoding='utf-8') as f:
                class_indices = json.load(f)
            if isinstance(class_indices, dict):
                class_names = list(class_indices.keys())
            elif isinstance(class_indices, list):
                class_names = class_indices
    except Exception as e:
        st.warning(f"Failed to load class indices ({CLASS_INDICES_PATH}) — using demo classes.")
        try:
            print("Class indices load error:", str(e))
        except:  # pragma: no cover
            pass

    if model is None or not class_names:
        # If anything failed, return demo mode defaults
        return None, _DEMO_CLASSES, "demo"

    return model, class_names, "real"

def preprocess_image(img):
    """
    Preprocess PIL image for model input.
    Returns: numpy array (1, 224, 224, 3) normalized to [-1, 1]
    """
    from PIL import Image
    
    # Resize to 224x224
    img = img.resize(IMG_SIZE)
    
    # Convert to numpy array
    arr = np.array(img, dtype=np.float32)
    
    # Normalize to [-1, 1] (typical for MobileNet)
    arr = arr / 127.5 - 1.0
    
    # Add batch dimension
    arr = np.expand_dims(arr, axis=0)
    
    return arr

def predict_with_confidence(model, arr, class_names):
    """
    Make predictions with confidence levels.
    Returns: (best_class, confidence, top5_list, full_predictions)
    """
    if model is None:
        # Demo mode - return mock predictions
        best_class = random.choice(class_names)
        confidence = random.uniform(75, 98)
        top5 = [(c, random.uniform(50, 99)) for c in random.sample(class_names, 5)]
        top5 = sorted(top5, key=lambda x: x[1], reverse=True)
        return best_class, confidence, top5, None
    
    # Real model prediction
    predictions = model.predict(arr)
    pred_array = predictions[0]
    
    # Get top-5
    top5_indices = np.argsort(pred_array)[-5:][::-1]
    top5 = [(class_names[idx], float(pred_array[idx]) * 100) for idx in top5_indices]
    
    # Best prediction
    best_idx = np.argmax(pred_array)
    best_class = class_names[best_idx]
    confidence = float(pred_array[best_idx]) * 100
    
    return best_class, confidence, top5, pred_array
