# Räknemätaren: hur mycket som är räknat, som stapel

Beslutad 2026-09-13 (valdagen, natten) av Daniel. Bygget måste vara pushat i god tid före 20.00, eftersom `valgrafik.js` och `valgrafik.css` cachas tio minuter hos läsarna.

## Vad

Två mätare som visar hur stor del av distrikten som är räknade, i sidans eget bildspråk (samma spår och fyllning som toppsvarets staplar, men tunnare).

**Toppen**, direkt under statusraden, två rader:

```
Majorna                        5 av 23 distrikt räknade
[██████░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░]
Sverige                        2 100 av 6 626
[████████░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░]
```

- Majorna: `raknadeIVal("rd")`, samma tal statusraden har i dag.
- Sverige: `aggregat.riket.rd.antal_distrikt` av `totalt_distrikt` (`harRaknade`). Saknas talen (äldre år, CSV-vägen) utelämnas raden.

**Kartsektionen**, mellan växeln (Största parti, Partistyrka) och legenden, en rad som följer valknapparna:

```
Riksdagsvalet                  5 av 23 distrikt räknade
[██████░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░]
```

- `raknadeIVal(state.val)`. De tre valen räknas i olika takt, så den kan visa 12 av 23 när toppen visar 9.

## När

Mätarna visas när statusraden är i sitt levande läge: `KONFIG.valnatt` sant, det visade året är `KONFIG.standardAr`, och räkningen inte är färdig (preliminär status, eller slutlig status med färre än 23 räknade i riksdagsvalet - samma villkor som ger statusraden "Ladda om"). När allt är räknat står stapeln full tills valnattsläget slås av; då försvinner mätarna. Före valdagen, på 2022 och övriga år, och efter sluträkningen finns de inte.

## Statusraden kortas

Mätaren bär talet, så statusraden slutar upprepa det:

| I dag | Efter |
|---|---|
| Preliminärt, 5 av 23 distrikt räknade. Uppdaterad 20:41. Ladda om | Preliminärt. Uppdaterad 20:41. Ladda om |
| Slutlig räkning pågår, 12 av 23 distrikt räknade. Ladda om | Slutlig räkning pågår. Ladda om |

Övriga grenar (tom före valdagen, "Slutligt resultat 2022. Ladda om", "Preliminärt resultat 2026", "Slutligt resultat, riksdagsvalet 2026.") ändras inte.

Kortets underrad i kartsektionen, "N av 23 distrikt räknade." för Hela Majorna på valnatten, tas bort av samma skäl; mätaren står precis ovanför kartan. Kohorttexten "räknat på N jämförbara distrikt av 23" under de små talen är en annan sak (jämförbara, inte räknade) och står kvar.

## Utseende

- Rad: etikett till vänster i stenfärg 16 px, talet till höger med tabellsiffror, `flex-wrap: wrap` så att talet lägger sig på egen rad på smala containrar i stället för att ge sidledsrullning.
- Spår: 10 px högt, `var(--linje)`, 2 px radie. Fyllning: `var(--morkgron)`, bredd = räknade / totalt i procent med en decimal, 0 ger tomt spår.
- Spåret är `aria-hidden`; talet i raden är det skärmläsaren läser.
- Toppens block har reserverad höjd så att sidhuvudet inte hoppar när talen ändras vid omladdning: två rader, mätt när det byggts (samma princip som `toppsvar` 314 px).
- All CSS börjar med `.mp-val`, inga `vh`, ingen `position: fixed` eller `sticky`, inga nya `document`-anrop (tillåtlistan i `tests/test_inbaddning.py` rörs inte).

## Kontroller

- `.venv/bin/python -m pytest -q`: 420 gröna, lintet i `test_inbaddning.py` godkänner CSS:en.
- `verktyg/tvaar-check.js`: `STATUS_2026` byts till den kortade raden; nya kontroller: mätaren i toppen finns med "23 av 23" på `--sida`, med "9 av 23" på `--partiell` (både toppen och kartsektionen, och Sverige-raden med rikets tal), saknas efter byte till 2022, saknas på `--prel` och `--slutlig` (byggda utan `--valnatt`). Kontrollen på kortets underrad (`kf6`) byts till mätaren i kartsektionen.
- `verktyg/historik-check.js`: kontrollen `partiell: statusraden innehåller "9 av 23"` flyttas till mätaren.
- `verktyg/skal-check.js`: mätaren saknas före valdagen.
- `verktyg/bredd-check.js`: ingen sidledsrullning i 320-1280 px på `--partiell`.
- `verktyg/beehiiv-check.js`: grön.

## Utanför

Självuppdatering, rikets tal per region och kommun i kartsektionen, stillbilder av mätaren.
