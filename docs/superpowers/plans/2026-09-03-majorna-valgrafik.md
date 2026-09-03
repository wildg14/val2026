# Så röstade Majorna - implementationsplan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** En statisk sida (index.html + data/) som visar valresultatet 2022 per valdistrikt i Majorna, plus skript som bygger datan ur källfilerna och tar in 2026 års siffror utan kodändring.

**Architecture:** Python-skript (openpyxl, pyproj, shapely) läser xlsx och GeoJSON, verifierar summor och skriver `data/*.json` samt identiska `data/*.js`. `index.html` laddar JS-filerna utifrån en konfigrad och ritar allt (karta, halvcirkel, staplar, lutningsdiagram) som inline-SVG utan bibliotek.

**Tech Stack:** Python 3.12 i `.venv` (uv), openpyxl, pyproj, shapely, pytest. Vanilla JS/CSS/SVG. Ingen byggkedja för sidan.

Spec: `docs/superpowers/specs/2026-09-03-majorna-valgrafik-design.md`. Projektet är inte ett git-repo och användaren har inte bett om git, så commit-stegen är ersatta med "kör testerna".

---

## Filstruktur

| Fil | Ansvar |
|---|---|
| `scripts/valmyndigheten.py` | Partimappning, läsning av kurerad xlsx, parser för Valmyndighetens rådatafiler, aggregat |
| `scripts/mandat.py` | Jämkade uddatalsmetoden med spärr |
| `scripts/geo.py` | Zip -> 23 polygoner i WGS84 med etikettpunkt |
| `scripts/schema.py` | Bygger `valdata`-objektet, skriver `.json` + `.js`, swing |
| `scripts/kontrollera.py` | Stämmer av `valdata_2022.json` mot xlsx, avbryter vid diff |
| `scripts/bygg_data.py` | Orkestrerar 2022-bygget |
| `scripts/uppdatera_2026.py` | Rådata 2026 -> `valdata_2026` + `swing_2026`, `--repetera`, `--csv` |
| `scripts/hamta_bakgrund.py` | Overpass -> `data/bakgrund.json/.js` |
| `index.html` | Sidan |
| `tests/test_mandat.py`, `tests/test_valmyndigheten.py`, `tests/test_geo.py`, `tests/test_schema.py`, `tests/test_kontrollera.py`, `tests/test_uppdatera.py` | pytest |
| `README.md` | Körordning, valnatten |

Kör tester med `.venv/bin/python -m pytest -q`.

---

### Task 1: mandat.py

**Files:** Create `scripts/mandat.py`, `tests/test_mandat.py`, `scripts/__init__.py` (tom), `tests/__init__.py` (tom).

- [ ] **Step 1: Skriv testet**

```python
# tests/test_mandat.py
from scripts.mandat import jamkade_uddatal

MAJORNA_RD_2022 = {"V": 5793, "S": 5515, "MP": 3349, "SD": 2152, "M": 1894,
                   "C": 910, "L": 886, "KD": 491, "Övriga": 318}

def test_majornas_riksdag_2022():
    m = jamkade_uddatal(MAJORNA_RD_2022, 349)
    assert m == {"V": 99, "S": 94, "MP": 57, "SD": 37, "M": 32, "C": 15, "L": 15}
    assert sum(m.values()) == 349

def test_sparr_raknas_pa_alla_giltiga_roster():
    # KD har 491/21308 = 2,3 % -> utanför. Övriga räknas i nämnaren men får aldrig mandat.
    m = jamkade_uddatal(MAJORNA_RD_2022, 349)
    assert "KD" not in m and "Övriga" not in m

def test_forsta_delningstal():
    # Med 1,0 som första delningstal (ren uddatalsmetod) ska litet parti gynnas.
    r = {"A": 100, "B": 8}
    assert jamkade_uddatal(r, 10, sparr=0, forsta_delningstal=1.0) == {"A": 9, "B": 1}
    assert jamkade_uddatal(r, 10, sparr=0, forsta_delningstal=1.2) == {"A": 10}
```

- [ ] **Step 2: Kör, förvänta ImportError**

- [ ] **Step 3: Implementera**

```python
# scripts/mandat.py
"""Jämkade uddatalsmetoden (modified Sainte-Laguë) med procentspärr."""

def jamkade_uddatal(roster, mandat, sparr=0.04, forsta_delningstal=1.2, exkludera=("Övriga",)):
    totalt = sum(roster.values())
    kandidater = {p: r for p, r in roster.items()
                  if p not in exkludera and totalt and r / totalt >= sparr}
    fordelning = {p: 0 for p in kandidater}
    for _ in range(mandat):
        def kvot(p):
            n = fordelning[p]
            return kandidater[p] / (forsta_delningstal if n == 0 else 2 * n + 1)
        vinnare = max(kandidater, key=kvot)
        fordelning[vinnare] += 1
    return {p: n for p, n in fordelning.items() if n > 0}
```

- [ ] **Step 4: Kör testet, PASS**

---

### Task 2: valmyndigheten.py - partier och kurerad xlsx

**Files:** Create `scripts/valmyndigheten.py`, `tests/test_valmyndigheten.py`.

- [ ] **Step 1: Test**

```python
# tests/test_valmyndigheten.py
from pathlib import Path
import pytest
from scripts import valmyndigheten as vm

ROT = Path(__file__).resolve().parents[1]
XLSX = ROT / "majorna-valresultat-2022.xlsx"

def test_partikod():
    assert vm.partikod(" Arbetarepartiet-Socialdemokraterna") == "S"
    assert vm.partikod("Liberalerna (tidigare Folkpartiet)") == "L"
    assert vm.partikod(" Demokraterna") == "D"
    assert vm.partikod("Piratpartiet") is None

def test_las_kurerad_svalebo():
    k = vm.las_kurerad(XLSX)
    d = k["distrikt"]["14800526"]
    assert d["namn"] == "Svalebo"
    assert d["rd"] == {"V": 179, "S": 217, "MP": 114, "SD": 102, "M": 60, "C": 43, "L": 42, "KD": 25, "Övriga": 15}
    assert d["giltiga"]["rd"] == 797 and d["rostande"]["rd"] == 805 and d["rostberattigade"]["rd"] == 1073
    assert d["kf"]["K"] == 10
    assert len(k["distrikt"]) == 23
    assert k["total"]["rd"]["roster"]["V"] == 5793
    assert k["sammanfattning"]["goteborg"]["rd"]["andel"]["V"] == pytest.approx(0.1284978810, abs=1e-9)
    assert k["sammanfattning"]["riket"]["rd"]["valdeltagande"] == pytest.approx(0.842118659, abs=1e-9)
```

- [ ] **Step 2: Kör, FAIL**

- [ ] **Step 3: Implementera**

```python
# scripts/valmyndigheten.py (del 1)
import openpyxl

VAL = {"rd": "Riksdag", "rf": "Region", "kf": "Kommun"}
PARTIER = {
    "V":  ("Vänsterpartiet", ["vänsterpartiet"]),
    "S":  ("Socialdemokraterna", ["arbetarepartiet-socialdemokraterna", "socialdemokraterna"]),
    "MP": ("Miljöpartiet", ["miljöpartiet de gröna", "miljöpartiet"]),
    "SD": ("Sverigedemokraterna", ["sverigedemokraterna"]),
    "M":  ("Moderaterna", ["moderaterna"]),
    "C":  ("Centerpartiet", ["centerpartiet"]),
    "L":  ("Liberalerna", ["liberalerna (tidigare folkpartiet)", "liberalerna", "folkpartiet liberalerna"]),
    "KD": ("Kristdemokraterna", ["kristdemokraterna"]),
    "D":  ("Demokraterna", ["demokraterna"]),
    "FI": ("Feministiskt initiativ", ["feministiskt initiativ"]),
    "K":  ("Kommunistiska Partiet", ["kommunistiska partiet"]),
}
NYCKELPARTIER = {"rd": ["V","S","MP","SD","M","C","L","KD"],
                 "rf": ["V","S","MP","M","SD","L","C","KD","D","FI"],
                 "kf": ["V","S","MP","M","SD","L","D","C","KD","FI","K"]}
OVRIGA = "Övriga"
MAJORNA_KODER = [str(14800526 + i) for i in range(23)]

def partikod(etikett):
    e = str(etikett).strip().lower()
    for kod, (_, etiketter) in PARTIER.items():
        if e in etiketter:
            return kod
    return None

def las_kurerad(path):
    wb = openpyxl.load_workbook(path, data_only=True)
    distrikt, total = {}, {}
    for val in VAL:
        ws = wb[val.upper()]
        rader = [r for r in ws.iter_rows(values_only=True) if any(v is not None for v in r)]
        huvud = [str(h).strip() for h in rader[0]]
        partier = huvud[2:huvud.index("Giltiga röster")]
        for r in rader[1:]:
            post = dict(zip(huvud, r))
            roster = {p: int(post[p]) for p in partier}
            if post["Distriktskod"] is None:
                total[val] = {"roster": roster, "giltiga": int(post["Giltiga röster"]),
                              "rostande": int(post["Röstande"]), "rostberattigade": int(post["Röstberättigade"])}
                continue
            kod = str(post["Distriktskod"]).strip()
            d = distrikt.setdefault(kod, {"kod": kod, "namn": str(post["Valdistrikt"]).strip(),
                                          "giltiga": {}, "rostande": {}, "rostberattigade": {}})
            d[val] = roster
            d["giltiga"][val] = int(post["Giltiga röster"])
            d["rostande"][val] = int(post["Röstande"])
            d["rostberattigade"][val] = int(post["Röstberättigade"])
    return {"distrikt": distrikt, "total": total, "sammanfattning": _las_sammanfattning(wb["Sammanfattning"])}
```

`_las_sammanfattning` går igenom fliken sektion för sektion (rubrikrad "Riksdagsvalet", "Regionvalet ...", "Kommunvalet ..."), tar kolumnerna "Andel Göteborg" och "Andel Riket"/"Andel Västra Götaland" per parti och raden "Valdeltagande" och returnerar `{"goteborg": {val: {"andel": {...}, "valdeltagande": x}}, "riket": {...}}`. För KF saknas riket: nyckeln utelämnas.

- [ ] **Step 4: Kör testet, PASS**

---

### Task 3: valmyndigheten.py - rådataparser

**Files:** Modify `scripts/valmyndigheten.py`, `tests/test_valmyndigheten.py`.

- [ ] **Step 1: Test** (hoppar över om råfilen saknas)

```python
RAD_RD = ROT / "Roster-per-distrikt-slutligt-antal-roster-inklusive-totalt-valdeltagande-riksdagsvalet-2022.xlsx"

@pytest.mark.skipif(not RAD_RD.exists(), reason="rådatafil saknas")
def test_rafil_matchar_kurerad():
    ra = vm.las_rafil(RAD_RD, koder=vm.MAJORNA_KODER)
    assert ra["val"] == "rd"
    d = vm.till_distrikt(ra["distrikt"]["14800526"], "rd")
    k = vm.las_kurerad(XLSX)["distrikt"]["14800526"]
    assert d["roster"] == k["rd"]
    assert (d["giltiga"], d["rostande"], d["rostberattigade"]) == (797, 805, 1073)
    assert ra["distrikt"]["14800526"]["namn"] == "Västra Centrum, Svalebo"
    # aggregat för Göteborg och riket
    agg = vm.aggregat_andelar(ra, "rd")
    assert agg["goteborg"]["andel"]["V"] == pytest.approx(0.1284978810, abs=1e-9)
    assert agg["riket"]["andel"]["S"] == pytest.approx(0.3032545689, abs=1e-9)
    assert agg["riket"]["valdeltagande"] == pytest.approx(0.842118659, abs=1e-9)

def test_validera_format_avvisar_fel_huvud():
    with pytest.raises(vm.FormatFel):
        vm.validera_huvud(["Kommun", "Parti", "Röster"])
```

- [ ] **Step 2: Kör, FAIL**

- [ ] **Step 3: Implementera**

Nyckelpunkter: `las_rafil(path, koder=None)` öppnar i read_only, hittar bladet vars namn börjar med `roster_`, validerar huvudet (`validera_huvud`), itererar alla rader. För varje rad: `kod = str(rad[kodkol]).strip()`, `etikett = str(rad[partikol]).strip().lower()`. Rader med etikett `summa giltiga röster` -> `giltiga`, `valdeltagande` -> `rostande`, i `OGILTIGA` -> `ogiltiga`, `övriga anmälda partier` -> läggs på partiet `Övriga`, annars parti med etiketten som nyckel. Aggregat samlas alltid för hela filen (riket), för rader med `Kommun == "Göteborg"` (goteborg) och för RF för rader med `Län == "Västra Götaland"` (region). `till_distrikt(post, val)` mappar etiketter till koder med `partikod`, lägger allt som inte är nyckelparti för valet i `Övriga`, och kastar `SummaFel` om `sum(roster) != giltiga` eller `giltiga + ogiltiga != rostande`. `aggregat_andelar(ra, val)` returnerar andelar (parti/giltiga) och valdeltagande (rostande/rostberattigade) för `riket`, `goteborg` och (rf) `region`.

Exempel på Göteborg-rad i RD-filen: `(' RD', 'RD-14-80-0526', 'Västra Götaland', 'Västra Götalandsregionen'?, 'Göteborg', ' 14800526', 'Västra Centrum, Svalebo', ' 16', 'Göteborgs kommun', ' Vänsterpartiet', 179, 1073)`. Kolumnindex tas ur huvudet, inte hårdkodas.

- [ ] **Step 4: Kör testet, PASS** (RF-filen har "Region"-kolumnen med regionens namn, kontrollera värdet för Göteborg i testkörningen och använd Län-kolumnen om den är stabilare)

---

### Task 4: geo.py

**Files:** Create `scripts/geo.py`, `tests/test_geo.py`.

- [ ] **Step 1: Test**

```python
# tests/test_geo.py
from pathlib import Path
from shapely.geometry import shape
from scripts import geo
from scripts.valmyndigheten import MAJORNA_KODER

ROT = Path(__file__).resolve().parents[1]

def test_distrikt_geojson():
    fc = geo.las_distrikt(ROT / "valdistrikt-vastra-gotalands-lan.zip", MAJORNA_KODER)
    assert fc["type"] == "FeatureCollection" and len(fc["features"]) == 23
    koder = sorted(f["properties"]["kod"] for f in fc["features"])
    assert koder == sorted(MAJORNA_KODER)
    for f in fc["features"]:
        g = shape(f["geometry"])
        assert g.is_valid and g.geom_type == "Polygon"
        lon, lat = f["properties"]["etikett"]
        assert 11.88 < lon < 11.95 and 57.67 < lat < 57.71
        assert g.contains(shape({"type": "Point", "coordinates": [lon, lat]}))
        assert not f["properties"]["namn"].startswith("Västra Centrum")
    assert fc["bbox"][0] < fc["bbox"][2]
```

- [ ] **Step 2: Kör, FAIL**

- [ ] **Step 3: Implementera**

```python
# scripts/geo.py
import json, zipfile
from pyproj import Transformer
from shapely.geometry import shape, mapping
from shapely.ops import polylabel

def las_distrikt(zip_path, koder, decimaler=6):
    with zipfile.ZipFile(zip_path) as z:
        namn = [n for n in z.namelist() if n.lower().endswith(".json")][0]
        gj = json.loads(z.read(namn).decode("utf-8"))
    tr = Transformer.from_crs("EPSG:3006", "EPSG:4326", always_xy=True)
    vill = set(koder)
    features = []
    for ft in gj["features"]:
        kod = str(ft["properties"]["Lkfv"]).strip()
        if kod not in vill:
            continue
        g = shape(ft["geometry"])
        if g.geom_type == "MultiPolygon":
            g = max(g.geoms, key=lambda p: p.area)
        ringar = [_transformera(r, tr, decimaler) for r in [g.exterior, *g.interiors]]
        poly = shape({"type": "Polygon", "coordinates": ringar}).buffer(0)
        etikett = polylabel(poly, tolerance=1e-5)
        features.append({"type": "Feature", "properties": {
            "kod": kod, "namn": kort_namn(ft["properties"]["Vdnamn"]),
            "etikett": [round(etikett.x, decimaler), round(etikett.y, decimaler)],
            "area_km2": round(g.area / 1e6, 4)},
            "geometry": mapping(poly)})
    saknas = vill - {f["properties"]["kod"] for f in features}
    if saknas:
        raise ValueError(f"Distrikt saknas i geodatan: {sorted(saknas)}")
    features.sort(key=lambda f: f["properties"]["kod"])
    xs = [c[0] for f in features for c in f["geometry"]["coordinates"][0]]
    ys = [c[1] for f in features for c in f["geometry"]["coordinates"][0]]
    return {"type": "FeatureCollection", "bbox": [min(xs), min(ys), max(xs), max(ys)], "features": features}

def kort_namn(vdnamn):
    return str(vdnamn).split(", ", 1)[-1].strip()

def _transformera(ring, tr, decimaler):
    return [[round(x, decimaler), round(y, decimaler)] for x, y in (tr.transform(*p) for p in ring.coords)]
```

- [ ] **Step 4: Kör testet, PASS**

---

### Task 5: schema.py - valdata-objekt, JS-filer, swing

**Files:** Create `scripts/schema.py`, `tests/test_schema.py`.

- [ ] **Step 1: Test**

```python
# tests/test_schema.py
import json
from scripts import schema

def test_skriv_json_och_js(tmp_path):
    obj = {"a": [1, 2], "å": "ö"}
    schema.skriv(tmp_path / "x", obj)
    assert json.loads((tmp_path / "x.json").read_text("utf-8")) == obj
    js = (tmp_path / "x.js").read_text("utf-8")
    assert js.startswith('window.MAJPOSTEN=window.MAJPOSTEN||{data:{}};window.MAJPOSTEN.data["x"]=')
    assert schema.las_js(tmp_path / "x.js") == obj

def test_swing():
    bas = {"distrikt": [{"kod": "1", "rd": {"V": 20, "S": 80}, "giltiga": {"rd": 100}}]}
    ny = {"distrikt": [{"kod": "1", "raknat": True, "rd": {"V": 30, "S": 70}, "giltiga": {"rd": 100}}]}
    s = schema.swing(ny, bas)
    assert s["distrikt"]["1"]["rd"] == {"V": 10.0, "S": -10.0}
    assert s["bas"] == 2022 or "bas" in s

def test_bygg_valdata_aggregat():
    d = [{"kod": "1", "namn": "A", "raknat": True, "rd": {"V": 1, "S": 3}, "rf": {}, "kf": {},
          "giltiga": {"rd": 4}, "rostande": {"rd": 5}, "rostberattigade": {"rd": 10}},
         {"kod": "2", "namn": "B", "raknat": False, "rd": {}, "rf": {}, "kf": {},
          "giltiga": {}, "rostande": {}, "rostberattigade": {}}]
    v = schema.bygg_valdata(2026, d, status="preliminar")
    assert v["aggregat"]["majorna"]["rd"] == {"roster": {"V": 1, "S": 3}, "giltiga": 4, "rostande": 5, "rostberattigade": 10}
    assert v["meta"]["valnatt"] == {"raknade": 1, "totalt": 2}
```

- [ ] **Step 2: Kör, FAIL**

- [ ] **Step 3: Implementera** `skriv(stam, obj)`, `las_js(path)`, `bygg_valdata(ar, distriktlista, status, jamforelser=None, mandat=None, uppdaterad=None)`, `swing(ny, bas)` (procentenheter, en decimal, bara räknade distrikt, plus `majorna`-aggregat). JS-filen: `window.MAJPOSTEN=window.MAJPOSTEN||{data:{}};window.MAJPOSTEN.data["<stam>"]=<json>;`.

- [ ] **Step 4: PASS**

---

### Task 6: kontrollera.py och bygg_data.py

**Files:** Create `scripts/kontrollera.py`, `scripts/bygg_data.py`, `tests/test_kontrollera.py`.

- [ ] **Step 1: Test för kontrollera**

```python
# tests/test_kontrollera.py
import json, subprocess, sys
from pathlib import Path
ROT = Path(__file__).resolve().parents[1]

def test_kontrollera_upptacker_manipulerad_siffra(tmp_path):
    src = ROT / "data" / "valdata_2022.json"
    if not src.exists():
        import pytest; pytest.skip("bygg data först")
    v = json.loads(src.read_text("utf-8"))
    v["distrikt"][3]["rd"]["V"] += 1
    p = tmp_path / "valdata_2022.json"; p.write_text(json.dumps(v), "utf-8")
    r = subprocess.run([sys.executable, "scripts/kontrollera.py", str(p), "majorna-valresultat-2022.xlsx"], cwd=ROT, capture_output=True, text=True)
    assert r.returncode != 0 and "14800529" in r.stdout + r.stderr

def test_kontrollera_godkanner_riktig_fil():
    src = ROT / "data" / "valdata_2022.json"
    if not src.exists():
        import pytest; pytest.skip("bygg data först")
    r = subprocess.run([sys.executable, "scripts/kontrollera.py", str(src), "majorna-valresultat-2022.xlsx"], cwd=ROT, capture_output=True, text=True)
    assert r.returncode == 0
```

- [ ] **Step 2: Implementera kontrollera.py**: läser JSON och xlsx (`las_kurerad`), jämför per distrikt, val, parti samt giltiga/rostande/rostberattigade; jämför kolumnsummor mot totalraden; jämför `aggregat.majorna` mot totalraden; kontrollerar att `.js`-filen bredvid innehåller identisk data. Skriver varje diff som en rad `DIFF 14800529 rd V json=255 xlsx=254` och avslutar med kod 1 om någon diff finns, annars `OK: 23 distrikt, 3 val, 0 diffar`.

- [ ] **Step 3: Implementera bygg_data.py** enligt specen: argparse med standardsökvägar, stegen 1 till 4, mandat ur `Mandatfordelning-jamforelser-mellan-2018-och-2022.xlsx` (fliken Riksdag, kolumn 2022, namn -> partikod), kontroll 5 om råfilerna finns, skriver `data/valdata_2022.json/.js`, `data/distrikt.geojson/.js`, kör kontrollera som subprocess, skriver ut filstorlekar.

- [ ] **Step 4: Kör `.venv/bin/python scripts/bygg_data.py`, förvänta `OK`, kör pytest, PASS**

---

### Task 7: hamta_bakgrund.py

**Files:** Create `scripts/hamta_bakgrund.py`.

- [ ] **Step 1: Implementera**: bbox ur `data/distrikt.geojson` + 0,004 grader marginal (0,008 i longitud). Overpass-fråga: highway i {motorway, trunk, primary, secondary, tertiary, residential, living_street, pedestrian, unclassified, *_link}, railway=tram, node railway=tram_stop, natural=water (way + relation), leisure=park, node place in {suburb, locality}. Linjer: transformera till EPSG:3006, `simplify(2.0)`, klipp mot bbox, tillbaka till WGS84 med 5 decimaler. Vatten-relationer: `linemerge` + `polygonize` av outer-medlemmar. Hållplatser: gruppera på namn, medelpunkt. Skriv `data/bakgrund.json/.js` via `schema.skriv`. Vid nätverksfel: skriv felet och avsluta med kod 2 utan att röra befintlig fil.

- [ ] **Step 2: Kör, kontrollera att `data/bakgrund.json` är under 250 kB och innehåller hållplatsen "Mariaplan".**

---

### Task 8: index.html

**Files:** Create `index.html`.

Sektioner i ordning: `<header>` rubrik + ingress + årväljare + valnattsbanderoll, `<section id="riksdag">` halvcirkel, `<section id="karta">` flikar + växel + SVG + legend, `<section id="panel">`, `<section id="rostdelning">`, `<section id="fakta">`, `<footer>`.

- [ ] **Step 1: Konfig och laddning**

```js
const KONFIG = { ar: ["2022"], standardAr: "2022", valnatt: false,
                 prenumerera: "https://majposten.se/subscribe" };
function laddaSkript(namn) {
  return new Promise((ok, fel) => {
    const s = document.createElement("script");
    s.src = "data/" + namn + ".js"; s.onload = () => ok(window.MAJPOSTEN.data[namn]); s.onerror = () => fel(namn);
    document.head.appendChild(s);
  });
}
// laddar valdata_{år} för alla år, distrikt, och försöker bakgrund + swing_{år} (fel ignoreras)
```

- [ ] **Step 2: Partier och format**

```js
const PARTIER = {
  V:{namn:"Vänsterpartiet",farg:"#9B1B30",text:"#fff"}, S:{namn:"Socialdemokraterna",farg:"#E3312D",text:"#fff"},
  MP:{namn:"Miljöpartiet",farg:"#5E9E3E",text:"#fff"}, C:{namn:"Centerpartiet",farg:"#2E8B57",text:"#fff"},
  L:{namn:"Liberalerna",farg:"#6DA9DC",text:"#2A241E"}, KD:{namn:"Kristdemokraterna",farg:"#1D2F6F",text:"#fff"},
  M:{namn:"Moderaterna",farg:"#2B6DB5",text:"#fff"}, SD:{namn:"Sverigedemokraterna",farg:"#E2C13B",text:"#2A241E"},
  D:{namn:"Demokraterna",farg:"#163A5E",text:"#fff"}, FI:{namn:"Feministiskt initiativ",farg:"#CF2A7B",text:"#fff"},
  K:{namn:"Kommunistiska Partiet",farg:"#7A1F1F",text:"#fff"}, "Övriga":{namn:"Övriga partier",farg:"#A79C8E",text:"#2A241E"}
};
const SPEKTRUM = ["V","S","MP","C","L","KD","M","SD"];   // halvcirkelns ordning
const procent = x => (x*100).toLocaleString("sv-SE",{minimumFractionDigits:1,maximumFractionDigits:1}) + " %";
const tal = n => n.toLocaleString("sv-SE");
```

- [ ] **Step 3: Projektion och karta**

```js
function projektion(bbox, bredd) {            // WGS84 -> SVG-koordinater, ekvirektangulär med cos(lat)
  const [w,s,e,n] = bbox, lat0 = (s+n)/2, kx = Math.cos(lat0*Math.PI/180);
  const skala = bredd / ((e-w)*kx);
  const hojd = (n-s)*skala;
  return { hojd, till: ([lon,lat]) => [ (lon-w)*kx*skala, (n-lat)*skala ] };
}
```
Polygoner: `<path d="M x y L ... Z" role="button" tabindex="0" data-kod=... aria-label=...>`. Etiketter vid `etikett`-punkten: partibokstav och procent (bara bokstav om `area_km2 < 0.06`). Bakgrund (om laddad): parker `#E4E8DC`, vatten `#DCE3E6`, gator `#FFFFFF` med bredd efter typ, spårväg streckad `#8C3B2B`-ton, hållplatser små cirklar + namn 10 px i sten-färg, stadsdelsnamn versaler 11 px. Klick/tap/Enter/mellanslag -> `valjDistrikt(kod)`.

- [ ] **Step 4: Halvcirkel**

```js
function halvcirkelPlatser(n, rader = 8, r0 = 0.42, r1 = 1.0) {
  const radier = Array.from({length: rader}, (_, i) => r0 + (r1 - r0) * i / (rader - 1));
  const summa = radier.reduce((a,b)=>a+b,0);
  let per = radier.map(r => Math.round(n * r / summa));
  let diff = n - per.reduce((a,b)=>a+b,0); per[per.length-1] += diff;
  const platser = [];
  per.forEach((k, i) => { for (let j = 0; j < k; j++) {
    const v = Math.PI - Math.PI * (j + 0.5) / k;      // vänster -> höger
    platser.push({ x: Math.cos(v) * radier[i], y: -Math.sin(v) * radier[i], v });
  }});
  platser.sort((a, b) => b.v - a.v);
  return platser;
}
```
Tilldelning: block i `SPEKTRUM`-ordning. Två knappar `role="radio"` för lägena. Byte sätter `fill` på varje `<circle>`; CSS `circle{transition:fill .6s}` med `transition-delay: calc(var(--i) * 1.2ms)`. `@media (prefers-reduced-motion: reduce){circle{transition:none}}`. IntersectionObserver kör övergången verklig -> Majorna första gången.

- [ ] **Step 5: Panel, tabell, röstdelning, fakta**: staplar som `<div>`-rader (namn, stapel med bredd = andel/skalmax, Majorna-snitt som lodrät `<span>`, procenttext). Skalmax = max andel i laddad data, uppåt till närmaste 5 %. Tabell med klickbara kolumnhuvuden. Lutningsdiagram som SVG med två kolumner. Fakta ur `aggregat`.

- [ ] **Step 6: Valnattsläge**: om `KONFIG.valnatt`: banderoll med `meta.valnatt.raknade`/`totalt` och `meta.uppdaterad`; distrikt med `raknat=false` fylls `#DDD5C6`, ingen etikett, aria-label "inte räknat än"; panelen visar "Inte räknat än" och 2022 års staplar dämpade om 2022 finns laddat. Årväljare visas om `KONFIG.ar.length > 1`.

- [ ] **Step 7: Verifiera i webbläsare** (`.claude/launch.json` med `python3 -m http.server 8765`): skärmdump 390 px, klicka alla 23 paths via JS och kontrollera panelrubriken, stickprov Mariaplan RD V 34,5 %, Skytteskogen KF MP 15,2 %, Svalebo RF V 32,2 %.

---

### Task 9: uppdatera_2026.py

**Files:** Create `scripts/uppdatera_2026.py`, `tests/test_uppdatera.py`.

- [ ] **Step 1: Test**

```python
# tests/test_uppdatera.py
import json, subprocess, sys
from pathlib import Path
import pytest
ROT = Path(__file__).resolve().parents[1]
RD = ROT / "Roster-per-distrikt-slutligt-antal-roster-inklusive-totalt-valdeltagande-riksdagsvalet-2022.xlsx"

@pytest.mark.skipif(not RD.exists(), reason="rådatafil saknas")
def test_bara_rd_ger_tomma_rf_kf(tmp_path):
    r = subprocess.run([sys.executable, "scripts/uppdatera_2026.py", "--rd", str(RD), "--ut", str(tmp_path),
                        "--ar", "2026", "--status", "preliminar"], cwd=ROT, capture_output=True, text=True)
    assert r.returncode == 0, r.stderr
    v = json.loads((tmp_path / "valdata_2026.json").read_text("utf-8"))
    assert v["meta"]["valnatt"] == {"raknade": 23, "totalt": 23}
    d = {x["kod"]: x for x in v["distrikt"]}["14800530"]
    assert d["rd"]["V"] == 287 and d["rf"] == {} and d["kf"] == {}
    s = json.loads((tmp_path / "swing_2026.json").read_text("utf-8"))
    assert s["distrikt"]["14800530"]["rd"]["V"] == 0.0

def test_csv_reservvag(tmp_path):
    csv = tmp_path / "valnatt.csv"
    csv.write_text("val;kod;parti;roster\nrd;14800530;V;300\nrd;14800530;S;200\nrd;14800530;giltiga;500\nrd;14800530;rostande;505\nrd;14800530;rostberattigade;1000\n", "utf-8")
    r = subprocess.run([sys.executable, "scripts/uppdatera_2026.py", "--csv", str(csv), "--ut", str(tmp_path), "--ar", "2026"], cwd=ROT, capture_output=True, text=True)
    assert r.returncode == 0, r.stderr
    v = json.loads((tmp_path / "valdata_2026.json").read_text("utf-8"))
    assert v["meta"]["valnatt"]["raknade"] == 1
    assert {x["kod"]: x for x in v["distrikt"]}["14800530"]["rd"] == {"V": 300, "S": 200}
```

- [ ] **Step 2: Implementera** enligt specen. `--repetera` = kör alla tre 2022-råfilerna, bygg valdata i minnet, jämför med `data/valdata_2022.json` (distrikt, giltiga, rostande, rostberattigade, aggregat.majorna) och skriv `REPETITION OK` eller diffar. Varningar skrivs med prefixet `VARNING:` till stderr.

- [ ] **Step 3: Kör `uppdatera_2026.py --repetera`, förvänta `REPETITION OK`. Kör pytest, PASS.**

---

### Task 10: README.md och sidvikt

- [ ] **Step 1: README** med: vad sidan är, mappstruktur, `uv venv` + `uv pip install -r requirements.txt`, `bygg_data.py`, `hamta_bakgrund.py`, lokal visning (`file://` eller `python3 -m http.server`), publicering (GitHub Pages / Vercel / subdomän: ladda upp `index.html` + `data/`), valnatten steg för steg med exakta kommandon och konfigraden, reservvägen med CSV, felsökning.

- [ ] **Step 2: Sidvikt**: `du -ch index.html data/*.js` under 1 MB. Skriv in resultatet i README.

---

## Självgranskning

Spec-täckning: rubrik/ingress (T8.1), halvcirkel (T8.4), karta med flikar och växel (T8.3), panel med Majorna-snitt och valdeltagande (T8.5), röstdelning (T8.5), faktaruta (T8.5), JS-datafiler (T5), kontrollskript (T6), geodata (T4), 2026-skript med swing, varningar, CSV, repetition (T9), valnattsläge (T8.6), README (T10), sidvikt (T10), tillgänglighet (T8.3 roles/aria, T8.5 tabell), tester (T1 till T9).
