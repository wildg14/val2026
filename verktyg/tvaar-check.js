const puppeteer = require('puppeteer-core');
// data/swing_<år>.js är valfri: saknas den visar sidan ingen förändringsrad för året. Webbläsarens 404 för
// en sådan fil är alltså väntad och räknas inte som JS-fel, men skrivs ut så att en oväntad lucka syns.
const valfriFil = m => /\/data\/swing_\d+\.js(\?|$)/.test((m.location() || {}).url || '') && m.text().includes('404');
const url = process.argv[2] || 'http://localhost:8765/tmp/tvaar/index.html';
const kfUrl = process.argv[3] || null;   // valfri testsida byggd med --kf-raknade 3, för markörtexten per val
const snallt = text => { const e = new Error(text); e.snallt = true; return e; };
// Statusraden gäller alltid riksdagsvalet, som är färdigräknat i testdatan - även på sidan där kf bara har 3 distrikt.
const STATUS_2026 = 'Preliminärt, 23 av 23 distrikt räknade i riksdagsvalet';

(async () => {
  const browser = await puppeteer.launch({ executablePath: '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome', headless: true, args: ['--no-first-run', '--disable-gpu'] });
  const fel = [], saknade = [];
  const oppna = async adress => {
    const page = await browser.newPage();
    await page.setViewport({ width: 390, height: 844, deviceScaleFactor: 2, isMobile: true, hasTouch: true });
    page.on('pageerror', e => fel.push(String(e)));
    page.on('console', m => { if (m.type() !== 'error') return; if (valfriFil(m)) saknade.push(m.location().url); else fel.push('console: ' + m.text()); });
    await page.goto(adress, { waitUntil: 'networkidle0' });
    await new Promise(r => setTimeout(r, 1500));
    return page;
  };
  const page = await oppna(url);
  const las = async () => {
    const res = await page.evaluate(() => {
      const rot = document.getElementById('valgrafik');
      if (!rot) return { saknas: 'ingen #valgrafik på sidan' };
      const svg = rot.querySelector('#karta svg');
      if (!svg) return { saknas: 'ingen <svg> i #karta', felruta: (rot.querySelector('.fel') || {}).textContent || null };
      const namn = [...rot.querySelectorAll('#karta path.distrikt')].map(p => p.getAttribute('aria-label').split('.')[0]);
      return { arknappar: [...rot.querySelectorAll('#arval button')].map(b => b.textContent), aktivtAr: (rot.querySelector('#arval button.aktiv') || {}).textContent,
               antalPaths: namn.length, harSandarna: namn.includes('Sandarna'), harSandarne: namn.includes('Sandarne'),
               statusrad: rot.querySelector('#statusrad').textContent, toppsvarRader: rot.querySelectorAll('.toppsvar-rad').length,
               ariaKarta: svg.getAttribute('aria-label'), viewBox: svg.getAttribute('viewBox') };
    });
    if (res.saknas) throw snallt(`kartan ritades inte på ${url}: ${res.saknas}.` + (res.felruta ? ` Sidans egen felruta: ${res.felruta}` : '')
      + ' Kontrollera att servern kör i projektroten och att testsidan byggts om med verktyg/forbered_tvaar.py.');
    return res;
  };
  const y2026 = await las();
  await page.evaluate(() => [...document.getElementById('valgrafik').querySelectorAll('#arval button')].find(b => b.textContent.endsWith('2022')).click());
  await new Promise(r => setTimeout(r, 600));
  const y2022 = await las();
  console.log(JSON.stringify({ y2026, y2022 }, null, 1));

  const kontroller = [
    ['två årsknappar', y2026.arknappar.length === 2],
    ['2026 aktivt från början', y2026.aktivtAr === 'Valet 2026'],
    ['23 polygoner 2026', y2026.antalPaths === 23],
    ['Sandarna finns 2026', y2026.harSandarna],
    ['Sandarne saknas 2026', !y2026.harSandarne],
    ['2022 aktivt efter klick', y2022.aktivtAr === 'Valet 2022'],
    ['23 polygoner 2022', y2022.antalPaths === 23],
    ['Sandarne finns 2022', y2022.harSandarne],
    ['samma kartram båda åren', y2026.viewBox === y2022.viewBox],
    ['fyra partier i toppsvaret 2026', y2026.toppsvarRader === 4],
    ['statusraden räknar riksdagsvalet', y2026.statusrad.startsWith(STATUS_2026)]
  ];

  if (kfUrl) {   // markörtexten ska räkna räknade distrikt per val, inte per fil
    const kfSida = await oppna(kfUrl);
    const kf = await kfSida.evaluate(() => {
      const rot = document.getElementById('valgrafik');
      const markor = () => { const el = rot.querySelector('.markorer .majorna'); return el ? el.textContent : null; };
      const valjRaknat = () => {
        const p = [...rot.querySelectorAll('#karta path.distrikt')].find(x => !x.getAttribute('aria-label').includes('inte räknat än'));
        if (!p) return null;
        const namn = p.getAttribute('aria-label').split('.')[0];
        if (rot.querySelector('#panel-rubrik').textContent !== namn) p.dispatchEvent(new MouseEvent('click', { bubbles: true }));
        return namn;
      };
      const ut = {};
      rot.querySelector('#flik-rd').click(); ut.rdDistrikt = valjRaknat(); ut.rdMarkor = markor();
      rot.querySelector('#flik-kf').click(); ut.kfDistrikt = valjRaknat(); ut.kfMarkor = markor();
      ut.statusrad = rot.querySelector('#statusrad').textContent;
      return ut;
    });
    console.log('kf-sidan:', JSON.stringify(kf, null, 1));
    kontroller.push(['markörtext rd: hela Majorna', kf.rdMarkor === 'Snittet för hela Majorna'],
                    ['markörtext kf: räknade distrikt', kf.kfMarkor === 'Snittet för räknade distrikt i Majorna'],
                    ['statusraden gäller riksdagsvalet på kf-sidan', kf.statusrad.startsWith(STATUS_2026)]);
    await kfSida.close();
  } else {
    console.log('kf-sidan: hoppas över (ingen andra URL angiven)');
  }

  kontroller.push(['inga JS-fel', fel.length === 0]);
  if (saknade.length) console.log('valfria filer som saknas:', [...new Set(saknade)].join(' | '));
  console.log(fel.length ? 'JS-FEL: ' + fel.join(' | ') : 'inga JS-fel');
  const fallna = kontroller.filter(k => !k[1]).map(k => k[0]);
  if (fallna.length) console.log('kontroller som föll: ' + fallna.join(', '));
  console.log(fallna.length ? 'TVÅÅRSKONTROLL MISSLYCKADES' : 'TVÅÅRSKONTROLL OK');
  await browser.close();
  process.exit(fallna.length ? 1 : 0);
})().catch(e => { console.error(e && e.snallt ? 'FEL: ' + e.message : e); process.exit(1); });
