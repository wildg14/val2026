"""Valmyndighetens valgeografi (SWEREF99 TM) -> GeoJSON i WGS84 för de valda distrikten."""
import json
import zipfile

from pyproj import Transformer
from shapely.geometry import mapping, shape
from shapely.ops import linemerge, polygonize, polylabel, transform, unary_union


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


def _matcha_kod(ny, original):
    """Vilken originalpolygon (lista av (kod, polygon)) hör en ny, förenklad polygon till: den med
    störst överlappande yta. Om ingen overlap alls hittas (kan hända för en mycket liten remsa efter
    kraftig förenkling) faller matchningen tillbaka på vilken original som innehåller ny:s
    representative_point. Ger None om ingen original matchar på något sätt."""
    bast_kod, bast_overlapp = None, 0.0
    for kod, g in original:
        overlapp = g.intersection(ny).area
        if overlapp > bast_overlapp:
            bast_overlapp = overlapp
            bast_kod = kod
    if bast_kod is not None:
        return bast_kod
    punkt = ny.representative_point()
    for kod, g in original:
        if g.contains(punkt):
            return kod
    return None


def _forenkla_topologiskt(features, forenkla_grader):
    """Förenklar polygonernas gemensamma gränser en gång i stället för varje polygon för sig - annars
    förenklas en delad gräns olika på var sida, vilket ger överlapp och luckor mellan grannar (mätt
    till 23 par grannar som överlappade och 12 luckor, cirka 3 procent geometrisk drift i konturen,
    med det gamla per-polygon-anropet). Metod: nodar alla polygoners boundary till ett sammanhängande
    gränsnät (unary_union), delar upp det i linjer mellan knutpunkterna (linemerge), förenklar varje
    sådan linje en gång (simplify, preserve_topology=True) och bygger nya polygoner ur det förenklade
    nätet (polygonize). Två grannar som delade en gräns delar då fortfarande exakt samma (nu
    förenklade) gränslinje, så inget överlapp eller lucka kan uppstå mellan dem.

    Varje polygon lagas med buffer(0) om den inte redan är giltig (samma mönster som _union_3006);
    går den inte att laga blir felet ValueError med distriktets kod. En ensam feature ger bara en
    boundary, så unary_union av den ger redan en LineString direkt (ingen union att göra) - linemerge
    kastar då ValueError ("Cannot linemerge") eftersom den bara tar MultiLineString eller en sekvens
    av linjer, så det steget hoppas över när resultatet redan är en enda LineString.

    Kräver dessutom att ingen kod förekommer två gånger i features och att inga två källpolygoner
    (projicerade till EPSG:3006) överlappar mer än en kvadratmeter - annars är indatan inte lämplig
    att förenkla topologiskt, oavsett tolerans.

    Returnerar kod -> ny polygon. Kräver att polygonize ger exakt lika många polygoner som features
    (annars har två slagits ihop eller en delats av förenklingen) och att varje kod matchar exakt en
    ny polygon (_matcha_kod); annars ValueError med en begriplig förklaring - sänk då toleransen.
    """
    sedda = set()
    original = []
    for ft in features:
        kod, g = ft["kod"], ft["geometry"]
        if kod in sedda:
            raise ValueError(f"features_till_schema: koden {kod} förekommer två gånger")
        sedda.add(kod)
        if not g.is_valid:
            g = g.buffer(0)
            if g.is_empty or not g.is_valid:
                raise ValueError(
                    f"features_till_schema: distrikt {kod}: ogiltig geometri som inte går att laga "
                    "med buffer(0)")
        original.append((kod, g))
    projicerade = [(kod, transform(_TILL_SWEREF, g)) for kod, g in original]
    for i, (kod_i, g_i) in enumerate(projicerade):
        for kod_j, g_j in projicerade[i + 1:]:
            if g_i.intersection(g_j).area > 1:
                raise ValueError(
                    f"features_till_schema: källpolygonerna {kod_i} och {kod_j} överlappar, "
                    "förenkla inte")
    granser_ra = unary_union([g.boundary for _, g in original])
    granser = granser_ra if granser_ra.geom_type == "LineString" else linemerge(granser_ra)
    linjer = [granser] if granser.geom_type == "LineString" else list(granser.geoms)
    forenklade = [ln.simplify(forenkla_grader, preserve_topology=True) for ln in linjer]
    nya = list(polygonize(forenklade))
    if len(nya) != len(original):
        raise ValueError(
            f"features_till_schema: forenkla_grader={forenkla_grader} gav {len(nya)} polygoner ur "
            f"gränsnätet, väntade {len(original)} - sänk toleransen")
    tilldelning = {}
    for ny in nya:
        kod = _matcha_kod(ny, original)
        if kod is None:
            raise ValueError(
                f"features_till_schema: forenkla_grader={forenkla_grader} - hittar ingen "
                f"originalpolygon för en ny polygon (yta {ny.area:.2e} kvadratgrader), sänk toleransen")
        if kod in tilldelning:
            raise ValueError(
                f"features_till_schema: forenkla_grader={forenkla_grader} - {kod} matchar mer än en "
                f"ny polygon, sänk toleransen")
        tilldelning[kod] = ny
    # Ingen saknas-kontroll här: med kod-dubbletter uteslutna ovan och len(nya) == len(original)
    # redan säkrat måste tilldelning innehålla exakt alla original-koder (en ren räkneövning), så
    # en sådan gren vore aldrig nåbar.
    return tilldelning


def features_till_schema(features, forenkla_grader=None):
    """En lista {"geometry": shapely-polygon (WGS84), "kod": str, "namn": str, valfritt "area_km2"}
    -> sidans featurecollection: etikett (polylabel), area_km2, bbox, sorterad på kod.

    forenkla_grader förenklar gemensamma gränser topologiskt, en gång, innan buffer(0) - se
    _forenkla_topologiskt; utan den bevaras gemensamma gränser exakt. buffer(0) lagar geometri som
    blivit ogiltig (till exempel av avrundning eller förenkling); blir resultatet en MultiPolygon
    behålls den största delen. area_km2 räknas i EPSG:3006 om featuren inte redan har ett eget värde -
    las_distrikt skickar med källans egen exakta area (SWEREF99 TM, före avrundningen till sex
    decimaler som annars skulle ge ett annat värde i fjärde decimalen); bygg_historik.bygg_geo saknar
    en sådan källa och får arean räknad här. Delas av las_distrikt (2022, 2026) och bygg_geo (2006
    till 2018), så att alla år får exakt samma schembygge.

    I en förenklad fil (forenkla_grader satt) beskriver area_km2 den förenklade polygonens egen yta,
    inte det verkliga distriktets - konturen har flyttats något, vilket kan skilja uppåt några
    procent för ett enskilt distrikt även om totalsumman håller (förenklingen bevarar gemensamma
    gränser, så det en granne vinner förlorar den andra).
    """
    if not features:
        raise ValueError("inga distrikt att skriva")
    tilldelning = _forenkla_topologiskt(features, forenkla_grader) if forenkla_grader is not None else None
    ut = []
    for ft in features:
        g = tilldelning[ft["kod"]] if tilldelning is not None else ft["geometry"]
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


def las_distrikt(zip_path, koder):
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

    Kontrollerar att alla efterfrågade koder faktiskt hittades i geodatan innan features_till_schema
    anropas - annars ger en tom poster-lista "min() iterable argument is empty" i stället för listan
    på de saknade koderna, som är valnattens troligaste fel (en felskriven eller föråldrad kod).
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
            ringar.append(_runda((tr.transform(x, y) for x, y in ring.coords), 6))
        poster.append({"geometry": shape({"type": "Polygon", "coordinates": ringar}),
                       "kod": kod, "namn": namn_kort or kod, "area_km2": g.area / 1e6})
    saknas = vill - {p["kod"] for p in poster}
    if saknas:
        raise ValueError(f"Distrikt saknas i geodatan: {sorted(saknas)}")
    return features_till_schema(poster)


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
