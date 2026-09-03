"""Bakgrundslagret: packning av Overpass-svar till kompakt lokal fil."""
from scripts import hamta_bakgrund as hb

BBOX = [11.90, 57.68, 11.93, 57.70]  # w, s, e, n


def vag(id_, tags, punkter):
    return {"type": "way", "id": id_, "tags": tags, "geometry": [{"lon": x, "lat": y} for x, y in punkter]}


def test_gata_forenklas_och_klipps():
    # Tre punkter på en nästan rak linje: mittpunkten avviker ~0,5 m och ska bort.
    g = vag(1, {"highway": "residential", "name": "Provgatan"},
            [(11.910, 57.690), (11.915, 57.6900045), (11.920, 57.690)])
    utanfor = vag(2, {"highway": "residential"}, [(11.95, 57.72), (11.96, 57.72)])
    ut = hb.packa([g, utanfor], BBOX)
    assert ut["bbox"] == BBOX
    assert len(ut["gator"]) == 1
    assert ut["gator"][0]["typ"] == "residential" and ut["gator"][0]["namn"] == "Provgatan"
    assert ut["gator"][0]["k"] == [[11.91, 57.69], [11.92, 57.69]]


def test_hallplatser_med_samma_namn_slas_ihop():
    n1 = {"type": "node", "id": 1, "lat": 57.6900, "lon": 11.9100, "tags": {"railway": "tram_stop", "name": "Mariaplan"}}
    n2 = {"type": "node", "id": 2, "lat": 57.6902, "lon": 11.9102, "tags": {"railway": "tram_stop", "name": "Mariaplan"}}
    n3 = {"type": "node", "id": 3, "lat": 57.6950, "lon": 11.9200, "tags": {"place": "suburb", "name": "Majorna"}}
    ut = hb.packa([n1, n2, n3], BBOX)
    assert ut["hallplatser"] == [{"namn": "Mariaplan", "k": [11.9101, 57.6901]}]
    assert ut["platser"] == [{"namn": "Majorna", "typ": "suburb", "k": [11.92, 57.695]}]


def test_vatten_relation_blir_polygon():
    rel = {"type": "relation", "id": 9, "tags": {"natural": "water", "type": "multipolygon"}, "members": [
        {"type": "way", "role": "outer", "geometry": [{"lon": 11.905, "lat": 57.695}, {"lon": 11.915, "lat": 57.695}, {"lon": 11.915, "lat": 57.699}]},
        {"type": "way", "role": "outer", "geometry": [{"lon": 11.915, "lat": 57.699}, {"lon": 11.905, "lat": 57.699}, {"lon": 11.905, "lat": 57.695}]},
    ]}
    park = vag(5, {"leisure": "park"}, [(11.92, 57.68), (11.925, 57.68), (11.925, 57.685), (11.92, 57.68)])
    ut = hb.packa([rel, park], BBOX)
    assert len(ut["vatten"]) == 1 and len(ut["vatten"][0]) >= 4
    assert len(ut["parker"]) == 1


def test_sparvag():
    t = vag(7, {"railway": "tram"}, [(11.91, 57.69), (11.92, 57.691)])
    ut = hb.packa([t], BBOX)
    assert len(ut["sparvag"]) == 1 and ut["gator"] == []
