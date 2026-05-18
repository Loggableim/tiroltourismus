#!/usr/bin/env python3
"""Test various settings for the model."""
import json, os, urllib.request, ssl

API_URL = "https://opencode.ai/zen/go/v1/chat/completions"
API_KEY = os.environ.get("OPENCODE_GO_API_KEY", "")

for max_tok in [1500, 2000, 4000]:
    body = {
        "model": "deepseek-v4-flash",
        "messages": [
            {"role": "system", "content": "Du schreibst kurze, sachliche Beschreibungen für ein Tirol-Tourismusportal. Deutsch, maximal 120 Wörter, als HTML-Paragraph. Antworte direkt, ohne nachzudenken."},
            {"role": "user", "content": "Schreibe 2-3 Sätze HTML über 'Camping Rossbach' in Nassereith, Tirol, Österreich. Art: Campingplatz. Maximal 120 Wörter. Format: <p>Text mit <strong>Hervorhebungen</strong>.</p>"}
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
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        },
        method="POST"
    )

    resp = urllib.request.urlopen(req, timeout=60, context=ctx)
    result = json.loads(resp.read())
    content = result["choices"][0]["message"]["content"].strip()
    usage = result["usage"]
    reasoning = usage.get("completion_tokens_details", {}).get("reasoning_tokens", 0)
    total_comp = usage["completion_tokens"]
    visible = total_comp - reasoning
    print(f"max_tokens={max_tok}: content='{content[:80]}...' finish={result['choices'][0]['finish_reason']} reasoning={reasoning} visible={visible} total_comp={total_comp}")
