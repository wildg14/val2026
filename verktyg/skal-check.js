const puppeteer = require('puppeteer-core');
(async () => {
  const browser = await puppeteer.launch({ executablePath: '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome', headless: true, args: ['--no-first-run', '--disable-gpu'] });
  const page = await browser.newPage();
  await page.setViewport({ width: 390, height: 844, deviceScaleFactor: 2, isMobile: true, hasTouch: true });
  const fel = []; page.on('pageerror', e => fel.push(String(e))); page.on('console', m => { if (m.type() === 'error') fel.push('console: ' + m.text()); });
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
    ut.konfig = window.MAJPOSTEN.data.konfig ? 'laddad' : 'saknas';
    ut.mpMain = !!rot.querySelector('.mp-main');
    ut.sektioner = [...rot.querySelectorAll('section h2')].map(h => h.textContent);
    ut.url = location.search;
    return ut;
  });
  console.log(JSON.stringify(res, null, 1));
  console.log(fel.length ? 'FEL: ' + fel.join(' | ') : 'inga JS-fel');
  await page.goto('http://localhost:8765/index.html?bild=karta&val=rd&format=liggande', { waitUntil: 'networkidle0' });
  await new Promise(r => setTimeout(r, 800));
  const ram = await page.evaluate(() => { const r = document.querySelector('.bildram'); return r ? { w: r.offsetWidth, h: r.offsetHeight, klass: document.getElementById('valgrafik').className } : null; });
  console.log('bildläge:', JSON.stringify(ram));
  await browser.close();
})().catch(e => { console.error(e); process.exit(1); });
