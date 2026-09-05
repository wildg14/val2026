# Datamodell för historikdatabasen

Filen `/Users/daniel/code/Temp/data/historik/majorna_historik.sqlite` (SQLite 3, cirka 27 MB)
byggs av `/Users/daniel/code/Temp/scripts/historik/bygg_databas.py` ur CSV-filerna i
`data/historik/`, ur `data/valdata_2022.json` och ur Valmyndighetens tre xlsx-filer för 2022.
Databasen byggs om från grunden vid varje körning; den innehåller inga handskrivna tal.

Kör om med

    /Users/daniel/code/Temp/.venv/bin/python \
        /Users/daniel/code/Temp/scripts/historik/bygg_databas.py

## Omfattning

Hela Göteborgs kommun (1480) för valen 2002, 2006, 2010, 2014, 2018 och 2022, i tre val:
`rd` riksdag, `rf` region eller landsting, `kf` kommunfullmäktige. Riket och Västra
Götaland finns på aggregatnivå. Distriktsantal per år: 2002 286, 2006 283 (varav 4
uppsamlingsdistrikt), 2010 286 (4), 2014 301 (4), 2018 351 (1), 2022 411 (1).

## Tabeller

| Tabell | Rader | Innehåll |
| --- | --- | --- |
| `val` | 18 | ett år och val per rad, med valdag och källa till valdagen |
| `distrikt` | 1918 | ett valdistrikt per år, med namn, valkrets och områdesprefix |
| `roster` | 92333 | röster per år, val, distrikt och parti |
| `distrikt_summa` | 5754 | giltiga, ogiltiga, röstande, röstberättigade och valdeltagande per distrikt |
| `aggregat` | 4126 | riket, Västra Götaland, Göteborg och valkretsar per parti |
| `crosswalk` | 11961 | kopplingar mellan distriktsindelningar olika år |
| `majorna_medlem` | 108 | vilka distrikt som utgör Majorna respektive år |
| `tidsserie` | 2487 | färdigsummerad serie för Majorna, Göteborg och riket |
| `parti_kanon` | 5 | harmonisering av partikoder mellan år och källor |
| `partier` | 622 | partibeteckningar per år |
| `rostberattigade_kategori` | 55740 | röstberättigade per distrikt, kön, medborgarskap och åldersgrupp (2010, 2014, 2018) |
| `fortidsroster` | 5160 | mottagna förtidsröster per lokal och dag (2010, 2014, 2018) |
| `mandat` | 1519 | mandat per val, nivå, valkrets och parti |

### val (ar, val, valdag, kalla)

Nyckel `(ar, val)`. `valdag` är hämtad ur en fil, inte ur allmän kunskap: 2002 och 2006 ur
attributen `VALDAG_FGVAL` och `VALDAG` i `dl2006/slutresultat_1480R.xml`, 2010 och 2014 ur
`VALDAG` i motsvarande XML, 2018 ur kolumnen `valdag` i `vallokaler_2018.csv` och 2022 ur
filnamnet `VD_14_20220910_Val_20220911.json`. `kalla` anger exakt var.

### distrikt (ar, kod, namn, valkrets, kommunvalkrets, sdn_eller_omrade, uppsamlingsdistrikt, kalla)

Nyckel `(ar, kod)`. Koden ensam räcker inte: 115 av 2006 års koder används redan 2002 för
helt andra distrikt (se `granskning_2006.md`), så alla sammanfogningar måste ske på
`(ar, kod)`.

- `valkrets` är riksdagsvalkretsen som källan anger den, `kommunvalkrets` är kolumnen
  `valkrets` i kommunvalsfilen. 2018 och 2022 har Göteborg en enda kommunvalkrets och
  fältet är därför tomt respektive "Göteborg".
- `sdn_eller_omrade` är prefixet före första kommatecknet i distriktsnamnet, annars namnet
  utan avslutande siffra. Det ger "Majorna" 2010, "Majorna-Linné" 2014 och 2018,
  "Västra Centrum" 2022 och "Kungsladugård-Sanna" 2006. Fältet är härlett ur namnet och
  ska inte användas för att avgränsa Majorna, se `majorna_medlem`.
- `uppsamlingsdistrikt` är 1 för de distrikt som bär röster som inte kan fördelas
  geografiskt (namnen "Uppsamlingsdistrikt", "Onsdagsdistrikt" och
  "I vallokal ej räknade röster"). De ska uteslutas ur all geografisk analys.

### roster (ar, val, kod, parti, parti_kalla, roster, kalla, parti_kanon)

Nyckel `(ar, val, kod, parti)`. `parti_kalla` är förkortningen som källan skriver den,
`parti` den normaliserade koden från extraktionssteget och `parti_kanon` den harmoniserade
koden som ska användas i tidsserier. `kalla` namnger filen och där det behövs fliken.

### distrikt_summa (ar, val, kod, giltiga, ogiltiga, rostande, rostberattigade, valdeltagande, blanka, kalla)

Nyckel `(ar, val, kod)`. `ogiltiga` innehåller blanka plus övriga ogiltiga. `blanka` är
särredovisad från och med 2006; 2002 saknas den och kolumnen är tom.
`rostberattigade` och `valdeltagande` är tomma för uppsamlingsdistrikt och för hela 2002.

### aggregat (ar, val, niva, parti, roster, andel, parti_kalla, giltiga, rostande, rostberattigade, parti_kanon, kalla)

Nyckel `(ar, val, niva, parti)`. Nivåer: `riket`, `vgregion`, `goteborg`, kommunvalkretsarna
med källans egna namn ("Göteborg 1" till "Göteborg 4" 2002 och 2006, "Göteborg, Centrum"
med flera 2010 och 2014) samt 2002 års `ej_raknade_i_vallokal`. Nivåer med suffixet
`|ovriga` kommer ur 2002 års separata uppdelning av övriga partier.

### crosswalk (ar_fran, ar_till, kod_fran, kod_till, andel_av_fran, andel_av_till, typ, kalla)

En rad per belagd koppling mellan två indelningar. Ingen nyckel, flera rader per par är
normalt. `typ` säger vilken sorts belägg raden bygger på:

| typ | Antal | Betydelse |
| --- | --- | --- |
| `geo_overlap` | 9718 | geometriskt överlapp; `andel_av_fran` och `andel_av_till` är andelar av respektive distrikts yta |
| `kedja:<utfall>` | 1348 | kedjeanalysens troligaste motsvarighet, utfall `identisk`, `namnbyte`, `delad`, `omritad`, `sammanslagen` eller `ny` |
| `mappning_officiell:jamforbart=ja/nej` | 410 | Göteborgs stads jämförelsefil 2018 till 2022 |
| `fgval` och `fgval:exakt` | 485 | koppling belagd med Valmyndighetens föregående vals röster |

Areaandelar är inte befolkningsandelar. Stora ytor i Majorna är hamn, park och
Slottsskogen, så `geo_overlap` säger hur gränserna gick, inte hur många väljare som
flyttades. Använd `typ='mappning_officiell'` och `typ='fgval'` när frågan gäller väljare.

### majorna_medlem (ar, kod, namn, klass, andel_i_majorna, ingar_i_jamforbart_majorna, beslut, kalla)

Nyckel `(ar, kod)`. `klass` och `andel_i_majorna` kommer ur `geo_majorna_<ar>.csv`, som
mäter varje distrikts yta mot unionen av 2022 års 23 Majornadistrikt (4,6554 km2).
`ingar_i_jamforbart_majorna` är 1 när `andel_i_majorna` är minst 0,5, och `beslut` skriver
ut det avgörandet i klartext för varje rad. Se `noter/databas.md` för hur många distrikt
som blir kvar per år.

Tre trösklar används i de bakomliggande stegen utan att vara samma sak: 0,1 procent av
unionens yta för att ett distrikt alls tas med i `geo_majorna_<ar>.csv`, 0,95 för klassen
`klass = 'inne'` i samma fil, och 0,5 för `ingar_i_jamforbart_majorna` här. De ger samma
antal distrikt alla år (se `geo2018.md` rad 67 för 2018). Tabellen innehåller bara de
distrikt som togs med i respektive `geo_majorna_<ar>.csv`; att den tomma `delvis`-klassen
(andelar mellan 0,05 och 0,95) verkligen är tom alla år framgår av noteringarna `geo2006.md`,
`geo2010.md`, `geo2014.md` och `geo2018.md`, som skriver ut även uteslutna kandidater, inte
av `majorna_medlem` självt.

### tidsserie (ar, val, niva, parti, roster, andel, giltiga, rostande, rostberattigade, valdeltagande, antal_distrikt, metod)

Nyckel `(ar, val, niva, parti)`. Nivåerna är `majorna`, `goteborg` och `riket`. `andel` är
`roster` genom `giltiga` i procent, omräknad här och inte kopierad från källan. Partiet
`SUMMA_ÖVRIGA` är residualen giltiga minus V, S, MP, SD, M, C, L, KD, D, FI och K, så att
åren går att jämföra trots att 2002 slår ihop småpartier och senare år listar dem.
`metod` beskriver hur raden räknats fram, inklusive vilken definition av Majorna som använts.

## Källprioritering

1. För 2006, 2010 och 2014 finns både Valmyndighetens XML och Excelfiler. Databasen använder
   XML (`roster_<ar>_<val>_xml.csv`), eftersom granskningarna visar att talen är identiska
   men xls-filerna innehåller nollrader som XML saknar. `kalla` i tabellen `roster` anger
   XML-filen.
2. 2002 kommer ur `roster_2002_<val>.csv` med den samlade raden `ÖVR` utbytt mot
   uppdelningen i `roster_2002_<val>_ovriga.csv`. Uppdelningen summerar exakt till `ÖVR` i
   alla 286 distrikt och alla tre val, kontrollerat vid bygget.
3. 2018 kommer ur `roster_2018_<val>.csv` (Excelfilernas antalflikar).
4. 2022 läses ur Valmyndighetens tre xlsx-filer, som täcker hela riket. Skriptet skriver
   samtidigt `roster_2022_<val>.csv`, `distrikt_2022_<val>.csv` och `aggregat_2022_<val>.csv`
   i samma långa format som övriga år. Alla 667 partital i de 23 Majornadistrikten
   kontrolleras mot `data/valdata_2022.json` vid varje körning.
5. Röstberättigade för Göteborg 2002 saknas i 2002 års källor och hämtas i tidsserien ur
   `valkretsar_goteborg.csv`, som i sin tur läst dem ur 2006 års XML.

## Kända luckor

- 2002 saknar geografi. Det finns ingen shapefil, och 2002 års distrikt i området
  (Karl Johan 1-12) täcker bara grovt samma yta som 2006 års 13 distrikt. Stigberget låg
  2002 inne i Masthugg 1-8 och går inte att skilja ut. Året finns därför i `roster`,
  `distrikt_summa` och `aggregat`, men inte i Majorna-tidsserien.
- 2002 saknar röstberättigade per distrikt och särredovisar inte blanka röster.
- 2018 och 2022 har Göteborg en enda kommunvalkrets, så kommunvalkretsnivån saknas de åren.
- `rostberattigade_kategori` och `fortidsroster` finns bara för 2010, 2014 och 2018.
- FGVAL-kedjan är inte komplett. 5 av 17 jämförbara Majornadistrikt 2014 är markerade
  Modifierad och saknar föregående vals röster, och `fgval_2014_rf.csv` avser omvalet 2011,
  inte 2010.
- Partikoder skiljer sig mellan år och källor. `parti_kanon` täcker de fall som är belagda
  (KPML lika med K, SFV lika med SPVG, 0524 lika med PP, SJVÅP lika med SJVP, OVR lika med
  ÖVR, samt nollutfyllnad av numeriska koder). Övriga småpartier kan ha olika koder olika år.
- Alla tal är slutliga sammanräkningar. Inga onsdags- eller uppsamlingsröster kan fördelas
  på distrikt något år.

## Exempel på frågor

### 1. Vänsterpartiets andel i Majorna per år i kommunvalet

```sql
SELECT ar, roster, giltiga, andel, antal_distrikt
FROM tidsserie
WHERE niva = 'majorna' AND val = 'kf' AND parti = 'V'
ORDER BY ar;
```

ger 2006 2731 av 18807 (14,52 procent), 2010 3233 av 20456 (15,80), 2014 4446 av 21063
(21,11), 2018 6242 av 21616 (28,88) och 2022 7479 av 21620 (34,59).

Samma sak direkt ur grunddata, utan den färdiga tidsserien:

```sql
SELECT r.ar, SUM(r.roster) AS roster
FROM roster r
JOIN majorna_medlem m ON m.ar = r.ar AND m.kod = r.kod
WHERE r.val = 'kf' AND r.parti_kanon = 'V' AND m.ingar_i_jamforbart_majorna = 1
GROUP BY r.ar ORDER BY r.ar;
```

### 2. Valdeltagande per år, Majorna mot Göteborg mot riket

```sql
SELECT ar,
       MAX(CASE WHEN niva = 'majorna'  THEN valdeltagande END) AS majorna,
       MAX(CASE WHEN niva = 'goteborg' THEN valdeltagande END) AS goteborg,
       MAX(CASE WHEN niva = 'riket'    THEN valdeltagande END) AS riket
FROM tidsserie
WHERE val = 'rd'
GROUP BY ar ORDER BY ar;
```

ger 2006 79,31 mot 79,54 mot 81,99, 2010 82,80 mot 82,72 mot 84,63, 2014 82,89 mot 82,82
mot 85,81, 2018 84,33 mot 84,28 mot 87,18 och 2022 82,76 mot 80,71 mot 84,21. För 2002
finns bara Göteborg (77,54).

### 3. Vilka distrikt 2018 som bygger upp Mariaplan 2022 (14800530)

```sql
SELECT cw.kod_fran,
       d.namn,
       ROUND(cw.andel_av_till * 100, 1) AS procent_av_2022_distriktet,
       ROUND(cw.andel_av_fran * 100, 1) AS procent_av_2018_distriktet
FROM crosswalk cw
JOIN distrikt d ON d.ar = cw.ar_fran AND d.kod = cw.kod_fran
WHERE cw.ar_fran = 2018 AND cw.ar_till = 2022
  AND cw.typ = 'geo_overlap' AND cw.kod_till = '14800530'
  AND cw.andel_av_till >= 0.01
ORDER BY cw.andel_av_till DESC;
```

ger 14801011 Gröna Vallen (52,1 procent av 2022-distriktet, 47,7 procent av 2018-distriktet),
14801015 Mariaplan (25,0 och 31,1) och 14801013 Kungsladugård Västra (22,9 och 21,0).
Byt `typ` till `mappning_officiell:jamforbart=ja` för Göteborgs stads egen bedömning av
vilka distrikt som är direkt jämförbara.
