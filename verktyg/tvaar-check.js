const puppeteer = require('puppeteer-core');
// data/swing_<år>.js är valfri: saknas den visar sidan ingen förändringsrad för året. Webbläsarens 404 för
// en sådan fil är alltså väntad och räknas inte som JS-fel, men skrivs ut så att en oväntad lucka syns.
const valfriFil = m => /\/data\/swing_\d+\.js(\?|$)/.test((m.location() || {}).url || '') && m.text().includes('404');
// Adresser: positionellt (sida, kf-sida) som förr, eller namngivet --sida= --kf= --kf6= --slutlig= --prel= --utanparti=.
// De två näst sista är sidor byggda utan --valnatt, med --status slutlig respektive preliminar, för statusradens stillsamma grenar.
// --utanparti= är en sida byggd med --utan-parti S: state är modullokal i valgrafik.js och går inte att nå
// från page.evaluate, så regeln "parti utan tal hoppas över" prövas mot en doktorerad swingfil i stället.
const argv = process.argv.slice(2);
const namngivet = (namn, standard) => {
  const p = argv.find(a => a.startsWith(`--${namn}=`));
  return p ? p.slice(namn.length + 3) : standard;
};
const positionella = argv.filter(a => !a.startsWith('--'));
const url = namngivet('sida', positionella[0] || 'http://localhost:8765/tmp/tvaar/index.html');
const kfUrl = namngivet('kf', positionella[1] || null);   // valfri testsida byggd med --kf-raknade 3, för markörtexten per val
const kf6Url = namngivet('kf6', null);                    // valfri testsida byggd med --kf-raknade 6: sex räknade, tre jämförbara
const slutligUrl = namngivet('slutlig', null);            // valfri sida utan --valnatt, --status slutlig
const prelUrl = namngivet('prel', null);                  // valfri sida utan --valnatt, --status preliminar
const utanPartiUrl = namngivet('utanparti', null);        // valfri sida byggd med --utan-parti S
const SVALEBO = '14800526';
const snallt = text => { const e = new Error(text); e.snallt = true; return e; };
// Statusraden gäller alltid riksdagsvalet, som är färdigräknat i testdatan - även på sidan där kf bara har 3 distrikt.
const STATUS_2026 = 'Preliminärt, 23 av 23 distrikt räknade.';
// Kohorten räknar distrikt som är både räknade och jämförbara: de tre första Majornadistrikten är alla
// jämförbara mot 2022, så kf-sidan byggd med --kf-raknade 3 ska säga tre.
const KOHORT_KF = 'räknat på 3 jämförbara distrikt av 23';

(async () => {
  const browser = await puppeteer.launch({ executablePath: '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome', headless: true, args: ['--no-first-run', '--disable-gpu'] });
  const fel = [], saknade = [];
  const oppna = async adress => {
    const page = await browser.newPage();
    await page.setViewport({ width: 390, height: 844, deviceScaleFactor: 2, isMobile: true, hasTouch: true });
    page.on('pageerror', e => fel.push(String(e)));
    page.on('console', m => { if (m.type() !== 'error') return; if (valfriFil(m)) saknade.push(m.location().url); else fel.push('console: ' + m.text()); });
    await page.goto(adress, { waitUntil: 'networkidle0' });
    await new Promise(r => setTimeout(r, 1500));
    return page;
  };
  const page = await oppna(url);
  const las = async () => {
    const res = await page.evaluate(() => {
      const rot = document.getElementById('valgrafik');
      if (!rot) return { saknas: 'ingen #valgrafik på sidan' };
      const svg = rot.querySelector('#karta svg');
      if (!svg) return { saknas: 'ingen <svg> i #karta', felruta: (rot.querySelector('.fel') || {}).textContent || null };
      const namn = [...rot.querySelectorAll('#karta path.distrikt')].map(p => p.getAttribute('aria-label').split('.')[0]);
      return { arknappar: [...rot.querySelectorAll('#arval button')].map(b => b.textContent), aktivtAr: (rot.querySelector('#arval button.aktiv') || {}).textContent,
               antalPaths: namn.length, harSandarna: namn.includes('Sandarna'), harSandarne: namn.includes('Sandarne'),
               statusrad: rot.querySelector('#statusrad').textContent, toppsvarRader: rot.querySelectorAll('.toppsvar-rad').length,
               laddaOm: !!rot.querySelector('#statusrad button.ladda-om'),
               ariaKarta: svg.getAttribute('aria-label'), viewBox: svg.getAttribute('viewBox') };
    });
    if (res.saknas) throw snallt(`kartan ritades inte på ${url}: ${res.saknas}.` + (res.felruta ? ` Sidans egen felruta: ${res.felruta}` : '')
      + ' Kontrollera att servern kör i projektroten och att testsidan byggts om med verktyg/forbered_tvaar.py.');
    return res;
  };
  const y2026 = await las();
  await page.evaluate(() => [...document.getElementById('valgrafik').querySelectorAll('#arval button')].find(b => b.textContent.endsWith('2022')).click());
  await new Promise(r => setTimeout(r, 600));
  const y2022 = await las();
  console.log(JSON.stringify({ y2026, y2022 }, null, 1));

  const kontroller = [
    ['två årsknappar', y2026.arknappar.length === 2],
    ['2026 aktivt från början', y2026.aktivtAr === 'Valet 2026'],
    ['23 polygoner 2026', y2026.antalPaths === 23],
    ['Sandarna finns 2026', y2026.harSandarna],
    ['Sandarne saknas 2026', !y2026.harSandarne],
    ['2022 aktivt efter klick', y2022.aktivtAr === 'Valet 2022'],
    ['23 polygoner 2022', y2022.antalPaths === 23],
    ['Sandarne finns 2022', y2022.harSandarne],
    ['samma kartram båda åren', y2026.viewBox === y2022.viewBox],
    ['fyra partier i toppsvaret 2026', y2026.toppsvarRader === 4],
    ['statusraden räknar distrikten', y2026.statusrad.startsWith(STATUS_2026)],
    ['Ladda om finns på valnatten', y2026.laddaOm],
    ['statusraden för 2022 på valnatten', y2022.statusrad.startsWith('Slutligt resultat 2022.')],
    ['ingen valdagsmening i 2022-raden', !y2022.statusrad.includes('Valet 2026 är')],
    ['Ladda om leder tillbaka från 2022', y2022.laddaOm]
  ];

  // Kortets rad "Hur har det ändrats" på 2026: jämförbart distrikt får talen, omritat meningen och
  // områdesraden, hela Majorna talen utan kohorttext så länge alla distrikt är räknade.
  await page.evaluate(() => [...document.getElementById('valgrafik').querySelectorAll('#arval button')].find(b => b.textContent.endsWith('2026')).click());
  await new Promise(r => setTimeout(r, 600));
  const panelText = () => page.evaluate(() => document.getElementById('valgrafik').querySelector('#panel').textContent);
  const kort = async kod => {
    await page.evaluate(k => document.getElementById('valgrafik').querySelector('#karta path[data-kod="' + k + '"]').dispatchEvent(new MouseEvent('click', { bubbles: true })), kod);
    await new Promise(r => setTimeout(r, 400));
    return panelText();
  };
  const talSpann = sida => sida.evaluate(() => [...document.getElementById('valgrafik').querySelectorAll('#panel .andrat-tal')].map(s => s.textContent.trim()));
  const partierna = spann => spann.map(t => t.split(' ')[0]);
  const svalebo = await kort(SVALEBO), svaleboTal = await talSpann(page);
  const mariaplan = await kort('14800530');
  const mariaplanLive = await page.evaluate(() => document.getElementById('valgrafik').querySelector('#panel-live').textContent);
  await page.evaluate(() => document.getElementById('valgrafik').querySelector('#panel-tillbaka').click());
  await new Promise(r => setTimeout(r, 400));
  const helaMajorna = await panelText();
  const andratRad = text => (text.match(/Sedan \d{4}:[^]*?procentenheter[^]*?(?=Tillbaka|$)/) || ['(ingen talrad)'])[0].trim();
  console.log('kortet:', JSON.stringify({ svalebo: andratRad(svalebo), svaleboTal, mariaplan: (mariaplan.match(/Gränserna[^]*?sedan \d{4}[^.]*\./) || ['(ingen mening)'])[0],
                                          mariaplanLive, helaMajorna: andratRad(helaMajorna) }, null, 1));
  kontroller.push(
    ['Svalebo har talraden', svalebo.includes('Sedan 2022:')],
    ['Svalebo saknar omritningsmeningen', !svalebo.includes('ritades om')],
    ['tre tal i Svalebos rad', svaleboTal.length === 3],
    ['Mariaplan har omritningsmeningen', mariaplan.includes('ritades om till 2026')],
    ['Mariaplan har områdesraden', mariaplan.includes('Hela Majorna:')],
    ['Mariaplan saknar talraden', !mariaplan.includes('Sedan 2022:')],
    ['skärmläsaren hör omritningsmeningen sist', /ritades om till 2026\. Siffrorna går inte att jämföra med 2022\.$/.test(mariaplanLive.trim())],
    ['hela Majorna har talraden', helaMajorna.includes('Sedan 2022:')],
    ['hela Majorna utan kohorttext när allt är räknat', !helaMajorna.includes('jämförbara distrikt')],
    ['noten utan förbehåll när hela området jämförs', helaMajorna.includes('i procentenheter.')]);

  // Sidor där bara några distrikt har kommunvalet räknat: markörtexten ska räkna räknade distrikt per val
  // och inte per fil, och kortets tal (kohorten) ska bära förbehållet - både i raden och i noten under staplarna.
  const kfSidan = async (namn, adress) => {
    if (!adress) { console.log(`${namn}: hoppas över (ingen adress angiven)`); return null; }
    const kfSida = await oppna(adress);
    const kf = await kfSida.evaluate(() => {
      const rot = document.getElementById('valgrafik');
      const markor = () => { const el = rot.querySelector('.markorer .majorna'); return el ? el.textContent : null; };
      const valjRaknat = () => {
        const p = [...rot.querySelectorAll('#karta path.distrikt')].find(x => !x.getAttribute('aria-label').includes('inte räknat än'));
        if (!p) return null;
        const namn = p.getAttribute('aria-label').split('.')[0];
        if (rot.querySelector('#panel-rubrik').textContent !== namn) p.dispatchEvent(new MouseEvent('click', { bubbles: true }));
        return namn;
      };
      const smaTalen = () => { const el = [...rot.querySelectorAll('.markorer span')].find(s => s.textContent.startsWith('Små tal')); return el ? el.textContent : null; };
      const ut = {};
      rot.querySelector('#flik-rd').click(); ut.rdDistrikt = valjRaknat(); ut.rdMarkor = markor();
      rot.querySelector('#flik-kf').click(); ut.kfDistrikt = valjRaknat(); ut.kfMarkor = markor(); ut.kfDistriktNot = smaTalen();
      rot.querySelector('#panel-tillbaka').click();   // tillbaka till hela Majorna, kommunvalet kvar
      ut.kfMajornaKort = rot.querySelector('#panel').textContent;
      ut.kfMajornaNot = smaTalen();
      ut.kfMajornaSub = rot.querySelector('#panel-sub').textContent;
      ut.statusrad = rot.querySelector('#statusrad').textContent;
      return ut;
    });
    console.log(`${namn}:`, JSON.stringify(kf, null, 1));
    kontroller.push([`${namn}: markörtext rd hela Majorna`, kf.rdMarkor === 'Snittet för hela Majorna'],
                    [`${namn}: markörtext kf räknade distrikt`, kf.kfMarkor === 'Snittet för räknade distrikt i Majorna'],
                    [`${namn}: statusraden gäller riksdagsvalet`, kf.statusrad.startsWith(STATUS_2026)],
                    [`${namn}: kortets kohorttext räknar jämförbara distrikt`, kf.kfMajornaKort.includes(KOHORT_KF)],
                    [`${namn}: noten på hela Majorna bär kohortförbehållet`, kf.kfMajornaNot === `Små tal: förändring mot 2022 i procentenheter, ${KOHORT_KF}.`],
                    [`${namn}: noten på ett distrikt är utan förbehåll`, kf.kfDistriktNot === 'Små tal: förändring mot 2022 i procentenheter.']);
    await kfSida.close();
    return kf;
  };
  await kfSidan('kf-sidan', kfUrl);
  // Sex räknade distrikt men bara tre jämförbara: staplarna vilar på sex, de små talen på tre. Det är
  // fallet noten finns för, och kortets underrad ska säga sex medan noten säger tre.
  const kf6 = await kfSidan('kf6-sidan', kf6Url);
  if (kf6) kontroller.push(['kf6: underraden räknar alla räknade distrikt', kf6.kfMajornaSub.includes('6 av 23 distrikt räknade')]);

  // Regeln "parti utan tal hoppas över": swingfilen på den här sidan saknar S helt.
  if (utanPartiUrl) {
    const sida = await oppna(utanPartiUrl);
    const up = await sida.evaluate(kod => {
      const rot = document.getElementById('valgrafik');
      rot.querySelector('#karta path[data-kod="' + kod + '"]').dispatchEvent(new MouseEvent('click', { bubbles: true }));
      return { tal: [...rot.querySelectorAll('#panel .andrat-tal')].map(s => s.textContent.trim()),
               rad: (rot.querySelector('#panel .andrat-rad') || {}).textContent || null };
    }, SVALEBO);
    console.log('utan-parti-sidan:', JSON.stringify({ ...up, jamfor: svaleboTal }, null, 1));
    const nya = partierna(up.tal), gamla = partierna(svaleboTal);
    kontroller.push(['utan S: talraden finns kvar', !!up.rad && up.rad.includes('Sedan 2022:')],
                    ['utan S: fortfarande tre tal', up.tal.length === 3],
                    ['utan S: inget tal för S', !nya.includes('S')],
                    ['utan S: inget 0,0 i raden', !up.rad.includes('0,0')],
                    ['utan S: ett annat parti har tagit platsen', nya.some(p => !gamla.includes(p))],
                    ['S fanns i raden före doktoreringen', gamla.includes('S')]);
    await sida.close();
  } else {
    console.log('utan-parti-sidan: hoppas över (ingen adress angiven)');
  }

  // Statusradens två grenar utan valnattsläge: sidorna byggs med --status slutlig respektive preliminar och utan --valnatt.
  const utanValnatt = async (namn, adress, vantad) => {
    if (!adress) { console.log(`${namn}-sidan: hoppas över (ingen adress angiven)`); return; }
    const sida = await oppna(adress);
    const res = await sida.evaluate(() => {
      const rot = document.getElementById('valgrafik');
      return { statusrad: rot.querySelector('#statusrad').textContent, laddaOm: !!rot.querySelector('#statusrad button.ladda-om') };
    });
    console.log(`${namn}-sidan:`, JSON.stringify(res));
    kontroller.push([`statusraden på ${namn}-sidan`, res.statusrad.trim() === vantad],
                    [`inget Ladda om på ${namn}-sidan`, !res.laddaOm]);
    await sida.close();
  };
  await utanValnatt('slutlig', slutligUrl, 'Slutligt resultat, riksdagsvalet 2026.');
  await utanValnatt('preliminär', prelUrl, 'Preliminärt resultat 2026.');

  kontroller.push(['inga JS-fel', fel.length === 0]);
  if (saknade.length) console.log('valfria filer som saknas:', [...new Set(saknade)].join(' | '));
  console.log(fel.length ? 'JS-FEL: ' + fel.join(' | ') : 'inga JS-fel');
  const fallna = kontroller.filter(k => !k[1]).map(k => k[0]);
  if (fallna.length) console.log('kontroller som föll: ' + fallna.join(', '));
  console.log(fallna.length ? 'TVÅÅRSKONTROLL MISSLYCKADES' : 'TVÅÅRSKONTROLL OK');
  await browser.close();
  process.exit(fallna.length ? 1 : 0);
})().catch(e => { console.error(e && e.snallt ? 'FEL: ' + e.message : e); process.exit(1); });
