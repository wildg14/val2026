#!/usr/bin/env python3
"""Hämtar Valmyndighetens resultatfiler för 2026 och packar upp dem till data/valnatt/<tidsstämpel>/.

    .venv/bin/python scripts/hamta_2026.py                       # preliminär räkning från val2026/
    .venv/bin/python scripts/hamta_2026.py --tillfalle s         # slutlig räkning
    .venv/bin/python scripts/hamta_2026.py --genrep              # simuleringarna, samma struktur, test: true
    .venv/bin/python scripts/hamta_2026.py --lokal MAPP          # zip-filer som redan ligger på disk
    .venv/bin/python scripts/hamta_2026.py --bara-om-nytt        # avsluta med kod 3 när index.md5 är oförändrad

Tre filer hämtas: riksdagen för hela landet (_00_RD), regionvalet för Västra Götaland (_14_RF) och
kommunvalet för Göteborg (_1480_KF). md5 kontrolleras mot index.md5 och JSON-filernas signaturer mot
Valmyndighetens certifikat (openssl). Sista utskriftsraden är "MAPP: <sökväg>" som uppdatera_2026.py läser.
Formatet: docs/superpowers/plans/2026-09-05-valnatt-2026.md, avsnittet Verifierade fakta.
"""
import argparse
import datetime as dt
import hashlib
import io
import re
import subprocess
import sys
import zipfile
from pathlib import Path
from urllib.request import Request, urlopen

ROT = Path(__file__).resolve().parents[1]
BAS_URL = "https://resultat.val.se/resultatfiler/val2026/"
GENREP_URL = "https://resultat.val.se/resultatfiler/genrep2026/"
CERT_URL = "https://resultat.val.se/keys/val-sign-crt.pem"
FILER = {"rd": ("rd", "_00_RD.zip"), "rf": ("rf", "_14_RF.zip"), "kf": ("kf", "_1480_KF.zip")}
DELAR = ("rostfordelning", "mandatfordelning", "summering")


class HamtFel(RuntimeError):
    """Hämtningen kan inte litas på: fel form på index, fel md5, fel i zip."""


def las_index(text):
    """index.md5 -> {"./p/kf/Fil.zip": md5}. Avvisar allt som inte ser ut som ett md5-index (till exempel en 404-sida)."""
    ut = {}
    for rad in text.splitlines():
        delar = rad.split()
        if len(delar) == 2 and re.fullmatch(r"[0-9a-f]{32}", delar[0]) and delar[1].startswith("./"):
            ut[delar[1]] = delar[0]
    if not ut:
        raise HamtFel("index.md5 är tom eller har fel form (svarar adressen 404 än?)")
    return ut


def valj_filer(index, tillfalle="p"):
    """-> {val: (sökväg i index, md5)} för de tre filer Majorna behöver. Väljer på katalog och suffix, inte på prefix."""
    ut = {}
    for val, (katalog, suffix) in FILER.items():
        traffar = [p for p in index if p.startswith(f"./{tillfalle}/{katalog}/") and p.endswith(suffix)]
        if len(traffar) != 1:
            raise HamtFel(f"{val}: {len(traffar)} filer i index matchar ./{tillfalle}/{katalog}/*{suffix}, väntade exakt en")
        ut[val] = (traffar[0], index[traffar[0]])
    return ut


def hamta(url, timeout=90):
    req = Request(url, headers={"User-Agent": "majposten-valgrafik/1.0 (majposten.se)"})
    with urlopen(req, timeout=timeout) as svar:
        return svar.read()


def kontrollera_md5(data, md5):
    verklig = hashlib.md5(data).hexdigest()
    if verklig != md5:
        raise HamtFel(f"md5 stämmer inte: {verklig} i filen, {md5} i index")


def packa_upp(zip_bytes, mapp):
    """Packar upp en resultatzip till mapp. -> {"rostfordelning": Path, "mandatfordelning": Path, ["summering": Path],
    "signaturer": {del: Path}}. Vägrar filnamn med sökvägar (zip slip)."""
    mapp = Path(mapp)
    mapp.mkdir(parents=True, exist_ok=True)
    ut = {"signaturer": {}}
    with zipfile.ZipFile(io.BytesIO(zip_bytes)) as z:
        for namn in z.namelist():
            if "/" in namn or "\\" in namn or namn.startswith("..") or not namn:
                raise HamtFel(f"zip-filen innehåller en sökväg, inte bara filnamn: {namn!r}")
            (mapp / namn).write_bytes(z.read(namn))
            for d in DELAR:
                if f"_{d}_" in namn or namn.endswith(f"_{d}.json") or f"_{d}_" in namn.replace("_sign.sha256", "_"):
                    if namn.endswith(".json"):
                        ut[d] = mapp / namn
                    elif namn.endswith("_sign.sha256"):
                        ut["signaturer"][d] = mapp / namn
    for d in ("rostfordelning", "mandatfordelning"):
        if d not in ut:
            raise HamtFel(f"zip-filen saknar {d}-filen: {sorted(p.name for p in mapp.iterdir())}")
    return ut


def verifiera_signatur(json_path, sign_path, nyckel_path):
    """openssl dgst -sha256 -verify <publik nyckel> -signature <fil>_sign.sha256 <fil>.json -> True vid 'Verified OK'."""
    r = subprocess.run(["openssl", "dgst", "-sha256", "-verify", str(nyckel_path), "-signature", str(sign_path), str(json_path)],
                       capture_output=True, text=True)
    return r.returncode == 0 and "Verified OK" in r.stdout


def hamta_nyckel(mapp):
    """Certifikatet från val.se -> publik nyckel (pem) i mapp. Kräver openssl."""
    mapp = Path(mapp)
    cert = mapp / "val-sign-crt.pem"
    cert.write_bytes(hamta(CERT_URL))
    pub = mapp / "val-sign-pub.pem"
    r = subprocess.run(["openssl", "x509", "-in", str(cert), "-pubkey", "-noout"], capture_output=True, text=True)
    if r.returncode != 0:
        raise HamtFel(f"kunde inte läsa certifikatet: {r.stderr.strip()}")
    pub.write_text(r.stdout, "utf-8")
    return pub


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--bas-url", default=BAS_URL)
    ap.add_argument("--genrep", action="store_true", help="hämta simuleringarna från genrep2026/ i stället")
    ap.add_argument("--tillfalle", choices=["p", "s"], default="p", help="p preliminär, s slutlig")
    ap.add_argument("--ut", default=ROT / "data" / "valnatt")
    ap.add_argument("--lokal", metavar="MAPP", help="zip-filer som redan ligger i MAPP (index.md5 där om den finns)")
    ap.add_argument("--nyckel", default=ROT / "val-sign-pub.pem", help="Valmyndighetens publika nyckel (pem)")
    ap.add_argument("--utan-signatur", action="store_true", help="hoppa över signaturkontrollen")
    ap.add_argument("--bara-om-nytt", action="store_true", help="avsluta med kod 3 om index.md5 inte ändrats sedan senaste körning")
    a = ap.parse_args()
    bas_url = GENREP_URL if a.genrep else a.bas_url
    ut = Path(a.ut)
    ut.mkdir(parents=True, exist_ok=True)
    try:
        if a.lokal:
            lokal = Path(a.lokal)
            index_filer = sorted(lokal.glob("index*.md5"))
            index = las_index(index_filer[0].read_text("utf-8")) if index_filer else None
            urval = {}
            for val, (katalog, suffix) in FILER.items():
                traffar = sorted(p for p in lokal.glob(f"*{suffix}") if ("slutlig" in p.name) == (a.tillfalle == "s"))
                if len(traffar) != 1:
                    raise HamtFel(f"{val}: {len(traffar)} zip-filer i {lokal} slutar på {suffix} för tillfälle {a.tillfalle}")
                urval[val] = (str(traffar[0]), index.get(f"./{a.tillfalle}/{katalog}/{traffar[0].name}") if index else None)
            index_text = index_filer[0].read_text("utf-8") if index_filer else ""
        else:
            index_text = hamta(bas_url + "index.md5").decode("utf-8")
            index = las_index(index_text)
            urval = valj_filer(index, a.tillfalle)
        if a.bara_om_nytt:
            senaste = ut / "senaste" / "index.md5"
            if senaste.exists() and senaste.read_text("utf-8") == index_text:
                print("Inget nytt: index.md5 är oförändrad sedan senaste körning")
                return 3
        mapp = ut / dt.datetime.now().strftime("%Y%m%d-%H%M%S")
        mapp.mkdir()
        (mapp / "index.md5").write_text(index_text, "utf-8")
        nyckel = None
        if not a.utan_signatur:
            nyckel = Path(a.nyckel)
            if not nyckel.exists():
                print(f"Hämtar Valmyndighetens certifikat till {nyckel}")
                nyckel = hamta_nyckel(nyckel.parent)
        for val, (kalla, md5) in urval.items():
            data = Path(kalla).read_bytes() if a.lokal else hamta(bas_url + kalla[2:])
            if md5:
                kontrollera_md5(data, md5)
            filer = packa_upp(data, mapp / val)
            if nyckel:
                for d, p in filer.items():
                    if d == "signaturer":
                        continue
                    if not verifiera_signatur(p, filer["signaturer"][d], nyckel):
                        raise HamtFel(f"{val}: signaturen för {p.name} stämmer inte")
            print(f"{val}: {Path(kalla).name} {len(data) / 1024:.0f} kB, md5 {'ok' if md5 else 'ej kontrollerad'}, "
                  f"signatur {'ok' if nyckel else 'ej kontrollerad'}, {len(filer) - 1} json-filer")
        lank = ut / "senaste"
        if lank.is_symlink() or lank.exists():
            lank.unlink()
        lank.symlink_to(mapp.resolve())
        print(f"MAPP: {mapp}")
        return 0
    except HamtFel as ex:
        print(f"FEL: {ex}", file=sys.stderr)
        return 1
    except OSError as ex:
        print(f"FEL: {ex}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
