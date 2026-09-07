/* Så röstade Majorna - valgrafik.js
   Renderar hela grafiken inuti <div class="mp-val" id="valgrafik"></div>. Datafiler och konfig läses från
   mappen data/ bredvid den här filen (adressen tas ur skriptets egen src). Inga globala stilar, inga vh-mått:
   filen kan ligga i ett HTML-block i Beehiivs sajtbyggare eller i det tunna skalet index.html.
   Konfig: data/konfig.js (ar, standardAr, valnatt, adress, inbaddad, skrivUrl, stickyTopp, valdag, toppsvar, historik).
   Geometri: data/distrikt_<år>.js per år i ar - kartan ritar det visade årets polygoner. */
(function () {
"use strict";
const rot = (document.currentScript && document.currentScript.closest && document.currentScript.closest(".mp-val")) || document.getElementsByClassName("mp-val")[0];
if (!rot) { console.error("valgrafik.js: hittar ingen <div class=\"mp-val\"> att rendera i"); return; }
// Basadress för data/: i första hand data-bas på containern, annars skriptets egen adress.
const BAS = (() => {
  if (rot.dataset.bas) return rot.dataset.bas.endsWith("/") ? rot.dataset.bas : rot.dataset.bas + "/";
  const s = document.currentScript;
  return s && s.src ? new URL(".", s.src).href : "";
})();
const MARKUP = `
<header class="topp">
    <p class="etikett" id="topp-etikett">Majposten</p>
    <h1>Så röstade Majorna</h1>
    <p class="statusrad" id="statusrad"></p>
    <div id="toppsvar" class="toppsvar"></div>
    <p class="samarbete" id="samarbete" hidden></p>
    <div id="arval" class="knappar" role="group" aria-label="Välj valår" hidden></div>
  </header>

  <div id="rutor" class="rutor" hidden></div>

  <section id="riksdag" aria-labelledby="riksdag-rubrik">
    <h2 id="riksdag-rubrik">Om Majorna bestämde</h2>
    <p class="not" id="mandat-ingress"></p>
    <div class="knappar" role="radiogroup" aria-label="Välj fördelning" id="mandat-lage"></div>
    <div id="halvcirkel"></div>
    <div id="mandat-legend"></div>
    <p class="not" id="mandat-metod"></p>
    <p class="forbehall" id="mandat-forbehall" hidden></p>
    <p id="mandat-live" class="sr-only" aria-live="polite"></p>
  </section>

  <section id="karta-sektion" aria-labelledby="karta-rubrik">
    <h2 id="karta-rubrik">Så röstade ditt kvarter</h2>
    <div class="flikar" role="tablist" aria-label="Välj val" id="flikar"></div>
    <div class="rad">
      <div class="knappar" role="radiogroup" aria-label="Färgläggning" id="lage"></div>
      <label class="partival" id="partival" hidden>Parti <select id="parti" aria-label="Välj parti"></select></label>
    </div>
    <div id="karta-yta">
      <div id="karta-legend" class="karta-legend"></div>
      <div id="karta"></div>
      <div id="panel" role="region" aria-labelledby="panel-rubrik">
        <div class="panel-huvud"><h3 id="panel-rubrik">Hela Majorna</h3><button type="button" id="panel-tillbaka" hidden>Visa hela Majorna</button></div>
        <p class="panel-hint" id="panel-hint">Tryck på ett distrikt på kartan. Resultatet visas här.</p>
        <p class="panel-sub" id="panel-sub"></p>
        <div id="panel-not"></div>
        <div id="panel-staplar"></div>
        <div class="panel-knappar" id="panel-knappar"></div>
        <p id="panel-live" class="sr-only" aria-live="polite"></p>
      </div>
    </div>
    <button id="tabell-knapp" aria-expanded="false" aria-controls="tabell">Visa alla distrikt som tabell</button>
    <div id="tabell" hidden></div>
  </section>

  <section id="jamforelse" aria-labelledby="jamforelse-rubrik">
    <h2 id="jamforelse-rubrik">Majorna mot Sverige</h2>
    <p class="not" id="jamforelse-not"></p>
    <div class="knappar" role="radiogroup" aria-label="Välj val för jämförelsen" id="jamforelse-val"></div>
    <div id="divergens"></div>
    <p class="forbehall" id="jamforelse-forbehall" hidden></p>
  </section>

  <section id="rostdelning" aria-labelledby="rostdelning-rubrik">
    <h2 id="rostdelning-rubrik">Röstdelningen</h2>
    <p class="not" id="rostdelning-not">Så röstar Majorna olika i riksdags-, region- och kommunvalet.</p>
    <div id="rostdelning-legend" class="rd-legend" aria-hidden="true"></div>
    <div id="rostdelning-rader"></div>
  </section>

  <section id="historik" aria-labelledby="historik-rubrik" hidden>
    <h2 id="historik-rubrik">Majorna sedan 2006</h2>
    <p class="hist-mening" id="hist-mening"></p>
    <div class="hist-bild" id="hist-bild-a"></div>
    <p class="hist-talrad" id="hist-talrad" aria-live="polite"></p>
    <p class="not" id="hist-not-a"></p>
    <div class="hist-rad2">
      <div class="hist-kol">
        <p class="hist-mening" id="hist-mening-b"></p>
        <div class="hist-bild hist-bild-b" id="hist-bild-b"></div>
        <p class="not" id="hist-not-b"></p>
      </div>
      <div class="hist-kol">
        <div class="hist-kartor" id="hist-kartor" aria-hidden="true"></div>
        <p class="not" id="hist-not-kartor"></p>
      </div>
    </div>
  </section>

  <section id="fakta" aria-labelledby="fakta-rubrik">
    <h2 id="fakta-rubrik">Om siffrorna</h2>
    <ul id="faktalista"></ul>
  </section>

  <footer id="fot"></footer>
`;
/* ===================================================================== KONFIG
   Lägg till "2026" i ar och sätt valnatt: true på valnatten. Datafilerna
   data/valdata_<år>.js (och swing_<år>.js) skrivs av scripts/uppdatera_2026.py.
   Geometrin ligger i data/distrikt_<år>.js per år i ar och byggs av scripts/bygg_geo.py. */
const KONFIG = {   // standardvärden som speglar schemat, men med de nästlade blocken förkortade (bara visa-flaggorna); data/konfig.js skriver över
  ar: ["2022"], standardAr: "2022", valnatt: false,
  adress: "https://majposten.se/val2026",
  inbaddad: false, skrivUrl: true, stickyTopp: 105,   // px från fönstrets överkant för det klibbiga kortet på desktop; Beehiivs klibbiga meny är 89 px hög
  valdag: "2026-09-13",   // visas i statusraden före valdagen
  toppsvar: { mening: "" },   // redaktionell mening under toppsvaret, tom = ingen mening
  historik: { visa: true, mening: { rd: "", rf: "", kf: "" } },   // sektionen Majorna sedan 2006, egen plan
  samarbete: { visa: false, valvaka: { visa: false } },   // samarbetsraden och valvakan, texter och adresser i data/konfig.json
  hjalp: { visa: false }   // rutan om rösthjälp
};

const PARTIER = {
  V:  { namn: "Vänsterpartiet",        farg: "#9B1B30", text: "#fff" },
  S:  { namn: "Socialdemokraterna",    farg: "#E3312D", text: "#fff" },
  MP: { namn: "Miljöpartiet",          farg: "#5E9E3E", text: "#fff" },
  C:  { namn: "Centerpartiet",         farg: "#2E8B57", text: "#fff" },
  L:  { namn: "Liberalerna",           farg: "#6DA9DC", text: "#2A241E" },
  KD: { namn: "Kristdemokraterna",     farg: "#1D2F6F", text: "#fff" },
  M:  { namn: "Moderaterna",           farg: "#2B6DB5", text: "#fff" },
  SD: { namn: "Sverigedemokraterna",   farg: "#E2C13B", text: "#2A241E" },
  D:  { namn: "Demokraterna",          farg: "#163A5E", text: "#fff" },
  FI: { namn: "Feministiskt initiativ", farg: "#CF2A7B", text: "#fff" },
  K:  { namn: "Kommunistiska Partiet", farg: "#7A1F1F", text: "#fff" },
  "Övriga": { namn: "Övriga partier",  farg: "#A79C8E", text: "#2A241E" }
};
const SPEKTRUM = ["V", "S", "MP", "C", "L", "KD", "M", "SD"];
const VALNAMN = { rd: "Riksdagsvalet", rf: "Regionvalet", kf: "Kommunvalet" };
const FARG = { papper: "#FAF6EE", black: "#2A241E", sten: "#6E6152", linje: "#E6DECF", gron: "#3F5A3A", ockra: "#C58A34", oraknat: "#DDD5C6" };

const state = { ar: KONFIG.standardAr, val: "rd", lage: "storsta", parti: "V", vald: null,
                mandatLage: "verklig", mandatRort: false, data: {}, swing: {}, geo: {}, bakgrund: null,
                sortering: { kol: "namn", fallande: false }, tabellOppen: false, skalmax: 0.5, jamforelseVal: "rd", bild: false,
                historik: null, historikGeo: null, historikAr: null };

/* ===================================================================== hjälp */
const $ = (s, el = rot) => el.querySelector(s);
const SVGNS = "http://www.w3.org/2000/svg";
function h(tag, attrs = {}, ...barn) {
  const el = document.createElement(tag);
  for (const [k, v] of Object.entries(attrs)) {
    if (v === null || v === undefined || v === false) continue;
    if (k === "class") el.className = v;
    else if (k === "html") el.innerHTML = v;
    else if (k.startsWith("on")) el.addEventListener(k.slice(2), v);
    else el.setAttribute(k, v === true ? "" : v);
  }
  for (const b of barn.flat()) if (b !== null && b !== undefined && b !== false) el.append(b.nodeType ? b : document.createTextNode(String(b)));
  return el;
}
function s(tag, attrs = {}, ...barn) {
  const el = document.createElementNS(SVGNS, tag);
  for (const [k, v] of Object.entries(attrs)) if (v !== null && v !== undefined) el.setAttribute(k, v);
  for (const b of barn.flat()) if (b !== null && b !== undefined) el.append(b.nodeType ? b : document.createTextNode(String(b)));
  return el;
}
const procent = (x, dec = 1) => (x * 100).toLocaleString("sv-SE", { minimumFractionDigits: dec, maximumFractionDigits: dec }) + " %";
const tal = n => Math.round(n).toLocaleString("sv-SE");
const pe = x => {   // avrundas först: ett värde som blir noll skrivs "0,0" utan tecken, aldrig "-0,0"
  let v = Math.round(x * 10) / 10;
  if (v === 0) v = 0;   // gäller även negativ noll
  return (v > 0 ? "+" : "") + v.toLocaleString("sv-SE", { minimumFractionDigits: 1, maximumFractionDigits: 1 });
};
const parti = p => PARTIER[p] || { namn: (data().meta.partier || {})[p] || p, farg: "#A79C8E", text: FARG.black };
const hexTal = hex => [1, 3, 5].map(i => parseInt(hex.slice(i, i + 2), 16));   // "#RRGGBB" till [r, g, b]
function mix(hex, t) {   // partifärg mot papper, t = 1 ger partifärgen
  const c = hexTal(hex), p = [250, 246, 238];
  return "#" + c.map((v, i) => Math.round(p[i] + (v - p[i]) * t).toString(16).padStart(2, "0")).join("");
}
function klockslag(iso) { const d = new Date(iso); return isNaN(d) ? iso : d.toLocaleTimeString("sv-SE", { hour: "2-digit", minute: "2-digit" }); }
function pilNavigering(container) {   // vänster/höger pil byter aktiv knapp i en flik- eller radioknapprad (roving tabindex)
  if (container.dataset.pilnav) return;
  container.dataset.pilnav = "1";
  container.addEventListener("keydown", e => {
    if (e.key !== "ArrowLeft" && e.key !== "ArrowRight") return;
    const knappar = [...container.querySelectorAll("button")];
    if (knappar.length < 2) return;
    e.preventDefault();
    const i = Math.max(0, knappar.findIndex(b => b.getAttribute("aria-checked") === "true" || b.getAttribute("aria-selected") === "true"));
    const ni = (i + (e.key === "ArrowRight" ? 1 : -1) + knappar.length) % knappar.length;
    knappar[ni].click();
    const aktiv = container.querySelector('[aria-checked="true"], [aria-selected="true"]');
    if (aktiv) aktiv.focus();
  });
}
function namnMedMjukaBindestreck(namn) {   // mjukt bindestreck (U+00AD) i långa partinamn, bara för den synliga texten
  const SHY = "\u00AD";
  return namn.replace(/Vänster/g, "Vänster" + SHY).replace(/Social/g, "Social" + SHY).replace(/Miljö/g, "Miljö" + SHY)
    .replace(/Center/g, "Center" + SHY).replace(/Krist/g, "Krist" + SHY).replace(/Sverige/g, "Sverige" + SHY);
}

/* ===================================================================== data */
const data = () => state.data[state.ar];
const distriktMap = () => Object.fromEntries(data().distrikt.map(d => [d.kod, d]));
const geo = () => state.geo[state.ar];            // det visade årets polygoner
const antalDistrikt = () => (data().distrikt || []).length;
const raknat = (d, val) => !!(d.raknat && d[val] && Object.keys(d[val]).length && d.giltiga[val]);
const raknadeIVal = (val, d = data()) => {   // distrikt räknade i just det här valet; meta.valnatt räknar "något val"
  const alla = d.distrikt || [];   // dataargumentet låter historiken räkna på ett annat år än det kartan visar
  return { raknade: alla.filter(x => raknat(x, val)).length, totalt: alla.length };
};
function andelar(roster, giltiga) {
  return Object.entries(roster).map(([p, n]) => ({ p, n, andel: giltiga ? n / giltiga : 0 }))
    .sort((a, b) => b.n - a.n || a.p.localeCompare(b.p, "sv"));
}
function storsta(roster) {
  let best = null;
  for (const [p, n] of Object.entries(roster)) if (p !== "Övriga" && (best === null || n > roster[best])) best = p;
  return best;
}
const majorna = val => data().aggregat.majorna[val];
const jamforelse = (omrade, val) => (data().aggregat[omrade] || {})[val] || null;
// Riket, regionen och kommunen räknas färdigt under valnatten. Talen finns bara i 2026 års aggregat: saknas de är området färdigräknat.
const harRaknade = post => !!post && post.antal_distrikt != null && post.totalt_distrikt != null;
const omradeDelvis = post => harRaknade(post) && post.antal_distrikt < post.totalt_distrikt;
const arPreliminar = (d = data()) => d.meta.status !== "slutlig";
const raknadeText = post => `${tal(post.antal_distrikt)} av ${tal(post.totalt_distrikt)} distrikt räknade`;
const majornaRaknat = val => majorna(val) && majorna(val).giltiga > 0;
function partierIVal(val) {
  const nycklar = Object.keys(majorna(val).roster || {}).filter(p => p !== "Övriga");
  return nycklar.length ? nycklar : SPEKTRUM;
}
function swingFor(kod, val) {
  const sw = state.swing[state.ar];
  if (!sw) return null;
  const post = kod ? (sw.distrikt || {})[kod] : sw.majorna;
  return post && post[val] ? post[val] : null;
}
function raknaSkalmax() {
  let m = 0;
  for (const v of Object.values(state.data)) {
    for (const val of Object.keys(VALNAMN)) {
      const agg = v.aggregat.majorna[val];
      if (agg && agg.giltiga) for (const [p, n] of Object.entries(agg.roster)) if (p !== "Övriga") m = Math.max(m, n / agg.giltiga);
      for (const d of v.distrikt) if (raknat(d, val)) for (const [p, n] of Object.entries(d[val])) if (p !== "Övriga") m = Math.max(m, n / d.giltiga[val]);
    }
  }
  state.skalmax = Math.max(0.2, Math.ceil(m * 20) / 20);
}
function ariaDistrikt(d, val) {
  if (!raknat(d, val)) return `${d.namn}. ${VALNAMN[val]} ${state.ar}: inte räknat än.`;
  const topp = andelar(d[val], d.giltiga[val]).filter(a => a.p !== "Övriga").slice(0, 3).map(a => `${a.p} ${procent(a.andel)}`).join(", ");
  const vd = d.rostberattigade[val] ? procent(d.rostande[val] / d.rostberattigade[val]) : "okänt";
  return `${d.namn}. ${VALNAMN[val]} ${state.ar}: ${topp}. Valdeltagande ${vd}.`;
}

/* ===================================================================== url
   ?distrikt=14800530&val=kf&lage=styrka&parti=SD&ar=2026 - delbara länkar, t.ex. per kvarter från Beehiiv.
   I Beehiivs sajtbyggare ligger blocket i en <iframe srcdoc> med samma ursprung som sidan: den egna adressen
   är "about:srcdoc" utan query, så länkar läses och skrivs mot förälderns adress när den går att nå. */
function sidLocation() {
  try { if (window.parent !== window && window.parent.location.href !== undefined) return window.parent.location; } catch (e) { /* korsdomän: egen adress gäller */ }
  return location;
}
function sidHistory() { return sidLocation() === location ? history : window.parent.history; }
function lasUrl() {
  const q = new URLSearchParams(sidLocation().search);
  if (KONFIG.ar.includes(q.get("ar"))) state.ar = q.get("ar");
  if (VALNAMN[q.get("val")]) state.val = q.get("val");
  if (["storsta", "styrka"].includes(q.get("lage"))) state.lage = q.get("lage");
  if (q.get("parti")) state.parti = q.get("parti");
  if (q.get("distrikt")) state.vald = q.get("distrikt");
}
function skrivUrl() {
  if (KONFIG.skrivUrl === false) return;
  const loc = sidLocation(), hist = sidHistory();
  const q = new URLSearchParams(loc.search);   // egna nycklar sätts eller tas bort, övriga (t.ex. Beehiivs utm_source) bevaras
  if (rot.classList.contains("inbaddad")) q.set("inbaddad", "1"); else q.delete("inbaddad");
  if (KONFIG.ar.length > 1 && state.ar !== KONFIG.standardAr) q.set("ar", state.ar); else q.delete("ar");
  if (state.val !== "rd") q.set("val", state.val); else q.delete("val");
  if (state.lage !== "storsta") { q.set("lage", state.lage); q.set("parti", state.parti); } else { q.delete("lage"); q.delete("parti"); }
  if (state.vald) q.set("distrikt", state.vald); else q.delete("distrikt");
  const qs = q.toString();
  try { hist.replaceState(hist.state, "", loc.pathname + (qs ? "?" + qs : "") + loc.hash); } catch (e) { /* file:// i vissa webbläsare, eller korsdomän */ }
}

/* ===================================================================== laddning */
function laddaSkript(namn) {
  return new Promise((ok, fel) => {
    const el = document.createElement("script");
    // konfigen alltid färsk; valdata och swing skrivs om under valnatten och får en minutnyckel.
    // Geometri och bakgrund ändras inte den natten och laddas utan parameter, så att cachen håller.
    const farsk = namn === "konfig" ? "?v=" + Date.now()
      : KONFIG.valnatt && /^(valdata|swing)_/.test(namn) ? "?v=" + Math.floor(Date.now() / 60000) : "";
    el.src = BAS + "data/" + namn + ".js" + farsk;
    el.onload = () => (window.MAJPOSTEN && window.MAJPOSTEN.data[namn]) ? ok(window.MAJPOSTEN.data[namn]) : fel(new Error(namn + " saknar data"));
    el.onerror = () => fel(new Error("kunde inte ladda data/" + namn + ".js"));
    document.head.appendChild(el);
  });
}
function monteraMarkup() {
  let m = rot.querySelector(".mp-main");
  if (!m) { m = document.createElement("div"); m.className = "mp-main"; rot.appendChild(m); }
  m.innerHTML = MARKUP;
}
async function start() {
  monteraMarkup();
  try { Object.assign(KONFIG, await laddaSkript("konfig")); } catch (e) { /* standardkonfig gäller */ }
  // Reserverad plats redan innan datan kommer, så att sidhuvudet inte hoppar: en rad extra i toppsvaret när
  // konfigen har en redaktionell mening, och årsknapparnas rad när konfigen räknar upp mer än ett år.
  rot.classList.toggle("har-mening", !!(KONFIG.toppsvar || {}).mening);
  $("#arval").hidden = (KONFIG.ar || []).length < 2;   // renderHuvud sätter om den efter vilka år som gick att ladda
  try {
    // Ett svep efter konfigen: geometri, valdata, bakgrund och swing startar samtidigt. Varje fil fångas
    // för sig, så att ett år utan filer hoppas över i stället för att släcka hela sidan.
    const onskade = KONFIG.ar.slice();
    const vill = !((KONFIG.historik || {}).visa === false);   // historiksektionen kan stängas av i konfigen
    const [geon, valdata, bakgrund, swingar, historik, historikGeo] = await Promise.all([
      Promise.all(onskade.map(a => laddaSkript("distrikt_" + a).catch(() => null))),
      Promise.all(onskade.map(a => laddaSkript("valdata_" + a).catch(() => null))),
      laddaSkript("bakgrund").catch(() => null),
      Promise.all(onskade.map(a => laddaSkript("swing_" + a).catch(() => null))),   // basåret står i filen, saknad fil ger ingen swing
      vill ? laddaSkript("historik").catch(() => null) : null,                      // Majorna sedan 2006: saknad fil döljer sektionen
      vill ? laddaSkript("distrikt_2006").catch(() => null) : null                  // konturkartan 2006, ritas i Task 8
    ]);
    state.historik = historik;
    state.historikGeo = historik ? historikGeo : null;
    const utan = [];
    onskade.forEach((a, i) => {
      if (geon[i] && valdata[i]) { state.geo[a] = geon[i]; state.data[a] = valdata[i]; state.swing[a] = swingar[i]; }
      else utan.push(a);
    });
    if (utan.length) console.warn("valgrafik: hoppar över år utan data: " + utan.join(", "));
    KONFIG.ar = onskade.filter(a => state.data[a]);   // årväljaren visar bara år som gick att ladda
    if (!KONFIG.ar.length) throw new Error("inget år kunde laddas");
    state.bakgrund = bakgrund;
    state.ar = KONFIG.ar.includes(KONFIG.standardAr) ? KONFIG.standardAr : KONFIG.ar[0];   // state skapades innan konfigen laddades
  } catch (e) {
    $("header.topp").append(h("p", { class: "fel" }, "Datafilerna kunde inte laddas: " + e.message + ". Kör scripts/bygg_data.py och kontrollera att data/ ligger bredvid valgrafik.js."));
    return;
  }
  raknaSkalmax();
  lasUrl();
  const q0 = new URLSearchParams(sidLocation().search);   // i Beehiivs iframe är den egna adressen about:srcdoc, parametrarna står på värdsidan
  if (q0.get("bild")) { renderBild(q0.get("bild")); return; }
  if (q0.get("inbaddad") || KONFIG.inbaddad) rot.classList.add("inbaddad");
  rot.style.setProperty("--mp-sticky-top", (Number(KONFIG.stickyTopp) || 16) + "px");
  const forsta = partierIVal(state.val);
  if (!forsta.includes(state.parti)) state.parti = forsta[0];
  if (state.vald && !distriktMap()[state.vald]) state.vald = null;
  renderAllt();
  autoOvergang();
  if (state.vald) $("#karta").scrollIntoView({ block: "start" });
  const sidHash = sidLocation().hash;
  const ankare = sidHash && sidHash.length > 1 ? rot.querySelector("#" + CSS.escape(sidHash.slice(1))) : null;
  if (ankare && !state.vald) ankare.scrollIntoView({ block: "start" });   // webbläsarens egen ankarrullning sker innan datan finns
}

/* ===================================================================== render */
function renderAllt() {
  renderHuvud(); renderSamarbete(); renderRiksdag(); renderKontroller(); renderKarta(); renderPanel(); renderTabell(); renderRostdelning(); renderJamforelse(); renderFakta(); renderHistorik();
}
function renderHuvud() {
  $("#topp-etikett").textContent = "Majposten · Valspecial";
  const arval = $("#arval");
  arval.innerHTML = "";
  arval.hidden = KONFIG.ar.length < 2;
  for (const a of KONFIG.ar) {
    arval.append(h("button", { type: "button", "aria-pressed": String(a === state.ar), class: a === state.ar ? "aktiv" : "",
      onclick: () => { state.ar = a; if (!partierIVal(state.val).includes(state.parti)) state.parti = partierIVal(state.val)[0]; renderAllt(); } }, "Valet " + a));
  }
  renderToppsvar();
}

/* ---- toppsvaret: svaret högst upp, alltid riksdagsvalet, inget att trycka på utom "Ladda om" på valnatten */
function datumText(iso) {   // "2026-09-13" -> "söndag 13 september"
  const d = new Date(iso + "T12:00:00");
  return isNaN(d) ? iso : d.toLocaleDateString("sv-SE", { weekday: "long", day: "numeric", month: "long" });
}
function laddaOm() { try { window.parent.location.reload(); } catch (e) { location.reload(); } }
function statusText() {
  const meta = data().meta, { raknade, totalt } = raknadeIVal("rd"), delvis = raknade < totalt;
  const valdagAr = Number(String(KONFIG.valdag || "").slice(0, 4));
  const rad = () => {
    // På valnatten men i ett annat år än det levande: bara resultatraden, och "Ladda om" som väg tillbaka.
    if (KONFIG.valnatt && state.ar !== KONFIG.standardAr) return { text: `${arPreliminar() ? "Preliminärt" : "Slutligt"} resultat ${meta.ar}.`, laddaOm: true };
    // Rubriken under raden säger redan att det är riksdagsvalet, så valnattsraden nämner inte valet.
    if (KONFIG.valnatt && arPreliminar()) return { text: `Preliminärt, ${raknade} av ${totalt} distrikt räknade. Uppdaterad ${klockslag(meta.uppdaterad)}.`, laddaOm: true };
    if (!arPreliminar() && valdagAr > Number(meta.ar)) return { text: `Slutligt resultat ${meta.ar}. Valet ${valdagAr} är ${datumText(KONFIG.valdag)}.`, laddaOm: false };
    if (!arPreliminar()) return { text: `Slutligt resultat, riksdagsvalet ${meta.ar}.`, laddaOm: false };
    return { text: `Preliminärt resultat ${meta.ar}` + (delvis ? `, ${raknade} av ${totalt} distrikt räknade.` : "."), laddaOm: false };
  };
  return Object.assign(rad(), { delvis });
}
function renderToppsvar() {
  const val = "rd", meta = data().meta, m = majorna(val), el = $("#toppsvar"), status = $("#statusrad");
  const st = statusText();
  status.replaceChildren(st.text);
  if (st.laddaOm) status.append(" ", h("button", { type: "button", class: "ladda-om", onclick: laddaOm }, "Ladda om"));
  el.innerHTML = "";
  if (!majornaRaknat(val)) { el.append(h("p", { class: "toppsvar-tom" }, `Riksdagsvalet ${meta.ar}: inget distrikt räknat än.`)); return; }
  const rader = andelar(m.roster, m.giltiga).filter(a => a.p !== "Övriga").slice(0, 4);
  const lista = h("div", { class: "toppsvar-rader", role: "list", "aria-label": `${VALNAMN[val]} ${meta.ar}, de fyra största partierna i Majorna` });
  // Raden har hela svaret i aria-label; innehållet döljs för skärmläsare så att talet inte läses två gånger.
  for (const a of rader) lista.append(h("div", { class: "toppsvar-rad", role: "listitem", "aria-label": `${parti(a.p).namn} ${procent(a.andel)}` },
    h("b", { class: "toppsvar-parti", "aria-hidden": "true" }, a.p),
    h("span", { class: "toppsvar-spar", "aria-hidden": "true" }, h("span", { class: "toppsvar-stapel", style: `width:${Math.min(100, a.andel / 0.4 * 100).toFixed(1)}%;background:${parti(a.p).farg}` })),
    h("span", { class: "toppsvar-tal", "aria-hidden": "true" }, procent(a.andel))));
  el.append(h("p", { class: "toppsvar-rubrik" }, st.delvis ? `Räknat hittills, riksdagsvalet ${meta.ar}` : `Riksdagsvalet ${meta.ar} i Majorna`), lista);
  const post = jamforelseOmrade(val).post;
  if (m.rostberattigade && !st.delvis) {   // riket tas med först när även riket är färdigräknat: de första distrikten är små och lantliga
    el.append(h("p", { class: "toppsvar-mening" }, `${procent(m.rostande / m.rostberattigade)} röstade`
      + (post && post.valdeltagande && !omradeDelvis(post) ? `, mot ${procent(post.valdeltagande)} i riket` : "") + "."));
  }
  if (KONFIG.toppsvar && KONFIG.toppsvar.mening) el.append(h("p", { class: "toppsvar-mening" }, KONFIG.toppsvar.mening));
}

/* ---- samarbete och rösthjälp: konfigstyrda block, avstängda tills redaktionen fyllt i texter och adresser */
function adressFor(url) {   // absolut adress eller adress relativt data-bas
  return /^(https?:)?\/\//.test(url) || url.startsWith("/") ? url : BAS + url;
}
function lankad(text, url, klass) {   // tom länk ger ren text, aldrig ett tomt href
  return url ? h("a", { href: url, class: klass || null }, text) : h("span", { class: klass || null }, text);
}
function ruta(post, standardLanktext) {
  const el = h("div", { class: "ruta" }, h("h2", {}, post.rubrik || ""));
  if (post.text) el.append(h("p", {}, post.text));
  if (post.lank) el.append(h("p", { class: "ruta-lank" }, h("a", { href: post.lank }, post.lanktext || standardLanktext)));
  return el;
}
function renderSamarbete() {
  const sam = KONFIG.samarbete || {}, valvaka = sam.valvaka || {}, hjalp = KONFIG.hjalp || {};
  const rad = $("#samarbete"), rutor = $("#rutor");
  rad.innerHTML = ""; rutor.innerHTML = "";
  const visaRad = !!sam.visa && !!sam.namn && !state.bild && !rot.classList.contains("inbaddad");   // raden hör ihop med rubriken, som är dold i bildläget och inbäddat
  rad.hidden = !visaRad;
  if (visaRad) {
    if (sam.logga) {
      const logga = h("img", { class: "samarbete-logga", src: adressFor(sam.logga), alt: sam.namn });
      rad.append(sam.lank ? h("a", { href: sam.lank }, logga) : logga);
    }
    rad.append(h("span", { class: "samarbete-text" }, (sam.text || "I samarbete med") + " ", lankad(sam.namn, sam.lank)));
  }
  const lista = [];
  if (sam.visa && valvaka.visa) lista.push(ruta(valvaka, "Läs mer"));
  if (hjalp.visa) lista.push(ruta(hjalp, "Läs mer"));
  rutor.hidden = !lista.length || state.bild;
  if (!rutor.hidden) rutor.append(...lista);
}

/* ---- Om Majorna bestämde */
// Ingressen står bara här: MARKUP lämnar <p id="mandat-ingress"> tom och renderRiksdag fyller den.
const MANDAT_INGRESS = jmf => `Riksdagens 349 mandat fördelade på Majornas riksdagsröster, jämfört med ${jmf}.`;
function halvcirkelPlatser(n, rader = 8, r0 = 0.5, r1 = 1.0) {
  const radier = Array.from({ length: rader }, (_, i) => r0 + (r1 - r0) * i / (rader - 1));
  const summa = radier.reduce((a, b) => a + b, 0);
  const per = radier.map(r => Math.round(n * r / summa));
  per[per.length - 1] += n - per.reduce((a, b) => a + b, 0);
  const platser = [];
  per.forEach((k, i) => { for (let j = 0; j < k; j++) {
    const v = Math.PI - Math.PI * (j + 0.5) / k;
    platser.push({ x: Math.cos(v) * radier[i], y: -Math.sin(v) * radier[i], v });
  } });
  platser.sort((a, b) => b.v - a.v);
  return platser;
}
function mandatOrdning(fordelning) {
  const extra = Object.keys(fordelning).filter(p => !SPEKTRUM.includes(p)).sort();
  const ordning = [];
  for (const p of [...SPEKTRUM, ...extra]) for (let i = 0; i < (fordelning[p] || 0); i++) ordning.push(p);
  return ordning;
}
function renderRiksdag() {
  const sek = $("#riksdag"), m = data().mandat || {}, meta = data().meta;
  const verklig = m.riksdag_verklig && Object.keys(m.riksdag_verklig).length ? m.riksdag_verklig : null;
  const egen = m.riksdag_majorna && Object.keys(m.riksdag_majorna).length ? m.riksdag_majorna : null;
  if (!egen && !verklig) { sek.hidden = true; return; }
  sek.hidden = false;
  const lagen = [];
  if (verklig) lagen.push(["verklig", `Riksdagen ${meta.ar}`]);
  if (egen) lagen.push(["majorna", "Om Majorna bestämde"]);
  if (!lagen.some(l => l[0] === state.mandatLage)) state.mandatLage = lagen[0][0];
  const knappar = $("#mandat-lage");
  knappar.innerHTML = "";
  knappar.hidden = lagen.length < 2;
  for (const [lage, text] of lagen) knappar.append(h("button", { type: "button", role: "radio", "aria-checked": String(lage === state.mandatLage), tabindex: lage === state.mandatLage ? "0" : "-1",
    onclick: () => { state.mandatRort = true; sattMandatLage(lage); } }, text));
  pilNavigering(knappar);
  const fordelning = state.mandatLage === "majorna" ? egen : verklig;
  const antal = Object.values(fordelning).reduce((a, b) => a + b, 0);
  const platser = halvcirkelPlatser(antal), ordning = mandatOrdning(fordelning);
  const svg = s("svg", { viewBox: "-1.08 -1.08 2.16 1.26", role: "img", "aria-label": `${antal} mandat. ` + Object.entries(fordelning).map(([p, n]) => `${p} ${n}`).join(", ") + "." });
  platser.forEach((pl, i) => svg.append(s("circle", { cx: pl.x.toFixed(4), cy: pl.y.toFixed(4), r: 0.026, fill: parti(ordning[i]).farg, style: `--i:${i}`, "data-i": i })));
  svg.append(s("text", { x: 0, y: 0.06, "text-anchor": "middle", "font-size": 0.1, "font-family": "Georgia, serif", "font-weight": 700, fill: FARG.black }, `${antal} mandat`));
  $("#halvcirkel").replaceChildren(svg);
  renderMandatLegend(verklig, egen);
  $("#mandat-metod").textContent = m.metod || "";
  // Riksdagens mandat kommer in preliminärt på valnatten och ändras under kvällen: då heter det bara "riksdagen".
  const preliminar = arPreliminar() && !!verklig, rike = jamforelse("riket", "rd");
  $("#mandat-ingress").textContent = MANDAT_INGRESS(preliminar ? "riksdagen" : "den verkliga riksdagen");
  $("#mandat-ingress").hidden = !(verklig && egen);
  const forbehall = $("#mandat-forbehall");
  forbehall.hidden = !preliminar;
  // Talet skrivs bara ut medan riket är delvis räknat: ett färdigräknat riket sent på kvällen ska inte säga "6 626 av 6 626".
  forbehall.textContent = !preliminar ? ""
    : omradeDelvis(rike) ? `Preliminär fördelning, riket: ${raknadeText(rike)}.` : "Preliminär mandatfördelning.";
}
function sattMandatLage(lage) {
  if (state.mandatLage === lage) return;
  state.mandatLage = lage;
  const m = data().mandat, fordelning = lage === "majorna" ? m.riksdag_majorna : m.riksdag_verklig;
  const ordning = mandatOrdning(fordelning), antal = ordning.length;
  $("#halvcirkel").querySelectorAll("circle").forEach((c, i) => c.setAttribute("fill", parti(ordning[i]).farg));
  const etikettLage = lage === "majorna" ? "Om Majorna bestämde" : `Riksdagen ${data().meta.ar}`;
  const fordelningText = Object.entries(fordelning).map(([p, n]) => `${p} ${n}`).join(", ") + ".";
  $("#halvcirkel svg").setAttribute("aria-label", `${antal} mandat, ${etikettLage.toLowerCase()}. ${fordelningText}`);
  $("#mandat-live").textContent = `${etikettLage}: ${fordelningText}`;
  $("#mandat-lage").querySelectorAll("button").forEach(b => {
    const aktiv = b.textContent.startsWith("Om") === (lage === "majorna");
    b.setAttribute("aria-checked", String(aktiv)); b.tabIndex = aktiv ? 0 : -1;
  });
  renderMandatLegend(m.riksdag_verklig, m.riksdag_majorna);
}
function renderMandatLegend(verklig, egen) {
  const partier = [...SPEKTRUM, ...Object.keys({ ...(verklig || {}), ...(egen || {}) }).filter(p => !SPEKTRUM.includes(p)).sort()]
    .filter(p => (verklig && verklig[p]) || (egen && egen[p]));
  const tabell = h("table", { class: "mandat" },
    h("thead", {}, h("tr", {}, h("th", {}, "Parti"), verklig && h("th", { class: "tal" }, `Riksdagen ${data().meta.ar}`), egen && h("th", { class: "tal" }, "Majornas riksdag"))),
    h("tbody", {}, partier.map(p => h("tr", {},
      h("td", {}, h("span", { class: "swatch", style: `background:${parti(p).farg};display:inline-block;vertical-align:-2px;margin-right:6px` }), h("b", {}, p), " ", h("span", { style: "color:var(--sten)" }, parti(p).namn)),
      verklig && h("td", { class: "tal " + (state.mandatLage === "verklig" ? "aktiv" : "dampad") }, verklig[p] || 0),
      egen && h("td", { class: "tal " + (state.mandatLage === "majorna" ? "aktiv" : "dampad") }, egen[p] ? String(egen[p]) : "under spärren")))));
  $("#mandat-legend").replaceChildren(tabell);
}
function autoOvergang() {
  const sek = $("#riksdag");
  if (sek.hidden || !("IntersectionObserver" in window) || lugn()) return;
  const io = new IntersectionObserver(poster => {
    if (!poster.some(p => p.isIntersecting)) return;
    io.disconnect();
    setTimeout(() => { if (!state.mandatRort && data().mandat && data().mandat.riksdag_majorna) sattMandatLage("majorna"); }, 1100);
  }, { threshold: 0.5 });
  io.observe(sek);
}

/* ---- kontroller ovanför kartan */
function renderKontroller() {
  const flikar = $("#flikar");
  flikar.innerHTML = "";
  for (const [val, namn] of Object.entries(data().meta.val || { rd: "Riksdag", rf: "Region", kf: "Kommun" })) {
    flikar.append(h("button", { type: "button", role: "tab", "aria-selected": String(val === state.val), tabindex: val === state.val ? "0" : "-1", id: "flik-" + val,
      onclick: () => { state.val = val; if (!partierIVal(val).includes(state.parti)) state.parti = partierIVal(val)[0]; renderKontroller(); renderKarta(); renderPanel(); renderTabell(); renderHistorik(); } }, namn));
  }
  pilNavigering(flikar);
  const lage = $("#lage");
  lage.innerHTML = "";
  for (const [l, text] of [["storsta", "Största parti"], ["styrka", "Partistyrka"]]) {
    lage.append(h("button", { type: "button", role: "radio", "aria-checked": String(l === state.lage), tabindex: l === state.lage ? "0" : "-1",
      onclick: () => { state.lage = l; renderKontroller(); renderKarta(); renderTabell(); } }, text));
  }
  pilNavigering(lage);
  const valj = $("#parti");
  valj.innerHTML = "";
  for (const p of partierIVal(state.val)) valj.append(h("option", { value: p, selected: p === state.parti }, `${p} - ${parti(p).namn}`));
  valj.onchange = () => { state.parti = valj.value; renderKarta(); renderTabell(); };
  valj.disabled = !data().distrikt.some(d => raknat(d, state.val));   // inget distrikt räknat: partival ger ingen mening än
  $("#partival").hidden = state.lage !== "styrka";
}

/* ---- kartan */
const HALLPLATSER = {
  mobil: ["Stigbergstorget", "Chapmans Torg", "Jægerdorffsplatsen", "Vagnhallen Majorna", "Mariaplan", "Sannaplan", "Högsbogatan", "Kungssten"],
  desktop: ["Stigbergstorget", "Chapmans Torg", "Jægerdorffsplatsen", "Vagnhallen Majorna", "Mariaplan", "Sannaplan", "Högsbogatan", "Kungssten", "Fjällgatan", "Ekedal", "Marklandsgatan", "Axel Dahlströms torg"]
};
const PLATSNAMN = { mobil: ["Eriksberg", "Slottsberget", "Stigberget", "Högsbohöjd"], desktop: ["Eriksberg", "Slottsberget", "Stigberget", "Högsbohöjd", "Färjenäs"] };
// typstorlekar i viewBox-enheter (1000 bred). Mobil: 1 enhet = 0,39 px. Desktop: 0,69 px.
// bildläget (state.bild) behåller dessa fasta enhetsvärden - stillbilderna ska inte ändras.
const STORLEK = { mobil: { etikett: 28, vald: 31, namn: 26, namnRad2: 22, kontur: 6, hallplats: 22, plats: 22 },
                  desktop: { etikett: 24, vald: 27, namn: 24, namnRad2: 20, kontur: 5, hallplats: 18, plats: 21 } };
// måltyper i px, oberoende av containerns bredd - räknas om till viewBox-enheter efter kartans faktiska pixelbredd
const PXMAL = { mobil: { etikett: 11, vald: 12, namn: 11, namnRad2: 9.5, kontur: 2.4, hallplats: 9, plats: 9 },
                desktop: { etikett: 15, vald: 17, namn: 15, namnRad2: 12.5, kontur: 2, hallplats: 12, plats: 12.5 } };
const arDesktop = () => rot.getBoundingClientRect().width >= 600;
const arBred = () => rot.getBoundingClientRect().width >= 900;   // kortet ligger bredvid kartan   // containerns bredd, inte fönstrets: rätt även inbäddad i en annan sida
function kartBredd() {   // kartans egen pixelbredd, reserv: containerns bredd
  const el = rot.querySelector("#karta");
  return (el && el.clientWidth) || rot.getBoundingClientRect().width || 390;
}
function histBildSlak() {   // historikbildens viewBox mot ytans bredd: glider de isär har CSS sträckt ut bilden
  const el = rot.querySelector("#hist-bild-a"), svg = el && el.querySelector("svg");
  if (!svg || el.clientWidth < 200) return false;   // under golvet i histLinjer skulle kontrollen aldrig bli nöjd
  const vb = (svg.getAttribute("viewBox") || "").trim().split(/\s+/)[2];
  return !vb || Math.abs(Number(vb) - el.clientWidth) > 4;
}
let senastDesktop = null, senastKartaBredd = null;
if ("ResizeObserver" in window) new ResizeObserver(() => {
  const nu = arDesktop(), breddNu = kartBredd();
  const desktopBytte = senastDesktop !== null && nu !== senastDesktop;
  const breddBytte = senastKartaBredd !== null && Math.abs(breddNu - senastKartaBredd) / senastKartaBredd > 0.1;
  if ((desktopBytte || breddBytte) && geo() && !state.bild) renderKarta();
  if (state.historik && !state.bild && (desktopBytte || breddBytte || histBildSlak())) renderHistorik();
  senastDesktop = nu;
  // Referensbredden flyttas bara när något faktiskt ritades om. Annars nollställs jämförelsen vid varje utslag
  // och en rad steg under tio procent hinner sträcka ut bilderna utan att någon omritning sker.
  if (desktopBytte || breddBytte || senastKartaBredd === null) senastKartaBredd = breddNu;
}).observe(rot);
function storlek() {   // typstorlekar i viewBox-enheter efter kartans faktiska pixelbredd, inte en fast 600 px-tröskel
  const bredd = kartBredd(), mal = bredd < 600 ? PXMAL.mobil : PXMAL.desktop, faktor = 1000 / bredd;
  const ut = {};
  for (const k in mal) ut[k] = mal[k] * faktor;
  return ut;
}

function projektion(bbox, padX = 0.045, padY = 0.16) {   // högre ram: mer älv och Slottsskog, cirka 60 vh på en telefon
  const [w0, s0, e0, n0] = bbox, dx = (e0 - w0) * padX, dy = (n0 - s0) * padY;
  const W = w0 - dx, E = e0 + dx, S = s0 - dy, N = n0 + dy;
  const kx = Math.cos((S + N) / 2 * Math.PI / 180), bredd = 1000, skala = bredd / ((E - W) * kx);
  return { bredd, hojd: (N - S) * skala, till: ([lon, lat]) => [(lon - W) * kx * skala, (N - lat) * skala], W, E, S, N };
}
function gemensamBbox() {   // en ram för alla laddade år, så att kartan inte hoppar vid årsbyte
  const bb = Object.values(state.geo).map(g => g && g.bbox).filter(Boolean);
  if (!bb.length) return geo().bbox;   // inget år har en bbox: det visade årets egen ram får duga
  return [Math.min(...bb.map(b => b[0])), Math.min(...bb.map(b => b[1])), Math.max(...bb.map(b => b[2])), Math.max(...bb.map(b => b[3]))];
}
const dAttr = (ring, proj, stang) => ring.map((c, i) => (i ? "L" : "M") + proj.till(c).map(v => v.toFixed(1)).join(",")).join("") + (stang ? "Z" : "");
const dRing = (ringSvg, stang) => ringSvg.map((c, i) => (i ? "L" : "M") + c.map(v => v.toFixed(1)).join(",")).join("") + (stang ? "Z" : "");
function textBredd(text, storlek, fet) { return text.length * storlek * (fet ? 0.62 : 0.56); }
function overlappar(a, b) { return !(a.x2 < b.x1 || b.x2 < a.x1 || a.y2 < b.y1 || b.y2 < a.y1); }
function iPolygon([lon, lat], ring) {
  let inne = false;
  for (let i = 0, j = ring.length - 1; i < ring.length; j = i++) {
    const [xi, yi] = ring[i], [xj, yj] = ring[j];
    if ((yi > lat) !== (yj > lat) && lon < (xj - xi) * (lat - yi) / (yj - yi) + xi) inne = !inne;
  }
  return inne;
}
function spannVid(ringSvg, y, x) {   // polygonens bredd på etikettens rad, och spannets mittpunkt
  const xs = [];
  for (let i = 0, j = ringSvg.length - 1; i < ringSvg.length; j = i++) {
    const [x1, y1] = ringSvg[i], [x2, y2] = ringSvg[j];
    if ((y1 > y) !== (y2 > y)) xs.push(x1 + (y - y1) * (x2 - x1) / (y2 - y1));
  }
  xs.sort((a, b) => a - b);
  for (let k = 0; k + 1 < xs.length; k += 2) if (x >= xs[k] - 1 && x <= xs[k + 1] + 1) return { bredd: xs[k + 1] - xs[k], mitt: (xs[k] + xs[k + 1]) / 2 };
  return { bredd: xs.length >= 2 ? xs[xs.length - 1] - xs[0] : 0, mitt: x };
}
function relLuminans(hex) {
  const c = hexTal(hex).map(v => v / 255).map(v => v <= 0.03928 ? v / 12.92 : Math.pow((v + 0.055) / 1.055, 2.4));
  return 0.2126 * c[0] + 0.7152 * c[1] + 0.0722 * c[2];
}
function textFarg(hex) {
  // Partifärg som text på papper: färgen blandas mot bläck i små steg tills kontrasten når WCAG:s 4,5:1.
  // V och M klarar gränsen och behåller sin färg exakt; SD-gult (1,6:1) och MP-grönt (3,0:1) mörkas.
  const lp = relLuminans(FARG.papper);
  const kontrast = f => { const l = relLuminans(f); return (Math.max(lp, l) + 0.05) / (Math.min(lp, l) + 0.05); };
  if (kontrast(hex) >= 4.5) return hex.toUpperCase();
  const black = hexTal(FARG.black), c = hexTal(hex);
  for (let t = 0.05; t <= 1.0001; t += 0.05) {
    const f = "#" + c.map((v, i) => Math.round(v + (black[i] - v) * t).toString(16).padStart(2, "0")).join("").toUpperCase();
    if (kontrast(f) >= 4.5) return f;
  }
  return FARG.black;
}
function styrkaSkala(val, p) {
  const varden = data().distrikt.filter(d => raknat(d, val)).map(d => Math.round((d[val][p] || 0) / d.giltiga[val] * 100));
  if (!varden.length) return { steg: 0, granser: [], klass: () => 0, farg: () => FARG.oraknat };   // inget distrikt räknat än
  const lo = Math.min(...varden), hi = Math.max(...varden), spann = hi - lo;
  const bas = parti(p).farg, ljus = relLuminans(bas) > 0.35;   // toppsteget är alltid partiets egen färg
  const steg = spann === 0 ? 1 : spann >= 6 ? 4 : 3;
  const toner = steg === 1 ? [1]
    : ljus ? (steg === 4 ? [0.22, 0.48, 0.74, 1] : [0.30, 0.62, 1])   // ljusa färger (SD, L): tonerna sprids mer
    : (steg === 4 ? [0.30, 0.55, 0.80, 1] : [0.35, 0.65, 1]);
  const granser = Array.from({ length: steg + 1 }, (_, i) => Math.round(lo + spann * i / steg));
  const farg = k => mix(bas, toner[k]);
  const klass = v => { let k = 0; for (let i = 1; i < steg; i++) if (v >= granser[i]) k = i; return k; };
  return { lo, hi, steg, granser, klass, farg };
}
const andelHeltal = (d, val, p) => Math.round((d[val][p] || 0) / d.giltiga[val] * 100);
function fyllFor(d, val, skala) {
  if (!raknat(d, val)) return FARG.oraknat;
  if (state.lage === "storsta") return parti(storsta(d[val])).farg;
  return skala.farg(skala.klass(andelHeltal(d, val, state.parti)));
}
function enfargad(val) {   // alla räknade distrikt har samma största parti: legenden säger allt
  return new Set(data().distrikt.filter(d => raknat(d, val)).map(d => storsta(d[val]))).size <= 1;
}
function etikettText(d, val, bredd) {   // vad som får plats på etikettraden i respektive läge
  if (!raknat(d, val)) return null;
  const S = state.bild ? STORLEK.mobil : storlek(), desktop = arDesktop() && !state.bild;
  if (state.lage === "storsta") {
    if (!desktop && enfargad(val)) return null;   // gäller även bildläget
    const p = storsta(d[val]), lang = `${p} ${andelHeltal(d, val, p)} %`;
    return desktop && bredd >= 130 && textBredd(lang, S.etikett, true) + 10 <= bredd ? lang : p;
  }
  const tal = String(andelHeltal(d, val, state.parti));
  return desktop && textBredd(tal + " %", S.etikett, true) + 10 <= bredd ? tal + " %" : tal;
}
function namnRader(namn) {
  if (namn.length <= 12 || !namn.includes(" ")) return [namn];
  const i = namn.lastIndexOf(" ");
  return [namn.slice(0, i), namn.slice(i + 1)];
}
function renderKarta() {
  const val = state.val, dm = distriktMap(), proj = projektion(gemensamBbox()), S = state.bild ? STORLEK.mobil : storlek(), desktop = arDesktop() && !state.bild;
  const skala = state.lage === "styrka" ? styrkaSkala(val, state.parti) : null;
  const svg = s("svg", { viewBox: `0 0 ${proj.bredd} ${proj.hojd.toFixed(1)}`, role: "group", "aria-label": `Karta över Majornas ${antalDistrikt()} valdistrikt, ${VALNAMN[val].toLowerCase()} ${state.ar}` });
  svg.append(s("title", {}, `Karta: ${VALNAMN[val]} ${state.ar} per valdistrikt`));
  const bg = state.bakgrund;
  const iBild = ([lon, lat]) => lon >= proj.W && lon <= proj.E && lat >= proj.S && lat <= proj.N;
  if (bg) {
    const parker = s("g", { class: "parker" }), vatten = s("g", { class: "vatten" });
    for (const ring of bg.parker || []) parker.append(s("path", { d: dAttr(ring, proj, true) }));
    for (const ring of bg.vatten || []) vatten.append(s("path", { d: dAttr(ring, proj, true) }));
    svg.append(parker, vatten);
  }
  const gDistrikt = s("g", { class: "distrikt-lager" }), ringar = {};
  for (const f of geo().features) {
    const d = dm[f.properties.kod];
    if (!d) continue;   // geometrikod utan valdata: hoppa över polygonen i stället för att kasta
    const ringSvg = f.geometry.coordinates[0].map(proj.till);
    ringar[d.kod] = ringSvg;
    const p = s("path", { class: "distrikt" + (state.vald === d.kod ? " vald" : ""), d: dRing(ringSvg, true),
      fill: fyllFor(d, val, skala), role: "button", tabindex: 0, "data-kod": d.kod, "aria-label": ariaDistrikt(d, val), "aria-pressed": String(state.vald === d.kod) });
    p.addEventListener("click", () => valjDistrikt(d.kod, true));
    p.addEventListener("keydown", e => { if (e.key === "Enter" || e.key === " ") { e.preventDefault(); valjDistrikt(d.kod, true); } });
    gDistrikt.append(p);
  }
  svg.append(gDistrikt);
  // distriktsetiketter bestäms först så att hållplatsnamn och platsnamn väjer för dem
  const etiketter = s("g", { class: "etiketter" }), upptaget = [];
  for (const f of geo().features) {
    const d = dm[f.properties.kod];
    if (!d) continue;
    const [lx, ly] = proj.till(f.properties.etikett), sp = spannVid(ringar[d.kod], ly, lx);
    const text = etikettText(d, val, sp.bredd), vald = state.vald === d.kod;
    if (!text && !vald) continue;
    const x = sp.bredd > 0 ? sp.mitt : lx;
    if (vald) {
      const rader = [...namnRader(d.namn), ...(text ? [text] : [])], st = [S.namn, ...rader.slice(1).map(() => S.namnRad2)];
      const hojd = st.reduce((a, b) => a + b, 0) * 1.05, w = Math.max(...rader.map((r, i) => textBredd(r, st[i], true)));
      const el = s("text", { class: "etikett-distrikt vald", x: x.toFixed(1), y: (ly - hojd / 2 + st[0] * 0.85).toFixed(1), "stroke-width": S.kontur + 1 });
      let dy = 0;
      rader.forEach((r, i) => { el.append(s("tspan", { x: x.toFixed(1), dy: dy.toFixed(1), "font-size": st[i] }, r)); dy = st[i] * 1.05; });
      upptaget.push({ x1: x - w / 2, x2: x + w / 2, y1: ly - hojd / 2, y2: ly + hojd / 2 });
      etiketter.append(el);
    } else {
      const w = textBredd(text, S.etikett, true);
      upptaget.push({ x1: x - w / 2, x2: x + w / 2, y1: ly - 0.45 * S.etikett, y2: ly + 0.55 * S.etikett });
      etiketter.append(s("text", { class: "etikett-distrikt" + (state.vald ? " dampad" : ""), x: x.toFixed(1), y: (ly + 0.35 * S.etikett).toFixed(1), "font-size": S.etikett, "stroke-width": S.kontur }, text));
    }
  }
  if (bg) {
    const bredd = { motorway: 7, trunk: 7, primary: 6, secondary: 5, tertiary: 4 };
    const gator = s("g", { class: "gator" }), grupper = {};
    for (const g of bg.gator || []) { const w = bredd[g.typ] || 2; grupper[w] = (grupper[w] || "") + dAttr(g.k, proj, false); }
    for (const [w, d] of Object.entries(grupper).sort((a, b) => a[0] - b[0])) gator.append(s("path", { d, "stroke-width": w }));
    const sparvag = s("g", { class: "sparvag" });
    sparvag.append(s("path", { d: (bg.sparvag || []).map(t => dAttr(t.k, proj, false)).join("") }));
    const hallplatser = s("g", { class: "hallplatser" }), urval = state.bild ? [] : desktop ? HALLPLATSER.desktop : HALLPLATSER.mobil;
    const valdNamn = state.vald && dm[state.vald] ? dm[state.vald].namn : null;
    for (const namn of urval) {
      const hp = (bg.hallplatser || []).find(h => h.namn === namn);
      if (!hp || !iBild(hp.k)) continue;
      const [x, y] = proj.till(hp.k);
      const cirkel = s("circle", { class: "hallplats", cx: x.toFixed(1), cy: y.toFixed(1), r: 4.5 });
      cirkel.append(s("title", {}, "Hållplats " + hp.namn));
      hallplatser.append(cirkel);
      if (hp.namn === valdNamn) continue;   // namnet dubblerar redan det valda distriktets namn på kartan
      const w = textBredd(hp.namn, S.hallplats, false), h1 = 0.35 * S.hallplats, h2 = 0.55 * S.hallplats;
      const lagen = [{ x: x + 8, anchor: "start", box: { x1: x + 8, x2: x + 8 + w, y1: y - h1, y2: y + h2 } },
                     { x: x - 8, anchor: "end", box: { x1: x - 8 - w, x2: x - 8, y1: y - h1, y2: y + h2 } }];
      const plats = lagen.find(l => !upptaget.some(b => overlappar(b, l.box)) && l.box.x1 >= 4 && l.box.x2 <= proj.bredd - 4);
      if (!plats) continue;
      upptaget.push(plats.box);
      hallplatser.append(s("text", { class: "hallplats-namn", x: plats.x.toFixed(1), y: (y + 0.35 * S.hallplats).toFixed(1), "font-size": S.hallplats, "text-anchor": plats.anchor }, hp.namn));
    }
    svg.append(gator, sparvag, hallplatser);
  }
  const markering = s("path", { class: "markering", d: state.vald && ringar[state.vald] ? dRing(ringar[state.vald], true) : "" });
  svg.append(markering, etiketter);
  if (bg) {
    const platser = s("g", { class: "platser" }), urval = state.bild ? [] : desktop ? PLATSNAMN.desktop : PLATSNAMN.mobil;
    for (const namn of urval) {
      const pl = (bg.platser || []).find(q => q.namn === namn);
      if (!pl || !iBild(pl.k)) continue;
      const [x, y] = proj.till(pl.k), w = textBredd(pl.namn, S.plats, false) * 1.3;
      const box = { x1: x - w / 2, x2: x + w / 2, y1: y - 0.8 * S.plats, y2: y + 0.2 * S.plats };
      if (box.x1 < 12 || box.x2 > proj.bredd - 12 || upptaget.some(b => overlappar(b, box))) continue;
      upptaget.push(box);
      platser.append(s("text", { class: "plats", x: x.toFixed(1), y: y.toFixed(1), "font-size": S.plats }, pl.namn.toUpperCase()));
    }
    svg.append(platser);
  }
  $("#karta").replaceChildren(svg);
  renderKartaLegend(val, skala);
  if (!state.bild) skrivUrl();
}
function renderKartaLegend(val, skala) {
  const ul = h("ul", { class: "legend" }), wrap = h("div");
  const oraknade = data().distrikt.filter(d => !raknat(d, val)).length;
  if (state.lage === "storsta") {
    const antal = {};
    for (const d of data().distrikt) if (raknat(d, val)) { const p = storsta(d[val]); antal[p] = (antal[p] || 0) + 1; }
    for (const [p, n] of Object.entries(antal).sort((a, b) => b[1] - a[1]))
      ul.append(h("li", {}, h("span", { class: "swatch", style: `background:${parti(p).farg}` }), `${parti(p).namn} störst i ${n} distrikt`));
  } else if (skala.steg) {
    wrap.append(h("p", { class: "legend-titel" }, `${parti(state.parti).namn}, andel av rösterna i procent`));
    for (let k = 0; k < skala.steg; k++) {
      const fran = skala.granser[k], till = k === skala.steg - 1 ? skala.granser[k + 1] : skala.granser[k + 1] - 1;
      ul.append(h("li", {}, h("span", { class: "swatch", style: `background:${skala.farg(k)}` }), fran >= till ? `${fran} %` : `${fran} till ${till} %`));
    }
  }
  if (oraknade) ul.append(h("li", {}, h("span", { class: "swatch", style: `background:${FARG.oraknat}` }), `Inte räknat än (${oraknade})`));
  wrap.append(ul);
  $("#karta-legend").replaceChildren(wrap);
}
const lugn = () => window.matchMedia("(prefers-reduced-motion: reduce)").matches;
function valjDistrikt(kod, franKartan) {
  state.vald = state.vald === kod ? null : kod;
  renderKarta(); renderPanel(); renderTabell();
  if (!franKartan) return;
  const p = $(`#karta path.distrikt[data-kod="${kod}"]`);
  if (p) p.focus({ preventScroll: true });   // omrenderingen tappar annars tangentbordsfokus
  if (!state.vald || arBred()) return;
  const svg = $("#karta svg").getBoundingClientRect();
  if (svg.height + 80 < innerHeight) $("#panel").scrollIntoView({ block: "nearest", behavior: lugn() ? "auto" : "smooth" });
}

/* ---- panelen */
function stapelRad(p, andel, markorer, swing, dampad) {
  const w = Math.min(100, andel / state.skalmax * 100);
  const varde = h("div", { class: "stapel-varde" }, procent(andel));
  if (swing !== null && swing !== undefined) varde.append(h("span", { class: "swing", title: "Förändring mot förra valet i procentenheter" }, pe(swing)));
  return h("div", { class: "stapel-rad" + (dampad ? " dampad" : ""), role: "group", "aria-label": `${parti(p).namn} ${procent(andel)}` },
    h("div", { class: "stapel-namn" }, h("b", {}, p), h("small", {}, namnMedMjukaBindestreck(parti(p).namn))),
    h("div", { class: "stapel-spar" }, h("div", { class: "stapel-fyll", style: `width:${w.toFixed(1)}%;background:${parti(p).farg}` }),
      markorer.filter(m => m.andel !== undefined).map(m => h("span", { class: "markor " + m.klass, style: `left:${Math.min(100, m.andel / state.skalmax * 100).toFixed(1)}%`, title: `${m.namn} ${procent(m.andel)}` }))),
    varde);
}
function toppTre(roster, giltiga) {
  return andelar(roster, giltiga).filter(a => a.p !== "Övriga").slice(0, 3).map(a => `${a.p} ${procent(a.andel)}`).join(", ");
}
/* ---- "Hur har det ändrats": bara det swingfilen tillåter. Jämförbart distrikt får talen, omritat får en
   mening och områdesraden, hela Majorna får talen med kohorttext. Ett parti utan tal i swingen (inte
   redovisat båda åren) hoppas över helt, det skrivs aldrig som 0,0. Kohorten räknar distrikt som är både
   räknade och jämförbara, därför står det "jämförbara distrikt" och inte bara "distrikt" som statusraden. */
const toppMedTal = (roster, giltiga, diff) =>
  andelar(roster, giltiga).filter(a => a.p !== "Övriga" && diff[a.p] !== undefined).slice(0, 3);
// Kohortförbehållet som slut på en mening: hela området mot hela basåret behöver bara punkten. Punkten
// hör till satsen och skrivs här, så att inget anropsställe behöver pröva helomrade en andra gång.
const kohortSlut = k => k.helomrade ? "." : `, räknat på ${k.antal} jämförbara distrikt av ${k.totalt}.`;
const kohortFor = val => { const sw = state.swing[state.ar]; return sw && sw.kohort ? sw.kohort[val] : null; };
const andratRubrik = () => h("h4", { class: "andrat-rubrik" }, "Hur har det ändrats");
// Talen skiljs av riktiga mellanslag: raden får brytas mellan två tal, aldrig inuti ett ("S +3,8" hålls
// ihop av .andrat-tal { white-space: nowrap }). h() plattar barnarrayen ett steg, så flatMap räcker.
const talrad = (bas, topp, diff, slut) =>
  h("p", { class: "andrat-rad" }, `Sedan ${bas}: `,
    topp.flatMap(a => [h("span", { class: "andrat-tal" }, `${a.p} ${pe(diff[a.p])}`), " "]),
    h("span", { class: "andrat-enhet" }, "procentenheter" + slut));
// Områdesraden faller bort när distriktets största parti saknar tal på områdesnivån (partiet redovisas
// inte båda åren i hela Majorna). Då står omritningsmeningen ensam; avsiktligt, hellre ingen rad än ett
// annat partis tal under ett distrikt som handlar om det största.
function omradesRad(sw, val, p) {
  const omrade = (sw.majorna || {})[val], k = (sw.kohort || {})[val];
  if (!omrade || omrade[p] === undefined || !k || !k.antal) return null;
  return h("p", { class: "andrat-rad" }, `Hela Majorna: ${p} ${pe(omrade[p])} sedan ${sw.bas}${kohortSlut(k)}`);
}
function hurAndrat(d, val) {
  const sw = state.swing[state.ar];
  if (!sw || !raknat(d, val)) return null;
  const post = (sw.distrikt || {})[d.kod], ej = (sw.ej_jamforbara || {})[d.kod];
  if (post && post[val]) {
    const topp = toppMedTal(d[val], d.giltiga[val], post[val]);
    if (!topp.length) return null;   // inget av distriktets partier redovisas båda åren
    return h("div", { class: "andrat" }, andratRubrik(), talrad(sw.bas, topp, post[val], "."));   // distriktets egna tal, inget kohortförbehåll
  }
  if (ej) {
    const storst = storsta(d[val]);
    const delar = [andratRubrik(), h("p", { class: "andrat-text" }, ej.mening || `Gränserna för ${d.namn} ritades om till ${sw.ar}. Siffrorna går inte att jämföra med ${sw.bas}.`)];
    if (ej.omradesrad !== false && storst) { const rad = omradesRad(sw, val, storst); if (rad) delar.push(rad); }
    return h("div", { class: "andrat" }, delar);
  }
  return null;
}
function hurAndratMajorna(val) {
  const sw = state.swing[state.ar], m = majorna(val);
  if (!sw || !m || !m.giltiga) return null;
  const omrade = (sw.majorna || {})[val], k = (sw.kohort || {})[val];
  if (!omrade || !Object.keys(omrade).length || !k || !k.antal) return null;
  const topp = toppMedTal(m.roster, m.giltiga, omrade);
  if (!topp.length) return null;
  return h("div", { class: "andrat" }, andratRubrik(), talrad(sw.bas, topp, omrade, kohortSlut(k)));
}
function renderPanel() {
  const val = state.val, dm = distriktMap(), d = state.vald ? dm[state.vald] : null, m = majorna(val);
  const rubrik = $("#panel-rubrik"), tillbaka = $("#panel-tillbaka"), hint = $("#panel-hint"),
        sub = $("#panel-sub"), not = $("#panel-not"), staplar = $("#panel-staplar"), knappar = $("#panel-knappar");
  not.innerHTML = ""; staplar.innerHTML = ""; knappar.innerHTML = "";
  tillbaka.hidden = !d; hint.hidden = !!d;
  tillbaka.onclick = () => valjDistrikt(state.vald);
  let toppText = "", subText = "", liveSlut = "";
  // De små talen vid staplarna. Ett distrikts egna tal behöver inget förbehåll, men hela Majornas är
  // räknade på kohorten (räknade och jämförbara distrikt) medan staplarna vilar på alla räknade: då ska
  // noten säga vad talen vilar på. Anropet skickar kohorten bara i Hela Majorna-grenen.
  // En kohort utan distrikt (inget räknat och jämförbart än) får inget förbehåll: "räknat på 0
  // jämförbara distrikt av 23" säger inget om talen, som då kommer från kartans egna markörer.
  const markorNot = [], swingNot = (sw, k) => sw ? [h("span", { style: "padding-left:0" },
    `Små tal: förändring mot ${state.swing[state.ar].bas} i procentenheter${k && k.antal ? kohortSlut(k) : "."}`)] : [];
  if (d && !raknat(d, val)) {
    rubrik.textContent = d.namn;
    toppText = `${VALNAMN[val]} ${state.ar}: inte räknat än.`;
    const bas = Object.keys(state.data).filter(a => a !== state.ar && state.data[a].distrikt.some(x => x.kod === d.kod && raknat(x, val))).sort().pop();
    if (bas) {
      const b = state.data[bas].distrikt.find(x => x.kod === d.kod);
      not.append(h("p", { class: "not" }, h("b", {}, `Så röstade ${d.namn} ${bas}`), ` (${VALNAMN[val].toLowerCase()}, ${tal(b.giltiga[val])} giltiga röster).`));
      for (const a of andelar(b[val], b.giltiga[val])) if (a.andel >= 0.01) staplar.append(stapelRad(a.p, a.andel, [], null, true));
    }
  } else if (d) {
    rubrik.textContent = d.namn;
    toppText = `${VALNAMN[val]} ${state.ar}: ${toppTre(d[val], d.giltiga[val])}.`;
    let vd = "";
    if (d.rostberattigade[val]) vd = `Valdeltagande ${procent(d.rostande[val] / d.rostberattigade[val])}` + (majornaRaknat(val) && m.rostberattigade ? ` (Majorna ${procent(m.rostande / m.rostberattigade)})` : "");
    subText = (vd ? vd + ". " : "") + `${tal(d.giltiga[val])} giltiga röster.`;
    const markorer = majornaRaknat(val) ? [{ klass: "majorna", namn: "Majorna" }] : [], swing = swingFor(d.kod, val);
    // meta.valnatt räknar distrikt där något val är räknat: räkna per visat val, som statusraden nedan gör
    const vnD = raknadeIVal(val);
    if (markorer.length) markorNot.push(h("span", { class: "majorna" }, KONFIG.valnatt && vnD.raknade < vnD.totalt ? "Snittet för räknade distrikt i Majorna" : "Snittet för hela Majorna"));
    markorNot.push(...swingNot(swing));   // distriktets egna tal, inget förbehåll
    for (const a of andelar(d[val], d.giltiga[val])) if (a.andel >= 0.01)
      staplar.append(stapelRad(a.p, a.andel, markorer.map(x => ({ ...x, andel: m.giltiga ? (m.roster[a.p] || 0) / m.giltiga : undefined })), swing ? swing[a.p] : null));
    const andrat = hurAndrat(d, val);
    if (andrat) {
      staplar.append(andrat);
      // Är distriktet omritat ska skärmläsaren höra förbehållet sist, med kortets egen mening.
      const mening = andrat.querySelector(".andrat-text");
      if (mening) liveSlut = " " + mening.textContent;
    }
    knappar.append(h("button", { type: "button", class: "till-kartan", onclick: () => $("#karta").scrollIntoView({ block: "start", behavior: lugn() ? "auto" : "smooth" }) }, "Tillbaka till kartan"));
  } else {
    rubrik.textContent = "Hela Majorna";
    if (!majornaRaknat(val)) {
      toppText = `${VALNAMN[val]} ${state.ar}: inget distrikt räknat än.`;
    } else {
      const omr = jamforelseOmrade(val), post = omr.post, swing = swingFor(null, val);
      const rak = raknadeIVal(val), vn = rak.totalt ? rak : data().meta.valnatt;   // samma källa som statusraden, meta som reserv
      toppText = `${VALNAMN[val]} ${state.ar}: ${toppTre(m.roster, m.giltiga)}.`;
      let vd = "";
      if (m.rostberattigade) {
        const namnLabel = val === "rd" ? "riket" : omr.namn;
        vd = `Valdeltagande ${procent(m.rostande / m.rostberattigade)}` + (post && post.valdeltagande && !omradeDelvis(post) ? ` (${namnLabel} ${procent(post.valdeltagande)})` : "");
      }
      subText = (KONFIG.valnatt && vn && vn.raknade < vn.totalt ? `${vn.raknade} av ${vn.totalt} distrikt räknade. ` : "") + (vd ? vd + ". " : "") + `${tal(m.giltiga)} giltiga röster.`;
      const markorer = [];
      if (post && post.andel) { markorer.push({ klass: "", namn: omr.namn, andelar: post.andel }); markorNot.push(h("span", {}, `Snittet i ${omr.namn}`)); }
      markorNot.push(...swingNot(swing, kohortFor(val)));   // områdets tal vilar på kohorten
      for (const a of andelar(m.roster, m.giltiga)) if (a.andel >= 0.01)
        staplar.append(stapelRad(a.p, a.andel, markorer.map(x => ({ ...x, andel: x.andelar[a.p] })), swing ? swing[a.p] : null));
      const andratM = hurAndratMajorna(val);
      if (andratM) staplar.append(andratM);
    }
  }
  sub.textContent = subText; sub.hidden = !subText;
  if (markorNot.length) not.append(h("div", { class: "markorer", "aria-hidden": "true" }, markorNot));
  $("#panel-live").textContent = `${rubrik.textContent}. ${toppText}${liveSlut}`;
  skrivUrl();
}

/* ---- tabellen */
function renderTabell() {
  const knapp = $("#tabell-knapp"), wrap = $("#tabell");
  knapp.onclick = () => { state.tabellOppen = !state.tabellOppen; renderTabell(); if (state.tabellOppen) wrap.scrollIntoView({ block: "nearest" }); };
  knapp.setAttribute("aria-expanded", String(state.tabellOppen));
  knapp.textContent = state.tabellOppen ? "Dölj tabellen" : "Visa alla distrikt som tabell";
  wrap.hidden = !state.tabellOppen;
  if (!state.tabellOppen) { wrap.innerHTML = ""; return; }
  const val = state.val, partier = partierIVal(val);
  const rader = data().distrikt.map(d => {
    const r = { kod: d.kod, namn: d.namn, raknat: raknat(d, val), vd: d.rostberattigade[val] ? d.rostande[val] / d.rostberattigade[val] : null };
    for (const p of partier) r[p] = r.raknat ? (d[val][p] || 0) / d.giltiga[val] : null;
    return r;
  });
  const { kol, fallande } = state.sortering;
  rader.sort((a, b) => {
    if (kol === "namn") return a.namn.localeCompare(b.namn, "sv") * (fallande ? -1 : 1);
    const x = a[kol] ?? -1, y = b[kol] ?? -1;
    return (y - x) * (fallande ? 1 : -1);
  });
  const sortera = kolNamn => { state.sortering = { kol: kolNamn, fallande: kol === kolNamn ? !fallande : kolNamn !== "namn" }; renderTabell(); };
  const th = (kolNamn, text) => h("th", { scope: "col", "aria-sort": kol === kolNamn ? (fallande ? "descending" : "ascending") : "none" },
    h("button", { type: "button", onclick: () => sortera(kolNamn) }, text));
  const radTangent = (r, e) => { if (e.key === "Enter" || e.key === " ") { e.preventDefault(); valjDistrikt(r.kod); } };
  const tabell = h("table", { class: "distrikt" },
    h("caption", {}, `${VALNAMN[val]} ${state.ar}, andel av giltiga röster per distrikt. Tryck på en kolumn för att sortera, på en rad för att välja distrikt.`),
    h("thead", {}, h("tr", {}, th("namn", "Distrikt"), partier.map(p => th(p, p)), th("vd", "Valdelt."))),
    h("tbody", {}, rader.map(r => h("tr", { class: r.kod === state.vald ? "vald" : "", tabindex: "0",
      onclick: () => valjDistrikt(r.kod), onkeydown: e => radTangent(r, e) },
      h("td", {}, r.namn), partier.map(p => h("td", {}, r.raknat ? procent(r[p]) : "-")), h("td", {}, r.vd !== null && r.raknat ? procent(r.vd) : "-")))));
  wrap.replaceChildren(h("div", { class: "tabell-wrap" }, tabell));
}

/* ---- röstdelningen: riksdag, region och kommun för varje parti på en gemensam procentaxel */
const RD_FORM = { rd: "cirkel", rf: "romb", kf: "kvadrat" };
const RD_KORT = { rd: "Riksdag", rf: "Region", kf: "Kommun" };
const RD_LED = { rd: "riksdags", rf: "region", kf: "kommun" };   // "riksdags-, region- och kommunvalet"
const andelTal = a => (a * 100).toLocaleString("sv-SE", { minimumFractionDigits: 1, maximumFractionDigits: 1 });
function renderRostdelning() {
  const sek = $("#rostdelning"), rader = $("#rostdelning-rader"), legend = $("#rostdelning-legend");
  const namnPaVal = data().meta.val || VALNAMN, distrikt = data().distrikt || [];
  const val = ["rd", "rf", "kf"].filter(v => distrikt.some(d => raknat(d, v)));
  if (val.length < 2) { sek.hidden = true; return; }
  // kohort: bara distrikt som är räknade i alla val som visas, annars jämförs olika områden med varandra
  const kohort = distrikt.filter(d => val.every(v => raknat(d, v)));
  if (!kohort.length) { sek.hidden = true; return; }
  sek.hidden = false;
  const summa = {};
  for (const v of val) {
    const post = { giltiga: 0, roster: {} };
    for (const d of kohort) { post.giltiga += d.giltiga[v]; for (const [p, n] of Object.entries(d[v])) post.roster[p] = (post.roster[p] || 0) + n; }
    summa[v] = post;
  }
  const andel = (v, p) => (summa[v].roster[p] !== undefined && summa[v].giltiga) ? summa[v].roster[p] / summa[v].giltiga : null;
  const alla = [...new Set(val.flatMap(v => Object.keys(summa[v].roster)))].filter(p => p !== "Övriga");
  const poster = alla.map(p => ({ p, varden: val.map(v => andel(v, p)) })).filter(r => r.varden.some(a => a !== null && a >= 0.01));
  if (!poster.length) { sek.hidden = true; return; }
  const huvud = val.includes("rd") ? "rd" : val[0], sist = val.includes("kf") ? "kf" : val[val.length - 1];
  poster.sort((a, b) => {   // fallande på riksdagsandel, partier utan riksdagsröster sist på kommunandel
    const av = andel(huvud, a.p), bv = andel(huvud, b.p);
    if (av === null && bv === null) return (andel(sist, b.p) || 0) - (andel(sist, a.p) || 0);
    if (av === null) return 1;
    if (bv === null) return -1;
    return bv - av;
  });
  const hogsta = Math.max(...poster.flatMap(r => r.varden.filter(a => a !== null)));
  const max = Math.max(0.05, Math.ceil(hogsta * 20) / 20);   // närmaste 5 procent över högsta värdet
  const pos = a => a / max * 100;
  const kolumner = barn => h("div", { class: "rd-tal" }, barn);
  legend.replaceChildren(...val.map(v => h("span", {}, h("i", { class: "rd-form rd-" + RD_FORM[v] }), RD_KORT[v])));
  const beskrivning = poster.map(r => `${parti(r.p).namn}: ` + val.map((v, i) => `${namnPaVal[v].toLowerCase()} ${r.varden[i] === null ? "inget resultat" : procent(r.varden[i])}`).join(", ")).join("; ") + ".";
  const grafik = h("div", { class: "rd-grafik", role: "img", "aria-label": `Andel av giltiga röster per val och parti. ${beskrivning}` });
  grafik.append(h("div", { class: "rd-huvud", "aria-hidden": "true" }, h("div"), h("div"),
    kolumner(val.map(v => h("span", {}, RD_KORT[v])))));
  for (const r of poster) {
    const finns = r.varden.filter(a => a !== null);
    const lo = Math.min(...finns), hi = Math.max(...finns);
    const axel = h("div", { class: "rd-axel" }, h("span", { class: "rd-spar" }),
      finns.length > 1 ? h("span", { class: "rd-spann", style: `left:${pos(lo).toFixed(2)}%;width:${(pos(hi) - pos(lo)).toFixed(2)}%` }) : null,
      val.map((v, i) => r.varden[i] === null ? null
        : h("span", { class: "rd-markor rd-" + RD_FORM[v], style: `left:${pos(r.varden[i]).toFixed(2)}%;background:${parti(r.p).farg}` })));
    grafik.append(h("div", { class: "rd-rad" },
      h("div", { class: "rd-parti" }, h("b", {}, r.p), h("small", {}, namnMedMjukaBindestreck(parti(r.p).namn))), axel,
      kolumner(r.varden.map(a => h("span", {}, a === null ? "-" : andelTal(a))))));
  }
  const steg = max > 0.25 ? 0.1 : 0.05, ticks = [];
  for (let v = 0; v <= max + 1e-9; v += steg) ticks.push(Math.round(v * 1000) / 1000);
  grafik.append(h("div", { class: "rd-rad rd-axelrad", "aria-hidden": "true" }, h("div"),
    h("div", { class: "rd-axel-tal" }, ticks.map((v, i) => h("span", {   // ytterkanternas tal hålls innanför axeln, annars rullar sidan i sidled
      style: `left:${pos(v).toFixed(2)}%;transform:translateX(${i === 0 ? "0" : i === ticks.length - 1 ? "-100%" : "-50%"})` }, Math.round(v * 100) + (i === 0 ? " %" : "")))), h("div")));
  rader.replaceChildren(grafik);
  const led = val.map(v => RD_LED[v]), valText = led.slice(0, -1).join("-, ") + "- och " + led[led.length - 1] + "valet";
  const kohortText = kohort.length < distrikt.length ? ` Räknat på ${kohort.length} av ${distrikt.length} distrikt.` : "";
  $("#rostdelning-not").textContent = `Så röstar Majorna olika i ${valText} ${state.ar}. Ju längre streck, desto mer röstdelning.` + kohortText;
}

/* ---- Majorna mot Sverige: divergerande staplar mot riket, Västra Götaland eller Göteborg */
function jamforelseOmrade(val) {
  if (val === "kf") return { namn: "Göteborg", genitiv: "Göteborgs", post: jamforelse("goteborg", val) };
  const riket = jamforelse("riket", val);
  const namn = riket && riket.namn && riket.namn !== "Riket" ? riket.namn : "Sverige";
  return { namn, genitiv: namn === "Sverige" ? "rikets" : namn + "s", post: riket };
}
function divergens(val, ar, kompakt = false, bild = false) {
  const d = state.data[ar || state.ar], m = d.aggregat.majorna[val], omr = jamforelseOmrade(val);
  if (!m || !m.giltiga || !omr.post || !omr.post.andel) return null;
  const rader = Object.keys(m.roster).filter(p => p !== "Övriga" && omr.post.andel[p] !== undefined)
    .map(p => ({ p, diff: (m.roster[p] / m.giltiga - omr.post.andel[p]) * 100 })).sort((a, b) => b.diff - a.diff);
  const max = Math.max(5, Math.ceil(Math.max(...rader.map(r => Math.abs(r.diff))) / 5) * 5);
  const steg = max > 15 ? 10 : 5;
  const pos = v => 50 + v / max * 50;
  const el = h("div", { class: "divergens", role: "img", "aria-label": `Skillnad mot ${omr.namn} i procentenheter: ` + rader.map(r => `${r.p} ${pe(r.diff)}`).join(", ") + "." });
  el.append(h("div", { class: "div-huvud" }, h("div"), h("div", {}, h("span", {}, "Mindre stöd i Majorna"), h("span", {}, "Större stöd i Majorna"))));
  const ticks = [0]; if (!bild) for (let v = steg; v <= max; v += steg) ticks.push(-v, v);
  ticks.sort((a, b) => a - b);
  for (const r of rader) {
    const w = Math.abs(r.diff) / max * 50, plus = r.diff >= 0;
    const omrade = h("div", { class: "div-omrade" }, ticks.filter(v => v).map(v => h("span", { class: "div-grid", style: `left:${pos(v)}%` })),
      h("span", { class: "div-noll", style: "left:50%" }),
      h("span", { class: "div-stapel", style: `${plus ? "left" : "right"}:50%;width:${w.toFixed(2)}%;background:${parti(r.p).farg}` }),
      h("span", { class: "div-varde", style: plus ? `left:calc(${(50 + w).toFixed(2)}% + 8px)` : `right:calc(${(50 + w).toFixed(2)}% + 8px)` }, pe(r.diff)));
    el.append(h("div", { class: "div-rad" }, h("div", { class: "div-parti" }, r.p), omrade));
  }
  el.append(h("div", { class: "div-axel" }, h("div"), h("div", {}, ticks.map(v => h("span", { style: `left:${pos(v)}%` }, v === 0 ? (kompakt ? "0" : `0 = ${omr.genitiv} nivå`) : (v > 0 ? "+" : "") + v)))));
  return { el, omr, rader };
}
function renderJamforelse() {
  const valLista = Object.keys(data().meta.val || VALNAMN);
  if (!divergens(state.jamforelseVal)) {
    const forsta = valLista.find(v => divergens(v));   // saknat val: byt till första tillgängliga i stället för att dölja
    if (forsta) state.jamforelseVal = forsta;
  }
  const sek = $("#jamforelse"), val = state.jamforelseVal, res = divergens(val, null, true);
  const knappar = $("#jamforelse-val");
  knappar.innerHTML = "";
  for (const v of valLista) {
    if (!divergens(v)) continue;
    knappar.append(h("button", { type: "button", role: "radio", "aria-checked": String(v === val), tabindex: v === val ? "0" : "-1",
      onclick: () => { state.jamforelseVal = v; renderJamforelse(); } }, (data().meta.val || VALNAMN)[v]));
  }
  pilNavigering(knappar);
  if (!res) { sek.hidden = true; return; }
  sek.hidden = false;
  $("#jamforelse-rubrik").textContent = `Majorna mot ${res.omr.namn}`;
  $("#jamforelse-not").textContent = `${VALNAMN[val]} ${state.ar} - skillnad i procentenheter mellan Majorna och ${res.omr.namn}. Noll är ${res.omr.genitiv} nivå.`;
  $("#divergens").replaceChildren(res.el);
  const forbehall = $("#jamforelse-forbehall"), delvis = omradeDelvis(res.omr.post);
  forbehall.hidden = !delvis;
  forbehall.textContent = delvis ? `${res.omr.namn}: ${raknadeText(res.omr.post)}.` : "";   // områdets visningsnamn ("Sverige"), samma som i rubriken
}
/* ---- bildläge för nyhetsbrev och sociala medier: ?bild=jamforelse&val=rd&format=liggande|kvadrat&etikett=... */
function renderBild(typ) {
  const q = new URLSearchParams(location.search), format = q.get("format") === "kvadrat" ? "kvadrat" : "liggande";
  const val = VALNAMN[q.get("val")] ? q.get("val") : "rd";
  rot.classList.add("bild");
  state.bild = true;   // gäller båda bilderna: ResizeObserver får inte rita om en karta som bildramen ersatt
  const ram = h("div", { class: "bildram", "data-format": format });
  const vard = (() => { try { return new URL(KONFIG.adress).host; } catch (e) { return KONFIG.adress; } })();
  if (typ === "jamforelse") {
    const res = divergens(val, null, false, true);
    if (!res) { ram.append(h("p", { class: "fel" }, "Jämförelsedata saknas för " + val)); }
    else {
      const rubrik = `Majorna mot ${res.omr.namn}`, n = res.rader.length;
      ram.append(h("p", { class: "etikett" }, q.get("etikett") || `Majposten · Valet ${state.ar}`),
        h("h1", {}, rubrik), h("p", { class: "bild-sub" }, `${VALNAMN[val]} ${state.ar} · skillnad i procentenheter`), res.el,
        h("p", { class: "bild-fot" }, `Källa: Valmyndigheten. Så röstade Majorna - hela grafiken på ${vard}`));
      $(".mp-main").replaceChildren(ram);
      // radhöjd efter antal rader, sedan säkerhetsnät: allt ska rymmas i ramen
      const kvadrat = format === "kvadrat", faktor = kvadrat ? 0.52 : 0.68;
      let radH = kvadrat ? (n <= 8 ? 84 : n <= 10 ? 68 : 60) : (n <= 8 ? 38 : n <= 10 ? 32 : 29);
      if (kvadrat && rubrik.length > 20) ram.style.setProperty("--rubrik", "52px");
      const satt = () => { ram.style.setProperty("--radH", radH + "px"); ram.style.setProperty("--stapelH", Math.round(radH * faktor) + "px"); };
      satt();
      while (ram.scrollHeight > ram.clientHeight && radH > 22) { radH -= 1; satt(); }
      return;
    }
  } else if (typ === "karta") {
    state.vald = null;
    if (!VALNAMN[state.val]) state.val = "rd";
    if (!partierIVal(state.val).includes(state.parti)) state.parti = partierIVal(state.val)[0];
    ram.classList.add("karta-bild");
    const under = state.lage === "styrka"
      ? `${parti(state.parti).namn}s andel i ${VALNAMN[state.val].toLowerCase()} ${state.ar}, ${antalDistrikt()} valdistrikt`
      : `Största parti i ${VALNAMN[state.val].toLowerCase()} ${state.ar}, ${antalDistrikt()} valdistrikt`;
    const etikett = h("p", { class: "etikett" }, q.get("etikett") || `Majposten · Valet ${state.ar}`);
    const rubrik = h("h1", {}, "Så röstade ditt kvarter"), sub = h("p", { class: "bild-sub" }, under);
    const legend = h("div", { id: "karta-legend", class: "karta-legend" }), karta = h("div", { id: "karta" });
    const uppmaning = h("p", { class: "bild-uppmaning" }, `Tryck på ditt kvarter på ${vard}`);
    const fot = h("p", { class: "bild-fot" }, "Valdata: Valmyndigheten. Kartunderlag © OpenStreetMaps bidragsgivare.");
    if (format === "kvadrat") ram.append(etikett, rubrik, sub, karta, legend, uppmaning, fot);
    else ram.append(h("div", { class: "bild-text" }, etikett, rubrik, sub, legend, uppmaning, fot), karta);
    $(".mp-main").replaceChildren(ram);
    renderKarta();
    return;
  } else ram.append(h("p", { class: "fel" }, "Okänd bildtyp: " + typ));
  $(".mp-main").replaceChildren(ram);
}

/* ---- Majorna sedan 2006: områdesserien ur data/historik.js, följer kartans val, inga egna knappar */
const HIST_PARTIER = { mobil: ["V", "S", "MP", "SD"], desktop: ["V", "S", "MP", "SD", "M"] };
const histPartier = () => arDesktop() ? HIST_PARTIER.desktop : HIST_PARTIER.mobil;
// Redaktionell konstant: FI fick 3 458 av 20 960 giltiga riksdagsröster i Majorna 2014, alltså 16,5 procent.
// Talet står i historikdatabasens tabell tidsserie (2014, rd, majorna, FI). Serien följer sidans partiuppsättning
// per val, där FI inte är nyckelparti i riksdagsvalet, så rösterna ligger i Övriga och går inte att räkna fram ur filen.
const HIST_NOT_FI_2014 = "16,5";
function historikSerie(val, niva) {
  const h = state.historik;
  return h && h.serie && h.serie[val] && h.serie[val][niva] ? h.serie[val][niva] : [];
}
const histAr = () => ((state.historik || {}).meta || {}).ar || [];   // seriens år, tom lista när filen saknas
const senasteAr = () => (KONFIG.ar || []).map(Number).filter(a => a).sort((a, b) => a - b).pop();
const histLista = a => a.length === 1 ? String(a[0]) : a.slice(0, -1).join(", ") + " och " + a[a.length - 1];
const histHarTal = (pt, q) => pt.andel[q] !== undefined && pt.andel[q] !== null;   // parti utan tal ritas inte som noll
function aretsPunkt(val, niva) {
  // Punkten för det senaste laddade året i seriens form, inte för det år kartans årsknapp visar: sektionen
  // följer kartans val men inte dess år. Punkten finns bara när alla distrikt i valet är räknade; annars
  // null, och året står som tom ring på axeln.
  const ar = senasteAr(), d = state.data[String(ar)];
  if (!d || histAr().includes(ar)) return null;
  const { raknade, totalt } = raknadeIVal(val, d);
  if (!totalt || raknade < totalt) return null;
  const preliminar = arPreliminar(d);
  if (niva === "majorna") {
    const m = (d.aggregat.majorna || {})[val];
    if (!m || !m.giltiga) return null;
    const andel = {};
    for (const [q, n] of Object.entries(m.roster)) andel[q] = n / m.giltiga;
    return { ar, andel, giltiga: m.giltiga, rostande: m.rostande, rostberattigade: m.rostberattigade,
             valdeltagande: m.rostberattigade ? m.rostande / m.rostberattigade : null,
             antal_distrikt: (d.distrikt || []).length, preliminar };
  }
  const post = (d.aggregat[niva] || {})[val] || null;
  // Ett delvis räknat jämförelseområde får ingen punkt: en halvräknad kommun ligger långt under sitt
  // slutresultat och skulle se ut som ett ras i valdeltagandebilden.
  if (!post || !post.andel || omradeDelvis(post)) return null;
  return { ar, andel: post.andel, valdeltagande: post.valdeltagande || null, preliminar };
}
function histPunkter(val, niva) {   // serien plus årets punkt när den finns
  const extra = aretsPunkt(val, niva);
  return historikSerie(val, niva).map(p => ({ ...p, preliminar: false })).concat(extra ? [extra] : []);
}
function histAxelAr() {
  // Årtalen på x-axeln: seriens år, det senaste laddade året och valåret ur konfigen, stigande och utan
  // dubbletter. Ett år utan punkt får stå som tom ring - före valdagen slutar linjerna på 2022 medan axeln
  // redan visar 26.
  const ar = new Set(histAr());
  const senaste = senasteAr(), valdagAr = Number(String(KONFIG.valdag || "").slice(0, 4));
  if (senaste) ar.add(senaste);
  if (valdagAr) ar.add(valdagAr);
  return [...ar].sort((a, b) => a - b);
}
function sistaPunkt(val) { const p = histPunkter(val, "majorna"); return p[p.length - 1]; }
function histMening(val) {
  const egen = ((KONFIG.historik || {}).mening || {})[val];
  if (egen) return egen;
  // Meningen fryses på senaste slutliga år, så att den inte ändrar sig under valnattens uppdateringar.
  const serie = historikSerie(val, "majorna"), forsta = serie[0], sista = [...histPunkter(val, "majorna")].reverse().find(p => !p.preliminar) || serie[serie.length - 1];
  const p = "V";
  return `${p} har gått från ${andelTal(forsta.andel[p] || 0)} till ${andelTal(sista.andel[p] || 0)} procent i ${VALNAMN[val].toLowerCase()} sedan ${forsta.ar}.`;
}
function antalDistriktText(val) {   // "17 år 2006, 2010 och 2014, 22 år 2018, 23 år 2022"
  const grupper = [];
  for (const p of histPunkter(val, "majorna")) {
    if (p.antal_distrikt == null) continue;
    const g = grupper[grupper.length - 1];
    if (g && g.n === p.antal_distrikt) g.ar.push(p.ar); else grupper.push({ n: p.antal_distrikt, ar: [p.ar] });
  }
  return grupper.map(g => `${g.n} år ${histLista(g.ar)}`).join(", ");
}
// Bild A och bild B delar ritsätt: ytans bredd, x-skalan, hjälplinjer med tal i vänsterkanten, årtal under
// axeln, en serie med hål i linjen, etiketter som skjuts isär och den tomma ringen för ett år som inte får
// ritas än.
// Golvet 200 gäller bara degenererade containrar: på en 320 px-telefon är ytan 288 px och viewBox ska vara
// lika bred, annars sträcker CSS ut bilden och axeltexten växer.
const histYta = el => Math.max(200, el.clientWidth || 358);
const histXSkala = (M, W, axelAr) => i => M.v + i * (W - M.v - M.h) / Math.max(1, axelAr.length - 1);
function histHjalplinjer(svg, { M, W, y, fran, till, steg }) {
  for (let v = fran; v <= till + 1e-9; v += steg) {
    svg.append(s("line", { x1: M.v, x2: W - M.h, y1: y(v).toFixed(1), y2: y(v).toFixed(1), stroke: FARG.linje }),
               s("text", { x: M.v - 6, y: (y(v) + 4).toFixed(1), "text-anchor": "end", "font-size": 12, fill: FARG.sten }, Math.round(v * 100) + (v + steg > till + 1e-9 ? " %" : "")));
  }
}
function histArAxel(svg, axelAr, x, yBas) {   // årtalen med två siffror, 06 till 26
  axelAr.forEach((a, i) => svg.append(s("text", { x: x(i).toFixed(1), y: yBas, "text-anchor": "middle", "font-size": 13, fill: FARG.sten }, String(a).slice(2))));
}
function histRitaSerie(svg, pts, { farg, bredd, streck = null, r }) {
  // pts har ett null där året saknar tal: linjen får ett hål och ingen punkt, aldrig ett värde på noll.
  const delar = [[]];
  for (const pt of pts) { if (pt) delar[delar.length - 1].push(pt); else delar.push([]); }
  for (const del of delar.filter(d => d.length)) {
    const fasta = del.filter(pt => !pt.preliminar);
    if (fasta.length > 1) svg.append(s("path", { d: fasta.map((pt, i) => (i ? "L" : "M") + pt.x.toFixed(1) + "," + pt.y.toFixed(1)).join(""), fill: "none", stroke: farg, "stroke-width": bredd, "stroke-dasharray": streck, "stroke-linejoin": "round" }));
    if (del.length > fasta.length && fasta.length) {
      // Preliminärt år: sträckan fram till den öppna ringen. En serie som redan är streckad behåller sin egen
      // streckning, annars skulle rikets linje byta mönster på sista sträckan; det är ringen som bär det preliminära.
      const a = fasta[fasta.length - 1], b = del[del.length - 1];
      svg.append(s("path", { d: `M${a.x.toFixed(1)},${a.y.toFixed(1)}L${b.x.toFixed(1)},${b.y.toFixed(1)}`, fill: "none", stroke: farg, "stroke-width": bredd, "stroke-dasharray": streck || "6 5" }));
    }
    for (const pt of del) svg.append(s("circle", { cx: pt.x.toFixed(1), cy: pt.y.toFixed(1), r, fill: pt.preliminar ? FARG.papper : farg, stroke: farg, "stroke-width": 2 }));
  }
}
function histEtiketter(svg, slut, { H, M }, extra = {}) {
  // Etiketterna får inte täcka varandra: skjut isär till 15 px och rita en kort ledarlinje från den punkt
  // etiketten hör till. Varje etikett står vid sin egen linjes slut, inte i en gemensam kolumn. Bara
  // etiketter vars texter ligger över varandra i sidled skjuts isär: en serie som slutar ett tidigare år
  // står långt till vänster och ska inte tryckas ned av en granne den ändå inte krockar med.
  const bredd = e => 13 + textBredd(e.text, 13, !!extra["font-weight"]);   // ledarlinjens 13 px plus texten
  const krock = (a, b) => a.px < b.px + bredd(b) && b.px < a.px + bredd(a);
  slut.sort((a, b) => a.y - b.y);
  for (let i = 1; i < slut.length; i++)
    for (let j = 0; j < i; j++) if (krock(slut[i], slut[j]) && slut[i].y - slut[j].y < 15) slut[i].y = slut[j].y + 15;
  // Förskjutningen får inte trycka ut en etikett under bilden: den nedersta klamras mot ritytans underkant
  // och de som skjutits isär mot den följer med uppåt. Baslinjen ligger 4,5 px under e.y.
  const golv = H - M.b + 4 - 4.5;
  for (let i = slut.length - 1; i >= 0; i--) {
    if (slut[i].y > golv) slut[i].y = golv;
    for (let j = i + 1; j < slut.length; j++) if (krock(slut[i], slut[j]) && slut[j].y - slut[i].y < 15) slut[i].y = slut[j].y - 15;
  }
  for (const e of slut) {
    if (Math.abs(e.y - e.py) > 1) svg.append(s("line", { x1: (e.px + 4).toFixed(1), y1: e.py.toFixed(1), x2: (e.px + 11).toFixed(1), y2: e.y.toFixed(1), stroke: e.farg, "stroke-width": 1 }));
    // Tunn papperskontur under texten: en etikett som hamnar inne i ritytan ska gå att läsa över en hjälplinje.
    svg.append(s("text", { x: (e.px + 13).toFixed(1), y: (e.y + 4.5).toFixed(1), "font-size": 13, ...extra, fill: textFarg(e.farg),
                           stroke: FARG.papper, "stroke-width": 3, "paint-order": "stroke" }, e.text));
  }
}
function histRing(svg, cx, cy) {   // året får inte ritas än: tom ring på skalans nedersta nivå, texten till vänster om den
  svg.append(s("text", { x: (cx - 10).toFixed(1), y: (cy + 4).toFixed(1), "text-anchor": "end", "font-size": 12, fill: FARG.sten }, "räknas på valnatten"),
             s("circle", { cx: cx.toFixed(1), cy: cy.toFixed(1), r: 5, fill: FARG.papper, stroke: FARG.sten, "stroke-width": 1.5 }));
}
let histLasX = {};   // årtal -> x i bildens viewBox, så att läslinjen kan flyttas utan att bilden ritas om
function histLinjer(val) {
  const el = $("#hist-bild-a"), W = histYta(el), H = arDesktop() ? 320 : 280, M = { v: 40, h: 48, t: 14, b: 30 };
  const punkter = histPunkter(val, "majorna"), axelAr = histAxelAr(), partier = histPartier();
  const max = Math.max(0.4, Math.ceil(Math.max(...punkter.flatMap(p => partier.map(q => p.andel[q] || 0))) * 20) / 20);
  const x = histXSkala(M, W, axelAr), y = a => M.t + (1 - a / max) * (H - M.t - M.b);
  histLasX = Object.fromEntries(axelAr.map((a, i) => [a, x(i)]));
  const utan = axelAr.filter(a => !punkter.some(p => p.ar === a));   // år på axeln som inte får ritas än
  // Talraden under bilden är textalternativet: etiketten säger vad bilden är och hur man byter år, inte
  // seriens alla tal - de lästes annars upp på nytt vid varje piltryck.
  const svg = s("svg", { viewBox: `0 0 ${W} ${H}`, class: "hist-svg", role: "img", tabindex: 0,
    "aria-label": `${histMening(val)} Andel av giltiga röster per valår i procent.`
      + " Talraden under bilden visar ett års tal; vänster och höger pil byter år."
      + (utan.length ? ` ${utan.join(", ")} räknas på valnatten.` : "") });
  histHjalplinjer(svg, { M, W, y, fran: 0.1, till: max, steg: 0.1 });
  histArAxel(svg, axelAr, x, H - 8);
  const slut = [];
  for (const p of partier) {
    const pts = punkter.map((pt, i) => histHarTal(pt, p) ? { x: x(i), y: y(pt.andel[p]), preliminar: pt.preliminar } : null);
    histRitaSerie(svg, pts, { farg: parti(p).farg, bredd: 2.5, r: 3.5 });
    const sista = pts.filter(Boolean).pop();
    // Etiketten står vid partiets egen sista punkt, inte vid bildens kant: så länge linjen slutar 2022 får
    // ingen ledarlinje sträcka sig fram till den tomma ringen och se ut som ett resultat.
    if (sista) slut.push({ text: p, farg: parti(p).farg, px: sista.x, py: sista.y, y: sista.y });
  }
  histEtiketter(svg, slut, { H, M }, { "font-weight": 700 });
  // Läslinjen skapas en gång och ritas före ringen, så att ringen ligger överst. Saknar året plats på axeln
  // hålls linjen dold i stället för att ritas om.
  const li = axelAr.indexOf(state.historikAr);
  svg.append(s("line", { class: "hist-laslinje", x1: li >= 0 ? x(li).toFixed(1) : null, x2: li >= 0 ? x(li).toFixed(1) : null,
                         y1: M.t, y2: y(0) - 8, stroke: FARG.sten, "stroke-dasharray": "3 3", visibility: li >= 0 ? null : "hidden" }));
  for (const a of utan) histRing(svg, x(axelAr.indexOf(a)), y(0));
  const narmast = px => { let best = 0; axelAr.forEach((a, i) => { if (Math.abs(x(i) - px) < Math.abs(x(best) - px)) best = i; }); return axelAr[best]; };
  svg.addEventListener("click", e => { const r = svg.getBoundingClientRect(); sattHistorikAr(narmast((e.clientX - r.left) * W / r.width)); });
  svg.addEventListener("keydown", e => {
    if (e.key !== "ArrowLeft" && e.key !== "ArrowRight") return;
    e.preventDefault();
    const i = Math.max(0, axelAr.indexOf(state.historikAr));
    sattHistorikAr(axelAr[(i + (e.key === "ArrowRight" ? 1 : -1) + axelAr.length) % axelAr.length]);
  });
  el.replaceChildren(svg);
}
function sattHistorikAr(ar) {
  // Bara läslinjen och talraden ändras. Bilden ritas inte om, så fokus ligger kvar av sig självt och
  // skärmläsaren läser talraden (aria-live) i stället för hela bildbeskrivningen på nytt.
  state.historikAr = ar;
  const linje = $("#hist-bild-a .hist-laslinje"), px = histLasX[ar];
  if (linje && px !== undefined) {
    linje.setAttribute("x1", px.toFixed(1)); linje.setAttribute("x2", px.toFixed(1));
    linje.removeAttribute("visibility");
  } else if (linje) linje.setAttribute("visibility", "hidden");
  histTalrad(state.val);
}
function histTalrad(val) {
  const el = $("#hist-talrad"), p = histPunkter(val, "majorna").find(q => q.ar === state.historikAr);
  if (!p) { el.textContent = `${state.historikAr}: räknas på valnatten.`; return; }
  // Ett span per parti, som kortets rad Hur har det ändrats: raden bryts mellan talen i stället för att
  // klippas på en smal skärm. Ett parti utan tal i årets punkt hoppas över, aldrig "0,0".
  const tal = histPartier().filter(q => histHarTal(p, q)).map(q => h("span", { class: "hist-tal" }, `${q} ${andelTal(p.andel[q])}`));
  el.replaceChildren(h("span", { class: "hist-tal" }, `${p.ar}${p.preliminar ? " (preliminärt)" : ""}:`), " ", ...tal.flatMap(n => [n, " "]));
}
function renderHistorik() {
  const sek = $("#historik");
  if (!state.historik || state.bild || !histAr().length || historikSerie(state.val, "majorna").length < 2) { sek.hidden = true; return; }
  sek.hidden = false;
  const val = state.val;
  // Läslinjen faller tillbaka till sista punkten när det valda året saknar punkt i det här valet, inte bara
  // när året saknas på axeln: kommunvalet kan sluta 2022 medan riksdagsvalet redan har en punkt för 2026.
  if (!histPunkter(val, "majorna").some(p => p.ar === state.historikAr)) state.historikAr = sistaPunkt(val).ar;
  $("#hist-mening").textContent = histMening(val);
  histLinjer(val);
  histTalrad(val);
  // Övriga-noten står bara i de val som faktiskt har partier utanför sidans uppsättning: riksdagsvalet (D, FI, K)
  // och regionvalet (K). I kommunvalet ryms alla tolv partierna och meningen skulle inte säga något.
  const meta = state.historik.meta, valetsPartier = (meta.partier_per_val || {})[val] || [];
  const utanfor = (meta.partier || []).filter(p => p !== "Övriga" && !valetsPartier.includes(p));
  $("#hist-not-a").textContent = "Tryck på ett år i bilden för att se det årets tal."
    + " Serien börjar 2006. Valdistrikten ritades om helt inför det valet, så 2002 går inte att räkna om till dagens Majorna."
    + ` Området hålls konstant medan antalet distrikt varierar: ${antalDistriktText(val)}. Liberalerna hette Folkpartiet till och med 2014.`
    + (utanfor.length ? ` Partier utanför valets uppsättning ligger i Övriga: ${histLista(utanfor.map(p => parti(p).namn))}`
        + (val === "rd" ? `; i riksdagsvalet 2014 fick Feministiskt initiativ ${HIST_NOT_FI_2014} procent.` : ".") : "");
  histDeltagande(val);
  histKartor();
}
function histDeltagande(val) {
  // Bild B: valdeltagandet i Majorna mot jämförelseområdena. Höjden är fast 160 px, samma som CSS reserverar,
  // så att bilden inte hoppar när den ritas om, och viewBox är lika bred som ytan.
  // Högermarginalen rymmer den längsta etiketten: Göteborg mäter 54,2 px i Arial 13 och står 13 px till
  // höger om sin punkt, alltså 67,2 px, och punkten kan ligga längst ut på axeln under valnatten.
  const el = $("#hist-bild-b"), W = histYta(el), H = 160, M = { v: 40, h: 70, t: 12, b: 26 };
  const menEl = $("#hist-mening-b"), notEl = $("#hist-not-b");
  // Riket ritas bara på desktop och bara i riksdagsvalet: historikfilens riket i region- och kommunvalet är
  // hela landets region- respektive kommunval, inte Västra Götaland, och är alltså inte Majornas jämförelse.
  const serier = [{ namn: "Majorna", genitiv: "Majornas", niva: "majorna", farg: FARG.gron, bredd: 2.5, streck: null },
                  { namn: "Göteborg", genitiv: "Göteborgs", niva: "goteborg", farg: FARG.sten, bredd: 2, streck: null }];
  if (arDesktop() && val === "rd") serier.push({ namn: "Riket", genitiv: "Rikets", niva: "riket", farg: FARG.sten, bredd: 1.5, streck: "5 4" });
  const deltagande = niva => histPunkter(val, niva).filter(p => p.valdeltagande);
  const majPunkter = deltagande("majorna");
  if (!majPunkter.length) { el.replaceChildren(); menEl.textContent = ""; notEl.textContent = ""; return; }
  // Jämförelseområdena får aldrig sträcka sig längre än Majorna: kommunens aggregat kan vara färdigräknat
  // medan Majornas egna distrikt inte är det, och punkten skulle då jämföras med ingenting.
  const sistaAr = majPunkter[majPunkter.length - 1].ar;
  const linjer = serier.map(sr => ({ ...sr, punkter: (sr.niva === "majorna" ? majPunkter : deltagande(sr.niva)).filter(p => p.ar <= sistaAr) }));
  const alla = linjer.flatMap(sr => sr.punkter.map(p => p.valdeltagande));
  // Skalan är aldrig smalare än 70 till 90 procent, men vidgas i hela femprocentssteg om något år hamnar utanför.
  const lo = Math.min(0.7, Math.floor(Math.min(...alla) * 20) / 20), hi = Math.max(0.9, Math.ceil(Math.max(...alla) * 20) / 20);
  const axelAr = histAxelAr();
  const x = histXSkala(M, W, axelAr), y = v => M.t + (1 - (v - lo) / (hi - lo)) * (H - M.t - M.b);
  const sistaM = [...majPunkter].reverse().find(p => !p.preliminar);   // meningen fryses på senaste slutliga år
  const gbg = linjer.find(sr => sr.niva === "goteborg");   // slås upp på nivån: serieordningen är inte ett löfte
  const sistaG = sistaM && gbg ? gbg.punkter.find(p => p.ar === sistaM.ar) : null;
  const mening = !sistaM ? "" : `Valdeltagande i ${VALNAMN[val].toLowerCase()} ${sistaM.ar}: Majorna ${andelTal(sistaM.valdeltagande)} procent`
    + (sistaG ? `, Göteborg ${andelTal(sistaG.valdeltagande)}.` : ".");
  menEl.textContent = mening;
  // Bilden har ingen talrad: beskrivningen är dess textalternativ och räknar upp serierna år för år.
  const beskrivning = linjer.filter(sr => sr.punkter.length).map(sr => `${sr.namn}: ` + sr.punkter.map(p => `${p.ar} ${andelTal(p.valdeltagande)}`).join(", ")).join("; ");
  const utan = axelAr.filter(a => !majPunkter.some(p => p.ar === a));   // år på axeln som inte får ritas än
  const svg = s("svg", { viewBox: `0 0 ${W} ${H}`, role: "img",
    "aria-label": `${mening} Valdeltagande i procent per valår. ${beskrivning}.`
      + (utan.length ? ` ${utan.join(", ")} räknas på valnatten.` : "") });
  histHjalplinjer(svg, { M, W, y, fran: lo, till: hi, steg: 0.05 });
  histArAxel(svg, axelAr, x, H - 8);
  const slut = [];
  for (const sr of linjer) {
    const pts = axelAr.map((a, i) => { const p = sr.punkter.find(q => q.ar === a); return p ? { x: x(i), y: y(p.valdeltagande), preliminar: p.preliminar } : null; });
    histRitaSerie(svg, pts, { farg: sr.farg, bredd: sr.bredd, streck: sr.streck, r: 3 });
    const sista = pts.filter(Boolean).pop();
    if (sista) slut.push({ text: sr.namn, farg: sr.farg, px: sista.x, py: sista.y, y: sista.y });
  }
  histEtiketter(svg, slut, { H, M });
  for (const a of utan) histRing(svg, x(axelAr.indexOf(a)), y(lo));
  el.replaceChildren(svg);
  // Skalan står i bildtexten eftersom y-axeln inte börjar på noll, och en serie som slutar tidigare än
  // Majorna får en egen mening: annars ser den avkortade linjen ut som ett bortfall.
  const rader = [`Skalan börjar vid ${Math.round(lo * 100)} procent.`
    + " Valdeltagande i olika val ska inte jämföras med varandra, eftersom röstberättigade skiljer sig mellan valen."];
  for (const sr of linjer.slice(1)) {
    const sista = sr.punkter[sr.punkter.length - 1];
    if (sista && sista.ar < sistaAr) rader.push(`${sr.genitiv} linje slutar ${sista.ar} tills aggregatet för ${sistaAr} finns.`);
  }
  notEl.textContent = rader.join(" ");
}
function histKartor() {
  // Kartorna följer kartans årsknapp, till skillnad från bild A och B som står på det senaste laddade året:
  // det är det år läsaren ser i kartan ovanför som ska ställas mot 2006.
  const el = $("#hist-kartor"), notEl = $("#hist-not-kartor"), g06 = state.historikGeo, gNu = geo();
  if (!g06 || !gNu) { el.replaceChildren(); notEl.textContent = ""; return; }
  // Gemensam ram ur båda filernas bbox, annars ser den ena kartan ut att täcka en annan yta än den andra
  // och poängen med bilden går förlorad.
  const bbox = [Math.min(g06.bbox[0], gNu.bbox[0]), Math.min(g06.bbox[1], gNu.bbox[1]),
                Math.max(g06.bbox[2], gNu.bbox[2]), Math.max(g06.bbox[3], gNu.bbox[3])];
  const proj = projektion(bbox, 0.02, 0.02);
  // Bara gränser i sten på papper: ingen partifärg, inga etiketter och inget att trycka på. Bilden svarar på
  // en fråga om distrikten, inte om resultatet, och ytan är aria-hidden så bildtexten är hela innehållet.
  const karta = (fc, ar) => {
    const svg = s("svg", { viewBox: `0 0 ${proj.bredd} ${proj.hojd.toFixed(1)}`, class: "hist-karta" });
    for (const f of fc.features)
      svg.append(s("path", { d: dAttr(f.geometry.coordinates[0], proj, true), fill: "none", stroke: FARG.sten, "stroke-width": 5, "stroke-linejoin": "round" }));
    return h("figure", { class: "hist-figur" }, svg, h("figcaption", {}, `${ar}, ${fc.features.length} distrikt`));
  };
  el.replaceChildren(karta(g06, 2006), karta(gNu, data().meta.ar));
  notEl.textContent = "Samma yta, fler distrikt. Ett kvarter 2006 är ofta två i dag."
    + " Hur olika åldrar röstade går inte att veta. Valhemligheten gäller per distrikt, inte per person.";
}

/* ---- fakta */
function renderFakta() {
  // Listan bär bara det som gäller hela sidan. Ett förbehåll som hör till ett enda diagram står under det
  // diagrammet: valdeltagandet i bild B, antalet distrikt per år i noten under bild A, avsändaren i sidfoten.
  const meta = data().meta;
  const li = [`Avgränsning: ${meta.avgransning}.`,
              `Källa: ${meta.kalla}. ${meta.status === "slutlig" ? "Slutligt resultat." : "Preliminärt resultat."} Andel = partiets röster delat med giltiga röster.`];
  $("#faktalista").replaceChildren(...li.map(t => h("li", {}, t)));
  $("#fot").replaceChildren(h("p", {}, "Så röstade Majorna - en valgrafik från Majposten. Valdata: Valmyndigheten." + (state.bakgrund ? " Kartunderlag © OpenStreetMaps bidragsgivare (ODbL)." : "")));
}

start();
})();
