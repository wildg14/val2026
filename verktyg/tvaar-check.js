const puppeteer = require('puppeteer-core');
const url = process.argv[2] || 'http://localhost:8765/tmp/tvaar/index.html';
(async () => {
  const browser = await puppeteer.launch({ executablePath: '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome', headless: true, args: ['--no-first-run', '--disable-gpu'] });
  const page = await browser.newPage();
  await page.setViewport({ width: 390, height: 844, deviceScaleFactor: 2, isMobile: true, hasTouch: true });
  const fel = []; page.on('pageerror', e => fel.push(String(e)));
  await page.goto(url, { waitUntil: 'networkidle0' });
  await new Promise(r => setTimeout(r, 1500));
  const las = () => page.evaluate(() => {
    const rot = document.getElementById('valgrafik');
    const namn = [...rot.querySelectorAll('#karta path.distrikt')].map(p => p.getAttribute('aria-label').split('.')[0]);
    return { arknappar: [...rot.querySelectorAll('#arval button')].map(b => b.textContent), aktivtAr: (rot.querySelector('#arval button.aktiv') || {}).textContent,
             antalPaths: namn.length, harSandarna: namn.includes('Sandarna'), harSandarne: namn.includes('Sandarne'),
             ariaKarta: rot.querySelector('#karta svg').getAttribute('aria-label'), viewBox: rot.querySelector('#karta svg').getAttribute('viewBox') };
  });
  const y2026 = await las();
  await page.evaluate(() => [...document.getElementById('valgrafik').querySelectorAll('#arval button')].find(b => b.textContent.endsWith('2022')).click());
  await new Promise(r => setTimeout(r, 600));
  const y2022 = await las();
  const ok = y2026.arknappar.length === 2 && y2026.aktivtAr === 'Valet 2026' && y2026.antalPaths === 23 && y2026.harSandarna && !y2026.harSandarne
          && y2022.aktivtAr === 'Valet 2022' && y2022.antalPaths === 23 && y2022.harSandarne && y2026.viewBox === y2022.viewBox && fel.length === 0;
  console.log(JSON.stringify({ y2026, y2022 }, null, 1));
  console.log(fel.length ? 'JS-FEL: ' + fel.join(' | ') : 'inga JS-fel');
  console.log(ok ? 'TVÅÅRSKONTROLL OK' : 'TVÅÅRSKONTROLL MISSLYCKADES');
  await browser.close();
  process.exit(ok ? 0 : 1);
})().catch(e => { console.error(e); process.exit(1); });
