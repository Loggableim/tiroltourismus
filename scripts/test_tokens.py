#!/usr/bin/env python3
"""Test with much higher max_tokens and longer timeout."""
import json, os, ssl, urllib.request, sys, time

env_file = "E:/HermesPortable/home/.env"
with open(env_file) as f:
    for line in f:
        line = line.strip()
        if '=' in line and not line.startswith('#'):
            k, v = line.split('=', 1)
            os.environ[k] = v

API_KEY = os.environ.get("OPENCODE_GO_API_KEY", "")
API_URL = "https://opencode.ai/zen/go/v1/chat/completions"

# Try various max_tokens settings
for max_tok in [512, 1024, 2048, 4096]:
    body = {
        "model": "deepseek-v4-flash",
        "messages": [
            {"role": "system", "content": "Du schreibst kurze, sachliche Beschreibungen für ein Tirol-Tourismusportal. Deutsch, maximal 120 Wörter, als HTML-Paragraph."},
            {"role": "user", "content": "Schreibe 2-3 Sätze HTML über 'Hotel Landhof' in Ellmau, Tirol. Art: Hotel. Format: <p>Text</p>"}
        ],
        "max_tokens": max_tok,
        "temperature": 0.4,
    }
    
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    
    req = urllib.request.Request(
        API_URL,
        data=json.dumps(body).encode(),
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {API_KEY}",
            "User-Agent": "Mozilla/5.0",
        },
        method="POST"
    )
    
    try:
        resp = urllib.request.urlopen(req, timeout=120, context=ctx)
        result = json.loads(resp.read())
        text = result["choices"][0]["message"]["content"].strip()
        fin_reason = result["choices"][0].get("finish_reason", "?")
        usage = result.get("usage", {})
        rt = (usage.get("completion_tokens_details") or {}).get("reasoning_tokens", 0)
        print(f"max_tokens={max_tok:5d}: finish={fin_reason:8s} reason_tok={rt:5d} content_len={len(text):4d} '{text[:100]}'")
    except Exception as e:
        print(f"max_tokens={max_tok:5d}: ERROR {e}")
