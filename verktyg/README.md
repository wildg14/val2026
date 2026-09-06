# Verktyg: skärmdumpar och mätningar

Puppeteer-skript som kör den installerade Chrome (macOS-sökvägen står i skripten) för att verifiera sidan. Kräver `node` och `puppeteer-core` i den här mappen:

```bash
cd verktyg && npm init -y >/dev/null && npm install puppeteer-core --no-audit --no-fund
```

Alla skript förutsätter att den lokala servern kör: `python3 -m http.server 8765` i projektroten (eller Claude Codes förhandsvisning `valgrafik` i `.claude/launch.json`).

| Skript | Gör | Exempel |
|---|---|---|
| `sektion.js URL SELEKTOR UT.png BREDD` | Elementskärmdump i given viewportbredd (under 600 = mobilemulering, 2x) | `node verktyg/sektion.js http://localhost:8765/index.html "#karta-sektion" ut.png 390` |
| `shots.js UTMAPP` | Fast uppsättning helsides- och sektionsskärmdumpar (mobil och desktop) | `node verktyg/shots.js /tmp/shots` |
| `skal-check.js` | Funktionstest av skalet: alla 23 distrikt klickbara, tre stickprov mot xlsx, konfig, sektionsordning, bildläge | `node verktyg/skal-check.js` |
| `desktop-check.js URL UT.png` | Mäter desktoplayouten på 1280 px: kolumner, klick utan scroll, sticky kort | `node verktyg/desktop-check.js http://localhost:8765/docs/inbaddningstest.html ut.png` |
| `vard-check.js` | Beräknade stilar åt båda hållen i den simulerade värdsidan (inget läckage in eller ut) | `node verktyg/vard-check.js` |
| `host-check.js URL UT.png` | Laddar blocket från GitHub Pages i en lokal värdsida och verifierar rendering | `node verktyg/host-check.js file:///.../block-test.html ut.png` |
| `forbered_tvaar.py --valnatt-data MAPP` | Bygger testsidan `tmp/tvaar/` (gitignorerad) med två år: 2022 ur `data/` och 2026 ur en valnattskörning. `bakgrund.js`, `swing_2022.js` och `swing_2026.js` är valfria. `--valnatt` slår på valnattsläget, `--kf-raknade N` låter bara de N första distrikten ha kommunvalet räknat, `--status slutlig\|preliminar` skriver om `meta.status` i sidans `valdata_2026.js` | `.venv/bin/python verktyg/forbered_tvaar.py --valnatt-data /tmp/valnatt-test/data --valnatt --kf-raknade 3 --ut tmp/tvaar-kf` |
| `tvaar-check.js [URL] [KF-URL]` eller `--sida= --kf= --slutlig= --prel=` | Kontrollerar tvåårssidan: två årsknappar, 23 distrikt båda åren, Sandarna 2026 och Sandarne 2022, samma viewBox, toppsvarets fyra partier, statusraden och "Ladda om" (även efter klick på Valet 2022), inga JS- eller konsolfel, och skriver ut vilka kontroller som föll. `--kf=` är en sida byggd med `--kf-raknade 3` (markörtexten per val), `--slutlig=` och `--prel=` är sidor byggda utan `--valnatt` med `--status slutlig` respektive `preliminar` (statusradens två stillsamma grenar, båda utan "Ladda om") | `node verktyg/tvaar-check.js --kf=http://localhost:8765/tmp/tvaar-kf/index.html --slutlig=http://localhost:8765/tmp/tvaar-slutlig/index.html --prel=http://localhost:8765/tmp/tvaar-prel/index.html` |
| `beehiiv-check.js` | Verifierar djuplänkar och rullning genom Beehiivs `iframe srcdoc` (`docs/beehiivtest.html`): kortets rubrik vid inläst länk, klick som byter distrikt och uppdaterar förälderns adress, att iframen växer när tabellen fälls ut, och att "Tillbaka till kartan" i 390 px hamnar under den klibbiga menyn | `node verktyg/beehiiv-check.js` |

Stillbilder görs inte här utan med `scripts/skapa_bilder.py` (Chrome headless direkt).
