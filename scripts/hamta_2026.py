#!/usr/bin/env python3
"""Hämtar Valmyndighetens resultatfiler för 2026 och packar upp dem till data/valnatt/<tidsstämpel>/.

    .venv/bin/python scripts/hamta_2026.py                       # preliminär räkning från val2026/
    .venv/bin/python scripts/hamta_2026.py --tillfalle s         # slutlig räkning
    .venv/bin/python scripts/hamta_2026.py --genrep              # simuleringarna, samma struktur, test: true
    .venv/bin/python scripts/hamta_2026.py --lokal MAPP          # zip-filer som redan ligger på disk
    .venv/bin/python scripts/hamta_2026.py --bara-om-nytt        # avsluta med kod 3 när de tre filerna är oförändrade

Tre filer hämtas: riksdagen för hela landet (_00_RD), regionvalet för Västra Götaland (_14_RF) och
kommunvalet för Göteborg (_1480_KF). md5 kontrolleras mot index.md5 och JSON-filernas signaturer mot
Valmyndighetens certifikat (openssl). Sista utskriftsraden är "MAPP: <sökväg>" som uppdatera_2026.py läser.

Servern skriver om resultatfilerna löpande under valkvällen. Om md5 inte stämmer för någon av de tre
filerna, eller om index inte längre pekar ut exakt en fil per val, hämtas index och filerna om en gång
till innan körningen avbryts (bara på nätvägen, inte med --lokal).

--bara-om-nytt jämför bara md5 för de tre valda filerna mot föregående körnings
data/valnatt/senaste/index.md5, inte hela landets index (som ändras varje minut oavsett Majorna).
Bara när alla tre är oförändrade avslutas körningen med kod 3 utan att något skrivs.

data/valnatt/senaste är en relativ symlänk (pekar på tidsstämpelmappens namn, inte en absolut sökväg)
och byts atomärt vid varje lyckad körning.

Formatet: docs/superpowers/plans/2026-09-05-valnatt-2026.md, avsnittet Verifierade fakta.
"""
import argparse
import datetime as dt
import hashlib
import http.client
import io
import os
import re
import subprocess
import sys
import time
import zipfile
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

ROT = Path(__file__).resolve().parents[1]
BAS_URL = "https://resultat.val.se/resultatfiler/val2026/"
GENREP_URL = "https://resultat.val.se/resultatfiler/genrep2026/"
CERT_URL = "https://resultat.val.se/keys/val-sign-crt.pem"
FILER = {"rd": ("rd", "_00_RD.zip"), "rf": ("rf", "_14_RF.zip"), "kf": ("kf", "_1480_KF.zip")}
DELAR = ("rostfordelning", "mandatfordelning", "summering")
STORLEKSGRANS = 200 * 1024 * 1024
PAUS_SEKUNDER = 3  # väntetid före det enda återförsöket, patchbar i tester


class HamtFel(RuntimeError):
    """Hämtningen kan inte litas på: fel form på index, fel md5, fel i zip."""


class AndradUnderHamtning(HamtFel):
    """Filerna ändrades under hämtningen (fel md5, eller fel antal träffar i index):
    servern skriver om resultatfilerna löpande, så detta är värt precis ett återförsök.
    Andra HamtFel (404, nätfel, trasig zip) är inte värda att försöka igen."""


def las_index(text):
    """index.md5 -> {"./p/kf/Fil.zip": md5}. Tar text eller bytes (utf-8-sig); ogiltig teckenkodning ger HamtFel,
    inte UnicodeDecodeError. Avvisar allt som inte ser ut som ett md5-index (till exempel en 404-sida)."""
    if isinstance(text, bytes):
        try:
            text = text.decode("utf-8-sig")
        except UnicodeDecodeError as ex:
            raise HamtFel(f"index.md5 går inte att avkoda som utf-8: {ex}") from ex
    text = text.lstrip("﻿")  # BOM, om den inte redan togs bort av avkodningen
    ut = {}
    for rad in text.splitlines():
        delar = rad.split()
        if len(delar) == 2 and re.fullmatch(r"[0-9a-f]{32}", delar[0]) and delar[1].startswith("./"):
            ut[delar[1]] = delar[0]
    if not ut:
        raise HamtFel("index.md5 är tom eller har fel form (svarar adressen 404 än?)")
    return ut


def valj_filer(index, tillfalle="p"):
    """-> {val: (sökväg i index, md5)} för de tre filer Majorna behöver. Väljer på katalog och suffix, inte på prefix.
    Fel antal träffar räknas som att filerna ändrats under hämtningen (AndradUnderHamtning), värt ett återförsök."""
    ut = {}
    for val, (katalog, suffix) in FILER.items():
        traffar = [p for p in index if p.startswith(f"./{tillfalle}/{katalog}/") and p.endswith(suffix)]
        if len(traffar) != 1:
            raise AndradUnderHamtning(
                f"{val}: {len(traffar)} filer i index matchar ./{tillfalle}/{katalog}/*{suffix}, väntade exakt en")
        ut[val] = (traffar[0], index[traffar[0]])
    return ut


def hamta_urval(bas_url, tillfalle):
    """Hämtar index.md5 och väljer ut de tre filerna för tillfälle. -> (index_text, urval)."""
    index_text = hamta(bas_url + "index.md5").decode("utf-8-sig")
    index = las_index(index_text)
    return index_text, valj_filer(index, tillfalle)


def hamta_och_kontrollera(bas_url, urval):
    """Hämtar de tre zip-filerna som urval pekar ut och kontrollerar md5 mot samma urval. -> {val: bytes}."""
    data = {}
    for val, (kalla, md5) in urval.items():
        innehall = hamta(bas_url + kalla[2:])
        if md5:
            kontrollera_md5(innehall, md5)
        data[val] = innehall
    return data


def valj_lokala_filer(lokal, tillfalle):
    """Zip-filer som redan ligger i lokal (ingen katalogstruktur krävs).
    Provar index*.md5 i sorterad ordning och tar den första som går att tolka; går ingen att tolka är index None.
    -> (index_text, index eller None, {val: (sökväg, md5 eller None)})."""
    lokal = Path(lokal)
    index_text, index = "", None
    for kandidat in sorted(lokal.glob("index*.md5")):
        try:
            text = kandidat.read_text("utf-8-sig")
            index = las_index(text)
        except (HamtFel, UnicodeDecodeError):
            continue
        index_text = text
        break
    urval = {}
    for val, (katalog, suffix) in FILER.items():
        traffar = sorted(p for p in lokal.glob(f"*{suffix}") if ("slutlig" in p.name.lower()) == (tillfalle == "s"))
        if len(traffar) != 1:
            raise HamtFel(f"{val}: {len(traffar)} zip-filer i {lokal} slutar på {suffix} för tillfälle {tillfalle}")
        md5 = None
        if index is not None:
            md5 = index.get(f"./{tillfalle}/{katalog}/{traffar[0].name}")
            if md5 is None:
                print(f"VARNING: index listar inte {traffar[0].name}, md5 ej kontrollerad", file=sys.stderr)
        urval[val] = (str(traffar[0]), md5)
    return index_text, index, urval


def ar_oforandrat(ut, tillfalle, urval):
    """True om alla tre filerna i urval har samma md5 som i föregående körnings data/valnatt/senaste/index.md5.
    Saknat eller trasigt senaste-index räknas som "nytt" (False), liksom en okänd md5 i det nya urvalet."""
    try:
        text = (Path(ut) / "senaste" / "index.md5").read_text("utf-8-sig")
        gammalt_urval = valj_filer(las_index(text), tillfalle)
    except (OSError, HamtFel):
        return False
    for val, (_, md5) in urval.items():
        if md5 is None or gammalt_urval.get(val, (None, None))[1] != md5:
            return False
    return True


def hamta(url, timeout=30):
    req = Request(url, headers={"User-Agent": "majposten-valgrafik/1.0 (majposten.se)"})
    try:
        with urlopen(req, timeout=timeout) as svar:
            return svar.read()
    except HTTPError as ex:
        if ex.code == 404 and url.endswith("index.md5"):
            raise HamtFel(f"{url} svarar 404: resultatfilerna publiceras först på valkvällen") from ex
        raise HamtFel(f"{url}: {ex}") from ex
    except URLError as ex:
        raise HamtFel(f"{url}: {ex.reason}") from ex
    except http.client.IncompleteRead as ex:
        raise HamtFel(f"{url}: hämtningen bröts i förtid, för lite data kom fram") from ex


def kontrollera_md5(data, md5):
    """Höjer AndradUnderHamtning vid fel md5: servern skriver om filerna löpande, värt ett återförsök."""
    verklig = hashlib.md5(data).hexdigest()
    if verklig != md5:
        raise AndradUnderHamtning(f"md5 stämmer inte: {verklig} i filen, {md5} i index")


def packa_upp(zip_bytes, mapp):
    """Packar upp en resultatzip till mapp. -> {"rostfordelning": Path, "mandatfordelning": Path, ["summering": Path],
    "signaturer": {del: Path}}. Vägrar filnamn med sökvägar (zip slip) och filer över 200 MB. Validerar hela
    namnlistan innan något skrivs till disk."""
    mapp = Path(mapp)
    try:
        with zipfile.ZipFile(io.BytesIO(zip_bytes)) as z:
            infolist = z.infolist()
            for info in infolist:
                namn = info.filename
                if "/" in namn or "\\" in namn or namn.startswith("..") or not namn:
                    raise HamtFel(f"zip-filen innehåller en sökväg, inte bara filnamn: {namn!r}")
                if info.file_size > STORLEKSGRANS:
                    raise HamtFel(f"{namn}: {info.file_size / 1024 / 1024:.0f} MB, större än gränsen 200 MB")
            mapp.mkdir(parents=True, exist_ok=True)
            ut = {"signaturer": {}}
            for info in infolist:
                namn = info.filename
                (mapp / namn).write_bytes(z.read(namn))
                for d in DELAR:
                    if f"_{d}_" in namn or namn.endswith(f"_{d}.json"):
                        if namn.endswith(".json"):
                            ut[d] = mapp / namn
                        elif namn.endswith("_sign.sha256"):
                            ut["signaturer"][d] = mapp / namn
    except zipfile.BadZipFile as ex:
        raise HamtFel(f"filen är inte en giltig zip-fil: {ex}") from ex
    for d in ("rostfordelning", "mandatfordelning"):
        if d not in ut:
            raise HamtFel(f"zip-filen saknar {d}-filen: {sorted(p.name for p in mapp.iterdir())}")
    return ut


def verifiera_signatur(json_path, sign_path, nyckel_path):
    """openssl dgst -sha256 -verify <publik nyckel> -signature <fil>_sign.sha256 <fil>.json -> True vid 'Verified OK'."""
    r = subprocess.run(["openssl", "dgst", "-sha256", "-verify", str(nyckel_path), "-signature", str(sign_path), str(json_path)],
                       capture_output=True, text=True)
    return r.returncode == 0 and "Verified OK" in r.stdout


def hamta_nyckel(nyckel_path):
    """Certifikatet från val.se -> publik nyckel (pem) skriven till exakt nyckel_path.
    Certifikatet läggs bredvid i samma katalog som val-sign-crt.pem. Kräver openssl."""
    nyckel_path = Path(nyckel_path)
    cert = nyckel_path.parent / "val-sign-crt.pem"
    cert.write_bytes(hamta(CERT_URL))
    r = subprocess.run(["openssl", "x509", "-in", str(cert), "-pubkey", "-noout"], capture_output=True, text=True)
    if r.returncode != 0:
        raise HamtFel(f"kunde inte läsa certifikatet: {r.stderr.strip()}")
    nyckel_path.write_text(r.stdout, "utf-8")
    return nyckel_path


def _kontrollera_lank_plats(lank):
    """Höjer HamtFel om lank finns och är en riktig katalog i stället för en länk. Anropas både tidigt i
    main (innan hämtning, så felet kommer snabbt) och i peka_senaste (som en sista vakt före bytet)."""
    if lank.exists() and not lank.is_symlink():
        raise HamtFel(f"{lank} är en katalog, inte en länk; flytta undan den")


def peka_senaste(ut, mapp):
    """Byter symlänken ut/senaste till att peka på mapp, atomärt (tempfil plus os.replace) och relativt (mapp.name).
    Höjer HamtFel om ut/senaste finns och är en riktig katalog i stället för en länk."""
    ut = Path(ut)
    mapp = Path(mapp)
    lank = ut / "senaste"
    _kontrollera_lank_plats(lank)
    tmp = ut / "senaste.tmp"
    if tmp.exists() or tmp.is_symlink():
        tmp.unlink()
    tmp.symlink_to(mapp.name)
    os.replace(tmp, lank)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--bas-url", default=BAS_URL)
    ap.add_argument("--genrep", action="store_true", help="hämta simuleringarna från genrep2026/ i stället")
    ap.add_argument("--tillfalle", choices=["p", "s"], default="p", help="p preliminär, s slutlig")
    ap.add_argument("--ut", default=ROT / "data" / "valnatt")
    ap.add_argument("--lokal", metavar="MAPP", help="zip-filer som redan ligger i MAPP (index.md5 där om den finns)")
    ap.add_argument("--nyckel", default=ROT / "val-sign-pub.pem", help="Valmyndighetens publika nyckel (pem)")
    ap.add_argument("--utan-signatur", action="store_true", help="hoppa över signaturkontrollen")
    ap.add_argument("--bara-om-nytt", action="store_true",
                     help="avsluta med kod 3 om de tre valda filerna har samma md5 som senaste körning")
    a = ap.parse_args()
    bas_url = GENREP_URL if a.genrep else a.bas_url
    ut = Path(a.ut)
    ut.mkdir(parents=True, exist_ok=True)
    try:
        _kontrollera_lank_plats(ut / "senaste")  # tidigt, så en riktig katalog upptäcks innan hämtningen
        zip_data = None
        if a.lokal:
            index_text, _, urval = valj_lokala_filer(Path(a.lokal), a.tillfalle)
            if a.bara_om_nytt and ar_oforandrat(ut, a.tillfalle, urval):
                print("Inget nytt: de tre filerna har samma md5 som senaste körning")
                return 3
        else:
            index_text = urval = None
            for forsok in range(2):
                try:
                    index_text, urval = hamta_urval(bas_url, a.tillfalle)
                    if a.bara_om_nytt and ar_oforandrat(ut, a.tillfalle, urval):
                        print("Inget nytt: de tre filerna har samma md5 som senaste körning")
                        return 3
                    zip_data = hamta_och_kontrollera(bas_url, urval)
                    break
                except AndradUnderHamtning:
                    if forsok == 0:
                        print("Filerna ändrades under hämtningen, försöker igen")
                        time.sleep(PAUS_SEKUNDER)
                        continue
                    raise

        nyckel = None
        if not a.utan_signatur:
            nyckel = Path(a.nyckel)
            if not nyckel.exists():
                print(f"Hämtar Valmyndighetens certifikat till {nyckel}")
                nyckel = hamta_nyckel(nyckel)

        bas = dt.datetime.now().strftime("%Y%m%d-%H%M%S")
        mapp = ut / bas
        n = 2
        while mapp.exists():
            mapp = ut / f"{bas}-{n}"
            n += 1
        mapp.mkdir()
        (mapp / "index.md5").write_text(index_text, "utf-8")

        for val, (kalla, md5) in urval.items():
            if a.lokal:
                data = Path(kalla).read_bytes()
                if md5:
                    kontrollera_md5(data, md5)
            else:
                data = zip_data[val]
            filer = packa_upp(data, mapp / val)
            if nyckel:
                for d, p in filer.items():
                    if d == "signaturer":
                        continue
                    sign = filer["signaturer"].get(d)
                    if sign is None:
                        raise HamtFel(f"{val}: signatur saknas för {p.name}")
                    if not verifiera_signatur(p, sign, nyckel):
                        raise HamtFel(f"{val}: signaturen för {p.name} stämmer inte")
            print(f"{val}: {Path(kalla).name} {len(data) / 1024:.0f} kB, md5 {'ok' if md5 else 'ej kontrollerad'}, "
                  f"signatur {'ok' if nyckel else 'ej kontrollerad'}, {len(filer) - 1} json-filer")

        peka_senaste(ut, mapp)
        print(f"MAPP: {mapp}")
        return 0
    except HamtFel as ex:
        print(f"FEL: {ex}", file=sys.stderr)
        return 1
    except OSError as ex:
        print(f"FEL: {ex}", file=sys.stderr)
        return 2
    except Exception as ex:
        print(f"FEL: oväntat fel: {type(ex).__name__}: {ex}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
