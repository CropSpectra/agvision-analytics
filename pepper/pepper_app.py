#!/usr/bin/env python3
import streamlit as st
import requests
import os
import json
from PIL import Image, ImageDraw

st.set_page_config(page_title="AgVision - Pepper Ripeness Counter", layout="wide")

st.title("🌶️ AgVision Analytics — Pepper Ripeness Counter")
st.markdown("Automated pepper fruit detection and ripeness staging powered by LandingAI")

api_key = os.environ.get("LANDINGAI_API_KEY")

RIPENESS_CLASSES = [
    {"prompt": "red chili pepper", "color": "#FF2222", "label": "Ripe (Red)"},
    {"prompt": "orange chili pepper turning red", "color": "#FF8C00", "label": "Turning (Orange)"},
    {"prompt": "yellow or green chili pepper", "color": "#FFD700", "label": "Unripe (Yellow/Green)"},
]

with st.sidebar:
    st.header("⚙️ Settings")

    if api_key:
        st.success("✅ API key configured")
    else:
        st.error("❌ Set LANDINGAI_API_KEY environment variable")
        st.stop()

    st.divider()
    st.markdown("**Ripeness Legend**")
    for cls in RIPENESS_CLASSES:
        st.markdown(
            f'<span style="background:{cls["color"]};padding:2px 10px;'
            f'border-radius:4px;color:white;font-weight:bold">&nbsp;</span> '
            f'{cls["label"]}',
            unsafe_allow_html=True
        )

    st.divider()
    conf_threshold = st.slider(
        "Min confidence",
        0.0,
        1.0,
        0.15,
        0.05,
        help="Lower values detect more peppers; higher values keep only more confident detections."
    )

uploaded_file = st.file_uploader(
    "Upload pepper field image",
    type=["jpg", "jpeg", "png"]
)


def run_detection(image_path, prompt, api_key):
    url = "https://api.va.landing.ai/v1/tools/agentic-object-detection"

    with open(image_path, "rb") as f:
        response = requests.post(
            url,
            files={"image": f},
            data={"prompts": prompt, "model": "agentic"},
            headers={"Authorization": f"Basic {api_key}"}
        )

    if response.status_code == 200:
        raw = response.json().get("data", [])
        if isinstance(raw, list) and raw and isinstance(raw[0], list):
            return raw[0]
        return raw

    return []


if uploaded_file and api_key:
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("📸 Original 
