#!/usr/bin/env python3
"""Bygger sidans historikfiler ur data/historik/majorna_historik.sqlite (skrivskyddat).

    .venv/bin/python scripts/bygg_historik.py historik            data/historik.json + .js
    .venv/bin/python scripts/bygg_historik.py swing2022           data/swing_2022.json + .js (bas 2018)
    .venv/bin/python scripts/bygg_historik.py geo2006             data/distrikt_2006.geojson + .js (förenklad, för konturkartan)
    .venv/bin/python scripts/bygg_historik.py ar 2006 2010 2014 2018   data/valdata_<år> och data/distrikt_<år>
    .venv/bin/python scripts/bygg_historik.py allt

Databasen byggs om med scripts/historik/bygg_databas.py. Serien börjar 2006 (Daniels beslut 2026-09-05);
2002 går inte att räkna om till dagens Majorna och tas inte med. Partikoden L täcker Folkpartiet till och
med 2014. Alla tal räknas ur tabellerna, inget skrivs för hand. Varje post i serien har roster med exakt
NYCKELPARTIER[val] plus Övriga (sidans partiuppsättning för valet); partier i tidsserien utanför den
uppsättningen, till exempel FI i riksdagsvalet eller K i regionvalet, läggs i Övriga.

Ett nyckelparti som inte fanns ett visst år och val (till exempel D före 2018, FI i regionvalet 2006 och
2010) får ingen egen nyckel i det årets distrikts- eller jämförelseposter - se partier_med_rader.
"""
import argparse
import csv
import datetime as dt
import json
import sqlite3
import sys
from pathlib import Path

from shapely.geometry import shape

ROT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROT))

from scripts import geo, schema  # noqa: E402
from scripts.mandat import jamkade_uddatal  # noqa: E402
from scripts.valmyndigheten import MAJORNA_KODER, NYCKELPARTIER, OVRIGA, VAL  # noqa: E402

DB = ROT / "data" / "historik" / "majorna_historik.sqlite"
KEDJA = ROT / "data" / "historik" / "kedja_majorna_2006_2022.csv"
GEO_HISTORIK = ROT / "data" / "historik"
AR = [2006, 2010, 2014, 2018, 2022]  # seriens fem år (historik.json och swing_2022, oavsett underkommando)
BAS_AR = 2018  # basår för swing_2022 (Task 2)
# Tillåtlista för underkommandot "ar": bara dessa år byggs härifrån. 2022 och 2026 har sina egna,
# kanoniska data/valdata_<år>-filer (byggda av bygg_data.py respektive uppdatera_2026.py) - utan den
# här spärren skrev "ar 2022" tidigare över den kanoniska filen, med annan `kalla`, innan körningen
# dog på saknad geometri (distrikt_2022_majornaomradet.geojson finns inte i historikkatalogen).
BYGGBARA_AR = [2006, 2010, 2014, 2018]
PARTIER = ["V", "S", "MP", "SD", "M", "C", "L", "KD", "D", "FI", "K", OVRIGA]
ALLA_KODER = [p for p in PARTIER if p != OVRIGA]  # de elva namngivna partikoderna, oavsett vilket val de har egen kolumn i
NIVAER = ["majorna", "goteborg", "riket"]
KALLA = "Valmyndigheten, slutlig rösträkning per valdistrikt 2006 till 2022."


def oppna(path=DB):
    if not Path(path).exists():
        print(f"FEL: {path} saknas, bygg den med scripts/historik/bygg_databas.py", file=sys.stderr)
        sys.exit(1)
    con = sqlite3.connect(f"file:{path}?mode=ro", uri=True)
    con.row_factory = sqlite3.Row
    try:
        con.execute("SELECT 1 FROM tidsserie LIMIT 1")
    except sqlite3.DatabaseError as e:
        print(f"FEL: {path} går inte att läsa som databas: {e}", file=sys.stderr)
        sys.exit(1)
    return con


def _post(rader, val):
    """Rader ur tidsserie för ett (ar, val, niva) -> en post i serien.

    roster får exakt nycklarna NYCKELPARTIER[val] plus Övriga (sidans partiuppsättning för
    detta val). Partier i tidsserien utanför den uppsättningen, till exempel FI i riksdagsvalet
    eller K i regionvalet, läggs i Övriga tillsammans med SUMMA_ÖVRIGA. Så blir raden identisk
    med den kurerade valdata_<år>.json som redan följer sidans schema.
    """
    if not rader:
        return None
    nycklar = NYCKELPARTIER[val]
    roster = {p: 0 for p in nycklar}
    roster[OVRIGA] = 0
    giltiga_ar, rostande_ar, rostberattigade_ar, antal_ar = set(), set(), set(), set()
    for r in rader:
        p = r["parti"]
        v = int(r["roster"] or 0)
        if p == "SUMMA_ÖVRIGA" or (p in ALLA_KODER and p not in nycklar):
            roster[OVRIGA] += v
        elif p in nycklar:
            roster[p] = v
        else:
            continue
        if r["giltiga"] is not None:
            giltiga_ar.add(int(r["giltiga"]))
        if r["rostande"] is not None:
            rostande_ar.add(int(r["rostande"]))
        if r["rostberattigade"] is not None:
            rostberattigade_ar.add(int(r["rostberattigade"]))
        if r["antal_distrikt"] is not None:
            antal_ar.add(int(r["antal_distrikt"]))
    plats = f"{rader[0]['ar']} {rader[0]['val']} {rader[0]['niva']}"
    for namn, varden in (("giltiga", giltiga_ar), ("rostande", rostande_ar), ("rostberattigade", rostberattigade_ar),
                         ("antal_distrikt", antal_ar)):
        if len(varden) > 1:
            raise SystemExit(f"FEL: {plats}: flera {namn}-värden på raderna {sorted(varden)}")
    if not giltiga_ar:
        return None
    giltiga = giltiga_ar.pop()
    rostande = rostande_ar.pop() if rostande_ar else None
    rostberattigade = rostberattigade_ar.pop() if rostberattigade_ar else None
    antal = antal_ar.pop() if antal_ar else None
    metoder = {r["metod"] for r in rader if r["metod"] and "residual" not in r["metod"]}
    if len(metoder) > 1:
        raise SystemExit(f"FEL: {plats}: flera metodsträngar {sorted(metoder)}")
    metod = metoder.pop() if metoder else None
    if sum(roster.values()) != giltiga:
        raise SystemExit(f"FEL: {plats}: partiernas röster {sum(roster.values())} != giltiga {giltiga}")
    return {"ar": int(rader[0]["ar"]), "roster": roster, "andel": {p: n / giltiga for p, n in roster.items()},
            "giltiga": giltiga, "rostande": rostande, "rostberattigade": rostberattigade,
            "valdeltagande": (rostande / rostberattigade) if rostande is not None and rostberattigade else None,
            "antal_distrikt": antal, "metod": metod}


def omradespost(con, ar, val, niva):
    """Slår upp och sammanställer en (ar, val, niva)-grupp ur tidsserie, eller None om den saknas.

    Task 2 använder den för basaggregatet 2018 (bas för swing_2022).
    """
    rader = con.execute("SELECT * FROM tidsserie WHERE ar=? AND val=? AND niva=? ORDER BY parti", (ar, val, niva)).fetchall()
    return _post(rader, val)


def bygg_historik(con):
    serie = {val: {niva: [] for niva in NIVAER} for val in VAL}
    metod_per_val_ar = {ar: {} for ar in AR}
    for val in VAL:
        for niva in NIVAER:
            for ar in AR:
                post = omradespost(con, ar, val, niva)
                if post is None:
                    raise SystemExit(f"FEL: tidsserie saknar {ar} {val} {niva}")
                if niva == "majorna":
                    metod_per_val_ar[ar][val] = post["metod"]
                serie[val][niva].append({k: v for k, v in post.items() if k != "metod"})
    metod_per_ar = {}
    for ar in AR:
        metoder = set(metod_per_val_ar[ar].values())
        if len(metoder) > 1:
            raise SystemExit(f"FEL: {ar}: metodsträngen skiljer sig mellan valen: {metod_per_val_ar[ar]}")
        metod_per_ar[str(ar)] = metoder.pop()
    return {"meta": {"byggd": dt.datetime.now().replace(microsecond=0).isoformat(), "kalla": KALLA, "ar": AR, "partier": PARTIER,
                     "partier_per_val": {val: NYCKELPARTIER[val] + [OVRIGA] for val in VAL},
                     "noter": ["Serien börjar 2006. Valdistrikten ritades om helt inför det valet, så 2002 går inte att räkna om till dagens Majorna.",
                               "Liberalerna hette Folkpartiet till och med 2014; serien använder koden L hela vägen.",
                               "Övriga är giltiga röster minus valets partier. Partiuppsättningen per val följer sidans schema: "
                               "riksdagsvalet V, S, MP, SD, M, C, L, KD; regionvalet dessutom D och FI; kommunvalet dessutom D, FI och K. "
                               "Partier utanför valets uppsättning, till exempel FI i riksdagsvalet, ingår i Övriga."],
                     "metod": metod_per_ar},
            "serie": serie}


MENING_BAKAT = "Gränserna såg annorlunda ut {bas}. Siffrorna hör till det årets distrikt."
KEDJA_KOLUMNER = ("kod_2022", "kod_2018", "jamforbar_tillbaka_till")


def _las_kedja_rader(path=KEDJA):
    """Läser kedjefilens rader som dict-per-rad, med filnivåkontroller gemensamma för las_kedja och las_kedja_alla.

    kod_2022 är kedjans nyckel för varje 2022-distrikt och får inte förekomma på mer än en rad -
    en dubblett vore ett fel i själva kedjefilen, inte ett tillåtet fall som las_kedja_alla:s
    dubbla kod_2018 (se dess docstring)."""
    path = Path(path)
    if not path.exists():
        print(f"FEL: {path} saknas", file=sys.stderr)
        sys.exit(1)
    with open(path, encoding="utf-8-sig", newline="") as f:
        r = csv.DictReader(f, delimiter=";")
        saknas = [k for k in KEDJA_KOLUMNER if k not in (r.fieldnames or [])]
        if saknas:
            raise SystemExit(f"FEL: {path}: saknar kolumnerna {saknas}")
        rader = list(r)
    koder = [rad["kod_2022"] for rad in rader]
    dubbletter = sorted({k for k in koder if koder.count(k) > 1})
    if dubbletter:
        raise SystemExit(f"FEL: {path}: kod_2022 förekommer på flera rader: {dubbletter}")
    return rader


def las_kedja(path=KEDJA):
    """kedja_majorna_2006_2022.csv -> {kod_2022: kod_2018} för raderna som är jämförbara till 2018 eller längre.

    Ingen kod_2018 får förekomma på mer än en av dessa rader (annars är kedjan tvetydig för swing_2022,
    som ger 2018-distriktet 2022 års kod) - det är skilt från las_kedja_alla, där samma 2018-distrikt
    får ligga bakom flera 2022-koder, till exempel när ett distrikt delats upp."""
    ut = {}
    for r in _las_kedja_rader(path):
        if r["jamforbar_tillbaka_till"] in ("2018", "2014", "2010", "2006") and r["kod_2018"]:
            if r["kod_2018"] in ut.values():
                raise SystemExit(f"FEL: {path}: kod_2018 {r['kod_2018']} förekommer på flera jämförbara rader")
            ut[r["kod_2022"]] = r["kod_2018"]
    return ut


def las_kedja_alla(path=KEDJA):
    """kedja_majorna_2006_2022.csv -> {kod_2022: kod_2018} för alla 23 raderna, oavsett jämförbarhet.

    Flera 2022-koder kan peka på samma kod_2018, till exempel 14800530 och 14800535 som båda kommer
    ur 2018 års 14801011: distriktet delades vid omritningen 2022."""
    return {r["kod_2022"]: r["kod_2018"] for r in _las_kedja_rader(path) if r["kod_2018"]}


def partier_med_rader(con, ar, val, koder):
    """Vilka partikoder som har minst en rad i `roster` för de givna distriktskoderna (ett historikårs
    Majorna-medlemmar, ur majorna_medlem) det året och valet - oavsett röstetal. Ett parti utan någon
    rad där fanns inte (till exempel D före 2018, FI i regionvalet 2006 och 2010); ett parti med en rad
    men noll röster räknas som att det fanns.

    Används för att bestämma partier_per_val (distrikt_ur_db) och, via samma mönster, vilka nyckelpartier
    som har en rad i tidsserie (_jamforelse) respektive aggregat (_vgregion) - så att ett nyckelparti som
    inte fanns aldrig visas som 0,0 procent."""
    if not koder:
        return set()
    platshallare = ",".join("?" * len(koder))
    rader = con.execute(f"SELECT DISTINCT parti_kanon FROM roster WHERE ar=? AND val=? AND kod IN ({platshallare})",
                        (ar, val, *koder)).fetchall()
    return {r["parti_kanon"] for r in rader}


def distrikt_ur_db(con, ar, kod, namn, partier_per_val):
    """Ett distrikt ett år i sidans schema: roster per val med sidans partikoder, summor ur distrikt_summa.

    `partier_per_val` ({val: [partikoder]}) är de nyckelpartier som fanns det året och valet (se
    partier_med_rader), beräknat en gång per år av anroparen - inte NYCKELPARTIER[val] rakt av, som skulle
    ge till exempel "Demokraterna 0,0 %" för år partiet inte existerade.

    Okända partikoder (utanför partier_per_val[val]) läggs i Övriga, eftersom rösttabellen `roster` inte
    har någon egen residualrad för dem - till skillnad från `_post`, som hoppar över okända koder i
    tidsserien, där SUMMA_ÖVRIGA redan är en färdig residualrad.

    Saknas summeringsraden i distrikt_summa för ett val, eller är giltiga NULL där, utelämnas nyckeln
    `post[val]` helt (ingen tom dict), och giltiga/rostande/rostberattigade för det valet sätts inte -
    giltiga hanteras alltså på samma sätt som rostande och rostberattigade (None om NULL), inte som ett
    särfall. `raknat` är True bara om minst ett val fick giltiga - annars vore det motsägelsefullt att
    kalla distriktet räknat utan någon data alls.
    """
    post = {"kod": kod, "namn": namn, "giltiga": {}, "rostande": {}, "rostberattigade": {}}
    nagot_val = False
    for val in VAL:
        roster = {p: 0 for p in partier_per_val[val]}
        roster[OVRIGA] = 0
        for r in con.execute("SELECT parti_kanon, roster FROM roster WHERE ar=? AND val=? AND kod=?", (ar, val, kod)):
            p = r["parti_kanon"]
            roster[p if p in roster else OVRIGA] += int(r["roster"] or 0)
        s = con.execute("SELECT giltiga, rostande, rostberattigade FROM distrikt_summa WHERE ar=? AND val=? AND kod=?", (ar, val, kod)).fetchone()
        if s is None:
            continue
        giltiga = int(s["giltiga"]) if s["giltiga"] is not None else None
        if giltiga is None:
            continue
        if sum(roster.values()) != giltiga:
            raise SystemExit(f"FEL: {ar} {val} {kod}: röster {sum(roster.values())} != giltiga {giltiga}")
        post[val] = roster
        post["giltiga"][val] = giltiga
        post["rostande"][val] = int(s["rostande"]) if s["rostande"] is not None else None
        post["rostberattigade"][val] = int(s["rostberattigade"]) if s["rostberattigade"] is not None else None
        nagot_val = True
    post["raknat"] = nagot_val
    return post


def bygg_swing_2022(con):
    """2022 mot BAS_AR (2018) för de nio jämförbara kvarteren; områdesnivån ur områdesserien (samma_yta=True), ingen efterhandsskrivning.

    Distriktsnivån räknas av schema.swing på ett basobjekt där alla 23 distrikt i BAS_AR fått 2022 års
    koder (las_kedja_alla) - inte bara de nio jämförbara. Annars saknar schema.swing ett bas-distrikt för
    de fjorton omritade och ger dem orsak "saknas i basåret", vilket är fel: de har en motsvarighet i
    kedjefilen, källan säger bara att gränserna ändrats för mycket för att jämförelsen ska gälla. Med alla
    23 i bas blir orsaken i stället "ej jämförbart enligt källan" för dem, medan `jamforbara` (de nio ur
    las_kedja) styr att bara de nio faktiskt räknas på distriktsnivå. Namnen i bas_distrikt är 2022 års
    (namn_2022), inte BAS_ARs egna - docs/historik/noter/kedja.md visar att namn och koder korsas i
    Majorna 2018 (två Gråberget-distrikt bytte sida), så BAS_ARs eget namn vore missvisande här.

    Områdesnivån (majorna, kohort) räknas av swing självt ur bas["aggregat"]["majorna"], byggt av
    omradespost ur tidsserien för BAS_AR - samma tal som historik.json:s serie det året, med exakt samma
    partiuppsättning som ny["aggregat"]["majorna"] (NYCKELPARTIER[val] plus Övriga), så Övriga kommer med
    i diffen. Ingenting i s["majorna"] eller s["kohort"] skrivs över efteråt.
    """
    ny = json.loads((ROT / "data" / "valdata_2022.json").read_text("utf-8"))
    namn_2022 = {d["kod"]: d["namn"] for d in ny["distrikt"]}
    kedja = las_kedja()
    kedja_alla = las_kedja_alla()
    kod_2022_alla = {d["kod"] for d in ny["distrikt"]}
    if set(kedja_alla) != kod_2022_alla:
        saknas = sorted(kod_2022_alla - set(kedja_alla))
        extra = sorted(set(kedja_alla) - kod_2022_alla)
        raise SystemExit(f"FEL: kedjefilen täcker inte {ny['meta']['ar']} års distrikt: saknas {saknas}, extra {extra}")
    bas_koder = sorted(set(kedja_alla.values()))
    bas_partier_per_val = {val: [p for p in NYCKELPARTIER[val] if p in partier_med_rader(con, BAS_AR, val, bas_koder)] for val in VAL}
    bas_distrikt = [distrikt_ur_db(con, BAS_AR, kod18, namn_2022[kod22], bas_partier_per_val) | {"kod": kod22}
                    for kod22, kod18 in kedja_alla.items()]
    bas_aggregat = {}
    for val in VAL:
        post = omradespost(con, BAS_AR, val, "majorna")
        if post is None:
            raise SystemExit(f"FEL: tidsserie saknar {BAS_AR} {val} majorna")
        bas_aggregat[val] = {k: post[k] for k in ("roster", "giltiga", "rostande", "rostberattigade")}
    bas = {"meta": {"ar": BAS_AR}, "distrikt": bas_distrikt, "aggregat": {"majorna": bas_aggregat}}
    meningar = {d["kod"]: MENING_BAKAT.format(bas=BAS_AR) for d in ny["distrikt"] if d["kod"] not in kedja}
    s = schema.swing(ny, bas, jamforbara=list(kedja), meningar=meningar, samma_yta=True)
    for val in VAL:
        s["kohort"][val]["metod"] = "omradesserien"
    totalt = len(ny["distrikt"])
    print(f"Jämförbara {ny['meta']['ar']} mot {BAS_AR} ({len(kedja)} av {totalt}): "
          + ", ".join(f"{k} ({kedja[k]})" for k in sorted(kedja)))
    print(f"Omritade sedan {BAS_AR} ({len(meningar)} av {totalt}): " + ", ".join(sorted(meningar)))
    return s


# Bara för 2006 (konturkartan). features_till_schema förenklar gemensamma gränser topologiskt (en gång
# för båda grannarna, se geo._forenkla_topologiskt) i stället för varje polygon för sig - annars
# förenklas en delad gräns olika på var sida, vilket med den gamla per-polygon-metoden gav 23 par
# grannar som överlappade och 12 luckor (cirka 3 procent geometrisk drift i konturen, uppmätt mot
# dagens fil innan detta byte).
#
# Uppmätt stegvis mot data/historik/distrikt_2006_majornaomradet.geojson (se tests/test_bygg_historik.py,
# byggd en gång per testmodul): vid 0,0002 grader blir distrikt_2006.geojson 20,3 kB och distrikt_2006.js
# (den fil sidan faktiskt laddar) 9,6 kB, ytsumman 4,6491 km² (facit 4,655 km²). Unionens symmetriska
# differens mot råfilens union är 0,55 procent av ytan (luckor och överlapp räknade var för sig, se
# geo.jamfor_union) - testets gräns är 1,2 procent. Nettoskillnaden ("skillnad" i geo.jamfor_union) är
# -0,11 procent, en lös gräns satt till 0,5 procent eftersom symmetrisk differens är det som faktiskt
# räknas här (nettot kan råka bli litet även med stora lokala fel, om luckor och överlapp tar ut
# varandra). Mot unionen av dagens data/distrikt_2022.geojson (samma yttre Majorna-kontur) är den
# symmetriska differensen 0,58 procent, också under 1,2 procent. Ingen polygon överlappar en annan
# (störst uppmätta överlapp 0 kvadratmeter i EPSG:3006). Alla 32 grad-3-noder (knutpunkter mellan tre
# eller fler distrikt) i det förenklade gränsnätet finns exakt bland originalnätets noder - förenklingen
# flyttar aldrig en knutpunkt, bara linjerna mellan dem. Största enskilda konturavvikelsen (varje
# originalhörn mot den förenklade linjen, i EPSG:3006) är cirka 20 meter, för distrikt 14808401 - inom
# den teoretiska gränsen för toleransen: 0,0002 grader är cirka 12 meter öst-väst och 22 meter nord-syd
# vid Majornas breddgrad (1 grad longitud krymper med cos(lat) i meter, latitud gör det inte). Kartan är
# 170 x 135 pixlar; distrikt_2006:s bbox är 2 838 x 2 844 meter, nästan kvadratisk, så det är höjden
# (135 px) som binder skalan, inte bredden - bredden ensam (2 838 meter på 170 px) skulle ge 16,7 meter
# per pixel, men med höjden bindande blir det i stället cirka 21 meter per pixel. En avvikelse på 20
# meter syns då som knappt en pixel - rimligt för en kontur i den storleken.
FORENKLA_GRADER = 0.0002

# 2006 får bara den förenklade konturgeometrin (byggd av underkommandot "geo2006", se ovan) - en
# oförenklad distrikt_2006 är inte verifierad eller testad (den förenklade filens 309 hörn mot till
# exempel 2010:s 1 146, se HANDOVER), så underkommandot "ar" hoppar över distrikt_<år>.geojson för de
# år som listas här.
GEO_FORENKLA_AR = {2006}


def bygg_geo(ar, forenkla):
    """distrikt_<år>_majornaomradet.geojson (WGS84, kod och namn) -> sidans geojson med etikett,
    area_km2 och bbox, via scripts.geo.features_till_schema - samma schembygge som las_distrikt
    använder för 2022 och 2026.

    forenkla=True (2006, konturkartan) förenklar med FORENKLA_GRADER; de andra åren (2010, 2014,
    2018) behåller gemensamma gränser exakt.
    """
    src = GEO_HISTORIK / f"distrikt_{ar}_majornaomradet.geojson"
    if not src.exists():
        raise SystemExit(f"FEL: {src} saknas")
    gj = json.loads(src.read_text("utf-8"))
    poster = []
    for ft in gj["features"]:
        g = shape(ft["geometry"])
        if g.geom_type == "MultiPolygon":
            g = max(g.geoms, key=lambda p: p.area)
        kod = str(ft["properties"]["kod"]).strip()
        namn = geo.kort_namn(ft["properties"].get("namn") or kod)
        poster.append({"geometry": g, "kod": kod, "namn": namn})
    return geo.features_till_schema(poster, forenkla_grader=FORENKLA_GRADER if forenkla else None)


def _mandat_riket_rd(con, ar):
    """Riksdagens verkliga mandat ett år, ur tabellen mandat (nivå riket, val rd), filtrerad till
    NYCKELPARTIER["rd"].

    Tabellen har dubbla rader per parti (mandat_<år>_riksdag.csv och mandat_riksdag_riket.csv, samma
    tal), en falsk residualrad (ÖVR 349 år 2006, FI 349 år 2014) och NULL-mandat för partier som inte
    fick något - DISTINCT, filtreringen till nyckelpartierna och mandat IS NOT NULL städar bort alla
    tre. 2006 saknar en egen SD-rad (partiet fick noll mandat den valperioden). Kontrollerar att varje
    parti får exakt ett mandattal (en dubblettrad med olika tal vore ett datafel) och att summan blir
    349 - vakten gäller summan, inte antalet partier, eftersom 2006 har sju medan de andra fyra åren
    har åtta."""
    rader = con.execute(
        "SELECT DISTINCT parti, mandat FROM mandat WHERE ar=? AND val='rd' AND niva='riket' AND mandat IS NOT NULL ORDER BY parti",
        (ar,)).fetchall()
    verklig = {}
    for r in rader:
        p = r["parti"]
        if p not in NYCKELPARTIER["rd"]:
            continue
        m = int(r["mandat"])
        if p in verklig and verklig[p] != m:
            raise SystemExit(f"FEL: {ar}: mandat-tabellen har olika mandattal för {p}: {verklig[p]} och {m}")
        verklig[p] = m
    summa = sum(verklig.values())
    if summa != 349:
        raise SystemExit(f"FEL: {ar}: riksdagens verkliga mandat summerar till {summa}, inte 349 ({verklig})")
    return verklig


def _jamforelse(con, ar, val, niva, namn):
    """En rad ur områdesserien (goteborg, riket) i sidans jämförelseschema för valdata_<år>.json, eller
    None om raden saknas.

    andel byggs bara för nyckelpartier som har en egen rad i tidsserie för (ar, val, niva) - omradespost
    (via _post) fyller annars på med en nolla för varje nyckelparti som saknas helt, vilket här skulle
    visa till exempel "Demokraterna 0,0 %" i Göteborg eller riket för år partiet inte fanns. Ett parti
    med en rad men noll röster behåller sin 0,0 %, det är en riktig nolla."""
    post = omradespost(con, ar, val, niva)
    if post is None:
        return None
    finns = {r["parti"] for r in con.execute(
        "SELECT DISTINCT parti FROM tidsserie WHERE ar=? AND val=? AND niva=?", (ar, val, niva)).fetchall()}
    return {"andel": {p: a for p, a in post["andel"].items() if p != OVRIGA and p in finns}, "valdeltagande": post["valdeltagande"],
            "giltiga": post["giltiga"], "rostande": post["rostande"], "rostberattigade": post["rostberattigade"], "namn": namn}


def _vgregion(con, ar, val):
    """Västra Götaland i regionvalet ur tabellen aggregat (nivå vgregion), som sidans 'riket' för rf.

    Samma "bara partier med rad"-regel som _jamforelse, men mot aggregat i stället för tidsserie: D och
    FI saknar rad i vgregion före de fanns i Västra Götalands regionval (se partier_med_rader). Som
    _post: en dubblettrad för samma parti är ett datafel (SystemExit), giltiga/rostande/rostberattigade
    ska vara eniga över raderna, och NULL blir None - inte 0 - för rostande och rostberattigade."""
    rader = con.execute(
        # ORDER BY parti löser till SELECT-listans alias (parti_kanon, den kanoniserade koden) -
        # inte tabellens egen kolumn parti (den okanoniserade koden ur källfilen).
        "SELECT parti_kanon AS parti, roster, giltiga, rostande, rostberattigade FROM aggregat "
        "WHERE ar=? AND val=? AND niva='vgregion' ORDER BY parti", (ar, val)).fetchall()
    if not rader:
        return None
    plats = f"{ar} {val} vgregion"
    sedda = set()
    giltiga_ar, rostande_ar, rostberattigade_ar = set(), set(), set()
    roster = {p: 0 for p in NYCKELPARTIER[val] if p in {r["parti"] for r in rader}}
    for r in rader:
        p = r["parti"]
        if p in sedda:
            raise SystemExit(f"FEL: {plats}: {p} förekommer på flera rader")
        sedda.add(p)
        if p in roster:
            roster[p] += int(r["roster"] or 0)
        if r["giltiga"] is not None:
            giltiga_ar.add(int(r["giltiga"]))
        if r["rostande"] is not None:
            rostande_ar.add(int(r["rostande"]))
        if r["rostberattigade"] is not None:
            rostberattigade_ar.add(int(r["rostberattigade"]))
    for namn, varden in (("giltiga", giltiga_ar), ("rostande", rostande_ar), ("rostberattigade", rostberattigade_ar)):
        if len(varden) > 1:
            raise SystemExit(f"FEL: {plats}: flera {namn}-värden på raderna {sorted(varden)}")
    if not giltiga_ar:
        return None
    giltiga = giltiga_ar.pop()
    if not giltiga:
        return None
    rostande = rostande_ar.pop() if rostande_ar else None
    rostberattigade = rostberattigade_ar.pop() if rostberattigade_ar else None
    return {"andel": {p: n / giltiga for p, n in roster.items()},
            "valdeltagande": (rostande / rostberattigade) if rostande is not None and rostberattigade else None,
            "giltiga": giltiga, "rostande": rostande, "rostberattigade": rostberattigade,
            "namn": "Västra Götaland"}


def bygg_valdata_ar(con, ar):
    """Ett historikårs valdata i sidans schema: distrikt via majorna_medlem (aldrig uppsamlingsdistrikt),
    jämförelseaggregat för Göteborg och riket (Västra Götaland i regionvalet), riksdagens verkliga
    mandat och Majornas eget räkneexempel.

    `meta.kalla` och `meta.avgransning` är publicerad text på sidan och nämner därför bara valet och
    året, ingen sökväg i repot. Härledningen: valdistrikten och rösterna kommer ur
    data/historik/majorna_historik.sqlite (byggd av scripts/historik/bygg_databas.py ur Valmyndighetens
    filer), och avgränsningen - vilka av dagens 23 distrikt som räknas till Majorna ett historikår - är
    områdesmetoden (areametod) som dokumenteras i docs/historik/valdistrikt-historik.md.
    """
    medlemmar = con.execute(
        "SELECT kod, namn FROM majorna_medlem WHERE ar=? AND ingar_i_jamforbart_majorna=1 ORDER BY kod", (ar,)).fetchall()
    if not medlemmar:
        raise SystemExit(f"FEL: majorna_medlem saknar {ar}")
    majorna_koder = [r["kod"] for r in medlemmar]
    partier_per_val = {}
    for val in VAL:
        finns = partier_med_rader(con, ar, val, majorna_koder)
        for p in NYCKELPARTIER[val]:
            if p not in finns:
                print(f"VARNING: {ar} {val}: {p} har inga rader, utelämnas", file=sys.stderr)
        partier_per_val[val] = [p for p in NYCKELPARTIER[val] if p in finns]
    distrikt = [distrikt_ur_db(con, ar, r["kod"], geo.kort_namn(r["namn"]), partier_per_val) for r in medlemmar]
    for d in distrikt:
        saknas_val = [val for val in VAL if val not in d]
        if saknas_val:
            raise SystemExit(f"FEL: {ar} {d['kod']}: saknar {saknas_val} - majorna_medlem ska ha data i alla tre "
                              "valen i en slutlig historikfil, annars sänker raknat=False antalet räknade tyst")
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
            else:
                print(f"VARNING: {ar} rf: ingen vgregion-rad, riket utelämnas för regionvalet", file=sys.stderr)
    verklig = _mandat_riket_rd(con, ar)
    rd_summa = schema._summa(distrikt, "rd")["roster"]
    mandat = {"riksdag_verklig": verklig, "riksdag_majorna": jamkade_uddatal(rd_summa, 349) if rd_summa else {},
              "metod": f"Räkneexempel: 4 %-spärr och jämkade uddatalsmetoden tillämpade på Majornas riksdagsröster {ar}."}
    valdag = con.execute("SELECT valdag FROM val WHERE ar=? AND val='rd'", (ar,)).fetchone()
    v = schema.bygg_valdata(ar, distrikt, "slutlig", jamforelser, mandat,
                            uppdaterad=(valdag["valdag"] + "T00:00:00") if valdag else None,
                            kalla=f"Valmyndigheten, slutlig rösträkning per valdistrikt {ar}.")
    v["meta"]["avgransning"] = f"{len(distrikt)} valdistrikt som täcker samma yta som dagens 23 (areametod)"
    return v


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("vad", choices=["historik", "swing2022", "geo2006", "ar", "allt"])
    ap.add_argument("aren", nargs="*", help="för 'ar' eller 'allt': vilka historikår (default 2006 2010 2014 2018)")
    ap.add_argument("--ut", default=ROT / "data")
    ap.add_argument("--db", default=DB)
    a = ap.parse_args()
    if a.vad in ("historik", "swing2022", "geo2006") and a.aren:
        print(f"FEL: {a.vad} tar inga år, fick {' '.join(a.aren)}", file=sys.stderr)
        return 1
    if a.vad in ("ar", "allt"):
        aren = a.aren or [str(x) for x in BYGGBARA_AR]
        for s in aren:
            if not s.isdigit():
                print(f"FEL: {s!r} är inte ett årtal", file=sys.stderr)
                return 1
            if int(s) not in BYGGBARA_AR:
                print(f"FEL: {int(s)} byggs inte av det här skriptet "
                      "(2022 och 2026 byggs av bygg_data.py och uppdatera_2026.py)", file=sys.stderr)
                return 1
    ut = Path(a.ut)
    con = oppna(a.db)
    skrivna = []
    if a.vad in ("historik", "allt"):
        skrivna += schema.skriv(ut / "historik", bygg_historik(con))
    if a.vad in ("swing2022", "allt"):
        skrivna += schema.skriv(ut / "swing_2022", bygg_swing_2022(con))
    if a.vad in ("geo2006", "allt"):
        skrivna += schema.skriv(ut / "distrikt_2006", bygg_geo(2006, forenkla=True), json_suffix=".geojson")
    if a.vad in ("ar", "allt"):
        for s in aren:
            arnum = int(s)
            skrivna += schema.skriv(ut / f"valdata_{arnum}", bygg_valdata_ar(con, arnum))
            if arnum not in GEO_FORENKLA_AR:
                skrivna += schema.skriv(ut / f"distrikt_{arnum}", bygg_geo(arnum, forenkla=False), json_suffix=".geojson")
    for f in skrivna:
        print(f"    {f.stat().st_size / 1024:6.1f} kB  {f}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
