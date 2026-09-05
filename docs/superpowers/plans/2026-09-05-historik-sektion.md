# Historiksektionen "Majorna sedan 2006" - implementationsplan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Sidan får sektionen "Majorna sedan 2006" (en mening, partilinjer 2006 till i dag, valdeltagande Majorna mot Göteborg, två konturkartor) och kortet får förändringsraden bakåt (2022 mot 2018 för de nio jämförbara kvarteren), allt räknat ur historikdatabasen och 2026 hakar på automatiskt.

**Architecture:** Ett nytt byggskript `scripts/bygg_historik.py` läser `data/historik/majorna_historik.sqlite` skrivskyddat och skriver `data/historik.json`, `data/swing_2022.json`, `data/distrikt_2006.geojson` (förenklad) samt `data/valdata_<år>` och `data/distrikt_<år>` för 2006 till 2018 i sidans befintliga schema, alla med `.js`-kopior via `scripts/schema.skriv`. `valgrafik.js` laddar `historik` och `distrikt_2006` vid start, renderar sektionen som inline-SVG (två linjediagram, två konturkartor) efter kartans val, och kortet visar den bakåtvända meningen ur `swing_2022` utan kodändring. Testdrivet i Python, webbläsarkontroller i `verktyg/`.

**Tech Stack:** Python 3.12 i `/Users/daniel/code/Temp/.venv` (sqlite3 ur standardbiblioteket, shapely, pyproj, pytest), vanilla JS/CSS/SVG, Puppeteer.

**Förutsättning:** planen `docs/superpowers/plans/2026-09-05-valnatt-2026.md` är genomförd (swingfilens schema med `ej_jamforbara`, `majorna` och `kohort`; geometri per år med `state.geo[år]`; `laddaSkript`; konfignyckeln `historik`; `hurAndrat` i kortet). Spec: `docs/superpowers/specs/2026-09-05-historik-2026-design.md` avsnitt 6 och 8, samt avsnitt 5 (kortet bakåt). Daniels beslut: serien börjar 2006, 2002 visas inte alls; linjer för V, S, MP och SD på mobil och M från 600 px containerbredd; sektionen har inga egna knappar.

**Arbetsregler:** samma som i valnattsplanen (skrivregler, Beehiivs regler för HTML-block, inga påhittade siffror, pytest före och efter varje task, svenska commit-meddelanden med `Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>`). Databasen öppnas alltid med `sqlite3.connect(f"file:{path}?mode=ro", uri=True)`; ingenting i `data/historik/` ändras. Databasen är gitignorerad och byggs om med `.venv/bin/python scripts/historik/bygg_databas.py` (cirka 25 sekunder) om den saknas.

---

## Verifierade fakta om historikdatan (kontrollerade 2026-09-05 mot databasen)

- `tidsserie(ar, val, niva, parti, roster, andel, giltiga, rostande, rostberattigade, valdeltagande, antal_distrikt, metod)`, nyckel `(ar, val, niva, parti)`. Nivåer `majorna`, `goteborg`, `riket`. `andel` och `valdeltagande` är procent med två decimaler (17.15, 79.31); sidan räknar egna bråk ur `roster`, `giltiga`, `rostande` och `rostberattigade`. Partiet `SUMMA_ÖVRIGA` är residualen giltiga minus V, S, MP, SD, M, C, L, KD, D, FI och K. Koden `L` används alla år (FP till och med 2014). Majorna finns 2006, 2010, 2014, 2018 och 2022 med `antal_distrikt` 17, 17, 17, 22, 23 och `metod` "areametod: distrikt med andel_i_majorna >= 0.50 i geo_majorna_<år>.csv" (2006 till 2018) respektive "2022 ars 23 distrikt". 2002 finns bara för `goteborg` och `riket` och utelämnas helt.
- Facit ur `tidsserie`, nivå majorna, riksdagsvalet: V 3225 av 18803 (2006), 3785 av 20452 (2010), 4102 av 20960 (2014), 6782 av 21167 (2018), 5793 av 21308 (2022). Valdeltagande riksdag Majorna 79,31, 82,80, 82,89, 84,33, 82,76 och Göteborg 79,54, 82,72, 82,82, 84,28, 80,71. Kommunvalet V 2731 av 18807 (2006) till 7479 av 21620 (2022). D finns bara i rf och kf 2018 och 2022, K bara i rf 2006 och 2010 samt kf alla år.
- `roster(ar, val, kod, parti, parti_kalla, roster, kalla, parti_kanon)` och `distrikt_summa(ar, val, kod, giltiga, ogiltiga, rostande, rostberattigade, valdeltagande, blanka, kalla)` per distrikt, `majorna_medlem(ar, kod, namn, klass, andel_i_majorna, ingar_i_jamforbart_majorna, beslut, kalla)` med 17, 17, 17, 22 respektive 23 rader med `ingar_i_jamforbart_majorna = 1` för 2006 till 2022. Nyckeln är alltid `(ar, kod)`; 115 av 2006 års koder används 2002 för andra distrikt.
- `data/historik/kedja_majorna_2006_2022.csv` (23 rader, semikolon): `kod_2022;namn_2022;kortnamn_2022;kod_2018;namn_2018;typ_2018_2022;kod_2014;namn_2014;typ_2014_2018;kod_2010;namn_2010;typ_2010_2014;kod_2006;namn_2006;typ_2006_2010;jamforbar_tillbaka_till;jamforbar_direkt;anmarkning`. Nio rader har `jamforbar_tillbaka_till` 2018 eller 2006: 14800526 Svalebo (2018: 14801017), 14800536 Kusttorget (14801036), 14800537 Chapmans Torg (14801031), 14800538 Slottsskogsgat. m fl (14801038), 14800539 Gråberget Västra (14801034), 14800541 Godhem (14801032), 14800546 Kommendörsgatan m fl (14801041), 14800547 Hängmattan (14801035), 14800548 Gatenhielmska (14801042). Kolumnen `kod_2018` ger 2018 års kod för varje rad.
- `data/historik/distrikt_2006_majornaomradet.geojson`: FeatureCollection, 17 features, WGS84 utan crs-block, egenskaperna `kod` och `namn`, 27 kB. Samma form för 2010 (17), 2014 (17) och 2018 (22). Ytan är densamma som 2022 på 0,04 procent när.
- Sidans schema för `valdata_<år>.json` står i README under Dataschema; 2022 års fil är facit för formen.

---

## Filstruktur

| Fil | Ansvar | Task |
|---|---|---|
| `scripts/bygg_historik.py` (ny) | Läser databasen och kedjefilen, skriver `historik`, `swing_2022`, `distrikt_2006` (förenklad), `valdata_<år>` och `distrikt_<år>` för 2006 till 2018. Underkommandon per fil. | 1, 2, 3, 4 |
| `tests/test_bygg_historik.py` (ny) | Summor, facit mot `valdata_2022.json`, exakt nio jämförbara, polygoner giltiga. Hoppas över om databasen saknas. | 1 till 4 |
| `scripts/kontrollera.py` | `--historik` stämmer av `historik.json` mot `valdata_2022.json`. | 5 |
| `valgrafik.js`, `valgrafik.css` | Laddning, sektionen, tre bilder, talrad, tillgänglighet, lägen för 2026. | 6, 7, 8, 9 |
| `tests/test_inbaddning.py`, `verktyg/historik-check.js` (ny) | Textkontroller och webbläsarkontroll av sektionen. | 6 till 9 |
| `README.md`, `docs/HANDOVER.md` | Dokumentation. | 10 |

---

### Task 1: `scripts/bygg_historik.py` - områdesserien `data/historik.json`

**Files:**
- Create: `scripts/bygg_historik.py`
- Create: `tests/test_bygg_historik.py`
- Create (genererade): `data/historik.json`, `data/historik.js`

Schema (specen avsnitt 8):

```
meta    byggd (ISO), kalla, ar [2006, 2010, 2014, 2018, 2022], partier [V, S, MP, SD, M, C, L, KD, D, FI, K, Övriga],
        noter [str], metod {ar: str}
serie   {val: {niva: [ {ar, roster {parti: n}, andel {parti: bråk}, giltiga, rostande, rostberattigade,
                        valdeltagande (bråk eller null), antal_distrikt (null för goteborg och riket)} ]}}
```

- [ ] **Step 1: Skriv de fallande testerna**

```python
# tests/test_bygg_historik.py
import json
import sqlite3
import subprocess
import sys
from pathlib import Path

import pytest

ROT = Path(__file__).resolve().parents[1]
DB = ROT / "data" / "historik" / "majorna_historik.sqlite"
finns = pytest.mark.skipif(not DB.exists(), reason="historikdatabasen saknas, bygg med scripts/historik/bygg_databas.py")
PARTIER = ["V", "S", "MP", "SD", "M", "C", "L", "KD", "D", "FI", "K", "Övriga"]


def kor(*args):
    return subprocess.run([sys.executable, "scripts/bygg_historik.py", *args], cwd=ROT, capture_output=True, text=True)


def db():
    return sqlite3.connect(f"file:{DB}?mode=ro", uri=True)


@finns
def test_historik_json_form_och_summor(tmp_path):
    r = kor("historik", "--ut", str(tmp_path))
    assert r.returncode == 0, r.stdout + r.stderr
    hst = json.loads((tmp_path / "historik.json").read_text("utf-8"))
    assert hst["meta"]["ar"] == [2006, 2010, 2014, 2018, 2022] and hst["meta"]["partier"] == PARTIER
    assert set(hst["serie"]) == {"rd", "rf", "kf"} and set(hst["serie"]["rd"]) == {"majorna", "goteborg", "riket"}
    for val, nivaer in hst["serie"].items():
        for niva, rader in nivaer.items():
            assert [p["ar"] for p in rader] == [2006, 2010, 2014, 2018, 2022], f"{val} {niva}"
            for p in rader:
                assert set(p["roster"]) == set(PARTIER)
                assert sum(p["roster"].values()) == p["giltiga"], f"{val} {niva} {p['ar']}: partiernas röster ska summera till giltiga"
                for q in PARTIER:
                    assert p["andel"][q] == pytest.approx(p["roster"][q] / p["giltiga"])
                if p["rostberattigade"]:
                    assert p["valdeltagande"] == pytest.approx(p["rostande"] / p["rostberattigade"])
    m = {p["ar"]: p for p in hst["serie"]["rd"]["majorna"]}
    assert m[2006]["roster"]["V"] == 3225 and m[2006]["giltiga"] == 18803 and m[2006]["antal_distrikt"] == 17
    assert m[2022]["roster"]["V"] == 5793 and m[2022]["antal_distrikt"] == 23
    assert m[2022]["valdeltagande"] == pytest.approx(0.8276, abs=0.0001)
    assert hst["serie"]["rd"]["goteborg"][4]["valdeltagande"] == pytest.approx(0.8071, abs=0.0001)
    assert hst["serie"]["rd"]["goteborg"][0]["antal_distrikt"] is None
    assert (tmp_path / "historik.js").exists() and (tmp_path / "historik.json").stat().st_size < 60000


@finns
def test_historik_2022_ar_identisk_med_valdata_2022(tmp_path):
    kor("historik", "--ut", str(tmp_path))
    hst = json.loads((tmp_path / "historik.json").read_text("utf-8"))
    v = json.loads((ROT / "data" / "valdata_2022.json").read_text("utf-8"))
    for val in ("rd", "rf", "kf"):
        h = [p for p in hst["serie"][val]["majorna"] if p["ar"] == 2022][0]
        agg = v["aggregat"]["majorna"][val]
        for p, n in agg["roster"].items():
            assert h["roster"][p] == n, f"{val} {p}"
        assert h["giltiga"] == agg["giltiga"] and h["rostande"] == agg["rostande"] and h["rostberattigade"] == agg["rostberattigade"]


@finns
def test_historik_utelamnar_2002_och_smapartier(tmp_path):
    kor("historik", "--ut", str(tmp_path))
    text = (tmp_path / "historik.json").read_text("utf-8")
    assert '"ar": 2002' not in text and "SUMMA_ÖVRIGA" not in text and "PP" not in text
```

- [ ] **Step 2: Kör och se dem falla**

Run: `/Users/daniel/code/Temp/.venv/bin/python -m pytest tests/test_bygg_historik.py -q`
Expected: FAIL (`No such file or directory: scripts/bygg_historik.py`).

- [ ] **Step 3: Skriv skriptet**

```python
#!/usr/bin/env python3
"""Bygger sidans historikfiler ur data/historik/majorna_historik.sqlite (skrivskyddat).

    .venv/bin/python scripts/bygg_historik.py historik            data/historik.json + .js
    .venv/bin/python scripts/bygg_historik.py swing2022           data/swing_2022.json + .js (bas 2018)
    .venv/bin/python scripts/bygg_historik.py geo2006             data/distrikt_2006.geojson + .js (förenklad, för konturkartan)
    .venv/bin/python scripts/bygg_historik.py ar 2006 2010 2014 2018   data/valdata_<år> och data/distrikt_<år>
    .venv/bin/python scripts/bygg_historik.py allt

Databasen byggs om med scripts/historik/bygg_databas.py. Serien börjar 2006 (Daniels beslut 2026-09-05);
2002 går inte att räkna om till dagens Majorna och tas inte med. Partikoden L täcker Folkpartiet till och
med 2014. Alla tal räknas ur tabellerna, inget skrivs för hand.
"""
import argparse
import csv
import datetime as dt
import json
import sqlite3
import sys
from pathlib import Path

ROT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROT))

from scripts import schema  # noqa: E402
from scripts.valmyndigheten import MAJORNA_KODER, NYCKELPARTIER, OVRIGA, VAL  # noqa: E402

DB = ROT / "data" / "historik" / "majorna_historik.sqlite"
KEDJA = ROT / "data" / "historik" / "kedja_majorna_2006_2022.csv"
GEO_HISTORIK = ROT / "data" / "historik"
AR = [2006, 2010, 2014, 2018, 2022]
PARTIER = ["V", "S", "MP", "SD", "M", "C", "L", "KD", "D", "FI", "K", OVRIGA]
NIVAER = ["majorna", "goteborg", "riket"]
KALLA = "Valmyndigheten, slutlig rösträkning per valdistrikt 2006 till 2022, sammanställd i data/historik/majorna_historik.sqlite"


def oppna(path=DB):
    if not Path(path).exists():
        print(f"FEL: {path} saknas, bygg den med scripts/historik/bygg_databas.py", file=sys.stderr)
        sys.exit(1)
    con = sqlite3.connect(f"file:{path}?mode=ro", uri=True)
    con.row_factory = sqlite3.Row
    return con


def _post(rader):
    """Rader ur tidsserie för ett (ar, val, niva) -> en post i serien."""
    roster = {p: 0 for p in PARTIER}
    giltiga = rostande = rostberattigade = None
    antal = metod = None
    for r in rader:
        p = r["parti"]
        if p == "SUMMA_ÖVRIGA":
            roster[OVRIGA] = int(r["roster"] or 0)
        elif p in roster:
            roster[p] = int(r["roster"] or 0)
        else:
            continue
        giltiga = int(r["giltiga"]) if r["giltiga"] is not None else giltiga
        rostande = int(r["rostande"]) if r["rostande"] is not None else rostande
        rostberattigade = int(r["rostberattigade"]) if r["rostberattigade"] is not None else rostberattigade
        antal = int(r["antal_distrikt"]) if r["antal_distrikt"] is not None else antal
        metod = r["metod"] if metod is None or "residual" not in (r["metod"] or "") else metod
    if giltiga is None:
        return None
    if sum(roster.values()) != giltiga:
        raise SystemExit(f"FEL: {rader[0]['ar']} {rader[0]['val']} {rader[0]['niva']}: partiernas röster {sum(roster.values())} != giltiga {giltiga}")
    return {"ar": int(rader[0]["ar"]), "roster": roster, "andel": {p: n / giltiga for p, n in roster.items()},
            "giltiga": giltiga, "rostande": rostande, "rostberattigade": rostberattigade,
            "valdeltagande": (rostande / rostberattigade) if rostande and rostberattigade else None,
            "antal_distrikt": antal, "metod": metod}


def bygg_historik(con):
    serie = {val: {niva: [] for niva in NIVAER} for val in VAL}
    metod_per_ar = {}
    for val in VAL:
        for niva in NIVAER:
            for ar in AR:
                rader = con.execute("SELECT * FROM tidsserie WHERE ar=? AND val=? AND niva=? ORDER BY parti", (ar, val, niva)).fetchall()
                post = _post(rader)
                if post is None:
                    raise SystemExit(f"FEL: tidsserie saknar {ar} {val} {niva}")
                if niva == "majorna":
                    metod_per_ar[str(ar)] = post["metod"]
                serie[val][niva].append({k: v for k, v in post.items() if k != "metod"})
    return {"meta": {"byggd": dt.datetime.now().replace(microsecond=0).isoformat(), "kalla": KALLA, "ar": AR, "partier": PARTIER,
                     "noter": ["Serien börjar 2006. Valdistrikten ritades om helt inför det valet, så 2002 går inte att räkna om till dagens Majorna.",
                               "Liberalerna hette Folkpartiet till och med 2014; serien använder koden L hela vägen.",
                               "Övriga är giltiga röster minus de elva partierna ovan."],
                     "metod": metod_per_ar},
            "serie": serie}


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("vad", choices=["historik", "swing2022", "geo2006", "ar", "allt"])
    ap.add_argument("aren", nargs="*", help="för 'ar': vilka år")
    ap.add_argument("--ut", default=ROT / "data")
    ap.add_argument("--db", default=DB)
    a = ap.parse_args()
    ut = Path(a.ut)
    con = oppna(a.db)
    skrivna = []
    if a.vad in ("historik", "allt"):
        skrivna += schema.skriv(ut / "historik", bygg_historik(con))
    if a.vad in ("swing2022", "allt"):
        skrivna += schema.skriv(ut / "swing_2022", bygg_swing_2022(con))
    if a.vad in ("geo2006", "allt"):
        skrivna += schema.skriv(ut / "distrikt_2006", bygg_geo(2006, forenkla=True), json_suffix=".geojson")
    if a.vad == "ar" or a.vad == "allt":
        for ar in (a.aren or ["2006", "2010", "2014", "2018"]):
            skrivna += schema.skriv(ut / f"valdata_{ar}", bygg_valdata_ar(con, int(ar)))
            if int(ar) != 2006:
                skrivna += schema.skriv(ut / f"distrikt_{ar}", bygg_geo(int(ar), forenkla=False), json_suffix=".geojson")
    for f in skrivna:
        print(f"    {f.stat().st_size / 1024:6.1f} kB  {f}")
    return 0


def bygg_swing_2022(con):
    raise SystemExit("swing2022 byggs i Task 2")


def bygg_geo(ar, forenkla):
    raise SystemExit("geo byggs i Task 3")


def bygg_valdata_ar(con, ar):
    raise SystemExit("valdata per år byggs i Task 4")


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 4: Kör testerna**

Run: `/Users/daniel/code/Temp/.venv/bin/python -m pytest tests/test_bygg_historik.py -q`
Expected: `3 passed`. Om summakontrollen faller för något år beror det på att `SUMMA_ÖVRIGA` och de elva partierna inte täcker `giltiga` i den raden; skriv då ut raden (`SELECT * FROM tidsserie WHERE ...`) och kontrollera mot `docs/historik/noter/databas.md` innan något ändras. Bygg sedan den riktiga filen: `/Users/daniel/code/Temp/.venv/bin/python scripts/bygg_historik.py historik` och notera storleken.

- [ ] **Step 5: Commit**

```bash
git add scripts/bygg_historik.py tests/test_bygg_historik.py data/historik.json data/historik.js
git commit -m "bygg_historik.py: områdesserien 2006 till 2022 för Majorna, Göteborg och riket ur historikdatabasen

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>"
```

---

### Task 2: `swing_2022.json` - 2022 mot 2018 för de nio jämförbara kvarteren

**Files:**
- Modify: `scripts/bygg_historik.py`
- Modify: `tests/test_bygg_historik.py`
- Create (genererade): `data/swing_2022.json`, `data/swing_2022.js`

Schemat är det från valnattsplanens Task 5 (`schema.swing`). Distriktsnivån räknas med `schema.swing` på ett basobjekt där 2018 års nio motsvarigheter fått 2022 års koder. Områdesnivån tas ur områdesserien (tidsserien håller området konstant, 22 distrikt 2018 mot 23 år 2022), inte ur kohorten, och `kohort` märks `helomrade: true` med `metod: "omradesserien"`. De fjorton övriga får den bakåtvända meningen.

- [ ] **Step 1: Skriv de fallande testerna**

```python
JAMFORBARA_2018 = {"14800526": "14801017", "14800536": "14801036", "14800537": "14801031", "14800538": "14801038", "14800539": "14801034",
                   "14800541": "14801032", "14800546": "14801041", "14800547": "14801035", "14800548": "14801042"}


@finns
def test_swing_2022_nio_jamforbara_och_omradesserien(tmp_path):
    r = kor("swing2022", "--ut", str(tmp_path))
    assert r.returncode == 0, r.stdout + r.stderr
    s = json.loads((tmp_path / "swing_2022.json").read_text("utf-8"))
    assert s["ar"] == 2022 and s["bas"] == 2018
    assert sorted(s["distrikt"]) == sorted(JAMFORBARA_2018)
    assert len(s["ej_jamforbara"]) == 14
    assert s["ej_jamforbara"]["14800530"]["mening"] == "Gränserna såg annorlunda ut 2018. Siffrorna hör till det årets distrikt."
    assert s["ej_jamforbara"]["14800530"]["omradesrad"] is True
    for val in ("rd", "rf", "kf"):
        assert s["kohort"][val]["metod"] == "omradesserien"
        assert s["kohort"][val]["helomrade"] is True and s["kohort"][val]["antal"] == 23 and s["kohort"][val]["totalt"] == 23
    with db() as con:
        v22 = con.execute("SELECT roster, giltiga FROM tidsserie WHERE ar=2022 AND val='rd' AND niva='majorna' AND parti='V'").fetchone()
        v18 = con.execute("SELECT roster, giltiga FROM tidsserie WHERE ar=2018 AND val='rd' AND niva='majorna' AND parti='V'").fetchone()
        vantat = round((v22[0] / v22[1] - v18[0] / v18[1]) * 100, 1)
        assert s["majorna"]["rd"]["V"] == pytest.approx(vantat, abs=0.05)
        g22 = con.execute("SELECT r.roster, s.giltiga FROM roster r JOIN distrikt_summa s ON s.ar=r.ar AND s.val=r.val AND s.kod=r.kod "
                          "WHERE r.ar=2022 AND r.val='rd' AND r.kod='14800541' AND r.parti_kanon='V'").fetchone()
        g18 = con.execute("SELECT r.roster, s.giltiga FROM roster r JOIN distrikt_summa s ON s.ar=r.ar AND s.val=r.val AND s.kod=r.kod "
                          "WHERE r.ar=2018 AND r.val='rd' AND r.kod='14801032' AND r.parti_kanon='V'").fetchone()
        assert s["distrikt"]["14800541"]["rd"]["V"] == pytest.approx(round((g22[0] / g22[1] - g18[0] / g18[1]) * 100, 1), abs=0.05)
    assert r.stdout.count("14800541") >= 1, "skriptet skriver ut listan över jämförbara distrikt för avstämning"
```

- [ ] **Step 2: Kör och se det falla** (`swing2022 byggs i Task 2`).

- [ ] **Step 3: Ersätt `bygg_swing_2022` i `scripts/bygg_historik.py`**

```python
MENING_BAKAT = "Gränserna såg annorlunda ut {bas}. Siffrorna hör till det årets distrikt."


def las_kedja():
    """kedja_majorna_2006_2022.csv -> {kod_2022: kod_2018} för raderna som är jämförbara till 2018 eller längre."""
    with open(KEDJA, encoding="utf-8", newline="") as f:
        rader = list(csv.DictReader(f, delimiter=";"))
    ut = {}
    for r in rader:
        if r["jamforbar_tillbaka_till"] in ("2018", "2014", "2010", "2006") and r["kod_2018"]:
            ut[r["kod_2022"]] = r["kod_2018"]
    return ut


def distrikt_ur_db(con, ar, kod, namn):
    """Ett distrikt ett år i sidans schema: roster per val med sidans partikoder, summor ur distrikt_summa."""
    post = {"kod": kod, "namn": namn, "raknat": True, "giltiga": {}, "rostande": {}, "rostberattigade": {}}
    for val in VAL:
        roster = {p: 0 for p in NYCKELPARTIER[val]}
        roster[OVRIGA] = 0
        for r in con.execute("SELECT parti_kanon, roster FROM roster WHERE ar=? AND val=? AND kod=?", (ar, val, kod)):
            p = r["parti_kanon"]
            roster[p if p in roster else OVRIGA] += int(r["roster"] or 0)
        s = con.execute("SELECT giltiga, rostande, rostberattigade FROM distrikt_summa WHERE ar=? AND val=? AND kod=?", (ar, val, kod)).fetchone()
        if s is None:
            post[val] = {}
            continue
        if sum(roster.values()) != int(s["giltiga"]):
            raise SystemExit(f"FEL: {ar} {val} {kod}: röster {sum(roster.values())} != giltiga {s['giltiga']}")
        post[val] = roster
        post["giltiga"][val] = int(s["giltiga"])
        post["rostande"][val] = int(s["rostande"] or 0)
        post["rostberattigade"][val] = int(s["rostberattigade"] or 0)
    return post


def bygg_swing_2022(con):
    ny = json.loads((ROT / "data" / "valdata_2022.json").read_text("utf-8"))
    kedja = las_kedja()
    bas_distrikt = [distrikt_ur_db(con, 2018, kod18, next(d["namn"] for d in ny["distrikt"] if d["kod"] == kod22)) | {"kod": kod22}
                    for kod22, kod18 in kedja.items()]
    hst = bygg_historik(con)
    bas = {"meta": {"ar": 2018}, "distrikt": bas_distrikt, "aggregat": {"majorna": {}}}
    meningar = {d["kod"]: MENING_BAKAT.format(bas=2018) for d in ny["distrikt"] if d["kod"] not in kedja}
    s = schema.swing(ny, bas, jamforbara=list(kedja), meningar=meningar)
    for val in VAL:
        p22 = next(p for p in hst["serie"][val]["majorna"] if p["ar"] == 2022)
        p18 = next(p for p in hst["serie"][val]["majorna"] if p["ar"] == 2018)
        s["majorna"][val] = {p: round((p22["andel"][p] - p18["andel"][p]) * 100, 1) for p in PARTIER}
        s["kohort"][val] = {"antal": len(ny["distrikt"]), "totalt": len(ny["distrikt"]), "helomrade": True,
                            "koder": [d["kod"] for d in ny["distrikt"]], "metod": "omradesserien"}
    print("Jämförbara 2022 mot 2018: " + ", ".join(f"{k} ({kedja[k]})" for k in sorted(kedja)))
    print("Omritade sedan 2018: " + ", ".join(sorted(meningar)))
    return s
```

`distrikt_ur_db(...) | {"kod": kod22}` ger 2018 års siffror under 2022 års kod, så att `schema.swing` hittar basdistriktet. Om `parti_kanon` i databasen skriver Folkpartiet som `FP` något år, lägg `"FP": "L"` som en mappning före uppslaget (`p = {"FP": "L"}.get(p, p)`); faktabladet säger att tidsserien använder L genomgående men tabellen `roster` behåller källans kod i `parti_kalla`, kontrollera med `SELECT DISTINCT parti_kanon FROM roster WHERE ar=2018`.

- [ ] **Step 4: Kör testerna och bygg filen**

Run: `/Users/daniel/code/Temp/.venv/bin/python -m pytest tests/test_bygg_historik.py -q && /Users/daniel/code/Temp/.venv/bin/python scripts/bygg_historik.py swing2022`
Expected: gröna tester, utskrift med de nio jämförbara och de fjorton omritade, `swing_2022.json` under 5 kB.

- [ ] **Step 5: Commit**

```bash
git add scripts/bygg_historik.py tests/test_bygg_historik.py data/swing_2022.json data/swing_2022.js
git commit -m "swing_2022: förändring 2022 mot 2018 för de nio jämförbara kvarteren, områdesnivån ur områdesserien

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>"
```

---

### Task 3: `distrikt_2006` förenklad för konturkartan, och polygoner för 2010 till 2018

**Files:**
- Modify: `scripts/bygg_historik.py`
- Modify: `tests/test_bygg_historik.py`
- Create (genererade): `data/distrikt_2006.geojson`, `data/distrikt_2006.js` (och senare `distrikt_2010`, `2014`, `2018` i Task 4)

- [ ] **Step 1: Skriv de fallande testerna**

```python
from shapely.geometry import shape


@finns
def test_geo2006_forenklad_med_17_giltiga_polygoner(tmp_path):
    r = kor("geo2006", "--ut", str(tmp_path))
    assert r.returncode == 0, r.stdout + r.stderr
    fc = json.loads((tmp_path / "distrikt_2006.geojson").read_text("utf-8"))
    assert len(fc["features"]) == 17 and fc["bbox"][0] < fc["bbox"][2]
    for f in fc["features"]:
        g = shape(f["geometry"])
        assert g.is_valid and g.geom_type == "Polygon", f["properties"]["kod"]
        lon, lat = f["properties"]["etikett"]
        assert g.contains(shape({"type": "Point", "coordinates": [lon, lat]}))
        assert set(f["properties"]) == {"kod", "namn", "etikett", "area_km2"}
    assert abs(sum(f["properties"]["area_km2"] for f in fc["features"]) - 4.655) < 0.02, "samma yta som 2022 på 0,04 procent när, förenklingen får kosta högst 0,4 procent"
    assert (tmp_path / "distrikt_2006.geojson").stat().st_size < 15000, "förenklad för en 170 px bred kontur"
    namn = {f["properties"]["kod"]: f["properties"]["namn"] for f in fc["features"]}
    assert namn["14805901"] == "Stigberget 1" and namn["14808504"] == "Majorna 4"
```

- [ ] **Step 2: Kör och se det falla** (`geo byggs i Task 3`).

- [ ] **Step 3: Ersätt `bygg_geo`** och lägg till importerna överst:

```python
from pyproj import Transformer
from shapely.geometry import mapping, shape
from shapely.ops import polylabel, transform as geo_transform

from scripts.geo import kort_namn  # noqa: E402
```

```python
def bygg_geo(ar, forenkla):
    """distrikt_<år>_majornaomradet.geojson (WGS84, kod och namn) -> sidans geojson med etikett, area_km2 och bbox.
    forenkla=True (2006, konturkartan) förenklar med 0,00012 grader (cirka 8 till 13 meter); de andra åren behåller
    gemensamma gränser exakt."""
    src = GEO_HISTORIK / f"distrikt_{ar}_majornaomradet.geojson"
    if not src.exists():
        raise SystemExit(f"FEL: {src} saknas")
    gj = json.loads(src.read_text("utf-8"))
    till_sweref = Transformer.from_crs("EPSG:4326", "EPSG:3006", always_xy=True).transform
    features = []
    for ft in gj["features"]:
        g = shape(ft["geometry"])
        if g.geom_type == "MultiPolygon":
            g = max(g.geoms, key=lambda p: p.area)
        if forenkla:
            g = g.simplify(0.00012, preserve_topology=True)
        g = g.buffer(0)
        if g.geom_type == "MultiPolygon":
            g = max(g.geoms, key=lambda p: p.area)
        etikett = polylabel(g, tolerance=1e-5)
        area = geo_transform(till_sweref, g).area / 1e6
        ringar = [[[round(x, 6), round(y, 6)] for x, y in ring] for ring in mapping(g)["coordinates"]]
        features.append({"type": "Feature",
                         "properties": {"kod": str(ft["properties"]["kod"]).strip(), "namn": kort_namn(ft["properties"].get("namn") or ft["properties"]["kod"]),
                                        "etikett": [round(etikett.x, 6), round(etikett.y, 6)], "area_km2": round(area, 4)},
                         "geometry": {"type": "Polygon", "coordinates": ringar}})
    features.sort(key=lambda f: f["properties"]["kod"])
    xs = [c[0] for f in features for c in f["geometry"]["coordinates"][0]]
    ys = [c[1] for f in features for c in f["geometry"]["coordinates"][0]]
    return {"type": "FeatureCollection", "bbox": [min(xs), min(ys), max(xs), max(ys)], "features": features}
```

- [ ] **Step 4: Kör testerna och bygg filen**

Run: `/Users/daniel/code/Temp/.venv/bin/python -m pytest tests/test_bygg_historik.py -q && /Users/daniel/code/Temp/.venv/bin/python scripts/bygg_historik.py geo2006`
Expected: grönt; utskriften visar storleken på `distrikt_2006.geojson` (riktvärde 10 kB). Blir filen större än 15 kB, höj toleransen till 0,0002 och kör om; blir ytan mer än 0,02 km² fel, sänk den. Rita en snabb kontrollbild: `.venv/bin/python -c "import json; fc=json.load(open('data/distrikt_2006.geojson')); print(len(fc['features']), sum(len(f['geometry']['coordinates'][0]) for f in fc['features']), 'hörn')"`.

- [ ] **Step 5: Commit**

```bash
git add scripts/bygg_historik.py tests/test_bygg_historik.py data/distrikt_2006.geojson data/distrikt_2006.js
git commit -m "distrikt_2006: förenklade polygoner för konturkartan, samma schema som 2022

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>"
```

---

### Task 4: `valdata_<år>` och `distrikt_<år>` för 2006, 2010, 2014 och 2018

**Files:**
- Modify: `scripts/bygg_historik.py`
- Modify: `tests/test_bygg_historik.py`
- Create (genererade): `data/valdata_2006.json` med `.js`, samma för 2010, 2014, 2018; `data/distrikt_2010.geojson` med `.js`, samma för 2014 och 2018

Filerna byggs så att ett historikår kan läggas i `KONFIG.ar` senare och visas på kartan med sina egna distrikt. Sidan laddar dem inte i den här planen. Jämförelseaggregat: Göteborg och riket för riksdagsvalet och kommunvalet ur `tidsserie`; för regionvalet Västra Götaland ur tabellen `aggregat` (nivå `vgregion`) när raden finns, annars utelämnas. Mandat: riksdagens verkliga ur tabellen `mandat` (nivå `riket`, val `rd`), Majornas egna med `jamkade_uddatal`.

- [ ] **Step 1: Skriv de fallande testerna**

```python
from scripts.mandat import jamkade_uddatal


@finns
def test_valdata_2006_i_sidans_schema(tmp_path):
    r = kor("ar", "2006", "--ut", str(tmp_path))
    assert r.returncode == 0, r.stdout + r.stderr
    v = json.loads((tmp_path / "valdata_2006.json").read_text("utf-8"))
    assert v["meta"]["ar"] == 2006 and v["meta"]["status"] == "slutlig" and len(v["distrikt"]) == 17
    assert v["meta"]["valnatt"] == {"raknade": 17, "totalt": 17}
    assert all(set(d) >= {"kod", "namn", "raknat", "rd", "rf", "kf", "giltiga", "rostande", "rostberattigade"} for d in v["distrikt"])
    with db() as con:
        t = con.execute("SELECT roster, giltiga FROM tidsserie WHERE ar=2006 AND val='rd' AND niva='majorna' AND parti='V'").fetchone()
    assert v["aggregat"]["majorna"]["rd"]["roster"]["V"] == t[0] and v["aggregat"]["majorna"]["rd"]["giltiga"] == t[1]
    assert v["aggregat"]["goteborg"]["rd"]["valdeltagande"] == pytest.approx(0.7954, abs=0.0001)
    assert v["aggregat"]["riket"]["rd"]["namn"] == "Riket" and 0.05 < v["aggregat"]["riket"]["rd"]["andel"]["V"] < 0.07
    assert sum(v["mandat"]["riksdag_verklig"].values()) == 349 and sum(v["mandat"]["riksdag_majorna"].values()) == 349
    assert not (tmp_path / "distrikt_2006.geojson").exists(), "2006 års polygoner byggs av geo2006, förenklade"


@finns
def test_valdata_2018_och_distrikt_2018(tmp_path):
    r = kor("ar", "2018", "--ut", str(tmp_path))
    assert r.returncode == 0, r.stdout + r.stderr
    v = json.loads((tmp_path / "valdata_2018.json").read_text("utf-8"))
    assert len(v["distrikt"]) == 22
    d = {x["kod"]: x for x in v["distrikt"]}["14801032"]
    assert d["namn"] == "Godhem" and d["rd"]["V"] > 0 and sum(d["rd"].values()) == d["giltiga"]["rd"]
    fc = json.loads((tmp_path / "distrikt_2018.geojson").read_text("utf-8"))
    assert len(fc["features"]) == 22
    assert sorted(f["properties"]["kod"] for f in fc["features"]) == sorted(x["kod"] for x in v["distrikt"])
```

- [ ] **Step 2: Kör och se dem falla** (`valdata per år byggs i Task 4`).

- [ ] **Step 3: Ersätt `bygg_valdata_ar`** och lägg till importen `from scripts.mandat import jamkade_uddatal  # noqa: E402`:

```python
def _jamforelse(con, ar, val, niva, namn):
    """En rad per parti ur tidsserie (goteborg, riket) -> {"andel", "valdeltagande", "giltiga", "rostande", "rostberattigade", "namn"}."""
    rader = con.execute("SELECT * FROM tidsserie WHERE ar=? AND val=? AND niva=? ORDER BY parti", (ar, val, niva)).fetchall()
    post = _post(rader)
    if post is None:
        return None
    return {"andel": {p: a for p, a in post["andel"].items() if p != OVRIGA}, "valdeltagande": post["valdeltagande"],
            "giltiga": post["giltiga"], "rostande": post["rostande"], "rostberattigade": post["rostberattigade"], "namn": namn}


def _vgregion(con, ar, val):
    """Västra Götaland i regionvalet ur tabellen aggregat (nivå vgregion), som sidans 'riket' för rf."""
    rader = con.execute("SELECT parti_kanon AS parti, roster, giltiga, rostande, rostberattigade FROM aggregat WHERE ar=? AND val=? AND niva='vgregion'", (ar, val)).fetchall()
    if not rader:
        return None
    roster = {p: 0 for p in NYCKELPARTIER[val]}
    giltiga = rostande = rostberattigade = None
    for r in rader:
        if r["parti"] in roster:
            roster[r["parti"]] += int(r["roster"] or 0)
        giltiga, rostande, rostberattigade = r["giltiga"], r["rostande"], r["rostberattigade"]
    if not giltiga:
        return None
    return {"andel": {p: n / giltiga for p, n in roster.items()}, "valdeltagande": (rostande / rostberattigade) if rostande and rostberattigade else None,
            "giltiga": int(giltiga), "rostande": int(rostande or 0), "rostberattigade": int(rostberattigade or 0), "namn": "Västra Götaland"}


def bygg_valdata_ar(con, ar):
    medlemmar = con.execute("SELECT kod, namn FROM majorna_medlem WHERE ar=? AND ingar_i_jamforbart_majorna=1 ORDER BY kod", (ar,)).fetchall()
    if not medlemmar:
        raise SystemExit(f"FEL: majorna_medlem saknar {ar}")
    distrikt = [distrikt_ur_db(con, ar, r["kod"], kort_namn(r["namn"])) for r in medlemmar]
    jamforelser = {"goteborg": {}, "riket": {}}
    for val in VAL:
        g = _jamforelse(con, ar, val, "goteborg", "Göteborg")
        if g:
            jamforelser["goteborg"][val] = g
        if val == "rd":
            r = _jamforelse(con, ar, val, "riket", "Riket")
            if r:
                jamforelser["riket"][val] = r
        elif val == "rf":
            vg = _vgregion(con, ar, val)
            if vg:
                jamforelser["riket"][val] = vg
    verklig = {r["parti"]: int(r["mandat"]) for r in con.execute("SELECT parti, mandat FROM mandat WHERE ar=? AND val='rd' AND niva='riket'", (ar,)) if r["mandat"]}
    rd_summa = {}
    for d in distrikt:
        for p, n in d["rd"].items():
            rd_summa[p] = rd_summa.get(p, 0) + n
    mandat = {"riksdag_verklig": verklig, "riksdag_majorna": jamkade_uddatal(rd_summa, 349) if rd_summa else {},
              "metod": f"Räkneexempel: 4 %-spärr och jämkade uddatalsmetoden tillämpade på Majornas riksdagsröster {ar}."}
    valdag = con.execute("SELECT valdag FROM val WHERE ar=? AND val='rd'", (ar,)).fetchone()
    v = schema.bygg_valdata(ar, distrikt, "slutlig", jamforelser, mandat, uppdaterad=(valdag["valdag"] + "T00:00:00") if valdag else None,
                            kalla=f"Valmyndigheten, slutlig rösträkning per valdistrikt {ar}, ur data/historik/majorna_historik.sqlite")
    v["meta"]["avgransning"] = f"{len(distrikt)} valdistrikt som täcker samma yta som 2022 års 23 (areametod, se docs/historik/valdistrikt-historik.md)"
    return v
```

Om `aggregat` saknar kolumnen `parti_kanon` med det namnet, använd `parti` (tabellen har båda enligt datamodellen: `parti` och `parti_kanon`). Kontrollera att `mandat`-tabellens riket-rader använder sidans partikoder (`SELECT DISTINCT parti FROM mandat WHERE niva='riket'`); annars mappa via `scripts.valmyndigheten.partikod` på partinamnet i `partier`-tabellen.

- [ ] **Step 4: Kör testerna och bygg filerna**

Run: `/Users/daniel/code/Temp/.venv/bin/python -m pytest tests/test_bygg_historik.py -q && /Users/daniel/code/Temp/.venv/bin/python scripts/bygg_historik.py ar 2006 2010 2014 2018`
Expected: gröna tester, åtta nya filer i `data/` (valdata för fyra år, distrikt för tre), valdata 5 till 7 kB var.

- [ ] **Step 5: Commit**

```bash
git add scripts/bygg_historik.py tests/test_bygg_historik.py data/valdata_2006.json data/valdata_2006.js data/valdata_2010.json data/valdata_2010.js data/valdata_2014.json data/valdata_2014.js data/valdata_2018.json data/valdata_2018.js data/distrikt_2010.geojson data/distrikt_2010.js data/distrikt_2014.geojson data/distrikt_2014.js data/distrikt_2018.geojson data/distrikt_2018.js
git commit -m "Historikåren 2006 till 2018 i sidans schema: valdata och polygoner per år, laddas inte än

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>"
```

---

### Task 5: `kontrollera.py --historik` stämmer av områdesserien mot 2022 års valdata

**Files:**
- Modify: `scripts/kontrollera.py`
- Modify: `tests/test_kontrollera.py`

- [ ] **Step 1: Skriv de fallande testerna**

```python
def test_kontrollera_historik_godkanner_riktig_fil():
    if not (ROT / "data" / "historik.json").exists():
        pytest.skip("bygg historik.json först")
    r = subprocess.run([sys.executable, "scripts/kontrollera.py", "data/valdata_2022.json", "majorna-valresultat-2022.xlsx", "--historik", "data/historik.json"],
                       cwd=ROT, capture_output=True, text=True)
    assert r.returncode == 0, r.stdout + r.stderr
    assert "historik" in r.stdout.lower()


def test_kontrollera_historik_upptacker_manipulerad_serie(tmp_path):
    src = ROT / "data" / "historik.json"
    if not src.exists():
        pytest.skip("bygg historik.json först")
    hst = json.loads(src.read_text("utf-8"))
    rad = [p for p in hst["serie"]["rd"]["majorna"] if p["ar"] == 2022][0]
    rad["roster"]["V"] += 1
    p = tmp_path / "historik.json"
    p.write_text(json.dumps(hst), "utf-8")
    r = subprocess.run([sys.executable, "scripts/kontrollera.py", "data/valdata_2022.json", "majorna-valresultat-2022.xlsx", "--historik", str(p)],
                       cwd=ROT, capture_output=True, text=True)
    assert r.returncode != 0 and "historik rd V" in r.stdout + r.stderr
```

- [ ] **Step 2: Kör och se dem falla** (`unrecognized arguments: --historik`).

- [ ] **Step 3: Ändra `scripts/kontrollera.py`**

Läs hur `main` tar sina två argument (sökväg till valdata och xlsx). Byt till `argparse` med två positionella argument plus `--historik`, och lägg till funktionen:

```python
def kontrollera_historik(valdata_path, historik_path):
    """historik.json, nivå majorna, år 2022 -> samma röster och summor som valdata_2022.json. Returnerar lista med diffar."""
    v = json.loads(Path(valdata_path).read_text("utf-8"))
    hst = json.loads(Path(historik_path).read_text("utf-8"))
    ar = v["meta"]["ar"]
    diffar, antal = [], 0
    for val in VAL:
        rad = next((p for p in hst["serie"][val]["majorna"] if p["ar"] == ar), None)
        if rad is None:
            diffar.append(f"DIFF historik {val}: år {ar} saknas i serien")
            continue
        agg = v["aggregat"]["majorna"][val]
        for p, n in agg["roster"].items():
            antal += 1
            if rad["roster"].get(p) != n:
                diffar.append(f"DIFF historik {val} {p} serie={rad['roster'].get(p)} valdata={n}")
        for f in ("giltiga", "rostande", "rostberattigade"):
            antal += 1
            if rad[f] != agg[f]:
                diffar.append(f"DIFF historik {val} {f} serie={rad[f]} valdata={agg[f]}")
    return diffar, antal
```

I `main`: om `--historik` angetts, kör funktionen efter den ordinarie kontrollen, skriv ut diffarna, räkna in dem i slutsummeringen ("OK: <ordinarie summering> plus N historikkontroller") och avsluta med kod 1 om någon diff finns.

- [ ] **Step 4: Kör testerna**, sedan hela sviten. Lägg också till kontrollen sist i `scripts/bygg_data.py`:s anrop av `kontrollera.py` om `data/historik.json` finns, så att bygget av 2022 aldrig glider ifrån serien.

- [ ] **Step 5: Commit**

```bash
git add scripts/kontrollera.py scripts/bygg_data.py tests/test_kontrollera.py
git commit -m "kontrollera.py --historik: områdesserien 2022 måste stämma med valdata_2022

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>"
```

---

### Task 6: Sektionen i sidan - laddning, mening, partilinjer och talrad

**Files:**
- Modify: `valgrafik.js` (MARKUP, `state`, `start`, `renderAllt`, `renderKontroller`, ResizeObserver, nya funktioner)
- Modify: `valgrafik.css`
- Modify: `tests/test_inbaddning.py`

Specen avsnitt 6, bild A. Sektionen ligger efter Röstdelningen, följer kartans `state.val`, har inga knappar. Diagrammet är inline-SVG i pixelmått: viewBox-bredden sätts till ytans faktiska bredd så att text alltid är 12 och 13 px, och ResizeObservern ritar om vid breddändring (samma mönster som kartan). Fyra serier på mobil (V, S, MP, SD), M som femte från 600 px containerbredd. Etiketterna i högerkanten förskjuts lodrätt när de ligger närmare än 15 px och får en kort ledarlinje. Läslinjen flyttas med tryck och med piltangenter; talraden under bilden byter år.

- [ ] **Step 1: Skriv det fallande testet**

```python
def test_historiksektionen_finns_och_foljer_kartans_val():
    js = JS.read_text("utf-8")
    css = CSS.read_text("utf-8")
    assert 'id="historik"' in js and "function renderHistorik()" in js and "function histLinjer(" in js and "function histTalrad(" in js
    assert 'laddaSkript("historik")' in js and 'laddaSkript("distrikt_2006")' in js
    assert 'id="hist-val"' not in js and "hist-knappar" not in js, "sektionen har inga egna valknappar"
    assert ".hist-bild { min-height" in css, "höjden är reserverad innan datan finns"
    assert (ROT / "data" / "historik.js").exists()
```

- [ ] **Step 2: Kör och se det falla**

Run: `/Users/daniel/code/Temp/.venv/bin/python -m pytest tests/test_inbaddning.py -q -k historiksektionen`

- [ ] **Step 3: MARKUP**: lägg in efter `</section>` för `#rostdelning` (före `#fakta`):

```html
  <section id="historik" aria-labelledby="historik-rubrik" hidden>
    <h2 id="historik-rubrik">Majorna sedan 2006</h2>
    <p class="hist-mening" id="hist-mening"></p>
    <div class="hist-bild" id="hist-bild-a"></div>
    <p class="hist-talrad" id="hist-talrad" aria-live="polite"></p>
    <p class="not" id="hist-not-a"></p>
    <div class="hist-rad2">
      <div class="hist-kol">
        <p class="hist-mening" id="hist-mening-b"></p>
        <div class="hist-bild hist-bild-b" id="hist-bild-b"></div>
        <p class="not" id="hist-not-b"></p>
      </div>
      <div class="hist-kol">
        <div class="hist-kartor" id="hist-kartor" aria-hidden="true"></div>
        <p class="not" id="hist-not-kartor"></p>
      </div>
    </div>
  </section>
```

- [ ] **Step 4: `state`** (rad 113 till 115): lägg till `historik: null, historikGeo: null, historikAr: null`.

- [ ] **Step 5: `start()`**: efter raden som laddar swing, före `catch`:

```js
    state.historik = KONFIG.historik && KONFIG.historik.visa === false ? null : await laddaSkript("historik").catch(() => null);
    state.historikGeo = state.historik ? await laddaSkript("distrikt_2006").catch(() => null) : null;
```

`renderAllt` får `renderHistorik();` sist. I `renderKontroller` (flikarnas `onclick`) läggs `renderHistorik();` till efter `renderTabell();`. I ResizeObservern (raden med `renderKarta()`): lägg till `if ((desktopBytte || breddBytte) && state.historik && !state.bild) renderHistorik();`.

- [ ] **Step 6: Nya funktioner**, lägg in före `/* ---- fakta */`:

```js
/* ---- Majorna sedan 2006: områdesserien ur data/historik.js, följer kartans val, inga egna knappar */
const HIST_PARTIER = { mobil: ["V", "S", "MP", "SD"], desktop: ["V", "S", "MP", "SD", "M"] };
const histPartier = () => arDesktop() ? HIST_PARTIER.desktop : HIST_PARTIER.mobil;
function historikSerie(val, niva) {
  const h = state.historik;
  return h && h.serie && h.serie[val] && h.serie[val][niva] ? h.serie[val][niva] : [];
}
function aretsPunkt(val, niva) {
  // det visade året som en punkt i seriens form, bara när alla distrikt är räknade; annars null (ringen "räknas på valnatten")
  const meta = data().meta, ar = Number(meta.ar);
  if (state.historik.meta.ar.includes(ar)) return null;
  const alla = data().distrikt || [], raknade = alla.filter(d => raknat(d, val)).length;
  if (!alla.length || raknade < alla.length) return null;
  const preliminar = meta.status !== "slutlig";
  if (niva === "majorna") {
    const m = majorna(val);
    if (!m || !m.giltiga) return null;
    const andel = {};
    for (const [p, n] of Object.entries(m.roster)) andel[p] = n / m.giltiga;
    return { ar, andel, giltiga: m.giltiga, rostande: m.rostande, rostberattigade: m.rostberattigade,
             valdeltagande: m.rostberattigade ? m.rostande / m.rostberattigade : null, preliminar };
  }
  const post = jamforelse(niva, val);
  if (!post || !post.andel) return null;
  return { ar, andel: post.andel, valdeltagande: post.valdeltagande || null, preliminar };
}
function histPunkter(val, niva) {   // serien plus årets punkt när den finns
  const extra = aretsPunkt(val, niva);
  return historikSerie(val, niva).map(p => ({ ...p, preliminar: false })).concat(extra ? [extra] : []);
}
function histAxelAr(val) {   // årtalen på x-axeln: seriens år plus det visade året, även när det inte får ritas än
  const ar = state.historik.meta.ar.slice(), visat = Number(data().meta.ar);
  return ar.includes(visat) ? ar : ar.concat([visat]);
}
function sistaPunkt(val) { const p = histPunkter(val, "majorna"); return p[p.length - 1]; }
function histMening(val) {
  const egen = ((KONFIG.historik || {}).mening || {})[val];
  if (egen) return egen;
  const serie = historikSerie(val, "majorna"), forsta = serie[0], sista = [...histPunkter(val, "majorna")].reverse().find(p => !p.preliminar) || serie[serie.length - 1];
  const p = "V";
  return `${p} har gått från ${andelTal(forsta.andel[p] || 0)} till ${andelTal(sista.andel[p] || 0)} procent i ${VALNAMN[val].toLowerCase()} sedan ${forsta.ar}.`;
}
function antalDistriktText(val) {   // "17 år 2006, 2010 och 2014, 22 år 2018, 23 år 2022"
  const grupper = [];
  for (const p of histPunkter(val, "majorna")) {
    const n = p.antal_distrikt || (p.ar === Number(data().meta.ar) ? antalDistrikt() : null);
    if (n === null) continue;
    const g = grupper[grupper.length - 1];
    if (g && g.n === n) g.ar.push(p.ar); else grupper.push({ n, ar: [p.ar] });
  }
  const lista = a => a.length === 1 ? String(a[0]) : a.slice(0, -1).join(", ") + " och " + a[a.length - 1];
  return grupper.map(g => `${g.n} år ${lista(g.ar)}`).join(", ");
}
function histLinjer(val) {
  const el = $("#hist-bild-a"), W = Math.max(300, el.clientWidth || 358), H = arDesktop() ? 320 : 280, M = { v: 34, h: 48, t: 14, b: 30 };
  const punkter = histPunkter(val, "majorna"), axelAr = histAxelAr(val), partier = histPartier();
  const max = Math.max(0.4, Math.ceil(Math.max(...punkter.flatMap(p => partier.map(q => p.andel[q] || 0))) * 20) / 20);
  const x = i => M.v + i * (W - M.v - M.h) / Math.max(1, axelAr.length - 1), y = a => M.t + (1 - a / max) * (H - M.t - M.b);
  const beskrivning = partier.map(p => `${parti(p).namn}: ` + punkter.map(pt => `${pt.ar} ${andelTal(pt.andel[p] || 0)}`).join(", ")).join("; ");
  const svg = s("svg", { viewBox: `0 0 ${W} ${H}`, class: "hist-svg", role: "img", tabindex: 0,
    "aria-label": `${histMening(val)} Andel av giltiga röster per valår i procent. ${beskrivning}. Vänster och höger pil byter år i talraden.` });
  for (let a = 0.1; a <= max + 1e-9; a += 0.1) {
    svg.append(s("line", { x1: M.v, x2: W - M.h, y1: y(a).toFixed(1), y2: y(a).toFixed(1), stroke: FARG.linje }),
               s("text", { x: M.v - 6, y: (y(a) + 4).toFixed(1), "text-anchor": "end", "font-size": 12, fill: FARG.sten }, Math.round(a * 100) + (a + 0.1 > max ? " %" : "")));
  }
  axelAr.forEach((a, i) => svg.append(s("text", { x: x(i).toFixed(1), y: H - 8, "text-anchor": "middle", "font-size": 13, fill: FARG.sten }, String(a).slice(2))));
  const slut = [];
  for (const p of partier) {
    const pts = punkter.map((pt, i) => ({ x: x(i), y: y(pt.andel[p] || 0), preliminar: pt.preliminar }));
    const fasta = pts.filter(pt => !pt.preliminar);
    svg.append(s("path", { d: fasta.map((pt, i) => (i ? "L" : "M") + pt.x.toFixed(1) + "," + pt.y.toFixed(1)).join(""), fill: "none", stroke: parti(p).farg, "stroke-width": 2.5, "stroke-linejoin": "round" }));
    if (pts.length > fasta.length) {
      const a = fasta[fasta.length - 1], b = pts[pts.length - 1];
      svg.append(s("path", { d: `M${a.x.toFixed(1)},${a.y.toFixed(1)}L${b.x.toFixed(1)},${b.y.toFixed(1)}`, fill: "none", stroke: parti(p).farg, "stroke-width": 2.5, "stroke-dasharray": "6 5" }));
    }
    for (const pt of pts) svg.append(s("circle", { cx: pt.x.toFixed(1), cy: pt.y.toFixed(1), r: 3.5, fill: pt.preliminar ? FARG.papper : parti(p).farg, stroke: parti(p).farg, "stroke-width": 2 }));
    const sista = pts[pts.length - 1];
    slut.push({ p, px: sista.x, py: sista.y, y: sista.y });
  }
  slut.sort((a, b) => a.y - b.y);   // etiketterna i högerkanten får inte täcka varandra: skjut isär till 15 px och rita en ledarlinje
  for (let i = 1; i < slut.length; i++) if (slut[i].y - slut[i - 1].y < 15) slut[i].y = slut[i - 1].y + 15;
  for (const e of slut) {
    if (Math.abs(e.y - e.py) > 1) svg.append(s("line", { x1: (e.px + 5).toFixed(1), y1: e.py.toFixed(1), x2: (W - M.h + 6).toFixed(1), y2: e.y.toFixed(1), stroke: parti(e.p).farg, "stroke-width": 1 }));
    svg.append(s("text", { x: (W - M.h + 9).toFixed(1), y: (e.y + 4.5).toFixed(1), "font-size": 13, "font-weight": 700, fill: parti(e.p).farg }, e.p));
  }
  if (axelAr.length > punkter.length) {   // det visade året får inte ritas än: tom ring
    const i = axelAr.length - 1;
    svg.append(s("circle", { cx: x(i).toFixed(1), cy: y(max / 2).toFixed(1), r: 5, fill: FARG.papper, stroke: FARG.sten, "stroke-width": 1.5 }));
  }
  const li = axelAr.indexOf(state.historikAr);
  if (li >= 0) svg.append(s("line", { class: "hist-laslinje", x1: x(li).toFixed(1), x2: x(li).toFixed(1), y1: M.t, y2: H - M.b, stroke: FARG.sten, "stroke-dasharray": "3 3" }));
  const narmast = px => { let best = 0; axelAr.forEach((a, i) => { if (Math.abs(x(i) - px) < Math.abs(x(best) - px)) best = i; }); return axelAr[best]; };
  svg.addEventListener("click", e => { const r = svg.getBoundingClientRect(); sattHistorikAr(narmast((e.clientX - r.left) * W / r.width), true); });
  svg.addEventListener("keydown", e => {
    if (e.key !== "ArrowLeft" && e.key !== "ArrowRight") return;
    e.preventDefault();
    const i = Math.max(0, axelAr.indexOf(state.historikAr));
    sattHistorikAr(axelAr[(i + (e.key === "ArrowRight" ? 1 : -1) + axelAr.length) % axelAr.length], true);
  });
  el.replaceChildren(svg);
}
function sattHistorikAr(ar, fokus) {
  state.historikAr = ar;
  histLinjer(state.val); histTalrad(state.val);
  if (fokus) $("#hist-bild-a svg").focus({ preventScroll: true });
}
function histTalrad(val) {
  const el = $("#hist-talrad"), p = histPunkter(val, "majorna").find(q => q.ar === state.historikAr);
  if (!p) { el.textContent = `${state.historikAr}: räknas på valnatten.`; return; }
  el.textContent = `${p.ar}${p.preliminar ? " (preliminärt)" : ""}: ` + histPartier().map(q => `${q} ${andelTal(p.andel[q] || 0)}`).join("   ");
}
function renderHistorik() {
  const sek = $("#historik");
  if (!state.historik || state.bild || historikSerie(state.val, "majorna").length < 2) { sek.hidden = true; return; }
  sek.hidden = false;
  const val = state.val;
  if (!histAxelAr(val).includes(state.historikAr)) state.historikAr = sistaPunkt(val).ar;
  $("#hist-mening").textContent = histMening(val);
  histLinjer(val);
  histTalrad(val);
  $("#hist-not-a").textContent = `Serien börjar 2006. Valdistrikten ritades om helt inför det valet, så 2002 går inte att räkna om till dagens Majorna. Området hålls konstant medan antalet distrikt varierar: ${antalDistriktText(val)}. Liberalerna hette Folkpartiet till och med 2014.`;
  histDeltagande(val);
  histKartor();
}
function histDeltagande(val) { $("#hist-bild-b").innerHTML = ""; }   // Task 7
function histKartor() { $("#hist-kartor").innerHTML = ""; }          // Task 8
```

- [ ] **Step 7: CSS**, efter Röstdelningens regler:

```css
/* Majorna sedan 2006: linjediagram i pixelmått (viewBox = ytans bredd), talrad under, konturkartor. Höjder reserverade. */
.mp-val .hist-mening { font-size: 18px; line-height: 1.4; margin: 0 0 10px; }
.mp-val .hist-bild { min-height: 280px; margin: 0 0 6px; }
.mp-val .hist-bild-b { min-height: 160px; }
.mp-val .hist-bild svg { width: 100%; height: auto; display: block; font-family: var(--sans); }
.mp-val .hist-svg { cursor: pointer; }
.mp-val .hist-talrad { font-variant-numeric: tabular-nums; margin: 0 0 4px; white-space: nowrap; overflow: hidden; }
.mp-val .hist-rad2 { display: grid; gap: 16px; margin-top: 20px; }
.mp-val .hist-kartor { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; min-height: 160px; }
.mp-val .hist-figur { margin: 0; }
.mp-val .hist-figur svg { width: 100%; height: auto; display: block; }
.mp-val .hist-figur figcaption { font-size: 13px; color: var(--sten); text-align: center; margin-top: 4px; }
```

och i desktopblocket (`@container (min-width: 900px)`):

```css
  .mp-val .hist-rad2 { grid-template-columns: 1fr 1fr; column-gap: 40px; align-items: start; }
  .mp-val .hist-bild { min-height: 320px; }
```

- [ ] **Step 8: Kör och titta**

```bash
cd /Users/daniel/code/Temp && .venv/bin/python -m pytest -q && NODE_PATH=verktyg/node_modules node verktyg/skal-check.js && node verktyg/sektion.js http://localhost:8765/index.html "#historik" /tmp/hist-390.png 390 && node verktyg/sektion.js http://localhost:8765/index.html "#historik" /tmp/hist-1280.png 1280
```

Titta på båda bilderna: meningen "V har gått från 17,2 till 27,2 procent i riksdagsvalet sedan 2006.", fyra linjer på mobil och fem på desktop, årtalen 06 10 14 18 22 26 på x-axeln, en tom ring på 26, etiketterna V och S isär i högerkanten, talraden "2022: V 27,2   S 25,9   MP 15,7   SD 10,1". Byt till Kommun vid kartan och kontrollera att meningen blir "från 14,5 till 34,6". Om V, S och SD-etiketterna kolliderar trots förskjutningen, höj avståndet till 16 px.

- [ ] **Step 9: Commit**

```bash
git add valgrafik.js valgrafik.css tests/test_inbaddning.py
git commit -m "Majorna sedan 2006: sektionen med mening, partilinjer 2006 till i dag, läslinje och talrad, följer kartans val

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>"
```

---

### Task 7: Bild B - valdeltagandet Majorna mot Göteborg

**Files:**
- Modify: `valgrafik.js` (`histDeltagande`)
- Modify: `tests/test_inbaddning.py`

Två linjer på mobil (Majorna i slottsskogsgrön 2,5 px, Göteborg i sten 2 px), riket som tredje linje från 600 px och bara i riksdagsvalet (historikfilens `riket` för regionvalet är inte Västra Götaland). Y-axeln från närmaste 5 procent under lägsta värdet till närmaste 5 över högsta, aldrig smalare än 70 till 90. Rubrikmening ur datan, bildtext om skalan och om att valdeltagande i olika val inte ska jämföras.

- [ ] **Step 1: Skriv det fallande testet**

```python
def test_valdeltagandebilden():
    js = JS.read_text("utf-8")
    assert "function histDeltagande(val) {" in js and "Skalan börjar vid" in js
    assert "riket" in js.split("function histDeltagande")[1].split("function histKartor")[0]
```

- [ ] **Step 2: Kör och se det falla** (den tomma `histDeltagande` innehåller inte texten).

- [ ] **Step 3: Ersätt `histDeltagande`**

```js
function histDeltagande(val) {
  const el = $("#hist-bild-b"), W = Math.max(280, el.clientWidth || 358), H = 170, M = { v: 34, h: 66, t: 12, b: 26 };
  const serier = [{ namn: "Majorna", niva: "majorna", farg: FARG.gron || "#3F5A3A", bredd: 2.5, streck: null },
                  { namn: "Göteborg", niva: "goteborg", farg: FARG.sten, bredd: 2, streck: null }];
  if (arDesktop() && val === "rd") serier.push({ namn: "Riket", niva: "riket", farg: FARG.sten, bredd: 1.5, streck: "5 4" });
  const data_ = serier.map(sr => ({ ...sr, punkter: histPunkter(val, sr.niva).filter(p => p.valdeltagande) }));
  const alla = data_.flatMap(sr => sr.punkter.map(p => p.valdeltagande));
  if (!alla.length) { el.innerHTML = ""; $("#hist-mening-b").textContent = ""; $("#hist-not-b").textContent = ""; return; }
  const lo = Math.min(0.7, Math.floor(Math.min(...alla) * 20) / 20), hi = Math.max(0.9, Math.ceil(Math.max(...alla) * 20) / 20);
  const axelAr = histAxelAr(val);
  const x = ar => M.v + axelAr.indexOf(ar) * (W - M.v - M.h) / Math.max(1, axelAr.length - 1), y = v => M.t + (1 - (v - lo) / (hi - lo)) * (H - M.t - M.b);
  const maj = data_[0].punkter, gbg = data_[1].punkter;
  const sistaM = [...maj].reverse().find(p => !p.preliminar), sistaG = sistaM && gbg.find(p => p.ar === sistaM.ar);
  const mening = sistaM && sistaG ? `Valdeltagande i ${VALNAMN[val].toLowerCase()} ${sistaM.ar}: Majorna ${andelTal(sistaM.valdeltagande)} procent, Göteborg ${andelTal(sistaG.valdeltagande)}.` : "";
  $("#hist-mening-b").textContent = mening;
  const beskrivning = data_.map(sr => `${sr.namn}: ` + sr.punkter.map(p => `${p.ar} ${andelTal(p.valdeltagande)}`).join(", ")).join("; ");
  const svg = s("svg", { viewBox: `0 0 ${W} ${H}`, role: "img", "aria-label": `${mening} Valdeltagande i procent per valår. ${beskrivning}.` });
  for (let v = lo; v <= hi + 1e-9; v += 0.05) {
    svg.append(s("line", { x1: M.v, x2: W - M.h, y1: y(v).toFixed(1), y2: y(v).toFixed(1), stroke: FARG.linje }),
               s("text", { x: M.v - 6, y: (y(v) + 4).toFixed(1), "text-anchor": "end", "font-size": 12, fill: FARG.sten }, Math.round(v * 100) + (v + 0.05 > hi ? " %" : "")));
  }
  axelAr.forEach(a => svg.append(s("text", { x: x(a).toFixed(1), y: H - 6, "text-anchor": "middle", "font-size": 13, fill: FARG.sten }, String(a).slice(2))));
  const slut = [];
  for (const sr of data_) {
    const fasta = sr.punkter.filter(p => !p.preliminar), pts = sr.punkter;
    svg.append(s("path", { d: fasta.map((p, i) => (i ? "L" : "M") + x(p.ar).toFixed(1) + "," + y(p.valdeltagande).toFixed(1)).join(""), fill: "none", stroke: sr.farg, "stroke-width": sr.bredd, "stroke-dasharray": sr.streck, "stroke-linejoin": "round" }));
    if (pts.length > fasta.length) { const a = fasta[fasta.length - 1], b = pts[pts.length - 1];
      svg.append(s("path", { d: `M${x(a.ar).toFixed(1)},${y(a.valdeltagande).toFixed(1)}L${x(b.ar).toFixed(1)},${y(b.valdeltagande).toFixed(1)}`, fill: "none", stroke: sr.farg, "stroke-width": sr.bredd, "stroke-dasharray": "6 5" })); }
    for (const p of pts) svg.append(s("circle", { cx: x(p.ar).toFixed(1), cy: y(p.valdeltagande).toFixed(1), r: 3, fill: p.preliminar ? FARG.papper : sr.farg, stroke: sr.farg, "stroke-width": 2 }));
    const sista = pts[pts.length - 1];
    slut.push({ namn: sr.namn, farg: sr.farg, px: x(sista.ar), py: y(sista.valdeltagande), y: y(sista.valdeltagande) });
  }
  slut.sort((a, b) => a.y - b.y);
  for (let i = 1; i < slut.length; i++) if (slut[i].y - slut[i - 1].y < 15) slut[i].y = slut[i - 1].y + 15;
  for (const e of slut) {
    if (Math.abs(e.y - e.py) > 1) svg.append(s("line", { x1: (e.px + 5).toFixed(1), y1: e.py.toFixed(1), x2: (W - M.h + 6).toFixed(1), y2: e.y.toFixed(1), stroke: e.farg, "stroke-width": 1 }));
    svg.append(s("text", { x: (W - M.h + 9).toFixed(1), y: (e.y + 4.5).toFixed(1), "font-size": 13, fill: e.farg === FARG.sten ? FARG.sten : FARG.black }, e.namn));
  }
  el.replaceChildren(svg);
  const gbgSlut = data_[1].punkter.length < axelAr.length ? ` Göteborgs linje slutar ${data_[1].punkter[data_[1].punkter.length - 1].ar} tills aggregatet för det visade året finns.` : "";
  $("#hist-not-b").textContent = `Skalan börjar vid ${Math.round(lo * 100)} procent. Valdeltagande i olika val ska inte jämföras med varandra, eftersom röstberättigade skiljer sig mellan valen.` + gbgSlut;
}
```

`FARG` saknar `gron`; lägg till `gron: "#3F5A3A"` i `FARG` (rad 111).

- [ ] **Step 4: Kör och titta**

```bash
cd /Users/daniel/code/Temp && .venv/bin/python -m pytest -q && node verktyg/sektion.js http://localhost:8765/index.html "#historik" /tmp/hist-390.png 390 && node verktyg/sektion.js http://localhost:8765/index.html "#historik" /tmp/hist-1280.png 1280
```

Titta: meningen "Valdeltagande i riksdagsvalet 2022: Majorna 82,8 procent, Göteborg 80,7.", två linjer som ligger på varandra 2006 till 2018 och skiljs 2022, y-axel 70 till 90, på desktop en streckad riketlinje ovanför. I kommunvalet ligger Majorna över Göteborg alla år.

- [ ] **Step 5: Commit**

```bash
git add valgrafik.js tests/test_inbaddning.py
git commit -m "Majorna sedan 2006: valdeltagandet Majorna mot Göteborg, riket på desktop i riksdagsvalet

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>"
```

---

### Task 8: Konturkartorna och den kortade Om siffrorna

**Files:**
- Modify: `valgrafik.js` (`histKartor`, `renderFakta`)
- Modify: `tests/test_inbaddning.py`

Två små kartor sida vid sida: 2006 (17 distrikt, ur `distrikt_2006`) och det visade året (ur `geo()`), bara gränser i sten på papper, gemensam ram, inga etiketter, `aria-hidden` med bildtexten som innehåll. Sist i sektionen meningen som stänger frågan om ålder. Om siffrorna kortas till avgränsning, källa och andelsdefinition; valdeltagandet står nu i bild B och "Byggd av Majposten" i sidfoten.

- [ ] **Step 1: Skriv det fallande testet**

```python
def test_konturkartor_och_kortad_om_siffrorna():
    js = JS.read_text("utf-8")
    fakta = js.split("function renderFakta()")[1]
    assert "Samma yta, fler distrikt" in js and "Valhemligheten gäller per distrikt" in js
    assert "Valdeltagande i Majorna" not in fakta and "Byggd av Majposten" not in fakta
    assert "hist-figur" in js
```

- [ ] **Step 2: Kör och se det falla**

- [ ] **Step 3: Ersätt `histKartor`**

```js
function histKartor() {
  const el = $("#hist-kartor"), g06 = state.historikGeo, gNu = geo();
  if (!g06 || !gNu) { el.innerHTML = ""; $("#hist-not-kartor").textContent = ""; return; }
  const bbox = [Math.min(g06.bbox[0], gNu.bbox[0]), Math.min(g06.bbox[1], gNu.bbox[1]), Math.max(g06.bbox[2], gNu.bbox[2]), Math.max(g06.bbox[3], gNu.bbox[3])];
  const proj = projektion(bbox, 0.02, 0.02);
  const karta = (fc, text) => {
    const svg = s("svg", { viewBox: `0 0 ${proj.bredd} ${proj.hojd.toFixed(1)}`, class: "hist-karta" });
    for (const f of fc.features) svg.append(s("path", { d: dAttr(f.geometry.coordinates[0], proj, true), fill: "none", stroke: FARG.sten, "stroke-width": 3, "stroke-linejoin": "round" }));
    return h("figure", { class: "hist-figur" }, svg, h("figcaption", {}, text));
  };
  el.replaceChildren(karta(g06, `2006, ${g06.features.length} distrikt`), karta(gNu, `${data().meta.ar}, ${gNu.features.length} distrikt`));
  $("#hist-not-kartor").textContent = "Samma yta, fler distrikt. Ett kvarter 2006 är ofta två i dag. Hur olika åldrar röstade går inte att veta. Valhemligheten gäller per distrikt, inte per person.";
}
```

- [ ] **Step 4: Korta `renderFakta`** till:

```js
function renderFakta() {
  const meta = data().meta;
  const li = [`Avgränsning: ${meta.avgransning}.`,
              `Källa: ${meta.kalla}. ${meta.status === "slutlig" ? "Slutligt resultat." : "Preliminärt resultat."} Andel = partiets röster delat med giltiga röster.`];
  $("#faktalista").replaceChildren(...li.map(t => h("li", {}, t)));
  $("#fot").replaceChildren(h("p", {}, "Så röstade Majorna - en valgrafik från Majposten. Valdata: Valmyndigheten." + (state.bakgrund ? " Kartunderlag © OpenStreetMaps bidragsgivare (ODbL)." : "")));
}
```

- [ ] **Step 5: Kör och titta**

```bash
cd /Users/daniel/code/Temp && .venv/bin/python -m pytest -q && NODE_PATH=verktyg/node_modules node verktyg/skal-check.js && node verktyg/sektion.js http://localhost:8765/index.html "#historik" /tmp/hist-390.png 390 && node verktyg/sektion.js http://localhost:8765/docs/inbaddningstest.html "#historik" /tmp/hist-vard-1280.png 1280
```

Titta: två konturer sida vid sida på 390 px med samma yttre form, 17 fält till vänster och 23 till höger, bildtexterna "2006, 17 distrikt" och "2022, 23 distrikt", meningen under. På desktop ligger valdeltagandet i vänster kolumn och kartorna i höger.

- [ ] **Step 6: Commit**

```bash
git add valgrafik.js tests/test_inbaddning.py
git commit -m "Majorna sedan 2006: konturkartor 2006 mot i dag, meningen om ålder, Om siffrorna kortad

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>"
```

---

### Task 9: Lägena för 2026 och webbläsarkontrollen `historik-check.js`

**Files:**
- Modify: `verktyg/forbered_tvaar.py` (nytt argument `--partiell N`)
- Create: `verktyg/historik-check.js`
- Modify: `verktyg/README.md`

Specen avsnitt 7: så länge räkningen pågår slutar linjerna vid 2022 och 2026 är en tom ring med talraden "2026: räknas på valnatten."; när alla distrikt är räknade men preliminärt ritas 2026 som öppen ring med streckad sista sträcka och "(preliminärt)" i talraden; när status är slutlig blir punkten fylld. Koden från Task 6 och 7 gör det redan via `aretsPunkt`; den här tasken bevisar det.

- [ ] **Step 1: `--partiell N` i `verktyg/forbered_tvaar.py`**: efter kopieringen av `valdata_2026.js`, om `a.partiell` är satt, läs `Path(a.valnatt_data) / "valdata_2026.json"`, sätt `raknat: False` och tomma `rd`, `rf`, `kf`, `giltiga`, `rostande`, `rostberattigade` på alla distrikt utom de N första, bygg om med `schema.bygg_valdata(2026, distrikt, "preliminar", v["aggregat"] ur goteborg/riket, v["mandat"], uppdaterad=v["meta"]["uppdaterad"], kalla=v["meta"]["kalla"])`, behåll flaggorna `jamforbar_mot_bas` och `grans_andrad` per distrikt, skriv om `valdata_2026` i testmappen med `schema.skriv`, och skriv `swing_2026` på nytt med `schema.swing(v, bas2022, jamforbara=[koder med jamforbar_mot_bas])` där `bas2022` är `data/valdata_2022.json`. Lägg till `ap.add_argument("--partiell", type=int, default=0, help="markera bara de N första distrikten som räknade")`.

- [ ] **Step 2: `verktyg/historik-check.js`**

```js
const puppeteer = require('puppeteer-core');
const url = process.argv[2] || 'http://localhost:8765/index.html';
const vantat = process.argv[3] || 'slutlig';   // slutlig | preliminar | partiell
(async () => {
  const browser = await puppeteer.launch({ executablePath: '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome', headless: true, args: ['--no-first-run', '--disable-gpu'] });
  const page = await browser.newPage();
  const fel = []; page.on('pageerror', e => fel.push(String(e)));
  const las = async bredd => {
    await page.setViewport(bredd < 600 ? { width: bredd, height: 844, deviceScaleFactor: 2, isMobile: true, hasTouch: true } : { width: bredd, height: 900 });
    await page.goto(url, { waitUntil: 'networkidle0' });
    await new Promise(r => setTimeout(r, 1500));
    return page.evaluate(() => {
      const rot = document.getElementById('valgrafik'), svg = rot.querySelector('#hist-bild-a svg');
      const etiketter = [...svg.querySelectorAll('text[font-weight="700"]')].map(t => ({ p: t.textContent, y: Number(t.getAttribute('y')) })).sort((a, b) => a.y - b.y);
      const minAvstand = Math.min(...etiketter.slice(1).map((e, i) => e.y - etiketter[i].y));
      return { synlig: !rot.querySelector('#historik').hidden, mening: rot.querySelector('#hist-mening').textContent, talrad: rot.querySelector('#hist-talrad').textContent,
               serier: etiketter.map(e => e.p), minAvstand, streckade: svg.querySelectorAll('path[stroke-dasharray="6 5"]').length,
               oppnaRingar: [...svg.querySelectorAll('circle')].filter(c => c.getAttribute('fill') === '#FAF6EE').length,
               xEtiketter: [...svg.querySelectorAll('text')].map(t => t.textContent).filter(t => /^\d\d$/.test(t)),
               kartor: rot.querySelectorAll('#hist-kartor figure').length, kartText: [...rot.querySelectorAll('#hist-kartor figcaption')].map(f => f.textContent),
               meningB: rot.querySelector('#hist-mening-b').textContent, notB: rot.querySelector('#hist-not-b').textContent,
               svgBredd: Number(svg.getAttribute('viewBox').split(' ')[2]) };
    });
  };
  const mobil = await las(390);
  await page.focus('#hist-bild-a svg'); await page.keyboard.press('ArrowLeft'); await new Promise(r => setTimeout(r, 300));
  const efterPil = await page.evaluate(() => document.getElementById('valgrafik').querySelector('#hist-talrad').textContent);
  const desktop = await las(1280);
  const ok = mobil.synlig && mobil.serier.join('') === 'VSMPSD'.replace(/(V|S|MP|SD)/g, '$1') && mobil.serier.length === 4 && desktop.serier.length === 5
    && mobil.minAvstand >= 14 && desktop.minAvstand >= 14 && mobil.kartor === 2 && mobil.xEtiketter.join(' ') === '06 10 14 18 22 26'
    && (vantat === 'partiell' ? mobil.talrad.includes('räknas på valnatten') && mobil.oppnaRingar === 1
      : vantat === 'preliminar' ? mobil.talrad.includes('preliminärt') && mobil.streckade >= 4
      : !mobil.talrad.includes('räknas') && !mobil.talrad.includes('preliminärt'))
    && efterPil !== mobil.talrad && mobil.svgBredd < 400 && desktop.svgBredd > 800 && fel.length === 0;
  console.log(JSON.stringify({ mobil, efterPil, desktop }, null, 1));
  console.log(fel.length ? 'JS-FEL: ' + fel.join(' | ') : 'inga JS-fel');
  console.log(ok ? 'HISTORIKKONTROLL OK' : 'HISTORIKKONTROLL MISSLYCKADES');
  await browser.close();
  process.exit(ok ? 0 : 1);
})().catch(e => { console.error(e); process.exit(1); });
```

Villkoret för serieordningen på mobil ska vara `mobil.serier.length === 4 && mobil.serier.every(p => ['V', 'S', 'MP', 'SD'].includes(p))` (etiketterna är sorterade på y, inte på partiordning); ersätt den krångliga raden med det.

- [ ] **Step 3: Kör de tre lägena**

```bash
cd /Users/daniel/code/Temp && NODE_PATH=verktyg/node_modules node verktyg/historik-check.js http://localhost:8765/index.html slutlig \
&& .venv/bin/python verktyg/forbered_tvaar.py --valnatt-data /tmp/valnatt-test/data --valnatt && NODE_PATH=verktyg/node_modules node verktyg/historik-check.js http://localhost:8765/tmp/tvaar/index.html preliminar \
&& .venv/bin/python verktyg/forbered_tvaar.py --valnatt-data /tmp/valnatt-test/data --valnatt --partiell 9 && NODE_PATH=verktyg/node_modules node verktyg/historik-check.js http://localhost:8765/tmp/tvaar/index.html partiell
```

Expected: `HISTORIKKONTROLL OK` tre gånger. I det partiella läget ska statusraden dessutom säga "9 av 23" (kontrollera med `node verktyg/tvaar-check.js` som redan läser statusraden) och kortet för Hela Majorna säga "räknat på 9 av 23 distrikt". Ta skärmdumpar av sektionen i alla tre lägena på 390 px och titta: tom ring, öppen ring med streckad sträcka, fylld punkt.

- [ ] **Step 4: Kör hela sviten och de övriga kontrollerna** (`skal-check`, `beehiiv-check`, `vard-check`, `tvaar-check`), lägg till `historik-check.js` och `--partiell` i `verktyg/README.md`.

- [ ] **Step 5: Commit**

```bash
git add verktyg/forbered_tvaar.py verktyg/historik-check.js verktyg/README.md
git commit -m "Historikkontroll i webbläsaren: tre lägen för 2026, etikettavstånd, tangentbord, konturkartor

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>"
```

---

### Task 10: Dokumentation

**Files:**
- Modify: `README.md`, `docs/HANDOVER.md`, `docs/historik/README.md`

- [ ] **Step 1: README**: i Mappen lägg till `scripts/bygg_historik.py`, `data/historik.json / .js`, `data/swing_2022.*`, `data/distrikt_2006.*`, `data/valdata_<år>` och `distrikt_<år>` för 2006 till 2018 (byggda, laddas inte). Nytt avsnitt "Historiken" efter "Stillbilder": vad sektionen visar, att den följer kartans val, hur `bygg_historik.py allt` körs om (databasen först), konfignyckeln `historik` (`visa`, `mening` per val), att 2002 utelämnas och varför, och att ett historikår kan läggas i `ar` för att visas på kartan (17 respektive 22 distrikt). I Dataschema: `historik.json` (meta och serie) och `swing_2022.json` (nio jämförbara, fjorton med bakåtvänd mening, områdesnivån ur serien). Uppdatera sidvikten med uppmätt tal (`du -ch valgrafik.js valgrafik.css data/konfig.js data/valdata_2022.js data/distrikt_2022.js data/bakgrund.js data/historik.js data/swing_2022.js data/distrikt_2006.js | tail -1`).

- [ ] **Step 2: HANDOVER**: statusavsnitt för historiksektionen (vad som byggts, filerna, kontrollerna), beslut om linjerna (V, S, MP, SD, M från 600 px), att 2002 inte visas, att kortets bakåtvända rad kommer ur `swing_2022`, fallgropar (`historik.js` laddas vid start, `distrikt_2006` är förenklad och får inte användas som karta för kvarteren, `aretsPunkt` avgör när 2026 ritas). Startpunkt för nästa session: stillbilder av områdesserien i `skapa_bilder.py`, årsväljare på kartan för historikåren om Daniel vill, "Tre saker som skiljer Majorna" (specen avsnitt 11 punkt 6), Codex 16 och 17.

- [ ] **Step 3: `docs/historik/README.md`**: en rad om att sidan nu läser databasen via `scripts/bygg_historik.py`, och att `kontrollera.py --historik` binder serien till 2022 års valdata.

- [ ] **Step 4: Kör allt en sista gång** (pytest, skal-check, beehiiv-check, vard-check, tvaar-check, historik-check i tre lägen), mät sidvikten och skriv in den.

- [ ] **Step 5: Commit**

```bash
git add README.md docs/HANDOVER.md docs/historik/README.md
git commit -m "Dokumentation för historiksektionen och byggskriptet

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>"
```

---

## Självgranskning mot specen

- Avsnitt 6, meningen: Task 6 (`histMening`, överskrivning via `KONFIG.historik.mening`). Bild A med fyra serier på mobil och M på desktop, läslinje, piltangenter, talrad, tom ring, förskjutna etiketter, `role="img"`: Task 6. Bild B: Task 7. Konturkartorna utan partifärg, `aria-hidden`, bildtext och meningen om ålder: Task 8. Desktop (bild A över båda kolumnerna, B till vänster, kartorna till höger): Task 6 CSS. Lägena för 2026 (linjerna slutar vid 2022 tills alla är räknade, öppen ring preliminärt, fylld punkt slutligt, frusen mening): `aretsPunkt` och `histMening` i Task 6, bevisade i Task 9.
- Avsnitt 5, bakåt: `swing_2022` med den bakåtvända meningen och områdesraden ur serien: Task 2. Kortet behöver ingen ändring (valnattsplanens Task 11).
- Avsnitt 8, filerna: `historik.json` Task 1, `swing_2022` Task 2, `distrikt_2006` Task 3, `valdata_<år>` och `distrikt_<år>` för 2006 till 2018 Task 4, `kontrollera.py` Task 5. Sidvikt mäts i Task 10.
- Avsnitt 3 rad 6 (Om siffrorna kortad): Task 8.
- Inte i planen: stillbilder av områdesserien, årsväljare på kartan för historikåren, "Tre saker som skiljer Majorna", borttagning av Partistyrka. Alla står som Daniels beslut efter valet i specen.

Namn som återkommer: `historikSerie(val, niva)`, `histPunkter(val, niva)`, `aretsPunkt(val, niva)`, `histAxelAr(val)`, `sistaPunkt(val)`, `histMening(val)`, `histLinjer(val)`, `histTalrad(val)`, `sattHistorikAr(ar, fokus)`, `histDeltagande(val)`, `histKartor()`, `renderHistorik()`; `state.historik`, `state.historikGeo`, `state.historikAr`; filerna `data/historik.js` (`window.MAJPOSTEN.data["historik"]`) och `data/distrikt_2006.js`; `schema.swing(ny, bas, jamforbara, meningar)` från valnattsplanen; `FARG.gron` läggs till i Task 7.
