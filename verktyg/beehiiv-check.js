// Verifierar djuplänkar och rullning genom Beehiivs iframe srcdoc (docs/beehiivtest.html).
// Kräver den lokala servern: python3 -m http.server 8765 --bind 127.0.0.1 i projektroten.
const puppeteer = require('puppeteer-core');
const KROM = '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome';
const BAS = 'http://localhost:8765/docs/beehiivtest.html';

async function nyIframeFrame(page) {
  const handle = await page.waitForSelector('#block');
  await page.waitForFunction(() => {
    const el = document.getElementById('block');
    return el && el.contentDocument && el.contentDocument.getElementById('valgrafik') &&
      el.contentDocument.getElementById('valgrafik').querySelector('.mp-main');
  }, { timeout: 15000 });
  return { handle, frame: await handle.contentFrame() };
}

// data/swing_<år>.js är valfri: saknas den visar sidan ingen förändringsrad för året. Webbläsarens 404 för
// en sådan fil är alltså väntad och räknas inte som JS-fel, men skrivs ut så att en oväntad lucka syns.
const valfriFil = m => /\/data\/swing_\d+\.js(\?|$)/.test((m.location() || {}).url || '') && m.text().includes('404');

(async () => {
  const browser = await puppeteer.launch({ executablePath: KROM, headless: true, args: ['--no-first-run', '--disable-gpu'] });
  const ut = {};
  const fel = [], saknade = [];

  // --- Desktop: djuplänk in, klick byter distrikt, förälderns URL uppdateras, tabellen växer iframen ---
  {
    const page = await browser.newPage();
    page.on('pageerror', e => fel.push('desktop: ' + e));
    page.on('console', m => { if (m.type() !== 'error') return; if (valfriFil(m)) saknade.push(m.location().url); else fel.push('desktop console: ' + m.text()); });
    await page.setViewport({ width: 1280, height: 900 });
    await page.goto(BAS + '?distrikt=14800530', { waitUntil: 'networkidle0' });
    const { handle, frame } = await nyIframeFrame(page);
    await new Promise(r => setTimeout(r, 500));

    ut.rubrikVidLast = await frame.evaluate(() => document.getElementById('valgrafik').querySelector('#panel-rubrik').textContent);

    await frame.evaluate(() => {
      document.getElementById('valgrafik').querySelector('#karta path[data-kod="14800527"]').dispatchEvent(new MouseEvent('click', { bubbles: true }));
    });
    await new Promise(r => setTimeout(r, 400));
    ut.rubrikEfterKlick = await frame.evaluate(() => document.getElementById('valgrafik').querySelector('#panel-rubrik').textContent);
    ut.foralderUrlEfterKlick = await page.evaluate(() => location.search);

    const hojdFore = await page.evaluate(() => document.getElementById('block').getBoundingClientRect().height);
    await frame.evaluate(() => document.getElementById('valgrafik').querySelector('#tabell-knapp').click());
    await new Promise(r => setTimeout(r, 500));
    const hojdEfter = await page.evaluate(() => document.getElementById('block').getBoundingClientRect().height);
    ut.iframeVaxte = hojdEfter > hojdFore + 20;
    ut.hojdFore = Math.round(hojdFore); ut.hojdEfter = Math.round(hojdEfter);

    await page.close();
  }

  // --- Mobil: klibbig meny, "Tillbaka till kartan" scrollar föräldern, kartans överkant hamnar under menyn ---
  {
    const page = await browser.newPage();
    page.on('pageerror', e => fel.push('mobil: ' + e));
    page.on('console', m => { if (m.type() !== 'error') return; if (valfriFil(m)) saknade.push(m.location().url); else fel.push('mobil console: ' + m.text()); });
    await page.setViewport({ width: 390, height: 844, deviceScaleFactor: 2, isMobile: true, hasTouch: true });
    await page.goto(BAS + '?distrikt=14800530', { waitUntil: 'networkidle0' });
    const { handle, frame } = await nyIframeFrame(page);
    await new Promise(r => setTimeout(r, 500));

    await page.evaluate(() => window.scrollTo(0, document.body.scrollHeight));
    await new Promise(r => setTimeout(r, 200));
    const tillbaka = await frame.$('.till-kartan');
    if (tillbaka) await tillbaka.click(); else fel.push('mobil: hittar ingen .till-kartan');
    await new Promise(r => setTimeout(r, 700));

    ut.foralderScrollYEfterTillbaka = await page.evaluate(() => scrollY);
    const kartaHandle = await frame.$('#karta');
    const box = kartaHandle ? await kartaHandle.boundingBox() : null;
    ut.kartaTopEfterTillbaka = box ? Math.round(box.y) : null;
    ut.kartaUnderMenyn = box ? box.y >= 89 : false;

    await page.close();
  }

  console.log(JSON.stringify(ut, null, 1));
  if (saknade.length) console.log('valfria filer som saknas:', [...new Set(saknade)].join(' | '));
  console.log(fel.length ? 'FEL: ' + fel.join(' | ') : 'inga JS-fel');
  await browser.close();
  if (fel.length) process.exit(1);
  if (ut.rubrikVidLast !== 'Mariaplan') { console.error('rubrikVidLast fel:', ut.rubrikVidLast); process.exit(1); }
  if (!ut.foralderUrlEfterKlick || ut.foralderUrlEfterKlick.indexOf('distrikt=14800527') === -1) { console.error('förälderns URL uppdaterades inte'); process.exit(1); }
  if (!ut.iframeVaxte) { console.error('iframen växte inte när tabellen fälldes ut'); process.exit(1); }
  if (!ut.kartaUnderMenyn) { console.error('kartans överkant hamnade under 89 px: reservlösningen i A9 behövs'); process.exit(1); }
})().catch(e => { console.error(e); process.exit(1); });
