# Granskning av valet 2018 (etikett granskning_2018)

Datum: 2026-09-03. Motgranskning av val2018-agentens filer i data/historik/. Uppdraget var att
leta fel, inte att bekräfta. Slutsatsen är att inga fel hittades i siffrorna: samtliga 2018-filer
går att räkna fram ur källfilerna igen, rad för rad och parti för parti, och de stämmer mot fyra
oberoende kontrollkällor. Tre öppna frågor i val2018.md är avgjorda, och en av de rapporterade
avvikelserna visade sig vara ett tolkningsfel i den första granskningens HTML-läsare, inte i data.

## Skript och loggar

| Fil | Innehåll |
|---|---|
| scripts/historik/granskning_2018_motpart.py | Min egen granskning, skriven från grunden. Läser källfilerna själv och räknar om allt. Avslutar med kod 0 när inget fel finns. |
| scripts/historik/granskning_2018_rattelse.py | Rättelsen av partier_2018.csv, idempotent. |
| scripts/historik/granskning_2018_kontroll.py | Fanns sedan tidigare från ett avbrutet granskningspass. Kördes om och reproducerade sina nio avvikelser exakt. Alla nio är tolkningsfel, se avsnittet om HTML. |
| scratchpad/granskning_2018_motpart.txt | Utskrift från min granskning (FEL 0, VARNING 0, INFO 0). |
| scratchpad/granskning_2018_rerun.txt | Utskrift från omkörningen av den äldre granskningen. |
| scratchpad/dl2018_motpart/ | 21 nedladdade distriktssidor från historik.val.se, cachade. |

## Lästa filer och hur

- Historiska dokument/2018_R_per_valdistrikt.xlsx, flikarna "R antal" och "R procent". 6325 datarader,
  varav 351 med LÄNSKOD 14 och KOMMUNKOD 80, 34 partikolumner (kolumnerna mellan VALDISTRIKTSNAMN
  och OGEJ). Läst med openpyxl, read_only, data_only.
- Historiska dokument/2018_L_per_valdistrikt.xlsx, flikarna "L antal" och "L procent". 6283 rader,
  351 Göteborgsrader, 48 partikolumner.
- Historiska dokument/2018_K_per_valdistrikt.xlsx, flikarna "K antal" och "K procent". 6325 rader,
  351 Göteborgsrader, 220 partikolumner.
- Historiska dokument/2018_mandat.xlsx, fliken "Mandatfördelning".
- slutligt-valresultat-riksdagen-jamforande-statistik-2018-2022.xlsx (i projektroten), flikarna
  Riket och Valkrets. Oberoende publikation från Valmyndigheten.
- scratchpad/unz/2018_valgeografi_valdistrikt/alla_valdistrikt.dbf, läst med dbfread, encoding utf-8.
- scratchpad/repaired/2018_rostberattigade_R/L/K.xlsx, kolumnerna som börjar på "Män/" och
  "Kvinnor/" summerade per valdistrikt_id med kommun_id 1480.
- scratchpad/unz/mappning_2014_2018/vd-indelning-2018.skv och vd-mappning-2014-2018.skv,
  ISO-8859-1, semikolon.
- historik.val.se, sidorna
  /val/val2018/slutresultat/{R,L,K}/valdistrikt/14/80/<vd>/index.html för 7 valdistrikt.
- data/historik/roster_2014_rd/rf/kf_xls.csv och _xml.csv (2014-agentens filer) för jämförelsen
  med föregående val.

## Vad som kontrollerades och resultatet

1. Filformat. Alla 14 filer är UTF-8 utan BOM, LF, semikolon, punkt som decimaltecken, samma antal
   fält på varje rad. Alla koder i roster-, distrikt- och ogiltigafilerna matchar `\d{8}`. Inga
   dubbletter av (kod, parti_kalla) i roster-filerna. Kolumnerna ar och val har rätt värde överallt.
2. Egen omräkning ur källan. 9126 (distrikt, parti)-par i riksdagsvalet, 5967 i regionvalet och
   7020 i kommunvalet jämfördes mot roster-filerna: samtliga lika. Andelen jämfördes både mot
   procentfliken och mot 100 gånger röster delat med giltiga: samtliga lika inom 0.01.
   Normaliseringen (DEM till D, versaler i övrigt) stämmer i varje rad.
3. Distriktsfälten. namn, valkrets, giltiga, blanka, ogiltiga_ovriga (OGEJ plus OG), ogiltiga,
   rostande, rostberattigade och valdeltagande stämmer mot källan för alla 351 rader per val.
   Ogiltigafilerna stämmer kolumn för kolumn (OGEJ, BLANK, OG).
4. Interna identiteter, alla 351 rader gånger tre val: partisumman är lika med giltiga, giltiga
   plus ogiltiga är lika med röstande, och valdeltagande är lika med 100 gånger röstande delat med
   röstberättigade avrundat till två decimaler. Uppsamlingsdistriktet 14800000 har noll
   röstberättigade och valdeltagande 0.00, vilket är källans eget värde.
5. Partitäckning. Varje partikolumn med minst en Göteborgsröst finns i roster-filen, och ingen
   kolumn utan Göteborgsröster har tagits med. Utelämnade kolumner: 8 i riksdagsvalet, 31 i
   regionvalet, 200 i kommunvalet. Det är regeln som val2018.md beskriver och den är följd.
6. Aggregat. Nivåerna goteborg, riket och vgregion räknades om ur källfilerna. Röster, andel,
   giltiga, röstande och röstberättigade stämmer för varje parti och nivå, och partisumman är lika
   med giltiga på varje nivå. Summan av roster-filens rader är lika med aggregatets Göteborgsrader,
   och summan av distriktsfilens rader är lika med kommuntotalen.
   Göteborg: riksdag giltiga 349645, röstande 352660, röstberättigade 418425, valdeltagande 84.28;
   region giltiga 350850, röstande 355311, röstberättigade 441183, valdeltagande 80.54;
   kommun giltiga 354160, röstande 357569, röstberättigade 441183, valdeltagande 81.05.
7. Shapefilen. De 350 geografiska koderna och namnen i distriktsfilerna är identiska med
   alla_valdistrikt.dbf, den enda extra koden är uppsamlingsdistriktet 14800000. Majorna-Linné har
   45 distrikt, 14801011 till 14801098, i både shapefilen, resultatfilerna och vd-indelning-2018.skv.
   Uppgiftens 47 går inte att belägga i någon källa; val2018.md har rätt.
8. Röstberättigade per distrikt. Summerade ur de reparerade ålders- och könsfilerna:
   350 distrikt, riksdag 418425, region och kommun 441183, noll avvikelser mot distriktsfilerna.
9. Mandat. 27 Göteborgsrader i 2018_mandat.xlsx jämfördes mot mandat_2018.csv (röster, fasta
   mandat, utjämningsmandat, summa) utan avvikelse. Fasta plus utjämning är lika med mandat i varje
   rad, och summorna är 349 i riksdagen, 149 i Västra Götalandsregionen och 81 i Göteborg.
10. Oberoende publikation. 16 partital i riksdagsvalet (riket och valkrets Göteborgs kommun) ur
    slutligt-valresultat-riksdagen-jamforande-statistik-2018-2022.xlsx stämmer mot aggregat_2018_rd.csv.
11. Officiell distriktsmappning. 348 av 350 Göteborgsdistrikt har minst en koppling till 2014 i
    vd-mappning-2014-2018.skv. De två utan koppling, 14804028 och 14805258, är de enda med
    indelningskod N (nytt) i vd-indelning-2018.skv, alltså väntat. Göteborgs 350 distrikt fördelar
    sig på 226 M (modifierat), 122 O (oförändrat) och 2 N.

## Stickprov mot råcell

Slumpat urval med annat frö än den första granskningen (random.seed(20181)), tre Majornadistrikt,
tre partital per distrikt och val, totalt 27 celler, alla lika med CSV. Exempel:

| Val | Fil och flik | Rad | Kolumn | Cell | roster_2018_*.csv |
|---|---|---|---|---|---|
| rd | 2018_R_per_valdistrikt.xlsx, "R antal" | 4018 | N (V) | 300 | 14801021 V = 300 |
| rd | 2018_R_per_valdistrikt.xlsx, "R antal" | 4021 | J (C) | 55 | 14801032 C = 55 |
| rd | 2018_R_per_valdistrikt.xlsx, "R antal" | 4030 | X (ENH) | 2 | 14801043 ENH = 2 |
| rf | 2018_L_per_valdistrikt.xlsx, "L antal" | 3976 | O (MP) | 114 | 14801021 MP = 114 |
| rf | 2018_L_per_valdistrikt.xlsx, "L antal" | 3979 | M (S) | 186 | 14801032 S = 186 |
| rf | 2018_L_per_valdistrikt.xlsx, "L antal" | 3988 | AX (SPVG) | 1 | 14801043 SPVG = 1 |
| kf | 2018_K_per_valdistrikt.xlsx, "K antal" | 4018 | HT (ÖVR) | 1 | 14801021 ÖVR = 1 |
| kf | 2018_K_per_valdistrikt.xlsx, "K antal" | 4021 | HG (VägV) | 30 | 14801032 VägV = 30 |
| kf | 2018_K_per_valdistrikt.xlsx, "K antal" | 4030 | FC (RS) | 2 | 14801043 RS = 2 |

Hela listan med alla 27 cellerna står i scratchpad/granskning_2018_motpart.txt under rubrik 7.

## Distriktssidorna på historik.val.se: de nio rapporterade avvikelserna är tolkningsfel

Eftersom XML-rådata för 2018 är gallrade finns bara en andra källa per distrikt: Valmyndighetens
egna resultatsidor per valdistrikt. Den tidigare granskningen läste dem med en enkel texttolkning
och fick nio avvikelser. Jag skrev om tolkningen så att den läser tabellernas tr- och td-element
och kontrollerade 18 sidor (sex distrikt gånger tre val), inklusive de tre distrikt som flaggades.
Resultat: noll avvikelser. Alla nio hade samma två orsaker:

1. Ett parti som står i tabellen "Röstfördelning övriga partier" utan röster har en tom antalcell.
   Den gamla tolkningen hoppade vidare till nästa siffra på sidan, som är raden "Röster på partier
   som ej beställt valsedlar 2018". Därav de rapporterade avvikelserna om RS 1 mot CSV 0 i 14801011 samt om
   PP och ENH med 1 röst som saknas i roster-filerna. Källfilerna har noll för dessa partier i just de distrikten, vilket är rätt.
   PP och ENH har dessutom noll röster i hela Göteborg i region- respektive kommunvalet (PP har
   1534 röster i landstingsvalen i riket), så de är korrekt utelämnade ur roster-filerna.
2. Kolumnen ÖVR i huvudtabellen är summan av hela tabellen "Röstfördelning övriga partier",
   alltså både de namngivna småpartierna och raden för partier som ej beställt valsedlar. I
   källfilen har de flesta av dem egna kolumner, och kolumnen ÖVR är resten. Den gamla kontrollen
   jämförde sidans ÖVR med CSV-summan av småpartierna utan CSV-kolumnen ÖVR, och blev därför alltid
   exakt en restpost fel. Exempel 14801011 regionval: sidan ÖVR 10, CSV MED 3 plus NMR 1 plus
   SPVG 5 plus ÖVR 1 är 10.

I den korrigerade kontrollen jämförs per sida: varje parti i huvudtabellen, varje parti i
övrigatabellen, sidans ÖVR mot CSV-summan inklusive ÖVR-kolumnen, summan av övrigatabellen mot
ÖVR, samt giltiga, röstberättigade, röstande, valdeltagande, OGEJ, BLANK och OG. Mellan 23 och 27
värden per sida, 18 sidor, alla lika.

## Jämförelse med föregående val (2014)

Inga fgval-filer finns för 2018 eftersom XML-rådata är gallrade, vilket val2018.md redovisar.
Distriktssidorna har däremot kolumnerna "Antal 2014" och "Andel 2014" för distrikt med
indelningskod O. Bland de 22 Majornadistrikten gäller det två: 14801032 Godhem, som enligt
vd-mappning-2014-2018.skv kommer från 2014 års 14801031 till 100 procent, och 14801042
Gatenhielmska, som kommer från 14801042 till 100 procent. Alla partital i 2014-kolumnen stämmer
mot 2014-agentens filer:

- Riksdag: 9 partier lika per distrikt. De småpartier som saknas i roster_2014_rd_xls.csv ligger i
  den filens OVR (14801031: 15 röster, 14801042: 13), och OVR är exakt lika med summan av de
  småpartier som roster_2014_rd_xml.csv listar var för sig. Sidans tal för ENH, PP, DjuP och KrVP
  är identiska med xml-filens.
- Region: 11 partier lika per distrikt, inga saknade.
- Kommun: 15 partier lika per distrikt, inga saknade.

Det är alltså en trevägskontroll som binder ihop 2018-filerna, 2014-filerna och Valmyndighetens
publicerade jämförelse. För övriga 20 Majornadistrikt går den inte att göra, eftersom de är
ombildade och sidorna då saknar 2014-kolumn. Den officiella mappningen får användas i stället.
Procenten i vd-mappning-2014-2018.skv är andelen av det gamla distriktet som gick till det nya:
summan per 2014-kod är 100 för alla 5837 koder (avrundning högst 0.1), medan summan per 2018-kod
kan vara vad som helst. Det är alltså inte en avvikelse att exempelvis 14801011 summerar till 90.8.

## Ändringar i filerna

En ändring gjord, i data/historik/partier_2018.csv, via scripts/historik/granskning_2018_rattelse.py.
Sex tomma namnfält fyllda:

| val | parti_kalla | namn | belägg |
|---|---|---|---|
| rd | BASIP | Basinkomstpartiet | distriktssidan R 14804154 Lundby, Rambergsstaden, Norra: enda raden utan förkortning, 3 röster; kolumnen BASIP i R-filen har 3 i samma distrikt, INI och NYREF har 0 |
| rd | INI | Initiativet | distriktssidan R 14805173 Askim-Frölunda-Högsbo, Gånglåten: enda raden utan förkortning, 3 röster; kolumnen INI har 3, BASIP och NYREF 0 |
| rd | NYREF | NY REFORM | distriktssidan R 14807031 Västra Hisingen, Länsmansgården, Ö: enda raden utan förkortning, 1 röst; kolumnen NYREF har 1, BASIP och INI 0 |
| rd, rf, kf | ÖVR | Övriga anmälda partier | partibeteckningen i kolumnen Parti på samtliga distriktssidor |

Kopplingen är entydig: i vart och ett av de tre distrikten är det bara ett av de tre partierna som
har röster, och bara en rad på sidan saknar förkortning. Namnen stämmer också med
deltagande_partier.skv, där Basinkomstpartiet (PARTIKOD 1372), Initiativet (1374) och NY REFORM
(1385) står som riksdagspartier utan förkortning. Därmed finns inga tomma namn kvar i
partier_2018.csv. Att 1397 är Skolpartiet Göteborg bekräftas också av sidorna: kolumnen 1397 har 1
röst i 14801021 och 2 i 14801043, och sidorna visar "Skolpartiet Göteborg" utan förkortning med
samma tal.

Observera att en omkörning av val2018_bygg.py skriver över partier_2018.csv och tar bort namnen.
Kör då granskning_2018_rattelse.py igen, den är idempotent.

## Kvarstående noteringar

- XML-rådata för 2018 saknas hos Valmyndigheten. Jag har inte gjort om sökningen efter dem, den är
  dokumenterad i val2018.md med 24 provade adresser. Konsekvensen är att 2018 är det enda året i
  serien utan en andra maskinläsbar källa per distrikt. Distriktssidorna i HTML fungerar som
  kontrollkälla men skulle behöva skrapas för alla 350 distrikt för att bli en fullvärdig sådan.
- De 22 Majornadistrikten i val2018.md är identiska med geo-agentens geo_majorna_2018.csv, som är
  framtagen geometriskt och oberoende. Summorna i val2018.md stämmer mot filerna: riksdag giltiga
  21167, röstande 21361, röstberättigade 25331, valdeltagande 84.33; region giltiga 21379, röstande
  21687, röstberättigade 25965, valdeltagande 83.52; kommun giltiga 21616, röstande 21839,
  röstberättigade 25965, valdeltagande 84.11.
- Distriktet 14801057 Majorna-Linné, Stigberget ligger utanför Majornaområdet trots namnet. Det är
  redovisat i val2018.md och stämmer med geo-filerna.
- Uppsamlingsdistriktet har koden 14800000 för 2018 men 14800001 i 2014-filerna. Den som bygger
  databasen behöver välja en konvention. Detta är en fråga för nästa steg, inte ett fel i 2018.
