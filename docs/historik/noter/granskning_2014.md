# granskning_2014 - oberoende granskning av v2014-agentens filer

Etikett: granskning_2014. Granskar de filer som v2014 skrev för valet 2014 (Göteborg, 1480) och
noteringen `docs/historik/noter/v2014.md`. Syftet var att hitta fel, inte att bekräfta.

Två granskningsskript finns. `scripts/historik/granskning_2014_kontroll.py` är från en tidigare granskningsomgång
och `scripts/historik/granskning_2014_verifiering.py` är skrivet i denna omgång, utan att importera något ur
v2014-skripten. Denna notering bygger på det senare skriptet; det tidigare gav samma utfall. Inget skript skriver
till data/historik. Inga CSV-filer har ändrats, eftersom inga fel i talen hittades.

Resultat i korthet: inga numeriska fel. Alla partital, andelar, summor, koder, namn och valkretsar stämmer mellan
Excel, XML, dbf och CSV-filerna, och FGVAL stämmer mot 2010-agentens filer. Det som finns att anmärka på är
tre formuleringar i v2014.md och några formskillnader som nästa steg behöver känna till.

## Lästa källor och hur

- `Historiska dokument/2014_riksdagsval_per_valdistrikt.xls` och `2014_landstingsval_per_valdistrikt.xls` (xlrd,
  första fliken `slutligt_valresultat_valdistrik`, rubriker på Excelrad 3, data från rad 4, Göteborg = kolumn A 14
  och kolumn B 80, 301 rader var). `2014_kommunval_per_valdistrikt.xlsx` (openpyxl read_only, samma layout, 528
  kolumner, tomma celler räknade som 0). Partikolumner = rubriker som slutar på " tal" med tillhörande " proc".
- `scratchpad/unz/slutresultat/slutresultat_1480R.xml`, `_1480L.xml`, `_1480K.xml`, `_00R.xml`, `_00L.xml`,
  `_00K.xml` (xml.etree, ISO-8859-1 enligt huvudet). VALDISTRIKT och ONSDAGSDISTRIKT lästa under respektive
  KRETS_KOMMUN så att valkretstillhörigheten kommer ur trädet. GILTIGA direkt och under ÖVRIGA_GILTIGA, HANDSKRIVNA,
  ÖVRIGA_FGVAL, OGILTIGA TEXT=BLANK/OG, VALDELTAGANDE. Attributen RÖSTER, RÖSTER_FGVAL, PROCENT, SUMMA_RÖSTER,
  RÖSTBERÄTTIGADE, RÖSTBERÄTTIGADE_KLARA_VALDISTRIKT_FGVAL, SUMMA_RÖSTER_FGVAL.
- `scratchpad/unz/slutresultat__1_/slutresultat_1480R.xml`, `_1480L.xml`, `_1480K.xml` och `_00L.xml` (2010) för
  FGVAL-matchning och för landstingsfrågan.
- `scratchpad/unz/valgeografi_valdistrikt/valgeografi_valdistrikt.dbf` (dbfread, latin-1, VD och VD_NAMN) och
  `scratchpad/unz/alla_valdistrikt/alla_valdistrikt.dbf` (2010, LKFV och VDNAMN).
- `Historiska dokument/mandatfordelning_per_valkrets_R.xls` (xlrd, flik `mandatfordelning_per_valkrets_R`, rubriker
  rad 3, Göteborgs kommun på Excelrad 26) och `Valkretsmandat riksdag 2014.xls` (rad 21) som extra kontroll av
  mandat_2014_riksdag.csv.
- Andra agenters filer i data/historik: `roster_2010_rd_xml.csv`, `roster_2010_kf_xml.csv`, `distrikt_2010_rd.csv`,
  `distrikt_2010_kf.csv`, `distrikt_2010_rf.csv`, `partier_2010.csv`, `rostberattigade_2014_rd/rf/kf_bred.csv`.

## Kontroller och utfall

1. Göteborgs totaler per parti och val. Excelsumman över 301 rader, XML-summan över 301 distrikt, XML:s
   KOMMUN-element, summan av roster_2014_<val>_xls.csv och summan av roster_2014_<val>_xml.csv jämfördes med
   aggregat_2014_<val>.csv nivå goteborg: 0 avvikelser (rd 9 Excelpartier och 26 XML-partier, rf 53 Excelkolumner
   varav 17 med röster och 18 XML-partier, kf 256 Excelkolumner varav 27 med röster och 27 XML-partier).
   Excelfilernas ÖVR = XML-partier utanför Excel plus HANDSKRIVNA: rd 5097, rf 1478, kf 241. Giltiga, röstande
   och röstberättigade lika i Excel, distrikt-CSV, XML KOMMUN och aggregat: rd 334294/336956/406851,
   rf 329674/333740/425380, kf 333790/336884/425380. Andel i alla aggregat-rader = 100 x roster / giltiga.
   Kommunvalkretsarna: varje aggregat-rad = XML:s KRETS_KOMMUN, giltiga/röstande/röstberättigade = summan av
   distriktsfilen per valkrets, och inget parti med röster i XML saknas på kretsnivå. Riket = NATION och vgregion
   = LÄN 14 i 00-filerna, alla partier med röster finns med.
2. Aritmetik per distrikt i CSV-filerna. Partisumma = giltiga i 301 av 301 distrikt, i både xls- och xml-filerna,
   alla tre val. blanka + ogiltiga_ovriga = ogiltiga och giltiga + ogiltiga = rostande i alla 301. Valdeltagande
   = 100 x rostande / rostberattigade avrundat till två decimaler i 297 av 297 distrikt med röstberättigade.
   Andel = 100 x roster / giltiga i alla rader med andel (rd 3010 + 4683, rf 4459 + 4764, kf 5821 + 6195 rader,
   0 avvikelser). Tomma andelar i xls-filerna (rf 959, kf 2607) förekommer bara i rader med 0 röster. Inga dubbla
   nycklar (kod, parti) i någon fil.
3. Två källor. Excel mot XML direkt ur källfilerna, per distrikt och parti: rd 2709, rf 15953 och kf 77056 partital
   jämförda, 0 avvikelser i röster och procent; giltiga, blank, og, röstande, röstberättigade och valdeltagande
   lika i alla 301 distrikt; namn lika; R-Excelens kolumn Kommunvalkrets = XML-trädets KRETS_KOMMUN för alla 301.
   CSV mot CSV (roster_xls mot roster_xml på kod + parti): 0 avvikelser i röster och andel i 3010, 5418 och 8428
   nycklar; summan av xml-filens partier utanför xls-filen = xls-filens ÖVR i varje distrikt. Valkrets i
   distrikt_2014_rd/rf/kf.csv = XML-trädet för alla 301.
4. Koder. Råtexten i roster-, distrikt- och fgval-filerna kontrollerad utan csv-modulen: alla koder är 8 siffror
   utan ".0" eller citattecken. 297 vanliga distrikt + 4 uppsamlingsdistrikt (14800001-14800004) = 301. dbf 2014
   har 297 Göteborgsposter med samma koder och samma namn.
5. Stickprov mot råcell, slumpfrö 20140914, tre Majornadistrikt per val och tre partier med röster i varje. Cellen
   lästes på nytt ur källfilen med radnummer i Excelräkning och kolumnbokstav:
   - rd, 2014_riksdagsval_per_valdistrikt.xls, blad slutligt_valresultat_valdistrik: 14801015 Skytteskogen rad 4186
     V kolumn S = 199 (proc T 14.07), FI kolumn Y = 238 (16.83), C kolumn K = 76 (5.37); 14801021 Sandarne rad 4188
     C K = 26 (1.93), FI Y = 211 (15.63), V S = 266 (19.70); 14801034 Majorna rad 4192 FP M = 68 (5.81),
     FI Y = 137 (11.71), M I = 191 (16.32). Alla lika CSV xls och xml.
   - rf, 2014_landstingsval_per_valdistrikt.xls: 14801043 Karl Johans torg rad 3934 C kolumn I = 32, KD M = 21,
     RS CE = 1; 14801033 Hängmattan rad 3949 S O = 255, FI W = 15, PP CA = 5; 14801034 Majorna rad 3950
     VägV DE = 23, MP S = 197, KD M = 38. Alla lika CSV.
   - kf, 2014_kommunval_per_valdistrikt.xlsx: 14801016 Svalebo rad 3992 DjuP kolumn EQ = 3, S O = 164, MP S = 170;
     14801031 Godhem rad 3974 RS NQ = 1, KD M = 32, S O = 153; 14801043 Karl Johans torg rad 3978 V Q = 384,
     DjuP EQ = 8, C I = 37. Alla lika CSV.
6. FGVAL mot 2010-agentens filer, via kod_2010 i fgval_matchning_2010_2014.csv. Fem slumpade Majornadistrikt
   per val:
   - rd: Djurgårdsgatan m fl (14800943), Skytteskogen (912), Kungsladugård (913), Karl Johans torg (942), Klippan
     (916): alla partirader lika roster_2010_rd_xml.csv, GILTIGA/BLANK/OG/SUMMA_RÖSTER/RÖSTBERÄTTIGADE lika
     distrikt_2010_rd.csv.
   - kf: Kungsladugård, Djurgårdsgatan m fl, Karl Johans torg, Mariaplan (914), Sandarne (921): alla lika.
   - rf: Klippan, Söderlingska ängen, Silverkällan, Gråberget, Karl Johans torg: FGVAL matchar som väntat inte
     2010 (till exempel Klippan FGVAL giltiga 866 mot 1378 år 2010), se nedan.
   Hela filerna: rd 2324 partirader mot roster_2010_rd_xml.csv med 1 avvikelse, kf 3054 med 14 avvikelser, alla
   förklarade under avvikelser; GILTIGA, BLANK, OG lika i alla 214, SUMMA_RÖSTER och RÖSTBERÄTTIGADE lika i de 210
   valdistrikten. roster_2014 i fgval-filerna = roster i roster_xml-filerna. Intern konsistens: partiernas
   roster_fgval + HANDSKRIVNA + ÖVRIGA_FGVAL = GILTIGA fgval, och GILTIGA + BLANK + OG = SUMMA_RÖSTER i alla
   distrikt och val.
7. Egen FGVAL-matchning mot 2010 års XML, med alla partier och giltiga som villkor, inte bara de åtta
   riksdagspartierna: rd 213 av 214 entydigt samma 2010-distrikt som filen anger, kf 201 av 214. Resten är de
   14 + 1 distrikt där en partikod bytt namn (se avvikelser); inget distrikt fick flera kandidater. namn_2010 i
   matchningsfilen = alla_valdistrikt.dbf i alla rader. 2010 års dbf har 17 distrikt 148009xx, som v2014 anger.
8. Extra. Röstberättigade i distrikt_2014_*.csv = totalt i rostberattigade_2014_*_bred.csv för alla 297 distrikt
   i alla tre valen. Mandat: riket 349, 29 valkretsar summa 349, Göteborgs kommun (1416) M 4, C 1, L 1, KD 1,
   S 4, V 2, MP 2, SD 2 = 17 utan utjämningsmandat, lika mandatfordelning_per_valkrets_R.xls rad 26 och
   Valkretsmandat riksdag 2014.xls rad 21 (17 fasta mandat, 405016 röstberättigade). Göteborg kf 81 = 22 + 20 +
   19 + 20, VG-regionen 149 = 46 + 33 + 27 + 18 + 25. Riksröster i mandat_2014_riksdag.csv = aggregat riket.
   Uppgifterna i v2014.md om de 17 Majornadistrikten stämmer: rd 25494 röstberättigade och 20960 giltiga, rf och
   kf 25835 röstberättigade. Radantalen i v2014.md:s tabell stämmer med filerna.

## Landstingets FGVAL är omvalet 2011

Bekräftat oberoende. 2014 års L-XML har för Göteborg RÖSTER_FGVAL 185909, SUMMA_RÖSTER_FGVAL 186963 och
RÖSTBERÄTTIGADE_KLARA_VALDISTRIKT_FGVAL 408541, medan 2010 års L-XML har 310466, 314725 och 405033. För R och K
är FGVAL däremot identiskt med 2010 (R 319302/389821, K 316690/405033). Ingen av de fem stickprovade
Majornadistrikten har något parti lika 2010. 00L.xml 2014 ger MANDAT_FGVAL för LÄN 14 M 38, C 9, FP 11, KD 9,
S 52, V 9, MP 12, SD 9 med RÖSTER_FGVAL 545215, medan 2010 års 00L.xml ger M 39, C 8, FP 12, KD 9, S 47, V 9,
MP 11, SPVG 7, SD 7 med 979417 röster. ar_fg=2011 i fgval_2014_rf.csv är alltså rätt.

## Avvikelser och anmärkningar (inget rättat i CSV-filerna)

- v2014.md skriver att uppsamlingsdistriktens röstberättigade "ingår i kommun- och valkretssummorna". Det är
  missvisande: summan av de 297 vanliga distriktens röstberättigade är exakt kommunens tal (406851 respektive
  425380), och R-Excel har tom cell, L- och K-Excel 0 för uppsamlingsdistrikten. De har inga egna röstberättigade.
  Tomt i distrikt-filerna är rätt; formuleringen i noteringen bör ändras.
- mandat_2014_rf.csv: kolumnen mandat_fgval avser omvalet 2011-05-15, inte 2010, av samma skäl som ovan
  (S 52 mot 47 år 2010, SPVG saknas). Det står inte i v2014.md.
- fgval_2014_kf.csv: 13 rader TOP och fgval_2014_rd.csv: 1 rad LBPO där roster_fgval inte kan hittas under samma
  partikod i 2010-filerna. Orsak: Torslandapartiet hade förkortningen 1027 år 2010 (partier_2010.csv, 2010 K-XML
  PARTI FÖRKORTNING 1027 BETECKNING Torslandapartiet) och ToP 2014; Landsbygdsdemokraterna 1011 år 2010 och
  LBPO Landsbygdspartiet Oberoende 2014. Talen stämmer (till exempel 14807041 TOP fgval 150 = 14801613 1027 150
  år 2010). Kolumnen parti i fgval-filerna är 2014 års kod. Dessutom 14805061 K fgval 0 där 2010-filen saknar
  K-rad. Inte fel, men partiserier över tid måste hantera kodbytena.
- parti_kalla skiljer sig mellan roster_2014_kf_xls.csv (450, 470) och roster_2014_kf_xml.csv (0450, 0470) för
  Framtidspartiet Sverige och Seniorpartiet, eftersom Excel tappat inledande nollor. Kolumnen parti är 0450 och
  0470 i båda, enligt v2014:s konvention. Nyckla på parti, inte parti_kalla.
- K (Kommunistiska Partiet) finns i L-Excel som kolumn och i L-XML med 0 röster i 242 distrikt; roster_2014_rf_xls.csv
  utelämnar K (0 röster i Göteborg) medan roster_2014_rf_xml.csv har K-rader med 0. v2014.md:s "18 partier"
  för rf-xls är 17 partier plus ÖVR.
- fgval-filerna saknar raderna SUMMA_RÖSTER och RÖSTBERÄTTIGADE för de fyra uppsamlingsdistrikten, eftersom XML
  saknar VALDELTAGANDE där. distrikt_2010_*.csv har tomt röstberättigade för samma distrikt.
- fgval_2014_rd.csv har 56 rader ÖVRIGA_FGVAL, alla med roster_2014 = 0, som v2014 anger; rf och kf har inga.
- Formskillnader mot 2010-agentens filer som nästa steg får harmonisera: aggregat_2010_*.csv har BLANK- och
  OG-rader, aggregat_2014 inte; aggregat_2010 har vgregion bara för rf, aggregat_2014 för alla tre; uppsamlings-
  distrikten heter Onsdagsdistrikt i distrikt_2010 och Uppsamlingsdistrikt i distrikt_2014.

## Öppna frågor

- Partikoder som bytt förkortning mellan 2010 och 2014 (1027 till ToP, 1011 till LBPO) behöver en kodtabell om
  fgval-filerna ska användas för partiserier. Riksdagspartierna berörs inte.
- Omvalsfilen 2011 saknas i källorna. fgval_2014_rf.csv är enda källan till omvalet per distrikt, och bara för
  de 210 oförändrade distrikten.
- De fem modifierade Majornadistrikten 2014 saknar 2010-siffror; det är en fråga för geometrin (geo2010, geo2014).
