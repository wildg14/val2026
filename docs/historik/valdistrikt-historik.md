# Så har valdistrikten i Majorna ändrats 2002-2022

Underlag för "Så röstade Majorna". Allt nedan bygger på filerna i `data/historik/` och
noteringarna i `docs/historik/noter/`. Områdesnamnet Majorna används här om primärområdena
Majorna, Stigberget, Kungsladugård och Sanna tillsammans, det vill säga den yta som 2022 års
23 valdistrikt 14800526 till 14800548 täcker.

## Indelningarna år för år

| År | Valdistrikt i Göteborg | Distrikt i Majornaområdet | Kodserier i området | Namnskick | Kommunvalkrets | Stadsdel eller områdesnamn i källan |
| --- | --- | --- | --- | --- | --- | --- |
| 2002 | 286 | okänt, går inte att avgränsa | 148013xx, delvis 148012xx | församling plus löpnummer, Karl Johan 1-12, Masthugg 1-8 | Göteborg 4 för Karl Johan, Göteborg 3 för Masthugg | inget prefix i namnet |
| 2006 | 279 plus 4 onsdagsdistrikt | 17 | 148084xx, 148085xx, 148059xx | områdesnamn plus löpnummer, Kungsladugård-Sanna 1-7, Majorna 1-6, Stigberget 1-4 | Göteborg 4 för Kungsladugård-Sanna och Majorna, Göteborg 3 för Stigberget | inget prefix i namnet |
| 2010 | 282 plus 4 onsdagsdistrikt | 17 | 148009xx | stadsdelsnämnd plus gatunamn, "Majorna, Svalebo" | Göteborg, Väster för 13 distrikt, Göteborg, Centrum för 4 | Majorna |
| 2014 | 297 plus 4 uppsamlingsdistrikt | 17 av 36 i stadsdelen | 148010xx, serierna 101x till 104x | "Majorna-Linné, Svalebo" | Göteborg, Väster för 13, Göteborg, Centrum för 4 | Majorna-Linné |
| 2018 | 350 plus 1 uppsamlingsdistrikt | 22 av 45 i stadsdelen | 148010xx, serierna 101x till 104x | "Majorna-Linné, Kungsladugård, Östra" | en enda kommunvalkrets, Göteborg | Majorna-Linné |
| 2022 | 410 plus 1 uppsamlingsdistrikt | 23 av 48 i området | 148005xx, 526 till 548 | "Västra Centrum, Svalebo" | en enda kommunvalkrets, Göteborg | Västra Centrum |

Källor: `distrikt_<år>_rd.csv` för antal, koder, namn och valkrets; `geo_majorna_<år>.csv`
för avgränsningen av området; `datamodell.md` för antalet distrikt per år.

### Vad som drev förändringen

**2002 till 2006: hela indelningen ritades om.** Attributet INDELNING i
`slutresultat_1480R.xml` är Modifierad för 275 av Göteborgs 279 valdistrikt 2006, vilket i
Valmyndighetens filer betyder att distriktet inte är jämförbart med föregående val. Bara
fyra distrikt i hela kommunen har jämförelsetal mot 2002. Samtidigt byttes namnskicket från
församling till område: Karl Johans församling blev Kungsladugård-Sanna och Majorna,
Masthuggs församling blev Masthugget och Stigberget, Oscar Fredriks församling blev
Olivedal. Röstsummorna skiljer sig 20 till 35 procent mellan de gamla och de nya
namngrupperna, mer än vad befolknings- och valdeltagandeförändringar rimligen förklarar.

**2006 till 2010: bara nya koder och nya namn.** Geometriskt hände ingenting i Majorna. Var
och ett av de 17 distrikten sammanfaller till 99,96 till 99,99 procent åt båda hållen med ett
enda 2010-distrikt. I hela Göteborg är 274 av 279 distrikt geometriskt oförändrade. Det som
ändrades var att distriktsnamnen fick stadsdelsnämndens namn som prefix och att koderna
148084xx, 148085xx och 148059xx blev 148009xx. Valmyndigheten anger jämförelsetal för
samtliga 17 distrikt, alltså källans egen bekräftelse på att ytan är oförändrad.

**2011: stadsdelsnämnderna slogs ihop, vilket syns först 2014.** Majorna och Linnéstaden
blev Majorna-Linné, och kodserierna 148009xx och 148008xx blev 148010xx. Namnen i
resultatfilerna 2014 följer den nya nämnden. Inuti Majorna flyttades två gränser: en del av
Slottsskogsgatan m fl gick till distriktet Majorna, och en del av Marieberg gick till
Hängmattan. Övriga 13 distrikt är identiska med 2010, med andelen 1,0000 åt båda hållen. Av
hela kommunens 282 distrikt är 209 geometriskt oförändrade.

**2018: omritningen.** Valmyndighetens indelningsfil `vd-indelning-2018.skv` kodar 226 av
Göteborgs 350 distrikt som modifierade, 122 som oförändrade och 2 som nya. Majornaområdet
gick från 17 till 22 distrikt: Kungsladugård och Gråberget delades i västra och östra delar,
och Gröna Vallen, Chapmans Torg och Klareborgsgatan m fl tillkom. Bara två av områdets
distrikt, Godhem och Gatenhielmska, är oförändrade sedan 2014.

**2022: ny indelning och nytt områdesnamn.** Göteborg gick från 350 till 410 valdistrikt, och
enligt Valmyndighetens och Göteborgs stads gemensamma jämförelsefil är bara 85 av de 410
jämförbara med 2018. Kodserien 148010xx för Majorna-Linné ersattes av 148005xx för Västra
Centrum, som omfattar 48 distrikt: 25 i Masthugget, Linnéstaden, Haga, Annedal och Änggården
(14800501 till 14800525) och 23 i Majornaområdet (14800526 till 14800548). Områdets
yttergräns mot Masthugget, Slottsskogen, Änggården och Älvsborg är oförändrad från 2018; all
omritning skedde inuti området, där 22 distrikt blev 23. Varför antalet distrikt ökade
framgår inte av källfilerna.

## De 23 distrikten 2022 och deras motsvarigheter bakåt

Tabellen läses stegvis. Kolumnen Typ efter varje år anger hur distriktet i det närmast
senare året förhåller sig till det år som står till vänster: typen efter 2018 gäller alltså
steget 2018 till 2022, typen efter 2014 steget 2014 till 2018 och så vidare. Koden i varje
årskolumn är den troligaste motsvarigheten, det vill säga det äldre distrikt som täcker
störst del av det nyare. Kolumnen längst till höger anger det tidigaste år dit kedjan är
obruten med enbart typerna identisk och namnbyte.

| 2022 | Namn 2022 | 2018 | Namn 2018 | Typ | 2014 | Namn 2014 | Typ | 2010 | Namn 2010 | Typ | 2006 | Namn 2006 | Typ | Jämförbar bakåt till |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 14800526 | Svalebo | 14801017 | Svalebo | identisk | 14801016 | Svalebo | omritad | 14800911 | Svalebo | omritad | 14808405 | Kungsladugård-Sanna 5 | namnbyte | 2018 |
| 14800527 | Skytteskogen | 14801016 | Skytteskogen | omritad | 14801015 | Skytteskogen | omritad | 14800912 | Skytteskogen | identisk | 14808404 | Kungsladugård-Sanna 4 | namnbyte | 2022 |
| 14800528 | Kungsladugård Östra | 14801014 | Kungsladugård, Östra | omritad | 14801012 | Kungsladugård | delad | 14800913 | Kungsladugård | identisk | 14808403 | Kungsladugård-Sanna 3 | namnbyte | 2022 |
| 14800529 | Kungsladugård Västra | 14801013 | Kungsladugård, Västra | omritad | 14801015 | Skytteskogen | omritad | 14800912 | Skytteskogen | identisk | 14808404 | Kungsladugård-Sanna 4 | namnbyte | 2022 |
| 14800530 | Mariaplan | 14801011 | Gröna Vallen | omritad | 14801013 | Mariaplan | omritad | 14800914 | Mariaplan | identisk | 14808402 | Kungsladugård-Sanna 2 | namnbyte | 2022 |
| 14800531 | Silverkällan | 14801015 | Mariaplan | omritad | 14801014 | Silverkällan | omritad | 14800915 | Silverkällan | identisk | 14808406 | Kungsladugård-Sanna 6 | namnbyte | 2022 |
| 14800532 | Sannaplan | 14801022 | Silverkällan | omritad | 14801021 | Sandarne | omritad | 14800921 | Sandarne | identisk | 14808407 | Kungsladugård-Sanna 7 | namnbyte | 2022 |
| 14800533 | Sandarne | 14801021 | Sandarne | omritad | 14801021 | Sandarne | delad | 14800921 | Sandarne | identisk | 14808407 | Kungsladugård-Sanna 7 | namnbyte | 2022 |
| 14800534 | Klippan | 14801012 | Klippan | omritad | 14801011 | Klippan | omritad | 14800916 | Klippan | identisk | 14808401 | Kungsladugård-Sanna 1 | namnbyte | 2022 |
| 14800535 | Gröna Vallen | 14801011 | Gröna Vallen | omritad | 14801013 | Mariaplan | omritad | 14800914 | Mariaplan | identisk | 14808402 | Kungsladugård-Sanna 2 | namnbyte | 2022 |
| 14800536 | Kusttorget | 14801036 | Majorna | namnbyte | 14801034 | Majorna | omritad | 14800932 | Majorna | omritad | 14808501 | Majorna 1 | namnbyte | 2018 |
| 14800537 | Chapmans Torg | 14801031 | Chapmans Torg | identisk | 14801034 | Majorna | omritad | 14800932 | Majorna | omritad | 14808501 | Majorna 1 | namnbyte | 2018 |
| 14800538 | Slottsskogsgat. m fl | 14801038 | Slottsskogsgatan m fl | namnbyte | 14801036 | Slottsskogsgatan m fl | delad | 14800931 | Slottsskogsgatan m fl | delad | 14808505 | Majorna 5 | namnbyte | 2018 |
| 14800539 | Gråberget Västra | 14801034 | Gråberget, Östra | namnbyte | 14801032 | Gråberget | omritad | 14800934 | Gråberget | identisk | 14808506 | Majorna 6 | namnbyte | 2018 |
| 14800540 | Gråberget Östra | 14801033 | Gråberget, Västra | omritad | 14801032 | Gråberget | omritad | 14800934 | Gråberget | identisk | 14808506 | Majorna 6 | namnbyte | 2022 |
| 14800541 | Godhem | 14801032 | Godhem | identisk | 14801031 | Godhem | identisk | 14800936 | Godhem | identisk | 14808504 | Majorna 4 | namnbyte | 2006 |
| 14800542 | Marieberg | 14801037 | Marieberg | omritad | 14801035 | Marieberg | delad | 14800935 | Marieberg | delad | 14808503 | Majorna 3 | namnbyte | 2022 |
| 14800543 | Klareborgsgatan m fl | 14801044 | Klareborgsgatan m fl | omritad | 14801043 | Karl Johans torg | delad | 14800942 | Karl Johans torg | identisk | 14805904 | Stigberget 4 | namnbyte | 2022 |
| 14800544 | Karl Johan | 14801043 | Karl Johans torg | delad | 14801044 | Söderlingska ängen | omritad | 14800941 | Söderlingska ängen | identisk | 14805903 | Stigberget 3 | namnbyte | 2022 |
| 14800545 | Söderlingska Ängen | 14801045 | Söderlingska ängen | omritad | 14801044 | Söderlingska ängen | omritad | 14800941 | Söderlingska ängen | identisk | 14805903 | Stigberget 3 | namnbyte | 2022 |
| 14800546 | Kommendörsgatan m fl | 14801041 | Djurgårdsgatan m fl | namnbyte | 14801041 | Djurgårdsgatan m fl | delad | 14800943 | Djurgårdsgatan m fl | identisk | 14805902 | Stigberget 2 | namnbyte | 2018 |
| 14800547 | Hängmattan | 14801035 | Hängmattan | identisk | 14801033 | Hängmattan | delad | 14800933 | Hängmattan | omritad | 14808502 | Majorna 2 | namnbyte | 2018 |
| 14800548 | Gatenhielmska | 14801042 | Gatenhielmska | identisk | 14801042 | Gatenhielmska | identisk | 14800944 | Gatenhielmska | identisk | 14805901 | Stigberget 1 | namnbyte | 2006 |

Källa: `data/historik/kedja_majorna_2006_2022.csv`, byggd av
`scripts/historik/kedja_bygg.py` ur Valmyndighetens jämförelsetal, den officiella
distriktsmappningen 2014 till 2018, Göteborgs stads jämförelsefil 2018 till 2022 och de
geometriska överlappen. Namnen är förkortade genom att stadsdels- eller områdesprefixet före
första kommatecknet har tagits bort.

Två distrikt av 23 är alltså jämförbara hela vägen tillbaka till 2006: 14800541 Godhem och
14800548 Gatenhielmska. Sju till är jämförbara med 2018: Svalebo, Kusttorget, Chapmans Torg,
Slottsskogsgat. m fl, Gråberget Västra, Kommendörsgatan m fl och Hängmattan. Övriga fjorton
har ingen obruten kedja ens ett steg bakåt.

Bilden bakåt i tiden är den motsatta mot vad koderna antyder. Steget 2006 till 2010 är helt
oproblematiskt i Majorna, trots att både koderna och namnen byttes. Steget 2010 till 2014 är
nästan lika bra. Det är 2018 och framför allt 2022 som bryter serien på distriktsnivå.

## Definitionen "jämförbart Majorna" per år

Alla år mäts mot samma referens: unionen av 2022 års 23 distrikt, 4,6554 kvadratkilometer.
Ett distrikt tas med när minst 50 procent av dess yta ligger inom unionen. Beslutet skrivs ut
i klartext per distrikt i kolumnen `beslut` i tabellen `majorna_medlem` i databasen.

Tre trösklar samverkar i det här steget utan att vara samma sak: 0,1 procent av unionens yta
för att ett distrikt alls ska tas med i `geo_majorna_<år>.csv`, 0,95 för klassen `inne` i samma
fil och i noteringarna `geo2006.md`, `geo2010.md`, `geo2014.md` och `geo2018.md`, och 0,5 för
medlemskap i `majorna_medlem` och i tabellen nedan. De tre trösklarna ger i praktiken samma
svar alla fyra åren, 17, 17, 17 och 22 distrikt. `geo2018.md` rad 67 visar det konkret för
2018: samma 22 distrikt fås oavsett om gränsen sätts vid 95 eller 50 procent av distriktets
yta.

| År | Distrikt | Koder | Sammanlagd yta | Täckning av 2022-unionen | Yta av unionen som saknas | Yta utanför unionen |
| --- | --- | --- | --- | --- | --- | --- |
| 2006 | 17 | 14805901-14805904, 14808401-14808407, 14808501-14808506 | 4,6541 km2 | 99,96 procent | 1700 m2 | 400 m2 |
| 2010 | 17 | 14800911-14800916, 14800921, 14800931-14800936, 14800941-14800944 | 4,6541 km2 | 99,97 procent | 1588 m2 | 239 m2 |
| 2014 | 17 | 14801011-14801016, 14801021, 14801031-14801036, 14801041-14801044 | 4,6541 km2 | 99,97 procent | 1588 m2 | 239 m2 |
| 2018 | 22 | 14801011-14801017, 14801021, 14801022, 14801031-14801038, 14801041-14801045 | 4,6541 km2 | 99,97 procent | 1588 m2 | 240 m2 |
| 2022 | 23 | 14800526-14800548 | 4,6554 km2 | 100 procent | 0 | 0 |

Källor: `geo_majorna_<år>.csv` och `noter/geo2006.md`, `geo2010.md`, `geo2014.md` och
`geo2018.md`, samt `majorna_tidsserie.json` under `meta.tackningsgrad_yta_mot_2022_unionen`.

Avvikelsen är alltså 0,03 procent åt vartdera hållet från och med 2010 och 0,04 procent för
2006. Den består av två saker. Den ena är en remsa på 1451 kvadratmeter (1536 kvadratmeter
enligt 2018 års mätning) vid Söderlingska Ängen som före 2022 tillhörde distriktet Änggården,
alltså 0,03 procent av Änggårdens yta, en gränsjustering mot Slottsskogen. Den andra är
digitaliseringsbrus längs kajkanten mot älven, plus, för 2006, restfel från
koordinattransformationen från RT90 2,5 gon V till SWEREF99 TM.

**Inget distrikt något år hamnade nära tröskeln.** Klassen `delvis`, som täcker andelar
mellan 0,05 och 0,95, är tom alla fyra åren. Det lägsta värdet bland de medtagna distrikten
är 0,9997 och den närmaste kandidaten utanför är 14801061 Majorna-Linné, Änggården med 0,0003
av sin yta i unionen. Regeln 0,5 avgör alltså inte något enskilt fall, men den står kvar som
explicit och kontrollerbar. Ingen omviktning görs: alla distrikt går in hela. Detta är belagt
i noteringarna `geo2006.md`, `geo2010.md`, `geo2014.md` och `geo2018.md`, som skriver ut både
medtagna och uteslutna kandidatdistrikt. Tabellen `majorna_medlem` i databasen och
`geo_majorna_<år>.csv` innehåller bara de distrikt som togs med, så det tomma
`delvis`-facket kan inte verifieras i databasen självt, bara i geo-noteringarna.

**2002 ingår inte.** Det finns ingen valgeografi för 2002, gränserna ritades om mellan 2002
och 2006, och Stigberget låg 2002 inne i Masthugg 1-8 och kan inte skiljas ut. De tolv
distrikten Karl Johan 1-12 (14801301 till 14801312) ligger i `majorna_medlem` med klassen
`ej_geo` och `ingar_i_jamforbart_majorna` lika med 0, så att avgörandet är dokumenterat i
databasen och inte bara i text. Att skillnaden är verklig och inte bara en namnfråga syns i
röstetalen: Karl Johan 1-12 hade 11519 giltiga riksdagsröster 2002 mot 14396 i 2006 års
tretton Kungsladugård-Sanna- och Majornadistrikt.

**Uppsamlingsdistrikten faller alltid utanför.** Varje år finns röster som räknats i
efterhand och inte kan fördelas på valdistrikt: fyra onsdagsdistrikt 2006 och 2010, fyra
uppsamlingsdistrikt 2014 och ett 2018 och 2022. De saknar geometri och ingår i kommunens
totaler men inte i något områdesaggregat.

## Tre metoder för att räkna historiskt

### 1. Areaöverlapp

Distriktspolygonerna från respektive år läggs ovanpå varandra och snittarean beräknas i
SWEREF99 TM. Resultatet finns i `geo_overlap_<a>_<b>.csv` för paren 2006-2010, 2006-2022,
2010-2014, 2010-2022, 2014-2018, 2014-2022 och 2018-2022, tillsammans 9718 rader i tabellen
`crosswalk`.

*Styrkor:* metoden är komplett för alla år från 2006, täcker hela kommunen, kräver inga
externa filer och ger ett exakt och reproducerbart svar på vilka distrikt som hänger ihop
geografiskt. Den fångar nästan alltid samma distriktspar som den officiella mappningen: av
den officiella filens 488 par för 2014 till 2018 hittar areametoden 483.

*Svagheter:* areaandel är inte befolkningsandel. Jämförelsen med Valmyndighetens officiella
mappning 2014 till 2018 visar att den genomsnittliga absoluta skillnaden mellan areaandel och
officiell andel är 12,3 procentenheter, att 103 av 483 par avviker mer än 20 procentenheter
och att den största avvikelsen är 85,9 procentenheter. I Majorna är avvikelsen störst just
där ytan är obebodd: distriktet Klippan 2014 lämnade officiellt 44,2 procent av väljarna till
Gröna Vallen men bara 11,1 procent av ytan, och Sandarne lämnade 28,5 procent av väljarna men
5,0 procent av ytan till Silverkällan. Metoden duger för att avgöra vilka distrikt som hör
till ett område, inte för att fördela röster mellan distrikt.

### 2. Valmyndighetens föregående-val-tal

I XML-filerna för 2006, 2010, 2014 och 2018 finns attributet RÖSTER_FGVAL, som anger
föregående vals röstetal per parti och valdistrikt. Om ett distrikt har sådana tal alls har
Valmyndigheten bedömt det som oförändrat, och talen identifierar entydigt vilket äldre
distrikt som avses.

*Styrkor:* det är källans egen bedömning, den bygger på väljare och inte på yta, och den går
att verifiera. Matchningen av talvektorn (M, C, L, KD, S, V, MP, SD) mot föregående års
faktiska röster ger ett entydigt svar för 271 av 282 distrikt i steget 2006 till 2010 och för
214 av 214 distrikt med jämförelsetal i steget 2010 till 2014. För Majorna 2006 ger metoden
exakt samma summa som areametoden, parti för parti, i alla tre valen: riksdagsvalet M 3324,
C 928, L 1674, KD 731, S 4469, V 3225, MP 3292, SD 371 och 18803 giltiga. Noll rader i
`majorna_metodjamforelse.csv` för 2006 har någon skillnad skild från noll. Det är ett
oberoende belägg för att de 17 distrikten 2006 och de 17 distrikten 2010 täcker samma område.

*Svagheter:* talen finns bara för oförändrade distrikt. Fem av de 17 jämförbara
Majornadistrikten 2014 är markerade Modifierad och saknar dem helt: Svalebo, Hängmattan,
Majorna, Marieberg och Slottsskogsgatan m fl, tillsammans 28,5 procent av områdets giltiga
röster 2014. Summan över de tolv återstående blir därför 14638 giltiga riksdagsröster mot
areametodens 20452, en skillnad som helt beror på att fem distrikt saknas. Regionvalets
jämförelsetal 2014 avser dessutom omvalet 2011, inte valet 2010. För 2018 finns inga inlästa
jämförelsetal alls, eftersom XML-filen är gallrad från Valmyndighetens servrar och den kopia
som finns i Internet Archive ännu inte är inläst.

### 3. Officiella mappningsfiler

Två sådana filer finns i materialet. `vd-mappning-2014-2018.skv` anger för varje par av
distrikt hur många procent av 2014-distriktet som gick till respektive 2018-distrikt, 488
rader för Göteborg, och `vd-indelning-2018.skv` anger per 2018-distrikt om det är
oförändrat, modifierat, summerat eller nytt. Göteborgs stads och Valmyndighetens
jämförelsefil för 2018 mot 2022 anger i stället bara ja eller nej per 2022-distrikt, 85 ja av
410 rader.

*Styrkor:* det är den enda källa som anger andelar byggda på väljare och inte på yta, och den
är den rätta grunden när frågan är om ett enskilt distrikt får jämföras rakt av.

*Svagheter:* de finns bara för två av fem steg. Ingen officiell mappning publicerades för
2006 till 2010 eller 2010 till 2014, och filen för 2018 till 2022 saknar procentandelar helt,
så delade distrikt kan inte viktas med officiella tal. Filen för 2018 till 2022 har dessutom
ett formateringsfel: för exakt de 85 jämförbara Göteborgsraderna står 2018-koden som ett tal
i kolumnen Jämförbart i stället för texten ja. Ett fall i skv-filen för 2014 till 2018 är
oförklarat: raden `14804172;14801017;2.3` säger att 2,3 procent av Lundbyvassen på Hisingen
skulle ha gått till Svalebo i Majorna, vilket geometriskt är omöjligt.

### Rekommendation för sidan

**På områdesnivå: använd areametoden och summera hela distrikt.** Den är komplett för alla år
2006-2022, den kräver ingen omviktning eftersom alla distrikt går in hela, och för steget
2006 till 2010 är den bevisligen identisk med Valmyndighetens egen översättning. Det är den
metod `majorna_tidsserie.csv` använder. FGVAL-serien ligger kvar som kontroll i
`majorna_tidsserie_fgval.csv` och skillnaderna redovisas parti för parti i
`majorna_metodjamforelse.csv`.

**På distriktsnivå: använd bara par som en officiell källa kallar jämförbara.** Det är nio av
23 distrikt mellan 2018 och 2022 och två av 23 hela vägen tillbaka till 2006. För övriga bör
sidan visa området som helhet eller grupper av distrikt, inte enskilda distrikt över tid.

**Vikta aldrig om röster med areaandelar.** Skillnaden mellan area och väljare är för stor,
och det finns ingen officiell viktning att falla tillbaka på för stegen 2018-2022 och
2022-2026. Ett bättre underlag vore röstberättigade per distrikt, som finns i
`rostberattigade_<år>_<val>_bred.csv` för 2010, 2014 och 2018, men det kan bara vikta hela
distrikt, inte delar av dem.

## Fallgropar

**Namnet Stigberget betyder olika saker olika år.** 2006 års Stigberget 1-4 ligger i Majorna
och ingår i området; de blev 2010 Gatenhielmska, Djurgårdsgatan m fl, Söderlingska ängen och
Karl Johans torg. Distriktet som heter Stigberget 2010, 2014, 2018 och 2022 ligger däremot i
Masthugget och ingår inte: 2022 års 14800503 Västra Centrum, Stigberget täcks till 99,97
procent av 2006 års Masthugget 6, och dess överlapp med Majornaunionen är elva kvadratmeter.
Filtrera aldrig på namn.

**Samma namn betyder inte samma gränser.** Svalebo, Skytteskogen, Mariaplan, Silverkällan,
Sandarne, Klippan, Hängmattan, Marieberg, Godhem, Gatenhielmska och Söderlingska Ängen finns
som namn både 2010 och 2022, men bara Hängmattan och Gatenhielmska har samma gränser hela
vägen från 2006. Svalebo 2022 får bara 66 procent av sin yta från Svalebo 2010. Silverkällan
2018 blev till 93 procent Sannaplan 2022. Mariaplan 2018 har bara 31 procent gemensamt med
Mariaplan 2022. Karl Johans torg 2010 motsvarar i huvudsak Klareborgsgatan m fl 2022, inte
Karl Johan 2022.

**Väderstrecken på Gråberget är omkastade.** 2018 års 14801033 heter Gråberget, Västra men
ligger helt inom 2022 års 14800540 Gråberget Östra, och 2018 års 14801034 Gråberget, Östra
blev till 83,5 procent 2022 års 14800539 Gråberget Västra. Samma sak gäller i mindre skala för
Karl Johans torg och Klareborgsgatan m fl mellan 2014 och 2018.

**Koder återanvänds mellan år.** 115 av 2006 års 279 distriktskoder används redan 2002 för
helt andra distrikt: 14800101 är Domkyrko 1 år 2002 och Backa-Brunnsbo 1 år 2006. På samma
sätt är 14801011 Majorna-Linné, Klippan år 2014 men Norra Hisingen, Backadalen år 2022. Varje
sammanfogning måste ske på paret år och kod, aldrig på koden ensam. 2010 och 2014 har 33
gemensamma distriktskoder, samtliga med olika namn de två åren; fyra av dem är
14800001-14800004, onsdagsdistrikt 2010 och uppsamlingsdistrikt 2014, så bland de riktiga
valdistrikten är det 29 koder som återanvänds.

**Stora ytor i Majorna saknar bostäder.** Sandarne är områdets största distrikt med 1,41
kvadratkilometer, ungefär 30 procent av Majornas yta, och består till stor del av hamn,
varvsmark, Röda sten och Älvsborgsbrons fäste. Klippan innehåller hamnytor och Klippans
kulturreservat, och Svalebo och Skytteskogen rymmer delar av Slottsskogen och
Änggårdsbergen. Att en tredjedel av Svalebo 2022 kommer från Sandarne 2010 säger nästan
ingenting om hur många väljare som flyttades. Vattenytor ingår dessutom i polygonerna:
kommunen är 721,9 kvadratkilometer i alla indelningar.

**Röstberättigade skiljer sig mellan valen.** Utländska medborgare får rösta i region- och
kommunval men inte i riksdagsval, medan utlandssvenskar omvänt får rösta till riksdagen men
inte till kommunen. I Göteborg var utländska medborgare med rösträtt (kategorin "Ej svenska
medborgare" i `rostberattigade_<år>_kf.csv`) 29976 personer 2010, 34410 år 2014 och 38623 år
2018. Den faktiska nettoskillnaden mellan kommunvalets och riksdagsvalets röstberättigade i
Göteborg är mindre, eftersom utlandssvenskarna drar åt andra hållet: 15212 personer 2010
(405033 mot 389821), 18529 år 2014 och 22758 år 2018. För Majorna 2022 är röstberättigade
26032 i riksdagsvalet och 26737 i region- och kommunvalet. Valdeltagande för olika val ska
därför aldrig jämföras utan att det sägs vilket val som avses.

**Namnformerna skiljer sig mellan filer.** 2018 skriver "Kungsladugård, Östra" med komma och
"Söderlingska ängen" med gemen begynnelsebokstav, 2022 skriver "Kungsladugård Östra" och
"Söderlingska Ängen". Valgeografin 2022 förkortar "Slottsskogsgat. m fl" medan resultatfilen
kan ha den oförkortade formen.

**Kommunvalkretsarna byter innebörd och försvinner.** 2002 och 2006 heter de Göteborg 1 till
4, 2010 och 2014 Göteborg Hisingen, Öster, Centrum och Väster, och från 2018 finns bara en
enda kommunvalkrets. Majorna spänner dessutom över två kretsar både 2010 och 2014, vilket
inte påverkar summering av distriktsröster men gör kretsnivån oanvändbar som områdesmått.

**En rättelse.** `noter/geo2006.md` skriver att alla 17 distrikt i Majornaområdet 2006 låg i
kommunvalkrets Göteborg 4. Resultatfilerna visar att Stigberget 1-4 (14805901 till 14805904)
låg i Göteborg 3, tillsammans med Masthugget, Olivedal och Annedal-Haga, medan
Kungsladugård-Sanna 1-7 och Majorna 1-6 låg i Göteborg 4. Källa: kolumnen `valkrets` i
`distrikt_2006_rd.csv`. Uppgiften i `noter/mandat.md` är den riktiga. Ingen beräkning berörs,
eftersom områdesdefinitionen bygger på geometri och inte på valkrets.

## Majorna, Göteborg och riket över tid

Tabellerna visar andelen av giltiga röster i procent. Andelen är omräknad ur röster och
giltiga i varje rad, inte kopierad från källan, så åren är räknade på samma sätt. Majorna
2002 saknas eftersom området inte kan avgränsas det året, och valdeltagandet för riket 2002
saknas eftersom röstberättigade inte finns i 2002 års källor. Ett bindestreck betyder att
partiet inte särredovisas på den nivån det året, utan ingår i den samlade posten ÖVR eller
SUMMA_ÖVRIGA, eller att partiet inte fanns. SD 2002 är exemplet: i `jamforelse_tidsserie.csv`
finns ingen egen SD-rad för riksdagsvalet 2002, varken för Göteborg eller riket, eftersom
2002 års källa bakar in SD i ÖVR för riksdagsvalet, men samma fil har en egen SD-rad för
kommunvalet 2002 i Göteborg (4532 röster, 1,65 procent), som också står i
kommunvalstabellen nedan. Bindestrecket i riksdagstabellen betyder alltså inte att SD saknade
väljare i Göteborg 2002.

### Riksdagsvalet

| År | Nivå | V | S | MP | M | L | C | KD | SD | FI | Giltiga | Valdeltagande |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2002 | Göteborg | 11,87 | 33,16 | 6,47 | 17,43 | 18,01 | 1,87 | 8,61 | - | - | 273056 | 77,54 |
| 2002 | Riket | 8,39 | 39,85 | 4,65 | 15,26 | 13,39 | 6,19 | 9,15 | - | - | 5303212 | okänt |
| 2006 | Majorna | 17,15 | 23,77 | 17,51 | 17,68 | 8,90 | 4,94 | 3,89 | 1,97 | 2,50 | 18803 | 79,31 |
| 2006 | Göteborg | 8,68 | 28,93 | 8,44 | 26,88 | 10,24 | 4,47 | 6,73 | 2,55 | 1,26 | 292726 | 79,54 |
| 2006 | Riket | 5,85 | 34,99 | 5,24 | 26,23 | 7,54 | 7,88 | 6,59 | 2,93 | 0,68 | 5551278 | 81,99 |
| 2010 | Majorna | 18,51 | 21,22 | 20,67 | 19,15 | 6,27 | 3,42 | 3,55 | 4,08 | 2,10 | 20452 | 82,80 |
| 2010 | Göteborg | 8,53 | 25,22 | 10,71 | 30,37 | 8,40 | 3,82 | 6,10 | 4,89 | 0,86 | 319302 | 82,72 |
| 2010 | Riket | 5,60 | 30,66 | 7,34 | 30,06 | 7,06 | 6,56 | 5,60 | 5,70 | 0,40 | 5960408 | 84,63 |
| 2014 | Majorna | 19,57 | 17,77 | 14,75 | 12,34 | 5,14 | 2,78 | 2,29 | 7,41 | 16,50 | 20960 | 82,89 |
| 2014 | Göteborg | 9,35 | 23,68 | 9,83 | 23,86 | 7,22 | 3,80 | 4,60 | 9,64 | 6,48 | 334294 | 82,82 |
| 2014 | Riket | 5,72 | 31,01 | 6,89 | 23,33 | 5,42 | 6,11 | 4,57 | 12,86 | 3,12 | 6231573 | 85,81 |
| 2018 | Majorna | 32,04 | 20,98 | 10,83 | 9,88 | 4,92 | 5,34 | 3,17 | 9,67 | 1,82 | 21167 | 84,33 |
| 2018 | Göteborg | 14,00 | 23,77 | 6,95 | 19,86 | 7,25 | 7,12 | 5,52 | 13,45 | 0,84 | 349645 | 84,28 |
| 2018 | Riket | 8,00 | 28,26 | 4,41 | 19,84 | 5,49 | 8,61 | 6,32 | 17,53 | 0,46 | 6476725 | 87,18 |
| 2022 | Majorna | 27,19 | 25,88 | 15,72 | 8,89 | 4,16 | 4,27 | 2,30 | 10,10 | 0,11 | 21308 | 82,76 |
| 2022 | Göteborg | 12,85 | 27,65 | 7,92 | 18,48 | 5,85 | 5,86 | 4,37 | 14,66 | 0,09 | 347103 | 80,71 |
| 2022 | Riket | 6,75 | 30,33 | 5,08 | 19,10 | 4,61 | 6,71 | 5,34 | 20,54 | 0,05 | 6477970 | 84,21 |

Källa: `data/historik/jamforelse_tidsserie.csv`, nivåerna majorna, goteborg och riket, val rd.

### Kommunfullmäktigevalet

| År | Nivå | V | S | MP | M | L | C | KD | SD | D | K | Giltiga | Valdeltagande |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2002 | Göteborg | 10,96 | 32,50 | 6,57 | 19,74 | 16,00 | 1,65 | 7,15 | 1,65 | - | 1,57 | 273965 | 74,09 |
| 2002 | Riket | 8,24 | 37,32 | 4,28 | 17,55 | 11,47 | 8,63 | 7,09 | - | - | - | 5313271 | okänt |
| 2006 | Majorna | 14,52 | 29,94 | 15,73 | 15,35 | 8,91 | 2,96 | 3,23 | 2,22 | - | 2,91 | 18807 | 77,86 |
| 2006 | Göteborg | 7,23 | 36,04 | 7,88 | 23,88 | 10,17 | 2,84 | 5,54 | 2,98 | - | 1,27 | 291051 | 76,22 |
| 2006 | Riket | 5,98 | 34,58 | 4,88 | 24,25 | 8,15 | 9,08 | 5,80 | 2,88 | - | 0,01 | 5521566 | 79,40 |
| 2010 | Majorna | 15,80 | 25,37 | 18,61 | 15,54 | 6,50 | 2,07 | 2,20 | 3,37 | - | 2,10 | 20456 | 81,56 |
| 2010 | Göteborg | 7,12 | 29,37 | 9,90 | 25,53 | 8,37 | 2,30 | 3,77 | 4,45 | - | 0,79 | 316690 | 78,99 |
| 2010 | Riket | 5,57 | 32,38 | 7,07 | 26,19 | 7,92 | 7,61 | 4,36 | 4,91 | - | 0,13 | 5926710 | 81,62 |
| 2014 | Majorna | 21,11 | 15,93 | 17,03 | 11,56 | 5,88 | 2,06 | 2,12 | 5,40 | - | 1,45 | 21063 | 82,31 |
| 2014 | Göteborg | 9,44 | 22,39 | 10,66 | 22,33 | 8,12 | 2,56 | 3,95 | 7,02 | - | 0,56 | 333790 | 79,20 |
| 2014 | Riket | 6,44 | 31,23 | 7,76 | 21,55 | 6,55 | 7,85 | 3,98 | 9,33 | - | 0,10 | 6235010 | 82,84 |
| 2018 | Majorna | 28,88 | 16,03 | 10,52 | 7,63 | 5,51 | 3,00 | 1,72 | 6,25 | 11,06 | 1,27 | 21616 | 84,11 |
| 2018 | Göteborg | 12,56 | 20,47 | 6,94 | 14,53 | 7,23 | 3,95 | 3,32 | 8,29 | 16,95 | 0,49 | 354160 | 81,05 |
| 2018 | Riket | 7,69 | 27,58 | 4,62 | 20,06 | 6,81 | 9,67 | 5,20 | 12,74 | 0,92 | 0,09 | 6532135 | 84,12 |
| 2022 | Majorna | 34,59 | 23,11 | 9,56 | 8,25 | 3,92 | 2,90 | 2,21 | 7,30 | 3,90 | 1,02 | 21620 | 81,78 |
| 2022 | Göteborg | 15,82 | 26,44 | 5,99 | 17,12 | 5,54 | 4,00 | 4,15 | 10,75 | 6,14 | 0,38 | 350794 | 76,49 |
| 2022 | Riket | 8,25 | 29,31 | 3,82 | 20,51 | 5,24 | 7,69 | 5,36 | 14,55 | 0,33 | 0,05 | 6498692 | 80,49 |

Källa: `data/historik/jamforelse_tidsserie.csv`, val kf. D är Demokraterna, K är
Kommunistiska Partiet. Regionvalet finns i samma fil under val rf och är inte utskrivet här.

Läsanvisning: partikoden L används genomgående även för åren då partiet hette Folkpartiet
liberalerna. Raden för riket i kommunvalet är en summering av alla kommunval i landet, vilket
förklarar Centerpartiets höga tal jämfört med Göteborg. Småpartier utanför de elva som följs
genom hela perioden ligger samlade i raden SUMMA_ÖVRIGA i källfilen och är inte utskrivna
här; för Majorna 2010 är den raden 5,15 procent i kommunvalet, varav Vägvalet står för 712 av
1054 röster enligt `roster_2010_kf_xml.csv`.
