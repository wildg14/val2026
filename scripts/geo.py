"""Valmyndighetens valgeografi (SWEREF99 TM) -> GeoJSON i WGS84 för de valda distrikten."""
import json
import zipfile

from pyproj import Transformer
from shapely.geometry import mapping, shape
from shapely.ops import polylabel


def kort_namn(vdnamn):
    """'Västra Centrum, Mariaplan' -> 'Mariaplan'."""
    return str(vdnamn).split(", ", 1)[-1].strip()


def egenskaper(props):
    """(kod, kort namn) ur en features egenskaper. 2022: Lkfv och Vdnamn. 2026: Valdistriktskod och Valdistriktsnamn."""
    kod = props.get("Lkfv", props.get("Valdistriktskod", ""))
    namn = props.get("Vdnamn", props.get("Valdistriktsnamn", ""))
    kod = str(kod).strip() if kod is not None else ""
    return kod, kort_namn(namn) if namn else ""


def _runda(koordinater, decimaler):
    return [[round(x, decimaler), round(y, decimaler)] for x, y in koordinater]


def las_distrikt(zip_path, koder, decimaler=6):
    """Läser zip-filen med länets valdistrikt och returnerar en FeatureCollection (WGS84)
    med exakt de distrikt som finns i `koder`, sorterade på kod.

    Polygonerna har 12 till 121 hörn i källan, så de förenklas inte: gemensamma gränser
    bevaras därmed exakt. Egenskaper: kod, namn, etikett (punkt inuti polygonen), area_km2.

    Egenskapsnamnen skiljer sig mellan år: 2022 har Lkfv och Vdnamn, 2026 har Valdistriktskod
    och Valdistriktsnamn (se egenskaper()). Zip-filen kan innehålla antingen .json eller .geojson.
    """
    with zipfile.ZipFile(zip_path) as z:
        namn = [n for n in z.namelist() if n.lower().endswith((".json", ".geojson"))]
        if not namn:
            raise ValueError(f"{zip_path}: innehåller ingen .json- eller .geojson-fil")
        gj = json.loads(z.read(namn[0]).decode("utf-8"))
    tr = Transformer.from_crs("EPSG:3006", "EPSG:4326", always_xy=True)
    vill = set(str(k) for k in koder)
    features = []
    for ft in gj["features"]:
        kod, namn_kort = egenskaper(ft["properties"])
        if kod not in vill:
            continue
        g = shape(ft["geometry"])
        if g.geom_type == "MultiPolygon":
            g = max(g.geoms, key=lambda p: p.area)
        ringar = []
        for ring in [g.exterior, *g.interiors]:
            ringar.append(_runda((tr.transform(x, y) for x, y in ring.coords), decimaler))
        poly = shape({"type": "Polygon", "coordinates": ringar}).buffer(0)
        if poly.geom_type == "MultiPolygon":
            poly = max(poly.geoms, key=lambda p: p.area)
        etikett = polylabel(poly, tolerance=1e-5)
        geom = mapping(poly)
        features.append({
            "type": "Feature",
            "properties": {
                "kod": kod,
                "namn": namn_kort or kod,
                "etikett": [round(etikett.x, decimaler), round(etikett.y, decimaler)],
                "area_km2": round(g.area / 1e6, 4),
            },
            "geometry": {"type": "Polygon",
                         "coordinates": [_runda(r, decimaler) for r in geom["coordinates"]]},
        })
    saknas = vill - {f["properties"]["kod"] for f in features}
    if saknas:
        raise ValueError(f"Distrikt saknas i geodatan: {sorted(saknas)}")
    features.sort(key=lambda f: f["properties"]["kod"])
    xs = [c[0] for f in features for c in f["geometry"]["coordinates"][0]]
    ys = [c[1] for f in features for c in f["geometry"]["coordinates"][0]]
    return {"type": "FeatureCollection", "bbox": [min(xs), min(ys), max(xs), max(ys)], "features": features}
