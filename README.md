# 🌱 AgroGuard AI — Intelligent Crop Protection System & Field Unit Risk Layer

[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![Streamlit](https://img.shields.io/badge/streamlit-1.35+-red.svg)](https://streamlit.io)
[![TensorFlow](https://img.shields.io/badge/tensorflow-2.13+-orange.svg)](https://tensorflow.org)

> **AI-Powered Field-Deployable Smart Farming Assistant**  
> High-performance disease classification for Tomato, Potato, and Bell Pepper crops paired with a pure Python environmental risk fusion engine and bilingual (English / Tamil) advisory support.

---

## 📌 Project Overview

**AgroGuard AI** bridges computer vision diagnostics with environmental context. While traditional leaf scanners only analyze visual symptoms in isolation, AgroGuard combines a 15-class MobileNetV2 convolutional neural network with an agronomic risk engine that evaluates soil moisture, temperature, and relative humidity.

When visual disease symptoms coincide with disease-favorable weather or environmental stress (such as high humidity or drought), AgroGuard calculates holistic field risk levels (Water Stress, Heat Stress, Disease Spread, and Overall Risk) and generates actionable, non-certainty advisory guidelines.

---

## ✨ Main Features

| Feature | Description | Status |
| :--- | :--- | :--- |
| 🔬 **Disease Detection** | MobileNetV2 CNN model classifies 15 conditions across Tomato, Potato & Bell Pepper | Fully Implemented |
| 🧪 **Field Unit** | Rule-based environmental risk engine & simulated sensor inputs | **Prototype Sensor Mode** |
| ⚖️ **Uncertainty Gate** | Confidence (<60%) and Top-1 vs. Top-2 margin (<15%) safety assessment | Fully Implemented |
| 🛡️ **Risk Fusion Engine** | Decoupled pure Python engine assessing Water Stress, Heat Stress, and Disease Spread | Fully Implemented |
| 🌐 **Bilingual Interface** | Complete English & Tamil UI with localized recommendations and audio support | Fully Implemented |
| 🛠 **Treatment & Fertilizer** | Crop- and disease-adapted chemical, organic, and NPK management guidance | Fully Implemented |
| 💬 **AgroBot Assistant** | Interactive bilingual chatbot for immediate agronomic guidance | Fully Implemented |
| 🎤 **Voice & TTS** | In-browser speech recognition and Text-to-Speech audio output via Web Speech API | Client-Side Demo |
| 🌦 **Weather Forecast** | 3-day OpenWeatherMap forecast with automatic mock fallback when offline | Fully Implemented |
| 📥 **Diagnosis Reports** | One-click exportable HTML diagnosis reports ready for field printing | Fully Implemented |

---

## 🧠 Model Architecture & Evaluation Results

### Model Architecture
- **Base Network**: `MobileNetV2` (pre-trained on ImageNet, frozen feature extractor with 2,257,984 non-trainable weights)
- **Input Dimensions**: $(224, 224, 3)$ RGB normalized to $[-1.0, 1.0]$ via $x / 127.5 - 1.0$
- **Classification Head**:
  - `GlobalAveragePooling2D()`
  - `Dense(128, activation='relu')` ($163,968$ trainable parameters)
  - `Dropout(rate=0.2)`
  - `Dense(15, activation='softmax')` ($1,935$ trainable parameters)
- **Total Parameters**: $2,755,695$ (Trainable: $165,903$; Non-trainable: $2,257,984$)
- **Loss Function**: `categorical_crossentropy`
- **Optimizer**: `Adam` ($lr = 0.001$)

### Verified Validation Performance

The model was trained on the curated 15-class PlantVillage corpus ($20,638$ images total; $16,511$ train, $4,127$ validation with `seed=123`). The verified performance metrics on the validation partition are:

| Metric | Result |
| :--- | :--- |
| **Validation Samples** | 4,127 images |
| **Disease Classes** | 15 classes across 3 crops |
| **Validation Accuracy** | **92.63%** |
| **Macro F1-Score** | **91.99%** |
| **Weighted F1-Score** | **92.61%** |
| **Validation Loss** | **0.2318** |

> [!NOTE]  
> **Important Distinction**: These metrics represent performance on the 4,127 PlantVillage **validation set**. They reflect controlled laboratory image distributions (single leaves against plain backgrounds) and do **not** represent independent out-of-distribution test accuracy or wild field conditions.

### Supported Crops & 15 Disease Classes
1. **Bell Pepper** (2 classes): `Bacterial spot`, `Healthy`
2. **Potato** (3 classes): `Early blight`, `Late blight`, `Healthy`
3. **Tomato** (10 classes): `Bacterial spot`, `Early blight`, `Late blight`, `Leaf Mold`, `Septoria leaf spot`, `Spider mites (Two-spotted spider mite)`, `Target Spot`, `Yellow Leaf Curl Virus`, `Mosaic virus`, `Healthy`

---

## 🛠 Technologies Used

- **Framework**: Python 3.9+
- **Deep Learning**: TensorFlow 2.x / Keras 3.x
- **Web UI**: Streamlit 1.35+
- **Data & Image Processing**: NumPy, Pillow
- **String Matching**: RapidFuzz / TheFuzz (treatment and crop database resolution)
- **Weather API**: OpenWeatherMap REST API (HTTPS)
- **Testing**: Python `unittest` standard library (13 passing automated unit tests)

---

## 📁 Repository Structure

```
agroguard/
├── app.py                      ← Main Streamlit dashboard (Scan, Weather, History, AgroBot, Voice, Field Unit)
├── config.py                   ← Path configuration (BASE_DIR), translations, TREATMENT_DB, FERTILIZER_DB
├── model_utils.py              ← Model asset loader, double-softmax prevention, preprocessing
├── services.py                 ← OpenWeatherMap HTTPS integration, HTML reports, feedback logger, chatbot
├── requirements.txt            ← Project dependencies
├── .env.example                ← Environment template (OpenWeatherMap API key)
├── .gitignore                  ← Git ignore rules (excludes caches, virtualenvs, local data)
├── README.md                   ← Project documentation
├── docs/
│   └── PROTOTYPE_STATUS.md     ← Implemented vs. Simulated vs. Proposed capability matrix
├── fusion/                     ← Pure-Python Risk Fusion Package (Decoupled from UI)
│   ├── __init__.py
│   ├── crop_params.py          ← Per-crop agronomic parameter limits (Tomato, Potato, Pepper)
│   ├── patch_analysis.py       ← Experimental 3x3 patch analysis module
│   ├── recommend.py            ← Advisory text generator (English & Tamil non-certainty guidance)
│   ├── risk_engine.py          ← Environmental & disease spread risk rules
│   ├── sensor_sim.py           ← Preset field scenarios & simulated sensor provider
│   ├── sensor_validator.py     ← Range & validity checker (missing/invalid inputs -> UNKNOWN)
│   └── uncertainty.py          ← Uncertainty gating logic (confidence and top-1 vs. top-2 margin)
├── models/
│   ├── agroguard_model.keras   ← Trained MobileNetV2 Keras model (11.6 MB)
│   └── class_indices.json      ← Canonical 15-class index map
├── reports/
│   └── .gitkeep                ← Placeholder for generated reports directory
└── tests/                      ← Automated Unit Test Suite
    ├── __init__.py
    ├── test_class_names.py     ← Verifies 15 classes resolve in treatment/fertilizer databases
    ├── test_risk_engine.py     ← Tests agronomic environmental risk rules
    ├── test_sensor_validator.py← Tests sensor ranges & missing value handling
    └── test_uncertainty.py     ← Tests confidence (<60%) and margin (<15%) gates
```

---

## 🚀 Installation & Setup

### 1. Clone Repository
```bash
git clone https://github.com/Jyothika-06/agroguard.git
cd agroguard
```

### 2. Create and Activate Virtual Environment
```bash
# Windows
python -m venv .venv
.venv\Scripts\activate

# Linux / macOS
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables (Optional)
To enable live 3-day weather forecasting for your location:
```bash
cp .env.example .env
```
Edit `.env` and set your key:
```env
AGROGUARD_WEATHER_API_KEY=your_openweather_api_key_here
AGROGUARD_CITY=Vellore
```
*(If unset, AgroGuard automatically falls back to realistic mock weather data).*

---

## 💻 Running the Application

Launch the Streamlit web dashboard:
```bash
streamlit run app.py
```
Open your browser at `http://localhost:8501`.

### Model File Availability
The pre-trained model `agroguard_model.keras` ($11.6\text{ MB}$) and `class_indices.json` are bundled directly in the `models/` directory. No external model download is required.

---

## 🧪 Running Automated Unit Tests

Run the full automated test suite (13 unit tests covering class resolution, sensor validation, risk rules, and uncertainty gating):

```bash
# Run all tests
python -m unittest discover tests

# Or run individual modules:
python tests/test_class_names.py
python tests/test_uncertainty.py
python tests/test_sensor_validator.py
python tests/test_risk_engine.py
```

---

## ⚠️ Limitations & Responsible-Use Disclaimer

1. **Controlled Dataset Bias**: The MobileNetV2 classifier was trained on single-leaf PlantVillage laboratory photographs against neutral backgrounds. Real field images with complex backgrounds, weeds, shadows, or multiple overlapping leaves may suffer performance degradation.
2. **Prototype Sensor Mode**: All environmental sensor readings (soil moisture, temperature, light, humidity) are currently **simulated** for demonstration purposes. Numerical risk thresholds (`moisture_low_limit`, `heat_stress_limit`, `humidity_spread_limit`) are prototype placeholders requiring localized agronomic field calibration.
3. **Advisory Disclaimer**: AgroGuard AI is a decision-support prototype. Critical farming, chemical treatment, and irrigation decisions should always be cross-checked with certified local agricultural extension officers.
