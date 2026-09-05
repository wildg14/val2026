const puppeteer = require('puppeteer-core');
(async () => {
  const browser = await puppeteer.launch({ executablePath: '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome', headless: true, args: ['--no-first-run', '--disable-gpu'] });
  const page = await browser.newPage();
  await page.setViewport({ width: 1280, height: 900 });
  await page.goto('http://localhost:8765/docs/inbaddningstest.html', { waitUntil: 'networkidle0' });
  await new Promise(r => setTimeout(r, 1500));
  const res = await page.evaluate(() => {
    // grafiken har inga länkar i standardläget (samarbete och hjälp är avstängda), så cs() måste tåla att elementet saknas
    const cs = el => { if (!el) return null; const c = getComputedStyle(el); return { color: c.color, font: c.fontFamily.split(',')[0], transform: c.textTransform, deco: c.textDecorationLine + ' ' + c.textDecorationStyle, radius: c.borderRadius, bg: c.backgroundColor }; };
    const rot = document.getElementById('valgrafik');
    return {
      vara: { h2: cs(rot.querySelector('#riksdag-rubrik')), knapp: cs(rot.querySelector('#flikar button')), lank: cs(rot.querySelector('#fot a') || rot.querySelector('a')), fotText: cs(rot.querySelector('#fot p') || rot.querySelector('#fot')), li: cs(rot.querySelector('.legend li')), td: cs(rot.querySelector('table.mandat td')) },
      vard: { h2: cs(document.querySelector('.vard-sektion h2')), knapp: cs(document.querySelector('.vard-sektion > button')), a: cs(document.querySelector('.vard-huvud a')) }
    };
  });
  console.log(JSON.stringify(res, null, 1));
  await browser.close();
})().catch(e => { console.error(e); process.exit(1); });
