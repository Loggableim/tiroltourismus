/**
 * seo.js — SEO Meta Description Generator
 * Erzeugt 120–160 Zeichen lange Meta Descriptions mit
 * Keyword-vorne + CTA für alle Collection-Typen.
 *
 * Nutzung:
 *   import { generateMetaDescription } from '../lib/seo.js';
 *   description={generateMetaDescription(entry, 'camping')}
 */

/**
 * Stripped HTML-Tags aus einem String
 */
function stripHtml(html) {
  if (!html) return '';
  return html
    .replace(/<[^>]+>/g, ' ')    // Tags entfernen
    .replace(/&[a-z]+;/g, ' ')   // HTML-Entities
    .replace(/\s+/g, ' ')        // Mehrfach-Leerzeichen
    .trim();
}

/**
 * Kürzt Text auf maximal `maxLen` Zeichen,
 * bricht an der letzten natürlichen Satz-/Komma-Grenze.
 */
function truncateText(text, maxLen = 150) {
  if (!text || text.length <= maxLen) return text || '';

  const truncated = text.slice(0, maxLen);
  // Letzte natürliche Grenze finden: . ! ? , — –
  const boundaries = ['.', '!', '?', ',', '–', '—', ';'];
  let cutAt = -1;
  for (const b of boundaries) {
    const idx = truncated.lastIndexOf(b);
    if (idx > Math.floor(maxLen * 0.6) && idx > cutAt) cutAt = idx;
  }
  if (cutAt > 0) return truncated.slice(0, cutAt + 1).trim();
  // Keine schöne Grenze → am letzten Leerzeichen trennen + …
  const lastSpace = truncated.lastIndexOf(' ');
  if (lastSpace > 0) return truncated.slice(0, lastSpace).trim() + ' …';
  return truncated.trim();
}

/**
 * Extrahiert den ersten aussagekräftigen Satz aus Beschreibungs-HTML.
 * Überspringt einleitende Floskeln ("Der/Die/Das … liegt/befindet"),
 * da der Name bereits als Keyword vorangestellt wird.
 * Liefert maximal ~90 Zeichen, damit build() nicht mitten im Satz kürzen muss.
 */
function extractDescription(htmlText) {
  const text = stripHtml(htmlText);
  if (!text) return '';

  // Sätze aufteilen und schwache Einleitungen überspringen (max 3)
  const sentences = text.match(/[^.!?]+[.!?]+/g);
  if (!sentences || sentences.length === 0) return text.slice(0, 90);

  const weakStart = /^(der|die|das|den|dem|des|ein|eine|einen|einer|eines)\s.*(liegt|befindet|ist|bietet|hat|verfügt|wird)/i;
  let startIdx = 0;
  for (let i = 0; i < Math.min(3, sentences.length); i++) {
    if (weakStart.test(sentences[i].trim())) {
      startIdx = i + 1;
    } else {
      break;
    }
  }

  if (startIdx >= sentences.length) {
    return sentences[0].trim().slice(0, 90);
  }

  // Nimm nur den ersten guten Satz (max 90 Zeichen)
  const first = sentences[startIdx].trim();
  return first.length > 90 ? first.slice(0, 87).trim() + ' …' : first;
}

export const COLLECTION_CATEGORY_TITLES = {
  de: {
    camping: 'Campingplätze',
    unterkuenfte: 'Unterkünfte',
    regionen: 'Regionen',
    orte: 'Orte',
    gastro: 'Gastro',
    sehenswuerdigkeiten: 'Sehenswertes',
    erlebnisse: 'Erlebnisse',
    events: 'Events',
    magazin: 'Magazin',
    bezirke: 'Bezirke',
  },
  en: {
    camping: 'Camping',
    unterkuenfte: 'Accommodations',
    regionen: 'Regions',
    orte: 'Places',
    gastro: 'Food & Drink',
    sehenswuerdigkeiten: 'Sights',
    erlebnisse: 'Experiences',
    events: 'Events',
    magazin: 'Magazine',
    bezirke: 'Districts',
  },
  fr: {
    camping: 'Camping',
    unterkuenfte: 'Hébergements',
    regionen: 'Régions',
    orte: 'Villages',
    gastro: 'Gastronomie',
    sehenswuerdigkeiten: 'Sites',
    erlebnisse: 'Expériences',
    events: 'Événements',
    magazin: 'Magazine',
    bezirke: 'Districts',
  },
  it: {
    camping: 'Campeggio',
    unterkuenfte: 'Alloggi',
    regionen: 'Regioni',
    orte: 'Paesi',
    gastro: 'Gastronomia',
    sehenswuerdigkeiten: 'Attrazioni',
    erlebnisse: 'Esperienze',
    events: 'Eventi',
    magazin: 'Magazine',
    bezirke: 'Distretti',
  },
  es: {
    camping: 'Camping',
    unterkuenfte: 'Alojamientos',
    regionen: 'Regiones',
    orte: 'Pueblos',
    gastro: 'Gastronomía',
    sehenswuerdigkeiten: 'Atracciones',
    erlebnisse: 'Experiencias',
    events: 'Eventos',
    magazin: 'Revista',
    bezirke: 'Distritos',
  },
  zh: {
    camping: '露营',
    unterkuenfte: '住宿',
    regionen: '地区',
    orte: '村镇',
    gastro: '美食',
    sehenswuerdigkeiten: '景点',
    erlebnisse: '体验',
    events: '活动',
    magazin: '杂志',
    bezirke: '行政区',
  },
  nl: {
    camping: 'Campings',
    unterkuenfte: 'Accommodaties',
    regionen: 'Regio’s',
    orte: 'Plaatsen',
    gastro: 'Eten & drinken',
    sehenswuerdigkeiten: 'Bezienswaardigheden',
    erlebnisse: 'Belevenissen',
    events: 'Evenementen',
    magazin: 'Magazine',
    bezirke: 'Districten',
  },
  cs: {
    camping: 'Kempy',
    unterkuenfte: 'Ubytování',
    regionen: 'Regiony',
    orte: 'Místa',
    gastro: 'Gastronomie',
    sehenswuerdigkeiten: 'Pamětihodnosti',
    erlebnisse: 'Zážitky',
    events: 'Akce',
    magazin: 'Časopis',
    bezirke: 'Okresy',
  },
};

/**
 * Titel-Vorlage pro Sprache:
 * Format: `<Name> – <Ort> | <Kategorie> | tiroltourismus`
 * Max. 60 Zeichen. Fallback wenn Ort fehlt: `<Name> | <Kategorie> | tiroltourismus`
 *
 * @param {object} entry
 * @param {string} collection
 * @param {string} [locale='de']
 * @returns {string}
 */
export function buildPageTitle(entry, collection, locale = 'de') {
  if (!entry) return 'tiroltourismus';

  const name = (entry.name || entry.titel || '').trim();
  const ort = (entry.ort || '').trim();
  const catMap = COLLECTION_CATEGORY_TITLES[locale] || COLLECTION_CATEGORY_TITLES.de;
  const category = (catMap && catMap[collection]) || collection || '';
  const brand = 'tiroltourismus';

  // Ideale Vorlage
  let title = '';
  if (name && ort && category) {
    title = `${name} – ${ort} | ${category} | ${brand}`;
  } else if (name && category) {
    title = `${name} | ${category} | ${brand}`;
  } else if (name) {
    title = `${name} | ${brand}`;
  } else {
    return brand;
  }

  if (title.length <= 60) {
    return title;
  }

  // Wenn zu lang (> 60), versuchen wir zuerst ohne Ort:
  if (ort && category) {
    const withoutOrt = `${name} | ${category} | ${brand}`;
    if (withoutOrt.length <= 60) {
      return withoutOrt;
    }
  }

  // Wenn immer noch zu lang, ohne Kategorie:
  const minimal = `${name} | ${brand}`;
  if (minimal.length <= 60) {
    return minimal;
  }

  // Wenn Name allein mit " | tiroltourismus" schon > 60 Zeichen ist:
  // Namenskürzung mit Ellipsis
  const maxNameLen = 60 - ` | ${brand}`.length;
  if (maxNameLen > 3) {
    return `${name.slice(0, maxNameLen - 1).trim()}… | ${brand}`;
  }

  return title.slice(0, 60);
}

/**
 * CTA-Phrasen pro Sprache und Collection
 */
export const CTAS_BY_LOCALE = {
  de: {
    camping:        '✅ Campingplatz in Tirol – jetzt Plätze sichern!',
    unterkuenfte:   '✅ Jetzt Unterkunft buchen und Tirol erleben!',
    regionen:       '🏔️ Jetzt Reise nach Tirol planen!',
    orte:           '📍 Jetzt Ort entdecken und Ausflug planen!',
    gastro:         '🍽️ Jetzt Tisch reservieren und genießen!',
    sehenswuerdigkeiten: '🏛️ Jetzt Sehenswürdigkeit entdecken!',
    erlebnisse:     '🎯 Jetzt Erlebnis buchen!',
    events:         '🎪 Jetzt Event besuchen – Tickets sichern!',
    magazin:        '📖 Jetzt lesen und inspirieren lassen!',
    bezirke:        '🗺️ Jetzt Bezirk entdecken und Ausflug planen!',
    default:        '✅ Jetzt mehr erfahren!',
  },
  en: {
    camping:        '✅ Campsite in Tyrol – book your pitch now!',
    unterkuenfte:   '✅ Book accommodation now and experience Tyrol!',
    regionen:       '🏔️ Plan your trip to Tyrol now!',
    orte:           '📍 Discover town and plan your excursion!',
    gastro:         '🍽️ Reserve a table now and enjoy!',
    sehenswuerdigkeiten: '🏛️ Discover sights now!',
    erlebnisse:     '🎯 Book your experience now!',
    events:         '🎪 Visit event – get tickets now!',
    magazin:        '📖 Read now and get inspired!',
    bezirke:        '🗺️ Discover district and plan your visit!',
    default:        '✅ Discover more now!',
  },
  fr: {
    camping:        '✅ Camping au Tyrol – réservez votre emplacement!',
    unterkuenfte:   '✅ Réservez votre hébergement et découvrez le Tyrol!',
    regionen:       '🏔️ Planifiez votre voyage au Tyrol dès maintenant!',
    orte:           '📍 Découvrez le village et planifiez votre excursion!',
    gastro:         '🍽️ Réservez une table et profitez de la cuisine alpine!',
    sehenswuerdigkeiten: '🏛️ Découvrez les sites incontournables du Tyrol!',
    erlebnisse:     '🎯 Réservez votre expérience dès maintenant!',
    events:         '🎪 Participez à l\'événement – réservez vos billets!',
    magazin:        '📖 Lisez dès maintenant et faites le plein d\'inspiration!',
    bezirke:        '🗺️ Découvrez le district et planifiez votre sortie!',
    default:        '✅ En savoir plus dès maintenant!',
  },
  it: {
    camping:        '✅ Campeggio in Tirolo – prenota subito la piazzola!',
    unterkuenfte:   '✅ Prenota subito l\'alloggio e vivi il Tirolo!',
    regionen:       '🏔️ Pianifica subito il tuo viaggio in Tirolo!',
    orte:           '📍 Scopri il paese e organizza la tua gita!',
    gastro:         '🍽️ Prenota subito un tavolo e gusta le specialità!',
    sehenswuerdigkeiten: '🏛️ Scopri subito le attrazioni del Tirolo!',
    erlebnisse:     '🎯 Prenota subito la tua esperienza!',
    events:         '🎪 Partecipa all\'evento – assicurati i biglietti!',
    magazin:        '📖 Leggi ora e lasciati ispirare!',
    bezirke:        '🗺️ Scopri il distretto e organizza la tua visita!',
    default:        '✅ Scopri di più subito!',
  },
  es: {
    camping:        '✅ Camping en Tirol – ¡reserva tu parcela ahora!',
    unterkuenfte:   '✅ ¡Reserva tu alojamiento y vive el Tirol!',
    regionen:       '🏔️ ¡Planifica tu viaje a Tirol ahora!',
    orte:           '📍 ¡Descubre el pueblo y planifica tu excursión!',
    gastro:         '🍽️ ¡Reserva mesa ahora y disfruta de la gastronomía!',
    sehenswuerdigkeiten: '🏛️ ¡Descubre atracciones imperdibles en Tirol!',
    erlebnisse:     '🎯 ¡Reserva tu experiencia ahora!',
    events:         '🎪 Asiste al evento – ¡consigue tus entradas!',
    magazin:        '📖 ¡Lee ahora e inspírate con nuestras historias!',
    bezirke:        '🗺️ ¡Descubre el distrito y planifica tu visita!',
    default:        '✅ ¡Descubre más ahora!',
  },
  zh: {
    camping:        '✅ 蒂罗尔露营地 – 立即锁定理想营位！',
    unterkuenfte:   '✅ 立即预订住宿，畅享蒂罗尔度假时光！',
    regionen:       '🏔️ 立即规划您的蒂罗尔之旅！',
    orte:           '📍 探索美丽城镇，规划精彩出行！',
    gastro:         '🍽️ 立即预订餐桌，享用地道高山美食！',
    sehenswuerdigkeiten: '🏛️ 立即探索蒂罗尔经典景点！',
    erlebnisse:     '🎯 立即预订难忘体验！',
    events:         '🎪 参加精彩活动 – 立即抢票！',
    magazin:        '📖 立即阅读获取旅行灵感！',
    bezirke:        '🗺️ 探索行政区，开启发现之旅！',
    default:        '✅ 了解更多详情！',
  },
  nl: {
    camping:        '✅ Camping in Tirol – reserveer nu je staanplaats!',
    unterkuenfte:   '✅ Boek nu accommodatie en beleef Tirol!',
    regionen:       '🏔️ Plan nu je reis naar Tirol!',
    orte:           '📍 Ontdek de plaats en plan je uitstap!',
    gastro:         '🍽️ Reserveer nu een tafel en geniet!',
    sehenswuerdigkeiten: '🏛️ Ontdek nu bezienswaardigheden in Tirol!',
    erlebnisse:     '🎯 Boek nu jouw belevenis!',
    events:         '🎪 Bezoek evenement – bemachtig nu tickets!',
    magazin:        '📖 Lees nu en doe inspiratie op!',
    bezirke:        '🗺️ Ontdek het district en plan je bezoek!',
    default:        '✅ Ontdek nu meer!',
  },
  cs: {
    camping:        '✅ Kemp v Tyrolsku – zajistěte si místo ještě dnes!',
    unterkuenfte:   '✅ Rezervujte ubytování a zažijte Tyrolsko!',
    regionen:       '🏔️ Naplánujte si cestu do Tyrolska ještě dnes!',
    orte:           '📍 Objevte místo a naplánujte si výlet!',
    gastro:         '🍽️ Rezervujte si stůl a vychutnejte speciality!',
    sehenswuerdigkeiten: '🏛️ Objevte tyrolské pamětihodnosti ještě dnes!',
    erlebnisse:     '🎯 Rezervujte si svůj zážitek ještě dnes!',
    events:         '🎪 Navštivte akci – zajistěte si vstupenky!',
    magazin:        '📖 Čtěte nyní a nechte se inspirovat!',
    bezirke:        '🗺️ Objevte okres a naplánujte si výlet!',
    default:        '✅ Zjistěte více ještě dnes!',
  },
};

export const CTAS = CTAS_BY_LOCALE.de;
export const CTAS_EN = CTAS_BY_LOCALE.en;

/**
 * Hauptfunktion: Erzeugt eine SEO-optimierte Meta Description
 *
 * @param {object} entry          - Das CMS-Entry-Objekt
 * @param {string} collection     - Collection-Name (camping, unterkuenfte, …)
 * @param {string} [locale='de']  - Sprache (de, en, fr, it, es, zh, nl, cs)
 * @param {object} [opts]         - Optionale Parameter
 * @param {string} [opts.typLabel] - Typ-Label für unterkuenfte
 * @returns {string}              - 120–160 Zeichen langer Description-Text
 */
export function generateMetaDescription(entry, collection, locale = 'de', opts = {}) {
  if (!entry) return '';

  const name = entry.name || entry.titel || '';
  const ort = entry.ort || '';
  const localeCTAs = CTAS_BY_LOCALE[locale] || CTAS_BY_LOCALE.de;
  const cta = localeCTAs[collection] || localeCTAs.default;
  const isDE = locale === 'de';

  /**
   * Helper: Baut finalen String aus Main-Keyword + Body + CTA
   * und kürzt auf 120–160 Zeichen
   */
  function build(keyword, body) {
    let result = keyword;
    let separator = '';
    if (body) {
      // Bug-Fix: Body, der mit dem Namen beginnt → Duplikat entfernen
      if (keyword && body.toLowerCase().startsWith(keyword.toLowerCase())) {
        body = body.substring(keyword.length).replace(/^[\s:–\-.,]+/, '').trim();
      }
      if (body) {
        separator = body.length > 80 ? ': ' : ' – ';
        result += separator + body.replace(/[.!?]+$/, '').trim();
      }
    }
    // CTA anhängen (wenn Platz)
    const ctaJoined = '. ' + cta;
    const totalWithCTA = result.length + ctaJoined.length;
    if (totalWithCTA <= 160) {
      result += ctaJoined;
    } else if (result.length > 120) {
      // CTA nicht reinpassend, truncate body
      result = keyword + separator + truncateText(body, 120 - keyword.length - separator.length - ctaJoined.length);
      result += ctaJoined;
    } else {
      // result already short, just add CTA
      result += ctaJoined;
    }

    // Final check: sollte zwischen 120–160 liegen
    if (result.length > 160) {
      result = truncateText(result, 157) + '…';
    }
    return result;
  }

  switch (collection) {
    // ─── CAMPING ───────────────────────────────────────────
    case 'camping': {
      // Beschreibung aus CMS extrahieren (HTML strip + intelligenter Satz)
      let body = extractDescription(entry.beschreibung);
      if (!body) {
        body = `Campingplatz in ${ort || 'Tirol'} mit Natur pur, Stellplätzen und Bergpanorama`;
      }
      return build(name, body);
    }

    // ─── UNTERKÜNFTE ───────────────────────────────────────
    case 'unterkuenfte': {
      const typ = opts.typLabel || entry.typ || 'Unterkunft';
      let body = extractDescription(entry.beschreibung);
      if (!body) {
        const sterne = entry.sterne ? `${entry.sterne}-Stern ` : '';
        body = `${sterne}${typ} in ${ort || 'Tirol'} – Komfort & Urlaubsgefühl in den Alpen`;
      }
      return build(name, body);
    }

    // ─── REGIONEN ──────────────────────────────────────────
    case 'regionen': {
      let body = entry.kurzbeschreibung || extractDescription(entry.beschreibung);
      if (body && body.length < 80) {
        body += ` – ${isDE ? 'Wanderwege, Skigebiete & Ausflugsziele' : 'Hiking trails, ski resorts & attractions'}`;
      }
      return build(name, body);
    }

    // ─── ORTE ──────────────────────────────────────────────
    case 'orte': {
      let body = entry.kurzbeschreibung || '';
      if (body && body.length < 60 && entry.region) {
        body += ` – Ausflugsziel in ${entry.region}`;
      }
      if (!body) {
        body = `${isDE ? 'Urlaubsort in Tirol mit Bergpanorama & Naturerlebnissen' : 'Town in Tyrol surrounded by mountains'}`;
      }
      return build(name, body);
    }

    // ─── GASTRO ────────────────────────────────────────────
    case 'gastro': {
      let body = entry.kurzbeschreibung || extractDescription(entry.beschreibung);
      if (!body) {
        const kat = entry.kategorie || 'Kulinarik';
        body = `${isDE ? 'Einkehren & genießen' : 'Dine & enjoy'} in ${ort || 'Tirol'} – ${kat}`;
      }
      return build(name, body);
    }

    // ─── SEHENSWÜRDIGKEITEN ────────────────────────────────
    case 'sehenswuerdigkeiten': {
      let body = entry.kurzbeschreibung || extractDescription(entry.beschreibung);
      if (!body) {
        body = `${isDE ? 'Sehenswürdigkeit' : 'Sight'} in ${ort || 'Tirol'} – ${entry.kategorie || ''}`;
      }
      return build(name, body);
    }

    // ─── ERLEBNISSE ────────────────────────────────────────
    case 'erlebnisse': {
      const kategorieLabel = {
        wandern: 'Wandern', ski: 'Ski & Snowboard', bike: 'Bike & Mountainbike',
        wellness: 'Wellness & Erholung', familie: 'Familie & Kinder',
        kulinarik: 'Kulinarik', kultur: 'Kultur', abenteuer: 'Abenteuer',
      };
      let body = entry.beschreibung || '';
      if (!body) {
        const kat = kategorieLabel[entry.kategorie] || 'Erlebnis';
        body = `${kat} in ${ort || 'Tirol'} – ${isDE ? 'ein unvergessliches Abenteuer' : 'an unforgettable adventure'}`;
      }
      return build(name, body);
    }

    // ─── EVENTS ────────────────────────────────────────────
    case 'events': {
      let body = entry.kurzbeschreibung || entry.beschreibung || '';
      if (!body) {
        body = `Event in ${ort || 'Tirol'} – ${entry.kategorie || 'Veranstaltung'}`;
      }
      return build(name, body);
    }

    // ─── MAGAZIN ───────────────────────────────────────────
    case 'magazin': {
      let body = entry.teaser || '';
      if (!body) {
        body = `${isDE ? 'Spannender Magazinbeitrag' : 'Interesting magazine article'} über ${name}`;
      }
      return build(name, body);
    }

    // ─── BEZIRKE ───────────────────────────────────────────
    case 'bezirke': {
      let body = entry.beschreibung || '';
      if (!body) {
        body = `${isDE ? 'Alle Gemeinden, Regionen & Ausflugsziele' : 'Municipalities, regions & attractions'}`;
      }
      return build(name, body);
    }

    // ─── DEFAULT ───────────────────────────────────────────
    default: {
      const body = entry.kurzbeschreibung || entry.beschreibung || entry.teaser || '';
      return build(name, body);
    }
  }
}
