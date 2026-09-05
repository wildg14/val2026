# Kedjekontroll av jämförbarhet mellan valen 2006-2022

Syftet är att för varje valdistrikt i Göteborgs kommun (1480) avgöra vilket distrikt i föregående val
det motsvarar, och hur stor förändringen är, så att en tidsserie kan byggas utan att jämföra tal som
inte hör ihop. Grunden är Valmyndighetens egna FGVAL-tal (föregående vals röster uttryckta i aktuella
distrikt), Valmyndighetens officiella distriktsmappning 2014 till 2018 och Göteborgs stads
jämförelsefil 2018 till 2022, med geometriskt överlapp som stöd.

## Skript

`/Users/daniel/code/Temp/scripts/historik/kedja_bygg.py`, körs med

    /Users/daniel/code/Temp/.venv/bin/python \
        /Users/daniel/code/Temp/scripts/historik/kedja_bygg.py

Alla källvägar ligger som konstanter högst upp i skriptet. Skriptet läser bara, förutom de fem
CSV-filer det skriver. Det ändrar ingen befintlig fil.

## Lästa filer och hur de lästes

Alla CSV-filer nedan ligger i `/Users/daniel/code/Temp/data/historik/` och lästes som UTF-8 med
semikolon som avgränsare via `csv.DictReader`.

1. `fgval_2010_rd.csv`, `fgval_2010_rf.csv`, `fgval_2010_kf.csv` (kolumner `kod_2010`, `namn_2010`,
   `parti`, `roster_fgval`). Tomt `roster_fgval` räknas som 0, eftersom XML-attributet RÖSTER_FGVAL
   utelämnas när värdet är 0 (belagt i `granskning_2010.md`).
2. `fgval_2014_rd.csv` och `fgval_2014_kf.csv` (kolumner `kod_2014`, `namn_2014`, `parti`,
   `roster_fgval`). `fgval_2014_rf.csv` används inte, se avvikelser.
3. `roster_2006_rd_xls.csv`, `roster_2006_rf_xls.csv`, `roster_2006_kf_xls.csv` och
   `roster_2010_rd_xls.csv`, `roster_2010_kf_xls.csv` (kolumner `kod`, `namn`, `parti`, `roster`)
   som facit för FGVAL-matchningen.
4. `distrikt_2010_rd.csv`, `distrikt_2014_rd.csv`, `distrikt_2018_rd.csv` (kolumnerna `kod` och
   `namn`) för den fullständiga distriktslistan och namnen per år.
5. `geo_overlap_2006_2010.csv`, `geo_overlap_2010_2014.csv`, `geo_overlap_2014_2018.csv`,
   `geo_overlap_2018_2022.csv` (kolumnerna `kod_<tidigt år>`, `namn_<tidigt år>`, `kod_<sent år>`,
   `namn_<sent år>`, `overlapp_m2`, `andel_av_<tidigt år>`, `andel_av_<sent år>`). Rader med
   `overlapp_m2` = 0 hoppas över.
6. `mappning_2018_2022.csv` (kolumnerna `kod_2018`, `kod_2022`, `jamforbart`, `namn_2018`,
   `namn_2022`, `kalla_fil`), webbagentens läsning av Göteborgs stads fil
   `jamforelser-2018-och-2022-valdistrikt-och-uppsamlingsdistrikt-v2.xlsx`. 85 av 410 rader har
   `jamforbart` = ja med en 2018-kod.
7. `/Users/daniel/code/Temp/Historiska dokument/unz/mappning_2014_2018/vd-mappning-2014-2018.skv`
   (`kod 2014;kod 2018;procent`, 6950 rader i riket varav 488 med Göteborgskoder) och
   `vd-indelning-2018.skv` (`kod 2018;O/M/S/N`, 6004 rader varav 350 Göteborgskoder: 226 M, 122 O,
   2 N). Lästa som latin-1, rader som börjar med `#` hoppas över. Även
   `upp-mappning-2014-2018.skv` och `upp-indelning-2018.skv` för uppsamlingsdistrikten.
8. `/Users/daniel/code/Temp/data/valdata_2022.json`, enbart `distrikt[].kod` och `distrikt[].namn`
   för de 23 Majornadistriktens kortnamn.
9. `granskning_2010_fgval_koppling_2006.csv` och `fgval_matchning_2010_2014.csv` användes inte som
   indata utan enbart som oberoende facit i efterkontrollen nedan.

## Metod

**FGVAL-matchning (2006 till 2010 och 2010 till 2014).** För varje distrikt i det senare valet
bildades vektorn (M, C, L, KD, S, V, MP, SD) ur `roster_fgval`, och för varje distrikt i det tidigare
valet samma vektor ur de faktiska rösterna. Ett distrikt räknas som styrkt när vektorn är identisk med
exakt ett distrikt i det tidigare valet, och när alla använda val (rd, rf och kf för 2006 till 2010,
rd och kf för 2010 till 2014) pekar på samma distrikt. FP är normaliserat till L i alla filer.
Distrikt utan FGVAL saknar det därför att Valmyndigheten har satt INDELNING = Modifierad, alltså
källans egen uppgift att distriktet är ändrat. I `belagg` skrivs ett av valens vektorer ut i klartext,
det som står först i uppräkningen (kf), med texten "ger var för sig identisk vektor, kf: ...".
Att även de övriga valen pekar på samma distrikt är ett villkor för raden, men deras tal skrivs inte
ut för att hålla fältet läsbart. De går att slå upp i `roster_<tidigare år>_<val>_xls.csv` på den
kod som står i `kod_<tidigare år>_troligast`.

**Namnjämförelse.** Kärndelen av namnet, det vill säga det som står efter första ", " (utan
stadsdelsnämnds- eller valkretsprefix), gemener, utan skiljetecken. Så blir "Majorna, Svalebo" och
"Majorna-Linné, Svalebo" lika, medan "Kungsladugård-Sanna 5" och "Svalebo" är olika.

**Geometri.** Ur geo_overlap-filerna hämtas för varje distrikt i det senare valet alla föregångare
med positiv snittarea. Två andelar används: hur stor del av det nya distriktet en föregångare täcker,
och hur stor del av föregångaren som ligger i det nya distriktet. Trösklarna är 0.98 för "i praktiken
samma yta", 0.90 för "föregångaren ligger i allt väsentligt inne i det nya distriktet" och 0.05 för
att alls räknas som källa.

**Rangordning.** Kolumnen `kod_<tidigare år>_troligast` är den föregångare som täcker störst del av
det nya distriktet. För 2014 till 2018 rangordnas kandidaterna ur skv-mappningen med geometrin,
eftersom skv-filens procenttal är andel av 2014-distriktet och inte av 2018-distriktet, och därför
inte säger vilken föregångare som dominerar det nya distriktet.

**Regel för typ.** Källan går före geometrin. Ett distrikt får `identisk` eller `namnbyte` bara när
källan säger att det är oförändrat: FGVAL finns och matchar exakt (2006 till 2010, 2010 till 2014),
`vd-indelning-2018.skv` = O (2014 till 2018) eller Göteborgs stads kolumn Jämförbart = ja (2018 till
2022). Skillnaden mellan `identisk` och `namnbyte` avgörs av namnjämförelsen. Övriga distrikt
klassas med geometrin som `delad` (det nya distriktet är en bit av ett enda gammalt), `sammanslagen`
(minst två gamla distrikt ligger i allt väsentligt inne i det nya), `ny` (ingen föregångare alls
eller indelning N) eller `omritad` (allt annat). Där geometrin i praktiken är 1:1 trots att källan
säger att distriktet är ändrat sätts en OBS-anmärkning i `belagg`, men typen förblir `omritad`.

## Skrivna filer

Alla i `/Users/daniel/code/Temp/data/historik/`, UTF-8, semikolon, punkt som decimaltecken, koder som
åttasiffrig text.

| Fil | Rader | Kolumner |
|---|---|---|
| `kedja_2006_2010.csv` | 286 | kod_2010;namn_2010;kod_2006_troligast;namn_2006;typ;belagg |
| `kedja_2010_2014.csv` | 301 | kod_2014;namn_2014;kod_2010_troligast;namn_2010;typ;belagg |
| `kedja_2014_2018.csv` | 351 | kod_2018;namn_2018;kod_2014_troligast;namn_2014;typ;belagg;kalla |
| `kedja_2018_2022.csv` | 410 | kod_2022;namn_2022;kod_2018_troligast;namn_2018;typ;belagg;kalla |
| `kedja_majorna_2006_2022.csv` | 23 | se nedan |

De två sista har kolumnen `kalla` eftersom uppgiften kräver att källan markeras när FGVAL saknas.
Radantalet är antalet distrikt i det senare året, inklusive uppsamlingsdistrikt: fyra 2010 och 2014,
ett 2018. 2022 års 410 rader är alla distrikt i kommunen, varav 23 ligger i Majornaområdet.

`kedja_majorna_2006_2022.csv` har en rad per 2022-distrikt i Majornaområdet (14800526-14800548) med
kolumnerna kod_2022;namn_2022;kortnamn_2022;kod_2018;namn_2018;typ_2018_2022;kod_2014;namn_2014;
typ_2014_2018;kod_2010;namn_2010;typ_2010_2014;kod_2006;namn_2006;typ_2006_2010;
jamforbar_tillbaka_till;jamforbar_direkt;anmarkning. `kortnamn_2022` kommer ur valdata_2022.json.
`jamforbar_tillbaka_till` är det tidigaste år dit kedjan är obruten med enbart identisk eller
namnbyte, och `jamforbar_direkt` är ja bara när kedjan är obruten hela vägen till 2006.
`anmarkning` samlar OBS-texterna ur de underliggande stegen.

## Resultat per steg

| Steg | identisk | namnbyte | delad | sammanslagen | omritad | ny | summa |
|---|---|---|---|---|---|---|---|
| 2006 till 2010 | 4 | 271 | 5 | 0 | 6 | 0 | 286 |
| 2010 till 2014 | 132 | 82 | 41 | 0 | 46 | 0 | 301 |
| 2014 till 2018 | 116 | 6 | 98 | 1 | 128 | 2 | 351 |
| 2018 till 2022 | 74 | 11 | 98 | 0 | 227 | 0 | 410 |

Summan identisk plus namnbyte är i varje steg exakt lika många som källan själv anger som
oförändrade: 275 (271 valdistrikt med FGVAL plus fyra onsdagsdistrikt), 214 (distrikt med FGVAL
2014), 122 (indelning O i vd-indelning-2018.skv) och 85 (Jämförbart = ja i Göteborgs stads fil).
Ingen rad fick typen okänd.

De fyra `identisk` 2006 till 2010 är onsdagsdistrikten 14800001-14800004, som 2006 har koderna
1480VK01-1480VK04 men samma namn. Alla 271 geografiska distrikt med FGVAL fick `namnbyte`, eftersom
Göteborg 2010 bytte namnskick från "Majorna 1" och "Kungsladugård-Sanna 5" till "Majorna, Svalebo".
Ytan är alltså oförändrad trots namn- och kodbyte.

De två `ny` 2018 är 14804028 Lundby, Vågmästarplatsen och 14805258 Askim-Frölunda-Högsbo,
Uggleberget, båda kodade N i vd-indelning-2018.skv och utan rad i vd-mappning-2014-2018.skv.
Geometrin visar ändå varifrån ytan kom (14804025 Kvillebäcken Östra respektive 14805255 Nygård), och
det står i `belagg`.

## Majornaområdet 2006 till 2022

Ingen kedja i Majornaområdet är obruten via 2006 utom två distrikt.

| Tillbaka till | Antal av 23 |
|---|---|
| 2018 eller tidigare | 9 |
| 2014 eller tidigare | 2 |
| 2010 eller tidigare | 2 |
| 2006 | 2 |

De två som är direkt jämförbara hela vägen är 14800541 Godhem (2018 14801032, 2014 14801031, 2010
14800936, 2006 14808504 Majorna 4) och 14800548 Gatenhielmska (2018 14801042, 2014 14801042, 2010
14800944, 2006 14805901 Stigberget 1). De sju övriga som är jämförbara med 2018 är 14800526 Svalebo,
14800536 Kusttorget, 14800537 Chapmans Torg, 14800538 Slottsskogsgatan m fl, 14800539 Gråberget
Västra, 14800546 Kommendörsgatan m fl och 14800547 Hängmattan. Övriga 14 distrikt har ingen obruten
kedja ens ett steg bakåt.

Bilden bakåt i tiden är alltså den motsatta mot vad koderna antyder. Steget 2006 till 2010 är helt
oproblematiskt i Majorna: alla 23 kedjor går obrutet genom det steget, och alla 17 dåvarande
Majornadistrikt och alla 19 Linnéstadsdistrikt har FGVAL. Steget 2010 till 2014 är nästan lika bra
(17 av 23 kedjor passerar det som identisk). Det är 2018 och framför allt 2022 som bryter serien:
Majorna-Linné delades och ritades om 2018, och Västra Centrum 2022 har 23 Majornadistrikt mot 17
tidigare.

För en tidsserie på områdesnivå spelar det mindre roll. Distrikten i Majornaområdet är i allt
väsentligt samma yta hela perioden, det är indelningen inuti som ändrats. Summan över de 23
distrikten 2022 kan jämföras med summan över motsvarande distrikt tidigare år, och crosswalk-filerna
`geo_crosswalk_<år>_2022_majorna.csv` från geo-delen anger vilka distrikt som bygger upp varje
2022-distrikt. Det som inte går är att jämföra ett enskilt distrikt över tid, utom för Godhem och
Gatenhielmska.

## Efterkontroll mot andra delars filer

Skriptet bygger sin FGVAL-matchning från grunden, utan att läsa de tidigare agenternas
matchningsfiler. Resultatet jämfördes efteråt:

- Mot `granskning_2010_fgval_koppling_2006.csv` (raderna med val = rd och traffar = 1): 271 av 271
  2010-distrikt får samma 2006-kod, 0 avvikelser. De fyra onsdagsdistrikten saknas i den filen och
  finns i min, eftersom jag matchar även dem.
- Mot `fgval_matchning_2010_2014.csv` (raderna med val = rd och matchning = exakt): 214 av 214
  2014-distrikt får samma 2010-kod, 0 avvikelser, och inget distrikt som den filen kallar exakt
  hamnade utanför identisk eller namnbyte hos mig.
- Ingen `kod_<tidigare år>_troligast` förekommer två gånger bland raderna med identisk eller
  namnbyte i någon av de fyra filerna. Relationen är alltså en till en där den ska vara det.
- Antalet rader per fil stämmer med antalet distrikt i respektive år: 286, 301, 351 och 410, alla
  koder unika.

## Avvikelser och tveksamma fall

- **Regionvalets FGVAL 2014 avser omvalet 2011.** `fgval_2014_rf.csv` har ar_fg 2011 (belagt i
  `v2014.md`). Därför bygger 2010 till 2014 bara på rd och kf. För 2006 till 2010 användes alla tre
  valen och de gav samma svar i samtliga fall.
- **Fem distrikt 2010 och fem 2014 är geometriskt 1:1 men saknar FGVAL.** De har alltså typen
  `omritad` trots att ytan är i praktiken oförändrad, med OBS i `belagg`. 2010: 14801141 Älvsborg
  Grimmered, 14801221 Frölunda Ruddalen, 14801631 Torslanda Lilleby, 14801811 Lundby Lindholmen,
  14801851 Lundby Västra Eriksberg. 2014: 14801016 Majorna-Linné Svalebo, 14802122 Örgryte-Härlanda
  Björkekärr Södra, 14806131 Angered Eriksbo, 14807011 Västra Hisingen Biskopsgården N, 14807012
  Västra Hisingen Svarte Mosse. Att Svalebo finns bland dem är av betydelse för Majorna: kedjan
  14800526 bryts formellt där, men skillnaden är liten och kan vara enbart en gränsjustering.
  Valmyndighetens uppgift har fått gälla, eftersom bara den vet om röstberättigade flyttats.
- **Nio 2022-distrikt är geometriskt 1:1 mot 2018 men markeras inte som jämförbara av Göteborgs
  stad**, varav två i Majorna: 14800533 Sandarne (14801021 täcker 100.0 procent av 2022-distriktet,
  98.4 procent av 2018-distriktet ligger där) och 14800545 Söderlingska Ängen (98.4 respektive 100.0
  procent). Övriga sju är 14800129 Lövgärdet Nedre, 14800316 Björkekärr Södra, 14800636 Lindås,
  14800640 Skintebo Västra, 14800714 Fiskebäck, 14800735 Donsö-Vrångö och 14800821 Andalen. Alla har
  typen `omritad` med OBS. Om stadens bedömning bygger på röstberättigade och inte på yta kan små
  flyttar av adresser ligga bakom. Detta är den viktigaste öppna frågan i kedjan.
- **Tvärtom finns 19 2022-distrikt som staden kallar jämförbara men där geometrin inte är 1:1**,
  varav fem i Majorna: 14800526 Svalebo (100.0 och 97.0 procent), 14800538 Slottsskogsgatan m fl
  (92.0 och 100.0), 14800539 Gråberget Västra (100.0 och 83.5), 14800541 Godhem (95.3 och 94.4) och
  14800546 Kommendörsgatan m fl (95.2 och 100.0). Även Godhem, det ena av de två distrikt som är
  direkt jämförbara hela vägen till 2006, har alltså en gränsändring 2022 på några procent av ytan.
  Formuleringen "oförändrat sedan 2006" bör därför inte användas utan förbehåll. De 14 övriga ligger
  i Centrum, Östra Centrum, Sydvästra Göteborg, Västra Hisingen, Centrala Hisingen och Norra
  Hisingen och listas med sina tal i `belagg` i kedja_2018_2022.csv.
- **Namn och koder korsas i Majorna 2018.** 2018 års 14801033 heter Gråberget, Västra men blev 2022
  Gråberget Östra, och 14801034 Gråberget, Östra blev 2022 Gråberget Västra, enligt Göteborgs stads
  egen jämförelsefil. På samma sätt är 2018 års 14801043 Karl Johans torg i huvudsak 2014 års
  14801044 Söderlingska ängen, medan 2018 års 14801044 Klareborgsgatan m fl i huvudsak är 2014 års
  14801043 Karl Johans torg. Koden i sig säger alltså ingenting om kontinuiteten i Majorna, och
  namnet inte heller.
- **Uppsamlingsdistrikten.** 2006 har koderna 1480VK01-1480VK04 i `roster_2006_*`, 2010 och 2014
  14800001-14800004, 2018 ett enda 14800000. FGVAL kopplar 2006 och 2010 samt 2010 och 2014 parvis,
  och `upp-mappning-2014-2018.skv` visar att de fyra slogs ihop till ett 2018 (indelning S). De
  finns med i kedjefilerna men saknar geometri och ingår inte i Majornatabellen.
- **`ny` används sparsamt.** Eftersom geometrin täcker hela kommunen finns alltid någon föregångare i
  ytan. Typen `ny` sätts bara när källan säger N eller när det saknas överlappning helt. Två
  distrikt 2018 fick den, inga 2022.

## Kontrollkörning

Skriptet kördes om efter att filerna först skrivits. Alla fem CSV-filer blev radvis identiska med
den tidigare körningen, det vill säga resultatet är reproducerbart ur källfilerna. Kontrollerat i
samma omgång: inga rader har fel antal kolumner, ingen rad har tom eller okänd typ, och
distriktslistan i varje kedjefil är exakt lika med `distrikt_<senare år>_rd.csv` (286, 301 och 351
distrikt) respektive alla 410 distrikt 2022. De enda två raderna utan motpartskod är de två
`ny`-distrikten 2018. Spårbarheten stickprovskontrollerades på 14800911 Majorna, Svalebo: `roster_2006_rd_xls.csv`
ger M 177 och C 63 för 14808405 Kungsladugård-Sanna 5, och `fgval_2010_rd.csv` ger samma tal för
14800911, vilket är den koppling kedjefilen anger.

## Öppna frågor

- Göteborgs stads jämförelsefil 2018 till 2022 saknar procenttal och anger bara ja eller nej. Vilket
  kriterium staden har använt framgår inte av det som lästs in i `mappning_2018_2022.csv`. Med ett
  kriterium i handen skulle Sandarne och Söderlingska Ängen kunna avgöras.
- Valmyndighetens XML för 2018 finns inte bland källorna, så det finns ingen FGVAL för 2018 och
  därmed ingen oberoende sifferkontroll av steget 2014 till 2018. Skulle den filen gå att hämta
  kunde 2014 års tal matchas mot 2018 års FGVAL på samma sätt som för de tidigare stegen.
- Ingen officiell mappning mellan 2006 och 2010 respektive 2010 och 2014 finns i skv-format, bara
  FGVAL. För de distrikt som saknar FGVAL i dessa steg är föregångaren enbart geometriskt bestämd.
- Röstberättigade per distrikt kunde användas som ett andra mått på hur mycket ett distrikt ändrats,
  utöver ytan. Filerna `rostberattigade_*_bred.csv` finns men har inte använts här.
