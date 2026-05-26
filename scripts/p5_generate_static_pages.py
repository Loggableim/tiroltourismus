#!/usr/bin/env python3
"""Phase 5: Erstelle locale-aware statische Seiten unter [locale]/"""
import os, re

LOCALE = "F:/tiroltourismus/src/pages/[locale]"
ROOT = "F:/tiroltourismus/src/pages"
DATA = "F:/tiroltourismus/src/data"

os.makedirs(f"{LOCALE}/agb", exist_ok=True)
os.makedirs(f"{LOCALE}/datenschutz", exist_ok=True)
os.makedirs(f"{LOCALE}/impressum", exist_ok=True)
os.makedirs(f"{LOCALE}/faq", exist_ok=True)
os.makedirs(f"{LOCALE}/kontakt", exist_ok=True)
os.makedirs(f"{LOCALE}/ueber-uns", exist_ok=True)
os.makedirs(f"{LOCALE}/preise", exist_ok=True)
os.makedirs(f"{LOCALE}/newsletter", exist_ok=True)
os.makedirs(f"{LOCALE}/fuer-betriebe", exist_ok=True)
os.makedirs(f"{LOCALE}/suche", exist_ok=True)
os.makedirs(f"{LOCALE}/merkliste", exist_ok=True)

IMPORT = "import { LANGUAGES_READY } from '../../../lib/languages.js';"
IMPORT2 = "import { LANGUAGES_READY } from '../../lib/languages.js';"

def write(path, content):
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content.strip() + '\n')
    print(f"  ✅ {path}")

# 1. AGB - Rechtstext, erstmal DE übernehmen für alle Sprachen
write(f"{LOCALE}/agb/index.astro", f"""---
import BaseLayout from '../../../layouts/BaseLayout.astro';
import Breadcrumbs from '../../../components/Breadcrumbs.astro';
import SectionHeader from '../../../components/SectionHeader.astro';
import {{ readSingleton }} from '../../../lib/content.js';
{IMPORT}

export async function getStaticPaths() {{
  return LANGUAGES_READY.map(locale => ({{ params: {{ locale }} }}));
}}

const {{ locale }} = Astro.params;
const settings = readSingleton('einstellungen', locale);
const nav = {{ de:'AGB', en:'Terms & Conditions', fr:'Conditions Générales', it:'Termini e Condizioni', es:'Términos y Condiciones', zh:'条款和条件' }};
---

<BaseLayout title="{{nav[locale] || nav.de}}" description="Allgemeine Geschäftsbedingungen von tiroltourismus.com" locale={{locale}}>
  <main>
    <Breadcrumbs items="{{[{{ label: nav[locale] || nav.de }}]}}" />
    <section class="legal-page section">
      <div class="container" style="max-width:720px">
        <SectionHeader title="{{nav[locale] || nav.de}}" />
        <div class="legal-text">
          <h2>1. Geltungsbereich</h2>
          <p>Diese Allgemeinen Geschäftsbedingungen (AGB) gelten für die Nutzung des Portals tiroltourismus.com sowie für alle damit verbundenen Dienstleistungen. Betreiber ist Dominik Rainer, A-6020 Innsbruck.</p>
          <h2>2. Leistungsbeschreibung</h2>
          <p>tiroltourismus.com ist ein Tourismusportal, das Informationen über Regionen, Unterkünfte, Orte, Gastronomie, Erlebnisse, Events und weitere touristische Angebote in Tirol bereitstellt.</p>
          <h2>3. Nutzungsbedingungen</h2>
          <p>Die Nutzung des Portals ist für Endnutzer kostenlos. Für die Richtigkeit der eingetragenen Daten sind die jeweiligen Betriebe selbst verantwortlich.</p>
          <h2>4. Haftung</h2>
          <p>Der Betreiber haftet nicht für Schäden, die durch die Nutzung des Portals entstehen, soweit diese nicht auf Vorsatz oder grober Fahrlässigkeit beruhen.</p>
        </div>
      </div>
    </section>
  </main>
</BaseLayout>""")

# 2. Datenschutz
write(f"{LOCALE}/datenschutz/index.astro", f"""---
import BaseLayout from '../../../layouts/BaseLayout.astro';
import Breadcrumbs from '../../../components/Breadcrumbs.astro';
import SectionHeader from '../../../components/SectionHeader.astro';
import {{ readSingleton }} from '../../../lib/content.js';
{IMPORT}

export async function getStaticPaths() {{
  return LANGUAGES_READY.map(locale => ({{ params: {{ locale }} }}));
}}

const {{ locale }} = Astro.params;
const t = {{ de:'Datenschutz', en:'Privacy Policy', fr:'Protection des Données', it:'Protezione dei Dati', es:'Política de Privacidad', zh:'隐私政策' }};
---

<BaseLayout title="{{t[locale] || t.de}}" description="Datenschutzerklärung von tiroltourismus.com" locale={{locale}}>
  <main>
    <div class="container"><Breadcrumbs items="{{[{{ label: t[locale] || t.de }}]}}" /></div>
    <section class="legal-page section">
      <div class="container" style="max-width:720px">
        <SectionHeader title="{{t[locale] || t.de}}" />
        <div class="legal-text">
          <h2>1. Verantwortlicher</h2>
          <p>Verantwortlicher im Sinne der Datenschutz-Grundverordnung (DSGVO) ist Dominik Rainer, A-6020 Innsbruck.</p>
          <h2>2. Erhebung und Speicherung personenbezogener Daten</h2>
          <p>Beim Besuch der Website werden automatisch Informationen an den Server gesendet: IP-Adresse, Datum/Uhrzeit, Browsertyp, Betriebssystem, aufgerufene Seiten. Eine Speicherung dieser Daten erfolgt nicht.</p>
          <h2>3. Cookies</h2>
          <p>Diese Website verwendet ausschließlich technisch notwendige Cookies (Session-Cookies). Es werden keine Tracking-Cookies, Analyse-Cookies oder Marketing-Cookies gesetzt.</p>
          <h2>4. Rechte der betroffenen Person</h2>
          <p>Sie haben jederzeit das Recht auf Auskunft, Berichtigung, Löschung und Einschränkung der Verarbeitung Ihrer Daten. Kontakt: office@tiroltourismus.com</p>
        </div>
      </div>
    </section>
  </main>
</BaseLayout>""")

# 3. Impressum
write(f"{LOCALE}/impressum/index.astro", f"""---
import BaseLayout from '../../../layouts/BaseLayout.astro';
import Breadcrumbs from '../../../components/Breadcrumbs.astro';
import SectionHeader from '../../../components/SectionHeader.astro';
{{IMPORT}}

export async function getStaticPaths() {{
  return LANGUAGES_READY.map(locale => ({{ params: {{ locale }} }}));
}}

const {{ locale }} = Astro.params;
const t = {{ de:'Impressum', en:'Imprint', fr:'Mentions Légales', it:'Impressum', es:'Aviso Legal', zh:'法律声明' }};
---

<BaseLayout title="{{t[locale] || t.de}}" description="Impressum von tiroltourismus.com" locale={{locale}}>
  <main>
    <div class="container"><Breadcrumbs items="{{[{{ label: t[locale] || t.de }}]}}" /></div>
    <section class="legal-page section">
      <div class="container" style="max-width:720px">
        <SectionHeader title="{{t[locale] || t.de}}" />
        <div class="legal-text">
          <p><strong>Medieninhaber & Betreiber:</strong><br>Dominik Rainer<br>A-6020 Innsbruck<br>Österreich</p>
          <p><strong>Kontakt:</strong><br>E-Mail: office@tiroltourismus.com</p>
          <p><strong>Unternehmensgegenstand:</strong><br>Tourismusportal und -vermarktung</p>
          <p><strong>Mitgliedschaften:</strong><br>WKO Tirol, Tourismusverband Tirol</p>
          <p><strong>Haftungsausschluss:</strong><br>Trotz sorgfältiger inhaltlicher Kontrolle übernehmen wir keine Haftung für die Inhalte externer Links. Für den Inhalt der verlinkten Seiten sind ausschließlich deren Betreiber verantwortlich.</p>
        </div>
      </div>
    </section>
  </main>
</BaseLayout>""")

# 4. FAQ - data-getrieben via readSingleton
write(f"{LOCALE}/faq/index.astro", f"""---
import BaseLayout from '../../../layouts/BaseLayout.astro';
import Breadcrumbs from '../../../components/Breadcrumbs.astro';
import SectionHeader from '../../../components/SectionHeader.astro';
import {{ readSingleton }} from '../../../lib/content.js';
{{IMPORT}}

export async function getStaticPaths() {{
  return LANGUAGES_READY.map(locale => ({{ params: {{ locale }} }}));
}}

const {{ locale }} = Astro.params;
const faqItems = readSingleton('faq', locale) || [];
const t = {{ de:'Häufige Fragen', en:'FAQ', fr:'FAQ', it:'FAQ', es:'Preguntas Frecuentes', zh:'常见问题' }};
const categoryLabels = {{ de:{{ allgemein:'Allgemein', anreise:'Anreise', unterkunft:'Unterkunft', wandern:'Wandern', ski:'Ski & Winter', familie:'Familie', gastro:'Kulinarik', regionen:'Regionen', wetter:'Wetter', events:'Events' }}, en:{{ allgemein:'General', anreise:'Arrival', unterkunft:'Accommodation', wandern:'Hiking', ski:'Ski & Winter', familie:'Family', gastro:'Food', regionen:'Regions', wetter:'Weather', events:'Events' }} }};
const catOrder = ['allgemein','anreise','unterkunft','wandern','ski','familie','gastro','regionen','wetter','events'];
const grouped = new Map();
for (const c of catOrder) {{
  const items = faqItems.filter(i => i.kategorie === c);
  if (items.length > 0) grouped.set(c, items);
}}
---

<BaseLayout title="{{t[locale] || t.de}} – Tirol" description="Antworten auf die häufigsten Fragen zu Tirol" locale={{locale}}>
  <main>
    <div class="container"><Breadcrumbs items="{{[{{ label: t[locale] || t.de }}]}}" /></div>
    <SectionHeader title="{{t[locale] || t.de}}" sub="Häufige Fragen zu Tirol" />
    {{[...grouped.entries()].map(([cat, items]) => (
      <div class="faq-group">
        <h2>{{categoryLabels['de']?.[cat] || cat}}</h2>
        {{items.map(item => (<details class="faq-item"><summary>{{item.frage || item.q}}</summary><p>{{item.antwort || item.a}}</p></details>))}}
      </div>
    ))}}
  </main>
</BaseLayout>""")

# 5. Kontakt
write(f"{LOCALE}/kontakt/index.astro", f"""---
import BaseLayout from '../../../layouts/BaseLayout.astro';
import Breadcrumbs from '../../../components/Breadcrumbs.astro';
import ContactForm from '../../../components/ContactForm.tsx';
{{IMPORT}}

export async function getStaticPaths() {{
  return LANGUAGES_READY.map(locale => ({{ params: {{ locale }} }}));
}}

const {{ locale }} = Astro.params;
const t = {{ de:'Kontakt', en:'Contact', fr:'Contact', it:'Contatti', es:'Contacto', zh:'联系我们' }};
---

<BaseLayout title="{{t[locale] || t.de}}" description="Kontaktiere das Tirol Tourismus Team." locale={{locale}}>
  <main>
    <div class="container"><Breadcrumbs items="{{[{{ label: t[locale] || t.de }}]}}" /></div>
    <section class="kontakt-section">
      <h1>{{t[locale] || t.de}}</h1>
      <p>office@tiroltourismus.com</p>
    </section>
    <ContactForm client:load />
  </main>
</BaseLayout>""")

# 6. Über uns
write(f"{LOCALE}/ueber-uns/index.astro", f"""---
import BaseLayout from '../../../layouts/BaseLayout.astro';
import Breadcrumbs from '../../../components/Breadcrumbs.astro';
{{IMPORT}}

export async function getStaticPaths() {{
  return LANGUAGES_READY.map(locale => ({{ params: {{ locale }} }}));
}}

const {{ locale }} = Astro.params;
const t = {{ de:{{ title:'Über uns', desc:'Über tiroltourismus.com – Mission & Vision, Team-Philosophie, Geschichte des Portals und unsere Werte: Innovation, Nachhaltigkeit, Leidenschaft.' }}, en:{{ title:'About Us', desc:'About tiroltourismus.com – our mission, vision, and values.' }}, fr:{{ title:'À Propos', desc:'À propos de tiroltourismus.com – notre mission et nos valeurs.' }}, it:{{ title:'Chi Siamo', desc:'Chi siamo – missione e valori di tiroltourismus.com.' }}, es:{{ title:'Sobre Nosotros', desc:'Sobre tiroltourismus.com – nuestra misión y valores.' }}, zh:{{ title:'关于我们', desc:'关于蒂罗尔旅游门户 – 我们的使命和价值观。' }} }};
const info = t[locale] || t.de;
---

<BaseLayout title="{{info.title}}" description="{{info.desc}}" locale={{locale}}>
  <main>
    <div class="container"><Breadcrumbs items="{{[{{ label: info.title }}]}}" /></div>
    <section class="ueber-uns">
      <h1>{{info.title}}</h1>
      <p>tiroltourismus.com ist das moderne Tourismusportal für Tirol – kuratiert, KI-gestützt und community-basiert. Unser Ziel: Besuchern die schönsten Seiten Tirols zu zeigen und Betrieben eine smarte Präsentationsplattform zu bieten.</p>
    </section>
  </main>
</BaseLayout>""")

# 7. Preise - data-getrieben
write(f"{LOCALE}/preise/index.astro", f"""---
import BaseLayout from '../../../layouts/BaseLayout.astro';
import Breadcrumbs from '../../../components/Breadcrumbs.astro';
import SectionHeader from '../../../components/SectionHeader.astro';
import {{ TIERS, LEMONSQUEEZY }} from '../../../config/pricing.js';
{{IMPORT}}

export async function getStaticPaths() {{
  return LANGUAGES_READY.map(locale => ({{ params: {{ locale }} }}));
}}

const {{ locale }} = Astro.params;
const t = {{ de:'Preise & Mitgliedschaft', en:'Pricing', fr:'Tarifs', it:'Prezzi', es:'Precios', zh:'价格' }};
const tiers = [TIERS.basic, TIERS.silver, TIERS.gold];
---

<BaseLayout title="{{t[locale] || t.de}}" description="Preise für Betriebe – tiroltourismus.com" locale={{locale}}>
  <main>
    <div class="container"><Breadcrumbs items="{{[{{ label: t[locale] || t.de }}]}}" /></div>
    <SectionHeader title="{{t[locale] || t.de}}" sub="Wähle das passende Paket für deinen Betrieb" />
    <div class="pricing-grid">
      {{tiers.map(tier => (
        <div class="pricing-card data-tier="{{tier.id}}">
          <h3>{{tier.name}}</h3>
          <div class="price">€{{tier.price}}<span>/Monat</span></div>
          <ul>{{tier.features.map(f => (<li>{{f}}</li>))}}</ul>
        </div>
      ))}}
    </div>
  </main>
</BaseLayout>""")

# 8. Newsletter
write(f"{LOCALE}/newsletter/index.astro", f"""---
import BaseLayout from '../../../layouts/BaseLayout.astro';
import Breadcrumbs from '../../../components/Breadcrumbs.astro';
import NewsletterForm from '../../../components/NewsletterForm.tsx';
{{IMPORT}}

export async function getStaticPaths() {{
  return LANGUAGES_READY.map(locale => ({{ params: {{ locale }} }}));
}}

const {{ locale }} = Astro.params;
const t = {{ de:'Newsletter', en:'Newsletter', fr:'Newsletter', it:'Newsletter', es:'Boletín', zh:'新闻通讯' }};
---

<BaseLayout title="{{t[locale] || t.de}}" description="Abonniere den Tirol Tourismus Newsletter." locale={{locale}}>
  <main>
    <div class="container"><Breadcrumbs items="{{[{{ label: t[locale] || t.de }}]}}" /></div>
    <section class="newsletter-page">
      <h1>{{t[locale] || t.de}}</h1>
      <p>Einmal im Monat die schönsten Seiten Tirols – Berggeschichten, Events und exklusive Angebote.</p>
      <NewsletterForm client:load />
    </section>
  </main>
</BaseLayout>""")

# 9. Für Betriebe
write(f"{LOCALE}/fuer-betriebe/index.astro", f"""---
import BaseLayout from '../../../layouts/BaseLayout.astro';
import Hero from '../../../components/Hero.astro';
import Breadcrumbs from '../../../components/Breadcrumbs.astro';
import SectionHeader from '../../../components/SectionHeader.astro';
{{IMPORT}}

export async function getStaticPaths() {{
  return LANGUAGES_READY.map(locale => ({{ params: {{ locale }} }}));
}}

const {{ locale }} = Astro.params;
const t = {{ de:'Für Betriebe', en:'For Businesses', fr:'Pour les Pros', it:'Per Aziende', es:'Para Empresas', zh:'企业服务' }};
---

<BaseLayout title="{{t[locale] || t.de}}" description="Präsentiere deinen Betrieb auf tiroltourismus.com." locale={{locale}}>
  <main>
    <div class="container"><Breadcrumbs items="{{[{{ label: t[locale] || t.de }}]}}" /></div>
    <Hero title="{{t[locale] || t.de}}" subtitle="Präsentiere deinen Betrieb auf dem modernsten Tourismusportal der Alpen." emoji="🏪" size="md" />
    <section class="section">
      <div class="container">
        <p>Mit tiroltourismus.com erreichst du tausende potenzielle Gäste. Kostenlose Basiseinträge, Premium-Features für mehr Sichtbarkeit.</p>
        <a href="/preise/" class="btn btn-pink">Jetzt Partner werden →</a>
      </div>
    </section>
  </main>
</BaseLayout>""")

# 10. Suche
write(f"{LOCALE}/suche/index.astro", f"""---
import BaseLayout from '../../../layouts/BaseLayout.astro';
{{IMPORT}}

export async function getStaticPaths() {{
  return LANGUAGES_READY.map(locale => ({{ params: {{ locale }} }}));
}}

const {{ locale }} = Astro.params;
const t = {{ de:{{ title:'Suche', desc:'Durchsuche das Tirol Tourismus Portal.' }}, en:{{ title:'Search', desc:'Search the Tyrol Tourism Portal.' }}, fr:{{ title:'Recherche', desc:'Rechercher sur le portail touristique du Tyrol.' }}, it:{{ title:'Cerca', desc:'Cerca nel portale turistico del Tirolo.' }}, es:{{ title:'Buscar', desc:'Buscar en el portal turístico del Tirol.' }}, zh:{{ title:'搜索', desc:'搜索蒂罗尔旅游门户。' }} }};
const info = t[locale] || t.de;
---

<BaseLayout title="{{info.title}}" description="{{info.desc}}" locale={{locale}}>
  <main>
    <div class="pagefind-search"><link href="/pagefind/pagefind-ui.css" rel="stylesheet" /><script src="/pagefind/pagefind-ui.js" is:inline></script><div id="search"></div><script is:inline>window.addEventListener('DOMContentLoaded',function(){{new PagefindUI({{element:'#search',showSubResults:true,showImages:false,resetStyles:false,baseUrl:locale==='de'?'/':'/'+locale+'/'}});}});</script></div>
  </main>
</BaseLayout>""")

# 11. Merkliste
write(f"{LOCALE}/merkliste/index.astro", f"""---
import BaseLayout from '../../../layouts/BaseLayout.astro';
import MerklistePage from '../../../components/MerklistePage.tsx';
{{IMPORT}}

export async function getStaticPaths() {{
  return LANGUAGES_READY.map(locale => ({{ params: {{ locale }} }}));
}}

const {{ locale }} = Astro.params;
const t = {{ de:'Merkliste', en:'Wishlist', fr:'Favoris', it:'Preferiti', es:'Favoritos', zh:'收藏夹' }};
---

<BaseLayout title="{{t[locale] || t.de}}" description="Deine Merkliste – gespeicherte Orte, Unterkünfte und Erlebnisse." locale={{locale}}>
  <main>
    <div class="container"><h1>{{t[locale] || t.de}}</h1></div>
    <MerklistePage client:load />
  </main>
</BaseLayout>""")

print(f"\n{'='*60}")
print(f"✅ 11 statische Seiten in [locale]/ erstellt")
print(f"{'='*60}")
