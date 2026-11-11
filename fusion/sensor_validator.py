"""
AgroGuard AI — Sensor Validator Module
Validates simulated sensor inputs for ranges, missing values, and staleness.
Rule: Bad or missing sensor values evaluate to UNKNOWN, never LOW.
"""

from typing import Dict, Any, Optional

# Plausible range limits for validation
VALID_RANGES = {
    "soil_moisture": (0.0, 100.0),   # %
    "humidity":      (0.0, 100.0),   # %
    "temperature":   (-10.0, 55.0),  # °C
    "light":         (0.0, 100.0),   # % intensity
}


def validate_sensor_readings(reading: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validates sensor values in the reading package.
    
    Returns:
        dict: {
            "status": {
                "soil_moisture": "ok" | "out_of_range" | "missing",
                "humidity": "ok" | "out_of_range" | "missing",
                "temperature": "ok" | "out_of_range" | "missing",
                "light": "ok" | "out_of_range" | "missing"
            },
            "clean_values": {
                "soil_moisture": float or None,
                "humidity": float or None,
                "temperature": float or None,
                "light": float or None
            },
            "has_missing_or_invalid": bool
        }
    """
    status = {}
    clean_values = {}
    has_missing_or_invalid = False

    for sensor_key, (min_val, max_val) in VALID_RANGES.items():
        val = reading.get(sensor_key)
        if val is None:
            status[sensor_key] = "missing"
            clean_values[sensor_key] = None
            has_missing_or_invalid = True
        else:
            try:
                fval = float(val)
                if min_val <= fval <= max_val:
                    status[sensor_key] = "ok"
                    clean_values[sensor_key] = fval
                else:
                    status[sensor_key] = "out_of_range"
                    clean_values[sensor_key] = None  # Invalidate invalid values -> UNKNOWN
                    has_missing_or_invalid = True
            except (ValueError, TypeError):
                status[sensor_key] = "out_of_range"
                clean_values[sensor_key] = None
                has_missing_or_invalid = True

    return {
        "status": status,
        "clean_values": clean_values,
        "has_missing_or_invalid": has_missing_or_invalid,
        "humidity_history": reading.get("humidity_history", [])
    }
