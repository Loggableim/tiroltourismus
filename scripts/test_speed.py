#!/usr/bin/env python3
"""Speed test for local GPU model."""
import json, urllib.request, time

API_URL = "http://localhost:8080/v1/chat/completions"
TYP_LABELS = {"hotel":"Hotel","gasthof":"Gasthof","ferienwohnung":"Ferienwohnung","ferienhaus":"Ferienhaus","jugendherberge":"Jugendherberge","camping":"Campingplatz","bauernhof":"Bauernhof"}

def gen(ort, typ, name):
    body = {
        "model": "Dolphin3.0-Llama3.1-8B-Q4_K_M",
        "messages": [
            {"role": "system", "content": "Du schreibst kurze, sachliche Beschreibungen für ein Tirol-Tourismusportal. Deutsch, maximal 120 Wörter, als HTML-Paragraph."},
            {"role": "user", "content": f"Schreibe 2-3 Sätze HTML über {name} in {ort}, Tirol. Art: {TYP_LABELS.get(typ,typ)}. Sachlich, maximal 120 Wörter. Format: <p>Text mit <strong>Hervorhebungen</strong>.</p>"}
        ],
        "max_tokens": 200, "temperature": 0.4,
    }
    t0 = time.time()
    req = urllib.request.Request(API_URL, data=json.dumps(body).encode(), headers={"Content-Type":"application/json"}, method="POST")
    resp = urllib.request.urlopen(req, timeout=120)
    result = json.loads(resp.read())
    text = result["choices"][0]["message"]["content"].strip()
    if not text.startswith("<"): text = f"<p>{text}</p>"
    return text, time.time() - t0

for name, ort, typ in [("Bilgeri Irma","Nesselwängle","ferienwohnung"),("Bio Landhaus Seethaler","Thiersee","hotel"),("Blattlbauer","Going am Wilden Kaiser","gasthof")]:
    text, t = gen(ort, typ, name)
    print(f"  {name} ({t:.1f}s): {text[:120]}...")
