"""Valmyndighetens valgeografi (SWEREF99 TM) -> GeoJSON i WGS84 för de valda distrikten."""
import json
import zipfile

from pyproj import Transformer
from shapely.geometry import mapping, shape
from shapely.ops import polylabel, transform, unary_union


def kort_namn(vdnamn):
    """'Västra Centrum, Mariaplan' -> 'Mariaplan'."""
    return str(vdnamn).split(", ", 1)[-1].strip()


def egenskaper(props):
    """(kod, kort namn) ur en features egenskaper. 2022: Lkfv och Vdnamn. 2026: Valdistriktskod och
    Valdistriktsnamn. Faller tillbaka på den andra kolumnen även när den första är null eller tom sträng."""
    kod = props.get("Lkfv") or props.get("Valdistriktskod") or ""
    namn = props.get("Vdnamn") or props.get("Valdistriktsnamn") or ""
    return str(kod).strip(), kort_namn(namn) if namn else ""


def _runda(koordinater, decimaler):
    return [[round(x, decimaler), round(y, decimaler)] for x, y in koordinater]


_TILL_SWEREF = Transformer.from_crs("EPSG:4326", "EPSG:3006", always_xy=True).transform


def features_till_schema(features, forenkla_grader=None):
    """En lista {"geometry": shapely-polygon (WGS84), "kod": str, "namn": str, valfritt "area_km2"}
    -> sidans featurecollection: etikett (polylabel), area_km2, bbox, sorterad på kod.

    forenkla_grader förenklar varje polygon (simplify, preserve_topology=True) innan buffer(0);
    utan den bevaras gemensamma gränser exakt. buffer(0) lagar geometri som blivit ogiltig (till
    exempel av avrundning eller förenkling); blir resultatet en MultiPolygon behålls den största
    delen. area_km2 räknas i EPSG:3006 om featuren inte redan har ett eget värde - las_distrikt
    skickar med källans egen exakta area (SWEREF99 TM, före avrundningen till sex decimaler som
    annars skulle ge ett annat värde i fjärde decimalen); bygg_historik.bygg_geo saknar en sådan
    källa och får arean räknad här. Delas av las_distrikt (2022, 2026) och bygg_geo (2006 till
    2018), så att alla år får exakt samma schembygge.
    """
    ut = []
    for ft in features:
        g = ft["geometry"]
        if forenkla_grader is not None:
            g = g.simplify(forenkla_grader, preserve_topology=True)
        g = g.buffer(0)
        if g.geom_type == "MultiPolygon":
            g = max(g.geoms, key=lambda p: p.area)
        etikett = polylabel(g, tolerance=1e-5)
        area_km2 = ft["area_km2"] if "area_km2" in ft else transform(_TILL_SWEREF, g).area / 1e6
        geom = mapping(g)
        ut.append({
            "type": "Feature",
            "properties": {
                "kod": ft["kod"],
                "namn": ft["namn"],
                "etikett": [round(etikett.x, 6), round(etikett.y, 6)],
                "area_km2": round(area_km2, 4),
            },
            "geometry": {"type": "Polygon", "coordinates": [_runda(r, 6) for r in geom["coordinates"]]},
        })
    ut.sort(key=lambda f: f["properties"]["kod"])
    xs = [c[0] for f in ut for c in f["geometry"]["coordinates"][0]]
    ys = [c[1] for f in ut for c in f["geometry"]["coordinates"][0]]
    return {"type": "FeatureCollection", "bbox": [min(xs), min(ys), max(xs), max(ys)], "features": ut}


def las_distrikt(zip_path, koder, decimaler=6):
    """Läser zip-filen med länets valdistrikt och returnerar en FeatureCollection (WGS84)
    med exakt de distrikt som finns i `koder`, sorterade på kod.

    Polygonerna har 12 till 121 hörn i källan, så de förenklas inte: gemensamma gränser
    bevaras därmed exakt (features_till_schema anropas utan forenkla_grader). Egenskaper:
    kod, namn, etikett (punkt inuti polygonen), area_km2.

    area_km2 skickas med som källans egen area (kvadratmeter i SWEREF99 TM, käll-CRS:ens
    ursprungliga precision) i stället för att räknas om från den avrundade WGS84-polygonen -
    annars skulle en ombyggnad ge ett annat värde i fjärde decimalen för några distrikt.

    Egenskapsnamnen skiljer sig mellan år: 2022 har Lkfv och Vdnamn, 2026 har Valdistriktskod
    och Valdistriktsnamn (se egenskaper()). Zip-filen kan innehålla antingen .json eller .geojson.
    """
    with zipfile.ZipFile(zip_path) as z:
        namn = sorted((n for n in z.namelist() if n.lower().endswith((".json", ".geojson"))),
                      key=lambda n: not n.lower().endswith(".geojson"))
        if not namn:
            raise ValueError(f"{zip_path}: innehåller ingen .json- eller .geojson-fil")
        vald = namn[0]
        gj = json.loads(z.read(vald).decode("utf-8"))
        if "features" not in gj:
            raise ValueError(f"{vald}: saknar features")
    tr = Transformer.from_crs("EPSG:3006", "EPSG:4326", always_xy=True)
    vill = set(str(k) for k in koder)
    poster = []
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
        poster.append({"geometry": shape({"type": "Polygon", "coordinates": ringar}),
                       "kod": kod, "namn": namn_kort or kod, "area_km2": g.area / 1e6})
    fc = features_till_schema(poster)
    saknas = vill - {f["properties"]["kod"] for f in fc["features"]}
    if saknas:
        raise ValueError(f"Distrikt saknas i geodatan: {sorted(saknas)}")
    return fc


def _union_3006(fc, tr):
    """Featurecollectionens polygoner (WGS84), projicerade till EPSG:3006 och slagna ihop till en union.

    En ogiltig polygon (självkorsande ring) får unary_union och symmetric_difference att kasta
    GEOSException; den lagas därför med buffer(0). Den som inte går att laga (ingen area) ger
    ValueError med distriktets kod, i stället för ett fel längre in i shapely."""
    polygoner = []
    for f in fc["features"]:
        g = transform(tr.transform, shape(f["geometry"]))
        if not g.is_valid:
            kod = (f.get("properties") or {}).get("kod", "?")
            g = g.buffer(0)
            if g.is_empty or not g.is_valid:
                raise ValueError(f"distrikt {kod}: ogiltig geometri som inte går att laga med buffer(0)")
        polygoner.append(g)
    return unary_union(polygoner)


def union_yta(fc):
    """Unionens area i kvadratmeter, med fc:s koordinater (WGS84) projicerade till EPSG:3006."""
    tr = Transformer.from_crs("EPSG:4326", "EPSG:3006", always_xy=True)
    return _union_3006(fc, tr).area


def jamfor_union(fc_a, fc_b):
    """Projicerar två featurecollections (WGS84) till EPSG:3006, tar unionen av var och en, och
    jämför dem geometriskt - inte bara som en summa av avrundade ytor, som varken ser luckor eller
    överlapp. `skillnad` är fc_b:s unionsyta minus fc_a:s (kvadratmeter). `symmetrisk_differens` är
    arean som skiljer mellan unionerna, dvs luckor och överlapp tillsammans (kvadratmeter): nära noll
    betyder att områdena täcker exakt samma yta, även om enskilda distrikt inom dem är omritade."""
    tr = Transformer.from_crs("EPSG:4326", "EPSG:3006", always_xy=True)
    union_a = _union_3006(fc_a, tr)
    union_b = _union_3006(fc_b, tr)
    yta_a, yta_b = union_a.area, union_b.area
    return {
        "yta_a": yta_a,
        "yta_b": yta_b,
        "skillnad": yta_b - yta_a,
        "symmetrisk_differens": union_a.symmetric_difference(union_b).area,
    }
