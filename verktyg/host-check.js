const puppeteer = require('puppeteer-core');
const [,, url, out] = process.argv;
(async () => {
  const browser = await puppeteer.launch({ executablePath: '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome', headless: true, args: ['--no-first-run', '--disable-gpu'] });
  const page = await browser.newPage();
  await page.setViewport({ width: 390, height: 844, deviceScaleFactor: 2, isMobile: true, hasTouch: true });
  const fel = []; page.on('pageerror', e => fel.push(String(e))); page.on('requestfailed', r => fel.push('request: ' + r.url()));
  await page.goto(url, { waitUntil: 'networkidle0' });
  await new Promise(r => setTimeout(r, 2000));
  const res = await page.evaluate(() => {
    const rot = document.getElementById('valgrafik');
    const paths = rot.querySelectorAll('#karta path.distrikt');
    paths[4] && paths[4].dispatchEvent(new MouseEvent('click', { bubbles: true }));
    return { distrikt: paths.length, konfig: window.MAJPOSTEN && window.MAJPOSTEN.data.konfig ? window.MAJPOSTEN.data.konfig.adress : 'saknas',
             rubrik: rot.querySelector('#panel-rubrik').textContent, h2: getComputedStyle(rot.querySelector('#riksdag-rubrik')).color,
             skript: [...document.scripts].filter(s => s.src.includes('github.io')).length };
  });
  console.log(url, JSON.stringify(res), fel.length ? 'FEL: ' + fel.join(' | ') : 'inga fel');
  await page.screenshot({ path: out, fullPage: false });
  await browser.close();
})().catch(e => { console.error(e); process.exit(1); });
