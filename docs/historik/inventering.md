# Inventering av historisk valdata 2002-2022

Underlag för "Så röstade Majorna". Sammanställningen bygger enbart på noteringarna i
`docs/historik/noter/`, filerna i `data/historik/` och de källfiler som räknas upp nedan.
Varje tal i dokumentet går att spåra till en fil och en kolumn. Där underlag saknas står
det okänt.

## Sammanfattning

Riksdagsval, regionval (landstingsval före 2019) och kommunfullmäktigval för samtliga
valdistrikt i Göteborgs kommun finns nu inlästa för alla sex valen 2002, 2006, 2010, 2014,
2018 och 2022, tillsammans 1918 distriktsrader och 92333 röstetal i
`data/historik/majorna_historik.sqlite`. För 2006, 2010 och 2014 finns två oberoende
källor, Valmyndighetens XML och dess Excelfiler, och granskningarna visar att de ger
identiska röstetal. För 2002 finns bara webbsidorna på historik.val.se, och de saknar
röstberättigade per distrikt och särredovisar inte blanka röster. För 2018 är
Valmyndighetens XML gallrad från de officiella servrarna men återfunnen i Internet Archive,
och 2022 publicerades utan ifyllda jämförelsetal mot 2018. Ett Majorna som är jämförbart
över tid går att bygga från och med 2006: 17 distrikt 2006, 17 år 2010, 17 år 2014, 22 år
2018 och 23 år 2022 täcker samma 4,6554 kvadratkilometer, med en avvikelse på 0,03 procent
av ytan från och med 2010 och 0,04 procent för 2006. Att områdessumman är jämförbar är belagt
två gånger om, dels geometriskt, dels med Valmyndighetens egna föregående-val-tal, som för
2006 ger exakt samma siffror som areametoden. År 2002 kan däremot inte kopplas till området,
eftersom det inte finns någon valgeografi för 2002 och gränserna ritades om mellan 2002 och
2006. Enskilda distrikt är i stort sett aldrig jämförbara över tid: av 2022 års 23
Majornadistrikt har bara Godhem och Gatenhielmska en obruten kedja tillbaka till 2006. Utöver resultaten finns röstberättigade
per kön, medborgarskap och åldersgrupp för 2010, 2014 och 2018, mottagna förtidsröster per
lokal och dag för samma år samt vallokaler med koordinater. Det som saknas och inte gick att
hämta är valgeografi för 2002, officiella distriktsmappningar för stegen 2006 till 2010 och
2010 till 2014, procentandelar för mappningen 2018 till 2022 samt röstberättigade efter
ålder och kön för 2022, som finns i projektroten men ännu inte är inläst.

## Källfiler per valår

Filnamn utan sökväg avser mappen `Historiska dokument/` i projektroten. `scratchpad` avser
`/Users/daniel/code/Temp/Historiska dokument`,
som är sessionsbunden och kan vara borta vid en senare körning. Utdatafilerna ligger i
`data/historik/`.

### 2002

Inga lokala originalfiler finns för 2002. Allt är hämtat från historik.val.se med
`scripts/historik/val2002_fetch.py` och sparat i `scratchpad/dl2002/` (908 filer, 19 MB).

| Källa | Innehåll | Format och läsbarhet | Kvalitet | Blev |
| --- | --- | --- | --- | --- |
| `historik.val.se/val/val_02/slutresultat/14X/1480/<kod>.html`, 858 sidor (286 distrikt gånger tre val) | röster och procent per parti, ogiltiga (OG), valdeltagande, uppdelning av övriga partier | statisk HTML, UTF-8 med META charset, läst med lxml | fullständig på distriktsnivå, procenten är trunkerad till en decimal, inte avrundad | `roster_2002_<val>.csv`, `roster_2002_<val>_ovriga.csv`, `distrikt_2002_<val>.csv`, `distrikt_2002_indelning.csv` |
| `14X/1480/1480-text.html` | alla distrikt i fast bredd plus kommunvalkretsarnas summor | HTML med fasta kolumner räknade i byte, inte i tecken | används som andra källa, 286 av 286 distrikt identiska i alla tre valen | kontroll, samt valkretsnivån i `aggregat_2002_<val>.csv` |
| `14X/1480/148001.html` till `148004.html` | länklistor med de åttasiffriga koderna, kommunvalkrets | HTML | fullständig | distriktslistan och kolumnen valkrets |
| `00X/00.html` och `00X/00-text.html`, `14X/14.html` | riket respektive Västra Götalands län | HTML | fullständig utom röstberättigade | nivåerna riket och vgregion i `aggregat_2002_<val>.csv` |
| `14R/1480/R-1480-16.html`, `14L/1480/L-1480-01.html`, `14K/1480/K-1480-01.html` till `04` | "I vallokal ej räknade röster", en post per kommun (R, L) och per kommunvalkrets (K) | HTML | saknar åttasiffrig kod och kan inte fördelas på distrikt | nivån `ej_raknade_i_vallokal` i aggregatfilerna |

Kvalitetsanmärkningar 2002: röstberättigade finns inte på någon sida, blanka röster
särredovisas inte utan ingår i OG, och 51 tomma röstceller (SPI 43, KPML 8) är tolkade som
noll efter kontroll mot textsidan. Ett distrikt, 14801301 Karl Johan 1, har noll ogiltiga i
riksdagsvalet enligt både distriktssidan och textsidan, vilket ser ut som en
registreringsmiss 2002 men är källans värde.

### 2006

| Källa | Innehåll | Format och läsbarhet | Kvalitet | Blev |
| --- | --- | --- | --- | --- |
| `scratchpad/dl2006/unz/riksdagen_i_valdistrikt.xls` | riksdagsvalet per valdistrikt, hela riket, 6177 rader | xls, xlrd, blad `riksdagsvalet_vd_2006_orginal` | 283 Göteborgsrader, fullständig | `roster_2006_rd_xls.csv` |
| `scratchpad/dl2006/unz/landstingen_i_valdistrikt.xls` | landstingsvalet per valdistrikt | xls, blad `L_vd_2006` | 283 rader | `roster_2006_rf_xls.csv` |
| `scratchpad/dl2006/unz/kommunerna_i_valdistrikt_14.xls` | kommunvalet per valdistrikt, Västra Götalands län | xls, blad `K_vd_14_2006` | 283 rader | `roster_2006_kf_xls.csv` |
| `scratchpad/dl2006/slutresultat_1480R.xml`, `_1480L.xml`, `_1480K.xml` | slutligt resultat per distrikt, parti, blanka, ogiltiga, valdeltagande, mandat | XML, ISO-8859-1, DTD parti person kommun 1.3, läst med lxml utan DTD | fullständig, alla 3679 partivärden i rd lika med xls | `roster_2006_<val>_xml.csv`, `distrikt_2006_<val>.csv`, `aggregat_2006_<val>.csv`, `distrikt_2006_indelning.csv`, `partier_2006.csv` |
| `scratchpad/dl2006/slutresultat_00R.xml`, `_00L.xml`, `_00K.xml` | riket, län, valkretsar, kommuner, mandat | XML | fullständig | nivåerna riket och vgregion, `mandat_2006_riksdag.csv` |
| `riksdagen_i_valdistrikt.zip`, uppackad i `scratchpad/unz/riksdagen_i_valdistrikt/` | shapefil 2006 med riksdagsresultat som attribut, 6150 polygoner | shapefil i RT90 2,5 gon V (EPSG:3021), dbf i latin-1, fältet heter `Lkfv` med gemener | 279 Göteborgsdistrikt, inga onsdagsdistrikt, alla geometrier giltiga | `geo_overlap_2006_2022.csv`, `geo_overlap_2006_2010.csv`, `geo_majorna_2006.csv`, `geo_crosswalk_2006_2022_majorna.csv`, `distrikt_2006_goteborg.geojson` |
| `scratchpad/dl2006/unz/riksdagen_i_kommuner.xls` | riksdagsvalet per kommun | xls | används bara som kontroll | kontroll av Göteborgsraden |

Kvalitetsanmärkningar 2006: de fyra onsdagsdistrikten har koderna 1480VK01 till 1480VK04 i
xls och R-1480-01 och framåt i XML, alltså inte åtta siffror, och bär 8883 giltiga
riksdagsröster i Göteborg som inte kan fördelas geografiskt. Tre distrikt i landstingsfilen
har giltiga övriga röster utan underliggande partirader. Attributet INDELNING är
Modifierad för 275 av 279 distrikt, vilket betyder att jämförelsetal mot 2002 saknas för
dem.

### 2010

| Källa | Innehåll | Format och läsbarhet | Kvalitet | Blev |
| --- | --- | --- | --- | --- |
| `slutligt_valresultat_valdistrikt_R.xls` | riksdagsvalet per distrikt, 6064 rader, flik "Röstresultat" | xls, xlrd | 286 Göteborgsrader inklusive fyra onsdagsdistrikt | `roster_2010_rd_xls.csv`, `distrikt_2010_rd.csv` |
| `slutligt_valresultat_valdistrikt_L.xls` | landstingsvalet, flik "RostresultatLandstingValP" | xls | 286 rader | `roster_2010_rf_xls.csv`, `distrikt_2010_rf.csv` |
| `slutligt_valresultat_valdistrikt_K_antal.xls` och `_K_procent.xls` | kommunvalet, antal och procent i var sin fil, 230 kolumner | xls | 286 rader, radordningen kontrollerad på koden | `roster_2010_kf_xls.csv`, `distrikt_2010_kf.csv` |
| `slutresultat (1).zip`, uppackad i `scratchpad/unz/slutresultat__1_/` | Valmyndighetens XML 2010, valdag 20100919 | XML, ISO-8859-1, DTD 1.6 | fullständig, men alla distriktsnamn är utbytta mot "Namnet gallrat" | `roster_2010_<val>_xml.csv`, `aggregat_2010_<val>.csv`, `fgval_2010_<val>.csv`, `fgval_2010_<val>_deltagande.csv`, `partier_2010.csv` |
| `slutligt_valresultat_kommuner_R.xls` | riksdagsvalet per kommun | xls | kontroll | kontroll av Göteborgsraden |
| `alla_valdistrikt.zip`, uppackad i `scratchpad/unz/alla_valdistrikt/` | shapefil 2010, 5668 polygoner | shapefil i SWEREF99 TM (EPSG:3006), dbf latin-1, fälten `LKFV` och `VDNAMN` | 282 Göteborgsdistrikt, koder och namn identiska med resultatfilerna | `geo_overlap_2010_2022.csv`, `geo_overlap_2010_2014.csv`, `geo_majorna_2010.csv`, `geo_crosswalk_2010_2022_majorna.csv`, `distrikt_2010_goteborg.geojson` |
| `rostberattigade (6).xls`, `(7)`, `(8)` | röstberättigade per distrikt, kön, medborgarskap och fem åldersgrupper, för riksdag, landsting och kommun | xls, blad Sheet1, 20 kategorikolumner | 282 Göteborgsdistrikt per val, summan stämmer mot resultatfilerna för alla distrikt | `rostberattigade_2010_<val>.csv` och `_bred.csv`, `rostberattigade_majornaomradet_2010.csv` |
| `vallokal (2).xls` | vallokal per distrikt med adress och koordinat | xls, 25 kolumner | 282 Göteborgsrader, koordinater i RT90 | `vallokaler_2010.csv`, `vallokaler_2010_lokaler.csv` |
| `mottagna_fortidsroster (2).xls` | mottagna förtidsröster per lokal och dag | xls, 19 datumkolumner plus Totalt | 105 Göteborgslokaler, summorna stämmer mot källans egen summarad | `fortidsroster_2010.csv`, `fortidsroster_2010_lokaler.csv` |
| `valkretsmandat_R_2010.xls`, `_L_2010.xls`, `_K_2010.xls` | fasta valkretsmandat och röstberättigade per 1 mars | xls | fullständig | `valkretsar_goteborg.csv`, kommunvalkretsarnas namn |
| `mandatfordelning_per_valkrets_R (1).xls` | riksdagsmandat per valkrets, fasta och utjämning | xls | fullständig, 310 fasta plus 39 utjämning | `mandat_2010_riksdag.csv`, `mandat_valkrets_goteborg.csv` |
| `mandatfordelning_per_valkrets_K.xls` | kommunmandat per valkrets, odaterad fil | xls | daterad till 2010 genom att Göteborgs fyra kretsar är exakt lika med 2010 års XML och olika 2014 | `mandat_valkrets_goteborg.csv` |

Kvalitetsanmärkningar 2010: elva distrikt är markerade Modifierad och saknar
jämförelsetal mot 2006, inget av dem i Majorna. Röstberättigade skiljer sig mellan
riksdagsvalet (389821) och region- och kommunvalet (405033). Kolumnen OVR i riksdagsfilen
har en procentsats som är summan av småpartiernas avrundade procenttal och därför avviker i
fem rader från röster delat med giltiga. En rättelse: uppgiften om 19 distrikt i
stadsdelsnämnden Majorna 2010 går inte att belägga. Shapefilen, XML-filen och
`distrikt_2010_rd.csv` har alla exakt 17 distrikt med prefix 148009; de fyra extra raderna
14800001-14800004 är valnämndens onsdagsdistrikt för hela kommunen och hör inte till
Majorna. Se `noter/geo2010.md`.

### 2014

| Källa | Innehåll | Format och läsbarhet | Kvalitet | Blev |
| --- | --- | --- | --- | --- |
| `2014_riksdagsval_per_valdistrikt.xls` | riksdagsvalet per distrikt, flik `slutligt_valresultat_valdistrik`, rubriker på rad 2 | xls, xlrd, 36 kolumner | 301 Göteborgsrader | `roster_2014_rd_xls.csv`, `distrikt_2014_rd.csv` |
| `2014_landstingsval_per_valdistrikt.xls` | landstingsvalet, 122 kolumner | xls | 301 rader | `roster_2014_rf_xls.csv`, `distrikt_2014_rf.csv` |
| `2014_kommunval_per_valdistrikt.xlsx` | kommunvalet, 528 kolumner | xlsx, openpyxl, tom cell betyder noll | 301 rader | `roster_2014_kf_xls.csv`, `distrikt_2014_kf.csv` |
| `slutresultat.zip`, uppackad i `scratchpad/unz/slutresultat/` | Valmyndighetens XML 2014, valdag 20140914 | XML, ISO-8859-1, DTD 1.6 | fullständig, distriktsnamnen finns i klartext | `roster_2014_<val>_xml.csv`, `aggregat_2014_<val>.csv`, `fgval_2014_<val>.csv`, `mandat_2014_riksdag/kf/rf.csv` |
| `valgeografi_valdistrikt.zip`, uppackad i `scratchpad/unz/valgeografi_valdistrikt/` | shapefil 2014, 5837 polygoner | shapefil i SWEREF99 TM, dbf latin-1, fälten `VD` och `VD_NAMN` | 297 Göteborgsdistrikt | `geo_overlap_2014_2022.csv`, `geo_overlap_2014_2018.csv`, `geo_majorna_2014.csv`, `geo_crosswalk_2014_2022_majorna.csv`, `distrikt_2014_goteborg.geojson` |
| `rostberattigade (3).xls`, `(4)`, `(5)` | röstberättigade per distrikt och kategori | xls | 297 Göteborgsdistrikt per val, stämmer mot resultatfilerna | `rostberattigade_2014_<val>.csv` och `_bred.csv` |
| `vallokal (1).xls` | vallokal per distrikt, 31 kolumner | xls | 297 rader | `vallokaler_2014.csv`, `vallokaler_2014_lokaler.csv` |
| `mottagna_fortidsroster (1).xls` | förtidsröster per lokal och dag | xls | 72 Göteborgslokaler | `fortidsroster_2014.csv`, `fortidsroster_2014_lokaler.csv` |
| `mandatfordelning_per_valkrets_R.xls` (daterad 2014-10-31), `Valkretsmandat riksdag 2014.xls`, `Valkretsmandat landsting 2014.xls`, `Valkretsmandat riksdag 1988-2014.xls` | mandat och mandatunderlag | xls | fullständig | `mandat_valkrets_goteborg.csv`, `valkretsar_goteborg.csv`, riksdagsmandat 2002 |
| `mandatfordelning_per_valkrets_L.xls` | landstingsmandat per valkrets, odaterad fil | xls | daterad till omvalet 2011-05-15, inte september 2010, eftersom summan för län 14 är exakt jämförelsetalet i 2014 års XML | `mandat_valkrets_goteborg.csv` med år 2011 |

Kvalitetsanmärkningar 2014: 87 av 297 distrikt är markerade Modifierad och saknar
jämförelsetal mot 2010, däribland fem i Majorna. Landstingsvalets jämförelsetal avser
omvalet 2011, inte valet 2010, trots att filhuvudet anger 20100919. Excel har tappat
inledande nollor i numeriska partikoder, så 450 i kommunfilen är 0450 i XML.

### 2018

| Källa | Innehåll | Format och läsbarhet | Kvalitet | Blev |
| --- | --- | --- | --- | --- |
| `2018_R_per_valdistrikt.xlsx` | riksdagsvalet per distrikt, flikarna "R antal" och "R procent", 6325 datarader, 49 kolumner | xlsx, openpyxl | 351 Göteborgsrader, alla interna summor stämmer | `roster_2018_rd.csv`, `distrikt_2018_rd.csv`, `ogiltiga_2018_rd.csv`, `aggregat_2018_rd.csv` |
| `2018_L_per_valdistrikt.xlsx` | landstingsvalet, 63 kolumner, Gotland saknas | xlsx | 351 rader | `roster_2018_rf.csv` med flera |
| `2018_K_per_valdistrikt.xlsx` | kommunvalet, 235 kolumner, försättsblad förklarar de numeriska partikoderna | xlsx | 351 rader, valkretskolumnen tom eftersom Göteborg hade en enda kommunvalkrets | `roster_2018_kf.csv` med flera |
| `2018_mandat.xlsx` | mandatfördelning per valtyp och valkrets, daterad 2018-11-06 | xlsx, flik "Mandatfördelning", 3191 rader | fullständig för mandat, men röster listas bara för partier med mandat i respektive valkrets | `mandat_2018.csv`, `mandat_valkrets_goteborg.csv` |
| `2018_valgeografi_valdistrikt.zip`, uppackad i `scratchpad/unz/2018_valgeografi_valdistrikt/` | shapefil 2018, 6004 polygoner | shapefil i SWEREF99 TM, dbf i UTF-8 trots att cpg-filen saknas | 350 Göteborgsdistrikt, identiska koder och namn som resultatfilerna | `geo_overlap_2018_2022.csv`, `geo_majorna_2018.csv`, `geo_crosswalk_2018_2022_majorna.csv`, `geo_crosswalk_2018_2022_vastra_centrum.csv`, `distrikt_2018_goteborg.geojson` |
| `mappning_2014_2018.zip`, uppackad i `scratchpad/unz/mappning_2014_2018/` | Valmyndighetens officiella distriktsmappning, `vd-mappning-2014-2018.skv` (kod 2014, kod 2018, procent) och `vd-indelning-2018.skv` (kod, O/M/S/N) | textfiler i latin-1 med CRLF, kommentarrad först | 488 mappningsrader och 350 indelningsrader för Göteborg: 226 M, 122 O, 2 N | `kedja_2014_2018.csv`, `geo_mappning_2014_2018_jamforelse.csv`, `geo_indelning_2018_jamforelse.csv` |
| `rostberattigade.xls`, `rostberattigade (1).xls`, `rostberattigade (2).xls` | röstberättigade per distrikt och kategori, riksdag, landsting, kommun | xls, trasiga för xlrd, se nästa avsnitt | efter reparation 350 Göteborgsdistrikt per val, summorna stämmer exakt mot resultatfilerna | `rostberattigade_2018_<val>.csv` och `_bred.csv` |
| `vallokal.xls` | vallokal per distrikt, koordinater i WGS84 | xls, trasig för xlrd | efter reparation 350 rader | `vallokaler_2018.csv`, `vallokaler_2018_lokaler.csv` |
| `mottagna_fortidsroster.xls` | förtidsröster per lokal och dag | xls, trasig för xlrd | efter reparation 81 Göteborgslokaler | `fortidsroster_2018.csv`, `fortidsroster_2018_lokaler.csv` |
| `historik.val.se/val/val2018/valsedlar/partier/deltagande_partier.skv`, sparad i `scratchpad/dl2018/` | Valmyndighetens lista över deltagande partier | skv, ISO-8859-1, semikolon | används bara för partinamn | `partier_2018.csv` |
| Internet Archive, `slutresultat.zip` 2018, uppackad i `scratchpad/dl_webb/2018/unz/` | Valmyndighetens XML 2018 med jämförelsetal mot 2014, 875 filer | XML, ISO-8859-1, DTD 1.7 | 350 Göteborgsdistrikt, namnen inte gallrade | ännu inte inläst, se avsnittet om luckor |

Kvalitetsanmärkningar 2018: uppsamlingsdistriktet 14800000 bär 13316 giltiga
riksdagsröster, saknas i shapefilen och skriver noll i stället för tomt för röstberättigade
och valdeltagande. Uppgiften om 47 Majorna-Linnédistrikt går inte att belägga: både
resultatfilerna, shapefilen och Valmyndighetens indelningsfil har 45.

### 2022

| Källa | Innehåll | Format och läsbarhet | Kvalitet | Blev |
| --- | --- | --- | --- | --- |
| `Roster-per-distrikt-slutligt-antal-roster-inklusive-totalt-valdeltagande-riksdagsvalet-2022.xlsx` samt motsvarande för regionval och kommunval, alla i projektroten | röster per distrikt och parti för hela riket, flikarna `roster_RD`, `roster_RF`, `roster_KF` | xlsx, openpyxl med read_only, kolumn B ger den åttasiffriga koden ur formen `RD-14-80-0526` | 411 Göteborgsdistrikt per val, alla partier var för sig | `roster_2022_<val>.csv`, `distrikt_2022_<val>.csv`, `aggregat_2022_<val>.csv` |
| `data/valdata_2022.json` | färdig fil för sidan, de 23 Majornadistrikten och aggregat | json | slår ihop småpartier till Övriga och täcker bara Majorna | används enbart som facit, 667 partital kontrolleras vid varje bygge |
| `valdistrikt-vastra-gotalands-lan.zip` i projektroten, uppackad i `scratchpad/unz/valgeografi_2022/` som `VD_14_20220910_Val_20220911.json` | valgeografi 2022 för Västra Götalands län, 1090 objekt | GeoJSON, koordinater i SWEREF99 TM utan crs-element i filen | 410 Göteborgsdistrikt, alla geometrier giltiga | alla `geo_overlap_*_2022`- och `geo_majorna_*`-filer, samtliga crosswalkfiler mot 2022 |
| `jamforelser-2018-och-2022-valdistrikt-och-uppsamlingsdistrikt-v2.xlsx`, hämtad från val.se till `scratchpad/dl_webb/2022/` | Göteborgs och Valmyndighetens slutliga bedömning av vilka distrikt som är jämförbara 2018 mot 2022 | xlsx, flikarna Fysiska valdistrikt och Uppsamlingsdistrikt | 410 Göteborgsrader, 85 jämförbara, inga procentandelar | `mappning_2018_2022.csv` |
| `Mandatfordelning-jamforelser-mellan-2018-och-2022.xlsx` och `slutligt-valresultat-riksdagen-jamforande-statistik-2018-2022.xlsx`, båda i projektroten | mandat 2018 och 2022 för riket, valkretsar och kommuner | xlsx | riksdagsvalkretsen Göteborg avviker för SD, se nedan | `mandat_riksdag_riket.csv`, `mandat_valkrets_goteborg.csv` |
| `resultat.val.se/data/resultat/val2022/<sökväg>_S.json`, 1238 filer i `scratchpad/dl_webb/2022/json/` | slutligt resultat per valdistrikt i det nya JSON-formatet | json | röstetalen finns, men samtliga jämförelsefält mot 2018 är tomma eller noll | inte använt som datakälla |
| `statistik-alder-och-kon-riksdag-valdag-2022.xlsx` samt regionfullmäktige och kommunfullmäktige, alla i projektroten | röstberättigade 2022 efter ålder och kön | xlsx | inte kontrollerad för kompatibilitet med 2010-2018 | ingenting, ännu inte inläst |
| `majorna-valresultat-2022.xlsx` i projektroten | sidans egen sammanställning för Majorna 2022 | xlsx | sidans arbetsfil, inte primärkälla | inte använd som källa här, se `data/valdata_2022.json` |
| `fortidsroster.csv` i projektroten | mottagna förtidsröster per lokal och dag 2022, hela riket | csv, ISO-8859-1, semikolon, en rad per lokal | sidans arbetsfil, inte kontrollerad mot Valmyndighetens egna filer | inte inläst i `data/historik/`, motsvarigheten för 2010-2018 är `fortidsroster_<år>.csv` |

Kvalitetsanmärkningar 2022: Göteborg hade en enda kommunvalkrets, så nivån kommunvalkrets
saknas. Riksdagsvalkretsen Göteborg har SD 2 mandat enligt mandatfilen för 2018 men 3
enligt jämförelsefilens kolumn för 2018, en avvikelse som skrivs ut vid varje körning av
`scripts/historik/mandat_valkretsar.py`. Fasta mandat och utjämningsmandat per parti för
riksdags- och regionvalkretsen Göteborg 2022 saknas i allt material som gått att hämta.

## De fem trasiga 2018-filerna och hur de lagades

Fem xls-filer från 2018 går inte att öppna med xlrd. Felet är detsamma i alla fem:
`xlrd.compdoc.CompDocError: Workbook corruption: seen[2] == 4`, alltså att xlrd:s kontroll av
sektortabellen i det sammansatta OLE-dokumentet hittar sektorer som är tilldelade två
gånger. Filerna är i övrigt intakta. Med `olefile` går det att öppna dokumentet och läsa
strömmen `Workbook` rakt av, och den strömmen kan sedan skickas till xlrd med argumentet
`file_contents`, som inte gör sektorkontrollen. Innehållet skrevs därefter cell för cell
till en ny xlsx-fil med openpyxl. De reparerade kopiorna ligger i `scratchpad/repaired/`
och är skapade 2026-09-03 klockan 19.13 enligt `docProps/core.xml` i respektive fil.

| Originalfil | Byte | Rader gånger kolumner i Workbook-strömmen | Reparerad kopia | Rader gånger kolumner |
| --- | --- | --- | --- | --- |
| `rostberattigade.xls` | 2877952 | 6005 gånger 26 | `2018_rostberattigade_R.xlsx` | 6005 gånger 26 |
| `rostberattigade (1).xls` | 3052032 | 5964 gånger 28 | `2018_rostberattigade_L.xlsx` | 5964 gånger 28 |
| `rostberattigade (2).xls` | 3072512 | 6005 gånger 28 | `2018_rostberattigade_K.xlsx` | 6005 gånger 28 |
| `vallokal.xls` | 3124224 | 6005 gånger 31 | `2018_vallokal.xlsx` | 6005 gånger 31 |
| `mottagna_fortidsroster.xls` | 1324544 | 2741 gånger 26 | `2018_mottagna_fortidsroster.xlsx` | 2741 gånger 26 |

Källa: filstorlekar ur filsystemet, dimensioner lästa med olefile och xlrd ur originalen
respektive med openpyxl ur kopiorna 2026-09-04.

Reparationen är kontrollerad mot en oberoende källa: summan av de tjugo
röstberättigadekategorierna per distrikt är exakt lika med kolumnen RÖSTBERÄTTIGADE i
`2018_R_per_valdistrikt.xlsx`, `2018_L_per_valdistrikt.xlsx` och `2018_K_per_valdistrikt.xlsx`
för alla 350 Göteborgsdistrikt i alla tre valen. Distriktskoderna i den reparerade
vallokalsfilen är identiska med resultatfilernas 350 koder, och förtidsröstfilens
dagkolumner summerar till kolumnen Totalt för varje lokal i hela riket.

En rättelse: `docs/historik/noter/rostberattigade.md` skriver att
`2018_rostberattigade_R.xlsx` är en kopia av `rostberattigade (1).xls`. Rubrikraden i
originalen visar att det är fel. `rostberattigade.xls` börjar med `riksdagsvalkrets_id` och
motsvarar R, `rostberattigade (1).xls` börjar med `landstings_id` och motsvarar L, och
`rostberattigade (2).xls` börjar med `län_id` och motsvarar K. De reparerade kopiorna har
rätt innehåll under rätt namn, så inga tal berörs, bara den nämnda meningen i noteringen.

Om scratchpad rensas måste reparationen göras om innan
`scripts/historik/rostberattigade_2010_2018.py` och
`scripts/historik/vallokaler_fortidsroster_2010_2018.py` går att köra.

## Filer som saknas eller inte gick att hämta

### 2002 per valdistrikt

Uppgiften kunde lösas, men inte på det sätt som var tänkt. Valmyndighetens XML för 2002 är
borta: adresserna `senaste/slutresultat_1480R.xml`, `_1480K.xml`, `_1480L.xml`, `_00R.xml`,
`_00K.xml` och `_00L.xml` länkas från sidorna men ger 404, liksom protokollsidorna
`protokoll/slutresultat/1480K.html`, `1480R.html`, `1480L.html` och `1416KR.html`.
Textversioner finns bara på riks- och kommunnivå: `14R/14-text.html`,
`14R/1480/148001-text.html` och `14R/1480/14801701-text.html` ger alla 404. Lösningen blev
att hämta de 858 distriktssidorna i HTML från
`https://historik.val.se/val/val_02/slutresultat/14X/1480/<kod>.html` och kontrollera dem
mot kommunens textsida. Det som fortfarande saknas för 2002 är röstberättigade per distrikt,
som inte finns på någon sida på historik.val.se; för Göteborg som helhet går de att läsa ur
2006 års XML som jämförelsetal (rd 357876, rf och kf 375849), men inte per distrikt. En
möjlig men oprövad väg är SCB.

### Valgeografi 2002

Finns inte. Sidan Rådata från val 2002-2022 på val.se anger uttryckligen att material från
2002 bara finns i textformat. En sökning i Internet Archive över val.se-domänerna med
filtret `original:.*(gis|valgeografi|valdistrikt).*\.zip.*` ger som äldsta kartmaterial 2006
års shapefiler under `historik.val.se/val/val2006/slutlig_ovrigt/statistik/kartor/`.
Konsekvensen är att 2002 inte kan knytas geografiskt till Majorna.

### Officiell mappning 2006 till 2010 och 2010 till 2014

Finns inte, och har aldrig publicerats. Kontrollerat på tre sätt: statistiksidorna
`https://historik.val.se/val/val2010/statistik/index.html` och
`https://historik.val.se/val/val2014/statistik/index.html` innehåller varken ordet mappning
eller indelning; en sökning i Internet Archive med filtret `original:.*mappning.*` ger tre
träffar i hela arkivet, alla för 2018 eller EP-valet 2019; filtret `original:.*indelning.*`
ger bara nutida informationssidor. I stället används attributet RÖSTER_FGVAL i
Valmyndighetens XML, som anger föregående vals röstetal per parti och distrikt och därmed
identifierar vilket äldre distrikt som avses.

### 2018 års XML

Den ursprungliga adressen `https://data.val.se/val/val2018/slutresultat/slutresultat.zip`
ger 404, och statistiksidan för 2018 har rubriken Rådata i XML-format men med texten
"Protokoll gallrat" och ingen länk. 24 adressvarianter provades och gav alla 404, bland dem
`https://historik.val.se/val/val2018/slutresultat/slutresultat.zip`,
`https://historik.val.se/val/val2018/statistik/slutresultat.zip`,
`https://historik.val.se/val/val2018/slutresultat/slutresultat_1480R.xml` och
`https://www.val.se/val/val2018/statistik/slutresultat.zip`. Filen finns däremot i Internet
Archive på
`https://web.archive.org/web/20210926125427id_/https://data.val.se/val/val2018/slutresultat/slutresultat.zip`
(48716326 byte) och är hämtad till
`scratchpad/dl_webb/2018/slutresultat_2018_wayback.zip`. Den innehåller
`slutresultat_1480R.xml`, `_1480L.xml` och `_1480K.xml` med 350 valdistrikt vardera och
5034, 5099 respektive 5699 förekomster av jämförelsetal mot 2014.

Filen är nu flyttad till en beständig plats, `Historiska dokument/dl_webb/2018/unz/`, och
inläst: `slutresultat_1480R.xml`, `_1480L.xml`, `_1480K.xml` (Göteborgs kommun) samt
`slutresultat_00R.xml`, `_00L.xml`, `_00K.xml` (riket, för en lättviktig integritetskontroll
av Göteborgs kommunsumma). Se `docs/historik/noter/xml2018.md` för vad inläsningen gav.

### Officiell mappning 2018 till 2022

Finns, men heter inte mappning utan "Jämförelser 2018 och 2022 - valdistrikt och
uppsamlingsdistrikt", och ligger på val.se under Analyser och jämförelser samt Rådata från
val 2002-2022. Två versioner finns: v1 publicerad 2022-09-05, alltså före valdagen, vars
adress i dag ger 404 och som bara finns i Internet Archive, och v2 publicerad 2022-10-27 på
`https://www.val.se/download/18.162047b519a91d0533119148/1666857349837/jamforelser-2018-och-2022-valdistrikt-och-uppsamlingsdistrikt-v2.xlsx`.
För Göteborgs 410 rader är de två versionerna identiska. Filen anger bara ja eller nej per
distrikt och saknar de procentandelar som motsvarande skv-fil för 2014 till 2018 har. Det
går alltså inte att vikta delade distrikt 2018 till 2022 med officiella tal.

### 2022 års rådata med jämförelse mot 2018

Fälten finns men är tomma. Varje distrikts-JSON på resultat.val.se har fälten `jamforbar`,
`totaltAntalRosterForegaendeVal`, `antalRostberattigadeForegaendeVal`,
`valdeltagandeForegaendeVal` samt per parti `antalRosterForegaendeVal` och
`forandringAntalRoster`. I samtliga 1238 hämtade filer är `jamforbar` false, summorna null
och partitalen noll, både i det slutliga och det preliminära räkningstillfället. Det beror
inte på att Göteborgs distrikt ändrades: kontrollhämtning av ett distrikt i Upplands Väsby
som jämförelsefilen uttryckligen kallar jämförbart mot samma kod 2018 ger samma tomma fält.
Filen `preliminar-riksdagsval-jamforande-statistik-2018-2022-med-uppsamlingsdistrikt-ny.xlsx`
har trots sitt namn bara flikarna Riksdag, Valkrets och Per Kommun, ingen distriktsnivå, och
samma sak gäller `slutligt-valresultat-riksdagen-jamforande-statistik-2018-2022.xlsx` i
projektroten. En jämförelse 2018 mot 2022 per distrikt måste därför byggas själv genom att
lägga samman `mappning_2018_2022.csv` med 2018 års egna resultat.

### Övrigt som saknas

- Mandat för kommunfullmäktige och regionfullmäktige 2006 och 2010 finns i XML-källorna men
  är aldrig utskrivna till CSV och saknas därför i tabellen `mandat`.
- Fasta mandat och utjämningsmandat per parti för riksdags- och regionvalkretsen Göteborg
  2022 saknas helt. Ett försök att hämta dem från val.se misslyckades: resultat.val.se är en
  javascriptsida och statistiksidan gav 404.
- Röstberättigade efter ålder och kön för 2022 finns i projektroten men är inte inlästa.
- Vallokaler och förtidsröstningslokaler för 2002, 2006 och 2022 ingår inte i materialet.
- Röstberättigade på valdagen för omvalet till regionfullmäktige 2011 saknas.
- Materialet för 2026 (`valdistrikt-jamforelser-mellan-2022-och-2026.xlsx` med flera, se
  `noter/webbkallor.md`) finns bara i den sessionsbundna mappen `scratchpad/dl_webb/2026/`
  och är inte skrivet till `data/historik/`. Uppgiften att fjorton av Majornas 23 distrikt är
  jämförbara 2022 mot 2026 är därför bara belagd i `noter/webbkallor.md`, inte i någon fil i
  `data/historik/`.

## Vad datan möjliggör redaktionellt

Nedan står vad som går att publicera utan förbehåll, vad som kräver en förklarande mening
och vad som inte går.

### Säkert

**Tidsserier per parti 2006-2022 för Majorna, Göteborg och riket, i alla tre valen.**
Underlag: `majorna_tidsserie.csv` och `jamforelse_tidsserie.csv`, 2487 rader.
Områdesdefinitionen är belagd både geometriskt och med Valmyndighetens egna jämförelsetal,
och för steget 2006 till 2010 ger de två metoderna exakt samma siffror, parti för parti, i
alla tre valen. Andelen är omräknad ur röster och giltiga, inte kopierad från källan, så
åren är räknade likadant.

**Valdeltagande över tid för Majorna, Göteborg och riket 2006-2022.** Samma filer.
Röstberättigade per distrikt kommer ur källorna för alla år från 2006.

**Röstdelning över tid, alltså skillnaden mellan riksdagsval och kommunval i samma
område.** Alla tre valen finns per distrikt varje år, så skillnaden i andel mellan rd och kf
för samma parti och år går att räkna direkt ur `jamforelse_tidsserie.csv`.

**Röstberättigade efter ålder, kön och medborgarskap för 2010, 2014 och 2018.** Underlag:
`rostberattigade_<år>_<val>.csv` och `rostberattigade_majornaomradet_<år>.csv`. Kategorierna
är ordagrant desamma alla tre åren, så de går att jämföra rakt av. Utländska medborgare
finns bara i region- och kommunvalens filer, vilket är rätt: de har inte rösträtt till
riksdagen.

**Förtidsröstning på Majornas bibliotek 2010, 2014 och 2018.** Underlag:
`fortidsroster_majornaomradet_2010_2018.csv`. Biblioteket tog emot 4585, 6667 och 7470
förtidsröster de tre åren, vilket är plats 7, 5 och 7 bland Göteborgs alla
förtidsröstningslokaler. Lokal-id 8357 är detsamma alla tre åren.

**Mandat i riksdagen 2002-2022 och i Göteborgs kommunfullmäktige.** Underlag:
`mandat_riksdag_riket.csv` och `mandat_valkrets_goteborg.csv`, kontrollerade så att varje år
summerar till 349 respektive 81.

### Kräver förbehåll

**Grannområden som jämförelse.** Masthugget och Linnéstaden finns som distriktsgrupper
alla år från 2006, men ingen av dem har någon färdig områdesdefinition i materialet
motsvarande den för Majorna. För 2018 mot 2022 finns hela Västra Centrum utrett i
`geo_crosswalk_2018_2022_vastra_centrum.csv`, och där ritades Linnéstadens kärna om
grundligt: sex distrikt 2018 blev sju 2022 och inget par har mer än 82 procent gemensam yta.
En jämförelse mellan Majorna och grannområdena kräver alltså att motsvarande
områdesdefinition byggs först, med samma metod som för Majorna. Kungsten finns som
valdistriktsnamn 2018 (14805043, Västra Göteborg, Kungsten) och 2022 (14800706, Västra
Göteborg, Kungsten) enligt `distrikt_2018_rd.csv` och `distrikt_2022_rd.csv`, men saknas som
egen kod 2006, 2010 och 2014.

**Förtidsröstning som mått på Majornabornas beteende.** Förtidsröster räknas in i väljarens
hemdistrikt oavsett var de lämnades. Filerna säger var göteborgarna förtidsröstade, inte hur
många i Majorna som förtidsröstade. Formuleringen måste vara "så många röster togs emot på
Majornas bibliotek", inte "så många i Majorna förtidsröstade".

**Jämförelser mellan enskilda distrikt över tid.** Se det andra dokumentet,
`valdistrikt-historik.md`. Bara Godhem och Gatenhielmska har en obruten kedja 2006-2022, och
även Godhem har en gränsändring 2022 på några procent av ytan.

**Småpartier över tid.** Partikoder skiljer sig mellan år och källor. Tabellen `parti_kanon`
täcker de fem fall som är belagda i granskningarna, men övriga småpartier kan ha olika koder
olika år. För tidsserier finns i stället raden `SUMMA_ÖVRIGA`, som är residualen efter de
elva partier som följs genom hela perioden.

**Uppsamlings- och onsdagsdistrikten.** Varje år finns röster som inte kan fördelas på
distrikt: 8883 giltiga riksdagsröster i Göteborg 2006 och 13316 år 2018. De ingår i
kommunens totaler men inte i något områdesaggregat, vilket gör att summan över Majornas
distrikt alltid är något lägre än områdets verkliga röstetal.

### Går inte

**Majorna 2002.** Det finns ingen valgeografi för 2002, gränserna ritades om mellan 2002 och
2006, och Stigberget låg 2002 inne i Masthugg 1-8 och kan inte skiljas ut. 2002 finns med
för Göteborg och riket, inte för Majorna. Uppgiften att Karl Johan 1-12 hade 11519 giltiga
riksdagsröster mot 14396 i 2006 års tretton distrikt visar hur stor skillnaden är.

**Valdeltagandet för riket 2002.** Röstberättigade för riket 2002 saknas i allt material, så
valdeltagandet på riksnivå det året kan inte räknas fram.

**Regionvalet 2010 jämfört bakåt med Valmyndighetens egna tal.** Jämförelsetalen i 2014 års
landstings-XML avser omvalet 2011-05-15, inte valet 2010, och omvalets fil finns inte bland
källorna.

## Rekommenderade nästa steg

1. **Läs in 2018 års XML från Internet Archive.** Gjort, se
   `docs/historik/noter/xml2018.md`. XML- och xlsx-byggena för 2018 är talmässigt
   identiska, och Valmyndighetens FGVAL bekräftar klassningen i `kedja_2014_2018.csv` fullt
   ut, men FGVAL saknas helt för alla delade, omritade och nya distrikt, så steget 2014 till
   2018 är fortfarande utan oberoende sifferkontroll för just de distrikt som ändrats.
2. **Flytta de reparerade 2018-filerna ut ur scratchpad.** Utan dem går två av skripten inte
   att köra om, och reparationen måste då göras från början.
3. **Läs in röstberättigade efter ålder och kön för 2022** ur de tre
   `statistik-alder-och-kon-*.xlsx` som redan ligger i projektroten, och kontrollera att
   kategorierna är desamma som 2010-2018. Det förlänger den enda demografiska serien från tre
   till fyra val.
4. **Bygg `mappning_2022_2026.csv`** ur den redan hämtade
   `valdistrikt-jamforelser-mellan-2022-och-2026.xlsx` (se `noter/webbkallor.md`). Fjorton av
   Majornas 23 distrikt är jämförbara 2022 mot 2026, och där de är det är koden oförändrad.
   Filen behövs inför valnatten 13 september 2026. Flytta samtidigt filen, liksom de fyra
   andra 2026-nedladdningarna som `noter/webbkallor.md` dokumenterar (valgeografi 2026,
   samtliga valdistrikt 2026, mandatfördelning 2022 och 2026, formatbeskrivningen av 2026
   års resultatfiler), ut ur `scratchpad/dl_webb/2026/` till en beständig plats, eftersom
   scratchpad försvinner med sessionen.
5. **Kontrollera tidigt på valnatten 2026 om fältet `valdistriktskodForegaendeVal` faktiskt
   fylls i.** Formatbeskrivningen lovar det, men 2022 års motsvarande fält visade sig tomma.
6. **Bygg en områdesdefinition för Masthugget och Linnéstaden** med samma metod som för
   Majorna, om grannjämförelser ska publiceras.
7. **Skriv ut mandaten för kommunfullmäktige och regionfullmäktige 2006 och 2010** ur
   XML-källorna, där de redan finns.
8. **Rätta meningen om filernas ursprung i `noter/rostberattigade.md`** enligt avsnittet om de
   trasiga 2018-filerna ovan.
9. **Överväg SCB som källa till röstberättigade per distrikt 2002.** Det är den enda
   återstående vägen till ett valdeltagande per distrikt det året, och den är oprövad.
