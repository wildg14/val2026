"""Hämtar Valmyndighetens resultat-JSON för val 2022 (nya formatet, resultat.val.se)
för alla nivåer som rör Göteborgs kommun (1480): riket per valtyp, valkrets/län,
kommun och alla valdistrikt, för RD, RF och KF.

Adresserna är hämtade ur webbappens JS-bundle (resultat.val.se/assets/index-*.js):
  valgeografi: https://resultat.val.se/data/valgeografi/valgeografi_val2022.json
  resultat:    https://resultat.val.se/data/resultat/val2022/<koder i sökvägen med _>_S.json
där sökvägen är den som visas i webbläsaren, till exempel
https://resultat.val.se/val2022/KF/14/1480/14800535 ger KF_14_1480_14800535_S.json.
S = slutligt, P = preliminärt.

Varje distrikts-JSON innehåller antal röster per parti 2022 samt fälten
antalRosterForegaendeVal och andelRosterForegaendeVal (2018) när fältet
jamforbar är true, annars null. Kör om skriptet för att fylla på filer som saknas.
"""
import csv
import json
import os
import sys
import time
import urllib.request
from concurrent.futures import ThreadPoolExecutor

SCRATCH = "/Users/daniel/code/Temp/Historiska dokument"
OUT_DIR = SCRATCH + "/dl_webb/2022/json"
VALGEOGRAFI_URL = "https://resultat.val.se/data/valgeografi/valgeografi_val2022.json"
RESULTAT_URL = "https://resultat.val.se/data/resultat/val2022/{path}_S.json"
KOMMUN = "1480"
MANIFEST = OUT_DIR + "/manifest.csv"
UA = "Mozilla/5.0 (Majposten valhistorik; kontakt via val.se-formulär ej aktuell)"


def hamta(url, mal):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            data = r.read()
        with open(mal, "wb") as f:
            f.write(data)
        return 200, len(data)
    except urllib.error.HTTPError as e:
        return e.code, 0
    except Exception as e:  # nätverksfel
        return -1, 0


def noder(tree):
    """Ger (valtyp, niva, kod, namn, path) för valtypsnivån, alla nivåer vars
    delträd innehåller Göteborg (1480) samt alla noder under Göteborg."""
    ut = []

    def walk(node, chain, valtyp):
        kod = str(node.get("kod"))
        typ = node.get("typ")
        chain = chain + [kod]
        if typ == "VALTYP":
            valtyp = kod
        barn = node.get("valgeografi") or []
        egen = kod == KOMMUN or (kod.startswith(KOMMUN) and len(kod) in (6, 8))
        under = [walk(b, chain, valtyp) for b in barn]
        traff = egen or any(under)
        if typ != "VALTILLFALLE" and (traff or typ == "VALTYP"):
            ut.append((valtyp, typ, kod, node.get("namn"), "_".join(chain[1:])))
        return traff

    walk(tree, [], None)
    ut.sort(key=lambda n: (n[0], len(n[4]), n[4]))
    return ut


def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    vg_fil = SCRATCH + "/dl_webb/2022/valgeografi_val2022.json"
    if not os.path.exists(vg_fil):
        print("hämtar valgeografi", hamta(VALGEOGRAFI_URL, vg_fil))
    tree = json.load(open(vg_fil, encoding="utf-8"))
    lista = noder(tree)
    # Lägg till mellannivåer (valkrets/län) som innehåller 1480 men inte fångades
    print("noder att hämta:", len(lista))
    rader = []

    def jobb(n):
        valtyp, typ, kod, namn, path = n
        url = RESULTAT_URL.format(path=path)
        mal = os.path.join(OUT_DIR, path + "_S.json")
        if os.path.exists(mal) and os.path.getsize(mal) > 0:
            return [valtyp, typ, kod, namn, path, url, "finns", os.path.getsize(mal)]
        status, n_bytes = hamta(url, mal)
        time.sleep(0.05)
        return [valtyp, typ, kod, namn, path, url, str(status), n_bytes]

    with ThreadPoolExecutor(max_workers=4) as ex:
        for r in ex.map(jobb, lista):
            rader.append(r)
    with open(MANIFEST, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f, delimiter=";", lineterminator="\n")
        w.writerow(["valtyp", "niva", "kod", "namn", "path", "url", "status", "bytes"])
        w.writerows(rader)
    from collections import Counter
    print("status:", Counter((r[0], r[1], r[6]) for r in rader))
    print("skrev", MANIFEST)


if __name__ == "__main__":
    sys.exit(main())
