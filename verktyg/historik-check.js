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
const snallt = text => { const e = new Error(text); e.snallt = true; return e; };
// WCAG-kontrasten räknas här i Node på de faktiskt renderade färgerna (getComputedStyle(t).fill, "rgb(r, g, b)"),
// inte på fill-attributet, samma formel som textFarg i valgrafik.js.
function hexTal(hex) { hex = (hex || '').replace('#', ''); return [0, 2, 4].map(i => parseInt(hex.substr(i, 2), 16)); }
function rgbTal(farg) {
  const m = /^rgba?\(\s*([\d.]+)[,\s]+([\d.]+)[,\s]+([\d.]+)/.exec((farg || '').trim());
  return m ? [Number(m[1]), Number(m[2]), Number(m[3])] : hexTal(farg);
}
function relLum(farg) {
  const c = rgbTal(farg).map(v => v / 255).map(v => v <= 0.03928 ? v / 12.92 : Math.pow((v + 0.055) / 1.055, 2.4));
  return 0.2126 * c[0] + 0.7152 * c[1] + 0.0722 * c[2];
}
function kontrast(farg1, farg2) {
  const l1 = relLum(farg1), l2 = relLum(farg2), hi = Math.max(l1, l2), lo = Math.min(l1, l2);
  return (hi + 0.05) / (lo + 0.05);
}
// Ringarna i bild B skiljs på radien: det år som inte får ritas än är en sten-ring med r 5 på skalans
// nedersta nivå, en serie med preliminärt sista år får en öppen punkt med seriens egen färg och r 3.
const tomRing = c => c.fill === PAPPER && c.stroke === STEN && c.r === 5;
const oppenPunkt = c => c.fill === PAPPER && c.r === 3;

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
    const harValgrafik = await page.evaluate(() => !!document.getElementById('valgrafik'));
    if (!harValgrafik) throw snallt(`sidan saknar #valgrafik på ${adress}. Kontrollera adressen och att den lokala servern kör.`);
    return page;
  };

  // Rådata från sektionen. Håller sig till fält som alltid går att läsa, även när #historik är dold -
  // annars kraschar felläget i stället för att ge en MISSLYCKAD kontroll.
  const universalLas = page => page.evaluate(() => {
    const hist = document.getElementById('historik');
    const bildBEl = document.getElementById('hist-bild-b'), svgB = bildBEl ? bildBEl.querySelector('svg') : null;
    const kartFigurer = [...document.querySelectorAll('#hist-kartor figure')].map(f => ({ paths: f.querySelectorAll('svg path').length, caption: (f.querySelector('figcaption') || {}).textContent || '' }));
    return {
      synlig: hist ? !hist.hidden : false,
      // Bild A och dess talrad är borttagna: de får inte komma tillbaka av misstag.
      bildAFinns: !!document.getElementById('hist-bild-a'),
      talradFinns: !!document.getElementById('hist-talrad'),
      notAFinns: !!document.getElementById('hist-not-a'),
      meningBFinns: !!document.getElementById('hist-mening-b'),
      svgBFinns: !!svgB,
      viewBoxB: svgB ? svgB.getAttribute('viewBox') : null,
      bildBClientWidth: bildBEl ? bildBEl.clientWidth : null,
      // Etiketterna vid linjernas slut: papperskonturen skiljer dem från hjälplinjernas tal och årtalen.
      etiketterB: svgB ? [...svgB.querySelectorAll('text[paint-order="stroke"]')].map(t => ({ text: t.textContent, fill: getComputedStyle(t).fill })) : [],
      cirklarB: svgB ? [...svgB.querySelectorAll('circle')].map(c => ({ fill: c.getAttribute('fill'), stroke: c.getAttribute('stroke'), cy: Number(c.getAttribute('cy')), r: Number(c.getAttribute('r')) })) : [],
      streckadeB54: svgB ? svgB.querySelectorAll('path[stroke-dasharray="5 4"]').length : 0,
      streckadeB65: svgB ? svgB.querySelectorAll('path[stroke-dasharray="6 5"]').length : 0,
      // Året utan punkt: "räknas på valnatten" före valdagen, "räknas just nu" när KONFIG.valnatt är sant.
      ringTextB: svgB ? [...svgB.querySelectorAll('text')].map(t => t.textContent).filter(t => /^räknas (på valnatten|just nu)$/.test(t)) : [],
      ariaB: svgB ? svgB.getAttribute('aria-label') : null,
      notB: (document.getElementById('hist-not-b') || {}).textContent || '',
      kartFigurer,
      faktaLi: document.querySelectorAll('#faktalista li').length,
      mening: (document.getElementById('hist-mening') || {}).textContent || '',
      statusrad: (document.getElementById('statusrad') || {}).textContent || '',
    };
  });

  // Kontroller som gäller alla fyra sidorna på 390 px.
  const universalKontroller = (namn, u) => {
    const vbB = (u.viewBoxB || '0 0 0 0').split(' ').map(Number);
    const namnen = u.etiketterB.map(e => e.text), kontraster = u.etiketterB.map(e => kontrast(e.fill, PAPPER));
    return [
      [`${namn}: #historik synlig`, u.synlig === true],
      [`${namn}: ingen bild A`, u.bildAFinns === false],
      [`${namn}: ingen talrad`, u.talradFinns === false],
      [`${namn}: ingen not under bild A`, u.notAFinns === false],
      [`${namn}: ingen egen mening över bild B`, u.meningBFinns === false],
      [`${namn}: bild B finns, höjd 160`, u.svgBFinns && vbB[3] === 160],
      [`${namn}: bild B viewBox-bredd = clientWidth`, u.svgBFinns && vbB[2] === u.bildBClientWidth],
      [`${namn}: bild B har etiketterna Majorna och Göteborg`, namnen.includes('Majorna') && namnen.includes('Göteborg')],
      [`${namn}: etikettfärg kontrast minst 4,5:1`, kontraster.length > 0 && kontraster.every(k => k >= 4.5 - 1e-6)],
      [`${namn}: hist-not-b börjar Skalan börjar vid`, u.notB.startsWith('Skalan börjar vid')],
      [`${namn}: hist-not-b utan jämförelseförbehållet`, !u.notB.includes('ska inte jämföras med varandra')],
      [`${namn}: sektionens mening finns`, /procent i \w+valet sedan \d{4}\.$/.test(u.mening.trim())],
      [`${namn}: första kartfiguren är 2006 med 17 distrikt`, u.kartFigurer.length === 2 && u.kartFigurer[0].paths === 17 && u.kartFigurer[0].caption.startsWith('2006, ')],
      [`${namn}: andra kartfiguren har 23 distrikt och ett fyrsiffrigt år`, u.kartFigurer.length === 2 && u.kartFigurer[1].paths === 23 && /^\d{4}, 23 distrikt/.test(u.kartFigurer[1].caption)],
      [`${namn}: Om siffrorna har två punkter`, u.faktaLi === 2],
    ];
  };

  const sidor = {};
  const provaSida = async (namn, url) => {
    if (!url) { console.log(`${namn}: hoppas över (ingen adress angiven)`); return null; }
    const page = await oppna(url);
    const u = await universalLas(page);
    console.log(`${namn}:`, JSON.stringify(u, null, 1));
    kontroller.push(...universalKontroller(namn, u));
    sidor[namn] = { page, u };
    return sidor[namn];
  };

  await provaSida('sida', sidaUrl);
  await provaSida('prel', prelUrl);
  await provaSida('partiell', partiellUrl);
  await provaSida('slutlig', slutligUrl);

  // b) --sida: läget före valdagen. 2026 är inte laddat än: en generisk tom ring, ingen öppen punkt och
  // inga preliminära sträckor.
  if (sidor.sida) {
    const { u } = sidor.sida;
    const tomma = u.cirklarB.filter(tomRing), oppnaRingar = u.cirklarB.filter(oppenPunkt);
    kontroller.push(
      ['sida: exakt en tom ring i bild B', tomma.length === 1],
      ['sida: "räknas på valnatten" i bild B', u.ringTextB.join() === 'räknas på valnatten'],
      ['sida: inga preliminära sträckor', u.streckadeB65 === 0],
      ['sida: inga öppna punkter', oppnaRingar.length === 0],
    );

    // --sida läses också i 320 och 1280 px: viewBox ska följa ytans bredd i båda ändarna, och rikets
    // streckade linje ritas bara på desktop.
    const p320 = await oppna(sidaUrl, { width: 320, height: 900, deviceScaleFactor: 2, isMobile: true, hasTouch: true });
    const r320 = await p320.evaluate(() => {
      const el = document.getElementById('hist-bild-b'), svg = el ? el.querySelector('svg') : null;
      if (!svg) return { viewBox: null, clientWidth: el ? el.clientWidth : null };
      return { viewBox: svg.getAttribute('viewBox').split(' ').map(Number), clientWidth: el.clientWidth };
    });
    console.log('sida 320px:', JSON.stringify(r320));
    kontroller.push(
      ['sida 320px: bild B viewBox-bredd finns och = clientWidth', !!r320.viewBox && r320.viewBox[2] === r320.clientWidth],
      ['sida 320px: bild B höjd 160', !!r320.viewBox && r320.viewBox[3] === 160],
    );
    await p320.close();

    const p1280 = await oppna(sidaUrl, { width: 1280, height: 900 });
    const r1280 = await p1280.evaluate(() => {
      const el = document.getElementById('hist-bild-b'), svg = el ? el.querySelector('svg') : null;
      if (!svg) return { viewBox: null, streckade54: 0, etiketter: [] };
      return { viewBox: svg.getAttribute('viewBox').split(' ').map(Number),
               streckade54: svg.querySelectorAll('path[stroke-dasharray="5 4"]').length,
               etiketter: [...svg.querySelectorAll('text[paint-order="stroke"]')].map(t => t.textContent) };
    });
    console.log('sida 1280px:', JSON.stringify(r1280));
    kontroller.push(
      ['sida 1280px: bild B viewBox-bredd över 300', !!r1280.viewBox && r1280.viewBox[2] > 300],
      ['sida 1280px: bild B höjd 160', !!r1280.viewBox && r1280.viewBox[3] === 160],
      ['sida 1280px: bild B har rikets streckade linje (5 4)', r1280.streckade54 >= 1],
      ['sida 1280px: bild B har etiketten Riket', r1280.etiketter.includes('Riket')],
    );
    await p1280.close();
  }

  // c) --prel: alla 23 distrikt räknade men preliminärt - öppna punkter och streckade sista sträckor,
  // ingen generisk tom ring.
  if (sidor.prel) {
    const { u } = sidor.prel;
    kontroller.push(
      ['prel: minst en öppen punkt i bild B', u.cirklarB.filter(oppenPunkt).length >= 1],
      ['prel: minst en preliminär sträcka "6 5"', u.streckadeB65 >= 1],
      ['prel: ingen tom sten-ring', u.cirklarB.filter(tomRing).length === 0],
      ['prel: hist-mening fryst på 2022', u.mening.includes('till 27,2 procent')],
      ['prel: bild B:s aria-label märker 2026 som preliminärt', (u.ariaB || '').includes('2026 (preliminärt)')],
    );
  }

  // d) --partiell: 9 av 23 räknade, inget val är helt räknat - en generisk tom ring och ingen preliminär sträcka.
  if (sidor.partiell) {
    const { u } = sidor.partiell;
    kontroller.push(
      ['partiell: exakt en tom sten-ring i bild B', u.cirklarB.filter(tomRing).length === 1],
      ['partiell: inga preliminära sträckor', u.streckadeB65 === 0],
      ['partiell: statusraden innehåller "9 av 23"', u.statusrad.includes('9 av 23')],
      ['partiell: "räknas just nu" i bild B', u.ringTextB.join() === 'räknas just nu'],
      ['partiell: bild B:s aria-label slutar "2026 räknas just nu."', (u.ariaB || '').endsWith('2026 räknas just nu.')],
    );
  }

  // e) --slutlig: alla räknade och färdiga, inga öppna eller tomma ringar, ingen preliminär streckning.
  // hist-mening räknas på det slutliga 2026, inte fryst på 2022.
  if (sidor.slutlig) {
    const { u } = sidor.slutlig;
    kontroller.push(
      ['slutlig: inga tomma ringar', u.cirklarB.filter(tomRing).length === 0],
      ['slutlig: inga öppna punkter', u.cirklarB.filter(oppenPunkt).length === 0],
      ['slutlig: inga preliminära sträckor', u.streckadeB65 === 0],
      ['slutlig: hist-mening räknad på 2026, inte fryst på 2022', !u.mening.includes('till 27,2 procent')],
      ['slutlig: bild B:s aria-label utan preliminärmarkering', !(u.ariaB || '').includes('(preliminärt)')],
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
