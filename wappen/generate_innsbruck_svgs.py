#!/usr/bin/env python3
"""Generate the Innsbruck city coat of arms in 3 different SVG styles."""
import os

OUT_DIR = 'img/generiert'
os.makedirs(OUT_DIR, exist_ok=True)

# ============================================================
# STYLE 1: Klassisch-Heraldisch (traditionell)
# ============================================================
style1 = '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 400 460" width="400" height="460">
  <defs>
    <pattern id="dach1" patternUnits="userSpaceOnUse" width="8" height="8">
      <rect width="8" height="8" fill="#e8e0d0"/>
      <path d="M0 2h3v3H0zM4 5h3v3H4z" fill="#c0b8a0"/>
      <path d="M2 0h1v2H2zM6 3h1v2H6zM1 4h1v2H1zM5 7h1v2H5z" fill="#d0c8b0"/>
    </pattern>
    <pattern id="fenster1" patternUnits="userSpaceOnUse" width="6" height="6">
      <rect width="6" height="6" fill="#1a1a2e"/>
      <circle cx="1.5" cy="1.5" r="0.5" fill="#3a3a5e"/>
      <circle cx="4.5" cy="1.5" r="0.5" fill="#3a3a5e"/>
      <circle cx="1.5" cy="4.5" r="0.5" fill="#3a3a5e"/>
      <circle cx="4.5" cy="4.5" r="0.5" fill="#3a3a5e"/>
    </pattern>
    <pattern id="bruecke1" patternUnits="userSpaceOnUse" width="10" height="14">
      <rect width="10" height="14" fill="#d8d0c0"/>
      <rect x="0" y="0" width="3" height="14" fill="#c0b8a0"/>
      <rect x="7" y="0" width="3" height="14" fill="#c0b8a0"/>
    </pattern>
  </defs>

  <!-- Schatten -->
  <ellipse cx="200" cy="240" rx="165" ry="210" fill="rgba(0,0,0,0.08)"/>

  <!-- Äußerer schwarzer Rand -->
  <path d="M200 20 Q310 30 350 160 Q370 230 320 380 Q280 450 200 450 Q120 450 80 380 Q30 230 50 160 Q90 30 200 20Z" fill="#1a1a1a"/>

  <!-- Innerer roter Schild (leicht verkleinert für Rand) -->
  <path d="M200 35 Q305 45 340 165 Q360 230 312 372 Q276 438 200 438 Q124 438 88 372 Q40 230 60 165 Q95 45 200 35Z" fill="#C8102E"/>

  <!-- Linker Turm -->
  <g transform="translate(95, 140)">
    <rect x="0" y="0" width="60" height="130" fill="url(#dach1)" stroke="#1a1a1a" stroke-width="2"/>
    <!-- Dach -->
    <polygon points="-8,0 30,-50 68,0" fill="url(#dach1)" stroke="#1a1a1a" stroke-width="2"/>
    <!-- First -->
    <line x1="30" y1="-50" x2="30" y2="0" stroke="#1a1a1a" stroke-width="1.5"/>
    <!-- Dachziegelmuster -->
    <line x1="8" y1="-10" x2="52" y2="-10" stroke="#8a8070" stroke-width="0.5" opacity="0.5"/>
    <line x1="14" y1="-20" x2="46" y2="-20" stroke="#8a8070" stroke-width="0.5" opacity="0.5"/>
    <line x1="19" y1="-30" x2="41" y2="-30" stroke="#8a8070" stroke-width="0.5" opacity="0.5"/>
    <!-- Fenster -->
    <rect x="15" y="40" width="30" height="35" fill="url(#fenster1)" stroke="#1a1a1a" stroke-width="2"/>
    <!-- Fensterkreuz -->
    <line x1="30" y1="40" x2="30" y2="75" stroke="#1a1a1a" stroke-width="1.5"/>
    <line x1="15" y1="57" x2="45" y2="57" stroke="#1a1a1a" stroke-width="1.5"/>
  </g>

  <!-- Rechter Turm (gespiegelt) -->
  <g transform="translate(245, 140)">
    <rect x="0" y="0" width="60" height="130" fill="url(#dach1)" stroke="#1a1a1a" stroke-width="2"/>
    <polygon points="-8,0 30,-50 68,0" fill="url(#dach1)" stroke="#1a1a1a" stroke-width="2"/>
    <line x1="30" y1="-50" x2="30" y2="0" stroke="#1a1a1a" stroke-width="1.5"/>
    <line x1="8" y1="-10" x2="52" y2="-10" stroke="#8a8070" stroke-width="0.5" opacity="0.5"/>
    <line x1="14" y1="-20" x2="46" y2="-20" stroke="#8a8070" stroke-width="0.5" opacity="0.5"/>
    <line x1="19" y1="-30" x2="41" y2="-30" stroke="#8a8070" stroke-width="0.5" opacity="0.5"/>
    <rect x="15" y="40" width="30" height="35" fill="url(#fenster1)" stroke="#1a1a1a" stroke-width="2"/>
    <line x1="30" y1="40" x2="30" y2="75" stroke="#1a1a1a" stroke-width="1.5"/>
    <line x1="15" y1="57" x2="45" y2="57" stroke="#1a1a1a" stroke-width="1.5"/>
  </g>

  <!-- Brücke -->
  <g transform="translate(155, 240)">
    <rect x="0" y="0" width="90" height="40" fill="url(#bruecke1)" stroke="#1a1a1a" stroke-width="2"/>
    <!-- Brückenbalken -->
    <rect x="0" y="0" width="8" height="40" fill="#c8c0b0" stroke="#1a1a1a" stroke-width="1"/>
    <rect x="12" y="0" width="8" height="40" fill="#c8c0b0" stroke="#1a1a1a" stroke-width="1"/>
    <rect x="24" y="0" width="8" height="40" fill="#c8c0b0" stroke="#1a1a1a" stroke-width="1"/>
    <rect x="36" y="0" width="8" height="40" fill="#c8c0b0" stroke="#1a1a1a" stroke-width="1"/>
    <rect x="48" y="0" width="8" height="40" fill="#c8c0b0" stroke="#1a1a1a" stroke-width="1"/>
    <rect x="60" y="0" width="8" height="40" fill="#c8c0b0" stroke="#1a1a1a" stroke-width="1"/>
    <rect x="72" y="0" width="8" height="40" fill="#c8c0b0" stroke="#1a1a1a" stroke-width="1"/>
    <!-- Horizontale Träger -->
    <rect x="0" y="10" width="90" height="4" fill="#b0a898" stroke="#1a1a1a" stroke-width="0.5"/>
    <rect x="0" y="26" width="90" height="4" fill="#b0a898" stroke="#1a1a1a" stroke-width="0.5"/>
    <!-- Brückengeländer -->
    <rect x="0" y="0" width="90" height="3" fill="#a09888" stroke="#1a1a1a" stroke-width="0.5"/>
    <rect x="0" y="37" width="90" height="3" fill="#a09888" stroke="#1a1a1a" stroke-width="0.5"/>
  </g>

  <!-- Bogen unter Brücke -->
  <path d="M155 280 Q200 310 245 280" fill="none" stroke="#1a1a1a" stroke-width="2"/>

  <!-- Bodenlinie -->
  <path d="M100 290 Q200 300 300 290" fill="none" stroke="#1a1a1a" stroke-width="1.5"/>
</svg>'''

# ============================================================
# STYLE 2: Modern-Minimalistisch (flaches Design)
# ============================================================
style2 = '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 400 460" width="400" height="460">
  <defs>
    <linearGradient id="redGrad" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0%" stop-color="#E83939"/>
      <stop offset="100%" stop-color="#B01818"/>
    </linearGradient>
    <linearGradient id="silverGrad" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0%" stop-color="#FFFFFF"/>
      <stop offset="100%" stop-color="#D4D4D8"/>
    </linearGradient>
  </defs>

  <!-- Runderes, modernes Schild -->
  <path d="M200 30 Q320 30 355 160 Q375 260 330 380 Q290 445 200 445 Q110 445 70 380 Q25 260 45 160 Q80 30 200 30Z" 
        fill="url(#redGrad)" stroke="#18181B" stroke-width="4" stroke-linejoin="round"/>

  <!-- Innerer weisser Rahmen (modern) -->
  <path d="M200 42 Q313 42 345 162 Q363 256 321 372 Q283 434 200 434 Q117 434 79 372 Q37 256 55 162 Q87 42 200 42Z" 
        fill="none" stroke="#E4E4E7" stroke-width="1.5" stroke-dasharray="4,3" opacity="0.3"/>

  <!-- Linker Turm (modern, geometrisch) -->
  <g transform="translate(100, 150)">
    <!-- Turmkörper -->
    <rect x="0" y="0" width="55" height="120" rx="2" fill="url(#silverGrad)" stroke="#18181B" stroke-width="2.5"/>
    <!-- Modernes Dach -->
    <polygon points="-5,0 27.5,-55 60,0" fill="#18181B" stroke="#18181B" stroke-width="2" stroke-linejoin="round"/>
    <!-- Fenster (rund, modern) -->
    <circle cx="27.5" cy="55" r="14" fill="#18181B" stroke="#18181B" stroke-width="2"/>
    <circle cx="27.5" cy="55" r="10" fill="url(#redGrad)"/>
    <!-- Linie -->
    <line x1="0" y1="90" x2="55" y2="90" stroke="#18181B" stroke-width="1.5" opacity="0.4"/>
  </g>

  <!-- Rechter Turm -->
  <g transform="translate(245, 150)">
    <rect x="0" y="0" width="55" height="120" rx="2" fill="url(#silverGrad)" stroke="#18181B" stroke-width="2.5"/>
    <polygon points="-5,0 27.5,-55 60,0" fill="#18181B" stroke="#18181B" stroke-width="2" stroke-linejoin="round"/>
    <circle cx="27.5" cy="55" r="14" fill="#18181B" stroke="#18181B" stroke-width="2"/>
    <circle cx="27.5" cy="55" r="10" fill="url(#redGrad)"/>
    <line x1="0" y1="90" x2="55" y2="90" stroke="#18181B" stroke-width="1.5" opacity="0.4"/>
  </g>

  <!-- Brücke (modern, minimal) -->
  <g transform="translate(157, 245)">
    <rect x="0" y="0" width="86" height="35" rx="1" fill="url(#silverGrad)" stroke="#18181B" stroke-width="2.5"/>
    <!-- Moderne Brückenstreben -->
    <rect x="2" y="4" width="10" height="27" rx="1" fill="#F4F4F5" stroke="#18181B" stroke-width="1.5"/>
    <rect x="18" y="4" width="10" height="27" rx="1" fill="#F4F4F5" stroke="#18181B" stroke-width="1.5"/>
    <rect x="34" y="4" width="10" height="27" rx="1" fill="#F4F4F5" stroke="#18181B" stroke-width="1.5"/>
    <rect x="50" y="4" width="10" height="27" rx="1" fill="#F4F4F5" stroke="#18181B" stroke-width="1.5"/>
    <rect x="66" y="4" width="10" height="27" rx="1" fill="#F4F4F5" stroke="#18181B" stroke-width="1.5"/>
    <!-- Horizontale Linie -->
    <line x1="0" y1="17" x2="86" y2="17" stroke="#18181B" stroke-width="1.5" opacity="0.5"/>
  </g>

  <!-- Minimaler Bogen -->
  <path d="M157 280 Q200 305 243 280" fill="none" stroke="#18181B" stroke-width="2.5" stroke-linecap="round"/>
</svg>'''

# ============================================================
# STYLE 3: Mittelalterlich-Holzschnitt (rustikal)
# ============================================================
style3 = '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 400 460" width="400" height="460">
  <defs>
    <filter id="rough">
      <feTurbulence type="turbulence" baseFrequency="0.04" numOctaves="4" result="turbulence"/>
      <feDisplacementMap in="SourceGraphic" in2="turbulence" scale="3" xChannelSelector="R" yChannelSelector="G"/>
    </filter>
    <filter id="woodgrain">
      <feTurbulence type="fractalNoise" baseFrequency="0.02 0.15" numOctaves="3" result="noise"/>
      <feColorMatrix type="saturate" values="0" in="noise" result="gray"/>
      <feBlend in="SourceGraphic" in2="gray" mode="multiply"/>
    </filter>
    <pattern id="wood" patternUnits="userSpaceOnUse" width="20" height="20">
      <rect width="20" height="20" fill="#F5E6CA"/>
      <line x1="0" y1="5" x2="20" y2="5" stroke="#DCC8A8" stroke-width="0.5" opacity="0.4"/>
      <line x1="0" y1="12" x2="20" y2="12" stroke="#DCC8A8" stroke-width="0.3" opacity="0.3"/>
      <line x1="0" y1="18" x2="20" y2="18" stroke="#DCC8A8" stroke-width="0.4" opacity="0.2"/>
    </pattern>
  </defs>

  <!-- Pergament-Hintergrund -->
  <rect width="400" height="460" fill="#F5E6CA"/>
  <rect width="400" height="460" fill="url(#wood)" opacity="0.3"/>

  <!-- Schild (Holzschnitt-Stil) -->
  <path d="M200 25 Q315 35 352 165 Q372 235 328 380 Q288 448 200 448 Q112 448 72 380 Q28 235 48 165 Q85 35 200 25Z" 
        fill="#C83030" stroke="#2a1a0a" stroke-width="5"/>
  <!-- Schattenschraffur Schild -->
  <path d="M200 25 Q315 35 352 165 Q372 235 328 380 Q288 448 200 448 Q112 448 72 380 Q28 235 48 165 Q85 35 200 25Z" 
        fill="none" stroke="#8a1a1a" stroke-width="2" stroke-dasharray="3,6" opacity="0.3"/>

  <!-- Schraffur Schildhintergrund (Holzschnitt-Linien) -->
  <g opacity="0.12" stroke="#2a1a0a" stroke-width="0.8">
    <line x1="80" y1="100" x2="80" y2="400"/>
    <line x1="100" y1="80" x2="100" y2="420"/>
    <line x1="120" y1="70" x2="120" y2="430"/>
    <line x1="140" y1="60" x2="140" y2="440"/>
    <line x1="160" y1="55" x2="160" y2="445"/>
    <line x1="180" y1="50" x2="180" y2="448"/>
    <line x1="200" y1="48" x2="200" y2="448"/>
    <line x1="220" y1="50" x2="220" y2="448"/>
    <line x1="240" y1="55" x2="240" y2="445"/>
    <line x1="260" y1="60" x2="260" y2="440"/>
    <line x1="280" y1="70" x2="280" y2="430"/>
    <line x1="300" y1="80" x2="300" y2="420"/>
    <line x1="320" y1="100" x2="320" y2="400"/>
  </g>

  <!-- Linker Turm (Holzschnitt) -->
  <g transform="translate(90, 145)" filter="url(#rough)">
    <rect x="0" y="0" width="65" height="125" fill="#F0E6D0" stroke="#2a1a0a" stroke-width="3.5"/>
    <!-- Dach -->
    <polygon points="-10,0 32.5,-55 75,0" fill="#2a1a0a" stroke="#2a1a0a" stroke-width="2"/>
    <!-- Dachschraffur -->
    <g stroke="#F0E6D0" stroke-width="1.2" opacity="0.30">
      <line x1="12" y1="-10" x2="53" y2="-10"/>
      <line x1="17" y1="-20" x2="48" y2="-20"/>
      <line x1="22" y1="-30" x2="43" y2="-30"/>
      <line x1="26" y1="-40" x2="39" y2="-40"/>
    </g>
    <!-- Mauerwerk-Andeutung -->
    <g stroke="#2a1a0a" stroke-width="1" opacity="0.25">
      <line x1="0" y1="20" x2="65" y2="20"/>
      <line x1="0" y1="40" x2="65" y2="40"/>
      <line x1="0" y1="60" x2="65" y2="60"/>
      <line x1="0" y1="80" x2="65" y2="80"/>
      <line x1="0" y1="100" x2="65" y2="100"/>
      <line x1="0" y1="120" x2="65" y2="120"/>
      <!-- Vertikale Fugen -->
      <line x1="22" y1="20" x2="22" y2="40"/>
      <line x1="44" y1="0" x2="44" y2="20"/>
      <line x1="22" y1="60" x2="22" y2="80"/>
      <line x1="44" y1="60" x2="44" y2="80"/>
    </g>
    <!-- Fenster -->
    <rect x="15" y="45" width="35" height="40" fill="#1a0a00" stroke="#2a1a0a" stroke-width="3"/>
    <!-- Fensterkreuz -->
    <line x1="32" y1="45" x2="32" y2="85" stroke="#F0E6D0" stroke-width="2.5"/>
    <line x1="15" y1="65" x2="50" y2="65" stroke="#F0E6D0" stroke-width="2.5"/>
  </g>

  <!-- Rechter Turm -->
  <g transform="translate(245, 145)" filter="url(#rough)">
    <rect x="0" y="0" width="65" height="125" fill="#F0E6D0" stroke="#2a1a0a" stroke-width="3.5"/>
    <polygon points="-10,0 32.5,-55 75,0" fill="#2a1a0a" stroke="#2a1a0a" stroke-width="2"/>
    <g stroke="#F0E6D0" stroke-width="1.2" opacity="0.30">
      <line x1="12" y1="-10" x2="53" y2="-10"/>
      <line x1="17" y1="-20" x2="48" y2="-20"/>
      <line x1="22" y1="-30" x2="43" y2="-30"/>
      <line x1="26" y1="-40" x2="39" y2="-40"/>
    </g>
    <g stroke="#2a1a0a" stroke-width="1" opacity="0.25">
      <line x1="0" y1="20" x2="65" y2="20"/>
      <line x1="0" y1="40" x2="65" y2="40"/>
      <line x1="0" y1="60" x2="65" y2="60"/>
      <line x1="0" y1="80" x2="65" y2="80"/>
      <line x1="0" y1="100" x2="65" y2="100"/>
      <line x1="0" y1="120" x2="65" y2="120"/>
      <line x1="22" y1="20" x2="22" y2="40"/>
      <line x1="44" y1="0" x2="44" y2="20"/>
      <line x1="22" y1="60" x2="22" y2="80"/>
      <line x1="44" y1="60" x2="44" y2="80"/>
    </g>
    <rect x="15" y="45" width="35" height="40" fill="#1a0a00" stroke="#2a1a0a" stroke-width="3"/>
    <line x1="32" y1="45" x2="32" y2="85" stroke="#F0E6D0" stroke-width="2.5"/>
    <line x1="15" y1="65" x2="50" y2="65" stroke="#F0E6D0" stroke-width="2.5"/>
  </g>

  <!-- Brücke (Holzschnitt) -->
  <g transform="translate(152, 243)" filter="url(#rough)">
    <rect x="0" y="0" width="96" height="40" fill="#E8DCC4" stroke="#2a1a0a" stroke-width="3"/>
    <!-- Balken -->
    <rect x="2" y="2" width="9" height="36" fill="#DCC8A8" stroke="#2a1a0a" stroke-width="1.5"/>
    <rect x="14" y="2" width="9" height="36" fill="#DCC8A8" stroke="#2a1a0a" stroke-width="1.5"/>
    <rect x="26" y="2" width="9" height="36" fill="#DCC8A8" stroke="#2a1a0a" stroke-width="1.5"/>
    <rect x="38" y="2" width="9" height="36" fill="#DCC8A8" stroke="#2a1a0a" stroke-width="1.5"/>
    <rect x="50" y="2" width="9" height="36" fill="#DCC8A8" stroke="#2a1a0a" stroke-width="1.5"/>
    <rect x="62" y="2" width="9" height="36" fill="#DCC8A8" stroke="#2a1a0a" stroke-width="1.5"/>
    <rect x="74" y="2" width="9" height="36" fill="#DCC8A8" stroke="#2a1a0a" stroke-width="1.5"/>
    <rect x="86" y="2" width="9" height="36" fill="#DCC8A8" stroke="#2a1a0a" stroke-width="1.5"/>
    <!-- Querbalken -->
    <rect x="0" y="8" width="96" height="4" fill="#C8B898" stroke="#2a1a0a" stroke-width="0.8"/>
    <rect x="0" y="28" width="96" height="4" fill="#C8B898" stroke="#2a1a0a" stroke-width="0.8"/>
  </g>

  <!-- Bogen (handgezeichnet) -->
  <path d="M152 283 Q200 312 248 283" fill="none" stroke="#2a1a0a" stroke-width="3.5" stroke-linecap="round"/>

  <!-- Verzierungen (Blattranken) -->
  <g stroke="#2a1a0a" stroke-width="1.5" fill="none" opacity="0.6">
    <!-- Linke Ranke -->
    <path d="M60 200 Q45 220 55 250 Q48 260 55 270" stroke-linecap="round"/>
    <ellipse cx="50" cy="240" rx="4" ry="6" transform="rotate(-20 50 240)" fill="#2a1a0a" opacity="0.4"/>
    <!-- Rechte Ranke -->
    <path d="M340 200 Q355 220 345 250 Q352 260 345 270" stroke-linecap="round"/>
    <ellipse cx="350" cy="240" rx="4" ry="6" transform="rotate(20 350 240)" fill="#2a1a0a" opacity="0.4"/>
  </g>

  <!-- Boden (Gras/Hügel) -->
  <path d="M80 380 Q140 360 200 370 Q260 360 320 380" fill="none" stroke="#2a1a0a" stroke-width="2.5" stroke-linecap="round"/>
  <g stroke="#2a1a0a" stroke-width="1.2" fill="none" opacity="0.4">
    <line x1="120" y1="375" x2="130" y2="365"/>
    <line x1="140" y1="370" x2="148" y2="358"/>
    <line x1="260" y1="370" x2="252" y2="358"/>
    <line x1="280" y1="375" x2="270" y2="365"/>
  </g>
</svg>'''

# Write files
files = {
    'wappen_innsbruck_klassisch.svg': style1,
    'wappen_innsbruck_modern.svg': style2,
    'wappen_innsbruck_holzschnitt.svg': style3,
}

for name, content in files.items():
    path = os.path.join(OUT_DIR, name)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"✅ {path} ({len(content)} bytes)")

print("\nAlle 3 Stile generiert!")
