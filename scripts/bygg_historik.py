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

Underkommandot "allt" är inte körbart förrän alla delar finns (Task 4).
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
BAS_AR = 2018  # basår för swing_2022 (Task 2)
PARTIER = ["V", "S", "MP", "SD", "M", "C", "L", "KD", "D", "FI", "K", OVRIGA]
ALLA_KODER = [p for p in PARTIER if p != OVRIGA]  # de elva namngivna partikoderna, oavsett vilket val de har egen kolumn i
NIVAER = ["majorna", "goteborg", "riket"]
KALLA = "Valmyndigheten, slutlig rösträkning per valdistrikt 2006 till 2022, sammanställd i data/historik/majorna_historik.sqlite"


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


def distrikt_ur_db(con, ar, kod, namn):
    """Ett distrikt ett år i sidans schema: roster per val med sidans partikoder, summor ur distrikt_summa.

    Okända partikoder (utanför NYCKELPARTIER[val]) läggs i Övriga, eftersom rösttabellen `roster` inte
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
        roster = {p: 0 for p in NYCKELPARTIER[val]}
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
    bas_distrikt = [distrikt_ur_db(con, BAS_AR, kod18, namn_2022[kod22]) | {"kod": kod22}
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


def bygg_geo(ar, forenkla):
    raise SystemExit("geo byggs i Task 3")


def bygg_valdata_ar(con, ar):
    raise SystemExit("valdata per år byggs i Task 4")


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


if __name__ == "__main__":
    sys.exit(main())
