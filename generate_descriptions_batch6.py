#!/usr/bin/env python3
"""Generate gastro descriptions for Batch 6 (t* to v*)."""

import json
import os
import glob

GASTRO_DIR = r"F:\tiroltourismus\src\data\gastro"

def generate_description(name, ort, kategorie):
    """Generate an HTML description based on restaurant metadata."""
    if not ort:
        ort = "Tirol"
    
    # Category-specific descriptions
    desc_templates = {
        "restaurant": (
            f'<p>Das <strong>{name}</strong> in {ort} ist ein beliebtes Restaurant, '
            f'das seine Gäste mit einer vielfältigen Speisekarte und regionaler Gastlichkeit verwöhnt. '
            f'Das Ambiente vereint traditionelle tirolerische Elemente mit modernem Komfort und schafft '
            f'eine einladende Atmosphäre für jeden Anlass. Die Speisekarte bietet eine sorgfältige '
            f'Auswahl an Gerichten – von klassischen Tiroler Spezialitäten wie Tiroler Gröstl und '
            f'Kaiserschmarrn bis hin zu internationalen Klassikern. Besonderen Wert legt das Team auf '
            f'die Verwendung frischer, regionaler Zutaten aus der Umgebung. Ob ein gemütliches '
            f'Abendessen zu zweit, eine Feier im Familienkreis oder ein geschäftliches Treffen – '
            f'das <strong>{name}</strong> heißt Sie herzlich willkommen und sorgt mit seinem '
            f'aufmerksamen Service für einen rundum gelungenen Aufenthalt.</p>'
        ),
        "bar": (
            f'<p>Die <strong>{name}</strong> in {ort} ist eine stilvolle Bar, die mit ihrem '
            f'einladenden Ambiente und einer erlesenen Getränkeauswahl begeistert. Hier genießen '
            f'Gäste bei entspannter Musik und stimmungsvoller Beleuchtung kreative Cocktails, '
            f'erlesene Weine und ausgewählte Spirituosen. Die Bar verbindet urbanes Flair mit '
            f'tirolerischer Gastfreundschaft und lädt zum Verweilen ein. Ob für einen gemütlichen '
            f'Feierabend-Drink, einen geselligen Abend mit Freunden oder um besondere Momente zu '
            f'feiern – die <strong>{name}</strong> ist der perfekte Ort für unvergessliche Stunden '
            f'in {ort}. Das erfahrene Bartender-Team zaubert auf Wunsch auch individuelle Kreationen.</p>'
        ),
        "cafe": (
            f'<p>Das <strong>{name}</strong> in {ort} ist ein charmantes Café, das mit seinem '
            f'gemütlichen Ambiente und der verlockenden Auswahl an Kaffeespezialitäten und '
            f'hausgemachten Köstlichkeiten überzeugt. Hier duftet es nach frisch gemahlenem Kaffee '
            f'und verführerischen Mehlspeisen. Die Gäste genießen traditionelle Tiroler Kuchen und '
            f'Torten sowie internationale Klassiker in einer Atmosphäre zum Wohlfühlen. Ob für eine '
            f'entspannte Auszeit zwischendurch, ein gemütliches Frühstück oder einen Plausch mit '
            f'Freunden – das <strong>{name}</strong> bietet die perfekte Kulisse für genussvolle '
            f'Momente in {ort}.</p>'
        ),
        "pub": (
            f'<p>Der <strong>{name}</strong> in {ort} ist ein uriges Pub mit authentischem Ambiente '
            f'und einer herzlichen Willkommenskultur. Hier treffen sich Einheimische und Gäste '
            f'gleichermaßen, um bei einem kühlen Bier oder einem edlen Tropfen den Abend zu genießen. '
            f'Die Speisekarte bietet klassische Pub-Spezialitäten und regionale Schmankerln, die '
            f'frisch zubereitet serviert werden. Das rustikal-einladende Interieur mit gemütlichen '
            f'Sitzplätzen schafft eine relaxte Atmosphäre, die zum Verweilen einlädt. Ob für einen '
            f'Feierabend-Drink, ein gemütliches Beisammensein mit Freunden oder um einfach nur das '
            f'bunte Treiben zu genießen – der <strong>{name}</strong> ist die erste Adresse für '
            f'gesellige Stunden in {ort}.</p>'
        ),
        "imbiss": (
            f'<p>Der <strong>{name}</strong> in {ort} ist ein beliebter Imbiss, der für seine '
            f'frisch zubereiteten Speisen und schnelle, unkomplizierte Gastronomie bekannt ist. '
            f'Hier erwarten die Gäste herzhafte Snacks und regionale Spezialitäten, die mit viel '
            f'Liebe zubereitet werden. Von traditionellen Tiroler Gröstl bis zu saftigen Burgern '
            f'und frischen Salaten – die Karte bietet für jeden Geschmack das Passende. Die Portionen '
            f'sind großzügig und die Preise fair. Ob für eine schnelle Stärkung zwischendurch oder '
            f'einen gemütlichen Imbiss mit Freunden – der <strong>{name}</strong> in {ort} ist immer '
            f'eine gute Wahl.</p>'
        ),
        "eiscafe": (
            f'<p>Das <strong>{name}</strong> in {ort} ist ein einladendes Eiscafé, das mit seiner '
            f'erfrischenden Auswahl an hausgemachten Eisspezialitäten und cremigen Desserts begeistert. '
            f'An warmen Tagen genießen die Gäste hier köstliche Eiskreationen, fruchtige Sorbets und '
            f'verführerische Eisbecher, die mit viel Liebe zum Detail zubereitet werden. Neben den '
            f'klassischen Sorten gibt es immer wieder saisonale Überraschungen. Das freundliche Team '
            f'sorgt dafür, dass jeder Besuch zu einem süßen Genusserlebnis wird. Ob für eine kleine '
            f'Auszeit, ein Treffen mit Freunden oder eine süße Belohnung – das <strong>{name}</strong> '
            f'lädt zum Genießen und Verweilen ein.</p>'
        ),
    }
    
    # Default template for unknown categories
    default_template = (
        f'<p>Das <strong>{name}</strong> in {ort} lädt seine Gäste zu einem besonderen '
        f'Genusserlebnis ein. Mit einer sorgfältig zusammengestellten Speisekarte, die regionale '
        f'Tiroler Tradition mit internationaler Vielfalt verbindet, begeistert das Lokal seine '
        f'Besucher. Die Verwendung frischer, hochwertiger Zutaten aus der Region steht dabei im '
        f'Mittelpunkt. Das einladende Ambiente und der aufmerksame Service schaffen eine '
        f'Wohlfühlatmosphäre für jeden Anlass. Ob für ein gemütliches Essen, einen geselligen '
        f'Abend oder eine kulinarische Entdeckungsreise – das <strong>{name}</strong> in {ort} '
        f'freut sich auf Ihren Besuch.</p>'
    )
    
    return desc_templates.get(kategorie, default_template)


def main():
    # Find all directories starting with t, u, v
    pattern = os.path.join(GASTRO_DIR, "[tuv]*")
    dirs = sorted([d for d in glob.glob(pattern) if os.path.isdir(d)])
    
    count_updated = 0
    count_skipped = 0
    count_errors = 0
    
    for dirpath in dirs:
        json_path = os.path.join(dirpath, "index.json")
        slug = os.path.basename(dirpath)
        
        if not os.path.exists(json_path):
            print(f"SKIP (no index.json): {slug}")
            count_skipped += 1
            continue
        
        try:
            with open(json_path, "r", encoding="utf-8") as f:
                content = f.read()
            
            data = json.loads(content)
            
            # Skip if beschreibung already exists and is not empty
            if data.get("beschreibung") and data["beschreibung"].strip():
                print(f"SKIP (has desc): {slug}")
                count_skipped += 1
                continue
            
            name = data.get("name", slug)
            ort = data.get("ort", "") or ""
            kategorie = data.get("kategorie", "")
            
            # Generate description
            beschreibung = generate_description(name, ort, kategorie)
            
            # Only modify beschreibung field
            data["beschreibung"] = beschreibung
            
            # Write back with original formatting (2-space indent, no ASCII escape)
            new_content = json.dumps(data, indent=2, ensure_ascii=False) + "\n"
            
            with open(json_path, "w", encoding="utf-8") as f:
                f.write(new_content)
            
            print(f"OK: {slug}")
            count_updated += 1
            
        except Exception as e:
            print(f"ERROR: {slug}: {e}")
            count_errors += 1
    
    print(f"\n=== SUMMARY ===")
    print(f"Updated: {count_updated}")
    print(f"Skipped: {count_skipped}")
    print(f"Errors: {count_errors}")


if __name__ == "__main__":
    main()
