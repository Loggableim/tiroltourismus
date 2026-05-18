/**
 * content-schema.js — Schema-Definitionen aller Collections
 * 
 * Dient als Doku für Agents: welche Collections gibt's, welche Felder,
 * welche Typen. Jeder Eintrag liegt in src/data/{collection}/{slug}/index.json
 * 
 * Singletons liegen direkt in src/data/{name}.json
 */

export const COLLECTIONS = {
  regionen: {
    label: 'Regionen',
    slugLabel: 'titel',
    fields: {
      titel:          { type: 'string', required: true, desc: 'Name der Region' },
      emoji:          { type: 'string', desc: 'Emoji-Icon (z.B. 🏔️)' },
      farbe:          { type: 'string', desc: 'Akzentfarbe als Hex (z.B. #0051BA)' },
      kurzbeschreibung:{ type: 'text', desc: 'Kurzer Teaser (1 Satz)' },
      beschreibung:   { type: 'richtext', desc: 'HTML-Inhalt mit Highlights' },
      bewertung:      { type: 'number', min: 1, max: 5 },
      hoehe:          { type: 'string', desc: 'z.B. "3.774 m"' },
      flaeche:        { type: 'string', desc: 'z.B. "530 km²"' },
      einwohner:      { type: 'string' },
      tags:           { type: 'array', items: 'string' },
      featured:       { type: 'boolean' },
      status:         { type: 'enum', values: ['published', 'draft', 'archived'] },
    },
    related: ['unterkuenfte', 'orte', 'gastro'],
  },

  unterkuenfte: {
    label: 'Unterkünfte',
    slugLabel: 'name',
    fields: {
      name:          { type: 'string', required: true },
      typ:           { type: 'enum', values: ['hotel', 'ferienwohnung', 'bauernhof', 'jugendherberge', 'camping'] },
      sterne:        { type: 'number', min: 1, max: 5 },
      tier:          { type: 'enum', values: ['gold', 'silver', 'basic'], desc: 'Free-Mium Tier' },
      preis_ab:      { type: 'number', desc: 'Preis in €/Nacht' },
      ort:           { type: 'string' },
      plz:           { type: 'string' },
      region:        { type: 'string', desc: 'Slug der Region (z.B. "oetztal")' },
      adresse:       { type: 'string' },
      telefon:       { type: 'string' },
      email:         { type: 'string' },
      webseite:      { type: 'url' },
      beschreibung:  { type: 'richtext' },
      ausstattung:   { type: 'array', items: 'string', desc: 'z.B. wifi, fruehstueck, sauna' },
      tags:          { type: 'array', items: 'string' },
      status:        { type: 'enum', values: ['published', 'draft', 'archived'] },
    },
    related: [],
  },

  gastro: {
    label: 'Gastronomie',
    slugLabel: 'name',
    fields: {
      name:           { type: 'string', required: true },
      emoji:          { type: 'string' },
      farbe:          { type: 'string' },
      kategorie:      { type: 'string', desc: 'z.B. cafe, restaurant, bar' },
      kurzbeschreibung:{ type: 'text' },
      beschreibung:   { type: 'richtext' },
      ort:            { type: 'string' },
      adresse:        { type: 'string' },
      region:         { type: 'string' },
      telefon:        { type: 'string' },
      email:          { type: 'string' },
      webseite:       { type: 'url' },
      preis:          { type: 'string', desc: 'Preiskategorie (€, €€, €€€)' },
      tags:           { type: 'array', items: 'string' },
      status:         { type: 'enum', values: ['published', 'draft', 'archived'] },
    },
    related: [],
  },

  orte: {
    label: 'Orte',
    slugLabel: 'name',
    fields: {
      name:           { type: 'string', required: true },
      emoji:          { type: 'string' },
      farbe:          { type: 'string' },
      kurzbeschreibung:{ type: 'text' },
      hoehe:          { type: 'string' },
      einwohner:      { type: 'string' },
      region:         { type: 'string' },
      tags:           { type: 'array', items: 'string' },
      status:         { type: 'enum', values: ['published', 'draft', 'archived'] },
    },
    related: ['unterkuenfte', 'gastro'],
  },

  sehenswuerdigkeiten: {
    label: 'Sehenswürdigkeiten',
    slugLabel: 'name',
    fields: {
      name:           { type: 'string', required: true },
      emoji:          { type: 'string' },
      farbe:          { type: 'string' },
      kategorie:      { type: 'enum', values: ['natur', 'kultur', 'aussicht', 'sport', 'museum', 'kirche', 'burg', 'wanderung'] },
      kurzbeschreibung:{ type: 'text' },
      beschreibung:   { type: 'richtext' },
      ort:            { type: 'string' },
      region:         { type: 'string' },
      hoehe:          { type: 'string' },
      dauer:          { type: 'string', desc: 'z.B. "1-2 Stunden"' },
      preis:          { type: 'string', desc: 'z.B. "12 € (Erwachsene)"' },
      oeffnungszeiten:{ type: 'string' },
      koordinaten:    { type: 'string' },
      webseite:       { type: 'url' },
      tags:           { type: 'array', items: 'string' },
      status:         { type: 'enum', values: ['published', 'draft', 'archived'] },
    },
    related: [],
  },

  magazin: {
    label: 'Magazin-Artikel',
    slugLabel: 'titel',
    fields: {
      titel:          { type: 'string', required: true },
      teaser:         { type: 'text' },
      datum:          { type: 'date' },
      autor:          { type: 'string' },
      kategorie:      { type: 'string' },
      tags:           { type: 'array', items: 'string' },
      inhalt:         { type: 'richtext', desc: 'HTML-Content des Artikels' },
      status:         { type: 'enum', values: ['published', 'draft', 'archived'] },
    },
    related: [],
  },
};

export const SINGLETONS = {
  home: {
    label: 'Homepage (JSON-basiert)',
    fields: ['hero_titel', 'hero_sub', 'hero_cta', 'stats'],
  },
  einstellungen: {
    label: 'Site-Einstellungen',
    fields: ['site_name', 'site_description', 'kontakt_email', 'kontakt_telefon', 'social'],
  },
  bezirke: {
    label: 'Bezirke Tirols (Singleton)',
    fields: ['innsbruck', 'innsbruck-land', 'imst', 'landeck', 'reutte', 'kufstein', 'kitzbuehel', 'schwaz', 'lienz'],
  },
  homepage: {
    label: 'Homepage (vollständig, alt)',
    fields: ['hero', 'stats', 'seelen', 'whyTirol', 'regionen', 'unterkuenfte', 'activities', 'events', 'magazin'],
  },
};
