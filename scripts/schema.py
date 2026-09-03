"""Datafilernas schema: bygger valdata-objektet, swing mot ett basår, skriver .json + .js."""
import datetime as dt
import json
from pathlib import Path

from .valmyndigheten import AVGRANSNING, VAL, partinamn

JS_PREFIX = 'window.MAJPOSTEN=window.MAJPOSTEN||{data:{}};window.MAJPOSTEN.data['
KALLA_STANDARD = "Valmyndigheten, rösträkning per valdistrikt"
KONFIG_STANDARD = {
    "ar": ["2022"], "standardAr": "2022", "valnatt": False,
    "adress": "https://majposten.se/val2026",
    "inbaddad": False, "skrivUrl": True, "stickyTopp": 16,
}


def skriv_js(stam, obj):
    """Skriver <stam>.js: samma data som JSON-filen, laddningsbar via <script> även från file://."""
    stam = Path(stam)
    stam.parent.mkdir(parents=True, exist_ok=True)
    kompakt = json.dumps(obj, ensure_ascii=False, separators=(",", ":"))
    stam.with_suffix(".js").write_text(f"{JS_PREFIX}{json.dumps(stam.name)}]={kompakt};\n", "utf-8")
    return stam.with_suffix(".js")


def skriv(stam, obj, json_suffix=".json"):
    """Skriver <stam>.json (läsbar) och <stam>.js (identisk data)."""
    stam = Path(stam)
    stam.parent.mkdir(parents=True, exist_ok=True)
    stam.with_suffix(json_suffix).write_text(json.dumps(obj, ensure_ascii=False, indent=1) + "\n", "utf-8")
    return stam.with_suffix(json_suffix), skriv_js(stam, obj)


def las_js(path):
    text = Path(path).read_text("utf-8")
    if not text.startswith(JS_PREFIX):
        raise ValueError(f"{path}: inte en datafil skriven av schema.skriv")
    start = text.index("]=", len(JS_PREFIX)) + 2
    return json.loads(text[start:].rstrip().rstrip(";"))


def _summa(distrikt, val):
    roster, giltiga, rostande, rostberattigade = {}, 0, 0, 0
    for d in distrikt:
        if not d.get("raknat", True) or not d.get(val):
            continue
        for p, n in d[val].items():
            roster[p] = roster.get(p, 0) + n
        giltiga += d["giltiga"].get(val, 0)
        rostande += d["rostande"].get(val, 0)
        rostberattigade += d["rostberattigade"].get(val, 0)
    return {"roster": roster, "giltiga": giltiga, "rostande": rostande, "rostberattigade": rostberattigade}


def bygg_valdata(ar, distrikt, status="slutlig", jamforelser=None, mandat=None, uppdaterad=None, kalla=None):
    """Sätter ihop valdata-objektet. `distrikt` är en lista med poster enligt specen
    (kod, namn, raknat, rd, rf, kf, giltiga, rostande, rostberattigade)."""
    jamforelser = jamforelser or {}
    lista = []
    for d in sorted(distrikt, key=lambda x: x["kod"]):
        post = {"kod": d["kod"], "namn": d["namn"], "raknat": bool(d.get("raknat", True))}
        for val in VAL:
            post[val] = dict(d.get(val) or {})
        for k in ("giltiga", "rostande", "rostberattigade"):
            post[k] = dict(d.get(k) or {})
        lista.append(post)
    raknade = sum(1 for d in lista if d["raknat"])
    meta = {
        "ar": int(ar),
        "status": status,
        "uppdaterad": uppdaterad or dt.datetime.now().replace(microsecond=0).isoformat(),
        "kalla": kalla or KALLA_STANDARD,
        "avgransning": AVGRANSNING,
        "val": dict(VAL),
        "partier": partinamn(),
        "valnatt": {"raknade": raknade, "totalt": len(lista)},
    }
    return {
        "meta": meta,
        "distrikt": lista,
        "aggregat": {
            "majorna": {val: _summa(lista, val) for val in VAL},
            "goteborg": jamforelser.get("goteborg", {}),
            "riket": jamforelser.get("riket", {}),
        },
        "mandat": mandat or {},
    }


def _diff(ny_roster, ny_giltiga, bas_roster, bas_giltiga):
    partier = list(ny_roster) + [p for p in bas_roster if p not in ny_roster]
    return {p: round((ny_roster.get(p, 0) / ny_giltiga - bas_roster.get(p, 0) / bas_giltiga) * 100, 1)
            for p in partier}


def swing(ny, bas):
    """Förändring i procentenheter per distrikt och för hela Majorna, ny mot bas. Bara räknade distrikt."""
    bas_d = {d["kod"]: d for d in bas["distrikt"]}
    ut = {"ar": ny["meta"]["ar"], "bas": bas["meta"]["ar"], "enhet": "procentenheter", "distrikt": {}, "majorna": {}}
    for d in ny["distrikt"]:
        b = bas_d.get(d["kod"])
        if not d.get("raknat", True) or b is None:
            continue
        per_val = {}
        for val in VAL:
            if d.get(val) and b.get(val) and d["giltiga"].get(val) and b["giltiga"].get(val):
                per_val[val] = _diff(d[val], d["giltiga"][val], b[val], b["giltiga"][val])
        if per_val:
            ut["distrikt"][d["kod"]] = per_val
    for val in VAL:
        n = ny["aggregat"]["majorna"].get(val, {})
        b = bas["aggregat"]["majorna"].get(val, {})
        if n.get("giltiga") and b.get("giltiga"):
            ut["majorna"][val] = _diff(n["roster"], n["giltiga"], b["roster"], b["giltiga"])
        else:
            ut["majorna"][val] = {}
    return ut


def las_konfig(mapp):
    """data/konfig.json om den finns, annars standardkonfigen."""
    p = Path(mapp) / "konfig.json"
    if p.exists():
        return {**KONFIG_STANDARD, **json.loads(p.read_text("utf-8"))}
    return dict(KONFIG_STANDARD)


def skriv_konfig(mapp, konfig):
    """Skriver data/konfig.json och data/konfig.js (läses av valgrafik.js före datafilerna)."""
    return skriv(Path(mapp) / "konfig", konfig)
