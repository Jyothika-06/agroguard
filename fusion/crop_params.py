"""
# prototype thresholds requiring field calibration; not agronomically validated

AgroGuard AI — Crop Threshold Parameters
Per-crop environmental parameter limits for risk evaluation.
"""

from typing import Dict, Any

# Prototype threshold parameters per supported crop
CROP_PARAMS: Dict[str, Dict[str, Any]] = {
    "Tomato": {
        "moisture_low_limit": 20.0,       # % soil moisture
        "heat_stress_limit": 35.0,        # °C temperature limit
        "water_stress_temp_min": 32.0,    # °C min temp for combined water stress
        "humidity_spread_limit": 80.0,    # % relative humidity
        "humidity_persistence_len": 3,    # consecutive readings needed for sustained humidity risk
        "threshold_note": "prototype thresholds requiring field calibration; not agronomically validated"
    },
    "Potato": {
        "moisture_low_limit": 25.0,       # % soil moisture
        "heat_stress_limit": 30.0,        # °C temperature limit
        "water_stress_temp_min": 28.0,    # °C min temp for combined water stress
        "humidity_spread_limit": 85.0,    # % relative humidity
        "humidity_persistence_len": 3,    # consecutive readings
        "threshold_note": "prototype thresholds requiring field calibration; not agronomically validated"
    },
    "Pepper": {
        "moisture_low_limit": 20.0,       # % soil moisture
        "heat_stress_limit": 35.0,        # °C temperature limit
        "water_stress_temp_min": 32.0,    # °C min temp for combined water stress
        "humidity_spread_limit": 80.0,    # % relative humidity
        "humidity_persistence_len": 3,    # consecutive readings
        "threshold_note": "prototype thresholds requiring field calibration; not agronomically validated"
    }
}


def get_crop_params(crop: str) -> Dict[str, Any]:
    """Retrieves crop parameter thresholds with fallback to Tomato defaults."""
    return CROP_PARAMS.get(crop, CROP_PARAMS["Tomato"])
