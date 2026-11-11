"""
AgroGuard AI v4.0 — Intelligent Crop Protection System
Professional, animated, hardware-ready Streamlit application
"""

import streamlit as st
import numpy as np
import os, base64, csv, json, re, time
from pathlib import Path
from datetime import datetime
from PIL import Image

from config import EN, TA, SUPPORTED_CROPS, FEEDBACK_FILE, MODEL_PATH, CLASS_INDICES_PATH, BASE_DIR
from services import (
    get_3day_forecast, get_weather_precaution,
    get_treatment, get_fertilizer,
    agro_chatbot_reply, generate_report, save_feedback,
)
from model_utils import load_model_assets, preprocess_image, predict_with_confidence
from fusion.uncertainty import assess_uncertainty
from fusion.crop_params import get_crop_params
from fusion.sensor_sim import get_preset_scenario, create_manual_reading
from fusion.sensor_validator import validate_sensor_readings
from fusion.risk_engine import evaluate_field_risk
from fusion.recommend import generate_field_recommendations
from fusion.patch_analysis import analyze_image_patches


# ── Directories ──────────────────────────────────────────────────────────────
(BASE_DIR / "models").mkdir(exist_ok=True)
(BASE_DIR / "reports").mkdir(exist_ok=True)

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="AgroGuard AI — Intelligent Crop Protection",
    page_icon="🌿",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Session state ─────────────────────────────────────────────────────────────
for k, v in {
    "language": "English",
    "chat_history": [],
    "scan_history": [],
    "theme": "dark",
    "voice_text": "",
}.items():
    if k not in st.session_state:
        st.session_state[k] = v

lang     = st.session_state.language
txt      = EN if lang == "English" else TA
theme    = st.session_state.theme
is_dark  = theme == "dark"

# ── CSS injection ─────────────────────────────────────────────────────────────
def load_css(dark: bool):
    # Color tokens
    if dark:
        bg_primary   = "#0a1628"
        bg_secondary = "#0f2040"
        bg_card      = "#132035"
        bg_glass     = "rgba(15,32,64,0.85)"
        border       = "rgba(0,255,136,0.18)"
        accent       = "#00ff88"
        accent2      = "#00c8ff"
        text_primary = "#e8f4f0"
        text_muted   = "#7a9e8e"
        panel_bg     = "#0d1e35"
        sidebar_bg   = "#080f1e"
    else:
        bg_primary   = "#f0f7f4"
        bg_secondary = "#ffffff"
        bg_card      = "#ffffff"
        bg_glass     = "rgba(255,255,255,0.9)"
        border       = "rgba(0,140,80,0.25)"
        accent       = "#008c50"
        accent2      = "#0066cc"
        text_primary = "#0d2a1a"
        text_muted   = "#4a7a5a"
        panel_bg     = "#e8f5ee"
        sidebar_bg   = "#d8f0e4"

    st.markdown(f"""
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Rajdhani:wght@400;500;600;700&family=Exo+2:wght@300;400;500;600&family=Share+Tech+Mono&display=swap" rel="stylesheet">
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.0/css/all.min.css">

<style>
/* ══ RESET & BASE ══════════════════════════════════════════════════════════ */
html, body, [class*="css"] {{
    font-family: 'Exo 2', sans-serif !important;
    background: {bg_primary} !important;
    color: {text_primary} !important;
}}
.main .block-container {{
    padding: 0.5rem 1.5rem 2rem !important;
    max-width: 1400px !important;
}}
[data-testid="stSidebar"] {{
    background: {sidebar_bg} !important;
    border-right: 1px solid {border} !important;
}}
[data-testid="stSidebar"] * {{ color: {text_primary} !important; }}

/* ══ ANIMATED HERO HEADER ══════════════════════════════════════════════════ */
.ag-hero {{
    position: relative;
    overflow: hidden;
    background: linear-gradient(135deg,
        {'#061428' if dark else '#c8ead8'} 0%,
        {'#0a2540' if dark else '#e8f5ee'} 40%,
        {'#061e14' if dark else '#d0f0e0'} 100%);
    border: 1px solid {border};
    border-radius: 20px;
    padding: 2rem 2.5rem;
    margin-bottom: 1.5rem;
    animation: heroReveal 0.8s ease-out;
}}
.ag-hero::before {{
    content: '';
    position: absolute; inset: 0;
    background:
        radial-gradient(ellipse 60% 40% at 80% 50%,
            {'rgba(0,255,136,0.07)' if dark else 'rgba(0,140,80,0.07)'} 0%, transparent 70%),
        radial-gradient(ellipse 40% 60% at 20% 80%,
            {'rgba(0,200,255,0.05)' if dark else 'rgba(0,100,200,0.04)'} 0%, transparent 70%);
    pointer-events: none;
}}
.ag-hero::after {{
    content: '';
    position: absolute;
    top: -2px; left: 0; right: 0; height: 3px;
    background: linear-gradient(90deg, transparent, {accent}, {accent2}, {accent}, transparent);
    animation: scanLine 3s ease-in-out infinite;
}}
@keyframes scanLine {{
    0%,100% {{ transform: scaleX(0); opacity:0; }}
    50% {{ transform: scaleX(1); opacity:1; }}
}}
@keyframes heroReveal {{
    from {{ opacity:0; transform:translateY(-20px); }}
    to   {{ opacity:1; transform:translateY(0); }}
}}

.hero-grid {{
    display: grid;
    grid-template-columns: auto 1fr auto;
    align-items: center;
    gap: 1.5rem;
}}
.hero-logo-wrap {{
    position: relative;
    width: 80px; height: 80px;
    display: flex; align-items: center; justify-content: center;
}}
.hero-logo-ring {{
    position: absolute; inset: 0;
    border: 2px solid {accent};
    border-radius: 50%;
    animation: rotateSlow 8s linear infinite;
    border-top-color: transparent; border-right-color: transparent;
}}
.hero-logo-ring2 {{
    position: absolute; inset: 6px;
    border: 1px solid {'rgba(0,200,255,0.4)' if dark else 'rgba(0,100,200,0.3)'};
    border-radius: 50%;
    animation: rotateSlow 5s linear infinite reverse;
    border-bottom-color: transparent;
}}
@keyframes rotateSlow {{ to {{ transform: rotate(360deg); }} }}

.hero-title {{
    font-family: 'Rajdhani', sans-serif !important;
    font-size: 2.4rem;
    font-weight: 700;
    letter-spacing: 3px;
    color: {accent} !important;
    text-shadow: {'0 0 30px rgba(0,255,136,0.4)' if dark else 'none'};
    margin: 0;
    line-height: 1.1;
}}
.hero-sub {{
    font-family: 'Exo 2', sans-serif;
    font-size: 0.85rem;
    color: {text_muted} !important;
    letter-spacing: 2px;
    text-transform: uppercase;
    margin-top: 4px;
}}
.hero-status {{
    display: flex; flex-direction: column; align-items: flex-end; gap: 6px;
}}
.status-pill {{
    display: flex; align-items: center; gap: 6px;
    background: {'rgba(0,255,136,0.1)' if dark else 'rgba(0,140,80,0.08)'};
    border: 1px solid {'rgba(0,255,136,0.3)' if dark else 'rgba(0,140,80,0.3)'};
    border-radius: 20px; padding: 4px 12px;
    font-size: 0.75rem; font-weight: 600;
    color: {accent} !important;
    font-family: 'Share Tech Mono', monospace;
}}
.status-dot {{
    width: 7px; height: 7px; border-radius: 50%;
    background: {accent};
    animation: pulse 1.5s ease-in-out infinite;
}}
@keyframes pulse {{
    0%,100% {{ opacity:1; transform:scale(1); box-shadow:0 0 0 0 rgba(0,255,136,0.4); }}
    50% {{ opacity:0.7; transform:scale(0.9); box-shadow:0 0 0 6px rgba(0,255,136,0); }}
}}

/* ══ METRIC ROW ════════════════════════════════════════════════════════════ */
.metrics-row {{
    display: grid;
    grid-template-columns: repeat(5, 1fr);
    gap: 10px;
    margin-bottom: 1.2rem;
}}
.metric-cell {{
    background: {bg_card};
    border: 1px solid {border};
    border-radius: 12px;
    padding: 12px 14px;
    text-align: center;
    transition: border-color 0.2s, transform 0.2s;
    animation: slideUp 0.5s ease-out both;
}}
.metric-cell:hover {{
    border-color: {accent};
    transform: translateY(-3px);
}}
.metric-val {{
    font-family: 'Rajdhani', sans-serif;
    font-size: 1.7rem; font-weight: 700;
    color: {accent} !important;
    line-height: 1;
}}
.metric-lbl {{
    font-size: 0.7rem; color: {text_muted} !important;
    text-transform: uppercase; letter-spacing: 1px;
    margin-top: 3px;
}}
@keyframes slideUp {{
    from {{ opacity:0; transform:translateY(16px); }}
    to   {{ opacity:1; transform:translateY(0); }}
}}

/* ══ TAB NAVIGATION ════════════════════════════════════════════════════════ */
.stTabs [data-baseweb="tab-list"] {{
    background: {panel_bg} !important;
    border: 1px solid {border} !important;
    border-radius: 12px !important;
    padding: 4px !important;
    gap: 3px !important;
}}
.stTabs [data-baseweb="tab"] {{
    font-family: 'Rajdhani', sans-serif !important;
    font-size: 0.9rem !important;
    font-weight: 600 !important;
    letter-spacing: 1px !important;
    text-transform: uppercase !important;
    border-radius: 9px !important;
    color: {text_muted} !important;
    padding: 8px 18px !important;
    transition: all 0.2s !important;
}}
.stTabs [aria-selected="true"] {{
    background: {'linear-gradient(135deg,rgba(0,255,136,0.15),rgba(0,200,255,0.1))' if dark else 'rgba(0,140,80,0.12)'} !important;
    color: {accent} !important;
    border: 1px solid {border} !important;
}}
.stTabs [data-baseweb="tab-panel"] {{
    background: transparent !important;
    padding: 1rem 0 !important;
}}

/* ══ CARDS ══════════════════════════════════════════════════════════════════ */
.ag-card {{
    background: {bg_card};
    border: 1px solid {border};
    border-radius: 14px;
    padding: 1.2rem 1.4rem;
    margin-bottom: 1rem;
    position: relative;
    overflow: hidden;
    transition: border-color 0.2s, transform 0.2s;
    animation: fadeCard 0.4s ease-out;
}}
.ag-card::before {{
    content: '';
    position: absolute; top:0; left:0; right:0; height:2px;
    opacity: 0;
    transition: opacity 0.2s;
}}
.ag-card:hover {{ border-color: {accent}; transform: translateY(-2px); }}
.ag-card:hover::before {{ opacity:1; }}
.ag-card-green::before  {{ background: linear-gradient(90deg,{accent},{accent2}); }}
.ag-card-red::before    {{ background: linear-gradient(90deg,#ff4444,#ff8800); }}
.ag-card-yellow::before {{ background: linear-gradient(90deg,#ffaa00,#ffdd00); }}
.ag-card-blue::before   {{ background: linear-gradient(90deg,{accent2},#8844ff); }}
@keyframes fadeCard {{
    from {{ opacity:0; transform:translateY(10px); }}
    to   {{ opacity:1; transform:translateY(0); }}
}}

/* ══ RESULT BANNERS ════════════════════════════════════════════════════════ */
.result-banner {{
    border-radius: 14px; padding: 1.2rem 1.4rem;
    margin-bottom: 1rem;
    display: flex; align-items: flex-start; gap: 14px;
    animation: bannerIn 0.5s cubic-bezier(0.34,1.56,0.64,1);
}}
@keyframes bannerIn {{
    from {{ opacity:0; transform:scale(0.92); }}
    to   {{ opacity:1; transform:scale(1); }}
}}
.result-banner.healthy {{
    background: {'rgba(0,255,136,0.08)' if dark else 'rgba(0,140,80,0.07)'};
    border: 1.5px solid {'rgba(0,255,136,0.4)' if dark else 'rgba(0,140,80,0.4)'};
}}
.result-banner.diseased {{
    background: {'rgba(255,60,60,0.08)' if dark else 'rgba(200,0,0,0.05)'};
    border: 1.5px solid {'rgba(255,80,80,0.4)' if dark else 'rgba(200,0,0,0.3)'};
}}
.banner-icon {{ font-size: 2.2rem; line-height: 1; }}
.banner-title {{
    font-family: 'Rajdhani', sans-serif;
    font-size: 1.4rem; font-weight: 700;
    color: {text_primary} !important;
    margin: 0 0 3px;
}}
.banner-disease {{
    font-size: 0.85rem; color: {text_muted} !important;
    font-family: 'Share Tech Mono', monospace;
}}

/* ══ CONFIDENCE METER ══════════════════════════════════════════════════════ */
.conf-wrap {{
    background: {panel_bg};
    border: 1px solid {border};
    border-radius: 10px;
    padding: 12px 14px;
    margin: 10px 0;
}}
.conf-header {{
    display: flex; justify-content: space-between;
    font-size: 0.75rem; color: {text_muted} !important;
    margin-bottom: 7px; font-family:'Exo 2',sans-serif;
    text-transform: uppercase; letter-spacing: 1px;
}}
.conf-pct {{
    font-family: 'Rajdhani', sans-serif;
    font-size: 1.1rem; font-weight: 700;
    color: {accent} !important;
}}
.conf-track {{
    height: 8px;
    background: {'rgba(255,255,255,0.06)' if dark else '#e0e8e4'};
    border-radius: 99px; overflow: hidden;
}}
.conf-fill {{
    height: 100%; border-radius: 99px;
    background: linear-gradient(90deg, {accent}, {accent2});
    transition: width 1s cubic-bezier(0.25, 1, 0.5, 1);
    position: relative;
}}
.conf-fill::after {{
    content: '';
    position: absolute; right:0; top:0; bottom:0; width:12px;
    background: {'rgba(255,255,255,0.5)' if dark else 'rgba(255,255,255,0.7)'};
    filter: blur(3px);
    animation: shimmer 1.5s ease-in-out infinite;
}}
@keyframes shimmer {{
    0%,100% {{ opacity:0.3; }} 50% {{ opacity:0.9; }}
}}

/* ══ SEVERITY BADGE ════════════════════════════════════════════════════════ */
.sev-badge {{
    display: inline-flex; align-items: center; gap: 5px;
    padding: 4px 12px; border-radius: 20px;
    font-size: 0.72rem; font-weight: 700;
    letter-spacing: 1.5px; text-transform: uppercase;
    font-family: 'Share Tech Mono', monospace;
}}
.sev-critical {{ background:rgba(255,30,30,0.15); color:#ff5555 !important; border:1px solid rgba(255,50,50,0.4); }}
.sev-high     {{ background:rgba(255,140,0,0.12); color:#ff9900 !important; border:1px solid rgba(255,140,0,0.35); }}
.sev-medium   {{ background:rgba(255,220,0,0.1);  color:#ddaa00 !important; border:1px solid rgba(255,200,0,0.3); }}
.sev-low,
.sev-none     {{ background:rgba(0,255,136,0.08); color:{accent} !important; border:1px solid rgba(0,255,136,0.3); }}

/* ══ SECTION TITLES ════════════════════════════════════════════════════════ */
.section-title {{
    font-family: 'Rajdhani', sans-serif;
    font-size: 0.75rem; font-weight: 700;
    text-transform: uppercase; letter-spacing: 2.5px;
    color: {text_muted} !important;
    margin: 1rem 0 0.6rem;
    display: flex; align-items: center; gap: 8px;
}}
.section-title::after {{
    content: ''; flex:1; height:1px;
    background: linear-gradient(90deg, {border}, transparent);
}}

/* ══ INFO GRID ══════════════════════════════════════════════════════════════ */
.info-grid {{
    display: grid; grid-template-columns: 1fr 1fr; gap: 8px;
}}
.info-item {{
    background: {panel_bg};
    border: 1px solid {border};
    border-radius: 8px; padding: 10px 12px;
}}
.info-lbl {{
    font-size: 0.68rem; text-transform: uppercase; letter-spacing: 1.2px;
    color: {text_muted} !important; margin-bottom: 3px;
}}
.info-val {{
    font-size: 0.82rem; color: {text_primary} !important; line-height: 1.4;
}}

/* ══ WEATHER CARDS ══════════════════════════════════════════════════════════ */
.wx-card {{
    background: {bg_card};
    border: 1px solid {border};
    border-radius: 14px; padding: 1rem;
    text-align: center;
    transition: all 0.2s;
    animation: slideUp 0.4s ease-out both;
}}
.wx-card:hover {{
    border-color: {accent};
    background: {'rgba(0,255,136,0.04)' if dark else 'rgba(0,140,80,0.04)'};
    transform: translateY(-4px);
}}
.wx-date {{ font-size: 0.72rem; letter-spacing: 1.5px; text-transform:uppercase; color:{text_muted} !important; }}
.wx-icon {{ font-size: 2.2rem; margin: 6px 0; }}
.wx-temp {{
    font-family: 'Rajdhani', sans-serif; font-size: 2rem; font-weight: 700;
    color: {accent} !important; line-height: 1;
}}
.wx-detail {{ font-size: 0.75rem; color: {text_muted} !important; margin-top: 4px; }}
.wx-alert {{
    font-size: 0.7rem; margin-top: 8px;
    padding: 4px 8px; border-radius: 6px;
    font-family: 'Exo 2', sans-serif;
}}
.wx-warn {{ background:rgba(255,170,0,0.12); color:#ddaa00 !important; border:1px solid rgba(255,170,0,0.3); }}
.wx-ok   {{ background:rgba(0,255,136,0.07); color:{accent} !important; border:1px solid rgba(0,255,136,0.2); }}

/* ══ CHAT ═══════════════════════════════════════════════════════════════════ */
.chat-viewport {{
    background: {panel_bg};
    border: 1px solid {border};
    border-radius: 14px;
    padding: 14px;
    max-height: 400px;
    overflow-y: auto;
    scrollbar-width: thin;
    scrollbar-color: {border} transparent;
}}
.chat-msg-user {{
    display: flex; justify-content: flex-end; margin: 6px 0;
}}
.chat-msg-bot {{
    display: flex; justify-content: flex-start; margin: 6px 0; gap: 8px;
    align-items: flex-end;
}}
.chat-bubble-user {{
    background: {'linear-gradient(135deg,rgba(0,255,136,0.2),rgba(0,200,255,0.15))' if dark else 'rgba(0,140,80,0.12)'};
    border: 1px solid {border};
    border-radius: 16px 16px 4px 16px;
    padding: 8px 14px; max-width: 75%;
    font-size: 0.875rem; color: {text_primary} !important;
}}
.chat-bubble-bot {{
    background: {bg_card};
    border: 1px solid {border};
    border-radius: 16px 16px 16px 4px;
    padding: 8px 14px; max-width: 75%;
    font-size: 0.875rem; color: {text_primary} !important;
}}
.bot-avatar {{
    width: 28px; height: 28px; border-radius: 50%;
    background: {'linear-gradient(135deg,rgba(0,255,136,0.3),rgba(0,200,255,0.3))' if dark else 'rgba(0,140,80,0.15)'};
    border: 1px solid {border};
    display: flex; align-items: center; justify-content: center;
    font-size: 14px; flex-shrink: 0;
}}

/* ══ HISTORY TABLE ══════════════════════════════════════════════════════════ */
.hist-row {{
    background: {bg_card};
    border: 1px solid {border};
    border-radius: 10px;
    padding: 10px 14px;
    margin-bottom: 6px;
    display: flex; align-items: center; gap: 12px;
    transition: border-color 0.2s;
    animation: slideUp 0.3s ease-out both;
}}
.hist-row:hover {{ border-color: {accent}; }}
.hist-sev-dot {{ width:10px; height:10px; border-radius:50%; flex-shrink:0; }}
.hist-disease {{ font-weight:600; font-size:0.9rem; color:{text_primary} !important; }}
.hist-meta {{ font-size:0.75rem; color:{text_muted} !important; margin-top:2px; }}
.hist-conf {{
    margin-left: auto; flex-shrink:0;
    font-family:'Rajdhani',sans-serif; font-size:1.1rem;
    font-weight:700; color:{accent} !important;
}}

/* ══ BUTTONS ════════════════════════════════════════════════════════════════ */
.stButton>button {{
    background: {'linear-gradient(135deg,rgba(0,255,136,0.15),rgba(0,200,255,0.1))' if dark else 'rgba(0,140,80,0.1)'} !important;
    color: {accent} !important;
    border: 1px solid {border} !important;
    border-radius: 8px !important;
    font-family: 'Rajdhani', sans-serif !important;
    font-size: 0.9rem !important;
    font-weight: 600 !important;
    letter-spacing: 1px !important;
    text-transform: uppercase !important;
    width: 100% !important;
    transition: all 0.2s !important;
}}
.stButton>button:hover {{
    border-color: {accent} !important;
    background: {'rgba(0,255,136,0.2)' if dark else 'rgba(0,140,80,0.18)'} !important;
    transform: translateY(-1px) !important;
}}

/* ══ INPUTS ═════════════════════════════════════════════════════════════════ */
.stTextInput>div>div>input, .stTextArea>div>div>textarea {{
    background: {panel_bg} !important;
    color: {text_primary} !important;
    border: 1px solid {border} !important;
    border-radius: 8px !important;
    font-family: 'Exo 2', sans-serif !important;
}}
.stTextInput>div>div>input:focus, .stTextArea>div>div>textarea:focus {{
    border-color: {accent} !important;
    box-shadow: 0 0 0 2px {'rgba(0,255,136,0.15)' if dark else 'rgba(0,140,80,0.12)'} !important;
}}

/* ══ FILE UPLOADER ══════════════════════════════════════════════════════════ */
[data-testid="stFileUploader"] {{
    background: {panel_bg} !important;
    border: 2px dashed {border} !important;
    border-radius: 14px !important;
    padding: 1rem !important;
    transition: border-color 0.2s !important;
}}
[data-testid="stFileUploader"]:hover {{
    border-color: {accent} !important;
}}

/* ══ SCAN PROGRESS ══════════════════════════════════════════════════════════ */
.scan-anim {{
    display: flex; align-items: center; gap: 10px;
    background: {panel_bg}; border: 1px solid {border};
    border-radius: 10px; padding: 10px 14px;
    font-family: 'Share Tech Mono', monospace;
    font-size: 0.8rem; color: {accent} !important;
}}
.scan-bar {{
    flex:1; height:4px; background:{'rgba(255,255,255,0.06)' if dark else '#e0e8e4'};
    border-radius:99px; overflow:hidden;
}}
.scan-bar-fill {{
    height:100%; border-radius:99px;
    background: linear-gradient(90deg, {accent}, {accent2});
    animation: scanProgress 2s ease-in-out infinite;
}}
@keyframes scanProgress {{
    0%   {{ width:0%; margin-left:0; }}
    50%  {{ width:60%; }}
    100% {{ width:0%; margin-left:100%; }}
}}

/* ══ DOWNLOAD BUTTON ════════════════════════════════════════════════════════ */
.dl-btn {{
    display: block; text-decoration:none !important;
    background: {'linear-gradient(135deg,rgba(0,255,136,0.15),rgba(0,200,255,0.1))' if dark else 'rgba(0,140,80,0.1)'};
    border: 1px solid {border};
    border-radius: 8px;
    padding: 10px 16px;
    text-align: center;
    font-family: 'Rajdhani', sans-serif;
    font-size: 0.9rem; font-weight:600; letter-spacing:1px;
    color: {accent} !important;
    transition: all 0.2s; margin-top:10px;
    text-transform: uppercase;
}}
.dl-btn:hover {{
    border-color: {accent};
    background: {'rgba(0,255,136,0.2)' if dark else 'rgba(0,140,80,0.18)'};
}}

/* ══ VOICE PANEL ════════════════════════════════════════════════════════════ */
.voice-panel {{
    background: {panel_bg};
    border: 1px solid {border};
    border-radius: 14px; padding: 1.2rem;
    text-align: center; margin-bottom: 1rem;
}}
.voice-icon {{
    font-size: 2.5rem; margin-bottom: 8px;
    animation: voicePulse 2s ease-in-out infinite;
}}
@keyframes voicePulse {{
    0%,100% {{ transform:scale(1); filter:drop-shadow(0 0 0px {'#00ff88' if dark else '#008c50'}); }}
    50%      {{ transform:scale(1.08); filter:drop-shadow(0 0 12px {'#00ff88' if dark else '#008c50'}); }}
}}

/* ══ SCROLLBAR ══════════════════════════════════════════════════════════════ */
::-webkit-scrollbar {{ width:5px; height:5px; }}
::-webkit-scrollbar-track {{ background: transparent; }}
::-webkit-scrollbar-thumb {{ background:{border}; border-radius:99px; }}

/* ══ RADIO / TOGGLE ═════════════════════════════════════════════════════════ */
[data-testid="stRadio"] label {{
    color: {text_primary} !important;
    font-family: 'Exo 2', sans-serif !important;
}}

/* ══ DIVIDER ════════════════════════════════════════════════════════════════ */
hr {{ border:none !important; height:1px !important;
    background: linear-gradient(90deg,transparent,{border},transparent) !important;
    margin: 0.8rem 0 !important; }}

/* ══ FOOTER ═════════════════════════════════════════════════════════════════ */
.ag-footer {{
    text-align: center; padding: 2rem 1rem 1rem;
    border-top: 1px solid {border};
    color: {text_muted} !important;
    font-size: 0.72rem; letter-spacing: 1px;
    font-family: 'Share Tech Mono', monospace;
    margin-top: 2rem;
}}

/* ══ QUICK TIPS BAR ═════════════════════════════════════════════════════════ */
.tip-ticker {{
    background: {'rgba(0,255,136,0.05)' if dark else 'rgba(0,140,80,0.05)'};
    border: 1px solid {border};
    border-radius: 8px; padding: 7px 14px;
    font-size: 0.75rem; color: {text_muted} !important;
    font-family: 'Share Tech Mono', monospace;
    overflow: hidden; white-space: nowrap;
    margin-bottom: 1rem;
}}
.tip-ticker span {{ animation: ticker 20s linear infinite; display:inline-block; }}
@keyframes ticker {{ 0% {{transform:translateX(100%);}} 100% {{transform:translateX(-100%);}} }}

/* ══ SIDEBAR LOGO ═══════════════════════════════════════════════════════════ */
.sb-logo-wrap {{
    text-align: center; padding: 1.2rem 0 0.8rem;
}}
.sb-logo-title {{
    font-family: 'Rajdhani', sans-serif;
    font-size: 1.3rem; font-weight: 700;
    color: {accent} !important; letter-spacing: 2px;
}}
.sb-logo-sub {{
    font-size: 0.65rem; color: {text_muted} !important;
    letter-spacing: 2px; text-transform: uppercase;
}}

/* ══ STAGGER DELAYS ═════════════════════════════════════════════════════════ */
.d1 {{ animation-delay: 0.05s; }}
.d2 {{ animation-delay: 0.10s; }}
.d3 {{ animation-delay: 0.15s; }}
.d4 {{ animation-delay: 0.20s; }}
.d5 {{ animation-delay: 0.25s; }}

/* Streamlit metric overrides */
[data-testid="stMetric"] {{
    background: {bg_card} !important;
    border: 1px solid {border} !important;
    border-radius: 10px !important;
    padding: 10px !important;
}}
[data-testid="stMetric"] label {{ color: {text_muted} !important; font-size:0.72rem !important; }}
[data-testid="stMetricValue"] {{ color: {accent} !important;
    font-family:'Rajdhani',sans-serif !important; }}

/* Info/warning/error boxes */
.stAlert {{ border-radius: 10px !important; border: 1px solid {border} !important; }}

/* Caption */
.stCaption {{ color: {text_muted} !important; font-size:0.72rem !important; }}

</style>
""", unsafe_allow_html=True)

load_css(is_dark)

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    # Logo SVG
    st.markdown(f"""
    <div class="sb-logo-wrap">
        <svg width="72" height="72" viewBox="0 0 72 72" fill="none" xmlns="http://www.w3.org/2000/svg">
          <circle cx="36" cy="36" r="34" stroke="{'#00ff88' if is_dark else '#008c50'}" stroke-width="1.5" stroke-dasharray="4 2"/>
          <circle cx="36" cy="36" r="26" fill="{'rgba(0,255,136,0.08)' if is_dark else 'rgba(0,140,80,0.08)'}"/>
          <path d="M36 18 C36 18, 48 26, 48 38 C48 50, 36 54, 36 54 C36 54, 24 50, 24 38 C24 26, 36 18 36 18Z"
                fill="{'rgba(0,255,136,0.15)' if is_dark else 'rgba(0,140,80,0.12)'}"
                stroke="{'#00ff88' if is_dark else '#008c50'}" stroke-width="1.5"/>
          <path d="M36 28 C36 28, 42 32, 42 38 C42 44, 36 47, 36 47 C36 47, 30 44, 30 38 C30 32, 36 28 36 28Z"
                fill="{'rgba(0,200,255,0.2)' if is_dark else 'rgba(0,100,200,0.12)'}"/>
          <line x1="36" y1="18" x2="36" y2="54" stroke="{'#00ff88' if is_dark else '#008c50'}" stroke-width="1"/>
          <circle cx="36" cy="36" r="3" fill="{'#00ff88' if is_dark else '#008c50'}"/>
          <path d="M20 36 Q28 30 36 36 Q44 42 52 36" stroke="{'rgba(0,200,255,0.6)' if is_dark else 'rgba(0,100,200,0.5)'}" stroke-width="1" fill="none"/>
        </svg>
        <div class="sb-logo-title">AGROGUARD</div>
        <div class="sb-logo-sub">AI · v4.0 · Hardware Ready</div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("---")

    # Theme toggle
    theme_choice = st.radio("🎨 Theme", ["Dark Mode", "Light Mode"],
                             index=0 if is_dark else 1, horizontal=True)
    if (theme_choice == "Dark Mode") != is_dark:
        st.session_state.theme = "dark" if theme_choice == "Dark Mode" else "light"
        st.rerun()

    # Language
    lang_choice = st.radio("🌐 Language / மொழி", ["English", "தமிழ்"], horizontal=True,
                            index=0 if lang == "English" else 1)
    if lang_choice != lang:
        st.session_state.language = lang_choice
        st.rerun()

    st.markdown("---")

    model, class_names = load_model_assets()
    m_status = "ONLINE" if model else "MODEL MISSING"
    m_color  = "#00ff88" if model else "#ff4444"
    st.markdown(f"""
    <div style="background:{'rgba(0,255,136,0.06)' if model else 'rgba(255,60,60,0.06)'};
               border:1px solid {m_color + '44'};border-radius:10px;
               padding:10px;text-align:center;margin:6px 0;">
        <div style="font-family:'Share Tech Mono',monospace;font-size:0.75rem;
                    color:{m_color};letter-spacing:2px;">
            {'◉' if model else '○'} AI ENGINE: {m_status}
        </div>
    </div>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns(3)
    col1.metric("Crops", "3")
    col2.metric("Classes", "15")
    col3.metric("Val Acc", "92.6%")

    st.markdown("---")
    st.markdown("""
    <div style="font-family:'Share Tech Mono',monospace;font-size:0.68rem;
                opacity:0.6;line-height:2;letter-spacing:0.5px;">
    ① Upload leaf photo<br>
    ② AI scans & diagnoses<br>
    ③ View treatment plan<br>
    ④ Check weather risk<br>
    ⑤ Download HTML report<br>
    ⑥ Submit feedback
    </div>
    """, unsafe_allow_html=True)

    # Feedback count
    if os.path.isfile(FEEDBACK_FILE):
        try:
            with open(FEEDBACK_FILE, encoding="utf-8") as f:
                n = sum(1 for _ in f) - 1
            if n > 0:
                st.markdown(f"""
                <div style="margin-top:12px;font-size:0.7rem;
                            font-family:'Share Tech Mono',monospace;opacity:0.6;
                            text-align:center;">
                    📊 {n} DIAGNOSES LOGGED
                </div>""", unsafe_allow_html=True)
        except Exception:
            pass

# ── Hero header ───────────────────────────────────────────────────────────────
feedback_count = 0
if os.path.isfile(FEEDBACK_FILE):
    try:
        with open(FEEDBACK_FILE, encoding="utf-8") as f:
            feedback_count = max(0, sum(1 for _ in f) - 1)
    except Exception:
        feedback_count = 0

st.markdown(f"""
<div class="ag-hero">
  <div class="hero-grid">
    <div class="hero-logo-wrap">
      <div class="hero-logo-ring"></div>
      <div class="hero-logo-ring2"></div>
      <svg width="48" height="48" viewBox="0 0 48 48" fill="none">
        <circle cx="24" cy="24" r="20" fill="{'rgba(0,255,136,0.1)' if is_dark else 'rgba(0,140,80,0.1)'}"/>
        <path d="M24 8 C24 8, 36 15, 36 26 C36 37, 24 41, 24 41 C24 41, 12 37, 12 26 C12 15, 24 8 24 8Z"
              fill="{'rgba(0,255,136,0.2)' if is_dark else 'rgba(0,140,80,0.18)'}"
              stroke="{'#00ff88' if is_dark else '#008c50'}" stroke-width="1.5"/>
        <circle cx="24" cy="26" r="5" fill="{'rgba(0,200,255,0.3)' if is_dark else 'rgba(0,100,200,0.2)'}"/>
        <line x1="24" y1="8" x2="24" y2="41" stroke="{'#00ff88' if is_dark else '#008c50'}" stroke-width="1"/>
        <path d="M14 26 Q19 21 24 26 Q29 31 34 26" stroke="{'rgba(0,200,255,0.7)' if is_dark else 'rgba(0,100,200,0.6)'}" stroke-width="1.2" fill="none"/>
      </svg>
    </div>
    <div>
      <div class="hero-title">{txt['app_title_short']}</div>
      <div class="hero-sub">{txt['subtitle']} — {txt['tagline']}</div>
    </div>
    <div class="hero-status">
      <div class="status-pill"><div class="status-dot"></div> AI ACTIVE</div>
      <div class="status-pill" style="border-color:{'rgba(0,200,255,0.3)' if is_dark else 'rgba(0,100,200,0.3)'};
                                       color:{'#00c8ff' if is_dark else '#0066cc'} !important;
                                       background:{'rgba(0,200,255,0.08)' if is_dark else 'rgba(0,100,200,0.06)'} !important;">
        🌾 {feedback_count} SCANS
      </div>
    </div>
  </div>
</div>
""", unsafe_allow_html=True)

# ── Metrics row ───────────────────────────────────────────────────────────────
st.markdown(f"""
<div class="metrics-row">
  <div class="metric-cell d1"><div class="metric-val">3</div><div class="metric-lbl">Crops Supported</div></div>
  <div class="metric-cell d2"><div class="metric-val">15</div><div class="metric-lbl">Disease Classes</div></div>
  <div class="metric-cell d3"><div class="metric-val">92.6%</div><div class="metric-lbl">Val Accuracy</div></div>
  <div class="metric-cell d4"><div class="metric-val">2</div><div class="metric-lbl">Languages</div></div>
  <div class="metric-cell d5"><div class="metric-val">24/7</div><div class="metric-lbl">Field Ready</div></div>
</div>
""", unsafe_allow_html=True)

# ── Ticker ────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="tip-ticker">
  <span>
    🌿 TIP: Spray fungicides early morning or evening for best results &nbsp;·&nbsp;
    💧 High humidity (>80%) increases fungal disease risk — inspect daily &nbsp;·&nbsp;
    🔄 Rotate crops every 3–4 years to break disease cycles &nbsp;·&nbsp;
    ☀️ Dry sunny days are ideal for chemical application &nbsp;·&nbsp;
    🌱 Apply compost before monsoon season for stronger plants
  </span>
</div>
""", unsafe_allow_html=True)

# ── Tabs ──────────────────────────────────────────────────────────────────────
tabs = st.tabs(["🔬  SCAN LEAF", "🌤  WEATHER", "📋  HISTORY", "💬  AGROBOT", "🎤  VOICE", "🧪  FIELD UNIT (Prototype Sensor Mode)"])


# ══════════════════════════════════════════════════════════════════════════════
# TAB 1 — SCAN
# ══════════════════════════════════════════════════════════════════════════════
with tabs[0]:
    if model is None:
        st.error("⚠️ AI model not found. Place `agroguard_model.keras` and `class_indices.json` in the `models/` folder.")
        st.stop()

    up_col, _ = st.columns([1, 0.02])
    with up_col:
        st.markdown('<div class="section-title">📁 Upload Leaf Image</div>', unsafe_allow_html=True)
        uploaded = st.file_uploader(
            txt["choose_image"],
            type=["jpg", "jpeg", "png"],
            accept_multiple_files=True,
            label_visibility="collapsed",
        )

    if not uploaded:
        st.markdown(f"""
        <div style="text-align:center;padding:3rem 1rem;opacity:0.5;">
          <div style="font-size:3.5rem;">🍃</div>
          <div style="font-family:'Rajdhani',sans-serif;font-size:1.1rem;
                      letter-spacing:2px;text-transform:uppercase;margin-top:8px;">
            {txt['upload_prompt']}
          </div>
          <div style="font-size:0.78rem;margin-top:6px;font-family:'Share Tech Mono',monospace;">
            TOMATO · POTATO · BELL PEPPER
          </div>
        </div>
        """, unsafe_allow_html=True)
    else:
        for idx, file in enumerate(uploaded):
            st.markdown(f'<div class="section-title">🖼 {file.name}</div>', unsafe_allow_html=True)
            img_col, res_col = st.columns([1, 1.6], gap="large")

            img = Image.open(file)
            img_col.image(img, use_container_width=True, caption="Uploaded leaf sample")

            with img_col:
                # Thumbnail in session history (store filename)
                pass

            with res_col:
                # Scan animation
                st.markdown("""
                <div class="scan-anim">
                  <span>⚡ ANALYZING</span>
                  <div class="scan-bar"><div class="scan-bar-fill"></div></div>
                  <span>CNN MODEL</span>
                </div>
                """, unsafe_allow_html=True)

                with st.spinner(""):
                    arr = preprocess_image(img)
                    best_class, confidence, top5, _ = predict_with_confidence(model, arr, class_names)

                crop_type     = next((c for c in SUPPORTED_CROPS if c.lower() in best_class.lower()), None)
                disease_label = best_class.split("___")[-1].replace("_", " ") if "___" in best_class else best_class
                is_healthy    = "healthy" in best_class.lower()
                treatment     = get_treatment(best_class)
                fertilizer    = get_fertilizer(crop_type, disease_label) if crop_type else {}
                severity      = treatment.get("severity", "Unknown")

                # Result banner
                banner_cls  = "healthy" if is_healthy else "diseased"
                banner_icon = "✅" if is_healthy else "🚨"
                headline    = txt["healthy_plant"] if is_healthy else txt["disease_detected"]

                sev_key = severity.lower().replace(" ", "")
                st.markdown(f"""
                <div class="result-banner {banner_cls}">
                  <div class="banner-icon">{banner_icon}</div>
                  <div>
                    <div class="banner-title">{headline}</div>
                    <div class="banner-disease">{disease_label.upper()}</div>
                    <div style="margin-top:8px;">
                      {'Crop: <strong>' + (crop_type or '—') + '</strong> &nbsp;|&nbsp;' if crop_type else ''}
                      <span class="sev-badge sev-{sev_key}">{severity}</span>
                    </div>
                  </div>
                </div>
                """, unsafe_allow_html=True)

                # Confidence
                st.markdown(f"""
                <div class="conf-wrap">
                  <div class="conf-header">
                    <span>AI Confidence Score</span>
                    <span class="conf-pct">{confidence:.1f}%</span>
                  </div>
                  <div class="conf-track">
                    <div class="conf-fill" style="width:{confidence:.1f}%;"></div>
                  </div>
                </div>
                """, unsafe_allow_html=True)

                # Top-5
                with st.expander("🔍 Top-5 prediction breakdown"):
                    for cls_n, prob in top5:
                        lbl = cls_n.split("___")[-1].replace("_", " ") if "___" in cls_n else cls_n
                        st.progress(prob / 100, text=f"{lbl}: {prob:.1f}%")

                # Treatment
                st.markdown(f'<div class="section-title">🛠 {txt["treatment_plan"]}</div>', unsafe_allow_html=True)
                if not is_healthy:
                    st.markdown(f"""
                    <div class="ag-card ag-card-yellow">
                      <div class="info-grid">
                        <div class="info-item">
                          <div class="info-lbl">⚗️ Chemical</div>
                          <div class="info-val">{treatment.get('pesticide','—')}</div>
                        </div>
                        <div class="info-item">
                          <div class="info-lbl">🌿 Organic</div>
                          <div class="info-val">{treatment.get('organic','—')}</div>
                        </div>
                        <div class="info-item">
                          <div class="info-lbl">⚠️ Precaution</div>
                          <div class="info-val">{treatment.get('precaution','—')}</div>
                        </div>
                        <div class="info-item">
                          <div class="info-lbl">⏱ Apply Every</div>
                          <div class="info-val">{treatment.get('treatment_days','Consult expert')}</div>
                        </div>
                      </div>
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    st.markdown(f"""
                    <div class="ag-card ag-card-green">
                      <div style="font-size:0.85rem;line-height:2;">
                        ✅ {txt['water_morning']}<br>
                        ✅ {txt['proper_spacing']}<br>
                        ✅ {txt['organic_fertilizer']}<br>
                        ✅ {txt['regular_inspection']}<br>
                        ✅ {txt['crop_rotation']}
                      </div>
                    </div>
                    """, unsafe_allow_html=True)

                # Fertilizer
                if fertilizer:
                    st.markdown(f'<div class="section-title">🌱 {txt["fertilizer_recommendation"]}</div>', unsafe_allow_html=True)
                    st.markdown(f"""
                    <div class="ag-card ag-card-blue">
                      <div class="info-grid">
                        <div class="info-item">
                          <div class="info-lbl">🟢 Nitrogen (N)</div>
                          <div class="info-val">{fertilizer.get('N','—')}</div>
                        </div>
                        <div class="info-item">
                          <div class="info-lbl">🔵 Phosphorus (P)</div>
                          <div class="info-val">{fertilizer.get('P','—')}</div>
                        </div>
                        <div class="info-item">
                          <div class="info-lbl">🟣 Potassium (K)</div>
                          <div class="info-val">{fertilizer.get('K','—')}</div>
                        </div>
                        <div class="info-item">
                          <div class="info-lbl">📋 Application</div>
                          <div class="info-val">{fertilizer.get('application','—')}</div>
                        </div>
                      </div>
                    </div>
                    """, unsafe_allow_html=True)

                # Download report
                report_html = generate_report(disease_label, crop_type, confidence, treatment, fertilizer)
                b64 = base64.b64encode(report_html.encode()).decode()
                ts  = datetime.now().strftime("%Y%m%d_%H%M%S")
                st.markdown(
                    f'<a class="dl-btn" href="data:text/html;base64,{b64}" '
                    f'download="agroguard_report_{ts}.html">📥 {txt["export_report"]}</a>',
                    unsafe_allow_html=True
                )

                # Feedback
                st.markdown(f'<div class="section-title">💬 {txt["feedback"]}</div>', unsafe_allow_html=True)
                fb1, fb2 = st.columns(2)
                fkey = f"fb_{idx}_{file.name}"
                if fb1.button(txt["feedback_correct"], key=f"ok_{fkey}"):
                    if save_feedback(file.name, best_class, "", True):
                        st.success("✅ " + txt["feedback_saved"])
                        st.balloons()
                    else:
                        st.error("⚠️ Could not save feedback (file locked or permission error).")
                if fb2.button(txt["feedback_wrong"], key=f"no_{fkey}"):
                    comment = st.text_input("What's the correct diagnosis?", key=f"cmt_{fkey}",
                                            placeholder="Enter correct disease name…")
                    if comment:
                        if save_feedback(file.name, best_class, comment, False):
                            st.success("✅ " + txt["feedback_saved"])
                        else:
                            st.error("⚠️ Could not save feedback (file locked or permission error).")

            # Save to history
            entry = {
                "ts": datetime.now().strftime("%Y-%m-%d %H:%M"),
                "file": file.name,
                "disease": disease_label,
                "crop": crop_type or "—",
                "conf": f"{confidence:.1f}",
                "severity": severity,
            }
            if not any(e["file"] == file.name for e in st.session_state.scan_history):
                st.session_state.scan_history.insert(0, entry)

            st.markdown("---")

# ══════════════════════════════════════════════════════════════════════════════
# TAB 2 — WEATHER
# ══════════════════════════════════════════════════════════════════════════════
with tabs[1]:
    st.markdown('<div class="section-title">🌦 3-Day Farming Forecast</div>', unsafe_allow_html=True)
    forecast  = get_3day_forecast()
    lang_code = "en" if lang == "English" else "ta"

    if forecast:
        w1, w2, w3 = st.columns(3)
        sky_map = {"clear": "☀️", "clouds": "☁️", "rain": "🌧️", "drizzle": "🌦️", "thunderstorm": "⛈️", "snow": "❄️", "mist": "🌫️"}
        for wcol, day in zip([w1, w2, w3], forecast):
            prec    = get_weather_precaution(day["hum"], day["sky"], day["temp"], lang_code)
            sky_low = day["sky"].lower()
            icon    = next((v for k, v in sky_map.items() if k in sky_low), "🌤️")
            alert_c = "wx-warn" if "⚠️" in prec else "wx-ok"
            with wcol:
                st.markdown(f"""
                <div class="wx-card">
                  <div class="wx-date">{day['date']}</div>
                  <div class="wx-icon">{icon}</div>
                  <div class="wx-temp">{day['temp']:.1f}°C</div>
                  <div class="wx-detail">{day['sky']} &nbsp;·&nbsp; 💧 {day['hum']:.0f}%</div>
                  <div class="wx-alert {alert_c}">{prec}</div>
                </div>
                """, unsafe_allow_html=True)

    st.markdown("---")
    st.markdown('<div class="section-title">📊 Disease Risk Matrix</div>', unsafe_allow_html=True)

    risk_col1, risk_col2 = st.columns(2)
    with risk_col1:
        st.markdown(f"""
        <div class="ag-card ag-card-red">
          <div style="font-family:'Rajdhani',sans-serif;font-size:1rem;font-weight:700;margin-bottom:10px;
                      letter-spacing:1px;">🔴 HIGH RISK CONDITIONS</div>
          <div class="info-grid">
            <div class="info-item"><div class="info-lbl">Humidity</div><div class="info-val">&gt; 80% — Fungal outbreak risk</div></div>
            <div class="info-item"><div class="info-lbl">Rain</div><div class="info-val">Delay all chemical sprays</div></div>
            <div class="info-item"><div class="info-lbl">Temp</div><div class="info-val">&gt; 32°C — Heat stress, mite risk</div></div>
            <div class="info-item"><div class="info-lbl">Night Dew</div><div class="info-val">Late blight trigger zone</div></div>
          </div>
        </div>
        """, unsafe_allow_html=True)
    with risk_col2:
        st.markdown(f"""
        <div class="ag-card ag-card-green">
          <div style="font-family:'Rajdhani',sans-serif;font-size:1rem;font-weight:700;margin-bottom:10px;
                      letter-spacing:1px;">🟢 IDEAL CONDITIONS</div>
          <div class="info-grid">
            <div class="info-item"><div class="info-lbl">Spray Day</div><div class="info-val">Sunny, low wind, dry leaves</div></div>
            <div class="info-item"><div class="info-lbl">Transplant</div><div class="info-val">Cloudy, mild temperature</div></div>
            <div class="info-item"><div class="info-lbl">Fertilise</div><div class="info-val">No rain forecast 24 h</div></div>
            <div class="info-item"><div class="info-lbl">Harvest</div><div class="info-val">Dry, 18–26°C window</div></div>
          </div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown('<div class="section-title">📅 Seasonal Disease Calendar</div>', unsafe_allow_html=True)
    st.markdown(f"""
    <div class="ag-card">
      <div class="info-grid">
        <div class="info-item"><div class="info-lbl">🌧 Monsoon (Jun–Sep)</div>
          <div class="info-val">Late blight, Leaf mold, Bacterial spot — CRITICAL PERIOD</div></div>
        <div class="info-item"><div class="info-lbl">🌞 Summer (Mar–May)</div>
          <div class="info-val">Spider mites, Target spot — inspect twice weekly</div></div>
        <div class="info-item"><div class="info-lbl">🍂 Post-monsoon (Oct–Nov)</div>
          <div class="info-val">Early blight, Septoria — preventive spraying advised</div></div>
        <div class="info-item"><div class="info-lbl">❄️ Winter (Dec–Feb)</div>
          <div class="info-val">Mosaic virus via aphids — use yellow sticky traps</div></div>
      </div>
    </div>
    """, unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# TAB 3 — HISTORY
# ══════════════════════════════════════════════════════════════════════════════
with tabs[2]:
    st.markdown('<div class="section-title">📋 Scan History — This Session</div>', unsafe_allow_html=True)

    history = st.session_state.scan_history
    sev_colors = {"critical": "#ff4444", "high": "#ff9900", "medium": "#ddaa00", "low": "#00ff88", "none": "#00ff88", "unknown": "#888"}

    if not history:
        st.markdown("""
        <div style="text-align:center;padding:3rem;opacity:0.4;">
          <div style="font-size:2.5rem;">📂</div>
          <div style="font-family:'Rajdhani',sans-serif;letter-spacing:2px;
                      text-transform:uppercase;margin-top:8px;">No Scans Yet</div>
        </div>
        """, unsafe_allow_html=True)
    else:
        # Summary stats
        total   = len(history)
        diseased = sum(1 for e in history if e["severity"].lower() not in ("none", "unknown"))
        critical = sum(1 for e in history if e["severity"].lower() == "critical")
        avg_conf = sum(float(e["conf"]) for e in history) / total

        st.markdown(f"""
        <div class="metrics-row" style="grid-template-columns:repeat(4,1fr);margin-bottom:1rem;">
          <div class="metric-cell"><div class="metric-val">{total}</div><div class="metric-lbl">Total Scans</div></div>
          <div class="metric-cell"><div class="metric-val">{diseased}</div><div class="metric-lbl">Diseased</div></div>
          <div class="metric-cell"><div class="metric-val">{critical}</div><div class="metric-lbl">Critical</div></div>
          <div class="metric-cell"><div class="metric-val">{avg_conf:.1f}%</div><div class="metric-lbl">Avg Confidence</div></div>
        </div>
        """, unsafe_allow_html=True)

        for i, e in enumerate(history):
            dot_color = sev_colors.get(e["severity"].lower(), "#888")
            delay_cls = f"d{(i%5)+1}"
            st.markdown(f"""
            <div class="hist-row {delay_cls}">
              <div class="hist-sev-dot" style="background:{dot_color};
                   box-shadow:0 0 6px {dot_color}88;"></div>
              <div>
                <div class="hist-disease">{e['disease']}</div>
                <div class="hist-meta">{e['crop']} · {e['ts']} · {e['file']}</div>
              </div>
              <div class="hist-conf">{e['conf']}%</div>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("🗑 Clear History", key="clear_hist"):
            st.session_state.scan_history = []
            st.rerun()

# ══════════════════════════════════════════════════════════════════════════════
# TAB 4 — AGROBOT
# ══════════════════════════════════════════════════════════════════════════════
with tabs[3]:
    lang_code = "en" if lang == "English" else "ta"

    bot_col, info_col = st.columns([1.6, 1], gap="large")

    with bot_col:
        st.markdown('<div class="section-title">💬 AgroBot Chat</div>', unsafe_allow_html=True)

        # Init greeting
        if not st.session_state.chat_history:
            greeting = txt["bot_greeting"]
            st.session_state.chat_history.append({"role": "bot", "text": greeting})

        # Chat window
        chat_html = '<div class="chat-viewport" id="chatBox">'
        for msg in st.session_state.chat_history:
            if msg["role"] == "user":
                chat_html += f'<div class="chat-msg-user"><div class="chat-bubble-user">{msg["text"]}</div></div>'
            else:
                chat_html += f'<div class="chat-msg-bot"><div class="bot-avatar">🤖</div><div class="chat-bubble-bot">{msg["text"]}</div></div>'
        chat_html += "</div>"
        st.markdown(chat_html, unsafe_allow_html=True)

        # Input
        inp_c, btn_c = st.columns([5, 1])
        user_msg = inp_c.text_input("", placeholder=txt["chat_placeholder"],
                                     label_visibility="collapsed", key="chat_in")
        if btn_c.button("→", key="chat_send"):
            if user_msg.strip():
                st.session_state.chat_history.append({"role": "user", "text": user_msg})
                reply = agro_chatbot_reply(user_msg, lang_code)
                st.session_state.chat_history.append({"role": "bot", "text": reply})
                st.rerun()

        if st.button("🗑 Clear Chat", key="clear_chat"):
            st.session_state.chat_history = []
            st.rerun()

    with info_col:
        st.markdown('<div class="section-title">⚡ Quick Questions</div>', unsafe_allow_html=True)
        lang_code = "en" if lang == "English" else "ta"
        if lang == "English":
            quick_qs = [
                "How do I treat Late blight?",
                "Best fertilizer for tomatoes?",
                "Organic control for Early blight?",
                "When should I spray pesticide?",
                "How to prevent Bacterial spot?",
                "What causes Yellow Leaf Curl?",
            ]
        else:
            quick_qs = [
                "பிற்போக்கு கருகல் சிகிச்சை என்ன?",
                "தக்காளிக்கு சிறந்த உரம் எது?",
                "உயிரி கட்டுப்பாடு எப்படி?",
                "கீட்டுமருந்து எப்போது தெளிக்கணும்?",
                "பாக்டீரியா புள்ளி தடுப்பு?",
                "இலை சுருள் வைரஸ் காரணம்?",
            ]
        for i, q in enumerate(quick_qs):
            if st.button(q, key=f"qq_{i}"):
                st.session_state.chat_history.append({"role": "user", "text": q})
                st.session_state.chat_history.append({"role": "bot",  "text": agro_chatbot_reply(q, lang_code)})
                st.rerun()

        st.markdown('<div class="section-title" style="margin-top:1rem;">🌿 AgroBot Can Help With</div>', unsafe_allow_html=True)
        st.markdown(f"""
        <div class="ag-card" style="font-size:0.78rem;line-height:2;font-family:'Share Tech Mono',monospace;opacity:0.75;">
          🔬 Disease identification<br>
          💊 Chemical &amp; organic treatment<br>
          🌱 NPK fertiliser planning<br>
          🌦 Weather farming advice<br>
          📅 Seasonal crop calendar<br>
          🔄 Crop rotation guidance
        </div>
        """, unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# TAB 5 — VOICE
# ══════════════════════════════════════════════════════════════════════════════
with tabs[4]:
    lang_code = "en" if lang == "English" else "ta"
    v_col1, v_col2 = st.columns(2, gap="large")

    with v_col1:
        st.markdown('<div class="section-title">🎤 Voice Input</div>', unsafe_allow_html=True)
        st.markdown(f"""
        <div class="voice-panel">
          <div class="voice-icon">🎙️</div>
          <div style="font-family:'Rajdhani',sans-serif;font-size:1rem;
                      letter-spacing:2px;text-transform:uppercase;margin-bottom:6px;">
            {txt['voice_title']}
          </div>
          <div style="font-size:0.75rem;opacity:0.6;font-family:'Share Tech Mono',monospace;">
            {txt['voice_sub']}
          </div>
        </div>
        """, unsafe_allow_html=True)

        st.info("""
**Voice Recognition** uses your browser's Web Speech API.

To use voice input:
1. Allow microphone access when prompted
2. Click the voice button below
3. Speak clearly in English or Tamil
4. Your question will be transcribed in the box below (copy it into AgroBot to ask)
        """)

        # Web Speech API — inject JS
        voice_lang = "ta-IN" if lang == "தமிழ்" else "en-US"
        st.components.v1.html(f"""
        <style>
          body {{ margin:0; background:transparent; font-family:'Exo 2',sans-serif; }}
          #voiceBtn {{
            width:100%; padding:12px; border-radius:10px; cursor:pointer;
            background:{'rgba(0,255,136,0.12)' if is_dark else 'rgba(0,140,80,0.1)'};
            border:1px solid {'rgba(0,255,136,0.35)' if is_dark else 'rgba(0,140,80,0.35)'};
            color:{'#00ff88' if is_dark else '#008c50'}; font-size:16px; font-weight:600;
            font-family:'Rajdhani',sans-serif; letter-spacing:2px; text-transform:uppercase;
            transition:all .2s;
          }}
          #voiceBtn:hover {{ opacity:0.8; }}
          #voiceBtn.listening {{
            background:rgba(255,60,60,0.15); border-color:rgba(255,60,60,0.4);
            color:#ff4444; animation: blink .7s ease-in-out infinite;
          }}
          @keyframes blink {{ 0%,100% {{opacity:1;}} 50% {{opacity:0.5;}} }}
          #voiceResult {{
            margin-top:10px; padding:10px 12px; border-radius:8px;
            background:{'rgba(255,255,255,0.04)' if is_dark else 'rgba(0,0,0,0.04)'};
            border:1px solid {'rgba(255,255,255,0.1)' if is_dark else 'rgba(0,0,0,0.1)'};
            color:{'#e8f4f0' if is_dark else '#0d2a1a'}; font-size:14px; min-height:44px;
            font-family:'Exo 2',sans-serif;
          }}
          #ttsBtn {{
            width:100%; padding:10px; border-radius:10px; cursor:pointer; margin-top:8px;
            background:{'rgba(0,200,255,0.1)' if is_dark else 'rgba(0,100,200,0.08)'};
            border:1px solid {'rgba(0,200,255,0.3)' if is_dark else 'rgba(0,100,200,0.3)'};
            color:{'#00c8ff' if is_dark else '#0066cc'}; font-size:15px; font-weight:600;
            font-family:'Rajdhani',sans-serif; letter-spacing:2px; text-transform:uppercase;
          }}
        </style>
        <button id="voiceBtn" onclick="startVoice()">🎤 SPEAK NOW ({voice_lang})</button>
        <div id="voiceResult">Your speech will appear here…</div>
        <button id="ttsBtn" onclick="speakText()" id="ttsBtn">🔊 HEAR TRANSCRIBED SPEECH</button>

        <script>
        var lastReply = '';
        function startVoice() {{
          if (!('webkitSpeechRecognition' in window) && !('SpeechRecognition' in window)) {{
            document.getElementById('voiceResult').innerText = '⚠️ Voice not supported in this browser. Use Chrome.';
            return;
          }}
          var SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
          var rec = new SpeechRecognition();
          rec.lang = '{voice_lang}';
          rec.interimResults = false;
          rec.maxAlternatives = 1;
          var btn = document.getElementById('voiceBtn');
          btn.classList.add('listening');
          btn.innerText = '🔴 LISTENING…';
          rec.onresult = function(e) {{
            var text = e.results[0][0].transcript;
            document.getElementById('voiceResult').innerText = '🗣 "' + text + '"';
            btn.classList.remove('listening');
            btn.innerText = '🎤 SPEAK NOW ({voice_lang})';
            lastReply = text;
          }};
          rec.onerror = function(e) {{
            document.getElementById('voiceResult').innerText = '⚠️ Error: ' + e.error;
            btn.classList.remove('listening');
            btn.innerText = '🎤 SPEAK NOW ({voice_lang})';
          }};
          rec.onend = function() {{
            btn.classList.remove('listening');
            btn.innerText = '🎤 SPEAK NOW ({voice_lang})';
          }};
          rec.start();
        }}
        function speakText() {{
          var t = document.getElementById('voiceResult').innerText;
          if (t && t !== 'Your speech will appear here…') {{
            var utt = new SpeechSynthesisUtterance(t);
            utt.lang = '{voice_lang}';
            utt.rate = 0.9;
            window.speechSynthesis.speak(utt);
          }}
        }}
        </script>
        """, height=200)

    with v_col2:
        st.markdown('<div class="section-title">🔊 Text-to-Speech</div>', unsafe_allow_html=True)
        st.markdown(f"""
        <div class="ag-card">
          <div style="font-size:0.8rem;margin-bottom:10px;opacity:0.75;font-family:'Share Tech Mono',monospace;">
            Type or paste any text below to hear it read aloud in {lang}
          </div>
        </div>
        """, unsafe_allow_html=True)

        tts_text = st.text_area(
            "Text to speak",
            placeholder=txt["tts_placeholder"],
            height=120,
            label_visibility="collapsed",
        )

        tts_lang = "ta-IN" if lang == "தமிழ்" else "en-US"
        if tts_text:
            escaped = tts_text.replace("'", "\\'").replace("\n", " ")
            st.components.v1.html(f"""
            <style>
              body {{ margin:0; }}
              #ttsPlayBtn {{
                width:100%; padding:10px; border-radius:8px; cursor:pointer;
                background:{'rgba(0,200,255,0.1)' if is_dark else 'rgba(0,100,200,0.08)'};
                border:1px solid {'rgba(0,200,255,0.35)' if is_dark else 'rgba(0,100,200,0.3)'};
                color:{'#00c8ff' if is_dark else '#0066cc'}; font-size:15px;
                font-family:'Rajdhani',sans-serif; font-weight:600;
                letter-spacing:2px; text-transform:uppercase;
              }}
            </style>
            <button id="ttsPlayBtn" onclick="doSpeak()">🔊 PLAY AUDIO</button>
            <script>
            function doSpeak() {{
              window.speechSynthesis.cancel();
              var u = new SpeechSynthesisUtterance('{escaped}');
              u.lang = '{tts_lang}'; u.rate = 0.88;
              window.speechSynthesis.speak(u);
            }}
            </script>
            """, height=60)

        st.markdown('<div class="section-title" style="margin-top:1rem;">🌍 Supported Languages</div>', unsafe_allow_html=True)
        st.markdown(f"""
        <div class="ag-card" style="font-size:0.82rem;line-height:2;">
          🇮🇳 <strong>Tamil</strong> (ta-IN) — Full UI + Voice + Chat<br>
          🇬🇧 <strong>English</strong> (en-US) — Full UI + Voice + Chat<br>
          <span style="opacity:0.5;font-size:0.72rem;font-family:'Share Tech Mono',monospace;">
            More languages coming in v5.0 (Hindi, Telugu, Kannada)
          </span>
        </div>
        """, unsafe_allow_html=True)

        st.markdown('<div class="section-title" style="margin-top:1rem;">⚙️ Hardware Integration</div>', unsafe_allow_html=True)
        st.markdown(f"""
        <div class="ag-card ag-card-blue" style="font-size:0.8rem;line-height:1.9;">
          <div style="font-family:'Rajdhani',sans-serif;font-weight:700;
                      margin-bottom:8px;letter-spacing:1px;">PLANNED HARDWARE MODULES</div>
          📷 Raspberry Pi Camera v3 — leaf capture<br>
          🔊 I²S Speaker + Mic — voice I/O<br>
          📡 LoRa SX1276 — offline field comm<br>
          🌡 DHT22 Sensor — humidity/temp monitoring<br>
          🖥 7″ Touch LCD — farmer interface<br>
          🔋 Solar + LiPo — field power supply<br>
          <span style="opacity:0.5;font-size:0.7rem;font-family:'Share Tech Mono',monospace;">
            Contact team for hardware SDK
          </span>
        </div>
        """, unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# TAB 6 — FIELD UNIT (Prototype Sensor Mode)
# ══════════════════════════════════════════════════════════════════════════════
with tabs[5]:
    st.markdown("""
    <div style="background:rgba(255,170,0,0.12); border:1px solid rgba(255,170,0,0.4); border-radius:10px; padding:12px 16px; margin-bottom:1.2rem; color:#ffaa00; font-weight:600; font-family:'Rajdhani',sans-serif; letter-spacing:1px;">
        ⚠️ <strong>PROTOTYPE SENSOR MODE</strong> – Sensor values are simulated, not from physical hardware sensors.
    </div>
    """, unsafe_allow_html=True)

    # ── System Status Panel ────────────────────────────────────────────────────
    st.markdown('<div class="section-title">🖥️ System Status Panel</div>', unsafe_allow_html=True)
    sys_col1, sys_col2, sys_col3, sys_col4 = st.columns(4)
    with sys_col1:
        st.markdown(f"**AI Model Status:** {'✅ Loaded' if model is not None else '❌ Not Loaded'}")
    with sys_col2:
        st.markdown("**Sensor Mode:** `SIMULATED` (Prototype)")
    with sys_col3:
        st.markdown("**Network:** `Offline / Local` (Not required)")
    with sys_col4:
        st.markdown("**Exclusions:** `Weather API Excluded`")

    st.markdown("---")

    # ── Grid Layout for Field Unit ─────────────────────────────────────────────
    fu_col1, fu_col2 = st.columns([1, 1])

    with fu_col1:
        st.markdown('<div class="section-title">📷 Crop & Leaf Image Diagnosis</div>', unsafe_allow_html=True)
        selected_crop = st.selectbox("Select Target Crop", SUPPORTED_CROPS, index=0, key="fu_crop")
        
        fu_uploaded = st.file_uploader(
            "Upload Leaf Image for Field Unit Analysis (Optional)",
            type=["jpg", "jpeg", "png"],
            key="fu_file"
        )

        unc_res = None
        disease_class = None
        pil_img = None

        if fu_uploaded:
            pil_img = Image.open(fu_uploaded)
            st.image(pil_img, caption="Field Unit Capture", use_container_width=True)
            
            if model is not None and class_names is not None:
                img_arr = preprocess_image(pil_img)
                best_class, confidence, top5, probs = predict_with_confidence(model, img_arr, class_names)
                disease_class = best_class
                
                unc_res = assess_uncertainty(probs, class_names)
                
                st.markdown(f"**Predicted Class:** `{best_class}`")
                st.markdown(f"**Confidence:** `{confidence:.1f}%` &nbsp;|&nbsp; **Margin:** `{unc_res['margin']:.1f}%`")
                
                if unc_res["status"] == "uncertain":
                    st.warning(f"⚠️ **Uncertain Prediction**: {unc_res['reason']}\n\nPlease re-capture the leaf image under better lighting.")
                else:
                    st.success("✅ **Confident Prediction**")
        else:
            st.info("ℹ️ No leaf image uploaded. Risk engine will evaluate environmental sensors with disease status as `UNKNOWN`.")

    with fu_col2:
        st.markdown('<div class="section-title">📡 Simulated Sensor Inputs</div>', unsafe_allow_html=True)
        scenario = st.selectbox(
            "Select Preset Field Scenario (Prototype Sensor Mode)",
            ["normal", "water_stress", "humid_disease_favourable", "missing_sensor", "out_of_range", "Custom Manual Values"],
            index=0,
            key="fu_scenario"
        )

        if scenario == "Custom Manual Values":
            m_soil = st.slider("Soil Moisture (%)", -10.0, 110.0, 45.0, 1.0)
            m_temp = st.slider("Temperature (°C)", -15.0, 65.0, 28.0, 1.0)
            m_hum = st.slider("Relative Humidity (%)", -10.0, 110.0, 75.0, 1.0)
            m_light = st.slider("Sunlight Intensity (%)", 0.0, 100.0, 80.0, 1.0)
            sensor_data = create_manual_reading(m_soil, m_temp, m_hum, m_light)
        else:
            sensor_data = get_preset_scenario(scenario)
            st.json({
                "mode": sensor_data.get("mode"),
                "soil_moisture (%)": sensor_data.get("soil_moisture"),
                "temperature (°C)": sensor_data.get("temperature"),
                "humidity (%)": sensor_data.get("humidity"),
                "light (%)": sensor_data.get("light"),
                "humidity_history": sensor_data.get("humidity_history")
            })

        val_sensors = validate_sensor_readings(sensor_data)

    st.markdown("---")

    # ── Risk Assessment Engine Output ─────────────────────────────────────────
    st.markdown('<div class="section-title">📊 Field Environmental & Disease Risk Assessment</div>', unsafe_allow_html=True)
    risk_res = evaluate_field_risk(unc_res, disease_class, selected_crop, val_sensors)

    r_col1, r_col2, r_col3, r_col4 = st.columns(4)
    
    def get_risk_badge(level):
        if level == "HIGH": return "🔴 HIGH"
        elif level == "MODERATE": return "🟡 MODERATE"
        elif level == "LOW": return "🟢 LOW"
        else: return "⚪ UNKNOWN"

    with r_col1:
        st.metric("Water Stress Risk", get_risk_badge(risk_res["water_stress_risk"]))
    with r_col2:
        st.metric("Heat Stress Risk", get_risk_badge(risk_res["heat_stress_risk"]))
    with r_col3:
        st.metric("Disease Spread Risk", get_risk_badge(risk_res["disease_spread_risk"]))
    with r_col4:
        st.metric("Overall Field Risk", get_risk_badge(risk_res["overall_risk"]))

    st.caption(f"ℹ️ Note: Thresholds are `{risk_res['thresholds_note']}`")

    if risk_res["reasons"]:
        st.markdown("**Rule Evaluation Logic & Reasons:**")
        for r in risk_res["reasons"]:
            st.markdown(f"- {r}")

    if risk_res["unknown_inputs"]:
        st.markdown("**Unknown / Missing Input Parameters:**")
        for u in risk_res["unknown_inputs"]:
            st.markdown(f"- ⚠️ {u}")

    st.markdown("---")

    # ── Actionable Recommendations ─────────────────────────────────────────────
    st.markdown('<div class="section-title">💡 Field Unit Recommendations</div>', unsafe_allow_html=True)
    rec_lang = "ta" if lang == "தமிழ்" else "en"
    recs = generate_field_recommendations(risk_res, rec_lang)
    for rec in recs:
        st.markdown(f"> {rec}")

    st.markdown("---")

    # ── Optional Experimental Patch-Wise Analysis ─────────────────────────────
    st.markdown('<div class="section-title">🧪 Experimental Patch-Wise Analysis</div>', unsafe_allow_html=True)
    enable_patch = st.checkbox(
        "Enable Patch-Wise Analysis (Experimental - disabled by default)",
        value=False,
        key="fu_patch_toggle"
    )
    if enable_patch:
        st.warning("⚠️ **Experimental Feature Warning**: Patch-wise 3x3 grid tiles are outside the single-leaf training distribution. Results are not validated for field accuracy.")
        if pil_img is not None and model is not None:
            with st.spinner("Analyzing 3x3 image patches…"):
                patch_res = analyze_image_patches(pil_img, model, class_names)
                st.markdown(f"**Diseased Patch Count:** `{patch_res['diseased_tile_count']} / 9`")
                
                grid_cols = st.columns(3)
                for idx, tile in enumerate(patch_res["tiles"]):
                    col_idx = idx % 3
                    with grid_cols[col_idx]:
                        t_status = "🔴 Sick" if tile["is_diseased"] and tile["is_confident"] else "🟢 Healthy/Uncertain"
                        st.markdown(f"**Tile ({tile['row']},{tile['col']})**: {t_status}\n- Class: `{tile['best_class']}`\n- Conf: `{tile['confidence']:.1f}%`")
        else:
            st.info("Upload a leaf image above to view patch-wise grid breakdown.")

# ── Footer ────────────────────────────────────────────────────────────────────

st.markdown(f"""
<div class="ag-footer">
  🌾 AGROGUARD AI v4.0 &nbsp;·&nbsp; INTELLIGENT CROP PROTECTION &nbsp;·&nbsp; HARDWARE READY
  <br>{txt['disclaimer']} &nbsp;·&nbsp; {txt['emergency']}
  <br><span style="opacity:0.4;">Built with ❤️ for farmers · Python · TensorFlow · Streamlit</span>
</div>
""", unsafe_allow_html=True)