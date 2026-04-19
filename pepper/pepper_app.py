#!/usr/bin/env python3
import streamlit as st
import requests
import os
import json
from PIL import Image, ImageDraw

st.set_page_config(page_title="AgVision - Pepper Ripeness Counter", layout="wide")
st.title("🌶️ AgVision Analytics — Pepper Ripeness Counter")
st.markdown("Automated pepper fruit detection & ripeness staging powered by LandingAI")

api_key = os.environ.get("LANDINGAI_API_KEY")

# Ripeness classes: prompt, box color, display label
RIPENESS_CLASSES = [
    {"prompt": "red chili pepper",                 "color": "#FF2222", "label": "Ripe (Red)"},
    {"prompt": "orange chili pepper turning red",  "color": "#FF8C00", "label": "Turning (Orange)"},
    {"prompt": "yellow or green chili pepper",     "color": "#FFD700", "label": "Unripe (Yellow/Green)"},
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
    conf_threshold = st.slider("Min confidence", 0.0, 1.0, 0.15, 0.05,
        help="Lower = detect more peppers, Higher = fewer but more certain")

uploaded_file = st.file_uploader(
    "Upload pepper field image", type=['jpg', 'jpeg', 'png']
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
        return raw[0] if (isinstance(raw, list) and raw and isinstance(raw[0], list)) else raw
    return []

if uploaded_file and api_key:
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("📸 Original Image")
        image = Image.open(uploaded_file)
        st.image(image, use_column_width=True)
        st.caption(f"Size: {image.width} x {image.height} px")

    if st.button("🔍 Analyze Ripeness", type="primary"):

        temp_path = "temp_pepper.jpg"
        try:
            with open(temp_path, "wb") as f:
                f.write(uploaded_file.getbuffer())

            annotated = image.copy().convert("RGB")
            draw = ImageDraw.Draw(annotated)

            all_results = {}
            total_all = 0

            progress = st.progress(0, text="Detecting ripeness stages...")

            for i, cls in enumerate(RIPENESS_CLASSES):
                progress.progress(
                    (i + 1) / len(RIPENESS_CLASSES),
                    text=f"Detecting: {cls['label']}..."
                )
                preds = run_detection(temp_path, cls["prompt"], api_key)

                # Apply confidence filter
                preds = [p for p in preds if p.get("score", 1.0) >= conf_threshold]

                all_results[cls["label"]] = preds
                total_all += len(preds)

                color = cls["color"]
                for pred in preds:
                    bbox = pred.get("bounding_box", [])
                    if len(bbox) == 4:
                        x1, y1, x2, y2 = bbox
                        draw.rectangle([x1, y1, x2, y2], outline=color, width=3)
                        draw.rectangle([x1, y1, x1+90, y1+16], fill=color)
                        draw.text((x1+3, y1+1), cls["label"][:14], fill="white")

            progress.empty()

            with col2:
                st.subheader("🌶️ Ripeness Map")
                st.image(annotated, use_column_width=True)

            st.divider()
            st.subheader("📊 Ripeness Summary")

            cols = st.columns(len(RIPENESS_CLASSES) + 1)
            cols[0].metric("🌶️ Total Peppers", total_all)

            report = {"total_peppers": total_all, "ripeness_breakdown": {}}

            for i, cls in enumerate(RIPENESS_CLASSES):
                count = len(all_results[cls["label"]])
                pct = (count / total_all * 100) if total_all > 0 else 0
                cols[i+1].metric(cls["label"], count, f"{pct:.0f}% of total")
                report["ripeness_breakdown"][cls["label"]] = {
                    "count": count,
                    "percent_of_total": round(pct, 1)
                }

            ripe_count   = len(all_results[RIPENESS_CLASSES[0]["label"]])
            orange_count = len(all_results[RIPENESS_CLASSES[1]["label"]])

            if total_all > 0:
                ripeness_index = ((ripe_count * 1.0) + (orange_count * 0.5)) / total_all * 100
                st.divider()
                st.subheader("🏹 Ripeness Index")
                st.progress(int(ripeness_index))
                ri_col1, ri_col2 = st.columns(2)
                ri_col1.metric("Ripeness Index", f"{ripeness_index:.1f} / 100",
                               help="0 = all unripe, 100 = fully ripe")
                harvest_ready = ripe_count / total_all * 100
                ri_col2.metric("Harvest-Ready", f"{harvest_ready:.1f}%",
                               help="% of peppers fully ripe")

                if harvest_ready >= 70:
                    st.success("✅ Ready to harvest! Over 70% of peppers are ripe.")
                elif harvest_ready >= 40:
                    st.warning("⏳ Approaching harvest — monitor daily.")
                else:
                    st.info("🌱 Early stage — majority still unripe.")

            report["ripeness_index"] = round(ripeness_index if total_all > 0 else 0, 1)

            st.download_button(
                "⬇️ Download Ripeness Report (JSON)",
                json.dumps(report, indent=2),
                "pepper_ripeness_report.json",
                mime="application/json"
            )
            st.success("✅ Analysis complete!")

        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)
else:
    if not uploaded_file:
        st.info("👆 Upload a pepper field image to get started")
