# AgroGuard SIH26180 — Prototype Status Documentation

**Team PLANTIFY · SIH26180**  
*AI-Powered Field-Deployable Smart Farming Assistant*

---

## Capability Status Matrix

| Capability | Status | Details |
|---|---|---|
| **MobileNetV2 Model** | **Implemented** | 15 classes, 3 crops (Tomato, Potato, Bell Pepper) |
| **Streamlit UI** | **Implemented** | Leaf scan upload, treatment/fertilizer KB, HTML report generator, feedback CSV |
| **Bilingual UI** | **Implemented** | English / Tamil language toggle, AgroBot chatbot, browser voice/TTS |
| **Weather Tab** | **Implemented** | OpenWeatherMap integration with mock fallback |
| **Confidence Display** | **Implemented & Fixed** | Double-softmax defect resolved; probabilities correctly bounded in [0, 100%] |
| **Uncertainty Gate** | **Implemented** | Evaluates prediction confidence and Top-1 vs Top-2 margin against prototype placeholders |
| **Sensor Simulator** | **Simulated** | Presets & custom inputs for soil moisture, temperature, humidity, sunlight (`Prototype Sensor Mode`) |
| **Sensor Validator** | **Implemented** | Range & validity checks; missing/invalid inputs evaluate to `UNKNOWN`, never `LOW` |
| **Rule-Based Risk Engine** | **Implemented** | Pure Python engine evaluating Water Stress, Heat Stress, Disease Spread, and Overall Risk |
| **Recommendation Engine** | **Implemented** | Non-certainty advisory strings (English & Tamil) with mandatory officer disclaimer |
| **Patch-Wise Analysis** | **Experimental** | Optional 3x3 grid tile analysis (disabled by default; unvalidated) |
| **Physical Sensors & Hardware** | **Proposed** | Physical soil moisture/temperature/humidity sensors, Pi Camera, Raspberry Pi edge board |
| **Edge Optimization** | **Proposed** | TFLite conversion/quantization, offline edge inference, local buzzer/mobile alert notifications |
| **Field Validation & Enclosures** | **Future** | Solar/battery power, IP65 enclosure, field validation trials, farmer pilot programs |

---

## Prototype Thresholds Disclaimer

> [!IMPORTANT]
> All numerical risk thresholds (`moisture_low_limit`, `heat_stress_limit`, `humidity_spread_limit`, `CONF_THRESHOLD = 60.0%`, `MARGIN_THRESHOLD = 15.0%`) are explicitly **prototype thresholds requiring field calibration**.
> They are non-validated placeholder values intended for prototype demonstration and field tuning on user test images after double-softmax correction.

---

## Known Model Limitations

1. **Single-Leaf Distribution**: The underlying MobileNetV2 model was trained on single-leaf, plain-background images from the PlantVillage dataset. Images containing multi-leaf field backgrounds or mixed healthy/diseased leaves may be predicted healthy.
2. **Experimental Patch Analysis**: The optional 3x3 grid tile analysis splits images into tiles outside the training distribution; results must be treated as experimental and unvalidated.
