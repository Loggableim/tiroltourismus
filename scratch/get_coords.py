import json, os, urllib.request, urllib.parse, time

places = [
    ("Kufstein", "Tyrol", "Austria"),
    ("Thiersee", "Tyrol", "Austria"),
    ("Söll", "Tyrol", "Austria"),
    ("Ebbs", "Tyrol", "Austria"),
    ("Scheffau am Wilden Kaiser", "Tyrol", "Austria"),
    ("Neustift im Stubaital", "Tyrol", "Austria"),
    ("Fulpmes", "Tyrol", "Austria"),
    ("St. Anton am Arlberg", "Tyrol", "Austria"),
    ("Umhausen", "Tyrol", "Austria"),
    ("Kaunertal", "Tyrol", "Austria"),
    ("Ellmau", "Tyrol", "Austria"),
]

for name, region, country in places:
    q = f"{name}, {region}, {country}"
    url = f"https://nominatim.openstreetmap.org/search?q={urllib.parse.quote(q)}&format=json&limit=1"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "TirolGastroBot/1.0"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read())
            if data:
                lat = data[0]["lat"]
                lon = data[0]["lon"]
                print(f'{name}: {{"lat": "{lat}", "lng": "{lon}"}}')
            else:
                print(f'{name}: NOT FOUND')
    except Exception as e:
        print(f'{name}: ERROR - {e}')
    time.sleep(1)
