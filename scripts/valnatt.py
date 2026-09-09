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
    """Ett heltal ur ett JSON-fält. None och tom sträng blir 0.

    Bråktal och skräpsträngar avvisas i stället för att tyst bli något annat: int(12.7) gav 12 röster
    utan att någon märkte det, och strängen "12,7" kastade en ValueError som ingen fångade, alltså en
    traceback i stället för en FEL-rad mitt på valnatten (granskningsfynd 5)."""
    if v is None or v == "":
        return 0
    if isinstance(v, bool):
        raise FormatFel(f"{v!r} är inget tal")
    if isinstance(v, int):
        return v
    if isinstance(v, float) and v.is_integer():
        return int(v)
    try:
        return int(str(v).strip())
    except (TypeError, ValueError):
        raise FormatFel(f"{v!r} är inget heltal") from None


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
    """Läser en sökväg som JSON, eller returnerar objektet oförändrat om det redan är ett.

    En halvskriven fil (avbruten hämtning, eller läst mitt i en skrivning på valnatten) ska aldrig
    stoppa körningen med en traceback: JSONDecodeError, fel teckenkodning och läsfel (saknad fil,
    rättighetsfel) fångas här och blir ett kort FormatFel med filnamnet, som uppdatera_2026.py visar
    som en vanlig FEL-rad.
    """
    if isinstance(kalla, (str, Path)):
        path = Path(kalla)
        try:
            text = path.read_text("utf-8")
            return json.loads(text)
        except (json.JSONDecodeError, UnicodeDecodeError, OSError) as ex:
            raise FormatFel(f"{path.name} har inte formen av en JSON-fil: {ex}") from ex
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
                "roster": {}, "giltiga": None, "rostande": None, "rostberattigade": _n(d.get("antalRostberattigade")),
                "okanda": {}, "orimligt": ""}
        if post["raknat"]:
            rf = d["rostfordelning"]
            rpm = rf["rosterPaverkaMandat"]
            roster, okanda = _mappa_partiroster(rpm, val)
            giltiga = _n(rpm.get("antalRoster"))
            rostande = _n(d.get("totaltAntalRoster"))
            rem = rf.get("rosterEjPaverkaMandat") or {}
            if not isinstance(rem, dict):
                raise FormatFel(f"{kod} {post['namn']}: rosterEjPaverkaMandat har fel form")
            ogiltiga = _n(rem.get("antalRoster"))
            # Rimlighet före summor. CSV-vägen har haft de här kontrollerna hela tiden; JSON-vägen
            # kontrollerade bara att partisumman stämde, och den kontrollen är blind för tecknet:
            # V -10 och S 110 summerar till samma 100 som två rimliga tal (granskningsfynd 5).
            #
            # Ett omöjligt tal stoppar bara sitt eget distrikt, till skillnad från en summa som inte går
            # ihop. Skillnaden är hur mycket man vet: går summorna inte ihop kan vi läsa filen fel, och då
            # är hela filen misstänkt; ett tal som är omöjligt på sitt eget ansikte är ett dåligt värde i
            # en fil vi läser rätt. Och till skillnad från CSV-vägen, som är handskriven och går att rätta
            # på plats, kommer den här filen från Valmyndigheten: att fälla hela kvällen på ett distrikt
            # vore värre än att visa 22 av 23. Talet når aldrig sidan, distriktet blir oräknat, och att
            # det fattas syns både i varningen och i statusraden.
            orimligt = [f"{etikett} {n}" for etikett, n in
                        [*roster.items(), ("giltiga", giltiga), ("ogiltiga", ogiltiga),
                         ("röstande", rostande), ("röstberättigade", post["rostberattigade"])] if n < 0]
            # Noll röstberättigade betyder att fältet saknas i filen, inte att ingen fick rösta.
            if post["rostberattigade"] and rostande > post["rostberattigade"]:
                orimligt.append(f"röstande {rostande} > röstberättigade {post['rostberattigade']}")
            if orimligt:
                post["raknat"] = False
                post["orimligt"] = "; ".join(orimligt)
                ut["distrikt"][kod] = post
                continue
            if sum(roster.values()) != giltiga:
                raise SummaFel(f"{kod} {post['namn']}: partiröster {sum(roster.values())} != giltiga {giltiga}")
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
    # Samma rimlighetskontroll som för distrikten. Aggregaten går rakt ut i "Majorna mot Sverige" och i
    # halvcirkelns förbehåll; ett fel här stoppar inte distriktsimporten (beslut 24) utan blir en varning
    # och ett tomt aggregat för valet.
    for etikett, n in roster.items():
        if n < 0:
            raise SummaFel(f"aggregat {namn or v.get('namn')}: negativt tal för {etikett}: {n}")
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
    if rostberattigade and rostande > rostberattigade:
        raise SummaFel(f"aggregat {namn or v.get('namn')}: röstande {rostande} > röstberättigade {rostberattigade}")
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
    if not isinstance(v, dict):
        raise FormatFel("valomrade har fel form")
    md = v.get("mandatfordelning") or {}
    if not isinstance(md, dict):
        raise FormatFel("mandatfordelning har fel form")
    lista = md.get("partiLista") or []
    if not isinstance(lista, list):
        return {}
    ut = {}
    for p in lista:
        if not isinstance(p, dict):
            continue
        n = _n(p.get("antalMandat"))
        if n < 0:
            raise SummaFel(f"riksdagens mandat: negativt tal för {parti_2026(p) or _s(p.get('partiforkortning'))}: {n}")
        if not n:
            continue
        kod = parti_2026(p) or _s(p.get("partiforkortning")) or _s(p.get("partibeteckning")) or _s(p.get("partikod"))
        if not kod:
            continue
        ut[kod] = ut.get(kod, 0) + n
    return ut
