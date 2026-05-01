
Action: file_editor create /app/agroguard/README.md --file-text "# 🌱 AgroGuard AI v5.0 — Intelligent Crop Protection System

> AI-powered bilingual plant-disease detection for Tomato, Potato & Bell Pepper crops.

---

## ✨ What's new in v5.0

| Area | Fix / improvement |
|------|------|
| 💬 Chat + Voice | Merged into a single **AgroBot** tab. Mic button feeds straight into chat; the bot's latest reply is read aloud automatically (TTS). |
| 🇮🇳 Tamil chatbot | Rewritten matcher — every Tamil quick-question now returns a distinct, correct answer (no more identical replies). |
| 🎤 Voice | Fixed — uses the browser's Web Speech API, posts the transcript back into Streamlit via query param. |
| 🎨 Design | Vibrant colourful theme with smooth animations, gradient headers, hover lifts, responsive grid. |
| 🌓 Light/Dark | Contrast issues resolved — all text readable in both modes. |
| 🧹 Content | Implementation details moved out of main tabs into a dedicated **About** tab. |
| 🧪 Demo mode | App now runs even without the trained model (uses deterministic mocked predictions). |

---

## 🚀 Quick Start

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. (Optional) Drop your trained model
#    models/agroguard_model.keras
#    models/class_indices.json
#    — without these, the app runs in demo mode.

# 3. Run
streamlit run app.py
```

Open http://localhost:8501 in **Google Chrome** for full voice support.

---

## 📁 File structure

```
agroguard/
├── app.py              ← Streamlit UI (5 tabs)
├── model_utils.py      ← Model loading + demo-mode fallback
├── services.py         ← Weather, treatment DB, bilingual chatbot
├── config.py           ← Strings, treatment DB, fertiliser DB
├── requirements.txt
├── models/
│   ├── agroguard_model.keras   (your trained CNN — not included)
│   └── class_indices.json
├── feedback_data.csv   (auto-generated on first feedback)
└── README.md
```

---

## 🧠 Model info

| Property | Value |
|----------|-------|
| Architecture | CNN (MobileNetV2 / EfficientNet recommended) |
| Input | 224 × 224 RGB |
| Normalisation | `pixel / 127.5 − 1.0` |
| Classes | 15 (Tomato 10, Potato 3, Pepper 2) |
| Dataset | PlantVillage |

`class_indices.json` may be either direction:

```json
{\"0\": \"Tomato___Bacterial_spot\", \"1\": \"Tomato___Early_blight\"}
```
or
```json
{\"Tomato___Bacterial_spot\": 0, \"Tomato___Early_blight\": 1}
```

---

## 🌐 Weather

Uses the OpenWeatherMap 5-day/3-hour forecast API.
Set your key in `config.py`:

```python
WEATHER_API_KEY = \"your_key_here\"
CITY            = \"YourCity\"
```

Without a key the app falls back to realistic mock forecasts.

---

## 🎤 Voice assistant — how it works

1. Click the **🎤 Mic** button in the AgroBot tab.
2. Speak in English or Tamil (choose from the sidebar).
3. The Web Speech API transcribes your speech.
4. The transcript is sent back to Streamlit via `?voice_msg=...`.
5. AgroBot generates a reply and speaks it aloud through the browser TTS.

Works best in **Google Chrome** (Edge also supported). Safari has partial support.

---

## 🆘 Troubleshooting

| Symptom | Fix |
|---------|-----|
| \"Voice not supported\" | Use Chrome/Edge — Firefox does not implement Web Speech. |
| Demo mode banner showing | Place `agroguard_model.keras` + `class_indices.json` in `models/`. |
| Tamil reply repeats | Already fixed in v5.0 — update `services.py`. |
| Light-mode white-on-white | Already fixed in v5.0 — update `app.py` CSS. |

---

## 📞 Support

AgroGuard is an AI aid, **not** a replacement for agricultural expertise.
For critical decisions always consult your local agricultural extension office.

Built with 💚 for farmers.
"
Observation: Create successful: /app/agroguard/README.md