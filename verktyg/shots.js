const puppeteer = require('puppeteer-core');
const out = process.argv[2];
const bas = 'http://localhost:8765/';
const shots = [
  { name: '01-mobil-hela-sidan', url: 'index.html', mobile: true, full: true },
  { name: '02-mobil-karta-mariaplan', url: 'index.html?distrikt=14800530', mobile: true, el: '#karta-sektion' },
  { name: '02b-mobil-panel-mariaplan', url: 'index.html?distrikt=14800530', mobile: true, el: '#panel' },
  { name: '03-mobil-partistyrka-sd-kommun', url: 'index.html?lage=styrka&parti=SD&val=kf', mobile: true, el: '#karta-sektion' },
  { name: '03b-mobil-tabell-kommun', url: 'index.html?val=kf', mobile: true, el: '#tabell', tabell: true },
  { name: '04-valnatt-test', url: 'valnatt-test.html?distrikt=14800534', mobile: true, full: true },
  { name: '05-desktop', url: 'index.html', mobile: false, full: true },
];
(async () => {
  const browser = await puppeteer.launch({ executablePath: '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome', headless: true, args: ['--no-first-run', '--disable-gpu'] });
  for (const s of shots) {
    const page = await browser.newPage();
    await page.setViewport(s.mobile ? { width: 390, height: 844, deviceScaleFactor: 2, isMobile: true, hasTouch: true } : { width: 1280, height: 900, deviceScaleFactor: 1 });
    const fel = []; page.on('pageerror', e => fel.push(String(e)));
    await page.goto(bas + s.url, { waitUntil: 'networkidle0' });
    await new Promise(r => setTimeout(r, 1800));
    if (s.tabell) { await page.click('#tabell-knapp'); await new Promise(r => setTimeout(r, 300)); }
    const mått = await page.evaluate(() => { const svg = document.querySelector('#karta svg'); const r = svg.getBoundingClientRect(); return { kartaPx: Math.round(r.height), vh: Math.round(r.height / innerHeight * 100) }; });
    if (s.el) { const el = await page.$(s.el); await el.screenshot({ path: `${out}/${s.name}.png` }); }
    else await page.screenshot({ path: `${out}/${s.name}.png`, fullPage: true });
    console.log(s.name, JSON.stringify(mått), fel.length ? 'JS-FEL: ' + fel.join(' | ') : 'inga JS-fel');
    await page.close();
  }
  await browser.close();
})().catch(e => { console.error(e); process.exit(1); });
