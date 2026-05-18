import os, json, urllib.request

key = os.environ.get('OPENCODE_GO_API_KEY', '')
print(f'Key length: {len(key)}')

body = {
    'model': 'deepseek-v4-flash',
    'messages': [{'role': 'user', 'content': 'Say hi'}],
    'max_tokens': 10
}
req = urllib.request.Request(
    'https://opencode.ai/zen/go/v1/chat/completions',
    data=json.dumps(body).encode(),
    headers={
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {key}',
        'User-Agent': 'curl/8.0',
    },
    method='POST'
)
try:
    resp = urllib.request.urlopen(req, timeout=15)
    result = json.loads(resp.read())
    print('OK:', result['choices'][0]['message']['content'])
except urllib.request.HTTPError as e:
    print(f'HTTP Error: {e.code} {e.reason}')
    print(f'Response body: {e.read().decode()[:500]}')
except Exception as e:
    print(f'Error: {type(e).__name__}: {e}')
