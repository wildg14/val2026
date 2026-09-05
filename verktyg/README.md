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
| `beehiiv-check.js` | Verifierar djuplänkar och rullning genom Beehiivs `iframe srcdoc` (`docs/beehiivtest.html`): kortets rubrik vid inläst länk, klick som byter distrikt och uppdaterar förälderns adress, att iframen växer när tabellen fälls ut, och att "Tillbaka till kartan" i 390 px hamnar under den klibbiga menyn | `node verktyg/beehiiv-check.js` |

Stillbilder görs inte här utan med `scripts/skapa_bilder.py` (Chrome headless direkt).
