#!/usr/bin/env python3
import json
import os

import requests
import streamlit as st
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


def run_detection(image_path, prompt, api_key):
    url = "https://api.va.landing.ai/v1/tools/agentic-object-detection"

    with open(image_path, "rb") as f:
        response = requests.post(
            url,
            files={"image": f},
            data={"prompts": prompt, "model": "agentic"},
            headers={"Authorization": f"Basic {api_key}"},
            timeout=120,
        )

    if response.status_code == 200:
        raw = response.json().get("data", [])
        if isinstance(raw, list) and raw and isinstance(raw[0], list):
            return raw[0]
        return raw

    st.warning(f"Detection request failed for prompt '{prompt}' with status {response.status_code}.")
    return []


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
            unsafe_allow_html=True,
        )

    st.divider()
    conf_threshold = st.slider(
        "Min confidence",
        min_value=0.0,
        max_value=1.0,
        value=0.15,
        step=0.05,
        help="Lower values detect more peppers; higher values keep only more confident detections.",
    )

uploaded_file = st.file_uploader(
    "Upload pepper field image",
    type=["jpg", "jpeg", "png"],
)

if uploaded_file and api_key:
    col1, col2 = st.columns(2)
    image = Image.open(uploaded_file)

    with col1:
        st.subheader("📸 Original Image")
        st.image(image, width="stretch")
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
                    text=f"Detecting: {cls['label']}...",
                )

                preds = run_detection(temp_path, cls["prompt"], api_key)
                preds = [p for p in preds if p.get("score", 1.0) >= conf_threshold]

                all_results[cls["label"]] = preds
                total_all += len(preds)

                for pred in preds:
                    bbox = pred.get("bounding_box", [])
                    if len(bbox) == 4:
                        x1, y1, x2, y2 = bbox
                        color = cls["color"]
                        draw.rectangle([x1, y1, x2, y2], outline=color, width=3)
                        draw.rectangle([x1, y1, x1 + 110, y1 + 18], fill=color)
                        draw.text((x1 + 4, y1 + 2), cls["label"][:16], fill="white")

            progress.empty()

            with col2:
                st.subheader("🌶️ Ripeness Map")
                st.image(annotated, width="stretch")

            st.divider()
            st.subheader("📊 Ripeness Summary")

            cols = st.columns(len(RIPENESS_CLASSES) + 1)
            cols[0].metric("🌶️ Total Peppers", total_all)

            report = {
                "total_peppers": total_all,
                "ripeness_breakdown": {},
            }

            for i, cls in enumerate(RIPENESS_CLASSES):
                count = len(all_results[cls["label"]])
                pct = (count / total_all * 100) if total_all > 0 else 0

                cols[i + 1].metric(cls["label"], count, f"{pct:.0f}% of total")

                report["ripeness_breakdown"][cls["label"]] = {
                    "count": count,
                    "percent_of_total": round(pct, 1),
                }

            ripe_count = len(all_results[RIPENESS_CLASSES[0]["label"]])

            if total_all > 0:
                harvest_ready = ripe_count / total_all * 100

                st.divider()
                st.subheader("🚜 Harvest Readiness")

                hr_col1, hr_col2 = st.columns(2)
                hr_col1.metric(
                    "Harvest-Ready",
                    f"{harvest_ready:.1f}%",
                    help="Percent of detected peppers that are fully ripe.",
                )
                hr_col2.metric("Fully Ripe Count", ripe_count)

                if harvest_ready >= 70:
                    st.success("✅ Ready to harvest. More than 70% of detected peppers are fully ripe.")
                elif harvest_ready >= 40:
                    st.warning("⏳ Approaching harvest. Continue monitoring the field closely.")
                else:
                    st.info("🌱 Early stage. Most detected peppers are still not fully ripe.")

                report["harvest_ready_percent"] = round(harvest_ready, 1)
                report["fully_ripe_count"] = ripe_count

            st.download_button(
                "⬇️ Download Ripeness Report (JSON)",
                json.dumps(report, indent=2),
                file_name="pepper_ripeness_report.json",
                mime="application/json",
            )

            st.success("✅ Analysis complete!")

        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)

else:
    st.info("👆 Upload a pepper field image to get started.")
