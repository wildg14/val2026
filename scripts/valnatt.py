"""Valmyndighetens resultatfiler 2026 (JSON i zip) till sidans schema.

Formatet är kontrollerat mot genrep-filerna, formatbeskrivningarna och val.se 2026-09-05, se
docs/superpowers/plans/2026-09-05-valnatt-2026.md. Modulen läser bara objekt eller filer och
returnerar råa poster; uppdatera_2026.py gör resten. Inga utskrifter härifrån.
"""
import json
from pathlib import Path

from .valmyndigheten import MAJORNA_KODER, NYCKELPARTIER, OVRIGA, SummaFel, partikod

VALTYP = {"RD": "rd", "RF": "rf", "KF": "kf"}
# partiforkortning i 2026 års filer -> sidans partikod, när partibeteckningen inte känns igen
FORKORTNING = {"M": "M", "C": "C", "L": "L", "KD": "KD", "S": "S", "V": "V", "MP": "MP", "SD": "SD",
               "DEM": "D", "D": "D", "FI": "FI", "K": "K", "KP": "K"}
STATUS_JAMFORBAR = "Kan jämföras"
KOMMUNKOD_GOTEBORG = "1480"


class FormatFel(ValueError):
    """Objektet har inte formen av en röstfördelningsfil från Valmyndigheten."""


def _s(v):
    return "" if v is None else str(v).strip()


def _n(v):
    return int(v or 0)


def kort_namn(namn):
    """'Västra Centrum, Svalebo' -> 'Svalebo'. Samma regel som scripts/geo.kort_namn, utan pyproj."""
    return _s(namn).split(", ", 1)[-1].strip()


def parti_2026(post):
    """En post i partiRoster -> sidans partikod, eller None när partiet inte är ett nyckelparti."""
    kod = partikod(post.get("partibeteckning", ""))
    if kod is None:
        kod = FORKORTNING.get(_s(post.get("partiforkortning")).upper())
    return kod


def ar_raknat(d):
    """Defensiv regel: räknat bara med rapporteringstid, röster och giltiga röster."""
    rpm = ((d.get("rostfordelning") or {}).get("rosterPaverkaMandat")) or {}
    return bool(_s(d.get("rapporteringsTid"))) and _n(d.get("totaltAntalRoster")) > 0 and _n(rpm.get("antalRoster")) > 0


def _las_objekt(kalla):
    if isinstance(kalla, (str, Path)):
        return json.loads(Path(kalla).read_text("utf-8"))
    return kalla


def _mappa_partiroster(rpm, val):
    """partiRoster + rosterOvrigaPartier -> röster per nyckelparti och Övriga, samt okända etiketter."""
    roster = {p: 0 for p in NYCKELPARTIER[val]}
    roster[OVRIGA] = 0
    okanda = {}
    for pr in rpm.get("partiRoster") or []:
        n = _n(pr.get("antalRoster"))
        kod = parti_2026(pr)
        if kod in roster:
            roster[kod] += n
        else:
            roster[OVRIGA] += n
            if n:
                etikett = _s(pr.get("partiforkortning")) or _s(pr.get("partibeteckning"))
                okanda[etikett] = okanda.get(etikett, 0) + n
    roster[OVRIGA] += _n((rpm.get("rosterOvrigaPartier") or {}).get("antalRoster"))
    return roster, okanda


def las_rostfordelning(kalla, koder=MAJORNA_KODER, kommunkod=None):
    """Röstfördelningsfilen (objekt eller sökväg) -> {"val", "meta", "distrikt": {kod: post}}.

    `koder` avgör vilka distrikt som returneras. `kommunkod` räknar hur många distrikt i filen som
    hör till kommunen (för riksdags- och regionfilen), annars räknas alla distrikt i filen.
    Varje post: kod, namn (kort), raknat, jamforbar, kod_forra (lista), roster, giltiga, rostande,
    rostberattigade, okanda. Oräknade distrikt har tomma röster och None som summor.
    """
    obj = _las_objekt(kalla)
    valtyp = _s(obj.get("valtyp")).upper()
    if valtyp not in VALTYP:
        raise FormatFel(f"valtyp {valtyp!r} känns inte igen (RD, RF eller KF)")
    if not isinstance(obj.get("valdistrikt"), list):
        raise FormatFel("fältet valdistrikt saknas eller är ingen lista")
    val = VALTYP[valtyp]
    vill = set(str(k) for k in koder)
    ut = {"val": val, "distrikt": {}, "meta": {
        "test": obj.get("test") is True,
        "rakningstillfalle": _s(obj.get("rakningstillfalle")),
        "valdatum": _s(obj.get("valdatum")), "tidigare_valdatum": _s(obj.get("tidigareValdatum")),
        "uppdaterad": _s(obj.get("senasteUppdateringstid")), "antal_uppdateringar": _n(obj.get("antalUppdateringar")),
        "raknade": _n(obj.get("antalValdistriktRaknade")), "totalt": _n(obj.get("antalValdistriktSomSkaRaknas")),
        "antal_i_omradet": 0}}
    for d in obj["valdistrikt"]:
        if kommunkod is None or _s(d.get("kommunkod")) == str(kommunkod):
            ut["meta"]["antal_i_omradet"] += 1
        kod = _s(d.get("valdistriktskod"))
        if kod not in vill:
            continue
        forra = d.get("valdistriktskodForegaendeVal")
        if isinstance(forra, str):
            forra = [forra]
        post = {"kod": kod, "namn": kort_namn(d.get("namn")) or kod, "raknat": ar_raknat(d),
                "jamforbar": _s(d.get("statusJamforelse")) == STATUS_JAMFORBAR, "kod_forra": [_s(k) for k in (forra or []) if _s(k)],
                "roster": {}, "giltiga": None, "rostande": None, "rostberattigade": _n(d.get("antalRostberattigade")), "okanda": {}}
        if post["raknat"]:
            rf = d["rostfordelning"]
            rpm = rf["rosterPaverkaMandat"]
            roster, okanda = _mappa_partiroster(rpm, val)
            giltiga = _n(rpm.get("antalRoster"))
            if sum(roster.values()) != giltiga:
                raise SummaFel(f"{post['namn']}: partiröster {sum(roster.values())} != giltiga {giltiga}")
            rostande = _n(d.get("totaltAntalRoster"))
            ogiltiga = _n((rf.get("rosterEjPaverkaMandat") or {}).get("antalRoster"))
            if giltiga + ogiltiga != rostande:
                raise SummaFel(f"{post['namn']}: giltiga {giltiga} + ogiltiga {ogiltiga} != röstande {rostande}")
            post.update(roster=roster, giltiga=giltiga, rostande=rostande, okanda=okanda)
        ut["distrikt"][kod] = post
    return ut
