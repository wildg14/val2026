# -*- coding: utf-8 -*-
"""
val2018_prova_xml.py - provar adresser pa historik.val.se (och nagra andra) dar
Valmyndighetens XML-radata for 2018 (slutresultat_1480R.xml med flera) kunde
tankas ligga. Sparar svar som inte ar 404 i NEDLADDNINGSMAPP och skriver en
statusrad per adress.

Resultat 2026-09-03: statistiksidan for 2018 anger under "Radata i XML-format"
en tom lank med texten "Protokoll gallrat", och ingen av adresserna nedan ger
en XML-fil. Se docs/historik/noter/val2018.md.

Kors med:
  <venv>/bin/python scripts/historik/val2018_prova_xml.py
"""
import os
import sys
import urllib.request
import urllib.error

NEDLADDNINGSMAPP = ("/private/tmp/claude-501/-Users-daniel-code-Temp/"
                    "f347baf2-1af3-43b3-b36d-e80b868ede0e/scratchpad/dl2018")

ADRESSER = [
    # sidor som finns (referens)
    "https://historik.val.se/val/val2018/statistik/index.html",
    "https://historik.val.se/val/val2018/slutresultat/R/rike/index.html",
    "https://historik.val.se/val/val2018/slutresultat/R/valdistrikt/14/80/1017/index.html",
    # monster fran 2014 (dar /val/val2014/slutresultat/slutresultat.zip finns)
    "https://historik.val.se/val/val2018/slutresultat/slutresultat.zip",
    "https://historik.val.se/val/val2018/slutresultat/slutresultat_2018.zip",
    "https://historik.val.se/val/val2018/slutresultat/slutresultat_1480R.xml",
    "https://historik.val.se/val/val2018/slutresultat/slutresultat_00R.xml",
    "https://historik.val.se/val/val2018/slutresultat/xml/slutresultat_1480R.xml",
    "https://historik.val.se/val/val2018/slutresultat/xml/slutresultat_00R.xml",
    "https://historik.val.se/val/val2018/slutresultat/R/rike/slutresultat_00R.xml",
    "https://historik.val.se/val/val2018/slutresultat/R/rike/slutresultat.zip",
    "https://historik.val.se/val/val2018/slutresultat/index.html",
    "https://historik.val.se/val/val2018/xml/slutresultat_1480R.xml",
    "https://historik.val.se/val/val2018/statistik/slutresultat.zip",
    "https://historik.val.se/val/val2018/statistik/slutresultat_2018.zip",
    "https://historik.val.se/val/val2018/statistik/2018_slutresultat.zip",
    "https://historik.val.se/val/val2018/statistik/slutresultat_xml.zip",
    "https://historik.val.se/val/val2018/statistik/xml.zip",
    "https://historik.val.se/val/val2018/statistik/slutresultat_1480R.xml",
    "https://historik.val.se/val/val2018/radata/index.html",
    "https://historik.val.se/val/val2018/valresultat.html",
    "https://historik.val.se/val/val2018/",
    "https://data.val.se/val/val2018/slutresultat/slutresultat.zip",
    "https://data.val.se/val/val2018/slutresultat/slutresultat_1480R.xml",
    "https://data.val.se/val/val2018/slutresultat/index.html",
    "https://www.val.se/val/val2018/statistik/slutresultat.zip",
    "https://www.val.se/valresultat/riksdag-region-och-kommun/2018/radata-och-statistik.html",
]


def main():
    os.makedirs(NEDLADDNINGSMAPP, exist_ok=True)
    traffar = []
    for u in ADRESSER:
        try:
            req = urllib.request.Request(u, headers={"User-Agent": "Mozilla/5.0 (majposten valgrafik)"})
            with urllib.request.urlopen(req, timeout=60) as sv:
                data = sv.read()
                status, typ, slut = sv.status, sv.headers.get("Content-Type", ""), sv.geturl()
        except urllib.error.HTTPError as e:
            status, typ, slut, data = e.code, e.headers.get("Content-Type", ""), u, b""
        except Exception as e:  # natfel
            status, typ, slut, data = "fel", str(e), u, b""
        print(f"{status} {len(data):>8} {typ[:40]:40} {u} -> {slut}")
        if status == 200 and ("xml" in typ or "zip" in typ or u.endswith((".xml", ".zip"))):
            namn = os.path.join(NEDLADDNINGSMAPP, os.path.basename(u))
            with open(namn, "wb") as f:
                f.write(data)
            traffar.append(namn)
    print("xml/zip-traffar:", traffar or "inga")
    return 0


if __name__ == "__main__":
    sys.exit(main())
