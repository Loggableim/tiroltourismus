#!/usr/bin/env python3
"""Batch-generate watercolor images for ALL magazine articles.

- 1 image for short articles (<2000 chars)
- 2 for medium (2000-4000)
- 3 for long (4000+)

Watercolor style is the default moving forward.
"""
import sys, time, json
from pathlib import Path
import torch
from diffusers import StableDiffusionXLPipeline

MODEL = Path(r"C:/HermesPortable/ComfyUI/models/checkpoints/sd_xl_base_1.0.safetensors")
MAGAZIN = Path("F:/tiroltourismus/src/data/magazin")
OUT_BASE = Path("F:/tiroltourismus/public/images/magazin")

WATERCOLOR = "Watercolor painting, soft washes, paper texture, loose brush strokes, transparent colors, artistic painterly, beautiful composition"
NEG = "photo, comic, 3d, sharp lines, digital art, graphic, neon, overexposed, oversaturated, cartoon, illustration"

def log(m):
    sys.stdout.write(f"[{time.strftime('%H:%M:%S')}] {m}\n"); sys.stdout.flush()

# ─── Subject prompts per article topic ───
# Each article slug gets a specific scene to paint
SCENES = {
    "apres-ski-in-tirol-die-besten-adressen": [
        "Cozy alpine après-ski hut in snow at golden hour with warm glowing windows, mountain backdrop",
        "Skiers celebrating with drinks at a wooden mountain hut terrace, snow-covered peaks",
    ],
    "arlberg-das-ultimative-ski-paradies": [
        "Wide alpine panorama of Arlberg ski slopes with dramatic mountain peaks, fresh powder snow",
        "Ski lift ascending through snowy forest in the Arlberg region, soft winter light",
        "Cozy mountain lodge in St. Anton with warm lights against snowy evening landscape",
    ],
    "die-10-schoensten-wanderwege-tirols-fuer-einsteiger": [
        "Gentle alpine hiking trail through green meadows with wildflowers, easy mountain path",
        "Hikers on a well-marked trail with views of Tyrolean mountains, summer morning",
        "Alpine hut at the end of a hiking trail, panoramic mountain view, peaceful setting",
    ],
    "die-5-schoensten-almen-tirols": [
        "Traditional wooden alpine hut (Alm) on a green mountain pasture with grazing cows",
        "Alpine meadow with wildflowers and a rustic farmhouse, dramatic mountain backdrop",
        "Sunset over a Tyrolean Alm with wooden benches and flower boxes, serene mountains",
    ],
    "die-besten-huetten-in-tirol-zum-einkehren": [
        "Rustic wooden mountain hut with flower boxes, sunny terrace overlooking alpine valley",
        "Cozy interior of a Tyrolean hut with wooden tables, tiled stove, warm atmosphere",
    ],
    "die-besten-skigebiete-tirols-2026-im-vergleich": [
        "Ski slope carving through alpine forest with multiple ski lifts, winter sports panorama",
        "Cross-section comparison view of different ski areas, snowy peaks and valleys",
    ],
    "die-schoensten-bergseen-tirols-erfrischende-ziele": [
        "Crystal-clear alpine lake reflecting jagged mountain peaks, emerald water, summer scene",
        "Turquoise mountain lake surrounded by pine forest and rocky peaks, serene mirror reflection",
    ],
    "die-schoensten-freizeitparks-und-erlebnisbaeder-tirols": [
        "Family water park with slides surrounded by alpine scenery, outdoor pool with mountain view",
        "Adventure playground in Tyrolean landscape with climbing frames and green hills",
        "Indoor adventure pool complex with palm trees and water slides, tropical atmosphere",
    ],
    "die-schoensten-sehenswuerdigkeiten-in-tirol": [
        "Goldenes Dachl in Innsbruck with ornate golden balcony against alpine backdrop",
        "Swarovski Crystal Worlds with giant green head sculpture and water feature",
        "Historic Tyrolean castle on a hill with mountain panorama, medieval architecture",
    ],
    "events--festivals-in-tirol-2026-der-jahreskalender": [
        "Alpine music festival with outdoor stage and mountain backdrop, summer evening concert",
        "Traditional Tyrolean festival with people in dirndl and lederhosen, decorated village square",
        "Christmas market in a Tyrolean town square with wooden stalls and mountain backdrop",
    ],
    "familienurlaub-in-tirol-die-besten-tipps": [
        "Happy family hiking on an easy alpine trail, children exploring nature, summer mountains",
        "Family playing in a green alpine meadow with mountain panorama, picnic and laughter",
        "Children feeding farm animals at a Tyrolean Bauernhof, rustic barn and hay",
    ],
    "familienurlaub-tirol": [
        "Parents and children enjoying a sunny day at an alpine lake, swimming and paddling",
    ],
    "huettenwanderungen-in-tirol-von-alm-zu-alm": [
        "Mountain trail connecting two alpine huts, scenic ridge walk with valley views",
        "Hikers arriving at a rustic mountain hut after a long walk, sunset lighting",
    ],
    "innsbruck-city-guide": [
        "Innsbruck cityscape with colorful houses along the Inn river, Nordkette mountain wall behind",
    ],
    "innsbruck-entdecken-der-grosse-city-guide": [
        "Panorama of Innsbruck with golden roof, baroque architecture and surrounding alpine peaks",
        "Narrow street in Innsbruck old town with colorful facades and mountain view backdrop",
        "Bergisel ski jump against snowy alpine panorama, architectural landmark in Innsbruck",
    ],
    "kaunertal-gletscherski-und-wilde-natur": [
        "Kaunertal glacier ski slopes winding between crevasses, dramatic high-altitude landscape",
        "Wild alpine valley in Kaunertal with rugged peaks and untouched nature, summer view",
        "Gletscherstraße mountain road winding through Kaunertal valley, dramatic rock formations",
    ],
    "kitzbuehel-events": [
        "Kitzbühel town square with Hahnenkamm mountain backdrop, traditional Tyrolean buildings",
    ],
    "kulinarik-oetztal": [
        "Traditional Tyrolean food platter with speck, cheese, bread on wooden board, mountain view",
    ],
    "kulinarische-events-in-tirol-genussmessen--co": [
        "Gourmet food festival in Tyrolean setting, tasting plates and wine glasses on wooden table",
        "Cheese and wine tasting with alpine backdrop, culinary event atmosphere",
        "Farmers market in a Tyrolean village square with fresh local produce and mountain views",
    ],
    "kultur-innsbruck": [
        "Hofkirche and Imperial Palace in Innsbruck, Renaissance architecture, mountain backdrop",
    ],
    "kulturhighlights-in-innsbruck-goldenes-dachl--co": [
        "Goldenes Dachl with golden copper tiles in Innsbruck old town, detailed architecture view",
        "Ambras Castle on a hill above Innsbruck, Renaissance garden and mountain panorama",
        "Imperial Hofburg palace interior, baroque splendor, crystal chandeliers and frescoes",
    ],
    "oetztal-reisefuehrer-aktivurlaub-im-sueden-tirols": [
        "Ötztal valley panorama with green meadows and dramatic mountain walls, summer landscape",
        "Stuibenfall waterfall cascading down rocky cliff, surrounded by alpine forest",
        "Adventure sports in Ötztal: rafting or canyoning in crystal-clear mountain stream",
    ],
    "ski-fahren-mit-familie-in-tirol-kinderfreundliche-gebiete": [
        "Children learning to ski on a gentle blue slope, colorful ski school group, sunny day",
        "Family ski fun park with snow tubes and easy lifts, children laughing in snow",
        "Ski instructor helping a child on skis, wide beginner slope with mountain panorama",
    ],
    "skifahren-arlberg": [
        "Skiers carving through fresh powder on Arlberg slopes, deep snow and winter sun",
    ],
    "skifahren-kaunertal": [
        "Solitary skier on Kaunertal glacier slope, endless white landscape, blue sky",
    ],
    "skiurlaub-in-tirol-alles-von-vorbereitung-bis-abfahrt": [
        "Complete ski equipment arranged on snow: boots, skis, poles, helmet, goggles",
        "Ski slope winding through alpine forest with panoramic mountain views, action scene",
        "Cozy ski resort village in evening, illuminated slopes and warm chalet lights",
    ],
    "sommerurlaub-in-tirol-was-tun-bei-regen": [
        "Indoor swimming pool with large windows showing rainy mountains, family having fun",
        "Museum or cultural building in Tyrolean town, art and history on a rainy day",
        "Cozy café interior with umbrella stand, rain on windows, warm drinks and cake",
    ],
    "stubaital-familien": [
        "Family hiking in Stubaital valley with wildflowers and sparkling mountain streams",
    ],
    "tiere-und-natur-in-tirol-alpenzoo-bauernhoefe--co": [
        "Alpenzoo Innsbruck with alpine animals in natural enclosures, mountain backdrop",
        "Farm animals on a Tyrolean Bauernhof: cows, chickens, goats in sunny barnyard",
        "Wild ibex on a rocky mountain ridge, alpine wildlife in natural habitat",
    ],
    "tiroler-kueche-traditionelle-gerichte--spezialitaeten": [
        "Traditional Tyrolean dish: Käsespätzle in a hot pan with golden cheese crust",
        "Assortment of Tyrolean delicacies: speck, cheese bread, strudel on rustic table",
    ],
    "tiroler-kueche-von-a-z-die-kulinarische-reise-durchs-land": [
        "Colorful spread of Tyrolean culinary specialties arranged on traditional wooden table",
        "Apfelstrudel with vanilla sauce on a checkered tablecloth, café atmosphere",
        "Tyrolean wine grapes on vine with alpine valley in background, vineyard terrace",
    ],
    "tiroler-kulinarik": [
        "Kaiserschmarrn with powdered sugar and plum compote on rustic wooden table",
    ],
    "wandern-in-tirol-der-ultimative-guide-fuer-alle-levels": [
        "Wide alpine hiking trail through blooming mountain meadow with dramatic peak backdrop",
        "Hikers on a ridge trail with spectacular valley views, summer alpine flowers",
        "Alpine mountain lake reflection of surrounding peaks, hikers resting by shore",
    ],
    "wandern-mit-kindern-in-tirol-familienfreundliche-touren": [
        "Children walking on a forest trail with mountain views, holding walking sticks",
        "Family crossing a wooden bridge over a mountain stream, alpine adventure together",
        "Kids playing in a mountain meadow with wildflowers, parents watching, scenic valley",
    ],
    "wanderparadies-zillertal": [
        "Zillertal hiking trail through green valley with traditional farmhouses and mountain peaks",
    ],
    "wanderwege-oetztal": [
        "Mountain trail winding through Ötztal valley with views of glacier peaks",
    ],
    "weinbau-in-tirol-suedliche-haenge-edle-tropfen": [
        "South-facing Tyrolean vineyard terrace with alpine backdrop, ripe grapes in autumn",
        "Winemaker holding grapes in a Tyrolean vineyard, harvest scene with mountains",
        "Wine cellar tasting room with oak barrels and mountain view through window",
    ],
    "wellness-in-tirol-die-besten-adressen-fuer-erholungssuchende": [
        "Luxury spa pool with panoramic mountain views, steaming water and candles",
        "Sauna building overlooking alpine valley, wooden architecture, relaxation area",
        "Couple enjoying massage treatment in mountain-view wellness suite, peaceful setting",
    ],
    "wellness-in-tirol-die-besten-thermen--spa-resorts": [
        "Thermal outdoor pool with steam rising into cold alpine air, mountain panorama",
        "Spa treatment room with natural stone, candles and view of alpine forest",
        "Relaxation lounge with mountain view, cozy blankets and herbal tea, tranquil scene",
    ],
    "wellness-thermen-tirol": [
        "Natural thermal springs in alpine setting, steam and warm water, winter landscape",
    ],
    "winterurlaub-in-tirol-was-muss-man-wissen": [
        "Winter wonderland scene: snow-covered Tyrolean village with church spire and lights",
        "Activities in snow: snowshoeing through quiet winter forest, pristine snow landscape",
    ],
    "winterurlaub-tirol": [
        "Snow-covered Tyrolean mountain village at twilight, warm-lit windows, winter forests",
        "Family playing in deep snow, building snowman, winter fun in alpine setting",
    ],
    "zillertal-reisefuehrer-tal-der-vielfalt": [
        "Zillertal valley panorama with traditional farms, green pastures and mountain backdrop",
        "Zillertal Arena ski slopes with modern lifts, winter sports paradise in wide valley",
        "Schlegeis alpine reservoir turquoise water surrounded by dramatic 3000m peaks",
    ],
}

# ─── Load all article data ───
def load_articles():
    arts = []
    for d in sorted(MAGAZIN.iterdir()):
        if not d.is_dir(): continue
        idx = d / "index.json"
        if not idx.exists(): continue
        data = json.loads(idx.read_text(encoding='utf-8'))
        slug = data.get("slug", d.name)
        titel = data.get("titel", d.name)
        inhalt = data.get("inhalt", "")
        if isinstance(inhalt, list):
            text_len = sum(len(str(item.get("text", item.get("content", "")))) for item in inhalt if isinstance(item, dict))
        else:
            text_len = len(str(inhalt))
        img_count = 1
        if text_len > 4000: img_count = 3
        elif text_len > 2000: img_count = 2
        arts.append({"slug": slug, "titel": titel, "len": text_len, "imgs": img_count, "path": d, "data": data})
    return arts

def main():
    log("Loading SDXL...")
    REQUESTS_CA_BUNDLE = "C:/HermesPortable/venv/Lib/site-packages/certifi/cacert.pem"
    pipe = StableDiffusionXLPipeline.from_single_file(str(MODEL), torch_dtype=torch.float16)
    pipe.to("cuda")
    pipe.vae.enable_slicing()
    log(f"Loaded. VRAM: {torch.cuda.memory_allocated()/1024**3:.1f} GB")

    arts = load_articles()
    total_imgs = sum(a["imgs"] for a in arts)
    done = 0
    log(f"Total articles: {len(arts)}, total images needed: {total_imgs}")

    for art in arts:
        slug = art["slug"]
        scenes = SCENES.get(slug)
        if not scenes:
            # Generic fallback prompt based on title
            scenes = [f"Beautiful Tyrolean landscape in watercolor style, alpine scenery, {art['titel'].split('–')[0].strip()[:60]}"]
        
        # How many images to generate for this article
        wanted = art["imgs"]
        # Pad or truncate scenes
        while len(scenes) < wanted:
            scenes.append(scenes[0])
        scenes = scenes[:wanted]
        
        out_dir = OUT_BASE / slug
        out_dir.mkdir(parents=True, exist_ok=True)
        
        # Generate each image
        img_data = []
        for i, scene in enumerate(scenes):
            out_path = out_dir / f"hero_{i+1}.png"
            if out_path.exists():
                log(f"  ⏭ SKIP {slug}/hero_{i+1}.png (exists)")
                img_data.append({"url": f"/images/magazin/{slug}/hero_{i+1}.png", "alt": f"{art['titel']} - Szene {i+1}"})
                done += 1
                continue

            prompt = f"{scene}. {WATERCOLOR}"
            log(f"[{done+1}/{total_imgs}] {slug}/hero_{i+1}...")
            
            gen = torch.Generator(device="cuda").manual_seed(42 + i + (hash(slug) % 10000))
            img = pipe(
                prompt=prompt, negative_prompt=NEG,
                height=1024, width=1024,
                guidance_scale=7.0, num_inference_steps=25, generator=gen,
            ).images[0]
            img.save(out_path)
            img_data.append({"url": f"/images/magazin/{slug}/hero_{i+1}.png", "alt": f"{art['titel']} - Szene {i+1}"})
            log(f"  ✓ ({out_path.stat().st_size/1024:.0f} KB)")
            done += 1
        
        # Update article's index.json
        data = art["data"]
        first_img = img_data[0]["url"] if img_data else ""
        data["hero_bild"] = first_img
        data["bilder"] = img_data
        (art["path"] / "index.json").write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding='utf-8')
    
    log(f"\n✅ ALL DONE! {done}/{total_imgs} images generated/article data updated.")

if __name__ == "__main__":
    main()
