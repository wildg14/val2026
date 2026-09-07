const puppeteer = require('puppeteer-core');
// data/swing_<år>.js är valfri: saknas den visar sidan ingen förändringsrad för året. Webbläsarens 404 för
// en sådan fil är alltså väntad och räknas inte som JS-fel, men skrivs ut så att en oväntad lucka syns.
const valfriFil = m => /\/data\/swing_\d+\.js(\?|$)/.test((m.location() || {}).url || '') && m.text().includes('404');
(async () => {
  let brutet = false;   // sätts när något av kontrollskriptets fel skrivs ut, avgör returkoden
  const browser = await puppeteer.launch({ executablePath: '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome', headless: true, args: ['--no-first-run', '--disable-gpu'] });
  const page = await browser.newPage();
  await page.setViewport({ width: 390, height: 844, deviceScaleFactor: 2, isMobile: true, hasTouch: true });
  const fel = [], saknade = [];
  page.on('pageerror', e => fel.push(String(e)));
  page.on('console', m => { if (m.type() !== 'error') return; if (valfriFil(m)) saknade.push(m.location().url); else fel.push('console: ' + m.text()); });
  await page.goto('http://localhost:8765/index.html', { waitUntil: 'networkidle0' });
  await new Promise(r => setTimeout(r, 1500));
  const res = await page.evaluate(() => {
    const rot = document.getElementById('valgrafik');
    const paths = [...rot.querySelectorAll('#karta path.distrikt')];
    const ut = { antal: paths.length, rubriker: [], stick: {} };
    for (const p of paths) { p.dispatchEvent(new MouseEvent('click', { bubbles: true })); ut.rubriker.push(rot.querySelector('#panel-rubrik').textContent); }
    const varde = namn => { const r = [...rot.querySelectorAll('#panel-staplar .stapel-rad')].find(x => x.getAttribute('aria-label').startsWith(namn)); return r ? r.querySelector('.stapel-varde').textContent : null; };
    const valj = kod => { const p = rot.querySelector('#karta path[data-kod="' + kod + '"]'); if (rot.querySelector('#panel-rubrik').textContent !== p.getAttribute('aria-label').split('.')[0]) p.dispatchEvent(new MouseEvent('click', { bubbles: true })); };
    rot.querySelector('#flik-rd').click(); valj('14800530'); ut.stick.mariaplan_rd_V = varde('Vänsterpartiet');
    rot.querySelector('#flik-kf').click(); valj('14800527'); ut.stick.skytteskogen_kf_MP = varde('Miljöpartiet');
    rot.querySelector('#flik-rf').click(); valj('14800526'); ut.stick.svalebo_rf_V = varde('Vänsterpartiet');
    ut.statusrad = rot.querySelector('#statusrad').textContent;
    ut.toppsvarRader = rot.querySelectorAll('.toppsvar-rad').length;
    ut.konfig = window.MAJPOSTEN.data.konfig ? 'laddad' : 'saknas';
    ut.mpMain = !!rot.querySelector('.mp-main');
    ut.sektioner = [...rot.querySelectorAll('section h2')].map(h => h.textContent);
    ut.url = location.search;
    return ut;
  });
  console.log(JSON.stringify(res, null, 1));
  // Statusraden börjar med "Slutligt resultat <år>": årtalet ska inte hårdkodas, kontrollen gäller varje år.
  if (res.toppsvarRader === 4 && res.statusrad.startsWith('Slutligt resultat')) console.log('toppsvar ok');
  else { console.log('TOPPSVAR FEL'); brutet = true; }
  // riktigt musklick (inte dispatchEvent) mitt på Kusttorget: gator/hållplatser ligger ovanpå men ska ha pointer-events: none
  const kusttorget = await page.$('#valgrafik #karta path[data-kod="14800536"]');
  await kusttorget.scrollIntoView();
  await new Promise(r => setTimeout(r, 200));
  const box = await kusttorget.boundingBox();
  await page.mouse.click(box.x + box.width / 2, box.y + box.height / 2);
  await new Promise(r => setTimeout(r, 300));
  const kusttorgetRubrik = await page.evaluate(() => document.getElementById('valgrafik').querySelector('#panel-rubrik').textContent);
  if (kusttorgetRubrik === 'Kusttorget') console.log('kusttorgetRubrik:', kusttorgetRubrik, 'ok');
  else { console.log('kusttorgetRubrik:', kusttorgetRubrik, 'FEL: musklick nådde inte distriktet'); brutet = true; }
  if (saknade.length) console.log('valfria filer som saknas:', [...new Set(saknade)].join(' | '));
  if (fel.length) { console.log('FEL: ' + fel.join(' | ')); brutet = true; } else console.log('inga JS-fel');
  for (const fraga of ['bild=karta&val=rd&format=liggande', 'bild=jamforelse&val=rd&format=kvadrat']) {
    const fore = fel.length;
    await page.goto('http://localhost:8765/index.html?' + fraga, { waitUntil: 'networkidle0' });
    await new Promise(r => setTimeout(r, 800));
    const ram = await page.evaluate(() => { const r = document.querySelector('.bildram'); return r ? { w: r.offsetWidth, h: r.offsetHeight, klass: document.getElementById('valgrafik').className } : null; });
    const nya = fel.slice(fore);
    if (nya.length) { console.log('bildläge ' + fraga + ':', JSON.stringify(ram), 'FEL: ' + nya.join(' | ')); brutet = true; }
    else console.log('bildläge ' + fraga + ':', JSON.stringify(ram), 'inga JS-fel');
  }
  await browser.close();
  if (brutet) process.exitCode = 1;
})().catch(e => { console.error(e); process.exit(1); });
