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
    """partiRoster + rosterOvrigaPartier -> röster per redovisat nyckelparti och Övriga, samt okända etiketter.

    Ett nyckelparti som inte förekommer i partiRoster saknas i resultatet: den preliminära filen listar bara
    rapportpartierna och lägger resten i rosterOvrigaPartier, och en nolla vore en påhittad siffra.
    """
    roster = {OVRIGA: 0}
    okanda = {}
    for pr in rpm.get("partiRoster") or []:
        n = _n(pr.get("antalRoster"))
        kod = parti_2026(pr)
        if kod in NYCKELPARTIER[val]:
            roster[kod] = roster.get(kod, 0) + n
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
    rostberattigade, okanda. Oräknade distrikt har tomma röster, None som giltiga och röstande, och
    röstberättigade ur filen (0 när fältet är null). Till skillnad från valmyndigheten.las_rafil larmar
    funktionen inte när ingen av de önskade koderna finns i filen; det gör uppdatera_2026.py.
    """
    obj = _las_objekt(kalla)
    if not isinstance(obj, dict):
        raise FormatFel("filen har inte ett objekt som rot")
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
        if kod in ut["distrikt"]:
            raise FormatFel(f"distriktskoden {kod} förekommer två gånger i filen")
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
                raise SummaFel(f"{kod} {post['namn']}: partiröster {sum(roster.values())} != giltiga {giltiga}")
            rostande = _n(d.get("totaltAntalRoster"))
            rem = rf.get("rosterEjPaverkaMandat") or {}
            if not isinstance(rem, dict):
                raise FormatFel(f"{kod} {post['namn']}: rosterEjPaverkaMandat har fel form")
            ogiltiga = _n(rem.get("antalRoster"))
            if giltiga + ogiltiga != rostande:
                raise SummaFel(f"{kod} {post['namn']}: giltiga {giltiga} + ogiltiga {ogiltiga} != röstande {rostande}")
            post.update(roster=roster, giltiga=giltiga, rostande=rostande, okanda=okanda)
        ut["distrikt"][kod] = post
    return ut


def _omrade(v, val, namn=None):
    """Ett valområde eller en kommun med rostfordelning -> aggregat.

    Formen är som valmyndigheten.aggregat_andelar (andel, valdeltagande, giltiga, rostande,
    rostberattigade, antal_distrikt) plus totalt_distrikt. namn sätts även för kommunen, inte bara
    för valmyndighetens eget valområde.
    """
    if val not in NYCKELPARTIER:
        raise FormatFel(f"okänt val {val!r}")
    rf = v.get("rostfordelning") or {}
    rpm = rf.get("rosterPaverkaMandat") or {}
    giltiga = _n(rpm.get("antalRoster"))
    if not giltiga:
        return None
    roster, _ = _mappa_partiroster(rpm, val)
    if sum(roster.values()) != giltiga:
        raise SummaFel(f"aggregat {namn or v.get('namn')}: partiröster {sum(roster.values())} != giltiga {giltiga}")
    rostande = _n(v.get("totaltAntalRoster"))
    rem = rf.get("rosterEjPaverkaMandat") or {}
    if isinstance(rem, dict) and rem.get("antalRoster") is not None:
        ogiltiga = _n(rem.get("antalRoster"))
        if giltiga + ogiltiga != rostande:
            raise SummaFel(f"aggregat {namn or v.get('namn')}: giltiga {giltiga} + ogiltiga {ogiltiga} != röstande {rostande}")
    # nämnaren är röstberättigade i de räknade distrikten, annars blir valdeltagandet fel så länge räkningen pågår
    rostberattigade = _n(v.get("antalRostberattigadeIRaknadeValdistrikt")) or _n(v.get("antalRostberattigade"))
    return {"namn": namn or _s(v.get("namn")),
            "andel": {p: n / giltiga for p, n in roster.items() if p != OVRIGA},
            "valdeltagande": rostande / rostberattigade if rostberattigade else None,
            "giltiga": giltiga, "rostande": rostande, "rostberattigade": rostberattigade,
            "antal_distrikt": _n(v.get("antalValdistriktRaknade")), "totalt_distrikt": _n(v.get("antalValdistriktSomSkaRaknas"))}


def _kontrollera_valtyp(obj, val):
    """Höjer FormatFel om rotobjektets valtyp inte stämmer med val. Saknad eller null valtyp godtas."""
    valtyp = obj.get("valtyp")
    if valtyp is not None and VALTYP.get(_s(valtyp).upper()) != val:
        raise FormatFel(f"filen gäller {valtyp} men {val.upper()} väntades")


def las_valomrade(kalla, val, namn=None):
    """Mandatfördelningsfilens valomrade (riket, ett län eller en kommun) -> aggregat."""
    obj = _las_objekt(kalla)
    if not isinstance(obj, dict):
        raise FormatFel("filen har inte ett objekt som rot")
    _kontrollera_valtyp(obj, val)
    v = obj.get("valomrade")
    if not isinstance(v, dict):
        raise FormatFel("mandatfördelningsfilen saknar objektet valomrade")
    return _omrade(v, val, namn)


def las_kommun(kalla, val, kommunkod=KOMMUNKOD_GOTEBORG, namn="Göteborg"):
    """Summeringsfilens kommuner[] -> aggregat för en kommun."""
    obj = _las_objekt(kalla)
    if not isinstance(obj, dict):
        raise FormatFel("filen har inte ett objekt som rot")
    _kontrollera_valtyp(obj, val)
    lista = obj.get("kommuner")
    if not isinstance(lista, list):
        raise FormatFel("summeringsfilen saknar listan kommuner")
    for k in lista:
        if isinstance(k, dict) and _s(k.get("kommunkod")) == str(kommunkod):
            return _omrade(k, val, namn)
    raise FormatFel(f"kommun {kommunkod} finns inte i summeringsfilen")


def aggregat_2026(val, mandat, summering=None):
    """-> {"riket": ..., "goteborg": ...} som uppdatera_2026.py lägger i valdata.aggregat.

    rd: riket ur mandatfördelningen (Riket) och Göteborg ur summeringen. rf: Västra Götaland som "riket"
    och Göteborg ur summeringen. kf: bara Göteborg, ur mandatfördelningen. Tomma aggregat utelämnas.
    """
    ut = {}
    if val == "rd":
        ut["riket"] = las_valomrade(mandat, val, "Riket")
        if summering is not None:
            ut["goteborg"] = las_kommun(summering, val)
    elif val == "rf":
        ut["riket"] = las_valomrade(mandat, val, "Västra Götaland")
        if summering is not None:
            ut["goteborg"] = las_kommun(summering, val)
    elif val == "kf":
        ut["goteborg"] = las_valomrade(mandat, val, "Göteborg")
    else:
        raise FormatFel(f"okänt val {val!r}")
    return {k: v for k, v in ut.items() if v is not None}


def riksdag_verklig(kalla):
    """Mandatfördelningsfilen för riksdagen -> {partikod: mandat}. Tom när fördelningen inte finns än."""
    obj = _las_objekt(kalla)
    if not isinstance(obj, dict):
        raise FormatFel("filen har inte ett objekt som rot")
    _kontrollera_valtyp(obj, "rd")
    v = obj.get("valomrade") or {}
    lista = ((v.get("mandatfordelning") or {}).get("partiLista")) or []
    if not isinstance(lista, list):
        return {}
    ut = {}
    for p in lista:
        if not isinstance(p, dict):
            continue
        n = _n(p.get("antalMandat"))
        if not n:
            continue
        kod = parti_2026(p) or _s(p.get("partiforkortning")) or _s(p.get("partibeteckning")) or _s(p.get("partikod"))
        ut[kod] = ut.get(kod, 0) + n
    return ut
