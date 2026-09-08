"""Datafilernas schema: bygger valdata-objektet, swing mot ett basår, skriver .json + .js."""
import datetime as dt
import copy
import json
import os
from pathlib import Path

from .valmyndigheten import AVGRANSNING, OVRIGA, VAL, partinamn

JS_PREFIX = 'window.MAJPOSTEN=window.MAJPOSTEN||{data:{}};window.MAJPOSTEN.data['
KALLA_STANDARD = "Valmyndigheten, rösträkning per valdistrikt"
KONFIG_STANDARD = {
    "ar": ["2022"], "standardAr": "2022", "valnatt": False,
    "adress": "https://majposten.se/val2026",
    "inbaddad": False, "skrivUrl": True, "stickyTopp": 105,   # Beehiivs klibbiga meny är 89 px hög
    "valdag": "2026-09-13",                       # visas i statusraden före valdagen
    "toppsvar": {"mening": ""},                    # redaktionell mening under toppsvaret, tom = ingen mening
    "historik": {"visa": True, "mening": {"rd": "", "rf": "", "kf": ""}},   # sektionen Majorna sedan 2006, egen plan
    # Samarbetsblocket och rösthjälpen är avstängda tills redaktionen fyllt i texter och adresser.
    "samarbete": {
        "visa": False, "namn": "Majornas Bryggeri", "text": "I samarbete med", "lank": "", "logga": "",
        "valvaka": {"visa": False, "rubrik": "Valvaka på Majornas Bryggeri",
                    "text": "[KOLLA] Tid, plats och vad som händer.", "lank": ""},
    },
    # "extra" är en avslutande mening som sidan bara visar från 600 px containerbredd: på en telefon
    # blir rutan annars en textvägg. Tom som standard, redaktionen fyller den i data/konfig.json.
    "hjalp": {
        "visa": False, "rubrik": "Behöver du hjälp att rösta?",
        "text": "hjalpmigrosta.se förklarar hur valet går till, på flera språk.",
        "extra": "", "lank": "https://hjalpmigrosta.se", "lanktext": "Till hjalpmigrosta.se",
    },
}


def _skriv_atomiskt(path, text):
    """Skriver till <fil>.tmp och byter namn: läsaren ser aldrig en halvskriven fil."""
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_text(text, "utf-8")
    os.replace(tmp, path)


def skriv_js(stam, obj):
    """Skriver <stam>.js: samma data som JSON-filen, laddningsbar via <script> även från file://."""
    stam = Path(stam)
    stam.parent.mkdir(parents=True, exist_ok=True)
    kompakt = json.dumps(obj, ensure_ascii=False, separators=(",", ":"))
    _skriv_atomiskt(stam.with_suffix(".js"), f"{JS_PREFIX}{json.dumps(stam.name)}]={kompakt};\n")
    return stam.with_suffix(".js")


def skriv(stam, obj, json_suffix=".json"):
    """Skriver <stam>.json (läsbar) och <stam>.js (identisk data), båda atomiskt."""
    stam = Path(stam)
    stam.parent.mkdir(parents=True, exist_ok=True)
    _skriv_atomiskt(stam.with_suffix(json_suffix), json.dumps(obj, ensure_ascii=False, indent=1) + "\n")
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
    """Procentenheter per parti, bara för partier som finns i båda åren. Ett parti som saknas i ett års
    data behandlas som inte redovisat det året, oavsett orsak: i en preliminär fil därför att det inte är
    rapportparti (rösterna ligger i Övriga), i en slutlig fil därför att det fick noll röster. Funktionen
    visar därför aldrig ett sådant parti som ett fall till noll - det är ett medvetet val. Skiljer sig
    partiuppsättningen mellan åren utelämnas även Övriga, eftersom dess sammansättning då inte är densamma."""
    gemensamma = [p for p in ny_roster if p in bas_roster]
    if set(ny_roster) - {OVRIGA} != set(bas_roster) - {OVRIGA}:
        gemensamma = [p for p in gemensamma if p != OVRIGA]
    # + 0.0 normaliserar bort negativ nolla (t.ex. round(-0.04, 1) == -0.0) så sidan aldrig visar "-0,0".
    return {p: round((ny_roster[p] / ny_giltiga - bas_roster[p] / bas_giltiga) * 100, 1) + 0.0 for p in gemensamma}


def _omradesniva(ny, bas, bas_d, val, jamforbara, samma_yta):
    """Områdesnivån för ett val: räknar ut majorna-diffen och kohortposten för `swing`.

    Är alla distrikt i ny räknade för valet jämförs hela området mot hela basåret (helomrade).
    Annars räknas bara på kohorten: räknade distrikt vars kod är jämförbar och finns med giltig
    data i bas, mot samma koder i bas.

    `samma_yta` styr när helomrade får gälla: None (standard) kräver dessutom att ny och bas har
    lika många distrikt. True intygar att området täcker samma yta i båda åren och kräver bara att
    alla distrikt i ny är räknade, oavsett antal distrikt i bas. False stänger av helomrade helt,
    så att kohorten alltid används.

    Returnerar (diff, kohortpost)."""
    ny_d = ny["distrikt"]
    raknade = [d for d in ny_d if d.get("raknat", True) and d.get(val) and d["giltiga"].get(val)]
    if samma_yta is False:
        helomrade = False
    elif samma_yta is True:
        helomrade = bool(raknade) and len(raknade) == len(ny_d)
    else:
        helomrade = bool(raknade) and len(raknade) == len(ny_d) and len(ny_d) == len(bas["distrikt"])
    if helomrade:
        n, b = ny["aggregat"]["majorna"].get(val, {}), bas["aggregat"]["majorna"].get(val, {})
        koder = [d["kod"] for d in raknade]
    else:
        kohort = [d for d in raknade if d["kod"] in jamforbara and bas_d.get(d["kod"], {}).get(val) and bas_d[d["kod"]]["giltiga"].get(val)]
        koder = [d["kod"] for d in kohort]
        n, b = _summa(kohort, val), _summa([bas_d[k] for k in koder], val)
    diff = _diff(n["roster"], n["giltiga"], b["roster"], b["giltiga"]) if n.get("giltiga") and b.get("giltiga") else {}
    kohortpost = {"antal": len(koder), "totalt": len(ny_d), "helomrade": helomrade, "koder": koder}
    return diff, kohortpost


def swing(ny, bas, jamforbara=None, meningar=None, samma_yta=None):
    """Förändring i procentenheter, ny mot bas.

    `distrikt` får bara räknade distrikt vars kod finns i `jamforbara` (None = alla koder som finns i bas,
    bakåtkompatibelt). Övriga distrikt i ny hamnar i `ej_jamforbara` med den mening kortet ska visa
    (`meningar` kan skriva över standardmeningen per kod). Områdesnivån `majorna` räknas på kohorten:
    är alla distrikt räknade jämförs hela området mot hela basåret (helomrade betyder hela området mot
    hela basåret, giltigt när ytan är densamma), annars bara räknade och jämförbara distrikt mot samma
    koder i bas. `kohort` säger vilka.

    `samma_yta` styr när helomrade får gälla, oberoende av jamforbara: None (standard) kräver att ny och
    bas har lika många distrikt, det bakåtkompatibla fallet. True intygar att området täcker samma yta i
    båda åren (till exempel 2022 mot 2018, 23 mot 22 distrikt): helomrade gäller då så snart alla
    distrikt i ny är räknade, oavsett antal. False stänger av helomrade helt.
    """
    bas_d = {d["kod"]: d for d in bas["distrikt"]}
    ny_d = list(ny["distrikt"])
    if jamforbara is None:
        jamforbara = [d["kod"] for d in ny_d if d["kod"] in bas_d]
    jamforbara = set(jamforbara)
    meningar = meningar or {}
    ar_ny, ar_bas = ny["meta"]["ar"], bas["meta"]["ar"]
    ut = {"ar": ar_ny, "bas": ar_bas, "enhet": "procentenheter", "distrikt": {}, "ej_jamforbara": {}, "majorna": {}, "kohort": {}}
    for d in ny_d:
        b = bas_d.get(d["kod"])
        if d["kod"] not in jamforbara or b is None:
            if b is None:
                mening_standard = f"{d['namn']} fanns inte som valdistrikt {ar_bas}. Siffrorna går inte att jämföra med {ar_bas}."
            else:
                mening_standard = f"Gränserna för {d['namn']} ritades om till {ar_ny}. Siffrorna går inte att jämföra med {ar_bas}."
            ut["ej_jamforbara"][d["kod"]] = {
                "orsak": "saknas i basåret" if b is None else "ej jämförbart enligt källan",
                "mening": meningar.get(d["kod"]) or mening_standard,
                "omradesrad": True}
            continue
        if not d.get("raknat", True):
            continue
        per_val = {}
        for val in VAL:
            if d.get(val) and b.get(val) and d["giltiga"].get(val) and b["giltiga"].get(val):
                per_val[val] = _diff(d[val], d["giltiga"][val], b[val], b["giltiga"][val])
        if per_val:
            ut["distrikt"][d["kod"]] = per_val
    for val in VAL:
        ut["majorna"][val], ut["kohort"][val] = _omradesniva(ny, bas, bas_d, val, jamforbara, samma_yta)
    return ut


def las_konfig(mapp):
    """data/konfig.json om den finns, annars standardkonfigen."""
    p = Path(mapp) / "konfig.json"
    if not p.exists():
        return copy.deepcopy(KONFIG_STANDARD)
    # Ett nästlat block i filen ersatte tidigare hela standardblocket, så en nyckel som lagts till i
    # standarden (till exempel hjalp.extra) aldrig nådde en befintlig konfig. Sammanslagningen går därför
    # ett steg ned: filens värden vinner, standardens fyller i det som saknas.
    fil = json.loads(p.read_text("utf-8"))
    ut = copy.deepcopy(KONFIG_STANDARD)
    for nyckel, varde in fil.items():
        if isinstance(varde, dict) and isinstance(ut.get(nyckel), dict):
            ut[nyckel] = {**ut[nyckel], **varde}
        else:
            ut[nyckel] = varde
    return ut


def skriv_konfig(mapp, konfig):
    """Skriver data/konfig.json och data/konfig.js (läses av valgrafik.js före datafilerna)."""
    return skriv(Path(mapp) / "konfig", konfig)
