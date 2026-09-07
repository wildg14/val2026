const puppeteer = require('puppeteer-core');
// data/swing_<år>.js är valfri: en 404 för den räknas inte som fel, se tvaar-check.js.
const valfriFil = m => /\/data\/swing_\d+\.js(\?|$)/.test((m.location() || {}).url || '') && m.text().includes('404');
// Namngivna argument: --sida= (standard index.html, läget före valdagen), --prel= (--valnatt, allt räknat,
// preliminärt), --partiell= (--valnatt --partiell 9), --slutlig= (--status slutlig, utan --valnatt).
// Utelämnade sidor hoppas över, --sida har alltid ett värde.
const argv = process.argv.slice(2);
const namngivet = (namn, standard) => {
  const p = argv.find(a => a.startsWith(`--${namn}=`));
  return p ? p.slice(namn.length + 3) : standard;
};
const sidaUrl = namngivet('sida', 'http://localhost:8765/index.html');
const prelUrl = namngivet('prel', null);
const partiellUrl = namngivet('partiell', null);
const slutligUrl = namngivet('slutlig', null);

const PAPPER = '#FAF6EE', STEN = '#6E6152';
// WCAG-kontrasten räknas här i Node på de fill-värden sidan själv skrivit, samma formel som textFarg i valgrafik.js.
function hexTal(hex) { hex = (hex || '').replace('#', ''); return [0, 2, 4].map(i => parseInt(hex.substr(i, 2), 16)); }
function relLum(hex) {
  const c = hexTal(hex).map(v => v / 255).map(v => v <= 0.03928 ? v / 12.92 : Math.pow((v + 0.055) / 1.055, 2.4));
  return 0.2126 * c[0] + 0.7152 * c[1] + 0.0722 * c[2];
}
function kontrast(hex1, hex2) {
  const l1 = relLum(hex1), l2 = relLum(hex2), hi = Math.max(l1, l2), lo = Math.min(l1, l2);
  return (hi + 0.05) / (lo + 0.05);
}
function minAvstandSammaX(etiketter) {
  // Etiketter som delar x-attribut (samma slutår) ska stå minst 14 px isär i y, annars krockar texten.
  const grupper = {};
  for (const e of etiketter) (grupper[e.x] = grupper[e.x] || []).push(e.y);
  let min = Infinity;
  for (const ys of Object.values(grupper)) { ys.sort((a, b) => a - b); for (let i = 1; i < ys.length; i++) min = Math.min(min, ys[i] - ys[i - 1]); }
  return min;
}
const tomRing = c => c.fill === PAPPER && c.stroke === STEN;          // året får inte ritas än, generisk sten-ring
const oppenPartiRing = c => c.fill === PAPPER && c.stroke !== STEN;   // en serie preliminärt sista år, öppen i partifärg

(async () => {
  const browser = await puppeteer.launch({ executablePath: '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome', headless: true, args: ['--no-first-run', '--disable-gpu'] });
  const fel = [], saknade = [], kontroller = [];
  const oppna = async (adress, vp) => {
    const page = await browser.newPage();
    await page.setViewport(vp || { width: 390, height: 900, deviceScaleFactor: 2, isMobile: true, hasTouch: true });
    page.on('pageerror', e => fel.push(String(e)));
    page.on('console', m => { if (m.type() !== 'error') return; if (valfriFil(m)) saknade.push(m.location().url); else fel.push('console: ' + m.text()); });
    await page.goto(adress, { waitUntil: 'networkidle0' });
    await new Promise(r => setTimeout(r, 1500));
    return page;
  };

  // Rådata från sektionen. Håller sig till fält som alltid går att läsa, även när #historik är dold -
  // annars kraschar felläget i stället för att ge en MISSLYCKAD kontroll.
  const universalLas = page => page.evaluate(() => {
    const hist = document.getElementById('historik');
    const bildAEl = document.getElementById('hist-bild-a'), svgA = bildAEl ? bildAEl.querySelector('svg') : null;
    const svgB = document.querySelector('#hist-bild-b svg');
    const talradEl = document.getElementById('hist-talrad');
    const etiketterA = svgA ? [...svgA.querySelectorAll('text[font-weight="700"]')].map(t => ({ text: t.textContent, x: t.getAttribute('x'), y: Number(t.getAttribute('y')), fill: t.getAttribute('fill') })) : [];
    const cirklarA = svgA ? [...svgA.querySelectorAll('circle')].map(c => ({ fill: c.getAttribute('fill'), stroke: c.getAttribute('stroke'), cy: Number(c.getAttribute('cy')) })) : [];
    const kartFigurer = [...document.querySelectorAll('#hist-kartor figure')].map(f => ({ paths: f.querySelectorAll('svg path').length, caption: (f.querySelector('figcaption') || {}).textContent || '' }));
    return {
      synlig: hist ? !hist.hidden : false,
      svgAFinns: !!svgA,
      viewBoxA: svgA ? svgA.getAttribute('viewBox') : null,
      bildAClientWidth: bildAEl ? bildAEl.clientWidth : null,
      etiketterA, cirklarA,
      streckadeA: svgA ? svgA.querySelectorAll('path[stroke-dasharray="6 5"]').length : 0,
      raknasPaValnattenA: svgA ? [...svgA.querySelectorAll('text')].filter(t => t.textContent === 'räknas på valnatten').length : 0,
      // text-anchor="middle" skiljer årtalen på x-axeln från hjälplinjernas tal i vänsterkanten (text-anchor="end"),
      // som annars kan råka bli tvåsiffriga också (till exempel "10", "20").
      xEtiketter: svgA ? [...svgA.querySelectorAll('text[text-anchor="middle"]')].map(t => t.textContent).filter(t => /^\d\d$/.test(t)) : [],
      talradText: (talradEl && talradEl.textContent) || '',
      talradSpannAntal: talradEl ? talradEl.querySelectorAll('span.hist-tal').length : 0,
      svgBFinns: !!svgB,
      viewBoxB: svgB ? svgB.getAttribute('viewBox') : null,
      streckadeB54: svgB ? svgB.querySelectorAll('path[stroke-dasharray="5 4"]').length : 0,
      raknasPaValnattenB: svgB ? [...svgB.querySelectorAll('text')].filter(t => t.textContent === 'räknas på valnatten').length : 0,
      meningB: (document.getElementById('hist-mening-b') || {}).textContent || '',
      notB: (document.getElementById('hist-not-b') || {}).textContent || '',
      kartFigurer,
      faktaLi: document.querySelectorAll('#faktalista li').length,
      mening: (document.getElementById('hist-mening') || {}).textContent || '',
      statusrad: (document.getElementById('statusrad') || {}).textContent || '',
    };
  });

  // Fokus + ArrowLeft (läslinjen och talraden ska ändras, fokus stannar på samma svg-nod) och ett klick
  // vid 2010 års x på axeln (talraden ska byta år). Ingen bild A: allt blir null/false, inga kontroller
  // kraschar på det.
  const interaktion = async page => {
    const finns = await page.evaluate(() => !!document.querySelector('#hist-bild-a svg'));
    if (!finns) return { fore: { talrad: '', x1: null }, efter: { talrad: '', x1: null, sammaNod: false }, talradEfterKlick: null };
    await page.evaluate(() => { document.querySelector('#hist-bild-a svg').__test = true; });
    const fore = await page.evaluate(() => ({
      talrad: document.getElementById('hist-talrad').textContent,
      x1: document.querySelector('#hist-bild-a .hist-laslinje').getAttribute('x1'),
    }));
    await page.evaluate(() => document.querySelector('#hist-bild-a svg').focus());
    await page.keyboard.press('ArrowLeft');
    await new Promise(r => setTimeout(r, 300));
    const efter = await page.evaluate(() => ({
      talrad: document.getElementById('hist-talrad').textContent,
      x1: document.querySelector('#hist-bild-a .hist-laslinje').getAttribute('x1'),
      sammaNod: document.activeElement != null && document.activeElement.__test === true,
    }));
    const klickInfo = await page.evaluate(() => {
      const svg = document.querySelector('#hist-bild-a svg'), rect = svg.getBoundingClientRect();
      const vbW = Number(svg.getAttribute('viewBox').split(' ')[2]);
      const t10 = [...svg.querySelectorAll('text[text-anchor="middle"]')].find(t => t.textContent === '10');
      return t10 ? { left: rect.left, top: rect.top, width: rect.width, height: rect.height, vbW, x: Number(t10.getAttribute('x')) } : null;
    });
    let talradEfterKlick = null;
    if (klickInfo) {
      await page.mouse.click(klickInfo.left + (klickInfo.x / klickInfo.vbW) * klickInfo.width, klickInfo.top + klickInfo.height / 2);
      await new Promise(r => setTimeout(r, 300));
      talradEfterKlick = await page.evaluate(() => document.getElementById('hist-talrad').textContent);
    }
    return { fore, efter, talradEfterKlick };
  };

  // Kontroller som gäller alla fyra sidorna på 390 px.
  const universalKontroller = (namn, u, ix) => {
    const vb = (u.viewBoxA || '0 0 0 0').split(' ').map(Number), vbB = (u.viewBoxB || '0 0 0 0').split(' ').map(Number);
    const partier = u.etiketterA.map(e => e.text), minAv = minAvstandSammaX(u.etiketterA);
    const kontraster = u.etiketterA.map(e => kontrast(e.fill, PAPPER));
    return [
      [`${namn}: #historik synlig`, u.synlig === true],
      [`${namn}: bild A finns, viewBox-bredd = clientWidth`, u.svgAFinns && vb[2] === u.bildAClientWidth],
      [`${namn}: bild A höjd 280`, vb[3] === 280],
      [`${namn}: fyra partietiketter V S MP SD`, partier.length === 4 && ['V', 'S', 'MP', 'SD'].every(p => partier.includes(p))],
      [`${namn}: etiketter på samma x minst 14 px isär`, !isFinite(minAv) || minAv >= 14],
      [`${namn}: etikettfärg kontrast minst 4,5:1`, kontraster.length > 0 && kontraster.every(k => k >= 4.5 - 1e-6)],
      [`${namn}: talraden har minst fem span.hist-tal`, u.talradSpannAntal >= 5],
      [`${namn}: talraden utan 0,0 eller NaN`, !u.talradText.includes('0,0') && !u.talradText.includes('NaN')],
      [`${namn}: x-axelns årtal 06 10 14 18 22 26`, u.xEtiketter.join(' ') === '06 10 14 18 22 26'],
      [`${namn}: piltangent ändrar läslinjen`, ix.fore.x1 !== ix.efter.x1],
      [`${namn}: piltangent ändrar talraden`, ix.fore.talrad !== ix.efter.talrad],
      [`${namn}: fokus stannar på samma svg efter piltangent`, ix.efter.sammaNod === true],
      [`${namn}: klick vid 2010 visar 2010 i talraden`, !!ix.talradEfterKlick && ix.talradEfterKlick.startsWith('2010:')],
      [`${namn}: bild B finns, höjd 160`, u.svgBFinns && vbB[3] === 160],
      [`${namn}: hist-mening-b börjar Valdeltagande i`, u.meningB.startsWith('Valdeltagande i')],
      [`${namn}: hist-not-b börjar Skalan börjar vid`, u.notB.startsWith('Skalan börjar vid')],
      [`${namn}: hist-kartor har 17 och 23 distrikt`, u.kartFigurer.length === 2 && u.kartFigurer.some(f => f.paths === 17) && u.kartFigurer.some(f => f.paths === 23)],
      [`${namn}: figurtexterna slutar på "distrikt"`, u.kartFigurer.length === 2 && u.kartFigurer.every(f => f.caption.endsWith('distrikt'))],
      [`${namn}: Om siffrorna har två punkter`, u.faktaLi === 2],
    ];
  };

  const sidor = {};
  const provaSida = async (namn, url) => {
    if (!url) { console.log(`${namn}: hoppas över (ingen adress angiven)`); return null; }
    const page = await oppna(url);
    const u = await universalLas(page);
    const ix = await interaktion(page);
    console.log(`${namn}:`, JSON.stringify({ u, ix }, null, 1));
    kontroller.push(...universalKontroller(namn, u, ix));
    sidor[namn] = { page, u };
    return sidor[namn];
  };

  await provaSida('sida', sidaUrl);
  await provaSida('prel', prelUrl);
  await provaSida('partiell', partiellUrl);
  await provaSida('slutlig', slutligUrl);

  // b) --sida: läget före valdagen. 2026 är inte laddat än: en generisk tom ring, ingen serie, ingen
  // öppen partiring och inga streckade sträckor. Talraden visar det senaste slutliga året, 2022.
  if (sidor.sida) {
    const { u } = sidor.sida;
    const tomma = u.cirklarA.filter(tomRing), oppna_ = u.cirklarA.filter(oppenPartiRing);
    kontroller.push(
      ['sida: exakt en tom ring i bild A', tomma.length === 1],
      ['sida: tomma ringen står på y(0) = 250', tomma.length === 1 && tomma[0].cy === 250],
      ['sida: "räknas på valnatten" i bild A', u.raknasPaValnattenA === 1],
      ['sida: "räknas på valnatten" i bild B', u.raknasPaValnattenB === 1],
      ['sida: inga streckade sträckor', u.streckadeA === 0],
      ['sida: inga öppna partiringar', oppna_.length === 0],
      ['sida: talraden börjar "2022:"', u.talradText.startsWith('2022:')],
    );

    // --sida läses också i 320 och 1280 px.
    const p320 = await oppna(sidaUrl, { width: 320, height: 900, deviceScaleFactor: 2, isMobile: true, hasTouch: true });
    const r320 = await p320.evaluate(() => {
      const bildAEl = document.getElementById('hist-bild-a'), svgA = bildAEl ? bildAEl.querySelector('svg') : null, talradEl = document.getElementById('hist-talrad');
      if (!svgA) return { viewBoxBredd: null, clientWidth: bildAEl ? bildAEl.clientWidth : null, talradScrollWidth: -1, talradClientWidth: 0 };
      return { viewBoxBredd: Number(svgA.getAttribute('viewBox').split(' ')[2]), clientWidth: bildAEl.clientWidth,
               talradScrollWidth: talradEl.scrollWidth, talradClientWidth: talradEl.clientWidth };
    });
    console.log('sida 320px:', JSON.stringify(r320));
    kontroller.push(
      ['sida 320px: talraden klipps inte', r320.talradScrollWidth <= r320.talradClientWidth],
      ['sida 320px: viewBox-bredd = clientWidth', r320.viewBoxBredd === r320.clientWidth],
    );
    await p320.close();

    const p1280 = await oppna(sidaUrl, { width: 1280, height: 900 });
    const r1280 = await p1280.evaluate(() => {
      const svgA = document.querySelector('#hist-bild-a svg'), svgB = document.querySelector('#hist-bild-b svg');
      if (!svgA) return { etiketter: [], viewBoxA: [0, 0, 0, 0], cirklar: [], streckade54: 0 };
      return {
        etiketter: [...svgA.querySelectorAll('text[font-weight="700"]')].map(t => t.textContent),
        viewBoxA: svgA.getAttribute('viewBox').split(' ').map(Number),
        cirklar: [...svgA.querySelectorAll('circle')].map(c => ({ fill: c.getAttribute('fill'), stroke: c.getAttribute('stroke'), cy: Number(c.getAttribute('cy')) })),
        streckade54: svgB ? svgB.querySelectorAll('path[stroke-dasharray="5 4"]').length : 0,
      };
    });
    console.log('sida 1280px:', JSON.stringify(r1280));
    const tomma1280 = r1280.cirklar.filter(tomRing);
    kontroller.push(
      ['sida 1280px: fem etiketter V S MP SD M', r1280.etiketter.length === 5 && ['V', 'S', 'MP', 'SD', 'M'].every(p => r1280.etiketter.includes(p))],
      ['sida 1280px: viewBox-bredd över 800', r1280.viewBoxA[2] > 800],
      ['sida 1280px: höjd 320', r1280.viewBoxA[3] === 320],
      ['sida 1280px: tomma ringens cy 290', tomma1280.length === 1 && tomma1280[0].cy === 290],
      ['sida 1280px: bild B har rikets streckade linje (5 4)', r1280.streckade54 >= 1],
    );
    await p1280.close();
  }

  // c) --prel: alla 23 distrikt räknade men preliminärt - öppna partiringar och streckade sista sträckor,
  // ingen generisk tom ring. hist-mening fryses på 2022 och rör sig inte när kartans årsknapp byts.
  if (sidor.prel) {
    const { page, u } = sidor.prel;
    const oppnaPrel = u.cirklarA.filter(oppenPartiRing), tommaPrel = u.cirklarA.filter(tomRing);
    kontroller.push(
      ['prel: minst fyra öppna partiringar', oppnaPrel.length >= 4],
      ['prel: minst fyra streckade sträckor "6 5"', u.streckadeA >= 4],
      ['prel: ingen tom sten-ring', tommaPrel.length === 0],
      ['prel: talraden börjar "2026 (preliminärt):"', u.talradText.startsWith('2026 (preliminärt):')],
      ['prel: hist-mening fryst på 2022', u.mening.includes('till 27,2 procent')],
    );
    const foreKlick = (await universalLas(page)).talradText;   // nuläget, inte det som lästes före piltangent/klick i universalKontroller
    await page.evaluate(() => { const b = [...document.querySelectorAll('#arval button')].find(x => x.textContent.endsWith('2022')); if (b) b.click(); });
    await new Promise(r => setTimeout(r, 600));
    const efterKlick = await universalLas(page);
    kontroller.push(
      ['prel: talraden oförändrad efter klick på "Valet 2022"', efterKlick.talradText === foreKlick],
      ['prel: fortfarande inga tomma ringar efter klick på "Valet 2022"', efterKlick.cirklarA.filter(tomRing).length === 0],
    );
  }

  // d) --partiell: 9 av 23 räknade, inget val är helt räknat - en generisk tom ring och ingen preliminär
  // sträcka. ArrowRight tar talraden fram till 2026, som saknar tal helt.
  if (sidor.partiell) {
    const { page, u } = sidor.partiell;
    const tommaPartiell = u.cirklarA.filter(tomRing);
    kontroller.push(
      ['partiell: exakt en tom sten-ring på cy 250', tommaPartiell.length === 1 && tommaPartiell[0].cy === 250],
      ['partiell: inga streckade sträckor', u.streckadeA === 0],
      ['partiell: talraden börjar "2022:"', u.talradText.startsWith('2022:')],
      ['partiell: statusraden innehåller "9 av 23"', u.statusrad.includes('9 av 23')],
    );
    await page.evaluate(() => document.querySelector('#hist-bild-a svg').focus());
    let talrad = await page.evaluate(() => document.getElementById('hist-talrad').textContent), forsok = 0;   // nuläget, inte det universalKontroller redan flyttat med piltangent/klick
    while (!talrad.startsWith('2026') && forsok < 6) {
      await page.keyboard.press('ArrowRight');
      await new Promise(r => setTimeout(r, 250));
      talrad = await page.evaluate(() => document.getElementById('hist-talrad').textContent);
      forsok++;
    }
    console.log('partiell efter ArrowRight:', JSON.stringify({ talrad, forsok }));
    kontroller.push(['partiell: talraden blir exakt "2026: räknas på valnatten."', talrad === '2026: räknas på valnatten.']);
  }

  // e) --slutlig: alla räknade och färdiga, inga öppna eller tomma ringar, ingen streckning. hist-mening
  // räknas på det slutliga 2026, inte fryst på 2022.
  if (sidor.slutlig) {
    const { u } = sidor.slutlig;
    const tommaSlutlig = u.cirklarA.filter(tomRing), oppnaSlutlig = u.cirklarA.filter(oppenPartiRing);
    kontroller.push(
      ['slutlig: inga tomma ringar', tommaSlutlig.length === 0],
      ['slutlig: inga öppna partiringar', oppnaSlutlig.length === 0],
      ['slutlig: inga streckade sträckor', u.streckadeA === 0],
      ['slutlig: talraden börjar "2026:" utan "(preliminärt)"', u.talradText.startsWith('2026:') && !u.talradText.includes('(preliminärt)')],
      ['slutlig: hist-mening räknad på 2026, inte fryst på 2022', !u.mening.includes('till 27,2 procent')],
    );
  }

  kontroller.push(['inga JS-fel', fel.length === 0]);
  if (saknade.length) console.log('valfria filer som saknas:', [...new Set(saknade)].join(' | '));
  console.log(fel.length ? 'JS-FEL: ' + fel.join(' | ') : 'inga JS-fel');
  const fallna = kontroller.filter(k => !k[1]).map(k => k[0]);
  if (fallna.length) console.log('kontroller som föll: ' + fallna.join(', '));
  console.log(fallna.length ? 'HISTORIKKONTROLL MISSLYCKADES' : 'HISTORIKKONTROLL OK');
  await browser.close();
  process.exit(fallna.length ? 1 : 0);
})().catch(e => { console.error(e && e.snallt ? 'FEL: ' + e.message : e); process.exit(1); });
