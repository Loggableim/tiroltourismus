#!/usr/bin/env python3
"""Test local GPU model for description generation."""
import json, urllib.request, os, sys

API_URL = "http://localhost:8080/v1/chat/completions"

def test():
    body = {
        "model": "Dolphin3.0-Llama3.1-8B-Q4_K_M",
        "messages": [
            {"role": "system", "content": "Du schreibst kurze, sachliche Beschreibungen für ein Tirol-Tourismusportal. Deutsch, maximal 120 Wörter, als HTML-Paragraph."},
            {"role": "user", "content": "Schreibe 2-3 Sätze HTML über 'Bilgeri Camping' in Tirol, Österreich. Art: Campingplatz. Beschreibe die Lage, Atmosphäre und was Gäste erwartet. Sachlich, kein Marketington, kein Superlativ. Maximal 120 Wörter. Format: <p>Text mit <strong>Hervorhebungen</strong>.</p>"}
        ],
        "max_tokens": 200,
        "temperature": 0.4,
    }
    req = urllib.request.Request(
        API_URL,
        data=json.dumps(body).encode(),
        headers={"Content-Type": "application/json"},
        method="POST"
    )
    resp = urllib.request.urlopen(req, timeout=60)
    result = json.loads(resp.read())
    text = result["choices"][0]["message"]["content"].strip()
    if not text.startswith("<"):
        text = f"<p>{text}</p>"
    print(text)
    
if __name__ == "__main__":
    test()
