"""
AgroGuard AI — Sensor Simulator Module (Prototype Sensor Mode)
Generates simulated sensor readings and preset field scenarios.
Light unit: % intensity (0-100%).
"""

from datetime import datetime
from typing import Dict, Any, Optional, List


def get_preset_scenario(scenario_name: str) -> Dict[str, Any]:
    """
    Returns preset simulated sensor data package.
    Light unit: % intensity (0.0 to 100.0%).
    All readings are explicitly tagged with simulated=True and mode="Prototype Sensor Mode".
    """
    now_iso = datetime.now().isoformat()
    
    if scenario_name == "water_stress":
        return {
            "simulated": True,
            "mode": "Prototype Sensor Mode",
            "timestamp": now_iso,
            "soil_moisture": 15.0,    # % (low soil moisture)
            "temperature": 34.0,      # °C (high temp)
            "humidity": 45.0,         # %
            "light": 85.0,            # % sunlight intensity
            "humidity_history": [48.0, 46.0, 45.0]
        }
    elif scenario_name == "humid_disease_favourable":
        return {
            "simulated": True,
            "mode": "Prototype Sensor Mode",
            "timestamp": now_iso,
            "soil_moisture": 45.0,    # % (adequate)
            "temperature": 26.0,      # °C
            "humidity": 88.0,         # % (high humidity)
            "light": 40.0,            # %
            "humidity_history": [86.0, 87.0, 88.0]  # sustained high humidity
        }
    elif scenario_name == "missing_sensor":
        return {
            "simulated": True,
            "mode": "Prototype Sensor Mode",
            "timestamp": now_iso,
            "soil_moisture": None,    # missing soil moisture sensor
            "temperature": 26.0,      # °C
            "humidity": None,         # missing humidity sensor
            "light": 60.0,            # %
            "humidity_history": []
        }
    elif scenario_name == "out_of_range":
        return {
            "simulated": True,
            "mode": "Prototype Sensor Mode",
            "timestamp": now_iso,
            "soil_moisture": -10.0,   # invalid range (<0)
            "temperature": 65.0,      # invalid extreme temperature
            "humidity": 120.0,        # invalid humidity (>100)
            "light": 50.0,            # %
            "humidity_history": [120.0, 120.0]
        }
    else:  # "normal" or fallback
        return {
            "simulated": True,
            "mode": "Prototype Sensor Mode",
            "timestamp": now_iso,
            "soil_moisture": 50.0,    # % (optimal)
            "temperature": 25.0,      # °C (optimal)
            "humidity": 60.0,         # % (optimal)
            "light": 70.0,            # %
            "humidity_history": [58.0, 59.0, 60.0]
        }


def create_manual_reading(
    soil_moisture: Optional[float],
    temperature: Optional[float],
    humidity: Optional[float],
    light: Optional[float],
    humidity_history: Optional[List[float]] = None
) -> Dict[str, Any]:
    """Constructs a custom simulated reading package."""
    hist = humidity_history if humidity_history is not None else ([humidity] if humidity is not None else [])
    return {
        "simulated": True,
        "mode": "Prototype Sensor Mode",
        "timestamp": datetime.now().isoformat(),
        "soil_moisture": soil_moisture,
        "temperature": temperature,
        "humidity": humidity,
        "light": light,
        "humidity_history": hist
    }
