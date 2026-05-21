#!/usr/bin/env python3
"""P5 Generator: Erstellt locale-aware statische Seiten unter [locale]/"""
import os, re

BASE = "F:/tiroltourismus"
LOCALE = f"{BASE}/src/pages/[locale]"
IMPORT = "import { LANGUAGES_READY } from '../../lib/languages.js';"

# ── Kategorien ──
STATICS = [
    # (ordner, title, desc, hat_formular, ist_legal)
    ("agb", "AGB", "Allgemeine Geschäftsbedingungen von tiroltourismus.com", False, True),
    ("datenschutz", "Datenschutz", "Datenschutzerklärung von tiroltourismus.com", False, True),
    ("impressum", "Impressum", "Impressum – Offenlegung, Kontakt und rechtliche Hinweise", False, True),
    ("faq", "FAQ", "Häufige Fragen zu Tirol – Antworten auf die wichtigsten Fragen", False, False),
    ("kontakt", "Kontakt", "Kontaktiere das Team von tiroltourismus.com", True, False),
    ("ueber-uns", "Über uns", "Über tiroltourismus.com – Mission & Vision", False, False),
    ("preise", "Preise & Mitgliedschaft", "Preise und Mitgliedschaft für Betriebe", False, False),
    ("newsletter", "Newsletter", "Melde dich zum Tirol-Newsletter an", True, False),
    ("fuer-betriebe", "Für Betriebe", "Für Betriebe – Jetzt eintragen und sichtbar werden", False, False),
    ("suche", "Suche", "Durchsuche das Tirol Tourismus Portal", False, False),
    ("merkliste", "Merkliste", "Deine gespeicherten Favoriten", False, False),
]

# ── Rechtstexte (hardcoded DE → zeigen wir in allen Sprachen gleich) ──
LEGAL_TEXTS = {}

# AGB aus git extrahieren
agb_text = """"""

files = {}
for folder, title, desc, has_form, is_legal in STATICS:
    os.makedirs(f"{LOCALE}/{folder}", exist_ok=True)
    
    # BaseLayout import depth: ../../ (from [locale]/x/index.astro)
    
    if is_legal:
        # Rechtstexte: read the exact content from git and wrap in locale-aware layout
        # Simple approach: extract text from git HEAD
        import subprocess
        r = subprocess.run(
            ["git", "show", f"HEAD:src/pages/{folder}/index.astro"],
            capture_output=True, text=True, timeout=10, cwd=BASE
        )
        raw = r.stdout
        
        # Extract everything between <BaseLayout...>...</BaseLayout>
        # Just keep the content after the frontmatter -- legal pages have no data logic
        # We'll recreate them as static pages
        
        content = f"""---
import BaseLayout from '../../layouts/BaseLayout.astro';
import Breadcrumbs from '../../components/Breadcrumbs.astro';
import SectionHeader from '../../components/SectionHeader.astro';
{IMPORT}

export async function getStaticPaths() {{
  return LANGUAGES_READY.map(locale => ({{ params: {{ locale }} }}));
}}

const {{ locale }} = Astro.params;
---

<BaseLayout title="{title}" description="{desc}" locale={{locale}}>
  <main>
    <div class="container">
      <Breadcrumbs items="{{[{{ label: '{title}' }}]}}" />
    </div>
    <section class="legal-page section">
      <div class="container" style="max-width:720px">
        <SectionHeader title="{title}" />
        <div class="legal-text">
"""
        # Extract the legal HTML content from original page
        # After "legal-text" div
        m = re.search(r'<div class="legal-text">(.*?)</div>\s*</section>', raw, re.DOTALL)
        if m:
            content += m.group(1)
        else:
            # Fallback: extract everything after last -->
            parts = raw.split('---')
            if len(parts) >= 3:
                body = '---'.join(parts[2:])
                # Remove BaseLayout wrapper  
                body = re.sub(r'<BaseLayout[^>]*>', '', body)
                body = re.sub(r'</BaseLayout>', '', body)
                content += body
        
        content += """</div>
      </div>
    </section>
  </main>
</BaseLayout>"""
        
        files[f"{folder}/index.astro"] = content
        print(f"  ✅ {folder} (legal text)")
        
    elif folder == "faq":
        # FAQ: data-driven via readSingleton('faq', locale)
        content = f"""---
import BaseLayout from '../../layouts/BaseLayout.astro';
import Breadcrumbs from '../../components/Breadcrumbs.astro';
import SectionHeader from '../../components/SectionHeader.astro';
import {{ readSingleton }} from '../../lib/content.js';
{IMPORT}

export async function getStaticPaths() {{
  return LANGUAGES_READY.map(locale => ({{ params: {{ locale }} }}));
}}

const {{ locale }} = Astro.params;
const faqItems = readSingleton('faq', locale) || [];

const categoryOrder = ['allgemein', 'anreise', 'unterkunft', 'wandern', 'ski', 'familie', 'gastro', 'regionen', 'wetter', 'events'];
const categoryLabels = {{
  allgemein: 'Allgemein', anreise: 'Anreise', unterkunft: 'Unterkunft',
  wandern: 'Wandern', ski: 'Ski & Winter', familie: 'Familie & Kinder',
  gastro: 'Kulinarik', regionen: 'Regionen', wetter: 'Wetter & Reisezeit', events: 'Events & Veranstaltungen',
}};
const categoryEmoji = {{
  allgemein: '📌', anreise: '🚗', unterkunft: '🏨', wandern: '🥾',
  ski: '⛷️', familie: '👨‍👩‍👧‍👦', gastro: '🍽️', regionen: '🗺️', wetter: '🌤️', events: '🎉',
}};

const grouped = new Map();
for (const cat of categoryOrder) {{
  const items = faqItems.filter(i => i.kategorie === cat);
  if (items.length > 0) grouped.set(cat, items);
}}
---

<BaseLayout title="FAQ – Tirol Tourismus" description="{desc}" locale={{locale}}>
  <main>
    <div class="container"><Breadcrumbs items="{{[{{ label: 'FAQ' }}]}}" /></div>
    <SectionHeader title="FAQ" sub="Häufige Fragen zu Tirol" />
    <div class="faq-grid">{{[...grouped.entries()].map(([cat, items]) => (
      <div class="faq-category"><h2 class="faq-cat-title">{{categoryEmoji[cat]}} {{categoryLabels[cat]}}</h2>
        {{items.map(item => (<details class="faq-item"><summary>{{item.frage || item.q}}</summary><p>{{item.antwort || item.a}}</p></details>))}}
      </div>
    ))}}</div>
  </main>
</BaseLayout>"""
        files[f"{folder}/index.astro"] = content
        print(f"  ✅ {folder} (data-driven)")
        
    elif has_form:
        # Kontakt / Newsletter: has a React component
        comp = "ContactForm" if folder == "kontakt" else "NewsletterForm"
        comp_path = f"../../components/{comp}.tsx"
        
        content = f"""---
import BaseLayout from '../../layouts/BaseLayout.astro';
import Breadcrumbs from '../../components/Breadcrumbs.astro';
import {comp} from '{comp_path}';
{IMPORT}

export async function getStaticPaths() {{
  return LANGUAGES_READY.map(locale => ({{ params: {{ locale }} }}));
}}

const {{ locale }} = Astro.params;
---

<BaseLayout title="{title}" description="{desc}" locale={{locale}}>
  <main>
    <div class="container"><Breadcrumbs items="{{[{{ label: '{title}' }}]}}" /></div>
    <section class="page-header"><h1>{title}</h1></section>
    {"<" + comp + " client:load />"}
  </main>
</BaseLayout>"""
        files[f"{folder}/index.astro"] = content
        print(f"  ✅ {folder} (form / {comp})")
        
    elif folder == "preise":
        # Pricing page: imports config
        content = f"""---
import BaseLayout from '../../layouts/BaseLayout.astro';
import Breadcrumbs from '../../components/Breadcrumbs.astro';
import SectionHeader from '../../components/SectionHeader.astro';
import {{ TIERS, LEMONSQUEEZY }} from '../../config/pricing.js';
{IMPORT}

export async function getStaticPaths() {{
  return LANGUAGES_READY.map(locale => ({{ params: {{ locale }} }}));
}}

const {{ locale }} = Astro.params;
const tiers = [TIERS.basic, TIERS.silver, TIERS.gold];
const features = TIERS.basic.features.map((f, i) => ({{
  label: f.text,
  basic: TIERS.basic.features[i].included,
  silver: TIERS.silver.features[i].included,
  gold: TIERS.gold.features[i].included,
}}));
---

<BaseLayout title="{title}" description="{desc}" locale={{locale}}>
  <main>
    <div class="container"><Breadcrumbs items="{{[{{ label: 'Preise' }}]}}" /></div>
    <SectionHeader title="Preise" sub="Wähle das passende Paket für deinen Betrieb" />
    <div class="pricing-grid">{{tiers.map(tier => (
      <div class="pricing-card" data-tier={{tier.id}}>
        <h3>{{tier.name}}</h3>
        <div class="price">{{tier.price > 0 ? '€' + tier.price + '/Monat' : 'Kostenlos'}}</div>
        <ul>{{features.filter(f => f[tier.id]).map(f => (<li>{{f.label}}</li>))}}</ul>
      </div>
    ))}}</div>
  </main>
</BaseLayout>"""
        files[f"{folder}/index.astro"] = content
        print(f"  ✅ {folder} (pricing)")
        
    elif folder == "suche":
        content = f"""---
import BaseLayout from '../../layouts/BaseLayout.astro';
{IMPORT}

export async function getStaticPaths() {{
  return LANGUAGES_READY.map(locale => ({{ params: {{ locale }} }}));
}}

const {{ locale }} = Astro.params;
---

<BaseLayout title="{title}" description="{desc}" locale={{locale}}>
  <main>
    <section class="search-hero">
      <div class="container" style="text-align:center;padding:80px 0 40px">
        <div style="font-size:64px;margin-bottom:8px">🔍</div>
        <h1 style="font-family:var(--font-display);font-size:48px;letter-spacing:2px;text-transform:uppercase;margin-bottom:8px">{title}</h1>
        <p style="color:var(--text2);font-size:16px;max-width:500px;margin:0 auto">Durchsuche das Tirol Tourismus Portal</p>
      </div>
    </section>
    <div class="container"><div class="search-container"><div class="pagefind-ui" data-pagefind-ignore></div></div></div>
  </main>
</BaseLayout>"""
        files[f"{folder}/index.astro"] = content
        print(f"  ✅ {folder} (search)")
        
    elif folder == "merkliste":
        content = f"""---
import BaseLayout from '../../layouts/BaseLayout.astro';
import MerklistePage from '../../components/MerklistePage.tsx';
{IMPORT}

export async function getStaticPaths() {{
  return LANGUAGES_READY.map(locale => ({{ params: {{ locale }} }}));
}}

const {{ locale }} = Astro.params;
---

<BaseLayout title="{title}" description="{desc}" locale={{locale}}>
  <main>
    <div class="container"><Breadcrumbs items="{{[{{ label: 'Merkliste' }}]}}" /></div>
    <MerklistePage client:load />
  </main>
</BaseLayout>"""
        files[f"{folder}/index.astro"] = content
        print(f"  ✅ {folder} (wishlist)")
        
    else:
        # Generic: Über uns, Für Betriebe — hardcoded DE text
        # We read from git and adapt
        import subprocess
        r = subprocess.run(
            ["git", "show", f"HEAD:src/pages/{folder}/index.astro"],
            capture_output=True, text=True, timeout=10, cwd=BASE
        )
        raw = r.stdout
        
        # Extract content sections between <BaseLayout> and </BaseLayout>
        # but convert to locale-aware version
        body_parts = raw.split('---')
        if len(body_parts) >= 3:
            body_html = '---'.join(body_parts[2:])
            # Keep HTML content as-is (it's in DE, will be shown for all locales)
            # Just replace the BaseLayout wrapper
            body_html = re.sub(r'<BaseLayout[^>]*>', '', body_html)
            body_html = re.sub(r'</BaseLayout>', '', body_html)
        else:
            body_html = f"<section class='page-header'><h1>{title}</h1></section>"
        
        content = f"""---
import BaseLayout from '../../layouts/BaseLayout.astro';
import Breadcrumbs from '../../components/Breadcrumbs.astro';
{IMPORT}

export async function getStaticPaths() {{
  return LANGUAGES_READY.map(locale => ({{ params: {{ locale }} }}));
}}

const {{ locale }} = Astro.params;
---

<BaseLayout title="{title}" description="{desc}" locale={{locale}}>
  <main>
    <div class="container"><Breadcrumbs items="{{[{{ label: '{title}' }}]}}" /></div>
    {body_html.strip()}
  </main>
</BaseLayout>"""
        files[f"{folder}/index.astro"] = content
        print(f"  ✅ {folder} (generic)")

# ── Write all files ──
count = 0
for rel_path, content in files.items():
    path = f"{LOCALE}/{rel_path}"
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content.strip() + '\n')
    count += 1

print(f"\n{'='*60}")
print(f"✅ {count} locale-aware statische Seiten erstellt")
print(f"{'='*60}")
