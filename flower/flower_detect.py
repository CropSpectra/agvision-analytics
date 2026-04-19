#!/usr/bin/env python3
import requests
import os
import json

def detect_flowers(image_path, api_key, prompt="flowers"):
    url = "https://api.va.landing.ai/v1/tools/agentic-object-detection"
    
    print(f"🔍 Analyzing: {image_path}")
    print(f"📝 Prompt: '{prompt}'")
    print("-" * 60)
    
    with open(image_path, "rb") as image_file:
        files = {"image": image_file}
        data = {"prompts": prompt, "model": "agentic"}
        headers = {"Authorization": f"Basic {api_key}"}
        
        response = requests.post(url, files=files, data=data, headers=headers)
        
        if response.status_code == 200:
            return response.json()
        else:
            print(f"Error {response.status_code}: {response.text}")
            return None

def analyze_results(results):
    if not results or 'data' not in results or not results['data']:
        print("No predictions found")
        return
    
    predictions = results['data'][0] if isinstance(results['data'], list) and results['data'] else []
    
    if not predictions:
        print("No predictions found")
        return
    
    flower_count = len(predictions)
    total_area = 0
    sizes = []
    
    print(f"\n🌸 RESULTS")
    print("=" * 60)
    print(f"Total Flowers Detected: {flower_count}\n")
    
    for i, pred in enumerate(predictions, 1):
        bbox = pred.get('bounding_box', [])
        
        if len(bbox) == 4:
            x1, y1, x2, y2 = bbox
            width = x2 - x1
            height = y2 - y1
            area = width * height
            total_area += area
            sizes.append(area)
    
    if sizes:
        avg_area = total_area / flower_count
        min_area = min(sizes)
        max_area = max(sizes)
        
        print("📊 SUMMARY")
        print("=" * 60)
        print(f"Total flowers: {flower_count}")
        print(f"Average flower area: {avg_area:.1f} px²")
        print(f"Min flower area: {min_area:.1f} px²")
        print(f"Max flower area: {max_area:.1f} px²")
        print(f"Total coverage: {total_area:.1f} px²")

def main():
    api_key = os.environ.get("LANDINGAI_API_KEY")
    
    if not api_key:
        print("Error: LANDINGAI_API_KEY not set")
        return
    
    image_path = "flower_test.jpeg"
    
    if not os.path.exists(image_path):
        print(f"Error: Image not found: {image_path}")
        return
    
    print("=" * 60)
    print("🌸 AUTOMATED FLOWER PHENOTYPING")
    print("=" * 60)
    
    results = detect_flowers(image_path, api_key, prompt="flowers")
    
    if results:
        with open('flower_results.json', 'w') as f:
            json.dump(results, f, indent=2)
        print("Results saved to: flower_results.json")
        analyze_results(results)
        print("\n✅ Analysis complete!")

if __name__ == "__main__":
    main()

