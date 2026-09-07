# Körschema valnatten 2026

Allt körs från projektmappen med `.venv/bin/python`. Servern för lokal kontroll: `python3 -m http.server 8765 --bind 127.0.0.1` i projektroten. Bakgrunden till varje steg står i README under Valnatten; det här är listan att bocka av.

Valdagen är söndag 13 september 2026. Vallokalerna stänger 20.00.

## Lördag 12 september

- [ ] `git pull origin main`. Sedan grenkontroll: `git branch --show-current` svarar `main`, och `git log origin/main --oneline -1` visar samma commit som `git log --oneline -1`. Valnattsomgången ligger på grenen `claude/valnattsplanen-superpowers-b46290`; körschemat förutsätter att den är mergad till `main` innan kvällens `git push origin main` kan nå hosten. Görs mergepushen i dag: välj en lugn timme (GitHub Pages har en mjuk gräns på tio bygg per timme, se Under kvällen) och kontrollera sidan (majposten.se/val2026) igen tio minuter senare - Pages cache kan dröja så länge, och det är det som gör `data/distrikt.js`-övergångskopian meningsfull för läsare som hann in mellan pushen och ombygget.
- [ ] Certifikatet finns: `ls val-sign-pub.pem`. Saknas det: `curl -sSo val-sign-crt.pem https://resultat.val.se/keys/val-sign-crt.pem && openssl x509 -in val-sign-crt.pem -pubkey -noout > val-sign-pub.pem`. (Skriptet hämtar det annars själv vid första körningen.)
- [ ] `.venv/bin/python -m pytest -q` grönt. Saknas pem-filerna hoppar sviten tyst över två signaturtester (`test_signatur_verifieras_med_valmyndighetens_nyckel` och `test_signatur_ger_false_vid_andrad_byte`) i stället för att fela - kör steget ovan först så att de räknas med.
- [ ] `.venv/bin/python scripts/uppdatera_2026.py --repetera` slutar med `REPETITION OK: 2022 års råfiler ger exakt samma valdata som valdata_2022.json (23 distrikt, 3 val, aggregat, mandat). Varningar: 35`.
- [ ] Torrkörning mot simuleringarna, till en tillfällig mapp:

```bash
.venv/bin/python scripts/uppdatera_2026.py --hamta --genrep --ut /tmp/torr --status preliminar
```

Facit, kört 2026-09-07 (klockslag och sökväg skiljer sig):

```
rd: Genrep_2026_preliminar_00_RD.zip 2109 kB, md5 ok, signatur ok, 3 json-filer
rf: Genrep_2026_preliminar_14_RF.zip 392 kB, md5 ok, signatur ok, 3 json-filer
kf: Genrep_2026_preliminar_1480_KF.zip 126 kB, md5 ok, signatur ok, 2 json-filer
MAPP: /tmp/torr/valnatt/20260907-030840
Läser rd: Genrep_2026_preliminar_rostfordelning_00_RD.json
VARNING: rd: 14800533 heter 'Sandarna' i filen men 'Sandarne' 2022
Läser rf: Genrep_2026_preliminar_rostfordelning_14_RF.json
Läser kf: Genrep_2026_preliminar_rostfordelning_1480_KF.json
VARNING: TESTDATA: minst en fil har test: true. Filerna skrivs med meta.test och får inte publiceras som skarpa.
Räknade distrikt: Riksdag 23/23, Region 23/23, Kommun 23/23
Jämförbara mot 2022: 14 av 23. Omritade: Kungsladugård Västra, Mariaplan, Silverkällan, Sannaplan, Sandarna, Klippan, Gröna Vallen, Slottsskogsgat. m fl, Godhem
      22.9 kB  /tmp/torr/valdata_2026.json
      14.7 kB  /tmp/torr/valdata_2026.js
      10.4 kB  /tmp/torr/swing_2026.json
       6.9 kB  /tmp/torr/swing_2026.js
2 varningar. Status: preliminar. Uppdaterad: 2026-09-07T03:08:41
Nästa steg: kör med --valnatt för att slå på valnattsläget i data/konfig.js, eller redigera filen för hand. Ladda sedan upp data/.
```

Skriptet vägrar skriva testdata (`meta.test`) till repots `data/` utan `--tvinga`: glöms `--ut` bort stoppar den spärren en torrkörning i stället för att skriva testmärkt data i skarp mapp.

- [ ] Kör samma kommando en gång till: väntat `Inget nytt: de tre filerna har samma md5 som senaste körning`, `Inget nytt att läsa in.` och returkod 3.
- [ ] Testsidan med båda åren, med servern igång (`python3 -m http.server 8765 --bind 127.0.0.1` i projektroten):

```bash
.venv/bin/python verktyg/forbered_tvaar.py --valnatt-data /tmp/torr --valnatt --ut tmp/tvaar
node verktyg/tvaar-check.js
```

Väntat: `TVÅÅRSKONTROLL OK`, inga JS-fel, och raden `valfria filer som saknas` med `tmp/tvaar/data/swing_2022.js` (den filen kommer först med historikplanen).

- [ ] Skarpa adressen svarar 404 än:

```bash
.venv/bin/python scripts/hamta_2026.py --ut /tmp/torr2
```

Väntat, ordagrant, och returkod 1:

```
FEL: https://resultat.val.se/resultatfiler/val2026/index.md5 svarar 404: resultatfilerna publiceras först på valkvällen
```

- [ ] `git status` rent, `git pull origin main` uppdaterat, hosten svarar (öppna majposten.se/val2026).
- [ ] Ta bort torrkörningens mappar när du är klar (`rm -rf /tmp/torr /tmp/torr2 tmp`). Repots `data/` ska inte ha ändrats av något steg ovan.

## Söndag 13 september

Vallokalerna stänger 20.00. De första distrikten i landet brukar komma strax efter; Majorna dröjer längre.

- [ ] 20.05 och framåt: `.venv/bin/python scripts/hamta_2026.py --ut /tmp/kontroll` tills index finns (returkod 0). Det skriver ingen data i repot.
- [ ] Första skarpa körningen:

```bash
.venv/bin/python scripts/uppdatera_2026.py --hamta --status preliminar --valnatt
```

Läs utskriften: räknade distrikt per val, `Jämförbara mot 2022: 14 av 23`, varningarna. Inget räknat Majornadistrikt är väntat den första timmen: filerna skrivs med 0 av 23 räknade och konfigen slår över i valnattsläge.

- [ ] Öppna `index.html` lokalt (eller http://localhost:8765/), kontrollera statusraden och toppsvaret, klicka ett räknat distrikt och jämför mot val.se.
- [ ] Publicera:

```bash
git add data && git commit -qm "Valnatten: första resultaten" && git push origin main
```

Vänta en minut, öppna majposten.se/val2026 med `?v=1` i adressen (för att komma runt cachen) och kontrollera statusraden, toppsvaret och kartan.

- [ ] Var tionde minut till omkring 23.30:

```bash
.venv/bin/python scripts/uppdatera_2026.py --hamta --status preliminar && git add data && git commit -qm "Valnatten: uppdaterat $(date +%H:%M)" && git push origin main
```

GitHub Pages bygger från grenen med en mjuk gräns på tio bygg per timme. Blir ett bygge strypt landar pushen ändå i git, men sidan uppdateras inte förrän nästa bygge går igenom - kontrollera då sidan innan nästa push.

Returkod 3 med `Inget nytt att läsa in.` betyder att Valmyndighetens tre filer är oförändrade: kedjan stannar, ingenting committas, allt är som det ska.

- [ ] Vid `FEL:`: läs meddelandet, åtgärda, kör igen. Ingenting är skrivet när ett FEL kommer. Vanliga fall:
  - Nätfel eller `md5 stämmer inte`: vänta någon minut och kör igen.
  - `färre räknade distrikt än i valdata_2026.json`: kör `.venv/bin/python scripts/uppdatera_2026.py --valnatt-mapp data/valnatt/senaste --tvinga --status preliminar`. Kom ihåg att `--tvinga` ersätter hela filen (val som saknas i den nya blir tomma) och samtidigt låser upp spärrarna mot testdata.
  - `har inte formen av en JSON-fil`: Valmyndigheten skrev filen medan vi läste. Kör igen.
  - Signaturfel: hämta om certifikatet. `--utan-signatur` är reservläge och bara efter att val.se bekräftat problemet: `.venv/bin/python scripts/uppdatera_2026.py --hamta --utan-signatur --status preliminar` ger utskriften "signatur ej kontrollerad".
  - Ett val som fattas helt eller är trasigt: komplettera för hand med `.venv/bin/python scripts/uppdatera_2026.py --valnatt-mapp data/valnatt/senaste --csv valnatt.csv --status preliminar` (CSV:n vinner per distrikt och val, JSON-vägen fyller resten). Mallen: `.venv/bin/python scripts/uppdatera_2026.py --skriv-mall valnatt.csv`, 12 rader per distrikt, 276 tal för riksdagsvalet.
- [ ] Halvfärdiga tidsstämpelmappar under `data/valnatt/` efter avbrutna körningar är ofarliga; `senaste` pekar bara på lyckade körningar. Mappen är gitignorerad.

## Måndag till onsdag

- [ ] Den preliminära räkningen fortsätter, med uppsamlingsräkningen på onsdagen: samma kommando som under kvällen, en gång i timmen räcker.
- [ ] Slutlig räkning när `s/` finns (från måndagen):

```bash
.venv/bin/python scripts/uppdatera_2026.py --hamta --tillfalle s --status slutlig
```

- [ ] När den slutliga räkningen ligger: sätt `"valnatt": false` i `data/konfig.json`, skriv om `konfig.js` med

```bash
.venv/bin/python -c "from scripts import schema; schema.skriv_konfig('data', schema.las_konfig('data'))"
```

och publicera. Statusraden blir då "Slutligt resultat, riksdagsvalet 2026." utan "Ladda om".

- [ ] Stillbilder till brevet:

```bash
.venv/bin/python scripts/skapa_bilder.py --ar 2026 --etikett "Majposten · Valet 2026"
```

- [ ] Kontrollera sidan en sista gång i webbläsaren: `node verktyg/skal-check.js` och `node verktyg/beehiiv-check.js` med servern igång.
