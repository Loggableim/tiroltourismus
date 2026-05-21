#!/usr/bin/env python3
"""
Phase 4 Generator: Erstellt locale-aware Kategorie-Seiten unter [locale]/ 
Alle 22 Dateien werden automatisch generiert.
"""
import os, shutil

BASE = "F:/tiroltourismus"
PAGES = f"{BASE}/src/pages"
LOCALE = f"{PAGES}/[locale]"

# ── LANGUAGES_READY import line ──
IMPORT_LANGS = 'import { LANGUAGES_READY } from \'../../lib/languages.js\';'
IMPORT_LANGS3 = 'import { LANGUAGES_READY } from \'../../../lib/languages.js\';'

# ── DIRECT GENERATION ──
# (Templates above are unused, generation happens inline below)
# ──

os.makedirs(f"{LOCALE}/gastro", exist_ok=True)
os.makedirs(f"{LOCALE}/unterkuenfte", exist_ok=True)
os.makedirs(f"{LOCALE}/orte", exist_ok=True)
os.makedirs(f"{LOCALE}/camping", exist_ok=True)
os.makedirs(f"{LOCALE}/sehenswuerdigkeiten", exist_ok=True)
os.makedirs(f"{LOCALE}/magazin", exist_ok=True)
os.makedirs(f"{LOCALE}/magazin/tag", exist_ok=True)
os.makedirs(f"{LOCALE}/magazin/tags", exist_ok=True)
os.makedirs(f"{LOCALE}/erlebnisse", exist_ok=True)
os.makedirs(f"{LOCALE}/events", exist_ok=True)
os.makedirs(f"{LOCALE}/events/eintragen", exist_ok=True)
os.makedirs(f"{LOCALE}/bezirke", exist_ok=True)

files = {}

# ── GASTRO ──
files[f"{LOCALE}/gastro/index.astro"] = f"""---
import BaseLayout from '../../layouts/BaseLayout.astro';
import Hero from '../../components/Hero.astro';
import Breadcrumbs from '../../components/Breadcrumbs.astro';
import SectionHeader from '../../components/SectionHeader.astro';
import GastroCard from '../../components/GastroCard.astro';
import SectionMap from '../../sections/SectionMap.astro';
import {{ readCollection, isPublished }} from '../../lib/content.js';
import {{ LANGUAGES_READY }} from '../../lib/languages.js';

export async function getStaticPaths() {{
  return LANGUAGES_READY.map(locale => ({{ params: {{ locale }} }}));
}}

const {{ locale }} = Astro.params;
const gastro = readCollection('gastro', locale).filter(g => isPublished(g.entry));
const gastroMitCoords = gastro.filter(g => g.entry.koordinaten?.lat && g.entry.koordinaten?.lng);
---

<BaseLayout title="Gastro in Tirol" description="Entdecke die kulinarische Vielfalt Tirols – von urigen Hütten bis zu Sternerestaurants." locale={{locale}}>
  <main>
    <div class="container">
      <Breadcrumbs items="{{[{{ label: 'Gastro' }}]}}" />
    </div>
    <Hero title="Gastro" subtitle="Entdecke die kulinarische Vielfalt Tirols." emoji="🍽️" size="md">
      <div slot="actions" class="hero-actions">
        <a href="#gastro-grid" class="btn btn-pink">Gastro entdecken →</a>
        <span class="hero-urgency">✨ {{gastro.length}} Adressen</span>
      </div>
    </Hero>
    <SectionHeader title="Gastro" sub="" />
    <div class="card-grid" id="gastro-grid">
      {{gastro.map(g => (<GastroCard {{...g.entry}} slug={{g.slug}} />))}}
    </div>
    {{gastroMitCoords.length > 0 && (
      <SectionMap markers="{{gastroMitCoords.map(g => ({{ lat: g.entry.koordinaten.lat, lng: g.entry.koordinaten.lng, label: g.entry.name, emoji: g.entry.emoji || '🍽️', href: '/' + (locale !== 'de' ? locale + '/' : '') + 'gastro/' + g.slug + '/' }}))}}" />
    )}}
  </main>
</BaseLayout>"""

files[f"{LOCALE}/gastro/[slug].astro"] = f"""---
import DetailPage from '../../sections/DetailPage.astro';
import {{ readEntry, readCollection, isPublished, findNearby, findByTag, autoLinkContent }} from '../../lib/content.js';
import {{ generateMetaDescription }} from '../../lib/seo.js';
import {{ LANGUAGES_READY }} from '../../lib/languages.js';

export async function getStaticPaths() {{
  const paths = [];
  for (const locale of LANGUAGES_READY) {{
    const all = readCollection('gastro', locale).filter(g => isPublished(g.entry));
    for (const g of all) paths.push({{ params: {{ locale, slug: g.slug }} }});
  }}
  return paths;
}}

const {{ locale, slug }} = Astro.params;
const entry = readEntry('gastro', slug, locale);
if (!entry) return Astro.redirect('/gastro/');

const emoji = entry.emoji || '🍽️';
const subtitle = entry.ort ? `${{entry.ort}}${{entry.kategorie ? ` · ${{entry.kategorie}}` : ''}}` : undefined;
const CATEGORY_EMOJI = {{ sehenswuerdigkeiten:'🏛️', gastro:'🍽️', unterkuenfte:'🏨', camping:'🏕️', erlebnisse:'🎯', orte:'🏘️', events:'🎪', regionen:'🏔️' }};
const nearbyEntries = entry.koordinaten ? findNearby(entry, 'gastro', locale, 8) : [];
const mapMarkers = [];
if (entry.koordinaten) {{
  mapMarkers.push({{ lat: entry.koordinaten.lat, lng: entry.koordinaten.lng, label: entry.name, emoji: emoji }});
}}
nearbyEntries.forEach(n => {{
  if (!n.entry.koordinaten) return;
  mapMarkers.push({{ lat: n.entry.koordinaten.lat, lng: n.entry.koordinaten.lng, label: n.entry.name || n.entry.titel, emoji: CATEGORY_EMOJI[n.collection] || '📍', href: '/' + n.collection + '/' + n.slug + '/' }});
}});
const title = entry.name || slug;
const metaDesc = generateMetaDescription(entry, 'de');
---

<DetailPage title={{title}} description={{metaDesc}} locale={{locale}}
  breadcrumbs="{{[{{ label: 'Gastro', href: '/gastro/' }}, {{ label: title }}]}}"
  sections="{{[
    {{ type: 'hero', title, subtitle, emoji, image: entry.hero_bild || (entry.bilder?.[0]?.url) }},
    {{ type: 'facts', items: [
      entry.ort && {{ icon: '📍', label: 'Ort', value: entry.ort }},
      entry.kategorie && {{ icon: '🏷️', label: 'Kategorie', value: entry.kategorie }},
      entry.preis && {{ icon: '💰', label: 'Preis', value: entry.preis }},
      entry.telefon && {{ icon: '📞', label: 'Telefon', value: entry.telefon }},
    ].filter(Boolean) }},
    {{ type: 'description', content: entry.kurzbeschreibung }},
    entry.koordinaten && {{ type: 'map', markers: mapMarkers }},
    nearbyEntries.length > 0 && {{ type: 'related', items: nearbyEntries.slice(0,4) }},
  ].filter(Boolean)}}"
/>"""

print("✅ gastro")

# ── UNTERKUENFTE ──
files[f"{LOCALE}/unterkuenfte/index.astro"] = f"""---
import BaseLayout from '../../layouts/BaseLayout.astro';
import SectionHeader from '../../components/SectionHeader.astro';
import SectionMap from '../../sections/SectionMap.astro';
import AccommodationCard from '../../components/AccommodationCard.astro';
import {{ readCollection, isPublished }} from '../../lib/content.js';
import {{ LANGUAGES_READY }} from '../../lib/languages.js';

export async function getStaticPaths() {{
  return LANGUAGES_READY.map(locale => ({{ params: {{ locale }} }}));
}}

const {{ locale }} = Astro.params;
const unterkuenfte = readCollection('unterkuenfte', locale).filter(u => isPublished(u.entry));
const mitCoords = unterkuenfte.filter(u => u.entry.koordinaten?.lat && u.entry.koordinaten?.lng);
const sorted = [...unterkuenfte].sort((a,b) => ({{gold:0,silver:1,basic:2}}[a.entry.tier||'basic']||2) - ({{gold:0,silver:1,basic:2}}[b.entry.tier||'basic']||2));
---

<BaseLayout title="Unterkünfte in Tirol" description="Finde Dein Zuhause in Tirol. Hotels, Ferienwohnungen & Bauernhöfe." locale={{locale}}>
  <main>
    <div class="container">
      <SectionHeader title="Unterkünfte" sub="${{unterkuenfte.length}} Unterkünfte" />
    </div>
    <div class="card-grid">
      {{sorted.map(u => (<AccommodationCard {{...u.entry}} slug={{u.slug}} />))}}
    </div>
    {{mitCoords.length > 0 && (<SectionMap markers="{{mitCoords.map(u => ({{lat:u.entry.koordinaten.lat,lng:u.entry.koordinaten.lng,label:u.entry.name,emoji:'🏨',href:'/'+(locale!=='de'?locale+'/':'')+'unterkuenfte/'+u.slug+'/'}}))}}" />)}}
  </main>
</BaseLayout>"""

files[f"{LOCALE}/unterkuenfte/[slug].astro"] = f"""---
import DetailPage from '../../sections/DetailPage.astro';
import PremiumBadge from '../../components/PremiumBadge.astro';
import PaywallOverlay from '../../components/PaywallOverlay.astro';
import {{ readEntry, readCollection, isPublished, findNearby, findByTag, autoLinkContent }} from '../../lib/content.js';
import {{ generateMetaDescription }} from '../../lib/seo.js';
import {{ LANGUAGES_READY }} from '../../lib/languages.js';

export async function getStaticPaths() {{
  const paths = [];
  for (const locale of LANGUAGES_READY) {{
    const all = readCollection('unterkuenfte', locale).filter(u => isPublished(u.entry));
    for (const u of all) paths.push({{ params: {{ locale, slug: u.slug }} }});
  }}
  return paths;
}}

const {{ locale, slug }} = Astro.params;
const entry = readEntry('unterkuenfte', slug, locale);
if (!entry) return Astro.redirect('/unterkuenfte/');

const typLabel = {{ hotel:'Hotel', ferienwohnung:'Ferienwohnung', bauernhof:'Bauernhof', jugendherberge:'Jugendherberge', camping:'Camping' }};
const tier = entry.tier || 'basic';
const CATEGORY_EMOJI = {{ sehenswuerdigkeiten:'🏛️', gastro:'🍽️', unterkuenfte:'🏨', camping:'🏕️', erlebnisse:'🎯', orte:'🏘️', events:'🎪', regionen:'🏔️' }};
const nearbyEntries = entry.koordinaten ? findNearby(entry, 'unterkuenfte', locale, 8) : [];
const mapMarkers = [];
if (entry.koordinaten) {{
  mapMarkers.push({{ lat: entry.koordinaten.lat, lng: entry.koordinaten.lng, label: entry.name, emoji: '🏨' }});
}}
nearbyEntries.forEach(n => {{
  if (!n.entry.koordinaten) return;
  mapMarkers.push({{ lat: n.entry.koordinaten.lat, lng: n.entry.koordinaten.lng, label: n.entry.name || n.entry.titel, emoji: CATEGORY_EMOJI[n.collection] || '📍', href: '/' + n.collection + '/' + n.slug + '/' }});
}});
const title = entry.name || slug;
const metaDesc = generateMetaDescription(entry, 'de');
---

<DetailPage title={{title}} description={{metaDesc}} locale={{locale}}
  breadcrumbs="{{[{{ label: 'Unterkünfte', href: '/unterkuenfte/' }}, {{ label: title }}]}}"
  sections="{{[
    {{ type: 'hero', title, subtitle: entry.ort || entry.region, emoji: '🏨', image: entry.hero_bild || (entry.bilder?.[0]?.url) }},
    {{ type: 'facts', items: [
      entry.ort && {{ icon: '📍', label: 'Ort', value: entry.ort }},
      entry.typ && {{ icon: '🏷️', label: 'Typ', value: typLabel[entry.typ] || entry.typ }},
      entry.preis_ab && {{ icon: '💰', label: 'Ab', value: '€' + entry.preis_ab }},
      tier !== 'basic' && {{ icon: '⭐', label: 'Status', value: tier }},
    ].filter(Boolean) }},
    {{ type: 'description', content: entry.kurzbeschreibung }},
    entry.koordinaten && {{ type: 'map', markers: mapMarkers }},
    nearbyEntries.length > 0 && {{ type: 'related', items: nearbyEntries.slice(0,4) }},
  ].filter(Boolean)}}"
/>"""

print("✅ unterkuenfte")

# ── ORTE ──
files[f"{LOCALE}/orte/index.astro"] = f"""---
import BaseLayout from '../../layouts/BaseLayout.astro';
import Hero from '../../components/Hero.astro';
import Breadcrumbs from '../../components/Breadcrumbs.astro';
import SectionHeader from '../../components/SectionHeader.astro';
import SectionMap from '../../sections/SectionMap.astro';
import OrtCard from '../../components/OrtCard.astro';
import {{ readCollection, isPublished }} from '../../lib/content.js';
import {{ LANGUAGES_READY }} from '../../lib/languages.js';

export async function getStaticPaths() {{
  return LANGUAGES_READY.map(locale => ({{ params: {{ locale }} }}));
}}

const {{ locale }} = Astro.params;
const orte = readCollection('orte', locale).filter(o => isPublished(o.entry));
const mitKarte = orte.filter(o => o.entry.koordinaten?.lat && o.entry.koordinaten?.lng);
---

<BaseLayout title="Orte in Tirol" description="Entdecke die schönsten Orte und Dörfer in Tirol." locale={{locale}}>
  <main>
    <div class="container"><Breadcrumbs items="{{[{{ label: 'Orte' }}]}}" /></div>
    <Hero title="Orte" subtitle="Die schönsten Dörfer und Städte Tirols." emoji="🏘️" size="md" />
    <div class="card-grid">
      {{orte.map(o => (<OrtCard {{...o.entry}} slug={{o.slug}} />))}}
    </div>
    {{mitKarte.length > 0 && (<SectionMap markers="{{mitKarte.map(o => ({{lat:o.entry.koordinaten.lat,lng:o.entry.koordinaten.lng,label:o.entry.name,emoji:o.entry.emoji||'🏘️',href:'/'+(locale!=='de'?locale+'/':'')+'orte/'+o.slug+'/'}}))}}" />)}}
  </main>
</BaseLayout>"""

files[f"{LOCALE}/orte/[slug].astro"] = f"""---
import DetailPage from '../../sections/DetailPage.astro';
import {{ readEntry, readCollection, isPublished, findNearby, findByTag }} from '../../lib/content.js';
import {{ generateMetaDescription }} from '../../lib/seo.js';
import {{ LANGUAGES_READY }} from '../../lib/languages.js';

export async function getStaticPaths() {{
  const paths = [];
  for (const locale of LANGUAGES_READY) {{
    const all = readCollection('orte', locale).filter(o => isPublished(o.entry));
    for (const o of all) paths.push({{ params: {{ locale, slug: o.slug }} }});
  }}
  return paths;
}}

const {{ locale, slug }} = Astro.params;
const entry = readEntry('orte', slug, locale);
if (!entry) return Astro.redirect('/orte/');

const {{ name, kurzbeschreibung, emoji, farbe, hoehe, einwohner, tags }} = entry;
const CATEGORY_EMOJI = {{ sehenswuerdigkeiten:'🏛️', gastro:'🍽️', unterkuenfte:'🏨', camping:'🏕️', erlebnisse:'🎯', orte:'🏘️', events:'🎪', regionen:'🏔️' }};
const nearbyEntries = entry.koordinaten ? findNearby(entry, 'orte', locale, 8) : [];
const mapMarkers = [];
if (entry.koordinaten) {{
  mapMarkers.push({{ lat: entry.koordinaten.lat, lng: entry.koordinaten.lng, label: name, emoji: emoji || '🏘️' }});
}}
nearbyEntries.forEach(n => {{
  if (!n.entry.koordinaten) return;
  mapMarkers.push({{ lat: n.entry.koordinaten.lat, lng: n.entry.koordinaten.lng, label: n.entry.name || n.entry.titel, emoji: CATEGORY_EMOJI[n.collection] || '📍', href: '/' + n.collection + '/' + n.slug + '/', category: n.collection }});
}});
const title = name || slug;
const metaDesc = generateMetaDescription(entry, 'de');
---

<DetailPage title={{title}} description={{metaDesc}} locale={{locale}}
  breadcrumbs="{{[{{ label: 'Orte', href: '/orte/' }}, {{ label: title }}]}}"
  sections="{{[
    {{ type: 'hero', title, subtitle: entry.region, emoji: emoji || '🏘️', image: entry.hero_bild || (entry.bilder?.[0]?.url), color: farbe }},
    {{ type: 'facts', items: [
      hoehe && {{ icon: '📏', label: 'Höhe', value: hoehe }},
      einwohner && {{ icon: '👥', label: 'Einwohner', value: einwohner }},
    ].filter(Boolean) }},
    {{ type: 'description', content: kurzbeschreibung }},
    entry.koordinaten && {{ type: 'map', markers: mapMarkers }},
    nearbyEntries.length > 0 && {{ type: 'related', items: nearbyEntries.slice(0,4) }},
  ].filter(Boolean)}}"
/>"""

print("✅ orte")

# ── CAMPING ──
files[f"{LOCALE}/camping/index.astro"] = f"""---
import BaseLayout from '../../layouts/BaseLayout.astro';
import SectionHeader from '../../components/SectionHeader.astro';
import SectionMap from '../../sections/SectionMap.astro';
import CampingCard from '../../components/CampingCard.astro';
import {{ readCollection, isPublished }} from '../../lib/content.js';
import {{ LANGUAGES_READY }} from '../../lib/languages.js';

export async function getStaticPaths() {{
  return LANGUAGES_READY.map(locale => ({{ params: {{ locale }} }}));
}}

const {{ locale }} = Astro.params;
const camping = readCollection('camping', locale).filter(c => isPublished(c.entry));
const mitCoords = camping.filter(c => c.entry.koordinaten?.lat && c.entry.koordinaten?.lng);
const byRegion = {{}};
for (const c of camping) {{
  const r = c.entry.region || 'sonstige';
  if (!byRegion[r]) byRegion[r] = [];
  byRegion[r].push(c);
}}
const regionNames = {{ ausserfern:'Außerfern', achensee:'Achensee', arlberg:'Arlberg', imst:'Imst', innsbruck:'Innsbruck', kitzbuehel:'Kitzbühel', kufstein:'Kufstein', landeck:'Landeck', osttirol:'Osttirol', schwaz:'Schwaz', oetztal:'Ötztal', stubaital:'Stubaital', zillertal:'Zillertal', sonstige:'Sonstige' }};
---

<BaseLayout title="Campingplätze in Tirol" description="Finde die schönsten Campingplätze in Tirol." locale={{locale}}>
  <main>
    <div class="container"><SectionHeader title="Campingplätze" sub="${{camping.length}} Plätze" /></div>
    {{Object.entries(byRegion).map(([region, items]) => (
      <div class="region-group">
        <h2 class="region-title">{{regionNames[region] || region}}</h2>
        <div class="card-grid">
          {{items.map(c => (<CampingCard {{...c.entry}} slug={{c.slug}} />))}}
        </div>
      </div>
    ))}}
    {{mitCoords.length > 0 && (<SectionMap markers="{{mitCoords.map(c => ({{lat:c.entry.koordinaten.lat,lng:c.entry.koordinaten.lng,label:c.entry.name,emoji:'🏕️',href:'/'+(locale!=='de'?locale+'/':'')+'camping/'+c.slug+'/'}}))}}" />)}}
  </main>
</BaseLayout>"""

files[f"{LOCALE}/camping/[slug].astro"] = f"""---
import DetailPage from '../../sections/DetailPage.astro';
import PremiumBadge from '../../components/PremiumBadge.astro';
import PaywallOverlay from '../../components/PaywallOverlay.astro';
import {{ readEntry, readCollection, isPublished, findNearby, findByTag, autoLinkContent }} from '../../lib/content.js';
import {{ generateMetaDescription }} from '../../lib/seo.js';
import {{ LANGUAGES_READY }} from '../../lib/languages.js';

export async function getStaticPaths() {{
  const paths = [];
  for (const locale of LANGUAGES_READY) {{
    const all = readCollection('camping', locale).filter(c => isPublished(c.entry));
    for (const c of all) paths.push({{ params: {{ locale, slug: c.slug }} }});
  }}
  return paths;
}}

const {{ locale, slug }} = Astro.params;
const entry = readEntry('camping', slug, locale);
if (!entry) return Astro.redirect('/camping/');

const tier = entry.tier || 'basic';
const ausstattungLabels = {{ stromanschluss:'Stromanschluss', wasseranschluss:'Wasseranschluss', sanitäranlagen:'Sanitäranlagen', entsorgung:'Entsorgung', restaurant:'Restaurant', kinder:'Kinderspielplatz', haustiere:'Haustiere', wifi:'WLAN', barrierearm:'Barrierearm' }};
const CATEGORY_EMOJI = {{ sehenswuerdigkeiten:'🏛️', gastro:'🍽️', unterkuenfte:'🏨', camping:'🏕️', erlebnisse:'🎯', orte:'🏘️', events:'🎪', regionen:'🏔️' }};
const nearbyEntries = entry.koordinaten ? findNearby(entry, 'camping', locale, 8) : [];
const mapMarkers = [];
if (entry.koordinaten) {{
  mapMarkers.push({{ lat: entry.koordinaten.lat, lng: entry.koordinaten.lng, label: entry.name, emoji: '🏕️' }});
}}
nearbyEntries.forEach(n => {{
  if (!n.entry.koordinaten) return;
  mapMarkers.push({{ lat: n.entry.koordinaten.lat, lng: n.entry.koordinaten.lng, label: n.entry.name || n.entry.titel, emoji: CATEGORY_EMOJI[n.collection] || '📍', href: '/' + n.collection + '/' + n.slug + '/' }});
}});
const title = entry.name || slug;
const metaDesc = generateMetaDescription(entry, 'de');
---

<DetailPage title={{title}} description={{metaDesc}} locale={{locale}}
  breadcrumbs="{{[{{ label: 'Camping', href: '/camping/' }}, {{ label: title }}]}}"
  sections="{{[
    {{ type: 'hero', title, subtitle: entry.ort || entry.region, emoji: '🏕️', image: entry.hero_bild || (entry.bilder?.[0]?.url) }},
    {{ type: 'facts', items: [
      entry.ort && {{ icon: '📍', label: 'Ort', value: entry.ort }},
      entry.region && {{ icon: '🗺️', label: 'Region', value: entry.region }},
      entry.preis_ab && {{ icon: '💰', label: 'Ab', value: '€' + entry.preis_ab }},
      entry.ausstattung?.filter?.(a => ['stromanschluss','wasseranschluss','sanitäranlagen'].includes(a))?.length > 0 && {{ icon: '🔌', label: 'Ausstattung', value: entry.ausstattung.filter(a => ['stromanschluss','wasseranschluss','sanitäranlagen'].includes(a)).map(a => ausstattungLabels[a]).join(', ') }},
    ].filter(Boolean) }},
    {{ type: 'description', content: entry.kurzbeschreibung }},
    entry.koordinaten && {{ type: 'map', markers: mapMarkers }},
    nearbyEntries.length > 0 && {{ type: 'related', items: nearbyEntries.slice(0,4) }},
  ].filter(Boolean)}}"
/>"""

print("✅ camping")

# ── SEHENSWUERDIGKEITEN ──
files[f"{LOCALE}/sehenswuerdigkeiten/index.astro"] = f"""---
import BaseLayout from '../../layouts/BaseLayout.astro';
import Hero from '../../components/Hero.astro';
import Breadcrumbs from '../../components/Breadcrumbs.astro';
import SectionHeader from '../../components/SectionHeader.astro';
import SectionMap from '../../sections/SectionMap.astro';
import SightCard from '../../components/SightCard.astro';
import {{ readCollection, isPublished }} from '../../lib/content.js';
import {{ LANGUAGES_READY }} from '../../lib/languages.js';

export async function getStaticPaths() {{
  return LANGUAGES_READY.map(locale => ({{ params: {{ locale }} }}));
}}

const {{ locale }} = Astro.params;
const sights = readCollection('sehenswuerdigkeiten', locale).filter(s => isPublished(s.entry));
const kategorieLabel = {{ natur:'🌿 Natur', kultur:'🎭 Kultur', aussicht:'🏔️ Aussicht', sport:'⚡ Sport', museum:'🏛️ Museum', kirche:'⛪ Kirche', burg:'🏰 Burg', wanderung:'🥾 Wanderung' }};
const kategorien = [...new Set(sights.map(s => s.entry.kategorie).filter(Boolean))];
---

<BaseLayout title="Sehenswürdigkeiten in Tirol" description="Entdecke die schönsten Sehenswürdigkeiten in Tirol." locale={{locale}}>
  <main>
    <Breadcrumbs items="{{[{{ label: 'Sehenswürdigkeiten' }}]}}" />
    <Hero title="Sehenswürdigkeiten" subtitle="Entdecke die schönsten Orte und Highlights in Tirol." emoji="🏛️" size="md">
      <div slot="actions" class="hero-actions">
        <a href="#sight-grid" class="btn btn-pink">Highlights entdecken →</a>
        <span class="hero-urgency">✨ {{sights.length}} Sehenswürdigkeiten</span>
      </div>
    </Hero>
    <div class="card-grid" id="sight-grid">
      {{sights.map(s => (<SightCard {{...s.entry}} slug={{s.slug}} />))}}
    </div>
  </main>
</BaseLayout>"""

files[f"{LOCALE}/sehenswuerdigkeiten/[slug].astro"] = f"""---
import DetailPage from '../../sections/DetailPage.astro';
import {{ readEntry, readCollection, isPublished, findNearby, findByTag, autoLinkContent }} from '../../lib/content.js';
import {{ generateMetaDescription }} from '../../lib/seo.js';
import {{ LANGUAGES_READY }} from '../../lib/languages.js';

export async function getStaticPaths() {{
  const paths = [];
  for (const locale of LANGUAGES_READY) {{
    const all = readCollection('sehenswuerdigkeiten', locale).filter(s => isPublished(s.entry));
    for (const s of all) paths.push({{ params: {{ locale, slug: s.slug }} }});
  }}
  return paths;
}}

const {{ locale, slug }} = Astro.params;
const entry = readEntry('sehenswuerdigkeiten', slug, locale);
if (!entry) return Astro.redirect('/sehenswuerdigkeiten/');

const catLabel = {{ natur:'Natur', kultur:'Kultur', aussicht:'Aussicht', sport:'Sport', museum:'Museum', kirche:'Kirche', burg:'Burg', wanderung:'Wanderung' }};
const catEmoji = {{ natur:'🌿', kultur:'🎭', aussicht:'🏔️', sport:'⚡', museum:'🏛️', kirche:'⛪', burg:'🏰', wanderung:'🥾' }};
const catStr = entry.kategorie ? `${{catEmoji[entry.kategorie] || ''}} ${{catLabel[entry.kategorie] || entry.kategorie}}` : undefined;
const CATEGORY_EMOJI = {{ sehenswuerdigkeiten:'🏛️', gastro:'🍽️', unterkuenfte:'🏨', camping:'🏕️', erlebnisse:'🎯', orte:'🏘️', events:'🎪', regionen:'🏔️' }};
const nearbyEntries = entry.koordinaten ? findNearby(entry, 'sehenswuerdigkeiten', locale, 8) : [];
const mapMarkers = [];
if (entry.koordinaten) {{
  mapMarkers.push({{ lat: entry.koordinaten.lat, lng: entry.koordinaten.lng, label: entry.name || entry.titel, emoji: '🏛️' }});
}}
nearbyEntries.forEach(n => {{
  if (!n.entry.koordinaten) return;
  mapMarkers.push({{ lat: n.entry.koordinaten.lat, lng: n.entry.koordinaten.lng, label: n.entry.name || n.entry.titel, emoji: CATEGORY_EMOJI[n.collection] || '📍', href: '/' + n.collection + '/' + n.slug + '/' }});
}});
const title = entry.name || entry.titel || slug;
const metaDesc = generateMetaDescription(entry, 'de');
---

<DetailPage title={{title}} description={{metaDesc}} locale={{locale}}
  breadcrumbs="{{[{{ label: 'Sehenswürdigkeiten', href: '/sehenswuerdigkeiten/' }}, {{ label: title }}]}}"
  sections="{{[
    {{ type: 'hero', title, subtitle: catStr, emoji: catEmoji[entry.kategorie] || '🏛️', image: entry.hero_bild || (entry.bilder?.[0]?.url) }},
    {{ type: 'facts', items: [
      entry.ort && {{ icon: '📍', label: 'Ort', value: entry.ort }},
      entry.kategorie && {{ icon: '🏷️', label: 'Kategorie', value: catLabel[entry.kategorie] || entry.kategorie }},
      entry.hoehe && {{ icon: '📏', label: 'Höhe', value: entry.hoehe }},
    ].filter(Boolean) }},
    {{ type: 'description', content: entry.kurzbeschreibung }},
    entry.koordinaten && {{ type: 'map', markers: mapMarkers }},
    nearbyEntries.length > 0 && {{ type: 'related', items: nearbyEntries.slice(0,4) }},
  ].filter(Boolean)}}"
/>"""

print("✅ sehenswuerdigkeiten")

# ── MAGAZIN ──
files[f"{LOCALE}/magazin/index.astro"] = f"""---
import BaseLayout from '../../layouts/BaseLayout.astro';
import Hero from '../../components/Hero.astro';
import Breadcrumbs from '../../components/Breadcrumbs.astro';
import SectionHeader from '../../components/SectionHeader.astro';
import ArticleCard from '../../components/ArticleCard.astro';
import {{ readCollection, isPublished }} from '../../lib/content.js';
import {{ LANGUAGES_READY }} from '../../lib/languages.js';

export async function getStaticPaths() {{
  return LANGUAGES_READY.map(locale => ({{ params: {{ locale }} }}));
}}

const {{ locale }} = Astro.params;
const articles = readCollection('magazin', locale).filter(a => isPublished(a.entry)).sort((a,b) => (b.entry.datum||'').localeCompare(a.entry.datum||''));
const catEmoji = {{ allgemein:'📰', tipps:'💡', reiseberichte:'✈️', interview:'🎙️', hintergrund:'🔍' }};
function formatDate(d) {{
  if (!d) return '';
  try {{ return new Date(d + 'T00:00:00').toLocaleDateString('de-DE', {{ year:'numeric', month:'long', day:'numeric' }}); }} catch {{ return d; }}
}}
---

<BaseLayout title="Magazin – Tirol Tourismus" description="Aktuelle Geschichten, Tipps und Inspiration für deinen Tirol-Urlaub." locale={{locale}}>
  <main>
    <div class="container"><Breadcrumbs items="{{[{{ label: 'Magazin' }}]}}" /></div>
    <Hero title="Magazin" subtitle="Geschichten aus den Bergen" emoji="📖" size="md" />
    <div class="article-grid">
      {{articles.map(a => (<ArticleCard {{...a.entry}} slug={{a.slug}} />))}}
    </div>
  </main>
</BaseLayout>"""

files[f"{LOCALE}/magazin/[slug].astro"] = f"""---
import DetailPage from '../../../sections/DetailPage.astro';
import {{ readEntry, readCollection, isPublished, findByTag }} from '../../../lib/content.js';
import ArticleCard from '../../../components/ArticleCard.astro';
import {{ generateMetaDescription }} from '../../../lib/seo.js';
import {{ LANGUAGES_READY }} from '../../../lib/languages.js';

export async function getStaticPaths() {{
  const paths = [];
  for (const locale of LANGUAGES_READY) {{
    const all = readCollection('magazin', locale).filter(a => isPublished(a.entry));
    for (const a of all) paths.push({{ params: {{ locale, slug: a.slug }} }});
  }}
  return paths;
}}

const {{ locale, slug }} = Astro.params;
const entry = readEntry('magazin', slug, locale);
if (!entry) return Astro.redirect('/magazin/');

function formatDate(d) {{
  if (!d) return '';
  try {{ return new Date(d + 'T00:00:00').toLocaleDateString('de-DE', {{ year:'numeric', month:'long', day:'numeric' }}); }} catch {{ return d; }}
}}
const related = (entry.tags?.length > 0) ? findByTag(entry.tags[0], locale).filter(r => r.slug !== slug).slice(0,3) : [];
const title = entry.titel || slug;
const metaDesc = generateMetaDescription(entry, 'de');
const catEmoji = {{ allgemein:'📰', tipps:'💡', reiseberichte:'✈️', interview:'🎙️', hintergrund:'🔍' }};
---

<DetailPage title={{title}} description={{metaDesc}} locale={{locale}}
  isArticle={{true}}
  breadcrumbs="{{[{{ label: 'Magazin', href: '/magazin/' }}, {{ label: entry.kategorie || 'Artikel' }}]}}"
  sections="{{[
    entry.bilder?.[0] && {{ type: 'articleHero', title, image: entry.bilder[0].url, alt: entry.bilder[0].alt, date: formatDate(entry.datum), author: entry.autor, kategorie: entry.kategorie, emoji: catEmoji[entry.kategorie] || '📰' }},
    {{ type: 'articleContent', content: entry.inhalt }},
    {{ type: 'tags', items: entry.tags || [] }},
    related.length > 0 && {{ type: 'relatedGrid', items: related.map(r => ({{ collection: r.collection, slug: r.slug, entry: r.entry, score: r.score }})), title: 'Ähnliche Beiträge' }},
  ].filter(Boolean)}}"
/>"""

files[f"{LOCALE}/magazin/tag/[tag].astro"] = f"""---
import BaseLayout from '../../../layouts/BaseLayout.astro';
import Hero from '../../../components/Hero.astro';
import Breadcrumbs from '../../../components/Breadcrumbs.astro';
import SectionHeader from '../../../components/SectionHeader.astro';
import ArticleCard from '../../../components/ArticleCard.astro';
import {{ readCollection, isPublished, findByTag }} from '../../../lib/content.js';
import {{ LANGUAGES_READY }} from '../../../lib/languages.js';

export async function getStaticPaths() {{
  const paths = [];
  for (const locale of LANGUAGES_READY) {{
    const published = readCollection('magazin', locale).filter(a => isPublished(a.entry));
    const tags = new Set();
    for (const a of published) {{
      if (a.entry.tags) a.entry.tags.forEach(t => tags.add(t));
    }}
    for (const tag of tags) paths.push({{ params: {{ locale, tag }} }});
  }}
  return paths;
}}

const {{ locale, tag }} = Astro.params;
const articles = findByTag(tag, locale).filter(a => a.collection === 'magazin').sort((a,b) => ((b.entry.datum||'')).localeCompare(a.entry.datum||''));
---

<BaseLayout title="{{tag}} – Magazin" description="Alle Artikel zum Thema {{tag}}" locale={{locale}}>
  <main>
    <div class="container"><Breadcrumbs items="{{[{{ label: 'Magazin', href: '/magazin/' }}, {{ label: tag }}]}}" /></div>
    <Hero title="{{tag}}" subtitle="Artikel zum Thema" emoji="📖" size="sm" />
    <div class="article-grid">{{articles.map(a => (<ArticleCard {{...a.entry}} slug={{a.slug}} />))}}</div>
  </main>
</BaseLayout>"""

files[f"{LOCALE}/magazin/tags/index.astro"] = f"""---
import BaseLayout from '../../../layouts/BaseLayout.astro';
import Breadcrumbs from '../../../components/Breadcrumbs.astro';
import SectionHeader from '../../../components/SectionHeader.astro';
import {{ readCollection, isPublished }} from '../../../lib/content.js';
import {{ LANGUAGES_READY }} from '../../../lib/languages.js';

export async function getStaticPaths() {{
  return LANGUAGES_READY.map(locale => ({{ params: {{ locale }} }}));
}}

const {{ locale }} = Astro.params;
const articles = readCollection('magazin', locale).filter(a => isPublished(a.entry));
const tagMap = new Map();
for (const {{ entry }} of articles) {{
  if (entry.tags) for (const tag of entry.tags) tagMap.set(tag, (tagMap.get(tag)||0)+1);
}}
const sortedTags = [...tagMap.entries()].sort((a,b) => b[1]-a[1]);
---

<BaseLayout title="Alle Tags – Magazin" description="Alle Schlagworte des Tirol Magazins" locale={{locale}}>
  <main>
    <div class="container"><Breadcrumbs items="{{[{{ label: 'Magazin', href: '/magazin/' }}, {{ label: 'Tags' }}]}}" /></div>
    <SectionHeader title="Tags" sub="${{sortedTags.length}} Schlagworte" />
    <div class="tag-cloud">{{sortedTags.map(([tag, count]) => (<a href="{{'/'+(locale!=='de'?locale+'/':'')+'magazin/tag/'+tag}}/" class="tag-pill">{{tag}} ({{count}})</a>))}}</div>
  </main>
</BaseLayout>"""

files[f"{LOCALE}/magazin/faq.astro"] = f"""---
import BaseLayout from '../../../layouts/BaseLayout.astro';
import Breadcrumbs from '../../../components/Breadcrumbs.astro';
import SectionHeader from '../../../components/SectionHeader.astro';
import {{ LANGUAGES_READY }} from '../../../lib/languages.js';

export async function getStaticPaths() {{
  return LANGUAGES_READY.map(locale => ({{ params: {{ locale }} }}));
}}

const {{ locale }} = Astro.params;
const faqItems = [
  {{ q:'Wie komme ich am besten nach Tirol?', a:'Tirol ist hervorragend an das internationale Verkehrsnetz angebunden. Mit dem Auto über die Inntalautobahn A12 oder Brennerautobahn A13. Mit der Bahn via Innsbruck, Kufstein oder Landeck – der Railjet verbindet stündlich mit Wien, München und Zürich. Nächste Flughäfen: Innsbruck (INN), München (MUC) und Salzburg (SZG).' }},
  {{ q:'Gibt es ein günstiges Öffi-Ticket für Touristen?', a:'Ja, mit der Tiroler Oberland Card oder dem Klimaticket Tirol. Viele Gemeinden stellen eine Gästekarte aus – kostenlose Nutzung von Regionalbussen und Ermäßigungen auf Bergbahnen.' }},
  {{ q:'Wann ist die beste Reisezeit für Tirol?', a:'Sommer (Juni–September) für Wandern und Seen, Winter (Dezember–März) für Ski und Snowboard. Frühling und Herbst sind ruhiger, ideal für Wellness und Kultur.' }},
  {{ q:'Welche Regionen in Tirol sind am schönsten?', a:'Das Zillertal für Familien, Ötztal für Skifahrer, Stubaital für Wanderer, Kitzbühel für Luxus, Osttirol für Ruhe und Innsbruck für Kultur.' }},
  {{ q:'Kann man in den Tiroler Bergen gut wandern?', a:'Ja, Tirol hat über 24.500 km Wanderwege. Von leichten Almwanderungen bis zu anspruchsvollen Gipfeltouren – für jedes Level. Viele Hütten laden zur Einkehr ein.' }},
];
---

<BaseLayout title="Häufige Fragen – Tirol" description="Antworten auf die häufigsten Fragen zu Tirol" locale={{locale}}>
  <main>
    <div class="container"><Breadcrumbs items="{{[{{ label: 'FAQ' }}]}}" /></div>
    <SectionHeader title="FAQ" sub="Häufige Fragen zu Tirol" />
    <div class="faq-list">{{faqItems.map(item => (
      <details class="faq-item"><summary>{{item.q}}</summary><p>{{item.a}}</p></details>
    ))}}</div>
  </main>
</BaseLayout>"""

print("✅ magazin")

# ── ERLEBNISSE ──
files[f"{LOCALE}/erlebnisse/index.astro"] = f"""---
import BaseLayout from '../../layouts/BaseLayout.astro';
import Hero from '../../components/Hero.astro';
import Breadcrumbs from '../../components/Breadcrumbs.astro';
import SectionHeader from '../../components/SectionHeader.astro';
import SectionMap from '../../sections/SectionMap.astro';
import {{ readCollection, isPublished }} from '../../lib/content.js';
import {{ LANGUAGES_READY }} from '../../lib/languages.js';

export async function getStaticPaths() {{
  return LANGUAGES_READY.map(locale => ({{ params: {{ locale }} }}));
}}

const {{ locale }} = Astro.params;
const erlebnisse = readCollection('erlebnisse', locale).filter(e => isPublished(e.entry));
const kategorieMeta = {{ wandern:{{emoji:'🥾',color:'var(--green)'}}, ski:{{emoji:'⛷️',color:'var(--blue)'}}, bike:{{emoji:'🚵',color:'var(--orange)'}}, wellness:{{emoji:'♨️',color:'var(--pink)'}}, familie:{{emoji:'👨‍👩‍👧‍👦',color:'var(--yellow)'}}, kulinarik:{{emoji:'🍷',color:'var(--purple)'}}, kultur:{{emoji:'🎭',color:'var(--orange)'}}, abenteuer:{{emoji:'🧗',color:'var(--tirol-red)'}} }};
---

<BaseLayout title="Erlebnisse in Tirol" description="Entdecke die vielfältigen Erlebnisse in Tirol." locale={{locale}}>
  <main>
    <div class="container"><Breadcrumbs items="{{[{{ label: 'Erlebnisse' }}]}}" /></div>
    <Hero title="Erlebnisse" subtitle="Entdecke unvergessliche Momente in Tirol" emoji="🎯" size="md" />
    <div class="erlebnis-grid">{{erlebnisse.map(e => (
      <a href="{{'/'+(locale!=='de'?locale+'/':'')+'erlebnisse/'+e.slug+'/'}}" class="erl-card" style="border-left:4px solid {{kategorieMeta[e.entry.kategorie]?.color||'var(--pink)'}}">
        <div class="erl-emoji">{{kategorieMeta[e.entry.kategorie]?.emoji||'🏔️'}}</div>
        <div class="erl-info"><h3>{{e.entry.name}}</h3><p>{{e.entry.kurzbeschreibung?.slice(0,120)}}...</p></div>
      </a>
    ))}}</div>
  </main>
</BaseLayout>"""

files[f"{LOCALE}/erlebnisse/[slug].astro"] = f"""---
import DetailPage from '../../sections/DetailPage.astro';
import {{ readEntry, readCollection, isPublished, findNearby, findByTag, autoLinkContent }} from '../../lib/content.js';
import {{ generateMetaDescription }} from '../../lib/seo.js';
import {{ LANGUAGES_READY }} from '../../lib/languages.js';

export async function getStaticPaths() {{
  const paths = [];
  for (const locale of LANGUAGES_READY) {{
    const all = readCollection('erlebnisse', locale).filter(e => isPublished(e.entry));
    for (const e of all) paths.push({{ params: {{ locale, slug: e.slug }} }});
  }}
  return paths;
}}

const {{ locale, slug }} = Astro.params;
const entry = readEntry('erlebnisse', slug, locale);
if (!entry) return Astro.redirect('/erlebnisse/');

const kategorieLabel = {{ wandern:'Wandern', ski:'Ski & Snowboard', bike:'Bike & Mountainbike', wellness:'Wellness & Erholung', familie:'Familie & Kinder', kulinarik:'Kulinarik', kultur:'Kultur', abenteuer:'Abenteuer' }};
const kategorieEmoji = {{ wandern:'🥾', ski:'⛷️', bike:'🚵', wellness:'♨️', familie:'👨‍👩‍👧‍👦', kulinarik:'🍷', kultur:'🎭', abenteuer:'🧗' }};
const emoji = entry.emoji || kategorieEmoji[entry.kategorie] || '🏔️';
const katStr = entry.kategorie ? `${{kategorieEmoji[entry.kategorie] || ''}} ${{kategorieLabel[entry.kategorie] || entry.kategorie}}` : undefined;
const CATEGORY_EMOJI = {{ sehenswuerdigkeiten:'🏛️', gastro:'🍽️', unterkuenfte:'🏨', camping:'🏕️', erlebnisse:'🎯', orte:'🏘️', events:'🎪', regionen:'🏔️' }};
const nearbyEntries = entry.koordinaten ? findNearby(entry, 'erlebnisse', locale, 8) : [];
const mapMarkers = [];
if (entry.koordinaten) {{ mapMarkers.push({{ lat: entry.koordinaten.lat, lng: entry.koordinaten.lng, label: entry.name, emoji: emoji }}); }}
nearbyEntries.forEach(n => {{
  if (!n.entry.koordinaten) return;
  mapMarkers.push({{ lat: n.entry.koordinaten.lat, lng: n.entry.koordinaten.lng, label: n.entry.name || n.entry.titel, emoji: CATEGORY_EMOJI[n.collection] || '📍', href: '/' + n.collection + '/' + n.slug + '/' }});
}});
const title = entry.name || slug;
const metaDesc = generateMetaDescription(entry, 'de');
---

<DetailPage title={{title}} description={{metaDesc}} locale={{locale}}
  breadcrumbs="{{[{{ label: 'Erlebnisse', href: '/erlebnisse/' }}, {{ label: title }}]}}"
  sections="{{[
    {{ type:'hero', title, subtitle: entry.ort ? entry.ort + (katStr ? ' · ' + katStr : '') : katStr, emoji, image: entry.hero_bild || (entry.bilder?.[0]?.url) }},
    {{ type:'facts', items: [
      entry.kategorie && {{ icon: kategorieEmoji[entry.kategorie]||'🏷️', label: 'Kategorie', value: kategorieLabel[entry.kategorie]||entry.kategorie }},
      entry.dauer && {{ icon: '⏱️', label: 'Dauer', value: entry.dauer }},
      entry.preis && {{ icon: '💰', label: 'Preis', value: entry.preis }},
    ].filter(Boolean) }},
    {{ type:'description', content: entry.beschreibung || entry.kurzbeschreibung }},
    entry.koordinaten && {{ type:'map', markers: mapMarkers }},
    nearbyEntries.length > 0 && {{ type:'related', items: nearbyEntries.slice(0,4) }},
  ].filter(Boolean)}}"
/>"""

print("✅ erlebnisse")

# ── EVENTS ──
files[f"{LOCALE}/events/index.astro"] = f"""---
import BaseLayout from '../../layouts/BaseLayout.astro';
import Breadcrumbs from '../../components/Breadcrumbs.astro';
import SectionHeader from '../../components/SectionHeader.astro';
import EventCard from '../../components/EventCard.astro';
import SectionMap from '../../sections/SectionMap.astro';
import {{ readCollection, isPublished }} from '../../lib/content.js';
import {{ LANGUAGES_READY }} from '../../lib/languages.js';

export async function getStaticPaths() {{
  return LANGUAGES_READY.map(locale => ({{ params: {{ locale }} }}));
}}

const {{ locale }} = Astro.params;
const events = readCollection('events', locale).filter(e => isPublished(e.entry));
const sorted = [...events].sort((a,b) => (a.entry.datum_von||'').localeCompare(b.entry.datum_von||''));
const mitCoords = events.filter(e => e.entry.koordinaten?.lat && e.entry.koordinaten?.lng);
---

<BaseLayout title="Events in Tirol" description="Events, Konzerte, Feste und kulinarische Highlights in Tirol." locale={{locale}}>
  <main>
    <div class="container"><Breadcrumbs items="{{[{{ label: 'Events' }}]}}" /></div>
    <section class="page-header"><h1>Events in Tirol</h1><p>Veranstaltungen, Feste und kulinarische Events.</p></section>
    <div class="event-list">{{sorted.map(e => (<EventCard {{...e.entry}} slug={{e.slug}} />))}}</div>
  </main>
</BaseLayout>"""

files[f"{LOCALE}/events/[slug].astro"] = f"""---
import DetailPage from '../../sections/DetailPage.astro';
import {{ readEntry, readCollection, isPublished, findNearby, findRelated, autoLinkContent }} from '../../lib/content.js';
import {{ generateMetaDescription }} from '../../lib/seo.js';
import {{ LANGUAGES_READY }} from '../../lib/languages.js';

export async function getStaticPaths() {{
  const paths = [];
  for (const locale of LANGUAGES_READY) {{
    const all = readCollection('events', locale).filter(e => isPublished(e.entry));
    for (const e of all) paths.push({{ params: {{ locale, slug: e.slug }} }});
  }}
  return paths;
}}

const {{ locale, slug }} = Astro.params;
const entry = readEntry('events', slug, locale);
if (!entry) return Astro.redirect('/events/');

const emoji = entry.emoji || '🎪';
const subtitle = [entry.ort, entry.region && entry.region !== entry.ort ? entry.region : null].filter(Boolean).join(' · ');
const CATEGORY_EMOJI = {{ sehenswuerdigkeiten:'🏛️', gastro:'🍽️', unterkuenfte:'🏨', camping:'🏕️', erlebnisse:'🎯', orte:'🏘️', events:'🎪', regionen:'🏔️' }};
const nearbyEntries = entry.koordinaten ? findNearby(entry, 'events', locale, 8) : [];
const mapMarkers = [];
if (entry.koordinaten) {{ mapMarkers.push({{ lat: entry.koordinaten.lat, lng: entry.koordinaten.lng, label: entry.name || entry.titel, emoji }}); }}
nearbyEntries.forEach(n => {{
  if (!n.entry.koordinaten) return;
  mapMarkers.push({{ lat: n.entry.koordinaten.lat, lng: n.entry.koordinaten.lng, label: n.entry.name || n.entry.titel, emoji: CATEGORY_EMOJI[n.collection] || '📍', href: '/' + n.collection + '/' + n.slug + '/' }});
}});
const title = entry.name || entry.titel || slug;
const metaDesc = generateMetaDescription(entry, 'de');
---

<DetailPage title={{title}} description={{metaDesc}} locale={{locale}}
  breadcrumbs="{{[{{ label: 'Events', href: '/events/' }}, {{ label: title }}]}}"
  sections="{{[
    {{ type:'hero', title, subtitle, emoji, image: entry.hero_bild || (entry.bilder?.[0]?.url) }},
    {{ type:'facts', items: [
      entry.datum_von && {{ icon: '📅', label: 'Datum', value: entry.datum_von + (entry.datum_bis ? ' – ' + entry.datum_bis : '') }},
      entry.ort && {{ icon: '📍', label: 'Ort', value: entry.ort }},
    ].filter(Boolean) }},
    {{ type:'description', content: entry.beschreibung || entry.kurzbeschreibung }},
    entry.koordinaten && {{ type:'map', markers: mapMarkers }},
    nearbyEntries.length > 0 && {{ type:'related', items: nearbyEntries.slice(0,4) }},
  ].filter(Boolean)}}"
/>"""

files[f"{LOCALE}/events/eintragen/index.astro"] = f"""---
import BaseLayout from '../../../layouts/BaseLayout.astro';
import Breadcrumbs from '../../../components/Breadcrumbs.astro';
import SectionHeader from '../../../components/SectionHeader.astro';
import EventSubmissionForm from '../../../components/EventSubmissionForm.tsx';
import {{ LANGUAGES_READY }} from '../../../lib/languages.js';

export async function getStaticPaths() {{
  return LANGUAGES_READY.map(locale => ({{ params: {{ locale }} }}));
}}

const {{ locale }} = Astro.params;
---

<BaseLayout title="Event eintragen" description="Trage dein Event kostenlos auf tiroltourismus.com ein." locale={{locale}}>
  <main>
    <div class="container">
      <Breadcrumbs items="{{[{{ label: 'Events', href: '/events/' }}, {{ label: 'Event eintragen' }}]}}" />
    </div>
    <section class="ev-page-header"><div class="ev-page-emoji">🎪</div><h1>Event eintragen</h1><p>Trage dein Event kostenlos ein.</p></section>
    <EventSubmissionForm client:load />
  </main>
</BaseLayout>"""

print("✅ events")

# ── BEZIRKE ──
files[f"{LOCALE}/bezirke/index.astro"] = f"""---
import BaseLayout from '../../layouts/BaseLayout.astro';
import Breadcrumbs from '../../components/Breadcrumbs.astro';
import {{ readSingleton }} from '../../lib/content.js';
import {{ LANGUAGES_READY }} from '../../lib/languages.js';

export async function getStaticPaths() {{
  return LANGUAGES_READY.map(locale => ({{ params: {{ locale }} }}));
}}

const {{ locale }} = Astro.params;
const bezirke = readSingleton('bezirke');
const items = bezirke ? Object.values(bezirke) : [];
---

<BaseLayout title="Bezirke Tirols" description="Alle neun Bezirke Tirols im Überblick." locale={{locale}}>
  <main>
    <div class="container"><Breadcrumbs items="{{[{{ label: 'Bezirke' }}]}}" /></div>
    <section class="bezirke-hero"><h1>Bezirke Tirols</h1><p>Die neun Bezirke im Überblick.</p></section>
    <div class="bezirke-grid">
      {{items.map(b => (
        <a href="{{'/'+(locale!=='de'?locale+'/':'')+'bezirke/'+b.slug+'/'}}" class="bezirk-card">
          <h3>{{b.name}}</h3>
          <p>{{b.kurzbeschreibung?.slice(0,100)}}</p>
        </a>
      ))}}
    </div>
  </main>
</BaseLayout>"""

files[f"{LOCALE}/bezirke/[slug].astro"] = f"""---
import BaseLayout from '../../layouts/BaseLayout.astro';
import Breadcrumbs from '../../components/Breadcrumbs.astro';
import {{ readSingleton, readCollection, isPublished }} from '../../lib/content.js';
import {{ generateMetaDescription }} from '../../lib/seo.js';
import OrtCard from '../../components/OrtCard.astro';
import {{ LANGUAGES_READY }} from '../../lib/languages.js';

const BEZIRK_REGIONS = {{
  innsbruck: ['innsbruck'], 'innsbruck-land': ['innsbruck-land'],
  imst: ['imst', 'oetztal'], landeck: ['landeck', 'arlberg', 'kaunertal'],
  reutte: ['ausserfern'], kufstein: ['kufstein'],
  kitzbuehel: ['kitzbuehel'], schwaz: ['schwaz', 'achensee', 'zillertal'],
  lienz: ['osttirol', 'lienz'],
}};

export async function getStaticPaths() {{
  const paths = [];
  const bezirke = readSingleton('bezirke');
  if (!bezirke) return [];
  for (const locale of LANGUAGES_READY) {{
    for (const [slug] of Object.entries(bezirke)) {{
      paths.push({{ params: {{ locale, slug }} }});
    }}
  }}
  return paths;
}}

const {{ locale, slug }} = Astro.params;
const bezirke = readSingleton('bezirke');
const bezirk = bezirke?.[slug];
if (!bezirk) return Astro.redirect('/bezirke/');

const regionSlugs = BEZIRK_REGIONS[slug] || [];
const orteImBezirk = regionSlugs.flatMap(rSlug =>
  readCollection('orte', locale).filter(o => isPublished(o.entry) && o.entry.region === rSlug)
);
const underkunftImBezirk = regionSlugs.flatMap(rSlug =>
  readCollection('unterkuenfte', locale).filter(u => isPublished(u.entry) && u.entry.region === rSlug)
);
const gastroImBezirk = regionSlugs.flatMap(rSlug =>
  readCollection('gastro', locale).filter(g => isPublished(g.entry) && g.entry.region === rSlug)
);
const totalEntries = orteImBezirk.length + underkunftImBezirk.length + gastroImBezirk.length;

function formatNumber(n) {{
  if (!n && n !== 0) return '';
  return n.toString().replace(/\\B(?=(\\d{{3}})+(?!\\d))/g, '.');
}}
---

<BaseLayout title="{{bezirk.name}}" description="Alle Informationen zum Bezirk {{bezirk.name}} in Tirol." locale={{locale}}>
  <main>
    <div class="container"><Breadcrumbs items="{{[{{ label: 'Bezirke', href: '/bezirke/' }}, {{ label: bezirk.name }}]}}" /></div>
    <section class="bezirk-hero"><h1>{{bezirk.name}}</h1><p>{{bezirk.kurzbeschreibung}}</p></section>
    {{orteImBezirk.length > 0 && (<section><h2>Orte</h2><div class="card-grid">{{orteImBezirk.map(o => (<OrtCard {{...o.entry}} slug={{o.slug}} />))}}</div></section>)}}
  </main>
</BaseLayout>"""

print("✅ bezirke")

# ── WRITE ALL FILES ──
count = 0
for path, content in files.items():
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content.strip() + '\n')
    count += 1
    if count % 5 == 0:
        print(f"  ✍️  {count} files written...")

print(f"\n{'='*60}")
print(f"✅ {count} locale-aware Dateien erstellt")
print(f"{'='*60}")
print("\nJetzt Build testen: cd F:/tiroltourismus && NODE_OPTIONS=\"--max-old-space-size=4096\" npx astro build")
