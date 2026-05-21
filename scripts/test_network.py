import requests, sys
r = requests.get('https://httpbin.org/get', timeout=10)
print('httpbin:', r.status_code, len(r.text))
r2 = requests.get('https://google.com', timeout=10)
print('google:', r2.status_code, len(r2.text))
