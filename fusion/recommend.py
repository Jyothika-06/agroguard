"""
AgroGuard AI — Recommendation Engine Module
Bilingual advisory text generation using risk assessment outputs.
Enforces strict advisory wording guidelines: no dosages, no autonomous commands, no certainty.
"""

from typing import Dict, Any, List


def generate_field_recommendations(risk_res: Dict[str, Any], lang: str = "en") -> List[str]:
    """
    Generates structured advisory recommendations based on environmental risk evaluation.
    
    Args:
        risk_res: Dict returned by evaluate_field_risk.
        lang: "en" or "ta" (or "English" / "Tamil").
        
    Returns:
        List[str]: Formatted recommendation lines.
    """
    is_ta = lang.lower() in ["ta", "tamil", "தமிழ்"]
    recs: List[str] = []

    water_risk = risk_res.get("water_stress_risk", "UNKNOWN")
    heat_risk = risk_res.get("heat_stress_risk", "UNKNOWN")
    spread_risk = risk_res.get("disease_spread_risk", "UNKNOWN")
    disease_status = risk_res.get("disease_status_used", "UNKNOWN")

    # 1. Water Stress Recommendation
    if water_risk in ["HIGH", "MODERATE"]:
        if is_ta:
            recs.append("💧 நீர் அழுத்தம் சாத்தியம்: மண் ஈரப்பதம் மற்றும் நீர்ப்பாசனத் தேவையை சரிபார்க்கவும். (to be reviewed)")
        else:
            recs.append("💧 Possible water stress: Check soil moisture and irrigation requirement.")
    elif water_risk == "LOW":
        if is_ta:
            recs.append("✅ மண் ஈரப்பதம் போதுமானது: கூடுதல் நீர்ப்பாசனம் தேவையில்லை. (to be reviewed)")
        else:
            recs.append("✅ Soil moisture is adequate: No immediate irrigation change required.")

    # 2. Heat Stress Recommendation
    if heat_risk in ["HIGH", "MODERATE"]:
        if is_ta:
            recs.append("🌡️ வெப்ப அழுத்தம் அறிகுறி: பயிர் நிழல் மற்றும் காற்றோட்டத்தை கண்காணிக்கவும். (to be reviewed)")
        else:
            recs.append("🌡️ Indication of heat stress: Monitor crop shading and soil canopy cover.")

    # 3. Disease Spread Recommendation
    if spread_risk in ["HIGH", "MODERATE"]:
        if disease_status != "UNKNOWN" and "healthy" not in disease_status.lower():
            if is_ta:
                recs.append(f"🦠 நோய் அறிகுறிகளுடன் ஈரப்பதமான சூழல் ({disease_status}): அருகில் உள்ள செடிகளை ஆய்வு செய்து பயிர் மேலாண்மையை பின்பற்றவும். (to be reviewed)")
            else:
                recs.append(f"🦠 Disease symptoms with humid conditions ({disease_status}): Inspect nearby plants and follow crop-specific management.")
        elif disease_status != "UNKNOWN" and "healthy" in disease_status.lower():
            if is_ta:
                recs.append("🌿 செடி ஆரோக்கியமாக தெரிகிறது, ஆனால் ஈரப்பதம் நோய் அபாயத்தை காட்டுகிறது: இலைகளை தொடர்ந்து கண்காணிக்கவும். (to be reviewed)")
            else:
                recs.append("🌿 Plant appears visually healthy, but humid conditions indicate possible environmental disease risk. Inspect leaves regularly.")
        else: # UNKNOWN disease image
            if is_ta:
                recs.append("☁️ ஈரப்பதம் அதிகமாக உள்ளது: பூஞ்சை நோய் தடுப்பு நடவடிக்கைகளை கண்காணிக்கவும். (to be reviewed)")
            else:
                recs.append("☁️ High humidity observed: Monitor leaves for early fungal disease indications.")

    # 4. Missing/Unknown Inputs Guidance
    unknown_inputs = risk_res.get("unknown_inputs", [])
    if unknown_inputs:
        inputs_str = ", ".join(unknown_inputs)
        if is_ta:
            recs.append(f"⚠️ சில தரவுகள் கிடைக்கவில்லை ({inputs_str}): சென்சார் அல்லது இலைப் படத்தை சரிபார்க்கவும். (to be reviewed)")
        else:
            recs.append(f"⚠️ Missing/Unknown inputs ({inputs_str}): Verify sensor connections or capture a clear leaf photo.")

    if not recs:
        if is_ta:
            recs.append("✅ அனைத்து கள நிலைகளும் சாதாரணமாக தெரிகிறது. (to be reviewed)")
        else:
            recs.append("✅ All field indicators appear within normal prototype baseline ranges.")

    # Mandatory Disclaimer Attachment
    disclaimer = "⚠ தமிழ் உரைகள் மதிப்பாய்வு செய்யப்பட வேண்டும். (to be reviewed)" if is_ta else "⚠ Consult your local agriculture officer for critical decisions."
    recs.append(disclaimer)

    return recs
