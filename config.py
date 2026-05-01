"""
AgroGuard AI v5.0 - Configuration
Constants, bilingual strings, treatment DB, fertilizer DB.
"""

# API and paths
WEATHER_API_KEY = "e0b6e39863d5960388618a1210b8afa1"  # Replace with your OpenWeatherMap API key
CITY = "Vellore"
IMG_SIZE = (224, 224)
MODEL_PATH = "models/agroguard_model.keras"
CLASS_INDICES_PATH = "models/class_indices.json"
FEEDBACK_FILE = "feedback_data.csv"
SUPPORTED_CROPS = ["Tomato", "Potato", "Pepper"]

# English strings
EN = {
    "app_title_short": "AGROGUARD",
    "app_title": "AgroGuard: Intelligent Crop Protection",
    "subtitle": "Tomato - Potato - Bell Pepper",
    "tagline": "AI-Powered Plant Disease Detection",
    "upload_prompt": "Upload a clear leaf image to begin diagnosis",
    "choose_image": "Choose leaf images (JPG / PNG) - multi-upload supported",
    "healthy_plant": "Healthy Plant",
    "disease_detected": "Disease Detected",
    "treatment_plan": "Treatment Plan",
    "fertilizer_recommendation": "Fertilizer Plan",
    "nitrogen": "Nitrogen (N)",
    "phosphorus": "Phosphorus (P)",
    "potassium": "Potassium (K)",
    "application": "Application",
    "water_morning": "Water plants in early morning only",
    "proper_spacing": "Maintain 60-90 cm spacing between plants",
    "organic_fertilizer": "Apply organic fertilizer monthly",
    "regular_inspection": "Inspect leaves weekly",
    "crop_rotation": "Rotate crops annually to break disease cycles",
    "feedback": "Feedback",
    "feedback_correct": "Correct",
    "feedback_wrong": "Wrong",
    "feedback_saved": "Thank you! Feedback saved.",
    "tab_scan": "Scan",
    "tab_weather": "Weather",
    "tab_history": "History",
    "tab_chat": "Chat",
    "tab_about": "About",
    "bot_greeting": "Hello! I'm AgroBot, your AI crop assistant. Ask me about disease prevention, treatment plans, or weather farming tips.",
    "chat_title": "Chat with AgroBot",
    "chat_placeholder": "Ask about treatments, fertilizers, weather...",
    "send": "Send",
    "voice_hint": "Or tap the mic to speak (voice recognition available in English)",
    "quick_questions": "Quick Questions",
    "clear": "Clear",
    "export_report": "Export Report",
    "footer": "AgroGuard AI - Smart farming for sustainable agriculture",
    "disclaimer": "Always consult local agricultural experts for critical decisions.",
}

# Tamil strings
TA = {
    "app_title_short": "AGROGUARD",
    "app_title": "AgroGuard: மேம்பட்ட பயிர் பாதுகாப்பு",
    "subtitle": "தக்காளி - உருளைக்கிழங்கு - குடைமிளகு",
    "tagline": "AI-இயக்கிய செடி நோய் கண்டறிதல்",
    "upload_prompt": "தெளிவான இலை பட்டைப்படத்தை பதிவேற்ற வேண்டும்",
    "choose_image": "இலை பட்டைப்படங்களை தேர்ந்தெடுக்கவும் (JPG / PNG)",
    "healthy_plant": "ஆரோக்கியமான செடி",
    "disease_detected": "நோய் கண்டறியப்பட்டது",
    "treatment_plan": "சிகிச்சை திட்டம்",
    "fertilizer_recommendation": "உரம் பரிந்துrை",
    "nitrogen": "நைட்ரஜன் (N)",
    "phosphorus": "பாஸ்பரஸ் (P)",
    "potassium": "பொட்டாசியம் (K)",
    "application": "பயன்பாடு",
    "water_morning": "அதிகாலையில் மட்டுமே நீர் ஊற்றவும்",
    "proper_spacing": "செடிகளுக்கு இடையே 60-90 செ.மீ இடைவெளி பாதுகாக்கவும்",
    "organic_fertilizer": "மாதாந்திர உயிரியல் உரம் பயன்படுத்தவும்",
    "regular_inspection": "வாரத்தில் இலைகளை பரிசோதிக்கவும்",
    "crop_rotation": "பயிற்சி சுழற்சி நோய்களை உடைக்க உதவுகிறது",
    "feedback": "கருத்து",
    "feedback_correct": "சரி",
    "feedback_wrong": "தவறு",
    "feedback_saved": "நன்றி! கருத்து சேமிக்கப்பட்டது.",
    "tab_scan": "ஸ்கேன்",
    "tab_weather": "வானிலை",
    "tab_history": "வரலாறு",
    "tab_chat": "சேட்",
    "tab_about": "பற்றி",
    "bot_greeting": "வணக்கம்! நான் AgroBot, உங்கள் AI விவசாய உதவி. நோய் தடுப்பு, சிகிச்சை திட்டங்கள், வானிலை வேளாண்மை குறிப்புகள் பற்றி கேளுங்கள்.",
    "chat_title": "AgroBot உடன் சேட் செய்யவும்",
    "chat_placeholder": "சிகிச்சை, உரங்கள், வானிலை பற்றி கேளுங்கள்...",
    "send": "அனுப்பவும்",
    "voice_hint": "அல்லது மைக்கைத் தட்டி பேசவும்",
    "quick_questions": "விரைவு கேள்விகள்",
    "clear": "மீட்டமைக்க",
    "export_report": "அறிக்கையை ஏற்றுமதி செய்க",
    "footer": "AgroGuard AI - நிலையான வேளாண்மைக்கான ஸ்மார்ட் விவசாயம்",
    "disclaimer": "முக்கிய முடிவுகளுக்கு உள்ளூர் வேளாண்மை நிபுணர்களை நிச்சயமாக ஆலோசிக்கவும்.",
}

# Treatment database
TREATMENT_DB = {
    "Tomato___Bacterial_spot": {
        "severity": "High",
        "pesticide": "Copper hydroxide 50% WP",
        "organic": "Bordeaux mixture (1%)",
        "precaution": "Avoid overhead watering",
        "treatment_days": "10-14 days",
    },
    "Tomato___Early_blight": {
        "severity": "High",
        "pesticide": "Mancozeb 75% WP",
        "organic": "Sulfur dust 90%",
        "precaution": "Remove lower infected leaves",
        "treatment_days": "7-10 days",
    },
    "Tomato___Late_blight": {
        "severity": "Critical",
        "pesticide": "Cymoxanil + Mancozeb",
        "organic": "Bordeaux mixture (1%)",
        "precaution": "Spray at first sign of disease",
        "treatment_days": "5-7 days",
    },
    "Tomato___Leaf_Mold": {
        "severity": "Medium",
        "pesticide": "Azoxystrobin 23% SC",
        "organic": "Sulfur dust 90%",
        "precaution": "Improve ventilation",
        "treatment_days": "7-10 days",
    },
    "Tomato___Septoria_leaf_spot": {
        "severity": "Medium",
        "pesticide": "Mancozeb 75% WP",
        "organic": "Sulfur dust 90%",
        "precaution": "Avoid overhead watering",
        "treatment_days": "7-10 days",
    },
    "Tomato___Spider_mites": {
        "severity": "Medium",
        "pesticide": "Abamectin 1.8% EC",
        "organic": "Neem oil 3%",
        "precaution": "Maintain high humidity",
        "treatment_days": "5-7 days",
    },
    "Tomato___Target_Spot": {
        "severity": "High",
        "pesticide": "Mancozeb 75% WP",
        "organic": "Sulfur dust 90%",
        "precaution": "Remove infected leaves",
        "treatment_days": "7-10 days",
    },
    "Tomato___Tomato_Yellow_Leaf_Curl_Virus": {
        "severity": "Critical",
        "pesticide": "Control whiteflies with Imidacloprid",
        "organic": "Yellow sticky traps + neem oil",
        "precaution": "Remove infected plants immediately",
        "treatment_days": "Continuous monitoring",
    },
    "Tomato___Tomato_mosaic_virus": {
        "severity": "High",
        "pesticide": "Control aphids with Imidacloprid",
        "organic": "Neem oil + yellow sticky traps",
        "precaution": "Remove infected plants",
        "treatment_days": "Continuous",
    },
    "Tomato___healthy": {
        "severity": "None",
        "pesticide": "No treatment needed",
        "organic": "Continue preventive sprays",
        "precaution": "Maintain good plant health",
        "treatment_days": "N/A",
    },
    "Potato___Early_blight": {
        "severity": "High",
        "pesticide": "Mancozeb 75% WP",
        "organic": "Sulfur dust 90%",
        "precaution": "Remove infected leaves immediately",
        "treatment_days": "7-10 days",
    },
    "Potato___Late_blight": {
        "severity": "Critical",
        "pesticide": "Metalaxyl + Mancozeb",
        "organic": "Bordeaux mixture (1%)",
        "precaution": "Spray preventively during rains",
        "treatment_days": "5-7 days",
    },
    "Potato___healthy": {
        "severity": "None",
        "pesticide": "No treatment needed",
        "organic": "Continue monitoring",
        "precaution": "Ensure proper drainage",
        "treatment_days": "N/A",
    },
    "Pepper__bell___Bacterial_spot": {
        "severity": "Medium",
        "pesticide": "Copper oxychloride 50% WP",
        "organic": "Bordeaux mixture (1%)",
        "precaution": "Avoid wet foliage",
        "treatment_days": "10-14 days",
    },
    "Pepper__bell___healthy": {
        "severity": "None",
        "pesticide": "No treatment needed",
        "organic": "Apply preventive neem oil",
        "precaution": "Weed control",
        "treatment_days": "N/A",
    },
}

# Fertilizer recommendations database
FERTILIZER_DB = {
    ("Tomato", "Healthy"): {
        "N": "150-200 kg/ha",
        "P": "60-80 kg/ha",
        "K": "100-150 kg/ha",
        "application": "Split doses every 15 days",
    },
    ("Tomato", "Early blight"): {
        "N": "120-150 kg/ha",
        "P": "80-100 kg/ha",
        "K": "150-200 kg/ha (increase K)",
        "application": "K-rich fertilizer every 10 days",
    },
    ("Tomato", "Late blight"): {
        "N": "100-120 kg/ha",
        "P": "100-120 kg/ha",
        "K": "200-250 kg/ha (critical)",
        "application": "Frequent K applications",
    },
    ("Potato", "Healthy"): {
        "N": "120-150 kg/ha",
        "P": "80-100 kg/ha",
        "K": "150-180 kg/ha",
        "application": "Pre-planting + split doses",
    },
    ("Potato", "Late blight"): {
        "N": "100-120 kg/ha",
        "P": "100-120 kg/ha",
        "K": "200-250 kg/ha (critical)",
        "application": "K chloride every 7-10 days",
    },
    ("Pepper", "Healthy"): {
        "N": "100-120 kg/ha",
        "P": "60-80 kg/ha",
        "K": "80-100 kg/ha",
        "application": "Split doses every 20 days",
    },
}
