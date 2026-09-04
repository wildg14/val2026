const puppeteer = require('puppeteer-core');
const [,, url, selector, out, bredd] = process.argv;
(async () => {
  const browser = await puppeteer.launch({ executablePath: '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome', headless: true, args: ['--no-first-run', '--disable-gpu'] });
  const page = await browser.newPage();
  const w = Number(bredd || 390);
  await page.setViewport(w < 600 ? { width: w, height: 844, deviceScaleFactor: 2, isMobile: true, hasTouch: true } : { width: w, height: 900, deviceScaleFactor: 1 });
  const fel = []; page.on('pageerror', e => fel.push(String(e)));
  await page.goto(url, { waitUntil: 'networkidle0' });
  await new Promise(r => setTimeout(r, 1500));
  const el = await page.$(selector);
  if (!el) { console.log('SAKNAS: ' + selector); process.exit(2); }
  await el.screenshot({ path: out });
  console.log(out, fel.length ? 'JS-FEL: ' + fel.join(' | ') : 'inga JS-fel');
  await browser.close();
})().catch(e => { console.error(e); process.exit(1); });
