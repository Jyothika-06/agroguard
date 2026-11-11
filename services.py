"""
AgroGuard AI v4.0 — Services
Weather, treatment/fertiliser, report, feedback, chatbot (EN + Tamil).
"""

import os, csv, requests
from datetime import datetime, timedelta
from thefuzz import process
from config import WEATHER_API_KEY, CITY, TREATMENT_DB, FERTILIZER_DB, FEEDBACK_FILE


# ─── WEATHER ──────────────────────────────────────────────────────────────────
def _mock_forecast():
    today = datetime.now()
    samples = [
        {"sky": "Clear",  "temp": 28.5, "hum": 62},
        {"sky": "Clouds", "temp": 27.8, "hum": 71},
        {"sky": "Rain",   "temp": 25.5, "hum": 87},
    ]
    return [{"date": (today + timedelta(days=i)).strftime("%Y-%m-%d"),
             **s} for i, s in enumerate(samples)]


def get_3day_forecast():
    if not WEATHER_API_KEY or WEATHER_API_KEY == "YOUR_API_KEY_HERE":
        return _mock_forecast()
    try:
        url = (f"https://api.openweathermap.org/data/2.5/forecast"
               f"?q={CITY}&appid={WEATHER_API_KEY}&units=metric")
        resp = requests.get(url, timeout=8)
        if resp.status_code != 200:
            return _mock_forecast()
        data = resp.json()
        result, seen = [], set()
        for item in data.get("list", []):
            date = item["dt_txt"].split(" ")[0]
            if date not in seen and len(result) < 3:
                seen.add(date)
                result.append({"date": date,
                                "temp": item["main"]["temp"],
                                "hum":  item["main"]["humidity"],
                                "sky":  item["weather"][0]["main"]})
        return result or _mock_forecast()
    except Exception:
        return _mock_forecast()


def get_weather_precaution(hum, sky, temp, lang="en"):
    sky_l = (sky or "").lower()
    if lang == "en":
        if hum > 80:           return "⚠️ Fungal risk — boost ventilation"
        elif "rain" in sky_l:  return "⚠️ Rain — delay fertiliser spray"
        elif temp > 32:        return "⚠️ Heat stress — irrigate more"
        elif "cloud" in sky_l: return "☁️ Good day for transplanting"
        elif "clear" in sky_l: return "☀️ Ideal day for pesticide spray"
        else:                  return "✅ Normal conditions"
    else:
        if hum > 80:           return "⚠️ பூஞ்சை அபாயம் — காற்றோட்டம் அதிகரிக்கவும்"
        elif "rain" in sky_l:  return "⚠️ மழை — உரம் தெளிக்க வேண்டாம்"
        elif temp > 32:        return "⚠️ வெப்பம் — நீர்பாசனம் அதிகரிக்கவும்"
        elif "cloud" in sky_l: return "☁️ நாற்று நடவு செய்ய ஏற்றது"
        elif "clear" in sky_l: return "☀️ மருந்து தெளிக்க சிறந்த நாள்"
        else:                  return "✅ சாதாரண நிலை"


# ─── TREATMENT / FERTILISER ───────────────────────────────────────────────────
_DEF_TRT = {
    "pesticide": "Consult your local agricultural officer",
    "organic":   "Apply neem oil spray (follow label guidance) as preventive",
    "precaution":"Isolate infected plants; seek expert advice",
    "severity":  "Unknown",
    "treatment_days": "Consult expert",
}
_DEF_FERT = {
    "N": "Consult local officer", "P": "Consult local officer",
    "K": "Consult local officer", "application": "Seek expert advice",
}


def get_treatment(disease_name):
    from model_utils import normalize_class_name
    norm_name = normalize_class_name(disease_name)
    if norm_name in TREATMENT_DB:
        return TREATMENT_DB[norm_name]
    if disease_name in TREATMENT_DB:
        return TREATMENT_DB[disease_name]
    best = process.extractOne(norm_name, list(TREATMENT_DB.keys()))
    return TREATMENT_DB[best[0]] if best and best[1] > 70 else _DEF_TRT


def get_fertilizer(crop, disease):
    from model_utils import normalize_class_name
    norm_name = normalize_class_name(disease)
    crop_db = FERTILIZER_DB.get(crop, {})
    if not crop_db:
        return _DEF_FERT
    if norm_name in crop_db:
        return crop_db[norm_name]
    if disease in crop_db:
        return crop_db[disease]

    # Extract condition part (e.g. Tomato___Bacterial_spot -> Bacterial spot)
    cond = norm_name.split("___")[-1] if "___" in norm_name else norm_name
    cond_clean = cond.replace("_", " ").strip()
    for key in crop_db:
        if key.lower() == cond_clean.lower() or key.lower() == cond.lower():
            return crop_db[key]

    best = process.extractOne(disease, list(crop_db.keys()))
    if best and best[1] > 65:
        return crop_db[best[0]]
    return crop_db.get("healthy", _DEF_FERT)



# ─── FEEDBACK ─────────────────────────────────────────────────────────────────
def save_feedback(file_name, predicted, comment, correct) -> bool:
    row = {"timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
           "file_name": file_name, "predicted_disease": predicted,
           "user_comment": comment, "was_correct": correct}
    try:
        os.makedirs(os.path.dirname(os.path.abspath(FEEDBACK_FILE)), exist_ok=True)
        exists = os.path.isfile(FEEDBACK_FILE) and os.path.getsize(FEEDBACK_FILE) > 0
        with open(FEEDBACK_FILE, "a", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=list(row.keys()))
            if not exists:
                w.writeheader()
            w.writerow(row)
        return True
    except Exception as e:
        print(f"Warning: Failed to save feedback to {FEEDBACK_FILE}: {e}")
        return False


# ─── REPORT ───────────────────────────────────────────────────────────────────
def generate_report(disease, crop, confidence, treatment, fertiliser, comment=""):
    ts      = datetime.now().strftime("%B %d, %Y at %I:%M %p")
    sev     = treatment.get("severity", "Unknown")
    is_sick = "healthy" not in disease.lower()
    card    = "disease" if is_sick else "healthy"

    fert_sec = ""
    if fertiliser:
        fert_sec = f"""
        <div class="section fertilizer">
          <h2>🌱 Fertiliser Recommendations</h2>
          <div class="g2">
            <div class="it"><div class="lb">Nitrogen (N)</div><div class="vl">{fertiliser.get('N','—')}</div></div>
            <div class="it"><div class="lb">Phosphorus (P)</div><div class="vl">{fertiliser.get('P','—')}</div></div>
            <div class="it"><div class="lb">Potassium (K)</div><div class="vl">{fertiliser.get('K','—')}</div></div>
            <div class="it"><div class="lb">Application</div><div class="vl">{fertiliser.get('application','—')}</div></div>
          </div>
        </div>"""

    return f"""<!DOCTYPE html>
<html><head><meta charset="UTF-8"><title>AgroGuard Report</title>
<style>
*{{margin:0;padding:0;box-sizing:border-box}}
body{{font-family:'Segoe UI',sans-serif;background:#0a1628;padding:40px;color:#e8f4f0}}
.container{{max-width:760px;margin:0 auto;background:#132035;border-radius:16px;
            overflow:hidden;border:1px solid rgba(0,255,136,0.2)}}
.header{{background:linear-gradient(135deg,#061428,#0a2540);color:#fff;padding:28px;
         text-align:center;border-bottom:2px solid rgba(0,255,136,0.3)}}
.header h1{{font-size:24px;margin-bottom:6px;color:#00ff88;letter-spacing:3px}}
.header p{{opacity:.7;font-size:13px}}
.content{{padding:24px}}
.section{{margin-bottom:18px;padding:16px;border-radius:10px}}
.disease {{background:rgba(255,60,60,0.08);border-left:3px solid #ff4444}}
.healthy {{background:rgba(0,255,136,0.07);border-left:3px solid #00ff88}}
.treatment{{background:rgba(255,170,0,0.07);border-left:3px solid #ffaa00}}
.fertilizer{{background:rgba(0,200,255,0.07);border-left:3px solid #00c8ff}}
h2{{font-size:15px;margin-bottom:12px;color:#00ff88;letter-spacing:1px;text-transform:uppercase}}
.g2{{display:grid;grid-template-columns:1fr 1fr;gap:8px;margin-top:10px}}
.it{{background:rgba(255,255,255,0.04);padding:10px;border-radius:6px;
     border:1px solid rgba(255,255,255,0.08)}}
.lb{{font-size:11px;color:#7a9e8e;text-transform:uppercase;letter-spacing:1px}}
.vl{{font-size:13px;color:#e8f4f0;margin-top:3px;line-height:1.4}}
.footer{{background:#0d1e35;padding:16px;text-align:center;color:#7a9e8e;font-size:11px;
         border-top:1px solid rgba(0,255,136,0.15)}}
</style></head>
<body><div class="container">
<div class="header">
  <h1>🌱 AGROGUARD AI REPORT</h1>
  <p>Generated: {ts} &nbsp;|&nbsp; v4.0</p>
</div>
<div class="content">
  <div class="section {card}">
    <h2>Diagnosis Results</h2>
    <div class="g2">
      <div class="it"><div class="lb">Crop</div><div class="vl">{crop or '—'}</div></div>
      <div class="it"><div class="lb">Condition</div><div class="vl">{disease}</div></div>
      <div class="it"><div class="lb">Confidence</div><div class="vl">{confidence:.1f}%</div></div>
      <div class="it"><div class="lb">Severity</div><div class="vl">{sev}</div></div>
    </div>
  </div>
  <div class="section treatment">
    <h2>Treatment Plan</h2>
    <div class="g2">
      <div class="it"><div class="lb">Chemical</div><div class="vl">{treatment.get('pesticide','—')}</div></div>
      <div class="it"><div class="lb">Organic</div><div class="vl">{treatment.get('organic','—')}</div></div>
      <div class="it"><div class="lb">Precaution</div><div class="vl">{treatment.get('precaution','—')}</div></div>
      <div class="it"><div class="lb">Apply Every</div><div class="vl">{treatment.get('treatment_days','—')}</div></div>
    </div>
  </div>
  {fert_sec}
  {'<div class="section"><h2>User Note</h2><p style="font-size:13px;color:#e8f4f0;">'+comment+'</p></div>' if comment else ''}
</div>
<div class="footer">
  AGROGUARD AI — Intelligent Crop Protection System<br>
  ⚠ Always consult local agricultural experts for critical decisions.
</div>
</div></body></html>"""


# ─── CHATBOT ──────────────────────────────────────────────────────────────────
_EN = {
    ("hi","hello","hey","good morning","good evening","howdy"): (
        "Hello! I'm AgroBot 🌿 I can help with disease detection, treatment plans, "
        "fertiliser advice, and weather farming tips. What would you like to know?"
    ),
    ("disease","detect","scan","diagnose","identify","identification"): (
        "To detect diseases: upload a clear leaf photo in the Scan Leaf tab. "
        "The AI will identify the disease, confidence score, severity level, and provide a full treatment plan."
    ),
    ("fertilizer","fertiliser","npk","nitrogen","urea","phosphorus","potassium","manure"): (
        "I provide crop-specific NPK recommendations that adapt to the detected disease. "
        "For example, Late blight requires reduced N and boosted P+K for plant immunity."
    ),
    ("treatment","cure","medicine","pesticide","spray","fungicide","bactericide"): (
        "Each diagnosis includes: chemical control (e.g. Mancozeb, Copper bactericide), "
        "an organic alternative (neem oil, garlic extract), and full safety precautions."
    ),
    ("organic","neem","natural","bio","biological","compost"): (
        "Top organic options: Neem oil spray, Garlic extract, "
        "Trichoderma bio-fungicide, Pseudomonas fluorescens, and compost tea. "
        "These are safer for soil health and beneficial insects."
    ),
    ("weather","rain","forecast","humidity","temperature","monsoon","climate"): (
        "Check the Weather tab for a 3-day forecast with farming precautions. "
        "Key risk: humidity >80% triggers fungal disease. Rain days = no spraying. "
        "Hot sunny days (>32°C) = spider mite risk."
    ),
    ("tomato","tomatoe"): (
        "Tomato diseases I detect (10 classes): Bacterial spot, Early blight, Late blight, "
        "Leaf mold, Septoria leaf spot, Spider mites, Target spot, "
        "Yellow Leaf Curl Virus, Mosaic virus, and Healthy."
    ),
    ("potato",): (
        "Potato diseases I detect (3 classes): Early blight, Late blight, and Healthy. "
        "Late blight is the most destructive — spreads within hours in wet weather. Act immediately!"
    ),
    ("pepper","capsicum","bell pepper","chilli"): (
        "Bell pepper diseases I detect (2 classes): Bacterial spot and Healthy. "
        "Treatment: Copper bactericide + Streptomycin. Avoid overhead irrigation."
    ),
    ("late blight","lateblight","phytophthora"): (
        "Late blight is CRITICAL (Phytophthora infestans). It spreads in cool, wet conditions. "
        "Chemical: Metalaxyl + Mancozeb (Ridomil Gold). Reduce N fertiliser immediately. "
        "Organic: Copper hydroxide (follow product label). Spray within 24–48 hours of detection!"
    ),
    ("early blight","alternaria"): (
        "Early blight (Alternaria solani) appears as dark concentric rings on lower leaves. "
        "Chemical: Mancozeb or Chlorothalonil (follow product label). "
        "Organic: neem oil + baking soda spray (weekly). Apply every 7–10 days."
    ),
    ("bacterial spot","bacteria","xanthomonas"): (
        "Bacterial spot is caused by Xanthomonas bacteria. "
        "Chemical: Copper bactericide (Kocide 2000) (follow product label). "
        "Organic: garlic extract + neem oil. Avoid overhead irrigation and stressed plants."
    ),
    ("mosaic","virus","viral","tmv"): (
        "Tomato Mosaic Virus has NO chemical cure. Remove and destroy infected plants immediately. "
        "Prevention: sanitise tools, wash hands, control aphid vectors with neem oil."
    ),
    ("yellow leaf curl","tylcv","whitefly"): (
        "Yellow Leaf Curl Virus is spread by whiteflies. "
        "Control whiteflies with Imidacloprid. Use reflective mulch and yellow sticky traps. "
        "Remove infected plants to stop spread."
    ),
    ("report","download","export","pdf","html"): (
        "After each scan, a 'Download HTML Diagnosis Report' button appears. "
        "It generates a complete HTML report with diagnosis, treatment, fertiliser details — "
        "ready to print or share with your agricultural officer."
    ),
    ("history","previous","past","scan history"): (
        "The Scan History tab shows all diagnoses from this session — "
        "disease, crop, confidence, severity — with a summary dashboard."
    ),
    ("voice","speak","audio","microphone","listen"): (
        "The Voice tab lets you speak questions in English or Tamil using your browser mic. "
        "There's also a Text-to-Speech feature to hear responses read aloud. "
        "Best supported in Google Chrome."
    ),
    ("language","tamil","english","bilingual"): (
        "Toggle English ↔ தமிழ் using the Language selector in the sidebar. "
        "The entire interface — including chatbot, diagnosis cards, and tips — switches language."
    ),
    ("hardware","raspberry","iot","sensor","device","field"): (
        "AgroGuard is designed for hardware integration! Planned modules: "
        "Raspberry Pi Camera (leaf capture), I²S mic+speaker (voice I/O), "
        "DHT22 sensor (humidity/temp), LoRa (offline field comm), 7\" LCD (farmer UI). "
        "Contact the team for the hardware SDK."
    ),
    ("accuracy","confidence","how accurate","reliable"): (
        "The model achieves 92.63% validation accuracy (91.99% Macro F1, 92.61% Weighted F1) "
        "on the 4,127 PlantVillage validation images. Confidence score is shown for every prediction. "
        "For best results: good lighting, clear leaf, fill the frame."
    ),
    ("tip","advice","best practice","how to"): (
        "Top farming tips: ✅ Spray early morning or evening. "
        "✅ Keep leaves dry — water at base only. "
        "✅ Rotate crops every 3–4 years. "
        "✅ Inspect leaves weekly for early detection. "
        "✅ Remove infected plants immediately to prevent spread."
    ),
}

_TA = {
    ("வணக்கம்","ஹலோ","நமஸ்தே","வணக்கங்கள்"): (
        "வணக்கம்! நான் அக்ரோபாட் 🌿 நோய் கண்டறிதல், சிகிச்சை, உரம், "
        "வானிலை பற்றி உதவ இங்கிருக்கிறேன். என்ன கேட்க விரும்புகிறீர்கள்?"
    ),
    ("நோய்","கண்டறி","ஸ்கேன்","பரிசோதனை","நோயறிதல்"): (
        "Scan Leaf தாவலில் இலையின் தெளிவான படத்தை பதிவேற்றவும். "
        "AI நோயின் பெயர், நம்பகத்தன்மை, தீவிரம், சிகிச்சை திட்டம் தரும்."
    ),
    ("உரம்","NPK","நைட்ரஜன்","யூரியா","பாஸ்பரஸ்","பொட்டாசியம்","உரங்கள்"): (
        "நோய்க்கு ஏற்ப தனிப்பயன் NPK பரிந்துரைகள் தருகிறேன். "
        "உதாரணம்: பிற்போக்கு கருகலுக்கு நைட்ரஜனை குறைத்து பாஸ்பரஸ்+பொட்டாசியம் அதிகரிக்கணும்."
    ),
    ("சிகிச்சை","மருந்து","கீட்நாசினி","பூஞ்சைக்கொல்லி","தெளிக்க"): (
        "ஒவ்வொரு கண்டறிதலிலும் இரசாயன (உ.தா. மேன்கோசெப்), "
        "உயிரி (வேப்பெண்ணெய், பூண்டு சாறு), முன்னெச்சரிக்கை ஆகியவை தருகிறேன்."
    ),
    ("தக்காளி","தக்காளி"): (
        "தக்காளி நோய்கள் (10 வகைகள்): பாக்டீரியா புள்ளி, முன்கருகல், பிற்போக்கு கருகல், "
        "இலைப்பூஞ்சை, இலைப்புள்ளி, சிலந்திப்பூச்சி, இலை சுருள் வைரஸ், மொசைக் வைரஸ், "
        "இலக்கு புள்ளி, ஆரோக்கியம்."
    ),
    ("உருளை","உருளைக்கிழங்கு"): (
        "உருளைக்கிழங்கு நோய்கள்: முன்கருகல், பிற்போக்கு கருகல், ஆரோக்கியம். "
        "பிற்போக்கு கருகல் மிகவும் ஆபத்தானது — ஈரமான சூழலில் மணிக்குள் பரவும்!"
    ),
    ("மிளகாய்","குடைமிளகாய்","மிர்ச்"): (
        "மிளகாய் நோய்கள்: பாக்டீரியா புள்ளி, ஆரோக்கியம். "
        "சிகிச்சை: செப்பு பாக்டீரியா கொல்லி + ஸ்ட்ரெப்டோமைசின். "
        "மேல்பகுதியில் நீர் பாய்ப்பதை தவிர்க்கவும்."
    ),
    ("பிற்போக்கு","கருகல்","லேட் ப்லைட்"): (
        "பிற்போக்கு கருகல் மிகவும் அபாயமானது! குளிர் ஈர சூழலில் வேகமாக பரவும். "
        "இரசாயன: மெட்டாலாக்சில் + மேன்கோசெப் (ரிடோமில் கோல்ட்). "
        "24–48 மணி நேரத்தில் தெளிக்கவும்!"
    ),
    ("முன்கருகல்","எர்லி ப்லைட்"): (
        "முன்கருகல் (Alternaria) கீழிலைகளில் கருப்பு வளையங்களாக தெரியும். "
        "இரசாயன: மேன்கோசெப் (அடைப்படை விவரப்படி). உயிரி: வேப்பெண்ணெய் + சமையல் சோடா. "
        "7–10 நாள் இடைவெளியில் தெளிக்கவும்."
    ),
    ("வேப்பெண்ணெய்","உயிரி","இயற்கை","கரிம"): (
        "உயிரி சிகிச்சைகள்: வேப்பெண்ணெய், பூண்டு சாறு, "
        "ட்ரைக்கோடெர்மா, சூடோமோனாஸ். இவை மண் ஆரோக்கியத்தை பாதிக்காது."
    ),
    ("வானிலை","மழை","வெப்பம்","ஈரப்பதம்"): (
        "Weather தாவலில் 3 நாள் வானிலை + விவசாய முன்னெச்சரிக்கைகள் உள்ளன. "
        "80%க்கு மேல் ஈரப்பதம் = பூஞ்சை அபாயம். மழை நாட்களில் மருந்து தெளிக்க வேண்டாம்."
    ),
    ("குரல்","மைக்","பேசு","கேட்க"): (
        "Voice தாவலில் தமிழிலோ ஆங்கிலத்திலோ பேசி கேள்விகள் கேட்கலாம். "
        "பதில்களை குரலில் கேட்க Text-to-Speech உள்ளது. Chrome பயன்படுத்தவும்."
    ),
    ("அறிக்கை","ரிப்போர்ட்","பதிவிறக்கம்"): (
        "ஒவ்வொரு ஸ்கேனுக்கும் 'HTML அறிக்கையை பதிவிறக்கம் செய்யவும்' பட்டன் வரும். "
        "HTML அறிக்கையில் நோய், சிகிச்சை, உரம் விவரங்கள் உள்ளன — "
        "அச்சிட்டு வேளாண்மை அலுவலரிடம் காட்டலாம்."
    ),
    ("வன்பொருள்","ஹார்ட்வேர்","ராஸ்பெரி","சாதனம்"): (
        "AgroGuard வன்பொருள் ஒருங்கிணைப்பிற்காக வடிவமைக்கப்பட்டது! "
        "திட்டமிட்ட தொகுதிகள்: Raspberry Pi கேமரா, I²S மைக்+ஸ்பீக்கர், "
        "DHT22 சென்சார், LoRa, 7\" LCD. SDK-க்கு குழுவை தொடர்பு கொள்ளவும்."
    ),
}



def agro_chatbot_reply(user_input: str, lang: str = "en") -> str:
    q    = user_input.lower()
    bank = _EN if lang == "en" else _TA

    for keywords, response in bank.items():
        if any(kw in q for kw in keywords):
            return response

    if lang == "en":
        return ("I can help with disease detection, treatments, fertiliser planning, weather advice, "
                "and hardware integration. Try asking about a specific disease or crop!")
    else:
        return ("நோய் கண்டறிதல், சிகிச்சை, உரம், வானிலை பற்றி கேட்கலாம். "
                "குறிப்பிட்ட நோய் அல்லது பயிரைப் பற்றி கேளுங்கள்!")