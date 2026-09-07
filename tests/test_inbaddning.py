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
    """Statusraden, toppsvaret och årsknapparna tar plats redan innan datan kommer, så att sidhuvudet inte hoppar."""
    css = CSS.read_text("utf-8")
    js = JS.read_text("utf-8")
    for regel in (".mp-val .statusrad", ".mp-val .toppsvar", ".mp-val.har-mening .toppsvar", ".mp-val #arval"):
        rad = next((r for r in css.splitlines() if r.startswith(regel + " {")), None)
        assert rad and "min-height:" in rad, f"{regel} saknar reserverad höjd"
    assert '"har-mening"' in js, "klassen har-mening sätts när konfigen har en mening"
    assert '$("#arval").hidden' in js, "årsknapparnas rad tar plats så snart konfigen är läst"


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
    # X-axeln tar nästa valår ur konfigen, så att 2026 står som tom ring redan före valdagen.
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
    assert "Samma yta, fler distrikt" in js, "noten säger vad kartorna visar"
    assert "Valhemligheten gäller per distrikt" in js, "meningen stänger frågan om ålder"
    fakta = js[js.index("function renderFakta()"):]
    assert "Avgränsning:" in fakta, "listan börjar med avgränsningen"
    assert "Andel = partiets röster delat med giltiga röster." in fakta, "andelsdefinitionen står kvar"
    assert "Valdeltagande i Majorna" not in fakta, "valdeltagandet står i bild B, inte i Om siffrorna"
    assert "Byggd av Majposten" not in fakta, "avsändaren står i sidfoten, inte i listan"


def test_arvaljaren_ar_en_dropdown():
    """Årväljaren är en <select> med etiketten på selecten, inte en knapprad med role=group."""
    js = JS.read_text("utf-8")
    css = CSS.read_text("utf-8")
    assert 'id: "arval-select"' in js, "selecten har ett eget id"
    assert '"aria-label": "Välj valår"' in js, "etiketten sitter på selecten"
    markup = next(r for r in js.splitlines() if 'id="arval"' in r)
    assert 'role="group"' not in markup and 'aria-label' not in markup, "behållaren har varken role eller etikett kvar"
    rad = next((r for r in css.splitlines() if r.strip().startswith(".mp-val #arval select {")), None)
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
    assert ".slice(0, 4)" not in kropp, "fyra rader är inte längre fast"
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
