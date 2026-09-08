"""Beehiivs regler för HTML-block i sajtbyggaren: allt inuti en container, scopad CSS, inga vh eller position: fixed."""
import json
import re
import subprocess
import sys
from pathlib import Path

import pytest

ROT = Path(__file__).resolve().parents[1]
CSS = ROT / "valgrafik.css"
JS = ROT / "valgrafik.js"
HTML = ROT / "index.html"


def css_regler(text):
    """Returnerar alla selektorer (även inuti @media) som lista av strängar."""
    text = re.sub(r"/\*.*?\*/", "", text, flags=re.S)
    selektorer, stack, buf = [], [], ""
    i = 0
    while i < len(text):
        c = text[i]
        if c == "{":
            huvud = buf.strip(); buf = ""
            stack.append(huvud)
            if not huvud.startswith("@"):
                selektorer.extend(s.strip() for s in huvud.split(","))
        elif c == "}":
            stack.pop(); buf = ""
        else:
            buf += c
        i += 1
    return [s for s in selektorer if s]


def test_css_ar_scopad_till_containern():
    regler = css_regler(CSS.read_text("utf-8"))
    assert regler, "tom css"
    fel = [s for s in regler if not s.startswith(".mp-val")]
    assert not fel, f"oscopade selektorer: {fel[:10]}"


def test_css_utan_vh_fixed_och_globala_reset():
    text = re.sub(r"/\*.*?\*/", "", CSS.read_text("utf-8"), flags=re.S)
    assert not re.search(r"\d\s*vh\b", text), "vh-mått är förbjudna i Beehiivs HTML-block"
    assert "position: fixed" not in text and "position:fixed" not in text
    assert not re.search(r"(^|[,{}\s])(html|body|:root)\s*[{,]", text), "globala regler på html, body eller :root"


# Allt utanför .mp-val är förbjudet mark i Beehiivs HTML-block: bara de här document-medlemmarna
# skapar noder eller hittar containern, ingen av dem läser eller ändrar värdsidan.
DOCUMENT_TILLATNA = {"currentScript", "createElement", "createElementNS", "createTextNode", "head", "getElementsByClassName"}


def test_js_renderar_i_container_utan_globala_dokumentreferenser():
    js = JS.read_text("utf-8")
    assert "document.currentScript" in js, "basadressen för data ska tas från skriptets egen src"
    otillatna = sorted({m for m in re.findall(r"document\.(\w+)", js) if m not in DOCUMENT_TILLATNA})
    assert not otillatna, f"document-medlemmar utanför tillåtlistan: {otillatna}"
    assert 'querySelector(".mp-main")' in js or "'.mp-main'" in js


def test_index_ar_ett_tunt_skal():
    html = HTML.read_text("utf-8")
    assert '<div id="valgrafik" class="mp-val">' in html
    assert '<link rel="stylesheet" href="valgrafik.css">' in html
    assert '<script src="valgrafik.js"></script>' in html
    assert "<section" not in html, "sidans innehåll ska ligga i valgrafik.js, inte i skalet"


def test_konfig_finns_som_datafil():
    k = json.loads((ROT / "data" / "konfig.json").read_text("utf-8"))
    assert k["ar"] == ["2010", "2014", "2018", "2022"] and k["standardAr"] == "2022" and k["valnatt"] is False
    js = (ROT / "data" / "konfig.js").read_text("utf-8")
    assert js.startswith('window.MAJPOSTEN=window.MAJPOSTEN||{data:{}};window.MAJPOSTEN.data["konfig"]=')


def test_uppdatera_valnatt_flagga_skriver_konfig(tmp_path):
    csv = tmp_path / "v.csv"
    csv.write_text("val;kod;parti;roster\nrd;14800530;V;300\nrd;14800530;S;200\nrd;14800530;giltiga;500\n"
                   "rd;14800530;rostande;505\nrd;14800530;rostberattigade;1000\n", "utf-8")
    (tmp_path / "konfig.json").write_text(json.dumps({"ar": ["2022"], "standardAr": "2022", "valnatt": False,
                                                       "prenumerera": "x", "adress": "y",
                                                       "samarbete": {"visa": True, "namn": "Majornas Bryggeri"},
                                                       "hjalp": {"visa": True, "rubrik": "Behöver du hjälp att rösta?"}}), "utf-8")
    r = subprocess.run([sys.executable, "scripts/uppdatera_2026.py", "--csv", str(csv), "--ut", str(tmp_path), "--ar", "2026", "--valnatt"],
                       cwd=ROT, capture_output=True, text=True)
    assert r.returncode == 0, r.stdout + r.stderr
    k = json.loads((tmp_path / "konfig.json").read_text("utf-8"))
    assert k["ar"] == ["2022", "2026"] and k["standardAr"] == "2026" and k["valnatt"] is True
    assert k["prenumerera"] == "x" and k["adress"] == "y", "övriga fält ska bevaras"
    assert k["samarbete"]["namn"] == "Majornas Bryggeri" and k["samarbete"]["visa"] is True, "samarbetsblocket ska bevaras"
    assert k["hjalp"]["rubrik"] == "Behöver du hjälp att rösta?" and k["hjalp"]["visa"] is True, "rösthjälpen ska bevaras"
    assert (tmp_path / "konfig.js").exists()


def test_konfig_har_samarbete_och_rosthjalp():
    k = json.loads((ROT / "data" / "konfig.json").read_text("utf-8"))
    assert isinstance(k["samarbete"]["visa"], bool), "samarbete.visa ska vara en boolean"
    assert isinstance(k["samarbete"]["valvaka"]["visa"], bool), "samarbete.valvaka.visa ska vara en boolean"
    assert isinstance(k["hjalp"]["visa"], bool), "hjalp.visa ska vara en boolean"
    from scripts import schema
    assert "samarbete" in schema.KONFIG_STANDARD and "hjalp" in schema.KONFIG_STANDARD
    js = (ROT / "data" / "konfig.js").read_text("utf-8")
    assert "samarbete" in js and "hjalp" in js, "konfig.js ska vara omskriven ur konfig.json"


def test_layout_foljer_containern_inte_fonstret():
    css = CSS.read_text("utf-8")
    assert "container-type: inline-size" in css
    assert "@container (min-width: 900px)" in css, "desktopläget (karta och kort sida vid sida) från 900 px containerbredd"
    assert "@media (min-width: 600px)" not in css and "@media (max-width: 599px)" not in css, "brytpunkter ska följa containern, inte fönstret"


def test_ingen_prenumerationsknapp():
    js = JS.read_text("utf-8")
    assert "Prenumerera på Majposten" not in js and 'class="cta"' not in js
    k = json.loads((ROT / "data" / "konfig.json").read_text("utf-8"))
    assert "prenumerera" not in k


def test_scroll_margin_under_beehiivs_klibbiga_meny():
    css = CSS.read_text("utf-8")
    assert "scroll-margin-top: var(--mp-sticky-top" in css
    k = json.loads((ROT / "data" / "konfig.json").read_text("utf-8"))
    assert isinstance(k["stickyTopp"], (int, float))


def test_djuplankar_lases_och_skrivs_mot_foraldern_i_iframen():
    js = JS.read_text("utf-8")
    assert "function sidLocation()" in js


def test_geometri_per_ar_dynamiskt_antal_och_swing_for_alla_ar():
    js = JS.read_text("utf-8")
    assert '"distrikt_" + a' in js, "sidan laddar distrikt_<år> för varje år i KONFIG.ar"
    assert "23 valdistrikt" not in js and "de 23 valdistrikten" not in js, "antalet distrikt läses ur datan"
    assert "sort()[0]" not in js, "basåret väljs inte längre implicit, swing laddas för alla år som har en fil"
    assert "function gemensamBbox()" in js
    # data/distrikt.js är en övergångskopia (samma data som distrikt_2022.js, nyckeln "distrikt") kvar åt
    # läsare med cachad gammal valgrafik.js som fortfarande laddar den filen; koden själv ska aldrig göra det.
    assert '"distrikt.js"' not in js and 'laddaSkript("distrikt")' not in js


def test_toppsvar_och_statusrad_ersatter_banderollen():
    js = JS.read_text("utf-8")
    css = CSS.read_text("utf-8")
    assert 'id="statusrad"' in js and 'id="toppsvar"' in js and "function renderToppsvar()" in js
    assert 'id="valnatt"' not in js and "renderBanderoll" not in js and 'id="ingress"' not in js
    assert ".banderoll" not in css and ".toppsvar-rad" in css
    assert "Ladda om" in js
    assert 'class: "ladda-om"' in js and '"button"' in js, "Ladda om är en knapp, inte en tom länk"
    assert 'href: "#"' not in js, "inga tomma länkar i grafiken"


def test_reserverade_hojder_i_sidhuvudet():
    """Statusraden, toppsvaret och årsknapparna tar plats redan innan datan kommer, så att sidhuvudet inte hoppar.
    Sedan grupp 4 ligger den redaktionella meningen i ett eget element som fylls i samma stund som konfigen
    lästs; den behöver därför ingen reserverad rad i toppsvaret, och klassen har-mening är borta."""
    css = CSS.read_text("utf-8")
    js = JS.read_text("utf-8")
    for regel in (".mp-val .statusrad", ".mp-val .toppsvar", ".mp-val .arval"):
        rad = next((r for r in css.splitlines() if r.startswith(regel + " {")), None)
        assert rad and "min-height:" in rad, f"{regel} saknar reserverad höjd"
    assert "har-mening" not in js and "har-mening" not in css, "meningen har eget element, ingen klass på roten"
    assert "for (const ruta of arvalRutor()) ruta.hidden" in js, \
        "alla fem väljarrader tar plats så snart konfigen är läst, inte bara sidhuvudets"
    assert '$("#statusrad").hidden' in js, "en statusrad som ska tiga döljs redan när konfigen lästs"


def test_kortet_har_ingen_andringsrad_kvar():
    """Blocket Hur har det ändrats är borta ur kortet: rubriken, talraden och områdesraden. Informationen
    står kvar där den hör hemma, som små tal vid stapeln den gäller."""
    js = JS.read_text("utf-8")
    assert "Hur har det ändrats" not in js, "rubriken är borttagen"
    for namn in ("andratRubrik", "andrat-rubrik", "andrat-rad", "andrat-tal", "andrat-enhet",
                 "omradesRad", "toppMedTal", "hurAndratMajorna"):
        assert namn not in js, f"{namn} skulle tas bort med ändringsraden"
    assert "`Sedan ${bas}: `" not in js and "Hela Majorna: ${p}" not in js, "talraden och områdesraden är borta"
    css = CSS.read_text("utf-8")
    for regel in (".andrat-rubrik", ".andrat-rad", ".andrat-tal", ".andrat-enhet"):
        assert regel not in css, f"{regel} har ingen märkspråksnod kvar"


def test_kortet_behaller_de_sma_talen_och_omritningsmeningen():
    """De två delarna som stannar: talen vid staplarna med sin legendrad, och meningen om ett omritat
    distrikt - den förklarar varför just det distriktet saknar små tal när grannarna har dem."""
    js = JS.read_text("utf-8")
    assert 'h("span", { class: "swing"' in js, "de små talen står kvar vid staplarna"
    assert "Små tal: förändring mot ${state.swing[state.ar].bas} i procentenheter" in js, "legendraden står kvar"
    assert "const kohortSlut =" in js and "kohortSlut(k)" in js, "kohortförbehållet hör till legendraden"
    assert "function omritadNot(" in js and "ej_jamforbara" in js
    assert "ritades om till ${sw.ar}" in js, "meningen om ett omritat distrikt står kvar"
    assert 'class: "not omritad"' in js, "meningen är ett fristående stycke utan rubrik"
    kropp = js[js.index("function renderPanel()"):js.index("/* ---- tabellen */")]
    assert "liveSlut" in kropp, "skärmläsarraden slutar med omritningsmeningen"


def test_kortets_underrad_utan_valdeltagande_och_giltiga_roster():
    """Underraden i kortet säger inte längre valdeltagande eller antal giltiga röster. Kvar blir bara
    räkneläget på valnatten, och raden döljs helt när det saknas."""
    js = JS.read_text("utf-8")
    kropp = js[js.index("function renderPanel()"):js.index("/* ---- tabellen */")]
    assert "${tal(m.giltiga)} giltiga röster" not in kropp and "${tal(d.giltiga[val])} giltiga röster" not in kropp
    assert "Valdeltagande ${procent" not in kropp, "valdeltagandet är borta ur kortet"
    assert "let vd" not in kropp and "vd + \". \"" not in kropp, "vd räknas inte längre"
    assert "`${vn.raknade} av ${vn.totalt} distrikt räknade.`" in kropp, "valnattsprefixet står kvar"
    assert "sub.hidden = !subText" in kropp, "tom rad döljs"


def test_rubriknivaerna_skyddas_mot_vardsidans_stilar():
    """Varje rubriknivå grafiken använder får färg och form uttryckligen, annars läcker värdsidans stilar in."""
    js = JS.read_text("utf-8")
    css = CSS.read_text("utf-8")
    nivaer = set(re.findall(r'h\("(h[1-6])"', js)) | set(re.findall(r"<(h[1-6])[ >]", js))
    assert "h3" in nivaer, "kortets rubrik ska vara en h3"
    skydd = next(r for r in css.splitlines() if "text-shadow: none" in r)
    farg = next(r for r in css.splitlines() if r.startswith(".mp-val h1,") and "color: var(--black)" in r)
    for niva in sorted(nivaer):
        assert f".mp-val {niva}," in skydd or f".mp-val {niva} " in skydd, f"{niva} saknas i skyddsregeln"
        assert f".mp-val {niva}," in farg or f".mp-val {niva} " in farg, f"{niva} saknar uttrycklig färg"


def test_kartan_skriver_inga_partibokstaver_i_storsta_laget():
    """Kartlegenden säger vilken färg som är vilket parti: etiketten i läget största parti är borta.
    Styrkeläget behåller sitt tal, och det valda distriktets namn ritas fortfarande ut."""
    js = JS.read_text("utf-8")
    kropp = js[js.index("function etikettText("):js.index("function namnRader(")]
    assert re.search(r'if \(state\.lage === "storsta"\) return null', kropp), "inget parti får en etikett"
    assert "andelHeltal(d, val, state.parti)" in kropp, "styrkeläget behåller talet"
    assert "enfargad" not in js, "grenen för enfärgad karta blir oanvänd och tas bort"
    assert "namnRader(d.namn)" in js, "det valda distriktets namn ritas fortfarande ut"


def test_distriktsgranserna_bar_kartan():
    """Utan bokstäver måste formerna bära mer: gränsen är 3 px papper, och hover och tangentbordsfokus
    är fortfarande tydligare än grundläget."""
    css = CSS.read_text("utf-8")
    rad = next(r for r in css.splitlines() if r.startswith(".mp-val #karta path.distrikt {"))
    assert "stroke: var(--papper)" in rad and "stroke-width: 3;" in rad
    bredd = lambda r: float(re.search(r"stroke-width: ([\d.]+)", r).group(1))
    hover = next(r for r in css.splitlines() if r.startswith(".mp-val #karta path.distrikt:hover"))
    fokus = next(r for r in css.splitlines() if r.startswith(".mp-val #karta path.distrikt:focus-visible"))
    assert bredd(hover) > bredd(rad) and bredd(fokus) > bredd(rad)


def test_historiksektionen_finns_och_foljer_kartans_val():
    """Majorna sedan 2006: egen sektion utan knapprad, reserverad höjd, laddad ur data/historik.js."""
    js = JS.read_text("utf-8")
    css = CSS.read_text("utf-8")
    assert 'id="historik"' in js and "function renderHistorik()" in js
    assert "function histDeltagande(" in js and "function histKartor()" in js
    assert 'laddaSkript("historik")' in js and 'laddaSkript("distrikt_2006")' in js
    assert 'id="hist-val"' not in js and "hist-knappar" not in js, "sektionen har inga egna valknappar"
    assert ".hist-bild-b { min-height" in css, "höjden är reserverad innan datan finns"
    assert (ROT / "data" / "historik.js").exists()
    # X-axeln tar nästa valår ur konfigen, men först på valnatten: se
    # test_axeln_visar_valaret_forst_pa_valnatten.
    kropp = js[js.index("function histAxelAr("):]
    assert "KONFIG.valdag" in kropp[:kropp.index("\n}")], "histAxelAr lägger till nästa valår ur KONFIG.valdag"
    # Ett år utan punkt: samma ord i ringen som i bildens beskrivning, olika i de två lägena. Orden står i
    # histVantetext, punkten efter dem i beskrivningens mall.
    assert "räknas på valnatten" in js, "ett år utan punkt räknas på valnatten"
    assert "räknas just nu" in js, "på valnatten står det räknas just nu i stället"
    assert "${histVantetext()}." in js, "beskrivningen avslutar väntetexten med punkt"


def test_bild_a_ar_borta_ur_historiksektionen():
    """Partilinjediagrammet med talraden och den långa noten är borttaget. Kvar står sektionens mening,
    bild B och konturkartorna."""
    js = JS.read_text("utf-8")
    css = CSS.read_text("utf-8")
    for namn in ("hist-bild-a", "hist-talrad", "hist-not-a", "histLinjer", "histTalrad", "sattHistorikAr",
                 "histLasX", "HIST_PARTIER", "HIST_NOT_FI_2014", "histPartier", "historikAr",
                 "histTalPartier", "antalDistriktText", "hist-laslinje", "hist-svg"):
        assert namn not in js, f"{namn} hörde till bild A och ska vara borta"
    for regel in (".hist-talrad", ".hist-tal ", ".hist-svg", ".hist-laslinje"):
        assert regel not in css, f"{regel} hörde till bild A"
    assert 'id="hist-mening"' in js and "function histMening(" in js, "sektionens mening står kvar"
    assert "histLista" in js, "delad hjälpare står kvar"
    for dod in ("histHarTal", "sistaPunkt"):
        assert dod not in js, f"{dod} hade bara bild A som kund och ska vara borta"
    # Slakkontrollen mäter den bild som finns kvar, annars blir den verkningslös.
    kropp = js[js.index("function histBildSlak()"):js.index("let senastDesktop")]
    assert "#hist-bild-b" in kropp and "#hist-bild-a" not in kropp


def test_valdeltagandebilden_har_bara_etikett_och_not():
    """Bild B har en etikett som säger vad den visar, utan årtal och tal - meningen med talen står i
    bildens aria-label. Noten säger var skalan börjar, utan meningen om att valdeltagande i olika val
    inte ska jämföras."""
    js = JS.read_text("utf-8")
    css = CSS.read_text("utf-8")
    assert 'id="hist-mening-b"' in js and "etikettEl" in js, "etiketten över bild B finns"
    assert "`Valdeltagande i ${VALNAMN[val].toLowerCase()}`" in js, "etiketten saknar årtal och tal"
    assert ".hist-etikett" in css and "min-height: 22px" in css, "etikettens höjd är reserverad"
    assert "ska inte jämföras med varandra" not in js, "förbehållet om röstberättigade är borttaget"
    kropp = js[js.index("function histDeltagande"):js.index("function histKartor")]
    assert "const mening =" in kropp and '"aria-label": `${mening}' in kropp, "meningen är bildens textalternativ"
    assert "Skalan börjar vid ${Math.round(lo * 100)} procent." in kropp


def container_kroppar(text, villkor):
    """Kropparna i alla @container-block med det givna villkoret, med klammermatchning."""
    ut = []
    for m in re.finditer(r"@container\s*\(" + re.escape(villkor) + r"\)\s*\{", text):
        i, djup = m.end(), 1
        while i < len(text) and djup:
            if text[i] == "{":
                djup += 1
            elif text[i] == "}":
                djup -= 1
            i += 1
        ut.append(text[m.end():i - 1])
    return ut


def test_historikbilden_reserverar_hojd():
    """Bild B är 160 px hög i alla bredder och reserverar den höjden, så att sektionen inte hoppar när
    den ritas. Ingen bredare container ger den en annan höjd."""
    css = CSS.read_text("utf-8")
    assert re.search(r"\.hist-bild-b\s*\{[^}]*min-height:\s*160px", css), "höjden är reserverad innan datan finns"
    kroppar = "\n".join(container_kroppar(css, "min-width: 600px") + container_kroppar(css, "min-width: 900px"))
    assert "min-height" not in kroppar or not re.search(r"\.hist-bild[^-\w][^}]*min-height", kroppar), \
        "bildens höjd ändras inte med containerns bredd"
    js = JS.read_text("utf-8")
    kropp = js[js.index("function histDeltagande"):js.index("function histKartor")]
    assert re.search(r"\bH = 160\b", kropp), "CSS reserverar samma höjd som bilden ritas i"


def test_historiksektionen_ritas_om_pa_de_tre_stallena():
    """renderHistorik körs i renderAllt, när fliken byter val och när containern byter bredd."""
    js = JS.read_text("utf-8")
    allt = re.search(r"function renderAllt\(\) \{\n([^\n]*)\n", js)
    assert allt and allt.group(1).rstrip().endswith("renderHistorik();"), "renderHistorik sist i renderAllt"
    flik = re.search(r"onclick: \(\) => \{ state\.val = val;[^\n]*renderHistorik\(\);", js)
    assert flik, "flikarna ritar om historiken när valet byts"
    obs = re.search(r"new ResizeObserver\(\(\) => \{(.*?)\}\)\.observe\(rot\);", js, re.S)
    assert obs and "renderHistorik()" in obs.group(1), "ResizeObservern ritar om historiken"
    markup = js[js.index('<section id="historik"'):]
    markup = markup[:markup.index("</section>")]
    assert "<button" not in markup, "sektionen följer kartans val och har inga egna knappar"


def test_valdeltagandebilden():
    """Bild B: Majorna mot Göteborg, riket som tredje linje, skalan står i bildtexten."""
    js = JS.read_text("utf-8")
    assert "function histDeltagande(val) {" in js, "bild B ritas av histDeltagande"
    assert "Skalan börjar vid" in js, "bildtexten säger var skalan börjar"
    assert re.search(r'gron:\s*"#3F5A3A"', js), "slottsskogsgrönt är Majornas linje"
    kropp = js[js.index("function histDeltagande"):js.index("function histKartor")]
    assert re.search(r'niva: "riket"', kropp), "riket ritas som tredje linje, inte bara nämns i en kommentar"
    assert re.search(r"\bH = 160\b", kropp), "höjden är 160 px, samma som CSS reserverar"


def test_valdeltagandebildens_hogermarginal():
    """Högermarginalen är exakt 70 px: etiketten Göteborg står 13 px till höger om sin punkt och mäter
    54,2 px i Arial 13, alltså 67,2 px, plus knappt tre pixlar marginal till bildkanten. Punkten kan ligga
    längst ut på axeln under valnatten. Talet är låst, så att en ändrad marginal kräver ett nytt beslut."""
    js = JS.read_text("utf-8")
    kropp = js[js.index("function histDeltagande"):js.index("function histKartor")]
    h = re.search(r"M = \{[^}]*\bh: (\d+)", kropp)
    assert h, "bild B sätter en högermarginal"
    assert int(h.group(1)) == 70, "etiketten Göteborg kräver 67,2 px och får inte klippas"


def test_konturkartorna_och_den_kortade_faktalistan():
    """Två konturkartor visar varför kvarteret inte går att följa bakåt, och Om siffrorna kortas till
    avgränsning, källa och andelsdefinition. Förbehåll som gäller ett diagram står under det diagrammet:
    valdeltagandet i bild B, Byggd av Majposten i sidfoten."""
    js = JS.read_text("utf-8")
    assert "hist-figur" in js, "varje karta ligger i en figure med bildtext"
    assert "function histKartor() {" in js
    kropp = js[js.index("function histKartor() {"):js.index("/* ---- fakta */")]
    assert "historikGeo" in kropp, "2006 års konturer kommer ur state.historikGeo"
    assert "figcaption" in kropp, "bildtexten säger år och antal distrikt"
    assert "Samma yta, olika gränser" in js, "etiketten säger vad kartorna visar"
    assert "Till vänster distrikten i valet" in js, "noten namnger båda åren"
    assert "valhemligheten gäller per distrikt" not in js, \
        "meningen om valhemligheten togs bort ur noten 2026-09-08"
    fakta = js[js.index("function renderFakta()"):]
    assert "Avgränsning:" in fakta, "listan börjar med avgränsningen"
    assert "Andel = partiets röster delat med giltiga röster." not in fakta, \
        "andelsdefinitionen togs bort 2026-09-08"
    assert 'Slutligt resultat." : "Preliminärt resultat."' not in fakta, \
        "statusmeningen upprepade ordet som redan står i meta.kalla"
    assert 'replace(/\\.\\s*$/, "")' in fakta, "en punkt som redan står i kallan ger inte dubbel punkt"
    assert "Valdeltagande i Majorna" not in fakta, "valdeltagandet står i bild B, inte i Om siffrorna"
    assert "Byggd av Majposten" not in fakta, "avsändaren står i sidfoten, inte i listan"


def test_arvaljaren_ar_en_dropdown():
    """Årväljaren är en <select> med etiketten på selecten, inte en knapprad med role=group."""
    js = JS.read_text("utf-8")
    css = CSS.read_text("utf-8")
    assert '"arval-select"' in js, "sidhuvudets select har ett eget id"
    assert '"arval-select-" + i' in js, "sektionernas väljare får egna id, ett id får inte dubbleras"
    assert '"aria-label": "Välj valår"' in js, "etiketten sitter på selecten"
    markup = next(r for r in js.splitlines() if 'id="arval"' in r)
    assert 'role="group"' not in markup and 'aria-label' not in markup, "behållaren har varken role eller etikett kvar"
    rad = next((r for r in css.splitlines() if r.strip().startswith(".mp-val .arval select {")), None)
    assert rad and "font: inherit" in rad and "color:" in rad and "background:" in rad and "border:" in rad, \
        "selecten ärver typsnitt och får egen färg, bakgrund och ram"


def test_arvaljaren_har_ingen_pilnavigering():
    """En <select> är nativt tillgänglig: pilnavigeringen för knapprader kopplas inte på den."""
    js = JS.read_text("utf-8")
    kropp = js[js.index("function renderHuvud()"):js.index("/* ---- toppsvaret")]
    assert "pilNavigering" not in kropp, "pilNavigering hör till knapprader, inte till en select"


def test_lat_laddning_av_ar():
    """Bara de år som behövs laddas vid start, resten när läsaren väljer dem."""
    js = JS.read_text("utf-8")
    assert "function laddaAr(" in js, "en gemensam funktion laddar ett år en gång"
    start = js[js.index("async function start()"):js.index("/* ===================================================================== render */")]
    assert "KONFIG.ar = onskade.filter" not in start, "årslistan filtreras inte längre till laddade år vid start"
    assert 'onskade.map(a => laddaSkript("valdata_' not in start, "alla år laddas inte i ett svep"
    assert "laddaAr" in start, "start laddar standardåret och eventuellt URL-året genom laddaAr"


def test_senaste_ar_ar_det_senaste_laddade():
    """Historiksektionen slår upp state.data[senasteAr()]: bara laddade år får räknas."""
    js = JS.read_text("utf-8")
    rad = next(r for r in js.splitlines() if r.startswith("const senasteAr ="))
    assert "state.data" in rad, "senasteAr räknar bara år som faktiskt är laddade"


def test_skalmax_raknas_om_efter_varje_laddat_ar():
    """Stapelbredden i kortet vilar på alla laddade år och kan växa när ett år till kommer in."""
    js = JS.read_text("utf-8")
    kropp = js[js.index("function laddaAr("):]
    kropp = kropp[:kropp.index("\n}\n")]
    assert "raknaSkalmax()" in kropp, "skalmax räknas om efter varje laddat år"


def test_arsbytet_tal_ett_ar_som_inte_gar_att_ladda():
    """Selecten stängs av under laddningen, vyn står kvar, och ett år utan filer ger en rad i #arval."""
    js = JS.read_text("utf-8")
    css = CSS.read_text("utf-8")
    assert "kunde inte laddas." in js, "felraden säger vilket år som föll"
    assert "disabled = true" in js, "selecten stängs av medan året laddas"
    assert "arval-fel" in js, "felraden har en egen klass"
    assert ".mp-val .arval-fel {" in css, "felraden får en stil"


def test_arsbytet_revaliderar_distriktet():
    """Ett distrikt som inte finns det nya året får inte bli kvar valt."""
    js = JS.read_text("utf-8")
    kropp = js[js.index("function visaAr("):]
    kropp = kropp[:kropp.index("\n}\n")]
    assert "distriktMap()[state.vald]" in kropp, "distriktet valideras om vid årsbyte"
    assert "partierIVal" in kropp, "partiet valideras om vid årsbyte"


def test_toppsvaret_visar_alla_partier_pa_desktop():
    """Fyra partier under 600 px containerbredd, alla utom Övriga från 600 px."""
    js = JS.read_text("utf-8")
    css = CSS.read_text("utf-8")
    kropp = js[js.index("function renderToppsvar()"):js.index("/* ---- samarbete")]
    assert "arDesktop()" in kropp, "antalet rader följer containerbredden"
    assert "arDesktop() ? utomOvriga : utomOvriga.slice(0, 4)" in kropp, "fyra rader gäller bara under brytpunkten"
    assert "rader.length" in kropp, "aria-etiketten följer antalet partier"
    # css har flera block med samma villkor: reservationen kan stå i vilket som helst av dem
    rad = None
    for m in re.finditer(r"@container \(min-width: 600px\) \{(.*?)\n\}\n", css, re.S):
        rad = rad or next((r for r in m.group(1).splitlines() if r.strip().startswith(".mp-val .toppsvar {")), None)
    assert rad and "min-height:" in rad, "åtta rader får en egen reserverad höjd på desktop"


def test_toppsvaret_ritas_om_vid_brytpunkten():
    """ResizeObservern ritar om toppsvaret när containern passerar 600 px."""
    js = JS.read_text("utf-8")
    obs = re.search(r"new ResizeObserver\(\(\) => \{(.*?)\}\)\.observe\(rot\);", js, re.S)
    assert obs and "renderToppsvar()" in obs.group(1), "toppsvaret ritas om vid desktopbytet"


def test_konfig_har_fyra_ar_och_valnattsmening():
    """Fyra historiska år i väljaren och den redaktionella meningen om valnatten."""
    k = json.loads((ROT / "data" / "konfig.json").read_text("utf-8"))
    assert k["ar"] == ["2010", "2014", "2018", "2022"], "fyra år i väljaren"
    assert k["standardAr"] == "2022"
    assert k["toppsvar"]["mening"].strip(), "meningen om valnatten står i konfigen"
    js = (ROT / "data" / "konfig.js").read_text("utf-8")
    assert '"2010","2014","2018","2022"' in js.replace(", ", ","), "konfig.js är omskriven ur konfig.json"
    assert k["toppsvar"]["mening"] in js, "meningen följer med till konfig.js"


def test_arvaljaren_behaller_tangentbordsfokus_over_en_laddning():
    """disabled flyttar fokus till sidans början: selecten tar tillbaka det när året är inne."""
    js = JS.read_text("utf-8")
    kropp = js[js.index("async function byteAr("):]
    kropp = kropp[:kropp.index("\n}\n")]
    assert "valj.focus({ preventScroll: true })" in kropp, "fokus läggs tillbaka på selecten efter laddningen"
    assert kropp.index("disabled = false") < kropp.index("valj.focus"), "först på igen, sedan fokus"


def test_valnatten_laddar_jamforelsearet_vid_start():
    """Med lat laddning står bara standardåret i state vid start. På valnatten är de flesta distrikt
    oräknade, och kortets bakåtvända rad slår upp basåret bland de laddade åren - alltså måste
    jämförelseåret laddas från början när KONFIG.valnatt är sant."""
    js = JS.read_text("utf-8")
    kropp = js[js.index("async function start()"):]
    kropp = kropp[:kropp.index("\n}\n")]
    assert "KONFIG.valnatt" in kropp, "valnattsgrenen finns i start"
    assert "Number(a) < Number(KONFIG.standardAr)" in kropp, "jämförelseåret är största året under standardåret"


def test_konturkartorna_stallar_valaret_mot_valt_ar():
    """Vänstra kartan är alltid valårets indelning, högra det år läsaren valt. Är de samma år tar det
    äldsta året i serien högra platsen, annars hade paret blivit två likadana kartor. Noten namnger de
    två åren i stället för att räkna distrikt."""
    js = JS.read_text("utf-8")
    kropp = js[js.index("function histKartor()"):]
    kropp = kropp[:kropp.index("\n}\n")]
    assert "valdagAret()" in kropp, "vänstra kartan följer valåret ur konfigen"
    assert "state.konturGeo" in kropp, "valårets geometri laddas vid sidan av årväljarens år"
    assert "state.historikGeo" in kropp, "2006 är reserven när valt år är valåret självt"
    assert "Till vänster distrikten i valet ${arA}" in kropp, "noten namnger båda åren"
    assert "gNu.features.length" not in kropp, "noten räknar inte längre distrikt"
    assert 'id="hist-etikett-kartor"' in js, "kartorna har en egen etikett, som bild B"


def test_arvaljarens_felrad_ar_en_levande_region():
    """En role=status som skapas först när felet inträffar hinner inte bli en levande region."""
    js = JS.read_text("utf-8")
    assert 'id="arval-fel" role="status" hidden' in js, "felraden ligger i markupen från början"
    kropp = js[js.index("async function byteAr("):]
    kropp = kropp[:kropp.index("\n}\n")]
    assert 'setAttribute("aria-busy", "true")' in kropp and 'removeAttribute("aria-busy")' in kropp


def test_arvaljaren_har_knappradens_marginal():
    """Selecten ärvde inte .knappar-regeln när knappraden byttes ut."""
    css = CSS.read_text("utf-8")
    rad = next(r for r in css.splitlines() if r.startswith(".mp-val .arval {"))
    assert "margin: 0 0 12px" in rad, "samma luft under årväljaren som knappraden hade"


def test_toppsvaret_utan_magiskt_tak():
    """Antalet partier på desktop är alla utom Övriga, inte ett tal som råkar vara stort nog."""
    js = JS.read_text("utf-8")
    assert "arDesktop() ? 99 : 4" not in js
    assert "const rader = arDesktop() ? utomOvriga : utomOvriga.slice(0, 4);" in js


def test_mandattabellen_ligger_i_en_rullbar_behallare():
    """Tabellen får inte dra med sig hela sidan i sidled: den ryms i en egen ruta som kan rulla."""
    js = JS.read_text("utf-8")
    css = CSS.read_text("utf-8")
    assert 'class: "mandat-wrap"' in js, "renderMandatLegend lägger tabellen i en behållare"
    rad = next(r for r in css.splitlines() if r.startswith(".mp-val .mandat-wrap {"))
    assert "overflow-x: auto" in rad and "max-width: 100%" in rad


def test_partinamnet_doljs_i_css_under_brytpunkten():
    """Det långa partinamnet är det som gör tabellen för bred på en smal skärm. Dölj det i CSS, inte i JS."""
    js = JS.read_text("utf-8")
    css = CSS.read_text("utf-8")
    assert 'class: "parti-namn"' in js, "partinamnet får en klass i stället för en inline-färg"
    assert 'h("span", { style: "color:var(--sten)" }, parti(p).namn)' not in js
    # 371 px, inte 380: tabellens naturliga bredd med namnet är 339 px och sektionen är rotbredden minus
    # 32 px, så namnet ryms redan från 372 px. En snävare gräns dolde det i ett band där det fick plats.
    block = css[css.index("@container (max-width: 371px)"):]
    block = block[:block.index("}", block.index("{", block.index("{") + 1)) + 1]
    assert ".parti-namn" in block and "display: none" in block
    kropp = js[js.index("function renderMandatLegend("):]
    kropp = kropp[:kropp.index("\n}\n")]
    assert "innerWidth" not in kropp and "matchMedia" not in kropp, "brytpunkten hör hemma i CSS"


def test_enhetsvaxeln_finns_och_ror_inte_mandatRort():
    """Växeln mandat eller procent styr bara tabellen: inte halvcirkeln och inte den automatiska övergången."""
    js = JS.read_text("utf-8")
    assert 'id="mandat-enhet"' in js, "knappraden ligger i markupen"
    assert 'mandatEnhet: "mandat"' in js, "standardläget är mandat"
    kropp = js[js.index("function sattMandatEnhet("):]
    kropp = kropp[:kropp.index("\n}\n")]
    assert "mandatRort" not in kropp, "enheten är inte ett byte av fördelning"
    assert "halvcirkel" not in kropp, "halvcirkeln är mandat till sin natur"
    assert "b.dataset.enhet" in kropp, "knapparna känns igen på sitt data-attribut, inte på texten"


def test_procentlaget_har_egna_kolumnrubriker():
    """Rubrikerna får inte påstå mandat när talen är röstandelar."""
    js = JS.read_text("utf-8")
    kropp = js[js.index("function skrivMandatTal("):]
    kropp = kropp[:kropp.index("\n}\n")]
    assert "Riket ${" in kropp and '"Majorna"' in kropp, "procentläget har egna rubriker"
    assert '"Majornas riksdag"' in kropp and "Riksdagen ${" in kropp, "mandatläget behåller sina"
    assert 'aktiv" : "dampad' in kropp, "fetstilen följer fördelningen i båda enheterna"


def test_axeletiketterna_glesas_efter_matning():
    """Antalet tick följer årets högsta andel, så en ren brytpunkt räcker inte - etiketterna mäts."""
    js = JS.read_text("utf-8")
    kropp = js[js.index("function glesaAxelEtiketter("):]
    kropp = kropp[:kropp.index("\n}\n")]
    assert "getBoundingClientRect" in kropp, "gallringen mäter etiketternas rutor"
    rd = js[js.index("function renderRostdelning("):]
    rd = rd[:rd.index("\n}\n")]
    assert rd.index("rader.replaceChildren(grafik)") < rd.index("glesaAxelEtiketter("), "mät först när grafiken sitter i DOM"


# ---- grupp 4 ur Daniels feedbackrunda: sidhuvudet bantat och årväljaren flyttad högst upp


def test_statusraden_tiger_fore_valdagen():
    """Meningen "Slutligt resultat 2022. Valet 2026 är söndag 13 september." är borta: årväljaren och den
    redaktionella meningen ovanför bär redan den informationen. Valnattens räknestatus och Ladda om står kvar."""
    js = JS.read_text("utf-8")
    assert "datumText" not in js, "datumtexten hade bara valdagsmeningen som kund"
    kropp = js[js.index("function statusText()"):js.index("function renderToppsvar()")]
    assert "Valet ${valdagAr}" not in kropp, "valdagsmeningen är borta"
    assert "Preliminärt, ${raknade} av ${totalt} distrikt räknade" in kropp, "valnattens räknestatus står kvar"
    assert "Slutligt resultat, riksdagsvalet ${meta.ar}" in kropp, "raden efter sluträkningen står kvar"
    assert "laddaOm: true" in kropp, "Ladda om står kvar på valnatten"


def test_toppsvaret_har_ingen_valdeltagandemening():
    """"82,8 % röstade, mot 84,2 % i riket." är borttagen ur toppsvaret."""
    js = JS.read_text("utf-8")
    kropp = js[js.index("function renderToppsvar()"):js.index("/* ---- samarbete")]
    assert "röstade" not in kropp, "valdeltagandemeningen är borta"
    assert "rostande" not in kropp and "rostberattigade" not in kropp, "talen räknas inte längre i toppsvaret"
    assert "toppsvar-mening" not in kropp, "den redaktionella meningen ligger i ett eget element"


def test_sidhuvudets_ordning():
    """Årväljaren högst upp i sektionen, sedan den redaktionella meningen, sedan statusraden och staplarna."""
    js = JS.read_text("utf-8")
    markup = js[js.index("const MARKUP = `"):js.index('<div id="rutor"')]
    ordning = ['id="topp-etikett"', "<h1>", 'id="arval"', 'id="arval-fel"',
               'id="topp-mening"', 'id="statusrad"', 'id="toppsvar"']
    platser = [markup.index(x) for x in ordning]
    assert platser == sorted(platser), "sidhuvudet ligger i fel ordning"


def test_den_redaktionella_meningen_har_eget_element():
    """Meningen ligger utanför toppsvaret och fylls när konfigen lästs, inte vid varje omritning."""
    js = JS.read_text("utf-8")
    css = CSS.read_text("utf-8")
    assert 'id="topp-mening"' in js, "meningen ligger i markupen från början"
    kropp = js[js.index("async function start()"):]
    kropp = kropp[:kropp.index("\n}\n")]
    assert "#topp-mening" in kropp, "meningen sätts när konfigen är läst"
    assert next((r for r in css.splitlines() if r.startswith(".mp-val .topp-mening {")), None), \
        "meningen har en egen regel"


def test_rubriken_over_staplarna_ar_dampad():
    """"Riksdagsvalet ÅÅÅÅ i Majorna" är en dämpad etikett över staplarna, inte en rubrik i bläck."""
    css = CSS.read_text("utf-8")
    rad = next(r for r in css.splitlines() if r.startswith(".mp-val .toppsvar-rubrik {"))
    assert "color: var(--sten)" in rad, "rubriken är dämpad, som statusraden var"


def test_arvaljaren_bar_sidans_knappstil():
    """Den vita rutan stack ut mot papperet: selecten bär sidans bakgrund och knapparnas mått."""
    css = CSS.read_text("utf-8")
    knapp = next(r for r in css.splitlines() if r.startswith(".mp-val button {"))
    for regel in (".mp-val select {", ".mp-val .arval select {"):
        rad = next(r for r in css.splitlines() if r.startswith(regel))
        assert "var(--papper)" in rad and "#fff" not in rad, f"{regel} bär sidans papper, inte vitt"
        for matt in ("min-height: 44px", "padding: 8px 14px", "border-radius: 4px"):
            assert matt in rad and matt in knapp, f"{regel} matchar inte knappens {matt}"


def test_axeln_visar_valaret_forst_pa_valnatten():
    """Före valdagen stod 26 längst ut på axeln med en tom ring under, utan att säga något. Året kommer
    med när räkningen börjat, och efter valet står det i serien via senasteAr()."""
    js = JS.read_text("utf-8")
    kropp = js[js.index("function histAxelAr("):]
    kropp = kropp[:kropp.index("\n}\n")]
    assert "KONFIG.valnatt" in kropp, "valåret läggs till först på valnatten"
    assert "räknas just nu" in js and "räknas på valnatten" in js, "ringens texter står kvar för valnatten"


def test_axeln_skriver_hela_artal_nar_de_far_plats():
    """Fyra siffror när avståndet mellan två tick räcker, annars två. Antalet år följer konfigen, så
    gränsen mäts i stället för att sättas."""
    js = JS.read_text("utf-8")
    kropp = js[js.index("function histArAxel("):]
    kropp = kropp[:kropp.index("\n}\n")]
    assert "textBredd" in kropp, "årtalens form mäts"
    assert "slice(2)" in kropp, "två siffror är kvar som reserv"


def test_historiksektionen_har_ingen_raknad_mening():
    """"V har gått från 17,2 till 27,2 procent i riksdagsvalet sedan 2006." är borttagen. Redaktionens
    egen mening i konfigen står kvar som möjlighet."""
    js = JS.read_text("utf-8")
    kropp = js[js.index("function histMening("):]
    kropp = kropp[:kropp.index("\n}\n")]
    assert "har gått från" not in kropp, "den räknade meningen är borta"
    assert "historikSerie" not in kropp and "andelTal" not in kropp, "inga tal räknas fram till meningen"
    assert "KONFIG.historik" in kropp, "redaktionens egen mening går fortfarande att sätta"


def test_etiketterna_i_bild_b_har_ingen_ledarlinje():
    """Den korta flärpen ned från punkten till en isärskjuten etikett är borttagen: färgen knyter
    etiketten till sin egen linje."""
    js = JS.read_text("utf-8")
    kropp = js[js.index("function histEtiketter("):]
    kropp = kropp[:kropp.index("\n}\n")]
    assert 's("line"' not in kropp, "ingen ledarlinje ritas"
    assert "py" not in kropp, "punktens y behövs inte längre när linjen är borta"


def test_rakneexemplet_ar_en_fotnot():
    """Räkneexemplet under halvcirkeln är en förklaring ingen behöver läsa: minsta grad på sidan."""
    css = CSS.read_text("utf-8")
    rad = next((r for r in css.splitlines() if r.startswith(".mp-val #mandat-metod {")), None)
    assert rad and "font-size: 13px" in rad, "räkneexemplet står mindre än de vanliga noterna"


def test_arvaljare_i_varje_sektion_som_foljer_aret():
    """Blocket ligger i en iframe hos Beehiiv, där position: sticky är verkningslöst. I stället står en
    synkad väljare överst i varje sektion som följer året, så att året syns var läsaren än befinner sig."""
    js = JS.read_text("utf-8")
    markup = js[js.index("const MARKUP = `"):js.index("\n`;\n")]
    assert markup.count('class="arval"') == 5, "sidhuvudet plus de fyra sektioner som följer året"
    for sek in ("riksdag", "karta-sektion", "jamforelse", "rostdelning"):
        bit = markup[markup.index('<section id="%s"' % sek):]
        bit = bit[:bit.index("</section>")]
        assert 'class="arval"' in bit, f"{sek} saknar årväljare"
        assert 'class="arval-fel"' in bit, f"{sek} saknar felrad vid sin väljare"
    hist = markup[markup.index('<section id="historik"'):]
    assert 'class="arval"' not in hist[:hist.index("</section>")], \
        "historiksektionen följer inte årväljaren, utom konturkartorna"
    assert "function renderArval(" in js, "väljarna byggs på ett ställe"
    kropp = js[js.index("async function byteAr("):]
    kropp = kropp[:kropp.index("\n}\n")]
    assert "arvalValjare()" in kropp, "alla väljare låses under laddningen, inte bara den som användes"
    assert "arvalFelRuta" in kropp, "felet står vid den väljare läsaren använde"


def test_omritade_distrikt_tonas_i_konturkartorna():
    """Elva av 23 distrikt fick nya gränser mellan 2022 och 2026, men bitarna är så små att konturerna ser
    lika ut. De tonas därför. Jämförelsen görs på distriktskod, area och omskrivande rektangel; två år utan
    gemensamma koder har inget att jämföra och får ingen toning."""
    js = JS.read_text("utf-8")
    assert "function jamforDistrikt(" in js, "jämförelsen ligger i en egen hjälpare"
    kropp = js[js.index("function jamforDistrikt("):]
    kropp = kropp[:kropp.index("\n}\n")]
    assert "area_km2" in kropp and "distriktRam" in kropp, "både area och ram jämförs"
    assert "properties.kod" in kropp, "bara koder som finns i båda åren jämförs"
    karta = js[js.index("function histKartor()"):]
    karta = karta[:karta.index("\n}\n")]
    assert "omritade.has" in karta, "de omritade distrikten får en ton i båda kartorna"
    assert "i båda kartorna" in karta, "noten säger att samma distrikt tonas i båda kartorna"
    assert "rakneord(omritade.size)" in karta, "små tal skrivs ut i löptext, inte som siffra"
    assert 'är tonat" : "är tonade"' in karta, "noten böjer sig efter antalet"
    assert "omritade.size" in karta, "noten nämner tonen bara när något faktiskt är tonat"
