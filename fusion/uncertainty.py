"""
AgroGuard AI — Uncertainty Gate Module
Pure Python module for evaluating model prediction confidence and top-1 vs top-2 margin.
"""

from typing import Dict, List, Any, Sequence
from config import CONF_THRESHOLD, MARGIN_THRESHOLD


def assess_uncertainty(
    probs: Sequence[float],
    class_names: List[str],
    conf_threshold: float = CONF_THRESHOLD,
    margin_threshold: float = MARGIN_THRESHOLD
) -> Dict[str, Any]:
    """
    Evaluates probability distribution across class names.
    
    Returns:
        dict: {
            "status": "confident" | "uncertain",
            "top1": str,
            "top2": str or None,
            "confidence": float (0-100),
            "margin": float (0-100),
            "reason": str,
            "threshold_note": "prototype thresholds requiring field calibration"
        }
    """
    if probs is None or len(probs) == 0 or len(class_names) == 0:
        return {
            "status": "uncertain",
            "top1": "Unknown",
            "top2": None,
            "confidence": 0.0,
            "margin": 0.0,
            "reason": "Missing or empty probability distribution.",
            "threshold_note": "prototype thresholds requiring field calibration"
        }

    # Ensure python floats
    prob_list = [float(p) for p in probs]
    
    # Sort indices by probability descending
    sorted_indices = sorted(range(len(prob_list)), key=lambda i: prob_list[i], reverse=True)
    
    top1_idx = sorted_indices[0]
    top1_class = class_names[top1_idx] if top1_idx < len(class_names) else "Unknown"
    confidence = prob_list[top1_idx] * 100.0 if prob_list[top1_idx] <= 1.0 else prob_list[top1_idx]
    
    if len(sorted_indices) > 1:
        top2_idx = sorted_indices[1]
        top2_class = class_names[top2_idx] if top2_idx < len(class_names) else "Unknown"
        top2_conf = prob_list[top2_idx] * 100.0 if prob_list[top2_idx] <= 1.0 else prob_list[top2_idx]
    else:
        top2_class = None
        top2_conf = 0.0

    margin = confidence - top2_conf
    
    reasons = []
    if confidence < conf_threshold:
        reasons.append(f"Confidence ({confidence:.1f}%) is below prototype threshold ({conf_threshold:.1f}%).")
    if margin < margin_threshold and len(sorted_indices) > 1:
        reasons.append(f"Top-1 vs Top-2 margin ({margin:.1f}%) is below prototype margin threshold ({margin_threshold:.1f}%).")
        
    if reasons:
        status = "uncertain"
        reason_str = " ".join(reasons)
    else:
        status = "confident"
        reason_str = f"Prediction confident (Confidence: {confidence:.1f}%, Margin: {margin:.1f}%)."
        
    return {
        "status": status,
        "top1": top1_class,
        "top2": top2_class,
        "confidence": confidence,
        "margin": margin,
        "reason": reason_str,
        "threshold_note": "prototype thresholds requiring field calibration"
    }
