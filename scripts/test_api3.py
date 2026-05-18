#!/usr/bin/env python3
"""Test API call with proper cert and higher token limits."""
import json, os, requests, urllib.request, ssl, certifi

env_file = "E:/HermesPortable/home/.env"
with open(env_file) as f:
    for line in f:
        line = line.strip()
        if '=' in line and not line.startswith('#'):
            k, v = line.split('=', 1)
            os.environ[k] = v

API_KEY = os.environ.get("OPENCODE_GO_API_KEY", "")
ca_bundle = certifi.where()
print(f"Using CA bundle: {ca_bundle}")

# Test 1: requests with certifi verify
print("\n=== Test 1: requests with certifi verify ===")
try:
    resp = requests.post(
        "https://opencode.ai/zen/go/v1/chat/completions",
        json={
            "model": "deepseek-v4-flash",
            "messages": [
                {"role": "system", "content": "Du schreibst kurze, sachliche Beschreibungen für ein Tirol-Tourismusportal. Deutsch, maximal 120 Wörter, als HTML-Paragraph."},
                {"role": "user", "content": "Schreibe 2-3 Sätze HTML über 'Hotel Landhof' in Ellmau, Tirol, Österreich. Art: Hotel. Beschreibe die Lage, Atmosphäre und was Gäste erwartet. Sachlich, kein Marketington. Maximal 120 Wörter. Format: <p>Text mit <strong>Hervorhebungen</strong>.</p>"}
            ],
            "max_tokens": 400,
            "temperature": 0.4,
        },
        headers={"Authorization": f"Bearer {API_KEY}"},
        timeout=30,
        verify=ca_bundle
    )
    print(f"Status: {resp.status_code}")
    result = resp.json()
    text = result["choices"][0]["message"]["content"].strip()
    print(f"Finish reason: {result['choices'][0].get('finish_reason', '?')}")
    print(f"Usage: {result.get('usage', {})}")
    print(f"Content: '{text}'")
    if text:
        print(f"Content length: {len(text)}")
    else:
        # Check reasoning content
        msg = result["choices"][0]["message"]
        if "reasoning_content" in msg:
            print(f"Reasoning (first 200): {msg['reasoning_content'][:200]}")
except Exception as e:
    print(f"Error: {e}")

# Test 2: urllib with certifi context
print("\n=== Test 2: urllib with certifi context ===")
try:
    ctx = ssl.create_default_context(cafile=ca_bundle)
    body = {
        "model": "deepseek-v4-flash",
        "messages": [
            {"role": "system", "content": "Du schreibst kurze, sachliche Beschreibungen für ein Tirol-Tourismusportal."},
            {"role": "user", "content": "Schreibe 2-3 Sätze HTML über 'Hotel Landhof' in Ellmau. Format: <p>Text</p>"}
        ],
        "max_tokens": 400,
        "temperature": 0.4,
    }
    req = urllib.request.Request(
        "https://opencode.ai/zen/go/v1/chat/completions",
        data=json.dumps(body).encode(),
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {API_KEY}",
        },
        method="POST"
    )
    resp = urllib.request.urlopen(req, timeout=30, context=ctx)
    result = json.loads(resp.read())
    text = result["choices"][0]["message"]["content"].strip()
    print(f"Status: {resp.status}")
    print(f"Content: '{text[:300]}'")
except Exception as e:
    print(f"Error: {e}")
