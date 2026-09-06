#!/usr/bin/env python3
"""Hämtar ett bakgrundslager för kartan från OpenStreetMap (Overpass) och skriver data/bakgrund.json/.js.

    .venv/bin/python scripts/hamta_bakgrund.py [--ut data] [--geojson data/distrikt_2022.geojson]

Lagret är valfritt: saknas filen ritar sidan kartan mot enfärgad bakgrund. Vid nätverksfel
lämnas befintliga filer orörda och skriptet avslutas med kod 2.
Innehåll: gator, spårväg, hållplatser, vatten, parker och stadsdelsnamn, klippta till
distriktens bbox med marginal, förenklade till 2 m och avrundade till 5 decimaler.
Data © OpenStreetMaps bidragsgivare (ODbL).
"""
import argparse
import json
import sys
import urllib.parse
import urllib.request
from pathlib import Path

from pyproj import Transformer
from shapely.geometry import LineString, Polygon, box
from shapely.ops import linemerge, polygonize, transform

ROT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROT))

from scripts import schema  # noqa: E402

GATOR = ["motorway", "trunk", "primary", "secondary", "tertiary", "residential", "living_street",
         "pedestrian", "unclassified", "motorway_link", "trunk_link", "primary_link", "secondary_link"]
PLATSER = {"suburb", "locality", "neighbourhood", "quarter"}
MARGINAL = (0.008, 0.004)  # grader i longitud och latitud
OVERPASS = "https://overpass-api.de/api/interpreter"

TILL_M = Transformer.from_crs("EPSG:4326", "EPSG:3006", always_xy=True).transform
TILL_GRADER = Transformer.from_crs("EPSG:3006", "EPSG:4326", always_xy=True).transform


def fraga(bbox):
    w, s, e, n = bbox
    b = f"({s},{w},{n},{e})"
    gator = "|".join(GATOR)
    return f"""[out:json][timeout:90];
(
  way["highway"~"^({gator})$"]{b};
  way["railway"="tram"]{b};
  node["railway"="tram_stop"]{b};
  way["natural"="water"]{b};
  relation["natural"="water"]{b};
  way["leisure"="park"]{b};
  node["place"~"^({'|'.join(sorted(PLATSER))})$"]{b};
);
out geom;"""


def hamta(bbox, url=OVERPASS, timeout=120):
    data = urllib.parse.urlencode({"data": fraga(bbox)}).encode()
    req = urllib.request.Request(url, data=data, headers={"User-Agent": "majposten-valgrafik/1.0"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read())["elements"]


def _punkter(geometri):
    return [(p["lon"], p["lat"]) for p in geometri]


def _runda(koordinater, decimaler):
    return [[round(x, decimaler), round(y, decimaler)] for x, y in koordinater]


def _delar(geom):
    if geom.is_empty:
        return []
    return list(geom.geoms) if hasattr(geom, "geoms") else [geom]


def _linjer(punkter, klipp_m, tolerans, decimaler):
    """WGS84-punkter -> förenklade, klippta linjer i WGS84 (lista av koordinatlistor)."""
    if len(punkter) < 2:
        return []
    linje = transform(TILL_M, LineString(punkter)).simplify(tolerans, preserve_topology=True)
    ut = []
    for del_ in _delar(linje.intersection(klipp_m)):
        if del_.geom_type == "LineString" and len(del_.coords) >= 2:
            ut.append(_runda(transform(TILL_GRADER, del_).coords, decimaler))
    return ut


def _ytor(polygon_grader, klipp_m, tolerans, decimaler):
    """Polygon i WGS84 -> förenklade, klippta ytterringar i WGS84."""
    if not polygon_grader.is_valid:
        polygon_grader = polygon_grader.buffer(0)
    yta = transform(TILL_M, polygon_grader).simplify(tolerans, preserve_topology=True)
    ut = []
    for del_ in _delar(yta.intersection(klipp_m)):
        if del_.geom_type == "Polygon" and del_.area > 25:
            ut.append(_runda(transform(TILL_GRADER, del_).exterior.coords, decimaler))
    return ut


def _relation_till_polygoner(rel):
    linjer = [LineString(_punkter(m["geometry"])) for m in rel.get("members", [])
              if m.get("role", "outer") in ("outer", "") and m.get("type") == "way" and len(m.get("geometry", [])) >= 2]
    if not linjer:
        return []
    sammanslaget = linemerge(linjer) if len(linjer) > 1 else linjer[0]
    return list(polygonize(_delar(sammanslaget)))


def packa(elements, bbox, tolerans_m=2.0, decimaler=5):
    """Overpass-element -> kompakt struktur för sidan."""
    w, s, e, n = bbox
    klipp_m = transform(TILL_M, box(w, s, e, n))
    ut = {"bbox": list(bbox), "gator": [], "sparvag": [], "hallplatser": [], "vatten": [], "parker": [], "platser": []}
    hallplatser = {}
    for el in elements:
        tags = el.get("tags", {})
        typ = el.get("type")
        if typ == "node":
            lon, lat = el.get("lon"), el.get("lat")
            if lon is None or not (w <= lon <= e and s <= lat <= n) or not tags.get("name"):
                continue
            if tags.get("railway") == "tram_stop":
                hallplatser.setdefault(tags["name"], []).append((lon, lat))
            elif tags.get("place") in PLATSER:
                ut["platser"].append({"namn": tags["name"], "typ": tags["place"],
                                      "k": [round(lon, decimaler), round(lat, decimaler)]})
        elif typ == "way":
            punkter = _punkter(el.get("geometry", []))
            if tags.get("highway") in GATOR:
                for k in _linjer(punkter, klipp_m, tolerans_m, decimaler):
                    post = {"typ": tags["highway"].replace("_link", ""), "k": k}
                    if tags.get("name"):
                        post["namn"] = tags["name"]
                    ut["gator"].append(post)
            elif tags.get("railway") == "tram":
                for k in _linjer(punkter, klipp_m, tolerans_m, decimaler):
                    ut["sparvag"].append({"k": k})
            elif tags.get("natural") == "water" or tags.get("leisure") == "park":
                if len(punkter) >= 4 and punkter[0] == punkter[-1]:
                    nyckel = "vatten" if tags.get("natural") == "water" else "parker"
                    ut[nyckel].extend(_ytor(Polygon(punkter), klipp_m, tolerans_m, decimaler))
        elif typ == "relation" and tags.get("natural") == "water":
            for poly in _relation_till_polygoner(el):
                ut["vatten"].extend(_ytor(poly, klipp_m, tolerans_m, decimaler))
    for namn, punkter in sorted(hallplatser.items()):
        lon = sum(p[0] for p in punkter) / len(punkter)
        lat = sum(p[1] for p in punkter) / len(punkter)
        ut["hallplatser"].append({"namn": namn, "k": [round(lon, decimaler), round(lat, decimaler)]})
    ordning = {t: i for i, t in enumerate(GATOR)}
    ut["gator"].sort(key=lambda g: -ordning.get(g["typ"], 99))  # småvägar först, stora leder ritas sist
    return ut


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--geojson", default=ROT / "data" / "distrikt_2022.geojson")
    ap.add_argument("--ut", default=ROT / "data")
    ap.add_argument("--url", default=OVERPASS)
    a = ap.parse_args()
    fc = json.loads(Path(a.geojson).read_text("utf-8"))
    w, s, e, n = fc["bbox"]
    bbox = [round(w - MARGINAL[0], 4), round(s - MARGINAL[1], 4), round(e + MARGINAL[0], 4), round(n + MARGINAL[1], 4)]
    print(f"Hämtar från {a.url} för bbox {bbox} ...")
    try:
        elements = hamta(bbox, a.url)
    except Exception as ex:  # nätverk, timeout, HTTP
        print(f"FEL: kunde inte hämta från Overpass: {ex!r}. Befintliga filer lämnas orörda.")
        sys.exit(2)
    ut = packa(elements, bbox)
    filer = schema.skriv(Path(a.ut) / "bakgrund", ut)
    for f in filer:
        print(f"    {f.stat().st_size / 1024:7.1f} kB  {f}")
    print("    " + ", ".join(f"{k}: {len(v)}" for k, v in ut.items() if isinstance(v, list)))
    print("OK")


if __name__ == "__main__":
    main()
