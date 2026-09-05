# Nästa steg för sidan, ur historikspåret

Skrivet 2026-09-05 efter samtal med Daniel. Historikspåret bygger inget som syns på sidan; det här är
listan över vad UX-sessionen kan bygga ur underlaget, med de fakta som behövs för att göra det, så att
inget tappas bort. Ordningen är förslag. Punkt 1 har ett datum: valdagen 13 september 2026.

## Fakta som är belagda

### Valnattens filer 2026

- Valmyndigheten publicerar resultat som zip-filer på `https://resultat.val.se/resultatfiler/val2026/`,
  listade i `index.md5` på samma adress. Mappen `p/` är preliminär räkning och uppdateras löpande under
  valnatten, `s/` är slutlig räkning från måndagen efter valet. Riksdagen är en fil för hela landet
  (`.../p/rd/..._00_RD.zip`, alla 6 626 distrikt), regionvalet en per län (`.../p/rf/..._14_RF.zip`),
  kommunvalet en per kommun (`.../p/kf/..._1480_KF.zip`). Varje zip innehåller `rostfordelning`,
  `mandatfordelning` och för riksdag och region `summering`, alla JSON, plus sha256-signaturer.
- Adressen `val2026` svarar 404 fram till valnatten. Simuleringarna 17 augusti till 2 september ligger
  kvar under `https://resultat.val.se/resultatfiler/genrep2026/` med samma struktur och `"test": true`.
  Fyra av dem är hämtade till `Historiska dokument/dl_webb/genrep2026/` (riksdag 00, region 14, kommun
  1480 preliminär och slutlig), uppackade i `unz/`. Siffrorna är påhittade, formatet är skarpt.
  Formatbeskrivningarna från val.se ligger i `Historiska dokument/dl_webb/2026/*.md`.
- Per distrikt finns: `valdistriktskod`, `namn`, `rapporteringsTid`, `totaltAntalRoster`,
  `antalRostberattigade`, `valdeltagandeVallokal`, `statusJamforelse`, `valdistriktskodForegaendeVal`,
  `totaltAntalRosterForegaendeVal`, samt `rostfordelning.rosterPaverkaMandat.partiRoster[]` med
  `partiforkortning`, `antalRoster`, `andelRoster`, `antalRosterForegaendeVal`, `forandringAndelRoster`,
  `rosterOvrigaPartier` och `rosterEjPaverkaMandat` (blanka, ej anmält deltagande, övriga ogiltiga).
  Filhuvudet har `antalValdistriktRaknade` och `antalValdistriktSomSkaRaknas`.
- Jämförelsen mot 2022 är ifylld per distrikt där Valmyndigheten anser distriktet jämförbart och tom
  annars. Svalebos jämförelsetal i simuleringen (805 röstande i riksdagsvalet, 825 i kommunvalet) är
  exakt sidans 2022-siffror.
- Excelfilen "Röster per distrikt" som `scripts/uppdatera_2026.py` läser kom 2022 först dagar efter valet.
  Den är slutlig-vägen, inte valnattsvägen.

### Distrikten 2022 mot 2026

- Valmyndighetens fil `valdistrikt-jamforelser-mellan-2022-och-2026.xlsx` (slutlig bedömning 2026-08-17,
  i `Historiska dokument/dl_webb/2026/`) säger att 14 av Majornas 23 distrikt kan jämföras och 9 inte:
  14800529 Kungsladugård Västra, 14800530 Mariaplan, 14800531 Silverkällan, 14800532 Sannaplan,
  14800533 Sandarne, 14800534 Klippan, 14800535 Gröna Vallen, 14800538 Slottsskogsgat. m fl och
  14800541 Godhem. Alla 23 koder finns kvar 2026, Västra Centrum har fortfarande 48 distrikt.
- De 23 distrikten täcker exakt samma yta 2026 som 2022 (4 655 448 kvadratmeter båda åren).
  Omritningen är intern: Silverkällan går från 59 910 till 112 424 kvadratmeter, Mariaplan, Sannaplan
  och Gröna Vallen växer, Klippan, Sandarne och Godhem krymper. Majornas totalsiffra och totala
  förändring mot 2022 är därför giltiga från första räknade distrikt.
- Geometrin för 2026 ligger i `Historiska dokument/dl_webb/2026/valdistrikt-vastra-gotaland-lan-2026.zip`
  (GeoJSON, EPSG:3006, egenskaperna `Valdistriktskod` och `Valdistriktsnamn`, inte `Lkfv` och `Vdnamn`
  som 2022). Sandarne stavas Sandarna 2026.

### Historiken

- Majorna som område är jämförbart från 2006: 17 distrikt 2006, 17 år 2010, 17 år 2014, 22 år 2018,
  23 år 2022 och 2026, samma yta på 0,04 procent när. Serien ligger i `data/historik/majorna_tidsserie.csv`
  (Majorna) och `jamforelse_tidsserie.csv` (Majorna, Göteborg, riket) och i databasen. 2002 går inte att
  koppla till området.
- Enskilda distrikt är sällan jämförbara bakåt: 9 av 23 mot 2018, 2 mot 2006 (`kedja_majorna_2006_2022.csv`).
- Polygoner per år finns i `data/historik/distrikt_<år>_goteborg.geojson` (hela Göteborg, WGS84) och
  `distrikt_<år>_majornaomradet.geojson` för 2006, 2010, 2014 och 2018. Vilka distrikt som ingår i
  jämförbart Majorna per år står i `geo_majorna_<år>.csv` (andel_i_majorna minst 0,5) och i tabellen
  `majorna_medlem`.

## Punkter att bygga

1. **Valnattshämtare.** Ett skript som laddar ner de tre zip-filerna (rd 00, rf 14, kf 1480) från
   `resultatfiler/val2026/p/`, kontrollerar mot `index.md5`, läser JSON och skriver `valdata_2026` och
   `swing_2026` i sidans befintliga schema. Swing per distrikt bara för de 14 jämförbara, för Majorna totalt
   alltid. Räknade distrikt ur `rapporteringsTid` och filhuvudets räknare. Körbart i slinga, till exempel
   var femte minut. Testas mot genrep-filerna nu, byter bara basadress på valnatten. Den nuvarande
   xlsx-vägen och CSV-reservvägen behålls.
2. **Kartans polygoner 2026.** Byt `data/distrikt.geojson` till 2026 års geometri (samma 23 koder) före
   valnatten, med samma bygge som 2022 men andra egenskapsnamn. Markera de nio omritade distrikten som
   "ny gräns 2026" i distriktskortet i stället för att visa förändring mot 2022.
3. **Områdesserien "Majorna sedan 2006".** En liten datafil (`data/historik.json` plus `.js`) ur databasen
   med per år, val och parti: röster, andel, giltiga, röstande, röstberättigade, valdeltagande, för
   Majorna, Göteborg och riket, plus metadata om antal distrikt och metod. Partier: sidans nyckelpartier,
   FP som L, FI egen rad 2014 och 2018, resten Övriga. Sektion med linjer per parti, Majorna mot Göteborg
   och riket, valdeltagande och röstdelningen V i riksdag mot kommun. Innevarande år läses ur
   `valdata_{år}` så att 2026 hakar på automatiskt.
4. **Årsväljare för kartan.** Samma kartram, årsväljaren som redan finns, polygonlager per år, varje år
   färgat med sina egna resultat per distrikt (finns för alla år i databasen, inget jämförelseproblem).
   Fast Majornakontur som referens, bildtext "17 distrikt 2006" och så vidare. 2026 kan visas som
   konturer utan data redan före valet. Sidan behöver klara olika antal distrikt per år (banderollen
   "X av 23" är hårdkodad i tanken, inte i datan).
5. **Förändring per distrikt, regler.** Visa bara där Valmyndigheten säger att det går: 14 av 23 mot 2022
   på valnatten, 9 av 23 mot 2018. Dölj annars, eller visa areaviktad skattning tydligt märkt. Underlag:
   `mappning_2018_2022.csv`, `geo_crosswalk_<år>_2022_majorna.csv`, jämförelsefilen 2022 till 2026.
6. **Stillbilder för brevet** av områdesserien, i `scripts/skapa_bilder.py` med samma format som i dag.
7. **Underlag som kan läsas in senare:** 2018 års XML (hämtad, i `Historiska dokument/dl_webb/2018/`),
   röstberättigade efter ålder och kön 2022 (xlsx i projektroten), områdesdefinition för Masthugget och
   Linnéstaden som grannjämförelse, `mappning_2022_2026.csv` ur jämförelsefilen.

## Beslut som är Daniels

- Om punkt 1 ska byggas före eller efter att sidan i övrigt är klar. Valdagen är fast.
- Om de nio omritade distrikten ska visas utan förändring eller med areaviktad skattning.
- Vilka partier som får egna linjer i områdesserien och hur långt tillbaka den ska gå (2006 är gränsen
  för exakt jämförbarhet).
