import json, urllib.request, os

key = os.environ.get("OPENCODE_GO_API_KEY", "")

# Try the tourism prompt with high max_tokens
body = {
    "model": "deepseek-v4-flash",
    "messages": [
        {"role": "system", "content": "Du schreibst kurze, sachliche Beschreibungen für ein Tirol-Tourismusportal. Deutsch, maximal 120 Wörter, als HTML-Paragraph."},
        {"role": "user", "content": "Schreibe 2-3 Sätze HTML über 'Posthotel Erlerwirt' in Erl, Tirol, Österreich. Art: Hotel. Beschreibe die Lage, Atmosphäre und was Gäste erwartet. Sachlich, kein Marketington, kein Superlativ."}
    ],
    "max_tokens": 2000,
    "temperature": 0.4,
}
req = urllib.request.Request(
    "https://opencode.ai/zen/go/v1/chat/completions",
    data=json.dumps(body).encode(),
    headers={
        "Content-Type": "application/json",
        "Authorization": f"Bearer {key}",
        "User-Agent": "curl/8.0.0",
    },
    method="POST"
)
try:
    resp = urllib.request.urlopen(req, timeout=60)
    result = json.loads(resp.read())
    content = result["choices"][0]["message"]["content"].strip()
    print(f"Content length: {len(content)}")
    print(f"Content: {content[:500]}")
    print(f"Finish reason: {result['choices'][0]['finish_reason']}")
    usage = result["usage"]
    print(f"Usage: {usage}")
    r = result["choices"][0]["message"].get("reasoning_content", "")
    print(f"Reasoning chars: {len(r)}")
except Exception as e:
    print(f"Error: {e}")
