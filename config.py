"""
AgroGuard AI v4.0 — Configuration
All settings, bilingual text, treatment DB, fertiliser DB.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# BASE_DIR is the root directory of the AgroGuard project
BASE_DIR = Path(__file__).resolve().parent

# Automatically load environment variables from .env located in the project directory
load_dotenv(BASE_DIR / ".env")

# ─── API / paths ──────────────────────────────────────────────────────────────
# NOTE: WEATHER_API_KEY is retrieved from the AGROGUARD_WEATHER_API_KEY environment variable.
WEATHER_API_KEY     = os.getenv("AGROGUARD_WEATHER_API_KEY", "")
CITY                = os.getenv("AGROGUARD_CITY", "Vellore")
IMG_SIZE            = (224, 224)
MODEL_PATH          = str(BASE_DIR / "models" / "agroguard_model.keras")
CLASS_INDICES_PATH  = str(BASE_DIR / "models" / "class_indices.json")
FEEDBACK_FILE       = str(BASE_DIR / "feedback_data.csv")
SUPPORTED_CROPS     = ["Tomato", "Potato", "Pepper"]

# ─── Uncertainty Thresholds (Prototype Placeholders) ──────────────────────────
# Note: These values are prototype thresholds requiring field calibration and tuning
# on your own test images after the double-softmax fix. They are NOT scientifically
# or agronomically validated.
CONF_THRESHOLD   = 60.0  # % confidence placeholder requiring field calibration
MARGIN_THRESHOLD = 15.0  # % margin (top1 - top2) placeholder requiring field calibration

# ─── English strings ──────────────────────────────────────────────────────────
EN = {
    "app_title_short":  "AGROGUARD AI",
    "app_title":        "🌱 AgroGuard: Intelligent Crop Protection",
    "subtitle":         "Tomato · Potato · Bell Pepper",
    "tagline":          "AI-Powered Disease Detection for Sustainable Farming",
    "upload_prompt":    "Upload a leaf image to begin diagnosis",
    "choose_image":     "Choose leaf images (JPG / PNG / JPEG) — multi-upload supported",
    "healthy_plant":    "Healthy Plant",
    "disease_detected": "Disease Detected",
    "treatment_plan":   "Treatment Plan",
    "chemical_control": "Chemical",
    "organic_control":  "Organic",
    "precautions":      "Precaution",
    "apply_every":      "Apply Every",
    "care_tips":        "Plant Care Tips",
    "water_morning":    "Water plants in early morning only",
    "proper_spacing":   "Maintain 24–36 inch spacing between plants",
    "organic_fertilizer":"Apply organic fertiliser monthly",
    "regular_inspection":"Inspect leaves weekly for early detection",
    "crop_rotation":    "Rotate crops annually to break disease cycles",
    "fertilizer_recommendation": "Fertiliser Plan",
    "nitrogen":         "Nitrogen (N)",
    "phosphorus":       "Phosphorus (P)",
    "potassium":        "Potassium (K)",
    "application":      "Application",
    "export_report":    "Download HTML Diagnosis Report",
    "feedback":         "Diagnosis Feedback",
    "feedback_correct": "✅  Correct",
    "feedback_wrong":   "❌  Incorrect",
    "feedback_saved":   "Feedback saved — thank you!",
    "chat_placeholder": "Ask about diseases, treatment, fertiliser…",
    "bot_greeting":     ("👋 Hello! I'm AgroBot, your AI farming assistant. "
                         "I can help with disease identification, treatment plans, fertiliser recommendations, "
                         "and weather advice. What would you like to know today?"),
    "voice_title":      "Voice Assistant",
    "voice_sub":        "Speak in English or Tamil — Chrome browser recommended",
    "tts_placeholder":  "Type any text here to hear it spoken aloud…",
    "footer":           "AgroGuard AI | Smart Farming for Better Yields",
    "disclaimer":       "⚠ Always consult local agricultural experts for critical decisions",
    "emergency":        "📞 Emergency: contact your local agricultural extension office",
}

# ─── Tamil strings ────────────────────────────────────────────────────────────
TA = {
    "app_title_short":  "அக்ரோகார்ட் AI",
    "app_title":        "🌱 அக்ரோகார்ட்: பயிர் பாதுகாப்பு அமைப்பு",
    "subtitle":         "தக்காளி · உருளைக்கிழங்கு · மிளகாய்",
    "tagline":          "செயற்கை நுண்ணறிவு மூலம் பயிர் நோய் கண்டறிதல்",
    "upload_prompt":    "நோய் கண்டறிய இலைப் படத்தை பதிவேற்றவும்",
    "choose_image":     "இலை படங்களை தேர்வு செய்யவும் (JPG / PNG) — பல படங்கள் ஆதரிக்கப்படுகின்றன",
    "healthy_plant":    "ஆரோக்கியமான செடி",
    "disease_detected": "நோய் கண்டறியப்பட்டது",
    "treatment_plan":   "சிகிச்சை திட்டம்",
    "chemical_control": "இரசாயன கட்டுப்பாடு",
    "organic_control":  "உயிரி கட்டுப்பாடு",
    "precautions":      "முன்னெச்சரிக்கை",
    "apply_every":      "தெளிக்கும் இடைவெளி",
    "care_tips":        "செடி பராமரிப்பு குறிப்புகள்",
    "water_morning":    "காலை நேரத்தில் மட்டுமே தண்ணீர் பாய்ச்சவும்",
    "proper_spacing":   "செடிகளுக்கிடையே 60–90 செமீ இடைவெளி பராமரிக்கவும்",
    "organic_fertilizer":"மாதந்தோறும் உயிரி உரம் இடவும்",
    "regular_inspection":"வாரந்தோறும் இலைகளை ஆய்வு செய்யவும்",
    "crop_rotation":    "ஆண்டுதோறும் பயிர் சுழற்சி முறையை பின்பற்றவும்",
    "fertilizer_recommendation": "உர பரிந்துரை",
    "nitrogen":         "நைட்ரஜன் (N)",
    "phosphorus":       "பாஸ்பரஸ் (P)",
    "potassium":        "பொட்டாசியம் (K)",
    "application":      "பயன்படுத்தும் முறை",
    "export_report":    "HTML அறிக்கையை பதிவிறக்கம் செய்யவும்",
    "feedback":         "கண்டறிதல் மதிப்பீடு",
    "feedback_correct": "✅  சரி",
    "feedback_wrong":   "❌  தவறு",
    "feedback_saved":   "கருத்து சேமிக்கப்பட்டது — நன்றி!",
    "chat_placeholder": "நோய், சிகிச்சை, உரம் பற்றி கேளுங்கள்…",
    "bot_greeting":     ("வணக்கம்! நான் அக்ரோபாட், உங்கள் AI வேளாண்மை உதவியாளர். "
                         "நோய் கண்டறிதல், சிகிச்சை, உரம், வானிலை பற்றி உதவ இங்கிருக்கிறேன். "
                         "என்ன கேட்க விரும்புகிறீர்கள்?"),
    "voice_title":      "குரல் உதவியாளர்",
    "voice_sub":        "ஆங்கிலம் அல்லது தமிழில் பேசுங்கள் — Chrome பயன்படுத்தவும்",
    "tts_placeholder":  "இங்கே எந்த உரையையும் தட்டச்சு செய்யுங்கள், கேட்கலாம்…",
    "footer":           "அக்ரோகார்ட் AI | சிறந்த விளைச்சலுக்கான ஸ்மார்ட் வேளாண்மை",
    "disclaimer":       "⚠ முக்கிய முடிவுகளுக்கு உள்ளூர் வேளாண்மை நிபுணர்களை அணுகவும்",
    "emergency":        "📞 அவசரம்: உள்ளூர் வேளாண்மை அலுவலகத்தை தொடர்பு கொள்ளவும்",
}

# ─── Treatment database ───────────────────────────────────────────────────────
TREATMENT_DB = {
    "Tomato___Bacterial_spot": {
        "pesticide": "Copper bactericide (Kocide 2000) — follow product label / consult local agricultural officer",
        "organic":   "Garlic extract + Neem oil spray (follow label guidance)",
        "precaution": "Avoid overhead irrigation; remove infected leaves",
        "severity":   "High",
        "treatment_days": "Every 7–10 days",
    },
    "Tomato___Early_blight": {
        "pesticide": "Chlorothalonil or Mancozeb — follow product label / consult local agricultural officer",
        "organic":   "Neem oil + Baking soda spray (follow label guidance)",
        "precaution": "Mulch around base; water at ground level only",
        "severity":   "Medium",
        "treatment_days": "Every 7–10 days",
    },
    "Tomato___Late_blight": {
        "pesticide": "Metalaxyl + Mancozeb (Ridomil Gold) — follow product label / consult local agricultural officer",
        "organic":   "Copper hydroxide spray — follow product label / consult local agricultural officer",
        "precaution": "Avoid moisture on leaves; improve drainage urgently",
        "severity":   "Critical",
        "treatment_days": "Immediately — within 24–48 hours",
    },
    "Tomato___Leaf_Mold": {
        "pesticide": "Chlorothalonil or Azoxystrobin — follow product label / consult local agricultural officer",
        "organic":   "Neem oil spray (follow label guidance); increase greenhouse ventilation",
        "precaution": "Reduce humidity; space plants further apart",
        "severity":   "Medium",
        "treatment_days": "Every 7–10 days",
    },
    "Tomato___Septoria_leaf_spot": {
        "pesticide": "Chlorothalonil or Copper fungicide — follow product label / consult local agricultural officer",
        "organic":   "Neem oil + Baking soda spray, weekly",
        "precaution": "Remove and destroy infected lower leaves",
        "severity":   "High",
        "treatment_days": "Every 7–10 days",
    },
    "Tomato___Spider_mites Two-spotted_spider_mite": {
        "pesticide": "Abamectin or Spinosad — follow product label / consult local agricultural officer",
        "organic":   "Neem oil + insecticidal soap spray (follow label guidance)",
        "precaution": "Remove heavily infested leaves; increase humidity",
        "severity":   "Medium",
        "treatment_days": "Every 3–5 days",
    },
    "Tomato___Target_Spot": {
        "pesticide": "Azoxystrobin or Chlorothalonil — follow product label / consult local agricultural officer",
        "organic":   "Copper spray + neem oil (follow label guidance)",
        "precaution": "Avoid overcrowding; ensure good air flow",
        "severity":   "Medium",
        "treatment_days": "Every 7–10 days",
    },
    "Tomato___Tomato_Yellow_Leaf_Curl_Virus": {
        "pesticide": "Imidacloprid (controls whitefly vector) — follow product label / consult local agricultural officer",
        "organic":   "Neem oil for whiteflies; install yellow sticky traps",
        "precaution": "Remove infected plants immediately; use reflective mulch",
        "severity":   "Critical",
        "treatment_days": "Manage vector continuously",
    },
    "Tomato___Tomato_mosaic_virus": {
        "pesticide": "No chemical cure — prevention only",
        "organic":   "Remove and destroy infected plants immediately",
        "precaution": "Wash hands before handling; sanitise all tools",
        "severity":   "Critical",
        "treatment_days": "Immediate removal required",
    },
    "Tomato___healthy": {
        "pesticide": "No treatment needed",
        "organic":   "Compost tea application for immunity boost",
        "precaution": "Continue regular monitoring weekly",
        "severity":   "None",
        "treatment_days": "N/A",
    },
    "Potato___Early_blight": {
        "pesticide": "Mancozeb or Chlorothalonil — follow product label / consult local agricultural officer",
        "organic":   "Neem oil + Trichoderma bio-fungicide (follow label guidance)",
        "precaution": "Crop rotation every 4 years; avoid infected seed",
        "severity":   "Medium",
        "treatment_days": "Every 7–10 days",
    },
    "Potato___Late_blight": {
        "pesticide": "Metalaxyl + Mancozeb (Ridomil Gold) — follow product label / consult local agricultural officer",
        "organic":   "Copper hydroxide spray — follow product label / consult local agricultural officer",
        "precaution": "Use certified disease-free seed tubers; hilling",
        "severity":   "Critical",
        "treatment_days": "Immediately",
    },
    "Potato___healthy": {
        "pesticide": "No treatment needed",
        "organic":   "Apply well-rotted compost at earthing-up",
        "precaution": "Regular hilling to prevent greening",
        "severity":   "None",
        "treatment_days": "N/A",
    },
    "Pepper__bell___Bacterial_spot": {
        "pesticide": "Copper bactericide + Streptomycin — follow product label / consult local agricultural officer",
        "organic":   "Neem oil + Pseudomonas fluorescens (follow label guidance)",
        "precaution": "Avoid overhead watering; use pathogen-free seeds",
        "severity":   "High",
        "treatment_days": "Every 7–10 days",
    },
    "Pepper__bell___healthy": {
        "pesticide": "No treatment needed",
        "organic":   "Balanced fertilisation + compost",
        "precaution": "Maintain proper plant spacing",
        "severity":   "None",
        "treatment_days": "N/A",
    },
}

# ─── Fertiliser database ──────────────────────────────────────────────────────
# ─── Fertiliser database ──────────────────────────────────────────────────────
FERTILIZER_DB = {
    "Tomato": {
        "healthy": {
            "N": "Standard Nitrogen (Urea) — follow local soil test / agricultural officer guidance",
            "P": "Standard Phosphorus (SSP) — follow local soil test / agricultural officer guidance",
            "K": "Standard Potassium (MOP) — follow local soil test / agricultural officer guidance",
            "application": "Basal at planting; top-dress per local agricultural extension schedule.",
        },
        "Bacterial spot": {
            "N": "Reduce Nitrogen application (excess N worsens spread — consult local officer)",
            "P": "Boost Phosphorus (consult local officer for soil drench schedule)",
            "K": "Boost Potassium for plant defense (consult local officer)",
            "application": "Boost P & K; soil drench method preferred.",
        },
        "Early blight": {
            "N": "Balanced Nitrogen — follow local extension guidelines",
            "P": "Standard Phosphorus — follow local soil test recommendation",
            "K": "Potassium-rich fertilization + organic neem cake soil amendment",
            "application": "Apply K-rich mix; add neem cake to soil per label guidance.",
        },
        "Late blight": {
            "N": "Reduce Nitrogen application (excess N worsens late blight)",
            "P": "Boost Phosphorus for root health & immunity (consult local officer)",
            "K": "Boost Potassium for plant immunity (consult local officer)",
            "application": "Skip N fertiliser; focus on P & K immunity under expert guidance.",
        },
        "Leaf Mold": {
            "N": "Reduce Nitrogen application (consult local officer)",
            "P": "Standard Phosphorus — follow local soil test recommendation",
            "K": "Boost Potassium (consult local officer)",
            "application": "K-rich mix; avoid overhead watering.",
        },
        "Septoria leaf spot": {
            "N": "Balanced Nitrogen (consult local officer)",
            "P": "Standard Phosphorus — follow local soil test recommendation",
            "K": "Standard Potassium — follow local soil test recommendation",
            "application": "Balanced nutrition; ensure proper drainage.",
        },
        "Spider mites Two-spotted spider mite": {
            "N": "Moderate Nitrogen — avoid excess growth",
            "P": "Standard Phosphorus — follow local soil test recommendation",
            "K": "Boost Potassium — follow local soil test recommendation",
            "application": "Foliar K-rich spray; maintain humidity.",
        },
        "Target Spot": {
            "N": "Balanced Nitrogen — follow local extension guidelines",
            "P": "Standard Phosphorus — follow local soil test recommendation",
            "K": "Standard Potassium — follow local soil test recommendation",
            "application": "Balanced; avoid plant overcrowding.",
        },
        "Tomato Yellow Leaf Curl Virus": {
            "N": "Moderate Nitrogen — avoid vector attraction",
            "P": "Boost Phosphorus for root health & vigor",
            "K": "Boost Potassium — follow local officer recommendation",
            "application": "P-rich for root health; remove infected plants first.",
        },
        "Tomato mosaic virus": {
            "N": "Moderate Nitrogen (consult local officer)",
            "P": "Standard Phosphorus — follow local soil test recommendation",
            "K": "Standard Potassium — follow local soil test recommendation",
            "application": "Balanced; remove diseased plants first.",
        },
    },
    "Potato": {
        "healthy": {
            "N": "Standard Nitrogen (Urea) — follow local soil test recommendation",
            "P": "Standard Phosphorus (SSP) — follow local soil test recommendation",
            "K": "Standard Potassium (MOP) — follow local soil test recommendation",
            "application": "At planting + earthing-up dose per local extension schedule.",
        },
        "Early blight": {
            "N": "Reduce Nitrogen application (consult local officer)",
            "P": "Standard Phosphorus — follow local soil test recommendation",
            "K": "Boost Potassium for tuber immunity (consult local officer)",
            "application": "Boost K; avoid overhead irrigation.",
        },
        "Late blight": {
            "N": "Reduce Nitrogen application (excess N worsens blight)",
            "P": "Boost Phosphorus — follow local officer guidance",
            "K": "Boost Potassium — follow local officer guidance",
            "application": "Heavy P & K; certified disease-free tubers only.",
        },
    },
    "Pepper": {
        "healthy": {
            "N": "Standard Nitrogen (Urea) — follow local soil test recommendation",
            "P": "Standard Phosphorus (SSP) — follow local soil test recommendation",
            "K": "Standard Potassium (MOP) — follow local soil test recommendation",
            "application": "Split doses: planting + flowering stage.",
        },
        "Bacterial spot": {
            "N": "Reduce Nitrogen application (consult local officer)",
            "P": "Boost Phosphorus — follow local officer guidance",
            "K": "Boost Potassium — follow local officer guidance",
            "application": "Boost P & K; avoid overhead watering.",
        },
    },
}