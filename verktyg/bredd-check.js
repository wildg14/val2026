const puppeteer = require('puppeteer-core');
/* Breddkontroll: sidan får aldrig rulla i sidled, Röstdelningens axeletiketter får aldrig krocka, och
   växeln mandat eller procent i "Om Majorna bestämde" ska byta både tal och kolumnrubriker.
   Kör medvetet UTAN mobilemulering. Med isMobile: true sätter Chrome innerWidth till layoutbredden
   (355 px vid en 320 px viewport), och då blir scrollWidth <= innerWidth sant fast sidan rullar.
   skal-check.js kör mobilemulerat i en enda bredd och kan därför inte bära den här kontrollen.
   Namngivna argument som i historik-check.js: --sida=, --prel=, --partiell=, --slutlig=. */
const valfriFil = m => /\/data\/swing_\d+\.js(\?|$)/.test((m.location() || {}).url || '') && m.text().includes('404');
const argv = process.argv.slice(2);
const namngivet = (namn, standard) => {
  const p = argv.find(a => a.startsWith(`--${namn}=`));
  return p ? p.slice(namn.length + 3) : standard;
};
const sidaUrl = namngivet('sida', 'http://localhost:8765/index.html');
const extraSidor = [['prel', namngivet('prel', null)], ['partiell', namngivet('partiell', null)], ['slutlig', namngivet('slutlig', null)]].filter(x => x[1]);
const BREDDER = [320, 360, 390, 600, 900, 1280];
const snallt = text => { const e = new Error(text); e.snallt = true; return e; };

// Allt som mäts i webbläsaren. Bredderna avrundas till en decimal så att utskriften går att jämföra mellan körningar.
const MAT = () => {
  const rot = document.getElementById('valgrafik');
  const bredd = el => el ? Math.round(el.getBoundingClientRect().width * 10) / 10 : null;
  const tabell = rot.querySelector('table.mandat');
  const wrap = rot.querySelector('.mandat-wrap');
  const axel = rot.querySelector('.rd-axel-tal');
  const spans = axel ? [...axel.querySelectorAll('span')].filter(s => !s.hidden && s.getClientRects().length) : [];
  const rutor = spans.map(s => s.getBoundingClientRect());
  let krockar = 0;
  for (let i = 1; i < rutor.length; i++) if (rutor[i].left < rutor[i - 1].right) krockar++;
  return {
    scrollWidth: document.documentElement.scrollWidth,
    innerWidth: window.innerWidth,
    sektion: bredd(rot.querySelector('#riksdag')),
    sektionH: rot.querySelector('#riksdag') ? Math.round(rot.querySelector('#riksdag').getBoundingClientRect().height) : null,
    tabell: bredd(tabell),
    wrapScroll: wrap ? wrap.scrollWidth : null,
    wrapClient: wrap ? wrap.clientWidth : null,
    harWrap: !!wrap,
    axelBredd: bredd(axel),
    ticks: axel ? axel.querySelectorAll('span').length : 0,
    synliga: spans.length,
    krockar,
    forsta: spans.length ? spans[0].textContent : '',
    rostdelningDold: !rot.querySelector('#rostdelning') || rot.querySelector('#rostdelning').hidden,
  };
};

// Tabellen och växeln i "Om Majorna bestämde", läst som texten står på skärmen.
const LAS_MANDAT = () => {
  const rot = document.getElementById('valgrafik');
  const t = rot.querySelector('table.mandat');
  const enhet = rot.querySelector('#mandat-enhet');
  const forbehall = rot.querySelector('#mandat-forbehall');
  return {
    rubriker: t ? [...t.querySelectorAll('thead th')].map(e => e.textContent.trim()) : [],
    rader: t ? [...t.querySelectorAll('tbody tr')].map(tr => ({
      parti: ((tr.querySelector('b') || {}).textContent || '').trim(),
      tal: [...tr.querySelectorAll('td.tal')].map(td => td.textContent.trim()),
      klasser: [...tr.querySelectorAll('td.tal')].map(td => td.className),
    })) : [],
    cirklar: rot.querySelectorAll('#halvcirkel circle').length,
    enhetKnappar: enhet ? [...enhet.querySelectorAll('button')].map(b => b.textContent.trim()) : [],
    enhetDold: enhet ? enhet.hidden : null,
    enhetVald: enhet ? (enhet.querySelector('[aria-checked="true"]') || {}).textContent : null,
    live: rot.querySelector('#mandat-live').textContent.trim(),
    forbehall: forbehall.textContent.trim(),
    forbehallDold: forbehall.hidden,
  };
};

const klickaEnhet = text => {
  const b = [...document.querySelectorAll('#valgrafik #mandat-enhet button')].find(x => x.textContent.trim() === text);
  if (b) b.click();
  return !!b;
};

(async () => {
  const browser = await puppeteer.launch({ executablePath: '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome', headless: true, args: ['--no-first-run', '--disable-gpu'] });
  const fel = [], saknade = [], kontroller = [];
  const paus = ms => new Promise(r => setTimeout(r, ms));
  const oppna = async (adress, bredd) => {
    const page = await browser.newPage();
    // isMobile: false, se filhuvudet. deviceScaleFactor 1 räcker: inget här mäts i enheter som beror på skalan.
    await page.setViewport({ width: bredd, height: 900, deviceScaleFactor: 1, isMobile: false, hasTouch: false });
    page.on('pageerror', e => fel.push(String(e)));
    page.on('console', m => { if (m.type() !== 'error') return; if (valfriFil(m)) saknade.push(m.location().url); else fel.push('console: ' + m.text()); });
    await page.goto(adress, { waitUntil: 'networkidle0' });
    await paus(1500);
    if (!await page.evaluate(() => !!document.getElementById('valgrafik'))) throw snallt(`sidan saknar #valgrafik på ${adress}. Kontrollera adressen och att den lokala servern kör.`);
    return page;
  };
  const aren = async page => page.evaluate(() => {
    const v = document.querySelector('#valgrafik #arval-select');
    return v ? [...v.options].map(o => o.value) : [];
  });
  const bytAr = async (page, ar) => { await page.select('#valgrafik #arval-select', ar); await paus(900); };

  // ---- 1 till 4: bredderna
  console.log('bredd | scrollW innerW | sektion | tabell | wrap scroll/client | axelspalt | tick synliga krockar | forsta | sektionH');
  for (const bredd of BREDDER) {
    const page = await oppna(sidaUrl, bredd);
    const alla = await aren(page);
    const m = await page.evaluate(MAT);
    console.log(`${bredd} | ${m.scrollWidth} ${m.innerWidth} | ${m.sektion} | ${m.tabell} | ${m.wrapScroll}/${m.wrapClient} | ${m.axelBredd} | ${m.ticks} ${m.synliga} ${m.krockar} | ${JSON.stringify(m.forsta)} | ${m.sektionH}`);
    kontroller.push([`${bredd} px: sidan rullar inte i sidled (${m.scrollWidth} <= ${m.innerWidth})`, m.scrollWidth <= m.innerWidth]);
    kontroller.push([`${bredd} px: mandattabellen ryms i sin behållare (${m.wrapScroll} <= ${m.wrapClient})`, m.harWrap && m.wrapScroll <= m.wrapClient + 1]);
    kontroller.push([`${bredd} px: inga krockande axeletiketter (${m.krockar})`, m.krockar === 0]);
    kontroller.push([`${bredd} px: första axeletiketten bär enheten (${JSON.stringify(m.forsta)})`, m.rostdelningDold || /%$/.test(m.forsta)]);
    // Antalet tick följer årets högsta andel, så bredderna kontrolleras om i vart och ett av åren.
    for (const ar of alla) {
      await bytAr(page, ar);
      const a = await page.evaluate(MAT);
      console.log(`  ${bredd} px år ${ar} | ${a.scrollWidth} ${a.innerWidth} | tabell ${a.tabell} | wrap ${a.wrapScroll}/${a.wrapClient} | axel ${a.axelBredd} | tick ${a.ticks} synliga ${a.synliga} krockar ${a.krockar}`);
      kontroller.push([`${bredd} px år ${ar}: sidan rullar inte i sidled (${a.scrollWidth} <= ${a.innerWidth})`, a.scrollWidth <= a.innerWidth]);
      kontroller.push([`${bredd} px år ${ar}: mandattabellen ryms i sin behållare (${a.wrapScroll} <= ${a.wrapClient})`, a.harWrap && a.wrapScroll <= a.wrapClient + 1]);
      kontroller.push([`${bredd} px år ${ar}: inga krockande axeletiketter (${a.krockar})`, a.krockar === 0]);
    }
    await page.close();
  }

  // ---- 5: procentväxeln, alla år, plus valnattssidorna
  let sparrSedd = false;   // minst ett år ska visa "under spärren" i mandat och ett tal i procent, det är hela poängen med växeln
  const procentKoll = async (namn, adress, kravForbehall) => {
    const page = await oppna(adress, 390);
    const alla = await aren(page);
    let forbehallSett = false;
    for (const ar of (alla.length ? alla : [null])) {
      if (ar) await bytAr(page, ar);
      const mandat = await page.evaluate(LAS_MANDAT);
      const arText = (mandat.rubriker[1] || '').replace('Riksdagen ', '').trim();
      const kd = mandat.rader.find(r => r.parti === 'KD');
      const etikett = `${namn}${ar ? ' år ' + ar : ''}`;
      // Testdatan för 2026 ger KD mandat i Majorna, riktiga år gör det inte. Spärrkravet gäller därför de år där
      // mandatläget faktiskt säger "under spärren", och att något år gör det kontrolleras separat på slutet.
      const sparr = !!kd && kd.tal[1] === 'under spärren';
      if (sparr) sparrSedd = true;
      if (!mandat.forbehallDold && mandat.forbehall.length) forbehallSett = true;
      console.log(`${etikett} mandat: rubriker ${JSON.stringify(mandat.rubriker)} KD ${JSON.stringify(kd && kd.tal)} cirklar ${mandat.cirklar} enhetsknappar ${JSON.stringify(mandat.enhetKnappar)} dold ${mandat.enhetDold} förbehåll ${JSON.stringify(mandat.forbehall)}`);
      kontroller.push([`${etikett}: växeln finns och visas`, mandat.enhetKnappar.join(',') === 'Mandat,Procent' && mandat.enhetDold === false]);
      kontroller.push([`${etikett}: mandatläget har rubriken Majornas riksdag`, mandat.rubriker[2] === 'Majornas riksdag']);

      await page.evaluate(klickaEnhet, 'Procent');
      await paus(200);
      const p = await page.evaluate(LAS_MANDAT);
      const kdP = p.rader.find(r => r.parti === 'KD');
      console.log(`${etikett} procent: rubriker ${JSON.stringify(p.rubriker)} KD ${JSON.stringify(kdP && kdP.tal)} cirklar ${p.cirklar} live ${JSON.stringify(p.live)} förbehåll ${JSON.stringify(p.forbehall)}`);
      kontroller.push([`${etikett}: procentläget har rubriken Riket ${arText}`, p.rubriker[1] === `Riket ${arText}`]);
      kontroller.push([`${etikett}: procentläget har rubriken Majorna`, p.rubriker[2] === 'Majorna']);
      kontroller.push([`${etikett}: alla tal i procentläget är andelar eller tankstreck`,
        p.rader.length > 0 && p.rader.every(r => r.tal.every(t => /^\d+,\d\s%$/.test(t) || t === '-'))]);
      kontroller.push([`${etikett}: KD visar ett tal i procentläget (${kdP && kdP.tal[1]})`, !!kdP && /^\d+,\d\s%$/.test(kdP.tal[1])]);
      if (sparr) kontroller.push([`${etikett}: procentläget ersätter "under spärren" med ett tal`, !!kdP && /^\d+,\d\s%$/.test(kdP.tal[1])]);
      kontroller.push([`${etikett}: halvcirkeln är oförändrad (${p.cirklar})`, p.cirklar === mandat.cirklar && p.cirklar > 0]);
      kontroller.push([`${etikett}: skärmläsarraden säger vad som ändrades`, /procent/i.test(p.live)]);
      kontroller.push([`${etikett}: samma partirader i båda enheterna`, p.rader.map(r => r.parti).join(',') === mandat.rader.map(r => r.parti).join(',')]);
      kontroller.push([`${etikett}: fetstilen följer fördelningen, inte enheten`, p.rader.map(r => r.klasser.join(' ')).join('|') === mandat.rader.map(r => r.klasser.join(' ')).join('|')]);
      // Procentläget får inte stå utan förbehåll när mandatläget har ett: orden ska täcka båda enheterna.
      kontroller.push([`${etikett}: förbehållet är detsamma i båda enheterna (${JSON.stringify(p.forbehall)})`,
        p.forbehall === mandat.forbehall && p.forbehallDold === mandat.forbehallDold]);

      await page.evaluate(klickaEnhet, 'Mandat');
      await paus(200);
      const t = await page.evaluate(LAS_MANDAT);
      const kdT = t.rader.find(r => r.parti === 'KD');
      kontroller.push([`${etikett}: tillbaka till mandat ger samma tabell som innan`,
        t.rubriker.join('|') === mandat.rubriker.join('|') && !!kdT && kdT.tal.join('|') === kd.tal.join('|')]);
    }
    if (kravForbehall) kontroller.push([`${namn}: den preliminära sidan har ett förbehåll under tabellen`, forbehallSett]);
    await page.close();
  };
  await procentKoll('index', sidaUrl, false);
  for (const [namn, adress] of extraSidor) await procentKoll(namn, adress, namn !== 'slutlig');
  kontroller.push(['något år visar "under spärren" i mandat och ett tal i procent', sparrSedd]);

  kontroller.push(['inga JS-fel', fel.length === 0]);
  if (saknade.length) console.log('valfria filer som saknas:', [...new Set(saknade)].join(' | '));
  console.log(fel.length ? 'JS-FEL: ' + fel.join(' | ') : 'inga JS-fel');
  const fallna = kontroller.filter(k => !k[1]).map(k => k[0]);
  if (fallna.length) console.log('kontroller som föll:\n  ' + fallna.join('\n  '));
  console.log(`${kontroller.length - fallna.length} av ${kontroller.length} kontroller gröna`);
  console.log(fallna.length ? 'BREDDKONTROLL MISSLYCKADES' : 'BREDDKONTROLL OK');
  await browser.close();
  process.exit(fallna.length ? 1 : 0);
})().catch(e => { console.error(e && e.snallt ? 'FEL: ' + e.message : e); process.exit(1); });
