import os
import base64
import json
from pathlib import Path
from datetime import datetime
from PIL import Image

import streamlit as st

from config import EN, TA, SUPPORTED_CROPS, FEEDBACK_FILE
from services import (
    get_3day_forecast, get_weather_precaution,
    get_treatment, get_fertilizer,
    agro_chatbot_reply, generate_report, save_feedback,
)
from model_utils import load_model_assets, preprocess_image, predict_with_confidence


# ── Directories ──────────────────────────────────────────────────────────────
Path("models").mkdir(exist_ok=True)
Path("reports").mkdir(exist_ok=True)


# ── Page config ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="AgroGuard AI — Intelligent Crop Protection",
    page_icon="🌿",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ── Session state ────────────────────────────────────────────────────────────
for k, v in {
    "language": "English",
    "chat_history": [],
    "scan_history": [],
    "theme": "light",        # default to light mode — friendlier
    "last_voice_msg": "",
}.items():
    if k not in st.session_state:
        st.session_state[k] = v


# ── Handle voice transcript coming from the mic (via query params) ───────────
_qp = st.query_params
if "voice_msg" in _qp:
    _voice_text = _qp.get("voice_msg", "")
    if isinstance(_voice_text, list):
        _voice_text = _voice_text[0] if _voice_text else ""
    if _voice_text and _voice_text != st.session_state.get("last_voice_msg"):
        st.session_state.last_voice_msg = _voice_text
        lang_code = "en" if st.session_state.language == "English" else "ta"
        st.session_state.chat_history.append({"role": "user", "text": _voice_text})
        st.session_state.chat_history.append(
            {"role": "bot", "text": agro_chatbot_reply(_voice_text, lang_code)}
        )
    # Clear the param so refreshes don't re-add
    st.query_params.clear()


lang    = st.session_state.language
txt     = EN if lang == "English" else TA
is_dark = st.session_state.theme == "dark"


# ═════════════════════════════════════════════════════════════════════════════
# CSS — vibrant, animated, perfectly readable in both themes
# ═════════════════════════════════════════════════════════════════════════════
def load_css(dark: bool):
    if dark:
        bg_primary   = "#0b1d14"
        bg_secondary = "#0f2a1d"
        bg_card      = "#13342a"
        border       = "rgba(94,234,148,0.25)"
        accent       = "#5eea94"
        accent2      = "#6bd0ff"
        accent3      = "#ffd166"
        text_primary = "#eaf7ef"
        text_muted   = "#9ab8a8"
        panel_bg     = "#0f2a1d"
        sidebar_bg   = "#0a2418"
        hero_from    = "#0b3a26"
        hero_to      = "#0b2e3a"
    else:
        bg_primary   = "#f5fbf6"
        bg_secondary = "#ffffff"
        bg_card      = "#ffffff"
        border       = "rgba(15,110,60,0.18)"
        accent       = "#0d8a4b"
        accent2      = "#1e7abf"
        accent3      = "#e08900"
        text_primary = "#0f2e1f"
        text_muted   = "#5a7a6a"
        panel_bg     = "#f0f8f2"
        sidebar_bg   = "#e8f5ec"
        hero_from    = "#d9f2e2"
        hero_to      = "#cfe8f6"

    st.markdown(f"""
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&family=Fraunces:wght@500;600;700&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">

<style>
html, body, [class*="css"], .stApp {{
    font-family: 'Plus Jakarta Sans', sans-serif !important;
    background: {bg_primary} !important;
    color: {text_primary} !important;
}}
.stApp {{
    background:
      radial-gradient(circle at 10% 0%, {accent}18 0%, transparent 40%),
      radial-gradient(circle at 90% 100%, {accent2}15 0%, transparent 40%),
      {bg_primary} !important;
}}

.main .block-container {{
    padding: 1rem 2rem 3rem !important;
    max-width: 1280px !important;
}}

/* Sidebar */
[data-testid="stSidebar"] {{
    background: {sidebar_bg} !important;
    border-right: 1px solid {border} !important;
}}
[data-testid="stSidebar"] * {{ color: {text_primary} !important; }}

/* Universal text readability */
p, span, div, label, li {{ color: {text_primary}; }}
h1, h2, h3, h4, h5, h6 {{ color: {text_primary} !important; }}
.stMarkdown, .stMarkdown * {{ color: {text_primary} !important; }}
.stMarkdown strong {{ color: {text_primary} !important; }}
.stMarkdown a {{ color: {accent} !important; }}

/* ═════ HERO ═════════════════════════════════════════════════════════════ */
.ag-hero {{
    position: relative;
    overflow: hidden;
    background: linear-gradient(135deg, {hero_from}, {hero_to});
    border: 1px solid {border};
    border-radius: 24px;
    padding: 2.2rem 2.5rem;
    margin-bottom: 1.5rem;
    animation: heroReveal .7s ease-out;
}}
.ag-hero::before {{
    content: '';
    position: absolute; inset: -50%;
    background:
      radial-gradient(circle at 20% 30%, {accent}33, transparent 40%),
      radial-gradient(circle at 80% 70%, {accent2}33, transparent 40%),
      radial-gradient(circle at 50% 90%, {accent3}22, transparent 40%);
    animation: heroFloat 12s ease-in-out infinite;
    pointer-events: none;
}}
@keyframes heroFloat {{
    0%,100% {{ transform: translate(0,0); }}
    50% {{ transform: translate(-3%, 3%); }}
}}
@keyframes heroReveal {{
    from {{ opacity:0; transform: translateY(-12px); }}
    to   {{ opacity:1; transform: translateY(0); }}
}}
.hero-grid {{
    position: relative; z-index: 1;
    display: grid;
    grid-template-columns: auto 1fr auto;
    align-items: center;
    gap: 1.5rem;
}}
.hero-emoji {{
    font-size: 3.2rem;
    filter: drop-shadow(0 4px 14px {accent}55);
    animation: bounce 3s ease-in-out infinite;
}}
@keyframes bounce {{
    0%,100% {{ transform: translateY(0) rotate(-2deg); }}
    50% {{ transform: translateY(-6px) rotate(2deg); }}
}}
.hero-title {{
    font-family: 'Fraunces', serif;
    font-size: 2.4rem;
    font-weight: 700;
    letter-spacing: -0.5px;
    color: {text_primary} !important;
    margin: 0;
    line-height: 1.1;
}}
.hero-title .accent {{
    background: linear-gradient(135deg, {accent}, {accent2});
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
}}
.hero-sub {{
    font-size: 0.95rem;
    color: {text_muted} !important;
    margin-top: 6px;
    font-weight: 500;
}}
.hero-badges {{ display: flex; flex-direction: column; gap: 6px; }}
.status-pill {{
    display: inline-flex; align-items: center; gap: 6px;
    background: {accent}22;
    border: 1px solid {accent}55;
    border-radius: 999px;
    padding: 5px 14px;
    font-size: .78rem; font-weight: 600;
    color: {accent} !important;
    white-space: nowrap;
}}
.status-dot {{
    width: 8px; height: 8px; border-radius: 50%;
    background: {accent};
    animation: pulse 1.6s ease-in-out infinite;
}}
@keyframes pulse {{
    0%,100% {{ opacity:1; box-shadow: 0 0 0 0 {accent}88; }}
    50%     {{ opacity:.6; box-shadow: 0 0 0 7px {accent}00; }}
}}

/* ═════ METRICS ══════════════════════════════════════════════════════════ */
.metrics-row {{
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
    gap: 12px;
    margin-bottom: 1.4rem;
}}
.metric-cell {{
    background: {bg_card};
    border: 1px solid {border};
    border-radius: 16px;
    padding: 16px 18px;
    position: relative;
    overflow: hidden;
    transition: transform .25s, border-color .25s, box-shadow .25s;
    animation: slideUp .5s ease-out both;
}}
.metric-cell::before {{
    content:''; position:absolute; top:0; left:0; right:0; height:3px;
    background: linear-gradient(90deg, {accent}, {accent2});
    transform: scaleX(0); transform-origin: left;
    transition: transform .3s;
}}
.metric-cell:hover {{
    transform: translateY(-4px);
    border-color: {accent};
    box-shadow: 0 12px 24px -10px {accent}44;
}}
.metric-cell:hover::before {{ transform: scaleX(1); }}
  .metric-val {{
  font-family: 'Fraunces', serif;
  font-size: 1.25rem; font-weight: 700;
  color: {accent} !important;
  line-height: 1;
}}
.metric-lbl {{
  font-size: .65rem; color: {text_muted} !important;
  text-transform: uppercase; letter-spacing: 1.2px;
  margin-top: 6px; font-weight: 600;
}}
@keyframes slideUp {{
    from {{ opacity:0; transform: translateY(16px); }}
    to   {{ opacity:1; transform: translateY(0); }}
}}

/* ═════ TABS ═════════════════════════════════════════════════════════════ */
.stTabs [data-baseweb="tab-list"] {{
    background: {panel_bg} !important;
    border: 1px solid {border} !important;
    border-radius: 16px !important;
    padding: 6px !important;
    gap: 4px !important;
    flex-wrap: wrap !important;
}}
.stTabs [data-baseweb="tab"] {{
    font-family: 'Plus Jakarta Sans', sans-serif !important;
    font-size: .9rem !important;
    font-weight: 600 !important;
    border-radius: 12px !important;
    color: {text_muted} !important;
    padding: 10px 20px !important;
    transition: all .2s !important;
    border: none !important;
}}
.stTabs [data-baseweb="tab"]:hover {{
    color: {text_primary} !important;
    background: {accent}11 !important;
}}
.stTabs [aria-selected="true"] {{
    background: linear-gradient(135deg, {accent}, {accent2}) !important;
    color: #fff !important;
    box-shadow: 0 6px 18px -6px {accent}77 !important;
}}
.stTabs [aria-selected="true"] * {{ color: #fff !important; }}
.stTabs [data-baseweb="tab-panel"] {{ padding: 1.2rem 0 !important; }}

/* ═════ CARDS ═════════════════════════════════════════════════════════════ */
.ag-card {{
    background: {bg_card};
    border: 1px solid {border};
    border-radius: 18px;
    padding: 1.3rem 1.5rem;
    margin-bottom: 1rem;
    position: relative;
    overflow: hidden;
    transition: all .25s;
    animation: fadeCard .4s ease-out;
}}
.ag-card::before {{
    content:''; position:absolute; top:0; left:0; right:0; height:3px;
    opacity:.9;
}}
.ag-card:hover {{
    transform: translateY(-2px);
    box-shadow: 0 16px 32px -16px rgba(0,0,0,.15);
}}
.ag-card-green::before  {{ background: linear-gradient(90deg,#2ea15f,#5eea94); }}
.ag-card-red::before    {{ background: linear-gradient(90deg,#e14b3e,#ff8f70); }}
.ag-card-yellow::before {{ background: linear-gradient(90deg,#e8a838,#ffd166); }}
.ag-card-blue::before   {{ background: linear-gradient(90deg,#1e7abf,#6bd0ff); }}
@keyframes fadeCard {{
    from {{ opacity:0; transform: translateY(10px); }}
    to   {{ opacity:1; transform: translateY(0); }}
}}

/* ═════ RESULT BANNERS ═══════════════════════════════════════════════════ */
.result-banner {{
    border-radius: 18px; padding: 1.3rem 1.5rem;
    margin-bottom: 1rem;
    display: flex; align-items: flex-start; gap: 16px;
    animation: bannerIn .5s cubic-bezier(0.34,1.56,0.64,1);
}}
@keyframes bannerIn {{
    from {{ opacity:0; transform: scale(.94); }}
    to   {{ opacity:1; transform: scale(1); }}
}}
.result-banner.healthy {{
    background: linear-gradient(135deg, {accent}22, {accent}11);
    border: 1.5px solid {accent}77;
}}
.result-banner.diseased {{
    background: linear-gradient(135deg, #e14b3e22, #e14b3e11);
    border: 1.5px solid #e14b3e88;
}}
.banner-icon {{ font-size: 2.4rem; line-height:1; }}
.banner-title {{
    font-family: 'Fraunces', serif;
    font-size: 1.5rem; font-weight: 700;
    color: {text_primary} !important;
    margin: 0 0 4px;
}}
.banner-disease {{
    font-size: .9rem; color: {text_muted} !important;
    font-family: 'JetBrains Mono', monospace;
}}

/* ═════ CONFIDENCE METER ═════════════════════════════════════════════════ */
.conf-wrap {{
    background: {panel_bg};
    border: 1px solid {border};
    border-radius: 14px;
    padding: 14px 16px;
    margin: 12px 0;
}}
.conf-header {{
    display: flex; justify-content: space-between;
    font-size: .78rem; color: {text_muted} !important;
    margin-bottom: 8px; text-transform: uppercase;
    letter-spacing: 1px; font-weight: 600;
}}
.conf-pct {{
    font-family: 'Fraunces', serif;
    font-size: 1.25rem; font-weight: 700;
    color: {accent} !important;
}}
.conf-track {{
    height: 10px;
    background: {accent}15;
    border-radius: 999px; overflow: hidden;
}}
.conf-fill {{
    height: 100%; border-radius: 999px;
    background: linear-gradient(90deg, {accent}, {accent2});
    transition: width 1.2s cubic-bezier(0.25,1,0.5,1);
    position: relative;
    box-shadow: 0 0 12px {accent}77;
}}
.conf-fill::after {{
    content:''; position:absolute; right:0; top:0; bottom:0; width:14px;
    background: rgba(255,255,255,.7);
    filter: blur(4px);
    animation: shimmer 1.5s ease-in-out infinite;
}}
@keyframes shimmer {{ 0%,100% {{opacity:.3;}} 50% {{opacity:.9;}} }}

/* ═════ SEVERITY BADGES ══════════════════════════════════════════════════ */
.sev-badge {{
    display: inline-flex; align-items: center; gap:5px;
    padding: 4px 12px; border-radius: 999px;
    font-size: .72rem; font-weight: 700;
    letter-spacing: 1.2px; text-transform: uppercase;
}}
.sev-critical {{ background:#ff555522; color:#ff5555 !important; border:1px solid #ff555555; }}
.sev-high     {{ background:#ff990022; color:#ff9900 !important; border:1px solid #ff990055; }}
.sev-medium   {{ background:#e8a83822; color:#e8a838 !important; border:1px solid #e8a83855; }}
.sev-low, .sev-none, .sev-unknown
             {{ background:{accent}22; color:{accent} !important; border:1px solid {accent}55; }}

/* ═════ SECTION TITLE ════════════════════════════════════════════════════ */
.section-title {{
    font-family: 'Fraunces', serif;
    font-size: 1.15rem; font-weight: 600;
    color: {text_primary} !important;
    margin: 1.2rem 0 .8rem;
    display: flex; align-items: center; gap: 10px;
}}
.section-title::after {{
    content:''; flex:1; height:1px;
    background: linear-gradient(90deg, {border}, transparent);
}}

/* ═════ INFO GRID ════════════════════════════════════════════════════════ */
.info-grid {{
    display: grid; grid-template-columns: repeat(auto-fit, minmax(180px,1fr));
    gap: 10px;
}}
.info-item {{
    background: {panel_bg};
    border: 1px solid {border};
    border-radius: 12px; padding: 12px 14px;
    transition: border-color .2s, transform .2s;
}}
.info-item:hover {{ border-color: {accent}; transform: translateY(-2px); }}
.info-lbl {{
    font-size: .72rem; text-transform: uppercase; letter-spacing: 1.1px;
    color: {text_muted} !important; margin-bottom: 4px; font-weight: 600;
}}
.info-val {{
    font-size: .88rem; color: {text_primary} !important;
    line-height: 1.5; font-weight: 500;
}}

/* ═════ WEATHER CARDS ════════════════════════════════════════════════════ */
.wx-card {{
    background: {bg_card};
    border: 1px solid {border};
    border-radius: 18px; padding: 1.2rem;
    text-align: center;
    transition: all .25s;
    animation: slideUp .4s ease-out both;
}}
.wx-card:hover {{
    border-color: {accent};
    transform: translateY(-5px);
    box-shadow: 0 18px 30px -16px {accent}55;
}}
.wx-date {{ font-size: .78rem; color:{text_muted} !important; font-weight:600; letter-spacing: 1px; }}
.wx-icon {{ font-size: 2.8rem; margin: 8px 0; }}
.wx-temp {{
    font-family: 'Fraunces', serif; font-size: 2.2rem; font-weight: 700;
    color: {accent} !important; line-height: 1;
}}
.wx-detail {{ font-size: .82rem; color: {text_muted} !important; margin-top: 6px; }}
.wx-alert {{
    font-size: .75rem; margin-top: 10px;
    padding: 6px 10px; border-radius: 10px;
    font-weight: 600;
}}
.wx-warn {{ background:#e8a83822; color:#cc8800 !important; border:1px solid #e8a83866; }}
.wx-ok   {{ background:{accent}1f; color:{accent} !important; border:1px solid {accent}66; }}

/* ═════ CHAT ═════════════════════════════════════════════════════════════ */
.chat-viewport {{
    background: {panel_bg};
    border: 1px solid {border};
    border-radius: 18px;
    padding: 18px;
    max-height: 480px;
    overflow-y: auto;
    scrollbar-width: thin;
}}
.chat-msg-user {{ display:flex; justify-content:flex-end; margin: 8px 0; }}
.chat-msg-bot  {{ display:flex; justify-content:flex-start; margin: 8px 0; gap:10px; align-items:flex-end; }}
.chat-bubble-user {{
    background: linear-gradient(135deg, {accent}, {accent2});
    color: #fff !important;
    border-radius: 18px 18px 4px 18px;
    padding: 10px 16px; max-width: 78%;
    font-size: .92rem; line-height: 1.5; font-weight: 500;
    box-shadow: 0 6px 14px -6px {accent}88;
    animation: msgIn .3s ease-out;
}}
.chat-bubble-user * {{ color: #fff !important; }}
.chat-bubble-bot {{
    background: {bg_card};
    border: 1px solid {border};
    border-radius: 18px 18px 18px 4px;
    padding: 10px 16px; max-width: 78%;
    font-size: .92rem; color: {text_primary} !important;
    line-height: 1.5; white-space: pre-wrap;
    animation: msgIn .3s ease-out;
}}
@keyframes msgIn {{
    from {{ opacity:0; transform: translateY(8px); }}
    to   {{ opacity:1; transform: translateY(0); }}
}}
.bot-avatar {{
    width: 34px; height: 34px; border-radius: 50%;
    background: linear-gradient(135deg, {accent}, {accent2});
    display: flex; align-items: center; justify-content: center;
    font-size: 16px; flex-shrink: 0;
    box-shadow: 0 4px 10px -4px {accent}88;
}}
          .bot-avatar-img {{
            width: 34px; height: 34px; border-radius: 50%; object-fit:cover; flex-shrink:0;
            box-shadow: 0 4px 10px -4px {accent}88;
          }}

/* ═════ HISTORY ═══════════════════════════════════════════════════════════ */
.hist-row {{
    background: {bg_card};
    border: 1px solid {border};
    border-radius: 14px;
    padding: 12px 16px;
    margin-bottom: 8px;
    display: flex; align-items: center; gap: 14px;
    transition: all .2s;
    animation: slideUp .3s ease-out both;
}}
.hist-row:hover {{
    border-color: {accent};
    transform: translateX(4px);
}}
.hist-sev-dot {{ width: 12px; height: 12px; border-radius: 50%; flex-shrink: 0; }}
.hist-disease {{ font-weight: 600; font-size: .95rem; color: {text_primary} !important; }}
.hist-meta {{ font-size: .78rem; color: {text_muted} !important; margin-top: 3px; }}
.hist-conf {{
    margin-left: auto;
    font-family: 'Fraunces', serif; font-size: 1.15rem;
    font-weight: 700; color: {accent} !important;
}}

/* ═════ BUTTONS ═══════════════════════════════════════════════════════════ */
.stButton>button {{
    background: linear-gradient(135deg, {accent}, {accent2}) !important;
    color: #fff !important;
    border: none !important;
    border-radius: 12px !important;
    font-family: 'Plus Jakarta Sans', sans-serif !important;
    font-size: .88rem !important;
    font-weight: 600 !important;
    padding: 10px 20px !important;
    width: 100% !important;
    transition: all .2s !important;
    box-shadow: 0 4px 12px -4px {accent}66 !important;
}}
.stButton>button:hover {{
    transform: translateY(-2px) !important;
    box-shadow: 0 10px 20px -6px {accent}99 !important;
    filter: brightness(1.05) !important;
}}
.stButton>button * {{ color: #fff !important; }}

/* ═════ INPUTS ═══════════════════════════════════════════════════════════ */
.stTextInput>div>div>input, .stTextArea>div>div>textarea {{
    background: {panel_bg} !important;
    color: {text_primary} !important;
    border: 1px solid {border} !important;
    border-radius: 12px !important;
    font-family: 'Plus Jakarta Sans', sans-serif !important;
    padding: 10px 14px !important;
}}
.stTextInput>div>div>input:focus, .stTextArea>div>div>textarea:focus {{
    border-color: {accent} !important;
    box-shadow: 0 0 0 3px {accent}22 !important;
}}

[data-testid="stFileUploader"] {{
    background: {panel_bg} !important;
    border: 2px dashed {border} !important;
    border-radius: 16px !important;
    padding: 1rem !important;
    transition: all .2s !important;
}}
[data-testid="stFileUploader"]:hover {{
    border-color: {accent} !important;
    background: {accent}08 !important;
}}
[data-testid="stFileUploader"] * {{ color: {text_primary} !important; }}

/* ═════ DOWNLOAD BUTTON ══════════════════════════════════════════════════ */
.dl-btn {{
    display: block; text-decoration: none !important;
    background: linear-gradient(135deg, {accent}, {accent2});
    color: #fff !important;
    border-radius: 12px;
    padding: 12px 20px;
    text-align: center;
    font-weight: 600;
    margin-top: 12px;
    transition: all .2s;
    box-shadow: 0 6px 14px -4px {accent}66;
}}
.dl-btn:hover {{
    transform: translateY(-2px);
    box-shadow: 0 14px 24px -6px {accent}99;
    filter: brightness(1.05);
}}

/* ═════ MIC BUTTON (voice) ═══════════════════════════════════════════════ */
.mic-wrap {{
    background: {bg_card};
    border: 1px solid {border};
    border-radius: 18px;
    padding: 1rem;
    text-align: center;
}}

/* ═════ TICKER ═══════════════════════════════════════════════════════════ */
.tip-ticker {{
    background: linear-gradient(90deg, {accent}14, {accent2}14);
    border: 1px solid {border};
    border-radius: 12px; padding: 10px 18px;
    font-size: .82rem; color: {text_primary} !important;
    overflow: hidden; white-space: nowrap;
    margin-bottom: 1rem; font-weight: 500;
}}
.tip-ticker span {{ display: inline-block; animation: ticker 28s linear infinite; }}
@keyframes ticker {{
    0% {{ transform: translateX(100%); }}
    100% {{ transform: translateX(-100%); }}
}}

/* ═════ FOOTER ═══════════════════════════════════════════════════════════ */
.ag-footer {{
    text-align: center; padding: 2rem 1rem 1rem;
    border-top: 1px solid {border};
    color: {text_muted} !important;
    font-size: .82rem;
    margin-top: 2rem;
}}

/* ═════ SCROLLBAR ════════════════════════════════════════════════════════ */
::-webkit-scrollbar {{ width: 8px; height: 8px; }}
::-webkit-scrollbar-thumb {{
    background: {accent}44; border-radius: 99px;
}}
::-webkit-scrollbar-thumb:hover {{ background: {accent}77; }}

hr {{
    border: none !important; height: 1px !important;
    background: linear-gradient(90deg, transparent, {border}, transparent) !important;
    margin: 1rem 0 !important;
}}

/* Streamlit metric override */
[data-testid="stMetric"] {{
    background: {bg_card} !important;
    border: 1px solid {border} !important;
    border-radius: 14px !important;
    padding: 12px !important;
}}
[data-testid="stMetricValue"] {{
    color: {accent} !important;
    font-family: 'Fraunces', serif !important;
  font-size: 1.1rem !important;
}}
[data-testid="stMetric"] label {{ color: {text_muted} !important; }}

.stAlert {{ border-radius: 12px !important; border: 1px solid {border} !important; }}
.stAlert * {{ color: {text_primary} !important; }}

/* Radio buttons */
[data-testid="stRadio"] label, [data-testid="stRadio"] * {{ color: {text_primary} !important; }}

/* Sidebar logo */
.sb-logo-wrap {{
    text-align: center; padding: 1rem 0 .8rem;
}}
.sb-emoji {{
    font-size: 3rem;
    animation: bounce 3s ease-in-out infinite;
    display: inline-block;
}}
.sb-logo-title {{
    font-family: 'Fraunces', serif;
    font-size: 1.4rem; font-weight: 700;
    background: linear-gradient(135deg, {accent}, {accent2});
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    letter-spacing: 1px; margin-top: 4px;
}}
.sb-logo-sub {{
    font-size: .72rem; color: {text_muted} !important;
    letter-spacing: 1.5px; text-transform: uppercase; font-weight: 600;
}}

.empty-state {{
    text-align: center; padding: 3rem 1rem;
    color: {text_muted} !important;
}}
.empty-state .emoji {{
    font-size: 3.6rem;
    animation: bounce 3s ease-in-out infinite;
}}
.empty-state .text {{
    font-family: 'Fraunces', serif;
    font-size: 1.2rem; margin-top: 10px; font-weight: 500;
}}

.d1 {{ animation-delay: 0.05s; }}
.d2 {{ animation-delay: 0.10s; }}
.d3 {{ animation-delay: 0.15s; }}
.d4 {{ animation-delay: 0.20s; }}
.d5 {{ animation-delay: 0.25s; }}
</style>
""", unsafe_allow_html=True)


load_css(is_dark)


# ═════════════════════════════════════════════════════════════════════════════
# SIDEBAR
# ═════════════════════════════════════════════════════════════════════════════
with st.sidebar:
    st.markdown("""
    <div class="sb-logo-wrap">
      <div class="sb-emoji">🌿</div>
      <div class="sb-logo-title">AGROGUARD</div>
      <div class="sb-logo-sub">AI · Plant Doctor</div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("---")

    theme_choice = st.radio(
        "🎨 Theme",
        ["Light Mode", "Dark Mode"],
        index=1 if is_dark else 0,
        horizontal=True,
        key="theme_radio",
    )
    if (theme_choice == "Dark Mode") != is_dark:
        st.session_state.theme = "dark" if theme_choice == "Dark Mode" else "light"
        st.rerun()

    lang_choice = st.radio(
        "🌐 Language / மொழி",
        ["English", "தமிழ்"],
        horizontal=True,
        index=0 if lang == "English" else 1,
        key="lang_radio",
    )
    if lang_choice != lang:
        st.session_state.language = lang_choice
        st.rerun()

    st.markdown("---")

    model, class_names, mode = load_model_assets()
    if mode == "real":
        st.success("🟢 AI Model: ONLINE")
    else:
        st.info("🟡 Demo Mode (model file not found)")

    c1, c2, c3 = st.columns(3)
    c1.metric("Crops", "3")
    c2.metric("Classes", "15")
    c3.metric("Acc", "~90%")

    st.markdown("---")
    st.markdown(f"""
    <div style="font-size:.8rem; line-height:1.9;">
    <strong>Quick Workflow</strong><br>
    1. Upload a leaf photo<br>
    2. View diagnosis & severity<br>
    3. Get treatment plan<br>
    4. Check weather risk<br>
    5. Download PDF report<br>
    6. Chat with AgroBot
    </div>
    """, unsafe_allow_html=True)


# ═════════════════════════════════════════════════════════════════════════════
# HERO
# ═════════════════════════════════════════════════════════════════════════════
feedback_count = 0
if os.path.isfile(FEEDBACK_FILE):
    with open(FEEDBACK_FILE, encoding="utf-8") as f:
        feedback_count = max(0, sum(1 for _ in f) - 1)

st.markdown(f"""
<div class="ag-hero">
  <div class="hero-grid">
    <div class="hero-emoji">🌱</div>
    <div>
      <div class="hero-title">{txt['app_title_short']} <span class="accent">AI</span></div>
      <div class="hero-sub">{txt['tagline']} · {txt['subtitle']}</div>
    </div>
    <div class="hero-badges">
      <span class="status-pill"><span class="status-dot"></span> AI Active</span>
      <span class="status-pill">🌾 {feedback_count} Scans</span>
    </div>
  </div>
</div>
""", unsafe_allow_html=True)


# Metrics row
st.markdown(f"""
<div class="metrics-row">
  <div class="metric-cell d1"><div class="metric-val">3</div><div class="metric-lbl">Crops Supported</div></div>
  <div class="metric-cell d2"><div class="metric-val">15</div><div class="metric-lbl">Disease Classes</div></div>
  <div class="metric-cell d3"><div class="metric-val">~90%</div><div class="metric-lbl">Accuracy</div></div>
  <div class="metric-cell d4"><div class="metric-val">2</div><div class="metric-lbl">Languages</div></div>
  <div class="metric-cell d5"><div class="metric-val">24/7</div><div class="metric-lbl">Field Ready</div></div>
</div>
""", unsafe_allow_html=True)

st.markdown("""
<div class="tip-ticker">
  <span>
    🌿 Spray fungicides in the early morning or evening for best results  ·
    💧 Humidity above 80% triggers fungal outbreaks — inspect daily  ·
    🔄 Rotate crops every 3–4 years to break disease cycles  ·
    ☀ Dry sunny days are ideal for chemical application  ·
    🌱 Apply compost before monsoon for stronger plants
  </span>
</div>
""", unsafe_allow_html=True)


# ═════════════════════════════════════════════════════════════════════════════
# TABS
# ═════════════════════════════════════════════════════════════════════════════
tabs = st.tabs([
    f"🔬 {txt['tab_scan']}",
    f"🌤 {txt['tab_weather']}",
    f"📋 {txt['tab_history']}",
    f"💬 {txt['tab_chat']}",
    f"ℹ {txt['tab_about']}",
])


# ─── TAB 1 — SCAN ────────────────────────────────────────────────────────────
with tabs[0]:
    if mode == "demo":
        st.warning(
            "⚠ Running in demo mode — predictions are mocked. "
            "Place `agroguard_model.keras` and `class_indices.json` "
            "inside the `models/` folder to use your trained model."
        )

    st.markdown(f'<div class="section-title">📁 Upload Leaf Image</div>', unsafe_allow_html=True)
    uploaded = st.file_uploader(
        txt["choose_image"],
        type=["jpg", "jpeg", "png"],
        accept_multiple_files=True,
        label_visibility="collapsed",
    )

    if not uploaded:
        st.markdown(f"""
        <div class="empty-state">
          <div class="emoji">🍃</div>
          <div class="text">{txt['upload_prompt']}</div>
          <div style="font-size:.85rem; margin-top:6px;">
            Tomato · Potato · Bell Pepper
          </div>
        </div>
        """, unsafe_allow_html=True)
    else:
        for idx, file in enumerate(uploaded):
            st.markdown(f'<div class="section-title">🖼 {file.name}</div>', unsafe_allow_html=True)
            img_col, res_col = st.columns([1, 1.6], gap="large")

            img = Image.open(file)
            img_col.image(img, use_container_width=True, caption="Uploaded leaf sample")

            with res_col:
                with st.spinner("Analysing leaf with AI…"):
                    arr = preprocess_image(img)
                    best_class, confidence, top5, _ = predict_with_confidence(model, arr, class_names)

                crop_type     = next((c for c in SUPPORTED_CROPS if c.lower() in best_class.lower()), None)
                disease_label = best_class.split("___")[-1].replace("_", " ") if "___" in best_class else best_class
                is_healthy    = "healthy" in best_class.lower()
                treatment     = get_treatment(best_class)
                fertilizer    = get_fertilizer(crop_type, disease_label) if crop_type else {}
                severity      = treatment.get("severity", "Unknown")

                banner_cls  = "healthy" if is_healthy else "diseased"
                banner_icon = "✅" if is_healthy else "🚨"
                headline    = txt["healthy_plant"] if is_healthy else txt["disease_detected"]
                sev_key     = severity.lower().replace(" ", "")

                st.markdown(f"""
                <div class="result-banner {banner_cls}">
                  <div class="banner-icon">{banner_icon}</div>
                  <div style="flex:1;">
                    <div class="banner-title">{headline}</div>
                    <div class="banner-disease">{disease_label.upper()}</div>
                    <div style="margin-top:8px;">
                      {'<strong>Crop:</strong> ' + (crop_type or '—') + ' &nbsp;·&nbsp; ' if crop_type else ''}
                      <span class="sev-badge sev-{sev_key}">{severity}</span>
                    </div>
                  </div>
                </div>
                """, unsafe_allow_html=True)

                st.markdown(f"""
                <div class="conf-wrap">
                  <div class="conf-header">
                    <span>AI Confidence</span>
                    <span class="conf-pct">{confidence:.1f}%</span>
                  </div>
                  <div class="conf-track">
                    <div class="conf-fill" style="width:{confidence:.1f}%;"></div>
                  </div>
                </div>
                """, unsafe_allow_html=True)

                with st.expander("🔍 Top-5 predictions"):
                    for cls_n, prob in top5:
                        lbl = cls_n.split("___")[-1].replace("_", " ") if "___" in cls_n else cls_n
                        st.progress(min(1.0, prob / 100), text=f"{lbl} — {prob:.1f}%")

                # Treatment
                st.markdown(f'<div class="section-title">🛠 {txt["treatment_plan"]}</div>', unsafe_allow_html=True)
                if not is_healthy:
                    st.markdown(f"""
                    <div class="ag-card ag-card-yellow">
                      <div class="info-grid">
                        <div class="info-item">
                          <div class="info-lbl">⚗ Chemical</div>
                          <div class="info-val">{treatment.get('pesticide','—')}</div>
                        </div>
                        <div class="info-item">
                          <div class="info-lbl">🌿 Organic</div>
                          <div class="info-val">{treatment.get('organic','—')}</div>
                        </div>
                        <div class="info-item">
                          <div class="info-lbl">⚠ Precaution</div>
                          <div class="info-val">{treatment.get('precaution','—')}</div>
                        </div>
                        <div class="info-item">
                          <div class="info-lbl">⏱ Apply Every</div>
                          <div class="info-val">{treatment.get('treatment_days','—')}</div>
                        </div>
                      </div>
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    st.markdown(f"""
                    <div class="ag-card ag-card-green">
                      <div style="font-size:.95rem;line-height:2;">
                        ✅ {txt['water_morning']}<br>
                        ✅ {txt['proper_spacing']}<br>
                        ✅ {txt['organic_fertilizer']}<br>
                        ✅ {txt['regular_inspection']}<br>
                        ✅ {txt['crop_rotation']}
                      </div>
                    </div>
                    """, unsafe_allow_html=True)

                if fertilizer:
                    st.markdown(f'<div class="section-title">🌱 {txt["fertilizer_recommendation"]}</div>', unsafe_allow_html=True)
                    st.markdown(f"""
                    <div class="ag-card ag-card-blue">
                      <div class="info-grid">
                        <div class="info-item">
                          <div class="info-lbl">🟢 {txt['nitrogen']}</div>
                          <div class="info-val">{fertilizer.get('N','—')}</div>
                        </div>
                        <div class="info-item">
                          <div class="info-lbl">🔵 {txt['phosphorus']}</div>
                          <div class="info-val">{fertilizer.get('P','—')}</div>
                        </div>
                        <div class="info-item">
                          <div class="info-lbl">🟣 {txt['potassium']}</div>
                          <div class="info-val">{fertilizer.get('K','—')}</div>
                        </div>
                        <div class="info-item">
                          <div class="info-lbl">📋 {txt['application']}</div>
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
                if fb1.button(f"✅ {txt['feedback_correct']}", key=f"ok_{fkey}"):
                    save_feedback(file.name, best_class, "", True)
                    st.success(txt["feedback_saved"])
                    st.balloons()
                if fb2.button(f"❌ {txt['feedback_wrong']}", key=f"no_{fkey}"):
                    comment = st.text_input("Correct diagnosis:", key=f"cmt_{fkey}",
                                            placeholder="Enter correct disease name…")
                    if comment:
                        save_feedback(file.name, best_class, comment, False)
                        st.success(txt["feedback_saved"])

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


# ─── TAB 2 — WEATHER ─────────────────────────────────────────────────────────
with tabs[1]:
    st.markdown('<div class="section-title">🌦 3-Day Farming Forecast</div>', unsafe_allow_html=True)
    forecast  = get_3day_forecast()
    lang_code = "en" if lang == "English" else "ta"
    sky_map   = {"clear": "☀", "clouds": "☁", "rain": "🌧", "drizzle": "🌦",
                 "thunderstorm": "⛈", "snow": "❄", "mist": "🌫"}

    if forecast:
        cols = st.columns(3)
        for wcol, day in zip(cols, forecast):
            prec    = get_weather_precaution(day["hum"], day["sky"], day["temp"], lang_code)
            sky_low = day["sky"].lower()
            icon    = next((v for k, v in sky_map.items() if k in sky_low), "🌤")
            alert_c = "wx-warn" if "⚠" in prec else "wx-ok"
            with wcol:
                st.markdown(f"""
                <div class="wx-card">
                  <div class="wx-date">{day['date']}</div>
                  <div class="wx-icon">{icon}</div>
                  <div class="wx-temp">{day['temp']:.1f}°C</div>
                  <div class="wx-detail">{day['sky']} · 💧 {day['hum']:.0f}%</div>
                  <div class="wx-alert {alert_c}">{prec}</div>
                </div>
                """, unsafe_allow_html=True)

    st.markdown('<div class="section-title">📊 Disease Risk Matrix</div>', unsafe_allow_html=True)
    r1, r2 = st.columns(2)
    with r1:
        st.markdown("""
        <div class="ag-card ag-card-red">
          <div style="font-family:'Fraunces',serif;font-size:1.1rem;font-weight:700;margin-bottom:10px;">
            🔴 High Risk Conditions</div>
          <div class="info-grid">
            <div class="info-item"><div class="info-lbl">Humidity</div><div class="info-val">> 80% — Fungal outbreak risk</div></div>
            <div class="info-item"><div class="info-lbl">Rain</div><div class="info-val">Delay all chemical sprays</div></div>
            <div class="info-item"><div class="info-lbl">Temp</div><div class="info-val">> 32°C — Mite risk</div></div>
            <div class="info-item"><div class="info-lbl">Night Dew</div><div class="info-val">Late blight trigger zone</div></div>
          </div>
        </div>
        """, unsafe_allow_html=True)
    with r2:
        st.markdown("""
        <div class="ag-card ag-card-green">
          <div style="font-family:'Fraunces',serif;font-size:1.1rem;font-weight:700;margin-bottom:10px;">
            🟢 Ideal Conditions</div>
          <div class="info-grid">
            <div class="info-item"><div class="info-lbl">Spray Day</div><div class="info-val">Sunny, low wind, dry leaves</div></div>
            <div class="info-item"><div class="info-lbl">Transplant</div><div class="info-val">Cloudy, mild temperature</div></div>
            <div class="info-item"><div class="info-lbl">Fertilise</div><div class="info-val">No rain forecast 24 h</div></div>
            <div class="info-item"><div class="info-lbl">Harvest</div><div class="info-val">Dry, 18–26°C window</div></div>
          </div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown('<div class="section-title">📅 Seasonal Disease Calendar</div>', unsafe_allow_html=True)
    st.markdown("""
    <div class="ag-card">
      <div class="info-grid">
        <div class="info-item"><div class="info-lbl">🌧 Monsoon (Jun–Sep)</div>
          <div class="info-val">Late blight, Leaf mold, Bacterial spot — critical period</div></div>
        <div class="info-item"><div class="info-lbl">🌞 Summer (Mar–May)</div>
          <div class="info-val">Spider mites, Target spot — inspect twice weekly</div></div>
        <div class="info-item"><div class="info-lbl">🍂 Post-monsoon (Oct–Nov)</div>
          <div class="info-val">Early blight, Septoria — preventive spraying</div></div>
        <div class="info-item"><div class="info-lbl">❄ Winter (Dec–Feb)</div>
          <div class="info-val">Mosaic virus via aphids — use yellow sticky traps</div></div>
      </div>
    </div>
    """, unsafe_allow_html=True)


# ─── TAB 3 — HISTORY ─────────────────────────────────────────────────────────
with tabs[2]:
    st.markdown('<div class="section-title">📋 Scan History</div>', unsafe_allow_html=True)
    history = st.session_state.scan_history
    sev_colors = {"critical": "#ff5555", "high": "#ff9900", "medium": "#e8a838",
                  "low": "#5eea94", "none": "#5eea94", "unknown": "#888"}

    if not history:
        st.markdown("""
        <div class="empty-state">
          <div class="emoji">📂</div>
          <div class="text">No scans yet — upload a leaf image in the Scan tab</div>
        </div>
        """, unsafe_allow_html=True)
    else:
        total    = len(history)
        diseased = sum(1 for e in history if e["severity"].lower() not in ("none", "unknown"))
        critical = sum(1 for e in history if e["severity"].lower() == "critical")
        avg_conf = sum(float(e["conf"]) for e in history) / total

        st.markdown(f"""
        <div class="metrics-row" style="grid-template-columns:repeat(auto-fit,minmax(150px,1fr));">
          <div class="metric-cell"><div class="metric-val">{total}</div><div class="metric-lbl">Total Scans</div></div>
          <div class="metric-cell"><div class="metric-val">{diseased}</div><div class="metric-lbl">Diseased</div></div>
          <div class="metric-cell"><div class="metric-val">{critical}</div><div class="metric-lbl">Critical</div></div>
          <div class="metric-cell"><div class="metric-val">{avg_conf:.1f}%</div><div class="metric-lbl">Avg Confidence</div></div>
        </div>
        """, unsafe_allow_html=True)

        for i, e in enumerate(history):
            dot = sev_colors.get(e["severity"].lower(), "#888")
            dcls = f"d{(i%5)+1}"
            st.markdown(f"""
            <div class="hist-row {dcls}">
              <div class="hist-sev-dot" style="background:{dot};box-shadow:0 0 10px {dot};"></div>
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


# ─── TAB 4 — AGROBOT (Chat + Voice unified) ──────────────────────────────────
with tabs[3]:
    lang_code = "en" if lang == "English" else "ta"
    voice_lang = "ta-IN" if lang == "தமிழ்" else "en-US"

    # Initialise greeting
    if not st.session_state.chat_history:
        st.session_state.chat_history.append({"role": "bot", "text": txt["bot_greeting"]})

    chat_col, side_col = st.columns([1.7, 1], gap="large")

    with chat_col:
        st.markdown(f'<div class="section-title">💬 {txt["chat_title"]}</div>', unsafe_allow_html=True)
        st.caption(txt["voice_hint"])

        # Render chat
        # Prepare optional bot logo (bot_logo.png or assets/bot_logo.png)
        logo_b64 = None
        for pth in ("bot_logo.png", "assets/bot_logo.png", "assets/bot_logo.jpg"):
          if os.path.isfile(pth):
            try:
              with open(pth, "rb") as _f:
                logo_b64 = base64.b64encode(_f.read()).decode()
            except Exception:
              logo_b64 = None
            break

        def _safe_html(s: str) -> str:
          return (s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace("\n", "<br>"))

        chat_html = '<div class="chat-viewport">'
        for msg in st.session_state.chat_history:
          safe = _safe_html(msg["text"])
          if msg["role"] == "user":
            chat_html += f'<div class="chat-msg-user"><div class="chat-bubble-user">{safe}</div></div>'
          else:
            avatar_html = f'<div class="bot-avatar">🌿</div>'
            if logo_b64:
              avatar_html = f'<img class="bot-avatar-img" src="data:image/png;base64,{logo_b64}" alt="AgroBot" />'
            chat_html += (
              '<div class="chat-msg-bot">'
              f'{avatar_html}'
              f'<div class="chat-bubble-bot">{safe}</div>'
              '</div>'
            )
        chat_html += "</div>"
        st.markdown(chat_html, unsafe_allow_html=True)

        # Text input row (inside a form so Enter submits)
        with st.form("chat_form", clear_on_submit=True):
            c1, c2 = st.columns([5, 1])
            user_msg = c1.text_input(
                "",
                placeholder=txt["chat_placeholder"],
                label_visibility="collapsed",
                key="chat_text_in",
            )
            sent = c2.form_submit_button(f"➤ {txt['send']}")
            if sent and user_msg and user_msg.strip():
                st.session_state.chat_history.append({"role": "user", "text": user_msg.strip()})
                reply = agro_chatbot_reply(user_msg.strip(), lang_code)
                st.session_state.chat_history.append({"role": "bot", "text": reply})
                st.rerun()

        # Voice mic component — captures speech, redirects with ?voice_msg=...
        last_bot_reply = ""
        for m in reversed(st.session_state.chat_history):
            if m["role"] == "bot":
                last_bot_reply = m["text"]
                break
        # Safely JSON-encode the reply for embedding into JS
        reply_js = json.dumps(last_bot_reply)

        mic_bg    = "#5eea94" if is_dark else "#0d8a4b"
        mic_bg2   = "#6bd0ff" if is_dark else "#1e7abf"
        mic_text  = "#fff"
        mic_panel = "#13342a" if is_dark else "#f0f8f2"
        mic_border = "rgba(94,234,148,0.25)" if is_dark else "rgba(15,110,60,0.18)"
        mic_result_color = "#eaf7ef" if is_dark else "#0f2e1f"

        st.components.v1.html(f"""
        <style>
          body {{ margin:0; background:transparent; font-family:'Plus Jakarta Sans',sans-serif; }}
          .mic-panel {{
            background:{mic_panel}; border:1px solid {mic_border};
            border-radius:18px; padding:14px; display:flex; gap:10px;
            align-items:center;
          }}
          #micBtn {{
            flex: 0 0 auto;
            width:56px; height:56px; border-radius:50%;
            background: linear-gradient(135deg, {mic_bg}, {mic_bg2});
            color: {mic_text}; border: none; cursor: pointer;
            font-size: 22px; display:flex; align-items:center; justify-content:center;
            box-shadow: 0 6px 18px -4px {mic_bg}77;
            transition: all .2s;
          }}
          #micBtn:hover {{ transform: scale(1.05); }}
          #micBtn.listening {{
            background: linear-gradient(135deg, #ff4d4d, #ff8a66);
            animation: mpulse 1s ease-in-out infinite;
          }}
          @keyframes mpulse {{
            0%,100% {{ box-shadow: 0 0 0 0 rgba(255,77,77,.6); }}
            50%     {{ box-shadow: 0 0 0 14px rgba(255,77,77,0); }}
          }}
          #micStatus {{
            flex:1; font-size:.9rem; color:{mic_result_color};
            line-height:1.4;
          }}
          #ttsBtn {{
            flex:0 0 auto; padding:10px 16px; border-radius:12px;
            background:{mic_bg2}22; border:1px solid {mic_bg2}66;
            color:{mic_bg2}; cursor:pointer; font-size:.85rem; font-weight:600;
            font-family: 'Plus Jakarta Sans', sans-serif;
          }}
          #ttsBtn:hover {{ background:{mic_bg2}44; }}
        </style>

        <div class="mic-panel">
          <button id="micBtn" onclick="startVoice()" title="Speak">🎤</button>
          <div id="micStatus">Tap the mic and speak in <strong>{voice_lang}</strong>. Your question will be sent to AgroBot.</div>
          <button id="ttsBtn" onclick="speakReply()">🔊 Play reply</button>
        </div>

        <script>
        const LAST_REPLY = {reply_js};
        function startVoice() {{
          const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
          if (!SR) {{
            document.getElementById('micStatus').innerText =
              '⚠ Voice not supported — please use Google Chrome.';
            return;
          }}
          const rec = new SR();
          rec.lang = '{voice_lang}';
          rec.interimResults = false;
          rec.maxAlternatives = 1;
          const btn = document.getElementById('micBtn');
          const status = document.getElementById('micStatus');
          btn.classList.add('listening');
          btn.innerText = '⏺';
          status.innerText = '🎙 Listening…';
          rec.onresult = function(e) {{
            const text = e.results[0][0].transcript;
            status.innerText = '🗣 "' + text + '" — sending to AgroBot…';
            btn.classList.remove('listening'); btn.innerText = '🎤';
            // Navigate parent Streamlit page with the transcript as query param
            const url = new URL(window.parent.location.href);
            url.searchParams.set('voice_msg', text);
            window.parent.location.href = url.toString();
          }};
          rec.onerror = function(e) {{
            status.innerText = '⚠ Error: ' + e.error;
            btn.classList.remove('listening'); btn.innerText = '🎤';
          }};
          rec.onend = function() {{
            btn.classList.remove('listening'); btn.innerText = '🎤';
          }};
          rec.start();
        }}
        function speakReply() {{
          window.speechSynthesis.cancel();
          if (!LAST_REPLY) return;
          const u = new SpeechSynthesisUtterance(LAST_REPLY);
          u.lang = '{voice_lang}'; u.rate = 0.92;
          window.speechSynthesis.speak(u);
        }}
        // Auto-speak the most recent bot reply (once per page load)
        window.addEventListener('load', function() {{
          setTimeout(function() {{
            try {{
              if (LAST_REPLY && sessionStorage.getItem('last_spoken') !== LAST_REPLY) {{
                sessionStorage.setItem('last_spoken', LAST_REPLY);
                const u = new SpeechSynthesisUtterance(LAST_REPLY);
                u.lang = '{voice_lang}'; u.rate = 0.92; u.volume = 0.9;
                window.speechSynthesis.speak(u);
              }}
            }} catch(e) {{}}
          }}, 400);
        }});
        </script>
        """, height=110)

        if st.button(f"🗑 {txt['clear']} Chat", key="clear_chat"):
            st.session_state.chat_history = []
            st.session_state.last_voice_msg = ""
            st.rerun()

    with side_col:
        st.markdown(f'<div class="section-title">⚡ {txt["quick_questions"]}</div>', unsafe_allow_html=True)

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
                st.session_state.chat_history.append(
                    {"role": "bot", "text": agro_chatbot_reply(q, lang_code)}
                )
                st.rerun()

        st.markdown('<div class="section-title" style="margin-top:1rem;">🌿 AgroBot can help with</div>',
                    unsafe_allow_html=True)
        st.markdown(f"""
        <div class="ag-card" style="font-size:.88rem; line-height:2;">
          🔬 Disease identification<br>
          💊 Chemical &amp; organic treatment<br>
          🌱 NPK fertiliser planning<br>
          🌦 Weather farming advice<br>
          📅 Seasonal crop calendar<br>
          🔄 Crop rotation guidance
        </div>
        """, unsafe_allow_html=True)


# ─── TAB 5 — ABOUT ───────────────────────────────────────────────────────────
with tabs[4]:
    st.markdown('<div class="section-title">ℹ About AgroGuard</div>', unsafe_allow_html=True)
    st.markdown("""
    <div class="ag-card ag-card-green">
      <p style="font-size:.95rem; line-height:1.7;">
        <strong>AgroGuard AI</strong> is a bilingual (English + Tamil) plant-disease
        detection assistant for tomato, potato and bell-pepper crops. It combines a
        convolutional neural network trained on the PlantVillage dataset with a
        curated knowledge base of treatments, fertiliser plans and weather-based
        farming advice.
      </p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown('<div class="section-title">🧠 Model details</div>', unsafe_allow_html=True)
    st.markdown("""
    <div class="ag-card">
      <div class="info-grid">
        <div class="info-item"><div class="info-lbl">Architecture</div><div class="info-val">CNN (MobileNetV2 / EfficientNet recommended)</div></div>
        <div class="info-item"><div class="info-lbl">Input size</div><div class="info-val">224 × 224 RGB</div></div>
        <div class="info-item"><div class="info-lbl">Normalisation</div><div class="info-val">pixel / 127.5 − 1.0</div></div>
        <div class="info-item"><div class="info-lbl">Dataset</div><div class="info-val">PlantVillage — 15 classes</div></div>
        <div class="info-item"><div class="info-lbl">Tomato</div><div class="info-val">10 disease classes</div></div>
        <div class="info-item"><div class="info-lbl">Potato</div><div class="info-val">3 classes</div></div>
        <div class="info-item"><div class="info-lbl">Bell pepper</div><div class="info-val">2 classes</div></div>
        <div class="info-item"><div class="info-lbl">Accuracy</div><div class="info-val">~85–90% on test set</div></div>
      </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown('<div class="section-title">🛠 Hardware integration roadmap</div>', unsafe_allow_html=True)
    st.markdown("""
    <div class="ag-card ag-card-blue">
      <div style="font-size:.9rem; line-height:2;">
        📷 Raspberry Pi Camera v3 — leaf capture in the field<br>
        🔊 I²S speaker + mic — offline voice I/O<br>
        📡 LoRa SX1276 — long-range field communication<br>
        🌡 DHT22 sensor — humidity &amp; temperature monitoring<br>
        🖥 7″ touch LCD — farmer interface<br>
        🔋 Solar + LiPo — self-sufficient power
      </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown('<div class="section-title">📁 Project file structure</div>', unsafe_allow_html=True)
    st.code("""agroguard/
├── app.py              ← Streamlit UI
├── model_utils.py      ← Model loading + demo-mode fallback
├── services.py         ← Weather, treatment DB, bilingual chatbot
├── config.py           ← Strings, treatment DB, fertiliser DB
├── requirements.txt
├── models/
│   ├── agroguard_model.keras   (your trained CNN — not included)
│   └── class_indices.json
├── feedback_data.csv   (auto-generated)
└── README.md""", language="text")

    st.markdown('<div class="section-title">🚀 Future improvements</div>', unsafe_allow_html=True)
    st.markdown("""
    <div class="ag-card">
      <div style="font-size:.9rem; line-height:2;">
        • Mobile camera capture (st.camera_input)<br>
        • Expand to rice, maize and wheat<br>
        • CI/CD retraining from feedback CSV<br>
        • Push notifications for high-severity detections<br>
        • Offline PWA wrapper for field use<br>
        • Hindi, Telugu and Kannada language support
      </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown('<div class="section-title">👥 Credits</div>', unsafe_allow_html=True)
    st.markdown("""
    <div class="ag-card" style="text-align:center;">
      <div style="font-family:'Fraunces',serif; font-size:1.1rem; font-weight:600;">
        Built with 💚 for farmers
      </div>
      <div style="font-size:.85rem; margin-top:8px; opacity:.8;">
        Python · TensorFlow · Streamlit · OpenWeatherMap · PlantVillage
      </div>
    </div>
    """, unsafe_allow_html=True)


# ─── FOOTER ──────────────────────────────────────────────────────────────────
st.markdown(f"""
<div class="ag-footer">
  🌾 {txt['footer']}<br>
  <span style="opacity:.7;">⚠ {txt['disclaimer']}</span>
</div>
""", unsafe_allow_html=True)
