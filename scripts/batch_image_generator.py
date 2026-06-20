#!/usr/bin/env python3
"""
Batch Image Generator for tiroltourismus.com
Generiert fehlende Hero-Bilder für Orte, POIs und Gastro via HuggingFace FLUX.1-schnell.
"""

import json
import os
import sys
import time
import requests

HF_TOKEN = os.environ.get("HF_TOKEN")
if not HF_TOKEN:
    try:
        with open("/c/sidekick/home/auth.json") as f:
            auth = json.load(f)
        for name, creds in auth.get("credential_pool", {}).items():
            if "hugging" in name.lower() or "hf" in name.lower():
                for c in creds:
                    if c.get("access_token"):
                        HF_TOKEN = c["access_token"]
                        break
    except:
        pass

API_URL = "https://router.huggingface.co/hf-inference/models/black-forest-labs/FLUX.1-schnell"
HEADERS = {"Authorization": f"Bearer {HF_TOKEN}"}

def generate_image(prompt, output_path):
    """Generate an image via HuggingFace FLUX API and save to path."""
    payload = {"inputs": prompt, "parameters": {"num_inference_steps": 4}}
    try:
        resp = requests.post(API_URL, headers=HEADERS, json=payload, timeout=120)
        if resp.status_code == 200:
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            with open(output_path, "wb") as f:
                f.write(resp.content)
            return True, len(resp.content)
        else:
            return False, f"HTTP {resp.status_code}: {resp.text[:100]}"
    except Exception as e:
        return False, str(e)

def main():
    base = "F:/tiroltourismus"
    generator_type = sys.argv[1] if len(sys.argv) > 1 else "orte"
    
    if generator_type == "orte":
        data_dir = os.path.join(base, "src/data/orte")
        img_base = os.path.join(base, "public/images/orte")
        
        for d in sorted(os.listdir(data_dir)):
            idx = os.path.join(data_dir, d, "index.json")
            if not os.path.isfile(idx): continue
            
            with open(idx, encoding="utf-8") as f:
                data = json.load(f)
            
            # Skip if already has hero_bild
            if data.get("hero_bild"): continue
            
            name = data.get("name", d)
            region = data.get("region", "Tirol")
            kat = data.get("kategorie", "dorf")
            hoehe = data.get("hoehe", "")
            bezirk = data.get("bezirk", "")
            
            prompt = (
                f"A scenic travel photo of {name}, a beautiful {kat} in "
                f"{region}, Tirol, Austria. Alpine landscape with traditional "
                f"Tyrolean houses with flower boxes, green meadows, "
                f"snow-capped mountains in background, blue sky with white "
                f"clouds. Professional travel photography, bright and inviting, "
                f"high resolution, 16:9 landscape. No text, no watermark."
            )
            
            img_dir = os.path.join(img_base, d)
            img_path = os.path.join(img_dir, "hero_1.png")
            
            print(f"[{name}] Generating... ", end="", flush=True)
            success, result = generate_image(prompt, img_path)
            
            if success:
                print(f"✅ {result//1024}KB")
                # Update JSON
                img_rel = f"/images/orte/{d}/hero_1.png"
                data["hero_bild"] = img_rel
                data["bilder"] = [{"url": img_rel, "alt": f"{name} — Aquarell"}]
                with open(idx, "w", encoding="utf-8") as f:
                    json.dump(data, f, indent=2, ensure_ascii=False)
            else:
                print(f"❌ {result}")
            
            time.sleep(0.5)  # Rate limit
        
        print("\n=== Orte-Bilder abgeschlossen ===")
    
    elif generator_type == "poi":
        data_dir = os.path.join(base, "src/data/sehenswuerdigkeiten")
        img_base = os.path.join(base, "public/images/sehenswuerdigkeiten")
        
        for d in sorted(os.listdir(data_dir)):
            idx = os.path.join(data_dir, d, "index.json")
            if not os.path.isfile(idx): continue
            with open(idx, encoding="utf-8") as f:
                data = json.load(f)
            if data.get("hero_bild"): continue
            
            name = data.get("name", d)
            ort = data.get("ort", "Tirol")
            kat = data.get("kategorie", "sehenswuerdigkeit")
            
            prompt = (
                f"A professional travel photo of {name} near {ort}, Tirol, "
                f"Austria. This is a {kat} attraction. Beautiful alpine "
                f"landscape, sunny day. Professional travel photography, "
                f"bright colors, high quality, 16:9 landscape. No text."
            )
            
            img_dir = os.path.join(img_base, d)
            img_path = os.path.join(img_dir, "hero_1.png")
            
            print(f"[{name}] Generating... ", end="", flush=True)
            success, result = generate_image(prompt, img_path)
            
            if success:
                print(f"✅ {result//1024}KB")
                img_rel = f"/images/sehenswuerdigkeiten/{d}/hero_1.png"
                data["hero_bild"] = img_rel
                data["bilder"] = [{"url": img_rel, "alt": f"{name}"}]
                with open(idx, "w", encoding="utf-8") as f:
                    json.dump(data, f, indent=2, ensure_ascii=False)
            else:
                print(f"❌ {result}")
            
            time.sleep(0.5)

if __name__ == "__main__":
    main()
