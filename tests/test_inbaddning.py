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
    assert k["ar"] == ["2022"] and k["standardAr"] == "2022" and k["valnatt"] is False
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


def test_kortets_forandringsrad_styrs_av_swingfilen():
    js = JS.read_text("utf-8")
    assert "function hurAndrat(" in js and "ej_jamforbara" in js and "kohort" in js
    assert "Hur har det ändrats" in js
    assert 'h("h4", { class: "andrat-rubrik" }' in js, "rubriken är en rubrik, inte ett stycke"
    # Riktiga mellanslag mellan talen: raden ska få brytas mellan dem, inte rinna ut ur kortet på smala telefoner.
    assert '{ class: "andrat-tal" }, `${a.p} ${pe(diff[a.p])}`), " "' in js, "talen ska skiljas av ett mellanslag"


def test_rubriknivaerna_skyddas_mot_vardsidans_stilar():
    """Varje rubriknivå grafiken använder får färg och form uttryckligen, annars läcker värdsidans stilar in."""
    js = JS.read_text("utf-8")
    css = CSS.read_text("utf-8")
    nivaer = set(re.findall(r'h\("(h[1-6])"', js)) | set(re.findall(r"<(h[1-6])[ >]", js))
    assert "h4" in nivaer, "kortets rubrik ska vara en h4"
    skydd = next(r for r in css.splitlines() if "text-shadow: none" in r)
    farg = next(r for r in css.splitlines() if r.startswith(".mp-val h1,") and "color: var(--black)" in r)
    for niva in sorted(nivaer):
        assert f".mp-val {niva}," in skydd or f".mp-val {niva} " in skydd, f"{niva} saknas i skyddsregeln"
        assert f".mp-val {niva}," in farg or f".mp-val {niva} " in farg, f"{niva} saknar uttrycklig färg"


def test_historiksektionen_finns_och_foljer_kartans_val():
    """Majorna sedan 2006: egen sektion utan knapprad, reserverad höjd, laddad ur data/historik.js."""
    js = JS.read_text("utf-8")
    css = CSS.read_text("utf-8")
    assert 'id="historik"' in js and "function renderHistorik()" in js and "function histLinjer(" in js and "function histTalrad(" in js
    assert 'laddaSkript("historik")' in js and 'laddaSkript("distrikt_2006")' in js
    assert 'id="hist-val"' not in js and "hist-knappar" not in js, "sektionen har inga egna valknappar"
    assert ".hist-bild { min-height" in css, "höjden är reserverad innan datan finns"
    assert (ROT / "data" / "historik.js").exists()
    # X-axeln tar nästa valår ur konfigen, så att 2026 står som tom ring redan före valdagen.
    kropp = js[js.index("function histAxelAr("):]
    assert "KONFIG.valdag" in kropp[:kropp.index("\n}")], "histAxelAr lägger till nästa valår ur KONFIG.valdag"
    assert "räknas på valnatten." in js, "ett år utan punkt får talraden räknas på valnatten"


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


def test_historikbilden_reserverar_hojd_och_talraden_far_brytas():
    """Höjden följer desktoptröskeln 600 px, och talraden bryts i stället för att klippas."""
    css = CSS.read_text("utf-8")
    assert re.search(r"\.hist-bild\s*\{[^}]*min-height:\s*280px", css), "höjden är reserverad innan datan finns"
    kroppar = "\n".join(container_kroppar(css, "min-width: 600px"))
    assert re.search(r"\.hist-bild\s*\{[^}]*min-height:\s*320px", kroppar), "desktophöjden gäller från 600 px, samma tröskel som arDesktop"
    assert re.search(r"\.hist-bild-b\s*\{[^}]*min-height:\s*160px", kroppar), "bild B ärver annars bild A:s reservation"
    talrad = re.search(r"\.mp-val \.hist-talrad\s*\{([^}]*)\}", css)
    assert talrad, "talraden har en egen regel"
    assert "nowrap" not in talrad.group(1) and "overflow" not in talrad.group(1), "talraden bryts i stället för att klippas"


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
    assert "Valdeltagande i Majorna" not in fakta, "valdeltagandet står i bild B, inte i Om siffrorna"
    assert "Byggd av Majposten" not in fakta, "avsändaren står i sidfoten, inte i listan"
