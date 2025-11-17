#!/usr/bin/env python3
import streamlit as st
import requests
import os
import json
from PIL import Image

st.set_page_config(page_title="AgVision Analytics", layout="wide")

st.title("🌸 AgVision Analytics Platform")
st.markdown("Professional Flower Phenotyping & Analysis")

# Hardcoded API key
api_key = "NjE4OHlmaXltZjNkdWc4Z2U1aWJ2OnBveURndUFzNlZiQ0k1V214b2ZOMkc2SVhoZTc0dEJ2"

with st.sidebar:
    st.header("⚙️ Settings")
    st.success("✅ API key configured")

uploaded_file = st.file_uploader("Upload flower image", type=['jpg', 'jpeg', 'png'])

if uploaded_file and api_key:
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📸 Original Image")
        image = Image.open(uploaded_file)
        st.image(image, use_column_width=True)
    
    if st.button("🔍 Analyze Flowers", type="primary"):
        with st.spinner("Analyzing image..."):
            temp_path = "temp_upload.jpg"
            with open(temp_path, "wb") as f:
                f.write(uploaded_file.getbuffer())
            
            url = "https://api.va.landing.ai/v1/tools/agentic-object-detection"
            
            with open(temp_path, "rb") as image_file:
                files = {"image": image_file}
                data = {"prompts": "flowers", "model": "agentic"}
                headers = {"Authorization": f"Basic {api_key}"}
                
                response = requests.post(url, files=files, data=data, headers=headers)
            
            if response.status_code == 200:
                results = response.json()
                predictions = results.get('data', [[]])[0] if 'data' in results else []
                
                if predictions:
                    flower_count = len(predictions)
                    total_area = 0
                    areas = []
                    
                    for pred in predictions:
                        bbox = pred.get('bounding_box', [])
                        if len(bbox) == 4:
                            x1, y1, x2, y2 = bbox
                            width = x2 - x1
                            height = y2 - y1
                            area = width * height
                            total_area += area
                            areas.append(area)
                    
                    with col2:
                        st.subheader("📊 Results")
                        
                        col2a, col2b, col2c = st.columns(3)
                        
                        with col2a:
                            st.metric("🌸 Flowers", flower_count)
                        
                        with col2b:
                            avg_area = total_area / flower_count if flower_count > 0 else 0
                            st.metric("📐 Avg Size", f"{avg_area:.0f} px²")
                        
                        with col2c:
                            coverage = (total_area / (image.width * image.height)) * 100
                            st.metric("📈 Coverage", f"{coverage:.1f}%")
                    
                    st.subheader("📋 Detailed Stats")
                    col3a, col3b, col3c, col3d = st.columns(4)
                    
                    with col3a:
                        st.write(f"**Min:** {min(areas):.0f} px²")
                    with col3b:
                        st.write(f"**Max:** {max(areas):.0f} px²")
                    with col3c:
                        st.write(f"**Avg:** {total_area/flower_count:.0f} px²")
                    with col3d:
                        st.write(f"**Total:** {total_area:.0f} px²")
                    
                    results_data = {
                        "flower_count": flower_count,
                        "average_area": total_area / flower_count,
                        "min_area": min(areas),
                        "max_area": max(areas),
                        "coverage_percent": coverage
                    }
                    
                    st.download_button(
                        "⬇️ Download Report",
                        json.dumps(results_data, indent=2),
                        "flower_analysis.json",
                        mime="application/json"
                    )
                    st.success("✅ Analysis complete!")
                else:
                    st.error("❌ No flowers detected")
            else:
                st.error(f"❌ Error: {response.status_code}")
                st.error(response.text)
            
            if os.path.exists(temp_path):
                os.remove(temp_path)
else:
    if not uploaded_file:
        st.info("👆 Upload an image to get started")

