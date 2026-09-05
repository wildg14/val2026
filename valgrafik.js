/* Så röstade Majorna - valgrafik.js
   Renderar hela grafiken inuti <div class="mp-val" id="valgrafik"></div>. Datafiler och konfig läses från
   mappen data/ bredvid den här filen (adressen tas ur skriptets egen src). Inga globala stilar, inga vh-mått:
   filen kan ligga i ett HTML-block i Beehiivs sajtbyggare eller i det tunna skalet index.html.
   Konfig: data/konfig.js (ar, standardAr, valnatt, adress, inbaddad, skrivUrl, stickyTopp). */
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
    <p class="ingress" id="ingress" data-redaktor="justera">Valresultatet för de 23 valdistrikten i klassiska Majorna - riksdag, region och kommun, kvarter för kvarter.</p>
    <div id="arval" class="knappar" role="group" aria-label="Välj valår" hidden></div>
    <div id="valnatt" class="banderoll" hidden></div>
  </header>

  <section id="riksdag" aria-labelledby="riksdag-rubrik">
    <h2 id="riksdag-rubrik">Om Majorna bestämde</h2>
    <p class="not" id="mandat-ingress">Riksdagens 349 mandat fördelade på Majornas riksdagsröster, jämfört med den verkliga riksdagen.</p>
    <div class="knappar" role="radiogroup" aria-label="Välj fördelning" id="mandat-lage"></div>
    <div id="halvcirkel"></div>
    <div id="mandat-legend"></div>
    <p class="not" id="mandat-metod"></p>
  </section>

  <section id="karta-sektion" aria-labelledby="karta-rubrik">
    <h2 id="karta-rubrik">Så röstade ditt kvarter</h2>
    <div class="flikar" role="tablist" aria-label="Välj val" id="flikar"></div>
    <div class="rad">
      <div class="knappar" role="radiogroup" aria-label="Färgläggning" id="lage"></div>
      <label class="partival" id="partival" hidden>Parti <select id="parti" aria-label="Välj parti"></select></label>
    </div>
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
  </section>

  <section id="tabell-sektion" aria-label="Alla distrikt som tabell">
    <button id="tabell-knapp" aria-expanded="false" aria-controls="tabell">Visa alla distrikt som tabell</button>
    <div id="tabell" hidden></div>
  </section>

  <section id="jamforelse" aria-labelledby="jamforelse-rubrik">
    <h2 id="jamforelse-rubrik">Majorna mot Sverige</h2>
    <p class="not" id="jamforelse-not"></p>
    <div class="knappar" role="radiogroup" aria-label="Välj val för jämförelsen" id="jamforelse-val"></div>
    <div id="divergens"></div>
  </section>

  <section id="rostdelning" aria-labelledby="rostdelning-rubrik">
    <h2 id="rostdelning-rubrik">Röstdelningen</h2>
    <p class="not" id="rostdelning-not">Så skiljer sig partiernas andel i Majorna mellan riksdagsvalet och kommunvalet.</p>
    <div id="lutning"></div>
  </section>


  <section id="fakta" aria-labelledby="fakta-rubrik">
    <h2 id="fakta-rubrik">Om siffrorna</h2>
    <ul id="faktalista"></ul>
  </section>

  <footer id="fot"></footer>
`;
/* ===================================================================== KONFIG
   Lägg till "2026" i ar och sätt valnatt: true på valnatten. Datafilerna
   data/valdata_<år>.js (och swing_<år>.js) skrivs av scripts/uppdatera_2026.py. */
const KONFIG = {   // standardvärden, skrivs över av data/konfig.js
  ar: ["2022"], standardAr: "2022", valnatt: false,
  adress: "https://majposten.se/val2026",
  inbaddad: false, skrivUrl: true, stickyTopp: 16   // px från fönstrets överkant för det klibbiga kortet på desktop, höj om Beehiivs sidhuvud är klibbigt
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
const FARG = { papper: "#FAF6EE", black: "#2A241E", sten: "#6E6152", linje: "#E6DECF", ockra: "#C58A34", oraknat: "#DDD5C6" };

const state = { ar: KONFIG.standardAr, val: "rd", lage: "storsta", parti: "V", vald: null,
                mandatLage: "verklig", mandatRort: false, data: {}, swing: {}, geo: null, bakgrund: null,
                sortering: { kol: "namn", fallande: false }, tabellOppen: false, skalmax: 0.5, jamforelseVal: "rd", bild: false };

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
const pe = x => (x > 0 ? "+" : "") + x.toLocaleString("sv-SE", { minimumFractionDigits: 1, maximumFractionDigits: 1 });
const parti = p => PARTIER[p] || { namn: (data().meta.partier || {})[p] || p, farg: "#A79C8E", text: FARG.black };
function mix(hex, t) {   // partifärg mot papper, t = 1 ger partifärgen
  const c = [1, 3, 5].map(i => parseInt(hex.slice(i, i + 2), 16)), p = [250, 246, 238];
  return "#" + c.map((v, i) => Math.round(p[i] + (v - p[i]) * t).toString(16).padStart(2, "0")).join("");
}
function klockslag(iso) { const d = new Date(iso); return isNaN(d) ? iso : d.toLocaleTimeString("sv-SE", { hour: "2-digit", minute: "2-digit" }); }
function namnMedMjukaBindestreck(namn) {   // mjukt bindestreck (U+00AD) i långa partinamn, bara för den synliga texten
  const SHY = "\u00AD";
  return namn.replace(/Vänster/g, "Vänster" + SHY).replace(/Social/g, "Social" + SHY).replace(/Miljö/g, "Miljö" + SHY)
    .replace(/Center/g, "Center" + SHY).replace(/Krist/g, "Krist" + SHY).replace(/Sverige/g, "Sverige" + SHY);
}

/* ===================================================================== data */
const data = () => state.data[state.ar];
const distriktMap = () => Object.fromEntries(data().distrikt.map(d => [d.kod, d]));
const geoMap = () => Object.fromEntries(state.geo.features.map(f => [f.properties.kod, f]));
const raknat = (d, val) => !!(d.raknat && d[val] && Object.keys(d[val]).length && d.giltiga[val]);
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
    el.src = BAS + "data/" + namn + ".js";
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
  state.ar = KONFIG.ar.includes(KONFIG.standardAr) ? KONFIG.standardAr : KONFIG.ar[0];   // state skapades innan konfigen laddades
  try {
    const [geo, ...valdata] = await Promise.all(["distrikt", ...KONFIG.ar.map(a => "valdata_" + a)].map(laddaSkript));
    state.geo = geo;
    KONFIG.ar.forEach((a, i) => { state.data[a] = valdata[i]; });
    if (!state.data[state.ar]) state.ar = KONFIG.ar[0];
    state.bakgrund = await laddaSkript("bakgrund").catch(() => null);
    for (const a of KONFIG.ar) state.swing[a] = a === [...KONFIG.ar].sort()[0] ? null : await laddaSkript("swing_" + a).catch(() => null);   // basåret har ingen swing
  } catch (e) {
    $("header.topp").append(h("p", { class: "fel" }, "Datafilerna kunde inte laddas: " + e.message + ". Kör scripts/bygg_data.py och kontrollera att data/ ligger bredvid valgrafik.js."));
    return;
  }
  raknaSkalmax();
  lasUrl();
  const q0 = new URLSearchParams(location.search);
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
  renderHuvud(); renderRiksdag(); renderKontroller(); renderKarta(); renderPanel(); renderTabell(); renderRostdelning(); renderJamforelse(); renderFakta();
}
function renderHuvud() {
  const meta = data().meta;
  $("#topp-etikett").textContent = "Majposten · Valspecial";
  $("#ingress").textContent = `Valresultatet ${meta.ar} för de 23 valdistrikten i klassiska Majorna - riksdag, region och kommun, kvarter för kvarter.`;
  const arval = $("#arval");
  arval.innerHTML = "";
  arval.hidden = KONFIG.ar.length < 2;
  for (const a of KONFIG.ar) {
    arval.append(h("button", { type: "button", "aria-pressed": String(a === state.ar), class: a === state.ar ? "aktiv" : "",
      onclick: () => { state.ar = a; if (!partierIVal(state.val).includes(state.parti)) state.parti = partierIVal(state.val)[0]; renderAllt(); } }, "Valet " + a));
  }
  renderBanderoll();
}
function renderBanderoll() {   // räknar räknade distrikt för aktuellt val ur distriktsdatan, ritas om vid flikbyte
  const band = $("#valnatt");
  if (!KONFIG.valnatt) { band.hidden = true; return; }
  const meta = data().meta, distrikt = data().distrikt || [];
  let raknade, totalt;
  if (distrikt.length) { raknade = distrikt.filter(d => raknat(d, state.val)).length; totalt = distrikt.length; }
  else if (meta.valnatt) { raknade = meta.valnatt.raknade; totalt = meta.valnatt.totalt; }   // reserv när distriktsdatan saknas
  else { band.hidden = true; return; }
  band.hidden = false;
  band.innerHTML = "";
  band.append(h("b", {}, `Valnatten ${meta.ar}: ${raknade} av ${totalt} distrikt räknade i ${VALNAMN[state.val].toLowerCase()}.`), " ",
    meta.status === "slutlig" ? "Slutliga siffror." : "Preliminära siffror.", ` Uppdaterat ${klockslag(meta.uppdaterad)}.`);
}

/* ---- Om Majorna bestämde */
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
  const sek = $("#riksdag"), m = data().mandat || {};
  const verklig = m.riksdag_verklig && Object.keys(m.riksdag_verklig).length ? m.riksdag_verklig : null;
  const egen = m.riksdag_majorna && Object.keys(m.riksdag_majorna).length ? m.riksdag_majorna : null;
  if (!egen && !verklig) { sek.hidden = true; return; }
  sek.hidden = false;
  const lagen = [];
  if (verklig) lagen.push(["verklig", `Riksdagen ${data().meta.ar}`]);
  if (egen) lagen.push(["majorna", "Om Majorna bestämde"]);
  if (!lagen.some(l => l[0] === state.mandatLage)) state.mandatLage = lagen[0][0];
  const knappar = $("#mandat-lage");
  knappar.innerHTML = "";
  knappar.hidden = lagen.length < 2;
  for (const [lage, text] of lagen) knappar.append(h("button", { type: "button", role: "radio", "aria-checked": String(lage === state.mandatLage),
    onclick: () => { state.mandatRort = true; sattMandatLage(lage); } }, text));
  const fordelning = state.mandatLage === "majorna" ? egen : verklig;
  const antal = Object.values(fordelning).reduce((a, b) => a + b, 0);
  const platser = halvcirkelPlatser(antal), ordning = mandatOrdning(fordelning);
  const svg = s("svg", { viewBox: "-1.08 -1.08 2.16 1.26", role: "img", "aria-label": `${antal} mandat. ` + Object.entries(fordelning).map(([p, n]) => `${p} ${n}`).join(", ") + "." });
  platser.forEach((pl, i) => svg.append(s("circle", { cx: pl.x.toFixed(4), cy: pl.y.toFixed(4), r: 0.026, fill: parti(ordning[i]).farg, style: `--i:${i}`, "data-i": i })));
  svg.append(s("text", { x: 0, y: 0.06, "text-anchor": "middle", "font-size": 0.1, "font-family": "Georgia, serif", "font-weight": 700, fill: FARG.black }, `${antal} mandat`));
  $("#halvcirkel").replaceChildren(svg);
  renderMandatLegend(verklig, egen);
  $("#mandat-metod").textContent = m.metod || "";
  $("#mandat-ingress").hidden = !(verklig && egen);
}
function sattMandatLage(lage) {
  if (state.mandatLage === lage) return;
  state.mandatLage = lage;
  const m = data().mandat, fordelning = lage === "majorna" ? m.riksdag_majorna : m.riksdag_verklig;
  const ordning = mandatOrdning(fordelning);
  $("#halvcirkel").querySelectorAll("circle").forEach((c, i) => c.setAttribute("fill", parti(ordning[i]).farg));
  $("#mandat-lage").querySelectorAll("button").forEach(b => b.setAttribute("aria-checked", String(b.textContent.startsWith("Om") === (lage === "majorna"))));
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
  if (sek.hidden || !("IntersectionObserver" in window)) return;
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
    flikar.append(h("button", { type: "button", role: "tab", "aria-selected": String(val === state.val), id: "flik-" + val,
      onclick: () => { state.val = val; if (!partierIVal(val).includes(state.parti)) state.parti = partierIVal(val)[0]; renderKontroller(); renderKarta(); renderPanel(); renderTabell(); renderBanderoll(); } }, namn));
  }
  const lage = $("#lage");
  lage.innerHTML = "";
  for (const [l, text] of [["storsta", "Största parti"], ["styrka", "Partistyrka"]]) {
    lage.append(h("button", { type: "button", role: "radio", "aria-checked": String(l === state.lage),
      onclick: () => { state.lage = l; renderKontroller(); renderKarta(); renderTabell(); } }, text));
  }
  const valj = $("#parti");
  valj.innerHTML = "";
  for (const p of partierIVal(state.val)) valj.append(h("option", { value: p, selected: p === state.parti }, `${p} - ${parti(p).namn}`));
  valj.onchange = () => { state.parti = valj.value; renderKarta(); renderTabell(); };
  $("#partival").hidden = state.lage !== "styrka";
}

/* ---- kartan */
const HALLPLATSER = {
  mobil: ["Stigbergstorget", "Chapmans Torg", "Jægerdorffsplatsen", "Vagnhallen Majorna", "Mariaplan", "Sannaplan", "Högsbogatan", "Kungssten"],
  desktop: ["Stigbergstorget", "Chapmans Torg", "Jægerdorffsplatsen", "Vagnhallen Majorna", "Mariaplan", "Sannaplan", "Högsbogatan", "Kungssten", "Fjällgatan", "Ekedal", "Marklandsgatan", "Axel Dahlströms torg"]
};
const PLATSNAMN = { mobil: ["Eriksberg", "Slottsberget", "Stigberget", "Högsbohöjd"], desktop: ["Eriksberg", "Slottsberget", "Stigberget", "Högsbohöjd", "Färjenäs"] };
// typstorlekar i viewBox-enheter (1000 bred). Mobil: 1 enhet = 0,39 px. Desktop: 0,69 px.
const STORLEK = { mobil: { etikett: 28, vald: 31, namn: 26, namnRad2: 22, kontur: 6, hallplats: 22, plats: 22 },
                  desktop: { etikett: 24, vald: 27, namn: 24, namnRad2: 20, kontur: 5, hallplats: 18, plats: 21 } };
const arDesktop = () => rot.getBoundingClientRect().width >= 600;
const arBred = () => rot.getBoundingClientRect().width >= 900;   // kortet ligger bredvid kartan   // containerns bredd, inte fönstrets: rätt även inbäddad i en annan sida
let senastDesktop = null;
if ("ResizeObserver" in window) new ResizeObserver(() => {
  const nu = arDesktop();
  if (senastDesktop !== null && nu !== senastDesktop && state.geo && !state.bild) renderKarta();
  senastDesktop = nu;
}).observe(rot);
const storlek = () => arDesktop() ? STORLEK.desktop : STORLEK.mobil;

function projektion(bbox, padX = 0.045, padY = 0.16) {   // högre ram: mer älv och Slottsskog, cirka 60 vh på en telefon
  const [w0, s0, e0, n0] = bbox, dx = (e0 - w0) * padX, dy = (n0 - s0) * padY;
  const W = w0 - dx, E = e0 + dx, S = s0 - dy, N = n0 + dy;
  const kx = Math.cos((S + N) / 2 * Math.PI / 180), bredd = 1000, skala = bredd / ((E - W) * kx);
  return { bredd, hojd: (N - S) * skala, till: ([lon, lat]) => [(lon - W) * kx * skala, (N - lat) * skala], W, E, S, N };
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
  const c = [1, 3, 5].map(i => parseInt(hex.slice(i, i + 2), 16) / 255).map(v => v <= 0.03928 ? v / 12.92 : Math.pow((v + 0.055) / 1.055, 2.4));
  return 0.2126 * c[0] + 0.7152 * c[1] + 0.0722 * c[2];
}
function morkna(hex, t) {   // mot bläck
  const c = [1, 3, 5].map(i => parseInt(hex.slice(i, i + 2), 16)), b = [42, 36, 30];
  return "#" + c.map((v, i) => Math.round(v + (b[i] - v) * t).toString(16).padStart(2, "0")).join("");
}
function styrkaSkala(val, p) {
  const varden = data().distrikt.filter(d => raknat(d, val)).map(d => Math.round((d[val][p] || 0) / d.giltiga[val] * 100));
  const lo = Math.min(...varden), hi = Math.max(...varden), spann = hi - lo;
  const steg = spann >= 8 ? 4 : 3, toner = steg === 4 ? [0.30, 0.55, 0.80, 1] : [0.35, 0.65, 1];
  const granser = Array.from({ length: steg + 1 }, (_, i) => Math.round(lo + spann * i / steg));
  const bas = parti(p).farg, topp = relLuminans(bas) > 0.35 ? morkna(bas, 0.22) : bas;
  const farg = k => k === steg - 1 ? topp : mix(bas, toner[k]);
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
  const val = state.val, dm = distriktMap(), proj = projektion(state.geo.bbox), S = state.bild ? STORLEK.mobil : storlek(), desktop = arDesktop() && !state.bild;
  const skala = state.lage === "styrka" ? styrkaSkala(val, state.parti) : null;
  const svg = s("svg", { viewBox: `0 0 ${proj.bredd} ${proj.hojd.toFixed(1)}`, role: "group", "aria-label": `Karta över Majornas 23 valdistrikt, ${VALNAMN[val].toLowerCase()} ${state.ar}` });
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
  for (const f of state.geo.features) {
    const d = dm[f.properties.kod], ringSvg = f.geometry.coordinates[0].map(proj.till);
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
  for (const f of state.geo.features) {
    const d = dm[f.properties.kod], [lx, ly] = proj.till(f.properties.etikett), sp = spannVid(ringar[d.kod], ly, lx);
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
  } else {
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
function renderPanel() {
  const val = state.val, dm = distriktMap(), d = state.vald ? dm[state.vald] : null, m = majorna(val);
  const rubrik = $("#panel-rubrik"), tillbaka = $("#panel-tillbaka"), hint = $("#panel-hint"),
        sub = $("#panel-sub"), not = $("#panel-not"), staplar = $("#panel-staplar"), knappar = $("#panel-knappar");
  not.innerHTML = ""; staplar.innerHTML = ""; knappar.innerHTML = "";
  tillbaka.hidden = !d; hint.hidden = !!d;
  tillbaka.onclick = () => valjDistrikt(state.vald);
  let toppText = "", subText = "";
  const markorNot = [], swingNot = sw => sw ? [h("span", { style: "padding-left:0" }, `Små tal: förändring mot ${state.swing[state.ar].bas} i procentenheter.`)] : [];
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
    if (markorer.length) markorNot.push(h("span", { class: "majorna" }, KONFIG.valnatt && data().meta.valnatt && data().meta.valnatt.raknade < data().meta.valnatt.totalt ? "Snittet för räknade distrikt i Majorna" : "Snittet för hela Majorna"));
    markorNot.push(...swingNot(swing));
    for (const a of andelar(d[val], d.giltiga[val])) if (a.andel >= 0.01)
      staplar.append(stapelRad(a.p, a.andel, markorer.map(x => ({ ...x, andel: m.giltiga ? (m.roster[a.p] || 0) / m.giltiga : undefined })), swing ? swing[a.p] : null));
    knappar.append(h("button", { type: "button", class: "till-kartan", onclick: () => $("#karta").scrollIntoView({ block: "start", behavior: lugn() ? "auto" : "smooth" }) }, "Tillbaka till kartan"));
  } else {
    rubrik.textContent = "Hela Majorna";
    if (!majornaRaknat(val)) {
      toppText = `${VALNAMN[val]} ${state.ar}: inget distrikt räknat än.`;
    } else {
      const vn = data().meta.valnatt, omr = jamforelseOmrade(val), post = omr.post, swing = swingFor(null, val);
      toppText = `${VALNAMN[val]} ${state.ar}: ${toppTre(m.roster, m.giltiga)}.`;
      let vd = "";
      if (m.rostberattigade) {
        const namnLabel = val === "rd" ? "riket" : omr.namn;
        vd = `Valdeltagande ${procent(m.rostande / m.rostberattigade)}` + (post && post.valdeltagande ? ` (${namnLabel} ${procent(post.valdeltagande)})` : "");
      }
      subText = (KONFIG.valnatt && vn && vn.raknade < vn.totalt ? `${vn.raknade} av ${vn.totalt} distrikt räknade. ` : "") + (vd ? vd + ". " : "") + `${tal(m.giltiga)} giltiga röster.`;
      const markorer = [];
      if (post && post.andel) { markorer.push({ klass: "", namn: omr.namn, andelar: post.andel }); markorNot.push(h("span", {}, `Snittet i ${omr.namn}`)); }
      markorNot.push(...swingNot(swing));
      for (const a of andelar(m.roster, m.giltiga)) if (a.andel >= 0.01)
        staplar.append(stapelRad(a.p, a.andel, markorer.map(x => ({ ...x, andel: x.andelar[a.p] })), swing ? swing[a.p] : null));
    }
  }
  sub.textContent = subText; sub.hidden = !subText;
  if (markorNot.length) not.append(h("div", { class: "markorer", "aria-hidden": "true" }, markorNot));
  $("#panel-live").textContent = `${rubrik.textContent}. ${toppText}`;
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
  const th = (kolNamn, text) => h("th", { scope: "col", "aria-sort": kol === kolNamn ? (fallande ? "descending" : "ascending") : "none",
    onclick: () => { state.sortering = { kol: kolNamn, fallande: kol === kolNamn ? !fallande : kolNamn !== "namn" }; renderTabell(); } }, text);
  const tabell = h("table", { class: "distrikt" },
    h("caption", {}, `${VALNAMN[val]} ${state.ar}, andel av giltiga röster per distrikt. Tryck på en kolumn för att sortera, på en rad för att välja distrikt.`),
    h("thead", {}, h("tr", {}, th("namn", "Distrikt"), partier.map(p => th(p, p)), th("vd", "Valdelt."))),
    h("tbody", {}, rader.map(r => h("tr", { class: r.kod === state.vald ? "vald" : "", onclick: () => valjDistrikt(r.kod) },
      h("td", {}, r.namn), partier.map(p => h("td", {}, r.raknat ? procent(r[p]) : "-")), h("td", {}, r.vd !== null && r.raknat ? procent(r.vd) : "-")))));
  wrap.replaceChildren(h("div", { class: "tabell-wrap" }, tabell));
}

/* ---- röstdelningen */
function renderRostdelning() {
  const sek = $("#rostdelning"), rd = majorna("rd"), kf = majorna("kf");
  if (!(rd && rd.giltiga && kf && kf.giltiga)) { sek.hidden = true; return; }
  sek.hidden = false;
  const partier = Object.keys(kf.roster).filter(p => p !== "Övriga" && rd.roster[p] !== undefined);
  const serier = partier.map(p => ({ p, a: rd.roster[p] / rd.giltiga, b: kf.roster[p] / kf.giltiga }));
  const fokus = ["V", "S", "MP"];
  const W = 600, H = 360, x1 = 190, x2 = 410, topp = 40, botten = 320;
  const max = Math.max(0.1, Math.ceil(Math.max(...serier.flatMap(q => [q.a, q.b])) * 10) / 10);
  const y = v => botten - (v / max) * (botten - topp);
  const svg = s("svg", { viewBox: `0 0 ${W} ${H}`, role: "img", "aria-label": "Röstdelning: " + serier.filter(q => fokus.includes(q.p)).map(q => `${q.p} ${procent(q.a)} i riksdagsvalet, ${procent(q.b)} i kommunvalet`).join("; ") });
  svg.append(s("text", { x: x1, y: 24, "text-anchor": "middle", "font-size": 15, "font-weight": 700, fill: FARG.black }, "Riksdag"),
             s("text", { x: x2, y: 24, "text-anchor": "middle", "font-size": 15, "font-weight": 700, fill: FARG.black }, "Kommun"),
             s("line", { x1, x2: x1, y1: topp, y2: botten, stroke: FARG.linje }), s("line", { x1: x2, x2, y1: topp, y2: botten, stroke: FARG.linje }));
  for (const q of serier.filter(q => !fokus.includes(q.p)))
    svg.append(s("line", { x1, y1: y(q.a), x2, y2: y(q.b), stroke: FARG.sten, "stroke-opacity": .35, "stroke-width": 2 }));
  const dodge = (poster, nyckel) => { poster.sort((a, b) => a[nyckel] - b[nyckel]); for (let i = 1; i < poster.length; i++) if (poster[i][nyckel] - poster[i - 1][nyckel] < 18) poster[i][nyckel] = poster[i - 1][nyckel] + 18; return poster; };
  const fokusSerier = serier.filter(q => fokus.includes(q.p)).map(q => ({ ...q, ya: y(q.a), yb: y(q.b), la: y(q.a), lb: y(q.b) }));
  dodge(fokusSerier, "la"); dodge(fokusSerier, "lb");
  for (const q of fokusSerier) {
    svg.append(s("line", { x1, y1: q.ya, x2, y2: q.yb, stroke: parti(q.p).farg, "stroke-width": 6, "stroke-linecap": "round" }),
      s("circle", { cx: x1, cy: q.ya, r: 6, fill: parti(q.p).farg }), s("circle", { cx: x2, cy: q.yb, r: 6, fill: parti(q.p).farg }),
      s("text", { x: x1 - 14, y: q.la + 5, "text-anchor": "end", "font-size": 15, fill: FARG.black }, `${q.p} ${procent(q.a)}`),
      s("text", { x: x2 + 14, y: q.lb + 5, "font-size": 15, fill: FARG.black }, `${procent(q.b)} ${q.p}`));
  }
  $("#lutning").replaceChildren(svg);
  $("#rostdelning-not").textContent = `Så skiljer sig partiernas andel i Majorna mellan riksdagsvalet och kommunvalet ${state.ar}. Grå linjer är övriga partier.`;
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
    knappar.append(h("button", { type: "button", role: "radio", "aria-checked": String(v === val), onclick: () => { state.jamforelseVal = v; renderJamforelse(); } }, (data().meta.val || VALNAMN)[v]));
  }
  if (!res) { sek.hidden = true; return; }
  sek.hidden = false;
  $("#jamforelse-rubrik").textContent = `Majorna mot ${res.omr.namn}`;
  $("#jamforelse-not").textContent = `${VALNAMN[val]} ${state.ar} - skillnad i procentenheter mellan Majorna och ${res.omr.namn}. Noll är ${res.omr.genitiv} nivå.`;
  $("#divergens").replaceChildren(res.el);
}
/* ---- bildläge för nyhetsbrev och sociala medier: ?bild=jamforelse&val=rd&format=liggande|kvadrat&etikett=... */
function renderBild(typ) {
  const q = new URLSearchParams(location.search), format = q.get("format") === "kvadrat" ? "kvadrat" : "liggande";
  const val = VALNAMN[q.get("val")] ? q.get("val") : "rd";
  rot.classList.add("bild");
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
    state.bild = true; state.vald = null;
    if (!VALNAMN[state.val]) state.val = "rd";
    if (!partierIVal(state.val).includes(state.parti)) state.parti = partierIVal(state.val)[0];
    ram.classList.add("karta-bild");
    const under = state.lage === "styrka"
      ? `${parti(state.parti).namn}s andel i ${VALNAMN[state.val].toLowerCase()} ${state.ar}, 23 valdistrikt`
      : `Största parti i ${VALNAMN[state.val].toLowerCase()} ${state.ar}, 23 valdistrikt`;
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

/* ---- fakta */
function renderFakta() {
  const meta = data().meta, rd = majorna("rd"), riket = jamforelse("riket", "rd"), gbg = jamforelse("goteborg", "rd");
  const li = [];
  if (rd && rd.rostberattigade) {
    let t = `Valdeltagande i Majorna: ${procent(rd.rostande / rd.rostberattigade)} i riksdagsvalet`;
    const jmf = [];
    if (gbg && gbg.valdeltagande) jmf.push(`Göteborg ${procent(gbg.valdeltagande)}`);
    if (riket && riket.valdeltagande) jmf.push(`riket ${procent(riket.valdeltagande)}`);
    li.push(t + (jmf.length ? ` (${jmf.join(", ")})` : "") + ".");
    li.push(`${tal(rd.giltiga)} giltiga riksdagsröster från ${tal(rd.rostberattigade)} röstberättigade.`);
  }
  li.push(`Avgränsning: ${meta.avgransning}.`);
  li.push(`Källa: ${meta.kalla}. ${meta.status === "slutlig" ? "Slutligt resultat." : "Preliminärt resultat."} Andel = partiets röster delat med giltiga röster.`);
  li.push("Byggd av Majposten.");
  $("#faktalista").replaceChildren(...li.map(t => h("li", {}, t)));
  $("#fot").replaceChildren(h("p", {}, "Så röstade Majorna - en valgrafik från Majposten. Valdata: Valmyndigheten." + (state.bakgrund ? " Kartunderlag © OpenStreetMaps bidragsgivare (ODbL)." : "")));
}

start();
})();
