# Ausstehende Betriebs-Einträge

Hier landen von Admin freigegebene Betriebs-Einträge als JSON.

## Struktur

```
src/data/pending/{slug}/index.json
```

## Workflow

1. Betrieb registriert sich via `/fuer-betriebe/registrierung/` (localStorage)
2. Admin prüft unter `/admin/pending/` und klickt "Freigeben"
3. Admin exportiert das JSON aus dem Dashboard
4. JSON wird hier als `src/data/pending/{slug}/index.json` abgelegt
5. Nach Build-Durchlauf ist der Eintrag live

## JSON-Schema

```json
{
  "slug": "gasthof-zur-post",
  "name": "Gasthof zur Post",
  "typ": "Gastronomie (Restaurant, Café, Bar)",
  "ort": "Innsbruck",
  "kurzbeschreibung": "Traditioneller Gasthof im Herzen von Innsbruck...",
  "kontakt": {
    "email": "info@gasthof-zur-post.at",
    "telefon": "+43 512 1234567"
  },
  "bildUrl": "https://example.com/foto.jpg",
  "status": "published",
  "erstelltAm": "2026-05-18T10:00:00.000Z",
  "veroeffentlichtAm": "2026-05-18T10:30:00.000Z"
}
```
