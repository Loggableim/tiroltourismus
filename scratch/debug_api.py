#!/usr/bin/env python3
import json, os, urllib.request

API_URL = 'https://opencode.ai/zen/go/v1/chat/completions'
API_KEY = os.environ.get('OPENCODE_GO_API_KEY', '')

body = {
    'model': 'deepseek-v4-flash',
    'messages': [
        {'role': 'system', 'content': 'Du schreibst kurze, sachliche Beschreibungen für ein Tirol-Tourismusportal. Deutsch, maximal 120 Wörter, als HTML-Paragraph.'},
        {'role': 'user', 'content': "Schreibe 2-3 Sätze HTML über 'Campingplatz Segelflugverein Ausserfern' in Höfen, Tirol, Österreich. Art: Campingplatz. Beschreibe die Lage, Atmosphäre und was Gäste erwartet. Sachlich, kein Marketington, kein Superlativ. Maximal 120 Wörter. Format: <p>Text mit <strong>Hervorhebungen</strong>.</p>"}
    ],
    'max_tokens': 200,
    'temperature': 0.4,
}

req = urllib.request.Request(
    API_URL,
    data=json.dumps(body).encode(),
    headers={
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {API_KEY}',
    },
    method='POST'
)
resp = urllib.request.urlopen(req, timeout=30)
result = json.loads(resp.read())
text = result['choices'][0]['message']['content'].strip()
print(f'Response text: |{text}|')
print(f'Full result: {json.dumps(result, indent=2)[:800]}')
