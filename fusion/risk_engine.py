"""
AgroGuard AI — Risk Fusion Engine
Pure Python environmental & disease risk assessment rules. Zero Streamlit dependencies.

Rule Enforcements:
- Invalid or missing sensor values evaluate to UNKNOWN, never LOW.
- A healthy disease prediction NEVER suppresses environmental risks.
- An uncertain disease prediction sets disease input to UNKNOWN, while environmental risks are still computed.
- Adequate soil moisture triggers NO irrigation advisory.
- All thresholds are marked as prototype placeholders requiring field calibration.
"""

from typing import Dict, Any, List, Optional
from fusion.crop_params import get_crop_params, CROP_PARAMS


def evaluate_field_risk(
    uncertainty_res: Optional[Dict[str, Any]],
    disease_class: Optional[str],
    crop: str,
    validated_sensors: Dict[str, Any],
    custom_crop_params: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Pure Python function evaluating crop environmental & disease risks.
    
    Returns:
        dict: {
            "water_stress_risk": "LOW" | "MODERATE" | "HIGH" | "UNKNOWN",
            "heat_stress_risk": "LOW" | "MODERATE" | "HIGH" | "UNKNOWN",
            "disease_spread_risk": "LOW" | "MODERATE" | "HIGH" | "UNKNOWN",
            "overall_risk": "LOW" | "MODERATE" | "HIGH" | "UNKNOWN",
            "reasons": [str],
            "unknown_inputs": [str],
            "thresholds_note": "prototype thresholds requiring field calibration",
            "disease_status_used": str
        }
    """
    params = custom_crop_params or get_crop_params(crop)
    clean_vals = validated_sensors.get("clean_values", {})
    sensor_status = validated_sensors.get("status", {})
    hum_history = validated_sensors.get("humidity_history", [])

    moisture = clean_vals.get("soil_moisture")
    temp = clean_vals.get("temperature")
    humidity = clean_vals.get("humidity")
    light = clean_vals.get("light")

    reasons: List[str] = []
    unknown_inputs: List[str] = []

    # ── 1. Disease Prediction Status Determination ─────────────────────────────
    disease_input_status = "UNKNOWN"
    if uncertainty_res is None or disease_class is None:
        disease_input_status = "UNKNOWN"
        unknown_inputs.append("Leaf Disease Image (Not uploaded)")
    elif uncertainty_res.get("status") == "uncertain":
        disease_input_status = "UNKNOWN"
        unknown_inputs.append("Leaf Disease Image (Uncertain model prediction)")
        reasons.append("Disease prediction is uncertain; treating visual disease state as UNKNOWN.")
    else:
        disease_input_status = disease_class

    is_healthy = False
    if disease_input_status != "UNKNOWN":
        is_healthy = "healthy" in disease_input_status.lower()

    # ── 2. Water Stress Risk ───────────────────────────────────────────────────
    moisture_low = params["moisture_low_limit"]
    temp_min_water = params["water_stress_temp_min"]

    if moisture is None:
        water_stress_risk = "UNKNOWN"
        unknown_inputs.append("Soil Moisture (Missing or invalid range)")
    elif temp is None:
        water_stress_risk = "UNKNOWN"
        unknown_inputs.append("Temperature (Missing or invalid range)")
    else:
        if moisture <= moisture_low and temp >= temp_min_water:
            water_stress_risk = "HIGH"
            reasons.append(
                f"Soil moisture ({moisture:.1f}%) is at/below prototype threshold ({moisture_low:.1f}%) "
                f"and temperature ({temp:.1f}°C) is high (>= {temp_min_water:.1f}°C) -> HIGH water stress risk."
            )
        elif moisture <= moisture_low:
            water_stress_risk = "MODERATE"
            reasons.append(
                f"Soil moisture ({moisture:.1f}%) is at/below prototype threshold ({moisture_low:.1f}%) -> MODERATE water stress risk."
            )
        else:
            water_stress_risk = "LOW"
            # Adequate moisture -> no water stress, no irrigation advice needed

    # ── 3. Heat Stress Risk ────────────────────────────────────────────────────
    heat_limit = params["heat_stress_limit"]

    if temp is None:
        heat_stress_risk = "UNKNOWN"
        if "Temperature (Missing or invalid range)" not in unknown_inputs:
            unknown_inputs.append("Temperature (Missing or invalid range)")
    else:
        if temp >= heat_limit:
            heat_stress_risk = "HIGH"
            reasons.append(
                f"Temperature ({temp:.1f}°C) exceeds prototype heat stress limit ({heat_limit:.1f}°C) -> HIGH heat stress risk."
            )
        elif temp >= temp_min_water:
            heat_stress_risk = "MODERATE"
            reasons.append(
                f"Temperature ({temp:.1f}°C) is elevated (>= {temp_min_water:.1f}°C) -> MODERATE heat stress risk."
            )
        else:
            heat_stress_risk = "LOW"

    # ── 4. Disease Spread Risk ─────────────────────────────────────────────────
    hum_spread_limit = params["humidity_spread_limit"]
    hum_persistence_len = params["humidity_persistence_len"]

    # Evaluate humidity persistence
    is_high_humidity = False
    if humidity is not None:
        if humidity >= hum_spread_limit:
            is_high_humidity = True
        elif hum_history and len(hum_history) >= hum_persistence_len:
            recent = hum_history[-hum_persistence_len:]
            if all(h >= hum_spread_limit for h in recent):
                is_high_humidity = True

    if humidity is None:
        disease_spread_risk = "UNKNOWN"
        unknown_inputs.append("Humidity (Missing or invalid range)")
    else:
        if disease_input_status != "UNKNOWN" and not is_healthy:
            # Active disease detected
            if is_high_humidity:
                disease_spread_risk = "HIGH"
                reasons.append(
                    f"Active disease symptoms detected ({disease_input_status}) AND humidity ({humidity:.1f}%) "
                    f"is high (>= prototype threshold {hum_spread_limit:.1f}%) -> HIGH disease spread risk."
                )
            else:
                disease_spread_risk = "MODERATE"
                reasons.append(
                    f"Active disease symptoms detected ({disease_input_status}) under moderate humidity ({humidity:.1f}%) -> MODERATE disease spread risk."
                )
        elif is_healthy:
            # Healthy plant image — healthy prediction NEVER suppresses environmental risk!
            if is_high_humidity:
                disease_spread_risk = "MODERATE"
                reasons.append(
                    f"Plant appears visually healthy, but humidity ({humidity:.1f}%) is high (>= {hum_spread_limit:.1f}%) -> MODERATE environmental disease risk."
                )
            else:
                disease_spread_risk = "LOW"
        else: # UNKNOWN disease image
            if is_high_humidity:
                disease_spread_risk = "MODERATE"
                reasons.append(
                    f"Disease state UNKNOWN, but humidity ({humidity:.1f}%) is high (>= {hum_spread_limit:.1f}%) -> MODERATE disease spread risk."
                )
            else:
                disease_spread_risk = "UNKNOWN"

    # ── 5. Overall Risk Calculation ───────────────────────────────────────────
    # Risk severity order: HIGH > MODERATE > LOW > UNKNOWN
    risk_levels = [water_stress_risk, heat_stress_risk, disease_spread_risk]
    
    if "HIGH" in risk_levels:
        overall_risk = "HIGH"
    elif "MODERATE" in risk_levels:
        overall_risk = "MODERATE"
    elif "LOW" in risk_levels:
        overall_risk = "LOW"
    else:
        overall_risk = "UNKNOWN"

    return {
        "water_stress_risk": water_stress_risk,
        "heat_stress_risk": heat_stress_risk,
        "disease_spread_risk": disease_spread_risk,
        "overall_risk": overall_risk,
        "reasons": reasons,
        "unknown_inputs": unknown_inputs,
        "thresholds_note": "prototype thresholds requiring field calibration",
        "disease_status_used": disease_input_status
    }
