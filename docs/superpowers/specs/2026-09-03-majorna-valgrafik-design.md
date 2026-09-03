# Så röstade Majorna - designspec för interaktiv valgrafik

Datum: 2026-09-03. Valdag: 2026-09-13. Underlag: `interaktiv-valgrafik-brief.md` och `majorna-valanalys-2022.md` i projektmappen.

## Mål

En helt statisk, självbärande webbsida som visar valresultatet 2022 för de 23 valdistrikten i klassiska Majorna, och som utan kodändring tar emot 2026 års siffror på valnatten. Publik: boende i Majorna, mobil först. Länkas från Majposten i Beehiiv.

Bärande (måste finnas): klickbar karta med tre val-flikar, "Om Majorna bestämde" ovanför kartan, dataformat som tar 2026-siffror, egen URL. Allt annat är sekundärt.

## Beslut som avviker från briefens förslag

**Kartan ritas som inline-SVG, inte med Leaflet eller MapLibre.** Skäl:

- Ett kartbibliotek på 60 vh kapar sidscrollen på mobil (kartan panoreras i stället för att sidan rullar). Med 23 polygoner behövs varken panorering eller zoom.
- Inga externa beroenden alls: sidan fungerar från `file://`, offline och på valnatten även om ett CDN ligger nere.
- Sidvikten hamnar runt 300 kB i stället för 1 MB.
- Utseendet kan följa Majpostens identitet (platt, inga skuggor, inga gradienter, pappersbakgrund) i stället för OSM-kakelplattor med partifärger ovanpå.

Orientering löses med ett eget bakgrundslager som hämtas från OpenStreetMap vid byggtid (gator, spårväg, hållplatser, vatten, parker) och sparas som lokal fil. Lagret är valfritt: saknas filen ritas kartan mot enfärgad bakgrund.

**Data laddas som JS-filer, inte via fetch.** Bygget skriver varje datafil både som `.json` (kanonisk, för andra konsumenter) och som `.js` (samma innehåll i ett anrop till `MAJPOSTEN.registrera`). Sidan laddar `.js`-filerna dynamiskt utifrån en konfigrad. Det gör att sidan fungerar via `file://` utan server. Båda filerna skrivs av samma funktion och kan inte glida isär.

## Filer

```
index.html                      hela sidan, all CSS och JS inline
data/valdata_2022.json / .js    röster per distrikt och val, aggregat, mandat
data/distrikt.geojson / .js     23 polygoner i WGS84
data/bakgrund.json / .js        gator, spårväg, hållplatser, vatten, parker (valfri)
data/valdata_2026.json / .js    skrivs av uppdatera_2026.py på valnatten
data/swing_2026.json / .js      förändring mot 2022 per distrikt, samma skript
scripts/valmyndigheten.py       parser för Valmyndighetens rådatafiler, partimappning
scripts/mandat.py               jämkade uddatalsmetoden med spärr
scripts/bygg_data.py            xlsx + zip -> data/, med kontrollsteg
scripts/kontrollera.py          stämmer av JSON mot xlsx, avbryter vid minsta diff
scripts/uppdatera_2026.py       rådatafiler 2026 -> valdata_2026 + swing_2026
scripts/hamta_bakgrund.py       Overpass -> data/bakgrund
tests/                          pytest
README.md                       körordning, valnatten steg för steg
requirements.txt                openpyxl, pyproj, shapely, pytest
```

## Dataschema `valdata_{år}.json`

```
{
  "meta": {
    "ar": 2022, "status": "slutlig" | "preliminar",
    "uppdaterad": "2026-09-03T12:00:00",
    "kalla": "Valmyndigheten, slutlig rösträkning per valdistrikt",
    "avgransning": "23 valdistrikt (14800526-14800548) = primärområdena ...",
    "val": {"rd": "Riksdag", "rf": "Region", "kf": "Kommun"},
    "partier": {"V": "Vänsterpartiet", ...},
    "valnatt": {"raknade": 23, "totalt": 23}          // bara meningsfullt 2026
  },
  "distrikt": [
    {
      "kod": "14800526", "namn": "Svalebo", "raknat": true,
      "rd": {"V": 179, "S": 217, ..., "Övriga": 15},
      "rf": {...}, "kf": {...},
      "giltiga":        {"rd": 797, "rf": 808, "kf": 810},
      "rostande":       {"rd": 805, "rf": 820, "kf": 825},
      "rostberattigade":{"rd": 1073, "rf": 1130, "kf": 1130}
    }, ... 23 st, alltid alla 23 (oräknade har raknat=false och tomma röstobjekt)
  ],
  "aggregat": {
    "majorna":  {"rd": {"roster": {...}, "giltiga": N, "rostande": N, "rostberattigade": N}, "rf": ..., "kf": ...},
    "goteborg": {"rd": {"andel": {"V": 0.128, ...}, "valdeltagande": 0.8071}, "rf": ..., "kf": ...},
    "riket":    {"rd": {"andel": {...}, "valdeltagande": 0.8421}, "rf": {... Västra Götaland ...}}
  },
  "mandat": {
    "riksdag_verklig": {"S": 107, "SD": 73, ...},        // ur Mandatfordelning-filen
    "riksdag_majorna": {"V": 99, "S": 94, ...},          // beräknad ur Majornas RD-röster
    "metod": "Räkneexempel: 4 %-spärr och jämkade uddatalsmetoden ..."
  }
}
```

Andelar beräknas alltid i sidan som parti / giltiga. Aggregat för Göteborg och riket lagras som andelar (källa: fliken Sammanfattning; för 2026 lämnas de tomma tills slutliga siffror finns, sidan döljer då jämförelsen).

`swing_{år}.json`: `{ "bas": 2022, "distrikt": { "14800526": { "rd": { "V": -2.1, ... } } }, "majorna": { "rd": {...} } }` i procentenheter. Sidan visar swing bara om filen finns.

## Sidan, uppifrån och ner

1. **Rubrik** "Så röstade Majorna" + ingress (en mening, markerad som placeholder för redaktören). Årväljare visas bara om konfigen listar fler än ett år. I valnattsläge: banderoll "X av 23 distrikt räknade, uppdaterat HH:MM".
2. **Om Majorna bestämde.** Halvcirkel med 349 prickar, partiblock i ordningen V, S, MP, C, L, KD, M, SD från vänster. Två lägen: "Riksdagen 2022" och "Om Majorna bestämde". Byte tonar om prickarna (CSS-transition, avstängd vid prefers-reduced-motion). Första gången sektionen kommer i bild går den automatiskt från verklig till Majorna. Legend med båda talen per parti. Etikett med metodtexten från briefen.
3. **Kartan.** Flikar Riksdag / Region / Kommun. Växel "Största parti" / "Partistyrka" med partiväljare i det senare läget. Största parti: fyll med partifärg, etikett med partibokstav och procent i varje distrikt. Partistyrka: sekvensiell skala (papper till partifärg, fem steg) med legend. Bakgrundslagret ritas under polygonerna, hållplatsnamn och stadsdelsnamn ovanpå i dämpad färg. Distrikten är `<path role="button" tabindex="0">` med aria-label som innehåller namn och de tre största partiernas procent. Klick, tapp, Enter eller mellanslag väljer.
4. **Distriktspanel** under kartan. Före val: "Hela Majorna". Efter val: distriktsnamn, staplar för alla partier >= 1 % med procent, markering av Majorna-snittet som lodrät linje per stapel, valdeltagande, antal röster. Om swing finns: kolumn med förändring mot 2022. Knapp "Visa alla distrikt som tabell" som fäller ut en fullständig tabell (tillgänglighet och grannskapsjämförelse).
5. **Röstdelningen.** Lutningsdiagram Riksdag -> Kommun för V, S och MP (övriga partier i grått), med procent i båda ändar.
6. **Faktaruta.** Valdeltagande Majorna och riket, giltiga riksdagsröster, avgränsningen, källa, "Byggd av Majposten", länk "Prenumerera på Majposten" (placeholder-URL). OpenStreetMap-attribution om bakgrundslagret finns.

Alla siffror i sidan räknas ut ur datafilerna. Inga tal hårdkodas i HTML.

## Utseende

Majpostens palett: papper `#FAF6EE` som bakgrund, bläck `#2A241E`, sten `#6E6152`, linje `#E6DECF`, slottsskogsgrön `#3F5A3A` för accenter och länkar, mörkgrön `#2E4A2C` för fyllda ytor. Georgia för rubriker, Arial/Helvetica för brödtext, minst 16 px. Platt: inga skuggor, gradienter, ikoner eller dekor. Streck skrivs som bindestreck med mellanslag, aldrig tankstreck. Inga utropstecken, inga emoji.

Partifärger (en definition i JS, en i Python): V `#9B1B30`, S `#E3312D`, MP `#5E9E3E`, C `#2E8B57`, L `#6DA9DC`, M `#2B6DB5`, KD `#1D2F6F`, SD `#E2C13B` (mörk text), D `#163A5E`, FI `#CF2A7B`, K `#7A1F1F`, Övriga `#A79C8E`. Färg står aldrig ensam: etikett eller procent finns alltid.

## Pipeline och kontroller

`bygg_data.py`:

1. Läser flikarna RD, RF, KF. Varje distriktsrad: partiröster, Giltiga, Röstande, Röstberättigade. Kontroll 1: summan av partikolumnerna = Giltiga röster på varje rad. Kontroll 2: kolumnsummor för de 23 raderna = totalraden "Majorna totalt", alla kolumner. Kontroll 3: totalerna = fliken Sammanfattning.
2. Läser Mandatfordelning-filen (verkliga mandat 2022), beräknar Majornas mandat med `mandat.py`.
3. Läser zip-filen, filtrerar 23 koder, transformerar EPSG:3006 -> EPSG:4326, avrundar till 6 decimaler. Polygonerna har 12 till 121 hörn, så ingen förenkling behövs (och gemensamma gränser bevaras därmed exakt). Kontroll 4: exakt 23 distrikt, giltiga ringar, namnen ur Vdnamn matchar xlsx-namnen efter borttag av prefixet "Västra Centrum, ".
4. Skriver alla filer, kör `kontrollera.py` som sista steg.

Om rådatafilerna för 2022 finns i mappen: kontroll 5, parsern i `valmyndigheten.py` måste ge exakt samma siffror som xlsx:en. Det är generalrepetitionen för 2026.

`uppdatera_2026.py --rd FIL --rf FIL --kf FIL [--status preliminar] [--tid 20:45]`:

- Validerar formatet (rätt kolumner, distriktskoder med 8 siffror, summeringsrader finns). Fel format -> avbryt med tydligt meddelande.
- Filtrerar de 23 koderna. Saknas ett distrikt i filen markeras det som oräknat. Har ett distrikt bytt namn eller finns nya koder i intervallet: varning i klartext.
- Partietiketter som inte känns igen och har över 0,5 % i något distrikt: varning.
- Skriver `valdata_2026` med `meta.status`, `meta.valnatt.raknade` och `raknat` per distrikt, samt `swing_2026` mot `valdata_2022`.
- `--csv FIL`: reservväg. Enkel långformats-CSV (val;kod;parti;roster) som redaktören kan fylla i för hand om Valmyndighetens filformat ändrats.
- `--repetera`: kör parsern på 2022 års råfiler och jämför med `valdata_2022.json`. Ska ge noll diff.

Valfria filer under valnatten: körs skriptet med bara `--rd` fylls rf och kf med tomma objekt och sidan visar "inte räknat" på de flikarna.

## Konfig i index.html

```js
const KONFIG = {
  ar: ["2022"],            // lägg till "2026" på valnatten
  standardAr: "2022",
  valnatt: false,          // true på valnatten: banderoll, gråtoning, räknade distrikt
  prenumerera: "https://majposten.se/subscribe"   // placeholder
};
```

## Test

- pytest: mandatberäkning (Majornas 349 mot briefens tal, spärr), parser mot 2022-råfiler (tre distrikt exakt), kontrollskriptet avbryter vid manipulerad siffra, geometrin har 23 giltiga polygoner inom Göteborgs bbox.
- Webbläsare: skärmdump i 390 px bredd, alla 23 distrikt klickbara (programmatisk klickning av varje path och kontroll av panelens rubrik), tre stickprov mot xlsx:en (Mariaplan RD, Skytteskogen KF, Svalebo RF).
- Sidvikt under 1 MB: mäts i bygget och skrivs ut.

## Utanför denna version

Adresssök, quiz, delningsbilder, tvillingkarta, automatisk pollning på valnatten, tolkningstext.
