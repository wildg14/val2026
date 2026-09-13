# Räknemätaren Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Två stapelmätare på valnatten som visar hur många distrikt som är räknade (toppen: Majorna och Sverige; kartsektionen: det visade valet), och en statusrad som slutar upprepa talet.

**Architecture:** Allt ligger i `valgrafik.js` (MARKUP-strängen, en `renderMatare()` som anropas i det fulla svepet och vid valbyte, två kortade grenar i `statusText()`, en borttagen underrad i `renderPanel()`) och `valgrafik.css`. Talen finns redan: `raknadeIVal(val)` och rikets `antal_distrikt`/`totalt_distrikt`. Kontrollerna är webbläsarverktygen i `verktyg/`, som skrivs om först (rött), sedan koden (grönt).

**Tech Stack:** Vanilla JS och CSS i Beehiivs `iframe srcdoc` (CSS börjar med `.mp-val`, inga nya `document`-anrop), pytest-lintet `tests/test_inbaddning.py`, Puppeteer-kontrollerna `verktyg/*.js` mot `http.server` på 8765.

Spec: `docs/superpowers/specs/2026-09-13-raknemataren-design.md`. Valdag i dag: koden måste vara pushad i god tid före 20.00.

---

### Task 1: Kontrollerna skrivs om först

**Files:**
- Modify: `verktyg/tvaar-check.js:26`, `:50-56`, `:84-92`, `:158-175`, `:200-210`, `:216-236`
- Modify: `verktyg/historik-check.js:92`, `:213`
- Modify: `verktyg/skal-check.js:25-26`, `:42`

- [ ] **Step 1: tvaar-check: den kortade statusraden och mätaren i toppen**

Rad 26:
```js
// Statusraden gäller alltid riksdagsvalet men bär inte längre talet: det står i mätaren under den.
const STATUS_2026 = 'Preliminärt. Uppdaterad ';
```

I `las()` (rad 50-56), lägg till i det returnerade objektet efter `laddaOm`:
```js
               matare: [...rot.querySelectorAll('#matare .matare-rad')].map(r => r.textContent),
               matareDold: rot.querySelector('#matare').hidden,
               kartaMatare: (rot.querySelector('#karta-matare .matare-rad') || {}).textContent || '',
```

I kontrollistan (rad 84-92), efter `['Ladda om finns på valnatten', y2026.laddaOm],`:
```js
    ['mätaren i toppen räknar Majorna', y2026.matare.length === 2 && y2026.matare[0].startsWith('Majorna') && y2026.matare[0].includes('23 av 23 distrikt räknade')],
    ['mätaren i toppen räknar Sverige', y2026.matare[1].startsWith('Sverige') && /\d av \d/.test(y2026.matare[1]) && !y2026.matare[1].includes('distrikt')],
    ['mätaren ovanför kartan följer valet', y2026.kartaMatare.startsWith('Riksdagsvalet') && y2026.kartaMatare.includes('23 av 23 distrikt räknade')],
    ['ingen mätare på 2022', y2022.matareDold === true],
```

- [ ] **Step 2: tvaar-check: kf-sidorna läser mätaren ovanför kartan i stället för kortets underrad**

I `kfSidan` (rad 158), byt raden `ut.kfMajornaSub = ...` mot:
```js
      ut.kfKartaMatare = rot.querySelector('#karta-matare .matare-rad').textContent;
```
Rad 175:
```js
  if (kf6) kontroller.push(['kf6: mätaren ovanför kartan räknar alla räknade distrikt', kf6.kfKartaMatare.startsWith('Kommunvalet') && kf6.kfKartaMatare.includes('6 av 23 distrikt räknade')]);
```

- [ ] **Step 3: tvaar-check: ingen mätare utan valnattsläge, mätaren på den delvis räknade sidan**

I `utanValnatt` (rad 200-210), evaluate-objektet får `matareDold: rot.querySelector('#matare').hidden` och kontrollistan:
```js
    kontroller.push([`statusraden på ${namn}-sidan`, res.statusrad.trim() === vantad],
                    [`inget Ladda om på ${namn}-sidan`, !res.laddaOm],
                    [`ingen mätare på ${namn}-sidan`, res.matareDold === true]);
```

I partiell-avsnittet (rad 216-236), evaluate-objektet får två fält och kontrollistan två rader:
```js
               matare: rot.querySelector('#matare').textContent,
               kartaMatare: rot.querySelector('#karta-matare').textContent,
```
```js
                    ['partiell: mätaren i toppen säger 9 av 23', (bak.matare || '').includes('9 av 23 distrikt räknade')],
                    ['partiell: mätaren ovanför kartan säger 9 av 23', (bak.kartaMatare || '').includes('9 av 23 distrikt räknade')],
```

- [ ] **Step 4: historik-check och skal-check**

historik-check rad 92, efter `statusrad:`:
```js
      matare: (document.getElementById('matare') || {}).textContent || '',
```
Rad 213:
```js
      ['partiell: mätaren i toppen innehåller "9 av 23"', u.matare.includes('9 av 23')],
```
skal-check rad 26, efter `ut.statusradDold`:
```js
    ut.matareDold = rot.querySelector('#matare').hidden;
```
Rad 42: villkoret får `&& res.matareDold` efter `res.statusradDold`.

- [ ] **Step 5: Kör och se rött**

Bygg testsidorna om från det här worktree:t (kopior av den ännu oförändrade koden) och kör:
```bash
node verktyg/tvaar-check.js --sida=... --kf=... --kf6=... --partiell=... --prel=... --slutlig=...
```
Väntat: `TVÅÅRSKONTROLL MISSLYCKADES` med raderna om mätaren och statusraden. (`#matare` finns inte än, så `rot.querySelector('#matare').hidden` kastar - det räknas också som rött.)

- [ ] **Step 6: Commit**
```bash
git add verktyg/tvaar-check.js verktyg/historik-check.js verktyg/skal-check.js
git commit -m "Räknemätaren: kontrollerna först (röda tills koden finns)"
```

### Task 2: Koden

**Files:**
- Modify: `valgrafik.js:24` (MARKUP sidhuvud), `:52` (MARKUP kartsektion), `:413` (fulla svepet), `:497,:508` (statusText), `:749` (flik-onclick), `:1100-1103` (renderPanel), ny `renderMatare()` efter `renderToppsvar()`
- Modify: `valgrafik.css:28` (efter `.toppsvar`)

- [ ] **Step 1: MARKUP**

Rad 24-25:
```html
    <p class="statusrad" id="statusrad"></p>
    <div id="matare" class="matare" hidden></div>
    <div id="toppsvar" class="toppsvar"></div>
```
Rad 52-53 (efter `</div>` som stänger `.rad`, före `<div id="karta-yta">`):
```html
    <div id="karta-matare" class="matare matare-karta" hidden></div>
```

- [ ] **Step 2: renderMatare**

Efter `renderToppsvar()` (rad 535):
```js
/* ---- räknemätaren: hur stor del av distrikten som är räknade, som spår och fyllning. Talet står i
   raden och läses av skärmläsaren; spåret är bara bild. Visas i samma läge som ger statusraden
   "Ladda om" för det levande året, och försvinner när valnattsläget slås av. */
function matarRad(namn, raknade, totalt, medOrd) {
  const andel = totalt ? Math.max(0, Math.min(100, raknade / totalt * 100)) : 0;
  return [h("div", { class: "matare-rad" }, h("span", { class: "matare-namn" }, namn),
            h("span", { class: "matare-tal" }, `${tal(raknade)} av ${tal(totalt)}` + (medOrd ? " distrikt räknade" : ""))),
          h("span", { class: "matare-spar", "aria-hidden": "true" }, h("span", { class: "matare-fyll", style: `width:${andel.toFixed(1)}%` }))];
}
function matareVisas() {
  if (!KONFIG.valnatt || state.ar !== KONFIG.standardAr) return false;
  const { raknade, totalt } = raknadeIVal("rd");
  return arPreliminar() || raknade < totalt;
}
function renderMatare() {
  const topp = $("#matare"), karta = $("#karta-matare"), visas = matareVisas();
  topp.hidden = karta.hidden = !visas;
  topp.innerHTML = ""; karta.innerHTML = "";
  if (!visas) return;
  const maj = raknadeIVal("rd"), riket = jamforelse("riket", "rd");
  topp.append(...matarRad("Majorna", maj.raknade, maj.totalt, true));
  if (harRaknade(riket)) topp.append(...matarRad("Sverige", riket.antal_distrikt, riket.totalt_distrikt, false));
  const v = raknadeIVal(state.val);
  karta.append(...matarRad(VALNAMN[state.val], v.raknade, v.totalt, true));
}
```

- [ ] **Step 3: Anropen**

Rad 413: `renderKontroller(); renderMatare(); renderKarta();`
Rad 749 (flik-onclick): `renderKontroller(); renderMatare(); renderKarta();`

- [ ] **Step 4: statusText kortas**

Rad 497:
```js
    if (KONFIG.valnatt && arPreliminar()) return { text: `Preliminärt. Uppdaterad ${klockslag(meta.uppdaterad)}.`, laddaOm: true };
```
Rad 508:
```js
      if (delvis) return { text: "Slutlig räkning pågår.", laddaOm: true };
```
Kommentaren ovanför rad 497 blir: `// Rubriken under raden säger redan att det är riksdagsvalet och mätaren under bär talet, så valnattsraden säger bara läge och klockslag.`

- [ ] **Step 5: renderPanel utan underraden**

Rad 1100 (`const rak = raknadeIVal(val), vn = ...`) och rad 1102-1103 (kommentaren och `subText = ...`) tas bort; `subText` förblir `""`. Kommentaren ersätts av: `// Räkneläget står i mätaren ovanför kartan sedan 2026-09-13; underraden är tom och döljs.`

- [ ] **Step 6: CSS**

Efter `.mp-val .toppsvar { ... }` (rad 28):
```css
/* Räknemätaren på valnatten: hur många distrikt som är räknade, i toppen (Majorna och Sverige) och ovanför kartan (det visade
   valet). Samma spår och fyllning som toppsvarets staplar men tunnare; talet står i raden, spåret är bara bild. Toppens block har
   reserverad höjd (två rader) så att sidhuvudet inte hoppar när talen ändras. */
.mp-val .matare { min-height: 96px; margin: 0 0 16px; }
.mp-val .matare-rad { display: flex; flex-wrap: wrap; justify-content: space-between; gap: 0 12px; font-size: 16px; color: var(--sten); margin: 0 0 4px; }
.mp-val .matare-tal { font-variant-numeric: tabular-nums; white-space: nowrap; }
.mp-val .matare-spar { display: block; height: 10px; background: var(--linje); border-radius: 2px; margin: 0 0 10px; }
.mp-val .matare-fyll { display: block; height: 100%; background: var(--morkgron); border-radius: 2px; }
.mp-val .matare-karta { min-height: 0; margin: 0 0 12px; }
```
Mät toppens block i 390 och 1280 px när sidan renderar (två rader) och rätta `96px` till det uppmätta talet.

- [ ] **Step 7: Lintet och sviten**
```bash
.venv/bin/python -m pytest -q tests/test_inbaddning.py
.venv/bin/python -m pytest -q
```
Väntat: gröna, 420.

- [ ] **Step 8: Bygg testsidorna om och kör alla kontroller**

Testsidorna innehåller kopior av `valgrafik.js`/`.css`: bygg om `tvaar`, `tvaar-kf` (`--kf-raknade 3`), `tvaar-kf6` (`--kf-raknade 6`), `tvaar-prel`, `tvaar-slutlig`, `tvaar-partiell` (`--partiell 9`), `tvaar-riketdelvis`, `prel`, `partiell`, `slutlig` med `verktyg/forbered_tvaar.py` från det här worktree:t. Servern på 8765 måste servera den nya koden för `index.html`-kontrollerna.
```bash
node verktyg/tvaar-check.js --sida=... --kf=... --kf6=... --partiell=... --prel=... --slutlig=... --riketdelvis=...
node verktyg/historik-check.js --sida=... --prel=... --partiell=... --slutlig=...
node verktyg/bredd-check.js --sida=... --prel=... --partiell=... --slutlig=...
node verktyg/skal-check.js
node verktyg/beehiiv-check.js
```
Väntat: alla OK, inga JS-fel, inga krockar, ingen sidledsrullning.

- [ ] **Step 9: Skärmdumpar i 390 och 1280 px på partiell-sidan** (toppen och kartsektionen) och titta på dem: mätaren ligger under statusraden respektive mellan växeln och legenden, talet på egen rad bara om det inte får plats.

- [ ] **Step 10: Commit**
```bash
git add valgrafik.js valgrafik.css
git commit -m "Räknemätaren: hur mycket som är räknat, som stapel i toppen och ovanför kartan"
```

### Task 3: Dokumentationen och publiceringen

**Files:**
- Modify: `README.md:351`, `:388`, `:534`, `:538`
- Modify: `docs/valnatt-korschema.md:157`
- Modify: `docs/HANDOVER.md` (nytt statusavsnitt före "Så hänger det ihop tekniskt")

- [ ] **Step 1: README och körschemat**

README rad 351: `"Preliminärt, X av 23 distrikt räknade. Uppdaterad HH:MM."` blir `"Preliminärt. Uppdaterad HH:MM."`, och efter "med knappen "Ladda om" bredvid" läggs till: `, under den räknemätaren (Majorna N av 23 distrikt räknade, Sverige N av 6 626, som staplar; ovanför kartan samma mätare för det visade valet)`.
README rad 388 och körschemat rad 157: `"Slutlig räkning pågår, N av 23 distrikt räknade."` blir `"Slutlig räkning pågår."` följt av ` (talet står i mätaren under)`.
README rad 534: `"Preliminärt, 12 av 23 distrikt räknade. Uppdaterad 21:35."` blir `"Preliminärt. Uppdaterad 21:35."`.
README rad 538: meningen `Kvar i den raden står bara valnattens "X av 23 distrikt räknade."; utanför valnatten är den tom och dold.` blir `Raden är tom och dold sedan 2026-09-13; räkneläget står i mätaren ovanför kartan.`

- [ ] **Step 2: HANDOVER**

Nytt avsnitt `## Status 2026-09-13: räknemätaren och valnattsslingan` med: beslutet (två rader i toppen, en ovanför kartan, statusraden kortad, kortets underrad borta), var koden ligger (`renderMatare`, `matareVisas`, `matarRad`), kontrollerna som ändrades, och att `verktyg/valnatt-slinga.sh` kör kvällen (se körschemat). Fem till tio rader.

- [ ] **Step 3: Commit, push, kontroll av den skarpa sidan**
```bash
git add README.md docs/valnatt-korschema.md docs/HANDOVER.md
git commit -m "Räknemätaren och slingan i dokumentationen"
git push origin HEAD:main
git -C /Users/daniel/code/Temp pull --ff-only origin main
```
Vänta på Pages-bygget (`gh api repos/wildg14/val2026/pages/builds/latest`), sedan `node verktyg/host-check.js` mot en värdsida som laddar blocket från Pages (scratchpad `block-test.html`): 23 distrikt, inga fel, och `#matare` dolt (före valnatten). Öppna majposten.se/val2026 i webbläsaren: inga konsolfel.
