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
ALLA_KODER = PARTIER[:-1]  # de elva namngivna partikoderna, oavsett vilket val de har egen kolumn i
NIVAER = ["majorna", "goteborg", "riket"]
KALLA = "Valmyndigheten, slutlig rösträkning per valdistrikt 2006 till 2022, sammanställd i data/historik/majorna_historik.sqlite"


def oppna(path=DB):
    if not Path(path).exists():
        print(f"FEL: {path} saknas, bygg den med scripts/historik/bygg_databas.py", file=sys.stderr)
        sys.exit(1)
    con = sqlite3.connect(f"file:{path}?mode=ro", uri=True)
    con.row_factory = sqlite3.Row
    return con


def _post(rader, val):
    """Rader ur tidsserie för ett (ar, val, niva) -> en post i serien.

    roster får exakt nycklarna NYCKELPARTIER[val] plus Övriga (sidans partiuppsättning för
    detta val). Partier i tidsserien utanför den uppsättningen, till exempel FI i riksdagsvalet
    eller K i regionvalet, läggs i Övriga tillsammans med SUMMA_ÖVRIGA. Så blir raden identisk
    med den kurerade valdata_<år>.json som redan följer sidans schema.
    """
    nycklar = NYCKELPARTIER[val]
    roster = {p: 0 for p in nycklar}
    roster[OVRIGA] = 0
    giltiga = rostande = rostberattigade = None
    antal = metod = None
    for r in rader:
        p = r["parti"]
        v = int(r["roster"] or 0)
        if p == "SUMMA_ÖVRIGA" or (p in ALLA_KODER and p not in nycklar):
            roster[OVRIGA] += v
        elif p in nycklar:
            roster[p] = v
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
                post = _post(rader, val)
                if post is None:
                    raise SystemExit(f"FEL: tidsserie saknar {ar} {val} {niva}")
                if niva == "majorna":
                    metod_per_ar[str(ar)] = post["metod"]
                serie[val][niva].append({k: v for k, v in post.items() if k != "metod"})
    return {"meta": {"byggd": dt.datetime.now().replace(microsecond=0).isoformat(), "kalla": KALLA, "ar": AR, "partier": PARTIER,
                     "noter": ["Serien börjar 2006. Valdistrikten ritades om helt inför det valet, så 2002 går inte att räkna om till dagens Majorna.",
                               "Liberalerna hette Folkpartiet till och med 2014; serien använder koden L hela vägen.",
                               "Övriga är giltiga röster minus de elva partierna ovan.",
                               "Partiuppsättningen per val följer sidans schema: riksdagsvalet V, S, MP, SD, M, C, L, KD; "
                               "partier utanför valets uppsättning, till exempel FI i riksdagsvalet, ingår i Övriga."],
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
