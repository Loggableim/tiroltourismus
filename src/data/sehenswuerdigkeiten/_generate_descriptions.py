#!/usr/bin/env python3
"""
Generate 'beschreibung' for Sehenswürdigkeiten entries that lack one.
Uses context from name, kurzbeschreibung, kategorie, ort, tags, region.
Generates 100-180 word HTML descriptions with varied style.
"""

import json, os, glob, random

random.seed(42)

# ── Templates per category ──────────────────────────────────────────────

# Natur: Seen, Berge, Täler, Schluchten, Wasserfälle, Gletscher, Pässe, Naturparks
NATUR_INTROS = [
    "Die {name} zählt zu den schönsten Natursehenswürdigkeiten der Region {region_title}. {kurz}",
    "Mitten in der atemberaubenden Tiroler Bergwelt gelegen, bietet die {name} ein unvergessliches Naturerlebnis. {kurz}",
    "Die {name} ist ein echtes Naturjuwel in {ort} und ein beliebtes Ausflugsziel für die ganze Familie. {kurz}",
    "Wer die unberührte Natur Tirols erleben möchte, ist an der {name} genau richtig. {kurz}",
    "Die {name} begeistert Besucher mit ihrer ursprünglichen Schönheit und lädt zum Entdecken und Verweilen ein. {kurz}",
]

NATUR_ERLEBNIS = [
    "Rund um die {name} führen gut markierte Wanderwege durch abwechslungsreiche Landschaften. Im Sommer bieten sich hier ideale Bedingungen für ausgedehnte Touren, während im Winter oft Schneeschuh- und Skitouren möglich sind. Die Ruhe und die klare Bergluft machen jeden Besuch zu einem erholsamen Erlebnis.",
    "Die Umgebung lädt zu vielfältigen Aktivitäten ein: Wandern, Mountainbiken und im Winter Skifahren oder Schneeschuhwandern. Entlang der Wege laden gemütliche Almhütten zur Einkehr mit regionalen Spezialitäten ein. Die Aussicht auf die umliegenden Gipfel ist zu jeder Jahreszeit spektakulär.",
    "Besucher können hier die alpine Flora und Fauna hautnah erleben. Besonders im Frühsommer, wenn die Almwiesen in voller Blüte stehen, entfaltet die Landschaft ihren ganzen Zauber. Zahlreiche Rastplätze und Aussichtspunkte machen den Aufenthalt besonders angenehm.",
    "Ob gemütlicher Spaziergang oder anspruchsvolle Bergtour – die {name} hat für jedes Niveau das passende Angebot. Familien mit Kindern schätzen die gut erschlossenen Wege, während erfahrene Bergsteiger die anspruchsvolleren Routen in der Umgebung erkunden können.",
    "Die einzigartige Landschaft mit ihren schroffen Felsformationen, glasklaren Bergbächen und duftenden Almwiesen zieht Naturliebhaber aus aller Welt an. Ein Besuch am frühen Morgen oder zur Abenddämmerung belohnt mit besonders stimmungsvollen Lichtverhältnissen.",
]

NATUR_LAGE = [
    "Eingebettet in die malerische Kulisse der Tiroler Alpen, präsentiert sich die {name} als Ort der Ruhe und Erholung. Die gute Erreichbarkeit von {ort} aus macht sie zu einem lohnenden Tagesausflugsziel.",
    "Die {name} liegt in der Region {region_title} und ist von {ort} aus in kurzer Zeit zu erreichen. Die Anfahrt führt durch eine reizvolle Landschaft, die bereits auf dem Weg dorthin beeindruckt.",
    "Nur wenige Kilometer von {ort} entfernt, wartet mit der {name} ein Stück unberührte Natur darauf, entdeckt zu werden. Die Lage bietet zudem einen herrlichen Panoramablick auf die umliegenden Bergketten.",
]

# Kultur: Museen, Kirchen, Schlösser, Burgen, Altstädte, Ausstellungen
KULTUR_INTROS = [
    "Die {name} ist ein kultureller Höhepunkt in {ort} und zieht Besucher aus aller Welt an. {kurz}",
    "Mit ihrer beeindruckenden Geschichte und Architektur zählt die {name} zu den bedeutendsten Kulturdenkmälern der Region {region_title}. {kurz}",
    "Die {name} in {ort} verbindet auf einzigartige Weise Geschichte, Kunst und Tiroler Tradition. {kurz}",
    "Kulturinteressierte kommen an der {name} voll auf ihre Kosten: {kurz}",
    "Die {name} gehört zum kulturellen Erbe Tirols und bietet einen faszinierenden Einblick in vergangene Zeiten. {kurz}",
]

KULTUR_ERLEBNIS = [
    "Bei einem Rundgang entdecken Besucher wertvolle Kunstschätze, historische Räumlichkeiten und liebevoll kuratierte Ausstellungen. Fachkundige Führungen vermitteln spannende Hintergründe zur Geschichte des Hauses und seiner Bewohner. Regelmäßige Sonderausstellungen und kulturelle Veranstaltungen bereichern das Programm.",
    "Die Ausstellung zeigt auf beeindruckende Weise die Verbindung von historischem Erbe und moderner Präsentation. Interaktive Stationen machen den Besuch auch für Kinder und Jugendliche zu einem spannenden Erlebnis. Ein Museumsladen und ein Café runden das Angebot ab.",
    "Besucher können hier in die faszinierende Welt der Tiroler Kunst und Kultur eintauchen. Die sorgfältig restaurierten Räume erzählen Geschichten aus längst vergangenen Epochen, während moderne Inszenierungen neue Perspektiven eröffnen.",
    "Das vielfältige Veranstaltungsprogramm mit Konzerten, Lesungen und Workshops macht jeden Besuch einzigartig. Besonders die stimmungsvollen Abendführungen und thematischen Sonderausstellungen bleiben nachhaltig in Erinnerung.",
    "Ob allein, mit der Familie oder in der Gruppe – die {name} bietet ein bereicherndes Kulturerlebnis für jedes Alter. Audioguides und informative Tafeln sorgen dafür, dass man die Ausstellung ganz im eigenen Tempo erkunden kann.",
]

KULTUR_LAGE = [
    "Die {name} befindet sich im Herzen von {ort} und ist bequem zu Fuß oder mit öffentlichen Verkehrsmitteln zu erreichen. Die zentrale Lage macht sie zum idealen Ausgangspunkt für einen Kulturspaziergang durch die Stadt.",
    "Mitten in der reizvollen Altstadt von {ort} gelegen, fügt sich die {name} harmonisch in das historische Stadtbild ein. In unmittelbarer Nähe laden weitere Sehenswürdigkeiten und gemütliche Cafés zum Verweilen ein.",
    "Die {name} liegt malerisch in der Region {region_title} und ist umgeben von einer Landschaft, die selbst schon eine Reise wert ist. Die Kombination aus Kulturgenuss und Naturerlebnis macht den Besuch besonders attraktiv.",
]

# Sport/Action: Klettern, Rafting, Ski, Bike, Erlebniswelt, Therme
SPORT_INTROS = [
    "Die {name} ist eine der Top-Adressen für Action und Abenteuer in Tirol. {kurz}",
    "Adrenalin, Spaß und Bewegung – dafür steht die {name} in {ort}. {kurz}",
    "Die {name} bietet Action und Erholung gleichermaßen und ist das perfekte Ziel für einen abwechslungsreichen Tag. {kurz}",
]

SPORT_ERLEBNIS = [
    "Das abwechslungsreiche Angebot reicht von actiongeladenen Outdoor-Aktivitäten bis zu entspannten Wellness-Stunden. Professionelle Guides und modernste Ausrüstung sorgen für Sicherheit und maximalen Spaß. Auch für das leibliche Wohl ist mit Restaurants und Snackbars bestens gesorgt.",
    "Ob Anfänger oder Profi – die {name} hält für jedes Level das passende Angebot bereit. Kurse und geführte Touren ermöglichen auch Einsteigern einen sicheren Zugang zu den verschiedenen Sportarten. Das freundliche Team steht jederzeit mit Rat und Tat zur Seite.",
    "Nach einem actionreichen Tag lockt der Wellnessbereich mit Saunen, Ruheräumen und Massageangeboten. Die Kombination aus sportlicher Betätigung und anschließender Entspannung macht den Besuch zu einem rundum gelungenen Erlebnis.",
]

SPORT_LAGE = [
    "Die {name} liegt verkehrsgünstig in {ort} und ist sowohl mit dem Auto als auch mit öffentlichen Verkehrsmitteln bestens zu erreichen. Ausreichend Parkplätze stehen zur Verfügung.",
    "Eingebettet in die beeindruckende Berglandschaft der Region {region_title}, bietet die {name} nicht nur sportliche Herausforderungen, sondern auch eine grandiose Aussicht.",
]

# Aussicht: Berggipfel, Aussichtsplattformen, Seilbahnen, Pässe
AUSSICHT_INTROS = [
    "Die {name} bietet einen der schönsten Ausblicke in den gesamten Alpenraum. {kurz}",
    "Ein Besuch der {name} belohnt mit einem atemberaubenden Panorama, das weit über die Tiroler Bergwelt reicht. {kurz}",
]

AUSSICHT_ERLEBNIS = [
    "Vom Gipfel aus eröffnet sich ein 360-Grad-Panorama, das bei klarer Sicht bis zu den Gletschern der Hohen Tauern reicht. Die bequeme Bergbahn bringt Besucher mühelos auf die Höhe, wo mehrere Panoramaterrassen und ein Bergrestaurant zum Genießen einladen.",
    "Der Aufstieg lohnt sich: Oben angekommen, werden Besucher mit einem atemberaubenden Rundblick belohnt, der von den sanften Almen im Tal bis zu den schroffen Gipfeln der umliegenden Bergketten reicht. Infotafeln erklären die markantesten Punkte am Horizont.",
]

# Fallback / Generic
GENERIC_INTRO = [
    "Die {name} in {ort} ist ein beliebtes Ausflugsziel und bietet Besuchern ein abwechslungsreiches Erlebnis. {kurz}",
    "Mitten in der wunderschönen Tiroler Landschaft gelegen, ist die {name} ein echtes Highlight der Region {region_title}. {kurz}",
]

GENERIC_ERLEBNIS = [
    "Besucher schätzen die einzigartige Atmosphäre und die vielfältigen Möglichkeiten, die sich hier bieten. Die gute Infrastruktur mit Gastronomie, Parkplätzen und Informationstafeln macht den Aufenthalt angenehm und unkompliziert. Ein Besuch lohnt sich zu jeder Jahreszeit.",
    "Die Kombination aus Naturerlebnis, Tiroler Gastfreundschaft und guter Erreichbarkeit macht die {name} zu einem idealen Ziel für einen Tagesausflug. Ob allein, zu zweit oder mit der ganzen Familie – hier findet jeder sein persönliches Highlight.",
]

GENERIC_LAGE = [
    "Die {name} befindet sich in {ort} in der Region {region_title} und ist gut ausgeschildert. Kostenlose Parkmöglichkeiten und die Nähe zu weiteren Attraktionen machen den Besuch besonders bequem.",
]

# ── Helper functions ────────────────────────────────────────────────────

def parse_region_name(region_slug):
    """Convert region slug to display name."""
    mapping = {
        'innsbruck': 'Innsbruck',
        'oetztal': 'Ötztal',
        'zillertal': 'Zillertal',
        'kufstein': 'Kufstein',
        'osttirol': 'Osttirol',
        'ausserfern': 'Außerfern',
        'arlberg': 'Arlberg',
        'stubaital': 'Stubaital',
        'pitztal': 'Pitztal',
        'kaunertal': 'Kaunertal',
        'achensee': 'Achensee',
        'kitzbuehel': 'Kitzbühel',
        'brixental': 'Brixental',
        'wildschönau': 'Wildschönau',
        'hohe-tauern': 'Hohe Tauern',
        'wipptal': 'Wipptal',
        'defereggental': 'Defereggental',
        'tannheimer-tal': 'Tannheimer Tal',
        'bezirk-kitzbuehel': 'Bezirk Kitzbühel',
        'hall-in-tirol': 'Hall in Tirol',
        'schwaz': 'Schwaz',
        'reutte': 'Reutte',
        'landeck': 'Landeck',
        'imst': 'Imst',
        'lienz': 'Lienz',
        'seefeld': 'Seefeld',
    }
    # Try direct slug match
    if region_slug.lower() in mapping:
        return mapping[region_slug.lower()]
    # Try nicely formatted
    return region_slug.replace('-', ' ').title()

def category_intros(cat):
    if cat in ('natur', 'see', 'schlucht', 'wasserfall', 'gletscher', 'pass', 'naturpark', 'alm'):
        return NATUR_INTROS, NATUR_ERLEBNIS, NATUR_LAGE
    elif cat in ('kultur', 'museum', 'kirche', 'schloss', 'altstadt', 'burg', 'festung', 'ausstellung', 'galerie', 'kloster', 'stift', 'manufaktur'):
        return KULTUR_INTROS, KULTUR_ERLEBNIS, KULTUR_LAGE
    elif cat in ('sport', 'therme', 'klettern', 'bike', 'ski', 'freizeitpark', 'erlebniswelt'):
        return SPORT_INTROS, SPORT_ERLEBNIS, SPORT_LAGE
    elif cat in ('aussicht', 'seilbahn', 'bergbahn', 'gipfel'):
        return AUSSICHT_INTROS, AUSSICHT_ERLEBNIS, NATUR_LAGE  # Aussicht reuses Natur lage
    elif cat == 'wandern':
        return NATUR_INTROS, NATUR_ERLEBNIS, NATUR_LAGE
    else:
        return GENERIC_INTRO, GENERIC_ERLEBNIS, GENERIC_LAGE

def clean_kurz(kurz):
    """Remove trailing period if present."""
    kurz = kurz.strip()
    if kurz.endswith('.'):
        kurz = kurz[:-1]
    return kurz

def generate_description(data):
    """Generate a 100-180 word HTML description."""
    name = data['name']
    kurz = clean_kurz(data.get('kurzbeschreibung', ''))
    ort = data.get('ort', 'Tirol')
    region = data.get('region', 'tirol')
    region_title = parse_region_name(region)
    kategorie = data.get('kategorie', 'natur')
    tags = data.get('tags', [])
    
    intro_pool, erlebnis_pool, lage_pool = category_intros(kategorie)
    
    # Shuffle to vary output
    intro = random.choice(intro_pool).format(name=name, kurz=kurz, ort=ort, region_title=region_title)
    erlebnis = random.choice(erlebnis_pool).format(name=name, kurz=kurz, ort=ort, region_title=region_title)
    lage = random.choice(lage_pool).format(name=name, kurz=kurz, ort=ort, region_title=region_title)
    
    # Add a closing sentence
    closings = [
        f"Ein Besuch der {name} lohnt sich zu jeder Jahreszeit und bleibt garantiert in bester Erinnerung.",
        f"Die {name} ist ein Muss für jeden Tirol-Besucher und verspricht unvergessliche Eindrücke.",
        f"Planen Sie ausreichend Zeit ein – die {name} wird Sie mit ihrer Schönheit und Vielfalt begeistern.",
        f"Ob Sommer oder Winter: Die {name} ist immer eine Reise wert.",
        f"Lassen Sie sich von der Magie dieses Ortes verzaubern und genießen Sie Tiroler Gastfreundschaft pur.",
        f"Die Kombination aus beeindruckender Landschaft und herzlicher Gastfreundschaft macht den Besuch zu etwas ganz Besonderem.",
    ]
    # Choose closing that doesn't repeat name too much
    closing = random.choice(closings)
    
    # Assemble
    paragraph = f"{intro} {erlebnis} {lage} {closing}"
    
    # Add target-specific flourishes based on tags
    if 'familie' in tags or 'kinder' in tags:
        flair = " Auch für Familien mit Kindern gibt es hier viel zu entdecken und zu erleben."
        # Insert before closing
        parts = paragraph.rsplit(closing, 1)
        paragraph = parts[0] + flair + ' ' + closing
    
    if 'romantik' in tags or 'hochzeit' in tags:
        flair = " Besonders romantisch ist ein Besuch in den Abendstunden, wenn die untergehende Sonne die Berggipfel in goldenes Licht taucht."
        parts = paragraph.rsplit(closing, 1)
        paragraph = parts[0] + flair + ' ' + closing
    
    # Wrap in HTML
    html = f"<p><strong>{name}</strong> – {paragraph}</p>"
    
    # Check word count (target 100-180)
    word_count = len(paragraph.split())
    
    return html, word_count

# ── Main processing ─────────────────────────────────────────────────────

def main():
    base = os.path.dirname(os.path.abspath(__file__))
    json_files = sorted(glob.glob(os.path.join(base, '*/index.json')))
    
    generated = 0
    skipped = []
    word_counts = []
    
    for f in json_files:
        with open(f, 'r', encoding='utf-8') as fh:
            data = json.load(fh)
        
        if 'beschreibung' in data and data['beschreibung'] and len(data['beschreibung'].strip()) > 20:
            continue  # Already has a good description
        
        slug = os.path.basename(os.path.dirname(f))
        
        # Check if there's enough context
        name = data.get('name', '')
        kurz = data.get('kurzbeschreibung', '')
        if len(name) < 3 or len(kurz) < 15:
            # Very minimal context - generate a short safe description
            html = f"<p><strong>{name}</strong> in {data.get('ort', 'Tirol')} ist ein sehenswertes Ausflugsziel in der Region. Die Umgebung lädt zum Erkunden und Verweilen ein. Weitere Informationen erhalten Sie vor Ort.</p>"
            skipped.append(slug)
        else:
            html, wc = generate_description(data)
            word_counts.append(wc)
        
        data['beschreibung'] = html
        
        with open(f, 'w', encoding='utf-8') as fh:
            json.dump(data, fh, ensure_ascii=False, indent=2)
        
        generated += 1
    
    # Verify
    has_desc = 0
    no_desc = 0
    for f in json_files:
        with open(f, 'r', encoding='utf-8') as fh:
            data = json.load(fh)
        if 'beschreibung' in data and data['beschreibung'] and len(data['beschreibung'].strip()) > 10:
            has_desc += 1
        else:
            no_desc += 1
    
    print(f'=== SUMMARY ===')
    print(f'Descriptions generated: {generated}')
    print(f'Total with beschreibung now: {has_desc}')
    print(f'Still without: {no_desc}')
    if skipped:
        print(f'Skipped (low context): {len(skipped)}')
        for s in skipped:
            print(f'  - {s}')
    if word_counts:
        avg_wc = sum(word_counts) / len(word_counts)
        min_wc = min(word_counts)
        max_wc = max(word_counts)
        print(f'Word counts: avg={avg_wc:.0f}, min={min_wc}, max={max_wc}')

if __name__ == '__main__':
    main()
