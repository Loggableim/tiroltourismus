# Batch 1a: Generate beschreibung for first 500 gastro entries
# Uses text-based replacement to preserve HTML tags in JSON values

$gastroDir = "F:\tiroltourismus\src\data\gastro"
$batchList = Get-Content "F:\tiroltourismus\gastro_batch1a.txt"
$totalProcessed = 0

# Region display names
$regionNames = @{
    "innsbruck" = "Innsbruck"
    "innsbruck-land" = "Innsbruck Land"
    "kitzbuehel" = "Kitzbühel"
    "kufstein" = "Kufstein"
    "zillertal" = "Zillertal"
    "ausserfern" = "Außerfern"
    "landeck" = "Landeck"
    "imst" = "Imst"
    "arlberg" = "Arlberg"
    "stubaital" = "Stubaital"
    "oetztal" = "Ötztal"
    "achensee" = "Achensee"
    "kaunertal" = "Kaunertal"
    "osttirol" = "Osttirol"
    "schwaz" = "Schwaz"
    "?" = "Tirol"
}

function Get-RegionDisplay {
    param($region)
    if ($regionNames.ContainsKey($region)) { return $regionNames[$region] }
    return $region
}

function Generate-Description {
    param($name, $kategorie, $ort, $region, $preis)
    
    $regionDisplay = Get-RegionDisplay -region $region
    $location = if (![string]::IsNullOrEmpty($ort)) { $ort } else { $regionDisplay }
    $escapedName = $name -replace "'", "&apos;" -replace '"', '&quot;'
    
    switch ($kategorie) {
        "restaurant" {
            $desc = "<p>Das <strong>$escapedName</strong> in $location ist ein beliebtes Restaurant, das seine Gäste mit einer vielfältigen Speisekarte und regionaler Gastlichkeit verwöhnt. Das Ambiente vereint traditionelle tirolerische Elemente mit modernem Komfort und schafft eine einladende Atmosphäre für jeden Anlass."
            $desc += " Die Speisekarte bietet eine sorgfältige Auswahl an Gerichten – von klassischen Tiroler Spezialitäten wie Tiroler Gröstl und Kaiserschmarrn bis hin zu internationalen Klassikern. Besonderen Wert legt das Team auf die Verwendung frischer, regionaler Zutaten aus der Umgebung."
            $desc += " Ob ein gemütliches Abendessen zu zweit, eine Feier im Familienkreis oder ein geschäftliches Treffen – das <strong>$escapedName</strong> heißt Sie herzlich willkommen und sorgt mit seinem aufmerksamen Service für einen rundum gelungenen Aufenthalt.</p>"
        }
        "cafe" {
            $desc = "<p>Das <strong>$escapedName</strong> in $location ist ein einladendes Café, das mit seinem gemütlichen Ambiente und einer feinen Auswahl an Kaffeespezialitäten, hausgemachten Kuchen und süßen Versuchungen begeistert. Hier können Gäste den Alltag hinter sich lassen und bei einer Tasse aromatischem Kaffee oder einem cremigen Cappuccino entspannen."
            $desc += " Das Angebot umfasst Frühstücksvariationen, leichte Snacks und täglich frische Mehlspeisen – von der klassischen Sachertorte bis zum saftigen Apfelstrudel. Die freundliche Bedienung und das wohnliche Interieur laden zum Verweilen und Genießen ein."
            $desc += " Ob für einen entspannten Start in den Tag, eine gemütliche Kaffeepause am Nachmittag oder einen Plausch mit Freunden – das <strong>$escapedName</strong> ist der ideale Ort für Genuss und Geselligkeit in $location.</p>"
        }
        "bar" {
            $desc = "<p>Das <strong>$escapedName</strong> in $location ist eine stilvolle Bar, die mit einer einladenden Atmosphäre und einer erlesenen Getränkekarte begeistert. Ob klassische Cocktails, edle Weine oder regionale Biere – hier findet jeder Gast das passende Getränk für den perfekten Abend."
            $desc += " Das Interieur verbindet modernes Design mit gemütlichen Elementen und schafft eine Wohlfühlatmosphäre, die zum Verweilen einlädt. Die erfahrenen Barkeeper mixen auf Wunsch auch gerne kreative Signature-Drinks, die man so nur hier findet."
            $desc += " Ob After-Work-Treff, gemütlicher Abend mit Freunden oder der Start in eine lange Nacht – das <strong>$escapedName</strong> bietet den idealen Rahmen für gesellige Stunden in $location.</p>"
        }
        "pub" {
            $desc = "<p>Das <strong>$escapedName</strong> in $location ist ein uriger Pub mit authentischem Ambiente und einer herzlichen Willkommenskultur. Hier treffen sich Einheimische und Gäste gleichermaßen, um bei einem kühlen Bier oder einem edlen Tropfen den Abend zu genießen."
            $desc += " Die Speisekarte bietet klassische Pub-Spezialitäten und regionale Schmankerln, die frisch zubereitet serviert werden. Das rustikal-einladende Interieur mit gemütlichen Sitzplätzen schafft eine relaxte Atmosphäre, die zum Verweilen einlädt."
            $desc += " Ob für einen Feierabend-Drink, ein gemütliches Beisammensein mit Freunden oder um einfach nur das bunte Treiben zu genießen – das <strong>$escapedName</strong> ist die erste Adresse für gesellige Stunden in $location.</p>"
        }
        "imbiss" {
            $desc = "<p>Das <strong>$escapedName</strong> in $location ist der perfekte Ort für eine schnelle, aber köstliche Stärkung zwischendurch. Mit einer abwechslungsreichen Auswahl an warmen und kalten Snacks, herzhaften Kleinigkeiten und süßen Leckereien kommt hier jeder auf seine Kosten."
            $desc += " Die Speisen werden mit viel Liebe zum Detail und frischen Zutaten zubereitet – ob herzhafte Wurstspezialitäten, knusprige Schnitzel im Brötchen oder vegetarische Optionen. Das freundliche Team sorgt für eine rasche Bedienung und ein Lächeln auf den Gesichtern der Gäste."
            $desc += " Ideal für eine Pause beim Erkunden der Region, einen schnellen Lunch oder einen kleinen Snack für unterwegs – das <strong>$escapedName</strong> bietet bodenständige Qualität zu fairen Preisen in $location.</p>"
        }
        "eiscafe" {
            $desc = "<p>Das <strong>$escapedName</strong> in $location ist ein beliebtes Eiscafé, das mit einer verführerischen Auswahl an cremigen Eisspezialitäten und erfrischenden Desserts begeistert. Hier genießen Gäste an sonnigen Tagen oder nach einem Ausflug in die Berge eine kühle Erfrischung in entspannter Atmosphäre."
            $desc += " Das Sortiment umfasst klassische Sorten wie Vanille, Schokolade und Erdbeere, aber auch ausgefallene Kreationen und saisonale Überraschungen. Dazu gibt es feine Kaffeespezialitäten, fruchtige Milchshakes und verführerische Eisbecher, die keine Wünsche offen lassen."
            $desc += " Ob eine kleine Auszeit zwischendurch, ein Eisbecher mit der Familie oder ein romantisches Date bei einem Affogato – das <strong>$escapedName</strong> ist der süße Treffpunkt in $location, der Groß und Klein begeistert.</p>"
        }
        "tirolerisch" {
            $desc = "<p>Das <strong>$escapedName</strong> in $location präsentiert die traditionelle Tiroler Küche in ihrer schönsten Form. Hier erleben Gäste authentische Gastlichkeit mit regionalen Spezialitäten, die nach überlieferten Familienrezepten zubereitet werden."
            $desc += " Auf der Speisekarte stehen Klassiker wie Tiroler Knödelvarianten, Schlutzkrapfen, Brettljause und natürlich ein würziger Tiroler Graukäse. Die Zutaten stammen von ausgewählten regionalen Produzenten, was den Gerichten ihren unverwechselbaren Charakter verleiht."
            $desc += " Das rustikal-einladende Ambiente mit Holzvertäfelung und traditionellem Dekor schafft eine behagliche Wirtshausatmosphäre. Das <strong>$escapedName</strong> in $location heißt seine Gäste mit tirolerischer Herzlichkeit willkommen.</p>"
        }
        "almwirtschaft" {
            $desc = "<p>Das <strong>$escapedName</strong> in $location ist eine urige Almwirtschaft, die mitten in der traumhaften Tiroler Bergkulisse liegt und authentische Almromantik pur bietet. Hier genießen Wanderer und Ausflugsgäste eine wohlverdiente Rast mit Blick auf die umliegenden Gipfel."
            $desc += " Die Speisekarte bietet bodenständige Almspezialitäten wie hausgemachten Kaiserschmarrn, würzigen Almkäse mit Brot und erfrischende Buttermilch – alles zubereitet mit Produkten der Almwirtschaft. Die einfache, aber feine Küche ist der Lohn für die Wanderung."
            $desc += " Die Sonnenterrasse lädt zum Verweilen ein, während das rustikale Innere an kühleren Tagen Schutz und Gemütlichkeit bietet. Das <strong>$escapedName</strong> ist ein Stück Tiroler Alpenkultur, das man erlebt haben muss.</p>"
        }
        "regional" {
            $desc = "<p>Das <strong>$escapedName</strong> in $location hat sich der regionalen Küche und den Produkten aus der Umgebung verschrieben. Das Konzept basiert auf kurzen Lieferwegen, saisonalen Zutaten und traditionellen Zubereitungsmethoden, die den natürlichen Geschmack bewahren."
            $desc += " Die wechselnde Speisekarte orientiert sich an dem, was die Jahreszeiten hergeben: Von frischen Kräutern und Gemüse im Sommer bis zu herzhaften Eintöpfen und Wildgerichten im Herbst und Winter. Jedes Gericht erzählt eine Geschichte der Region."
            $desc += " Das stilvoll-ländliche Ambiente unterstreicht den Fokus auf Nachhaltigkeit und Genuss. Das <strong>$escapedName</strong> in $location ist eine Entdeckung für alle, die ehrliche, schmackhafte Küche mit regionalem Charakter schätzen.</p>"
        }
        "international" {
            $desc = "<p>Das <strong>$escapedName</strong> in $location bringt internationale Küche nach Tirol und begeistert mit einer abwechslungsreichen Speisekarte voller Aromen aus aller Welt. Von mediterranen Klassikern über asiatische Spezialitäten bis hin zu kreativen Fusionsgerichten – hier wird Vielfalt großgeschrieben."
            $desc += " Die Gerichte werden mit hochwertigen Zutaten und viel Leidenschaft zubereitet, wobei auch regionale Produkte in die internationalen Rezepte einfließen. Das moderne, stilvolle Ambiente schafft eine einladende Atmosphäre für kulinarische Entdeckungsreisen."
            $desc += " Ob ein exotisches Abendessen, ein Lunch mit Freunden oder ein besonderes Dinner zu zweit – das <strong>$escapedName</strong> entführt Sie auf eine kulinarische Reise rund um den Globus.</p>"
        }
        "pizzeria" {
            $desc = "<p>Das <strong>$escapedName</strong> in $location ist die Adresse für echte italienische Pizzakunst. Hier werden knusprige Pizzen im traditionellen Holzofen gebacken und mit erlesenen Zutaten belegt. Der Duft von frisch gebackenem Teig und geschmolzenem Käse empfängt die Gäste bereits am Eingang."
            $desc += " Die Speisekarte bietet neben einer großen Auswahl an Pizzen auch hausgemachte Pasta, frische Insalate und köstliche Antipasti. Alle Gerichte werden mit viel Liebe zum Detail und nach original italienischen Rezepten zubereitet."
            $desc += " Das gemütlich-rustikale Ambiente und die herzliche Gastfreundschaft machen jeden Besuch zu einem kleinen Italien-Urlaub. Das <strong>$escapedName</strong> heißt Sie willkommen – Buon Appetito!</p>"
        }
        "eissalon" {
            $desc = "<p>Das <strong>$escapedName</strong> in $location verwöhnt seine Gäste mit einer großen Auswahl an hausgemachten Eisspezialitäten. In gemütlicher Atmosphäre können Gäste zwischen vielen klassischen und ausgefallenen Eissorten wählen."
            $desc += " Das Angebot umfasst cremige Eisbecher, erfrischende Milchshakes und feine Kaffeespezialitäten. Alle Eissorten werden mit hochwertigen Zutaten zubereitet und begeistern mit ihrem intensiven Geschmack."
            $desc += " Ein perfekter Ort für eine süße Auszeit in $location – ob an einem warmen Sommertag oder einfach so, weil Eis immer glücklich macht.</p>"
        }
        default {
            $desc = "<p>Das <strong>$escapedName</strong> in $location empfängt seine Gäste mit herzlicher Tiroler Gastfreundschaft und einer einladenden Atmosphäre. Das Haus bietet eine sorgfältige Auswahl an Speisen und Getränken, die mit frischen Zutaten zubereitet werden."
            $desc += " Der freundliche Service und das gemütliche Ambiente sorgen dafür, dass sich Gäste sofort wohlfühlen. Ob für einen kleinen Snack zwischendurch oder einen ausgedehnten Abend – das <strong>$escapedName</strong> ist stets eine gute Wahl."
            $desc += " In $location gelegen, lädt das <strong>$escapedName</strong> Einheimische und Besucher gleichermaßen dazu ein, die tirolerische Lebensart zu genießen und unvergessliche Momente zu erleben.</p>"
        }
    }
    
    return $desc
}

foreach ($dirName in $batchList) {
    $jsonPath = Join-Path $gastroDir $dirName "index.json"
    
    if (-not (Test-Path $jsonPath)) {
        Write-Warning "File not found: $jsonPath"
        continue
    }
    
    try {
        # Read file as text
        $content = Get-Content $jsonPath -Raw -Encoding UTF8
        
        # Parse JSON to get values
        $json = $content | ConvertFrom-Json
        
        $beschreibung = if ($json.PSObject.Properties.Name -contains 'beschreibung') { $json.beschreibung } else { $null }
        $len = if ([string]::IsNullOrEmpty($beschreibung)) { 0 } else { $beschreibung.Length }
        
        if ($len -ge 100) {
            Write-Output "SKIP $dirName - already has beschreibung ($len chars)"
            continue
        }
        
        $name = $json.name
        $kategorie = if ($json.PSObject.Properties.Name -contains 'kategorie') { $json.kategorie } else { "restaurant" }
        $ort = if ($json.PSObject.Properties.Name -contains 'ort') { $json.ort } else { "" }
        $region = if ($json.PSObject.Properties.Name -contains 'region') { $json.region } else { "?" }
        $preis = if ($json.PSObject.Properties.Name -contains 'preis') { $json.preis } else { "€€" }
        
        $newDescription = Generate-Description -name $name -kategorie $kategorie -ort $ort -region $region -preis $preis
        
        # Escape the description for JSON (handle quotes, backslashes, newlines)
        $escapedDesc = $newDescription -replace '\\', '\\' -replace '"', '\"' -replace "`n", '\n' -replace "`r", '\r' -replace "`t", '\t'
        
        # Use regex to replace the beschreibung field
        if ($content -match '"beschreibung"\s*:\s*"[^"]*"') {
            $content = $content -replace '"beschreibung"\s*:\s*"[^"]*"', '"beschreibung": "' + $escapedDesc + '"'
        } elseif ($content -match '"beschreibung"\s*:\s*""') {
            $content = $content -replace '"beschreibung"\s*:\s*""', '"beschreibung": "' + $escapedDesc + '"'
        } else {
            # Try multiline beschreibung
            $pattern = '"beschreibung"\s*:\s*"(?:[^"\\]|\\.)*"'
            if ($content -match $pattern) {
                $content = $content -replace $pattern, '"beschreibung": "' + $escapedDesc + '"'
            } else {
                Write-Warning "Could not find beschreibung field in $jsonPath"
                continue
            }
        }
        
        # Write back
        $content | Out-File -FilePath $jsonPath -Encoding UTF8 -NoNewline
        
        $totalProcessed++
        Write-Output "OK $dirName ($totalProcessed/500) - $name ($kategorie, $region)"
    }
    catch {
        Write-Error "ERROR $dirName : $_"
    }
}

Write-Output "==========================================="
Write-Output "Batch 1a completed. Processed: $totalProcessed entries"
