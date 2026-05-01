"""
AgroGuard AI v5.0 - Services
Weather, treatment/fertilizer, report, feedback, and bilingual chatbot.
"""

import os
import csv
import json
import requests
from datetime import datetime, timedelta
from config import WEATHER_API_KEY, CITY, TREATMENT_DB, FERTILIZER_DB, FEEDBACK_FILE

# ============================================================================
# WEATHER SERVICE
# ============================================================================

def get_3day_forecast():
    """Fetch 3-day weather forecast from OpenWeatherMap API"""
    try:
        url = f"https://api.openweathermap.org/data/2.5/forecast"
        params = {
            "q": CITY,
            "appid": WEATHER_API_KEY,
            "units": "metric",
            "cnt": 24,  # 3 days (8 forecasts per day * 3)
        }
        
        response = requests.get(url, params=params, timeout=5)
        response.raise_for_status()
        data = response.json()
        
        forecasts = []
        seen_dates = set()
        
        for item in data['list'][:24]:
            dt = datetime.fromtimestamp(item['dt'])
            date_str = dt.strftime("%a, %d %b")
            
            if date_str not in seen_dates:
                seen_dates.add(date_str)
                forecasts.append({
                    "date": date_str,
                    "temp": item['main']['temp'],
                    "hum": item['main']['humidity'],
                    "sky": item['weather'][0]['main'],
                })
            
            if len(forecasts) >= 3:
                break
        
        return forecasts if forecasts else _mock_forecast()
    
    except Exception as e:
        print(f"Weather API error: {e}")
        return _mock_forecast()

def _mock_forecast():
    """Fallback mock forecast"""
    today = datetime.now()
    return [
        {
            "date": today.strftime("%a, %d %b"),
            "temp": 28.5,
            "hum": 62,
            "sky": "Clear",
        },
        {
            "date": (today + timedelta(days=1)).strftime("%a, %d %b"),
            "temp": 26.2,
            "hum": 75,
            "sky": "Rainy",
        },
        {
            "date": (today + timedelta(days=2)).strftime("%a, %d %b"),
            "temp": 27.8,
            "hum": 68,
            "sky": "Cloudy",
        },
    ]

def get_weather_precaution(humidity, sky, temp, lang_code="en"):
    """Get farming precautions based on weather"""
    precautions = {
        "en": {
            "high_humid": "⚠ High humidity - risk of fungal diseases",
            "rain": "⚠ Delay spraying - wait 24h after rain",
            "ideal": "✓ Ideal conditions for spraying",
            "hot": "⚠ High temperature - use evening spray",
        },
        "ta": {
            "high_humid": "⚠ உயர் ஈரப்பதம் - பூஞ்சை நோய் ஆபத்து",
            "rain": "⚠ தெளிக்க தாமதம் - மழைக்கு 24 மணி நேரம்",
            "ideal": "✓ தெளிப்பதற்கான சிறந்த நிலைமைகள்",
            "hot": "⚠ உচ்च வெப்பநிலை - மாலை தெளிக்க",
        },
    }
    
    lang = precautions.get(lang_code, precautions["en"])
    
    if humidity > 80:
        return lang["high_humid"]
    elif "rain" in sky.lower() or "drizzle" in sky.lower():
        return lang["rain"]
    elif temp > 32:
        return lang["hot"]
    else:
        return lang["ideal"]

# ============================================================================
# TREATMENT & FERTILIZER SERVICE
# ============================================================================

def get_treatment(disease_class):
    """Get treatment recommendations for a disease"""
    treatment = TREATMENT_DB.get(disease_class, {
        "severity": "Unknown",
        "pesticide": "Consult local expert",
        "organic": "Consult local expert",
        "precaution": "Monitor plant health",
        "treatment_days": "N/A",
    })
    return treatment

def get_fertilizer(crop_type, disease_label):
    """Get fertilizer recommendations"""
    key = (crop_type, disease_label) if crop_type else None
    
    if key and key in FERTILIZER_DB:
        return FERTILIZER_DB[key]
    elif crop_type:
        # Try to find a healthy recommendation
        healthy_key = (crop_type, "Healthy")
        return FERTILIZER_DB.get(healthy_key, {})
    
    return {}

# ============================================================================
# REPORT GENERATION
# ============================================================================

def generate_report(disease, crop, confidence, treatment, fertilizer):
    """Generate HTML report for the scan"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    html = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>AgroGuard Diagnosis Report</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 40px; background: #f5f5f5; }}
        .container {{ background: white; padding: 30px; border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.1); }}
        h1 {{ color: #0d8a4b; text-align: center; }}
        h2 {{ color: #0d8a4b; border-bottom: 2px solid #5eea94; padding-bottom: 10px; }}
        .info-grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin: 20px 0; }}
        .info-item {{ background: #f9f9f9; padding: 15px; border-radius: 5px; }}
        .label {{ font-weight: bold; color: #333; }}
        .value {{ color: #666; margin-top: 5px; }}
        .footer {{ text-align: center; margin-top: 40px; color: #999; font-size: 12px; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>AgroGuard AI Diagnosis Report</h1>
        
        <div class="info-grid">
            <div class="info-item">
                <div class="label">Diagnosis</div>
                <div class="value">{disease}</div>
            </div>
            <div class="info-item">
                <div class="label">Crop</div>
                <div class="value">{crop or 'Not specified'}</div>
            </div>
            <div class="info-item">
                <div class="label">Confidence</div>
                <div class="value">{confidence:.1f}%</div>
            </div>
            <div class="info-item">
                <div class="label">Severity</div>
                <div class="value">{treatment.get('severity', 'Unknown')}</div>
            </div>
        </div>
        
        <h2>Treatment Plan</h2>
        <div class="info-grid">
            <div class="info-item">
                <div class="label">Chemical Control</div>
                <div class="value">{treatment.get('pesticide', 'N/A')}</div>
            </div>
            <div class="info-item">
                <div class="label">Organic Control</div>
                <div class="value">{treatment.get('organic', 'N/A')}</div>
            </div>
            <div class="info-item">
                <div class="label">Precaution</div>
                <div class="value">{treatment.get('precaution', 'N/A')}</div>
            </div>
            <div class="info-item">
                <div class="label">Treatment Interval</div>
                <div class="value">{treatment.get('treatment_days', 'N/A')}</div>
            </div>
        </div>
        
        {"" if not fertilizer else f'''
        <h2>Fertilizer Recommendation</h2>
        <div class="info-grid">
            <div class="info-item">
                <div class="label">Nitrogen (N)</div>
                <div class="value">{fertilizer.get('N', 'N/A')}</div>
            </div>
            <div class="info-item">
                <div class="label">Phosphorus (P)</div>
                <div class="value">{fertilizer.get('P', 'N/A')}</div>
            </div>
            <div class="info-item">
                <div class="label">Potassium (K)</div>
                <div class="value">{fertilizer.get('K', 'N/A')}</div>
            </div>
            <div class="info-item">
                <div class="label">Application</div>
                <div class="value">{fertilizer.get('application', 'N/A')}</div>
            </div>
        </div>
        '''}
        
        <div class="footer">
            Generated by AgroGuard AI on {timestamp}<br>
            <strong>Disclaimer:</strong> This report is for guidance only. Always consult local agricultural experts for critical decisions.
        </div>
    </div>
</body>
</html>
    """
    return html

# ============================================================================
# FEEDBACK SERVICE
# ============================================================================

def save_feedback(filename, predicted_class, correct_disease, is_correct):
    """Save user feedback for model improvement"""
    try:
        file_exists = os.path.isfile(FEEDBACK_FILE)
        
        with open(FEEDBACK_FILE, 'a', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            
            # Write header if file is new
            if not file_exists:
                writer.writerow(['timestamp', 'filename', 'predicted_class', 'correct_disease', 'is_correct'])
            
            # Write feedback
            writer.writerow([
                datetime.now().isoformat(),
                filename,
                predicted_class,
                correct_disease,
                is_correct,
            ])
    except Exception as e:
        print(f"Error saving feedback: {e}")

# ============================================================================
# CHATBOT SERVICE
# ============================================================================

def agro_chatbot_reply(user_input, lang_code="en"):
    """
    Bilingual keyword-based chatbot.
    Matches user questions to predefined answers.
    """
    user_input_lower = user_input.lower()
    
    if lang_code == "ta":
        return _tamil_chatbot_reply(user_input_lower)
    else:
        return _english_chatbot_reply(user_input_lower)

def _english_chatbot_reply(user_input_lower):
    """English chatbot responses"""
    
    if any(word in user_input_lower for word in ["late blight", "late blight treatment"]):
        return "Late blight is a critical disease affecting both tomato and potato. Treatment: Spray Metalaxyl + Mancozeb or Bordeaux mixture every 5-7 days. Precaution: Avoid overhead watering and improve ventilation."
    
    elif any(word in user_input_lower for word in ["early blight", "early blight treatment"]):
        return "Early blight affects tomato and potato leaves. Treatment: Use Mancozeb 75% WP or Sulfur dust 90%. Remove infected lower leaves. Spray every 7-10 days."
    
    elif any(word in user_input_lower for word in ["fertilizer", "npk", "nitrogen", "phosphorus", "potassium"]):
        return "For healthy tomato crops, use: Nitrogen 150-200 kg/ha, Phosphorus 60-80 kg/ha, Potassium 100-150 kg/ha. Apply in split doses every 15 days. For diseased plants, increase Potassium content."
    
    elif any(word in user_input_lower for word in ["spray", "when to spray", "spraying time"]):
        return "Best spraying conditions: Early morning or late evening. Wait 24 hours after rain. Avoid spraying when temperature exceeds 32°C. Spray when plant leaves are dry."
    
    elif any(word in user_input_lower for word in ["prevent", "prevention", "preventive", "how to prevent"]):
        return "Prevention tips: 1) Crop rotation every 3 years 2) Maintain proper plant spacing 3) Avoid overhead watering 4) Weekly leaf inspection 5) Remove infected leaves immediately 6) Use resistant varieties when available."
    
    elif any(word in user_input_lower for word in ["bacterial spot", "bacterial", "spot"]):
        return "Bacterial spot affects tomato and pepper. Treatment: Copper hydroxide 50% WP or Bordeaux mixture. Precaution: Avoid overhead watering and wet foliage. Spray every 10-14 days."
    
    elif any(word in user_input_lower for word in ["spider mite", "mites", "pest"]):
        return "Spider mites (two-spotted) damage by sucking leaf juices. Treatment: Abamectin 1.8% EC or Neem oil 3%. Maintain high humidity. Spray every 5-7 days if infestation is severe."
    
    elif any(word in user_input_lower for word in ["yellow leaf curl", "curl", "virus"]):
        return "Tomato Yellow Leaf Curl Virus is spread by whiteflies. Prevention: Use yellow sticky traps, grow resistant varieties. Treatment: Control whiteflies with Imidacloprid. Remove infected plants immediately."
    
    elif any(word in user_input_lower for word in ["weather", "humidity", "temperature", "rain", "monsoon"]):
        return "Humidity above 80% triggers fungal diseases. Heavy rains delay spraying operations. Temperature above 32°C increases mite/thrips risk. Ideal farming temperature: 18-26°C with moderate humidity (60-70%)."
    
    elif any(word in user_input_lower for word in ["watering", "water", "irrigation"]):
        return "Water tomato and pepper plants in early morning only. Avoid overhead watering as it promotes fungal diseases. Provide consistent moisture but avoid waterlogging. Potato requires 500-600mm seasonal rainfall."
    
    elif any(word in user_input_lower for word in ["hello", "hi", "hey", "help"]):
        return "Hello! I'm AgroBot. I can help you with: disease identification, treatment plans, fertilizer recommendations, weather-based farming advice, and crop rotation guidance. Ask me anything!"
    
    else:
        return "I can help you with disease treatment, fertilizer planning, spray schedules, and weather-based farming tips. Could you please be more specific? For example: 'How to treat late blight?' or 'Best fertilizer for tomatoes?'"

def _tamil_chatbot_reply(user_input_lower):
    """Tamil chatbot responses"""
    
    if any(word in user_input_lower for word in ["பிற்போக்கு கருகல்", "late blight"]):
        return "பிற்போக்கு கருகல் என்பது தக்காளி மற்றும் உருளைக்கிழங்கு பாதிக்கும் கடும் நோய். சிகிச்சை: Metalaxyl + Mancozeb அல்லது Bordeaux கலவை 5-7 நாட்களுக்கு ஒரு முறை தெளிக்கவும்."
    
    elif any(word in user_input_lower for word in ["நிர்வாணமான கருகல்", "early blight"]):
        return "நிர்வாணமான கருகல் தக்காளி மற்றும் உருளைக்கிழங்கு இலைகளை பாதிக்கிறது. சிகிச்சை: Mancozeb 75% அல்லது கந்தக பொடி 90% பயன்படுத்தவும். 7-10 நாட்களுக்கு ஒரு முறை தெளிக்கவும்."
    
    elif any(word in user_input_lower for word in ["உரம்", "நைட்ரஜன்", "பாஸ்ஃபரஸ்"]):
        return "ஆரோக்கியமான தக்காளி பயிருக்கு: நைட்ரஜன் 150-200 கி.கி/ஹெ, பாஸ்பரஸ் 60-80 கி.கி/ஹெ, பொட்டாசியம் 100-150 கி.கி/ஹெ. 15 நாட்களுக்கு ஒரு முறை பிரிக்கப்பட்ட அளவில் பயன்படுத்தவும்."
    
    elif any(word in user_input_lower for word in ["தெளிக்க", "தெளிப்பு"]):
        return "சிறந்த தெளிக்கும் நிலை: அதிகாலையில் அல்லது மாலையில். மழையைத் தொடர்ந்து 24 மணி நேரம் பொறுக்கவும். வெப்பநிலை 32°C க்கு மேல் இருக்கும்போது தெளிக்க வேண்டாம்."
    
    elif any(word in user_input_lower for word in ["தடுக்க", "தடுப்பு", "போக்கொழுக்கம்"]):
        return "தடுப்பு குறிப்புகள்: 1) 3 ஆண்டுகளுக்கு ஒரு முறை பயிர் சுழற்சி 2) சரியான செடி இடைவெளி 3) தலைக்கு மேல் நீர் ஊற்றாதே 4) வாரத்தில் ஒரு முறை இலை பরிசோதனை 5) கோளாறுள்ள இலைகளை உடனே நீக்கவும்."
    
    elif any(word in user_input_lower for word in ["பாக்டீரியா"]):
        return "பாக்டீரியா புள்ளி தக்காளி மற்றும் குடைமிளகை பாதிக்கிறது. சிகிச்சை: Copper hydroxide அல்லது Bordeaux கலவை. தலைக்கு மேல் நீர் ஊற்றாதே. 10-14 நாட்களுக்கு ஒரு முறை தெளிக்கவும்."
    
    elif any(word in user_input_lower for word in ["அணு", "பூச்சி", "வளர்ப்பு"]):
        return "சிலந்திப் பூச்சிகள் (இரண்  இடப்பட்ட) இலையின் சாறு உறிஞ்சுகிறது. சிகிச்சை: Abamectin அல்லது நீம் எண்ணெய் 3%. आद्रता அधिक ಮಾಡಿ. ತೀವ್ರ ಸೋಂಕಿತವಾಗಿದ್ದರೆ 5-7 ದಿನಗಳಿಗೆ ಚಿಮುಕಿಸಿ."
    
    elif any(word in user_input_lower for word in ["வைरस", "புறக்kezek்கு", "curl"]):
        return "தக்காளி மஞ்சள் இலை மடிப்பு வைरस வெள்ளை ஈ மூலம் பரவுகிறது. தடுப்பு: மஞ்சள் ஒட்டும்함정ு பயன்படுத்தவும்,வைरस-resistant வகைகளை பயிர் செய்யவும்."
    
    else:
        return "வணக்கம்! நான் AgroBot. நோய் சிகிச்சை, உரம் பரிந்துरை, தெளிப்பு வரிசை, மற்றும் வானிலை அடிப்படையிலான விவசாய ஆலோசனை வழங்க முடியும். 'தக்காளிக்கு சிறந்த உரம் எது?' அல்லது 'பிற்போக்கு கருகல் சிகிச்சை?' போன்ற வினாக்களை கேளுங்கள்."
