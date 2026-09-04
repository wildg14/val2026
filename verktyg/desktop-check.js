const puppeteer = require('puppeteer-core');
const [,, url, out] = process.argv;
(async () => {
  const browser = await puppeteer.launch({ executablePath: '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome', headless: true, args: ['--no-first-run', '--disable-gpu'] });
  const page = await browser.newPage();
  await page.setViewport({ width: 1280, height: 900 });
  const fel = []; page.on('pageerror', e => fel.push(String(e)));
  await page.goto(url, { waitUntil: 'networkidle0' });
  await new Promise(r => setTimeout(r, 1500));
  const before = await page.evaluate(() => {
    const rot = document.getElementById('valgrafik');
    const r = s => { const b = rot.querySelector(s).getBoundingClientRect(); return { x: Math.round(b.left), y: Math.round(b.top + scrollY), w: Math.round(b.width), h: Math.round(b.height) }; };
    return { container: Math.round(rot.getBoundingClientRect().width), karta: r('#karta'), panel: r('#panel'), halvcirkel: r('#halvcirkel'), legend: r('#mandat-legend'), jamforelse: r('#jamforelse'), rostdelning: r('#rostdelning'), sidhojd: document.documentElement.scrollHeight, tillKartan: !!rot.querySelector('.till-kartan') };
  });
  // klicka Mariaplan när kartan är i bild: ingen scroll ska ske, kortet ska uppdateras
  await page.evaluate(() => document.getElementById('valgrafik').querySelector('#karta').scrollIntoView({ block: 'start' }));
  const y0 = await page.evaluate(() => scrollY);
  const p = await page.$('#valgrafik #karta path[data-kod="14800530"]');
  const box = await p.boundingBox();
  await page.mouse.click(box.x + box.width / 2, box.y + box.height / 2);
  await new Promise(r => setTimeout(r, 700));
  const after = await page.evaluate(() => { const rot = document.getElementById('valgrafik'); const pb = rot.querySelector('#panel').getBoundingClientRect(); return { scrollY, rubrik: rot.querySelector('#panel-rubrik').textContent, panelTop: Math.round(pb.top), tillKartanSynlig: getComputedStyle(rot.querySelector('.till-kartan')).display }; });
  // sticky: scrolla 500 px ned, kortet ska ligga kvar på top 16
  await page.evaluate(() => scrollBy(0, 500));
  await new Promise(r => setTimeout(r, 300));
  const sticky = await page.evaluate(() => { const rot = document.getElementById('valgrafik'); return { panelTop: Math.round(rot.querySelector('#panel').getBoundingClientRect().top), kartaTop: Math.round(rot.querySelector('#karta').getBoundingClientRect().top) }; });
  console.log(JSON.stringify({ before, klick: { y0, ...after }, sticky }, null, 1), fel.length ? 'FEL: ' + fel.join(' | ') : 'inga JS-fel');
  await page.evaluate(() => scrollTo(0, 0));
  await page.screenshot({ path: out, fullPage: true });
  await browser.close();
})().catch(e => { console.error(e); process.exit(1); });
