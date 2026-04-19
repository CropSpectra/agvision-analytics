#!/usr/bin/env python3
import streamlit as st
import requests
import os
import json
from PIL import Image, ImageDraw

st.set_page_config(page_title="AgVision - Pepper Counter", layout="wide")
st.title("🌶️ AgVision Analytics — Pepper Fruit Counter")
st.markdown("Automated pepper fruit counting powered by LandingAI")

# API key from environment variable
api_key = os.environ.get("LANDINGAI_API_KEY")

with st.sidebar:
    st.header("⚙️ Settings")
    if api_key:
        st.success("✅ API key configured")
    else:
        st.error("❌ Set LANDINGAI_API_KEY environment variable")
        st.stop()

uploaded_file = st.file_uploader("Upload pepper field image", type=['jpg', 'jpeg', 'png'])

if uploaded_file and api_key:
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("📸 Original Image")
        image = Image.open(uploaded_file)
        st.image(image, use_column_width=True)

    if st.button("🌶️ Count Peppers", type="primary"):
        with st.spinner("Detecting peppers..."):
            temp_path = "temp_pepper.jpg"
            try:
                with open(temp_path, "wb") as f:
                    f.write(uploaded_file.getbuffer())

                url = "https://api.va.landing.ai/v1/tools/agentic-object-detection"

                with open(temp_path, "rb") as image_file:
                    files = {"image": image_file}
                    data = {"prompts": "pepper fruit", "model": "agentic"}
                    headers = {"Authorization": f"Basic {api_key}"}
                    response = requests.post(url, files=files, data=data, headers=headers)

                if response.status_code == 200:
                    results = response.json()
                    raw = results.get('data', [])
                    predictions = raw[0] if (isinstance(raw, list) and raw and isinstance(raw[0], list)) else raw

                    if predictions:
                        pepper_count = len(predictions)
                        areas = []
                        total_area = 0

                        # Draw bounding boxes
                        annotated = image.copy().convert("RGB")
                        draw = ImageDraw.Draw(annotated)

                        for pred in predictions:
                            bbox = pred.get('bounding_box', [])
                            score = pred.get('score', 0)
                            if len(bbox) == 4:
                                x1, y1, x2, y2 = bbox
                                area = (x2 - x1) * (y2 - y1)
                                areas.append(area)
                                total_area += area
                                draw.rectangle([x1, y1, x2, y2], outline="red", width=2)
                                draw.text((x1 + 2, y1 + 2), f"{score:.2f}", fill="yellow")

                        with col2:
                            st.subheader("🌶️ Detected Peppers")
                            st.image(annotated, use_column_width=True)

                        st.divider()
                        m1, m2, m3 = st.columns(3)
                        m1.metric("🌶️ Total Peppers", pepper_count)
                        m2.metric("📐 Avg Fruit Size", f"{total_area/pepper_count:.0f} px²")
                        m3.metric("📈 Image Coverage", f"{(total_area/(image.width*image.height))*100:.1f}%")

                        report = {
                            "pepper_count": pepper_count,
                            "average_area_px2": total_area / pepper_count,
                            "min_area_px2": min(areas),
                            "max_area_px2": max(areas),
                            "total_area_px2": total_area,
                            "coverage_percent": (total_area / (image.width * image.height)) * 100
                        }

                        st.download_button(
                            "⬇️ Download Report",
                            json.dumps(report, indent=2),
                            "pepper_count_results.json",
                            mime="application/json"
                        )
                        st.success("✅ Analysis complete!")

                    else:
                        st.warning("No peppers detected. Try a clearer image.")
                else:
                    st.error(f"❌ API Error {response.status_code}")
                    st.code(response.text)
            finally:
                if os.path.exists(temp_path):
                    os.remove(temp_path)
else:
    if not uploaded_file:
        st.info("👆 Upload a pepper field image to get started")
