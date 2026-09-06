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


def test_js_renderar_i_container_utan_globala_dokumentreferenser():
    js = JS.read_text("utf-8")
    assert "document.currentScript" in js, "basadressen för data ska tas från skriptets egen src"
    assert "document.body" not in js
    assert "document.querySelector(" not in js and "document.getElementById(" not in js
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
    assert (ROT / "data" / "distrikt_2022.js").exists() and not (ROT / "data" / "distrikt.js").exists()
