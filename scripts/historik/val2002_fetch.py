#!/usr/bin/env python3
"""Hamtar 2002 ars slutresultat for Goteborg (1480) fran historik.val.se.

Sparar varje sida oforandrad (ISO-8859-1) i DL_DIR sa att tolkningen kan goras om
utan natverk. Filnamn: <val><omrade>_<sokvag med _ i stallet for />.html,
till exempel 14R_1480_14801301.html for valdistrikt 14801301 i riksdagsvalet.

Kors: python val2002_fetch.py            (hamtar det som saknas)
      python val2002_fetch.py --force    (hamtar om allt)
"""
import os
import re
import subprocess
import sys
import time

BASE = "https://historik.val.se/val/val_02/slutresultat"
DL_DIR = "/private/tmp/claude-501/-Users-daniel-code-Temp/f347baf2-1af3-43b3-b36d-e80b868ede0e/scratchpad/dl2002"
VAL = ["R", "K", "L"]          # riksdag, kommunfullmaktige, landsting
KOMMUN = "1480"                # Goteborg
VALKRETSAR = ["148001", "148002", "148003", "148004"]
TIMEOUT = 60
PAUSE = 0.2                    # sekunder mellan anrop, for att inte belasta servern

# Sidor pa riks-, lans- och kommunniva (sokvag relativt BASE -> lokalt filnamn)
TOP_PAGES = {
    "00R/00-text.html": "00R_00-text.html",
    "00K/00-text.html": "00K_00-text.html",
    "00L/00-text.html": "00L_00-text.html",
    "00R/00.html": "00R_00.html",
    "14R/14.html": "14R_14.html",
    "14K/14.html": "14K_14.html",
    "14L/14.html": "14L_14.html",
    "14R/1416KR.html": "14R_1416KR.html",
    "14K/1416KR.html": "14K_1416KR.html",
    "14L/1401KL.html": "14L_1401KL.html",
    "14R/1480/R-1480-16.html": "14R_1480_R-1480-16.html",
    "14L/1480/L-1480-01.html": "14L_1480_L-1480-01.html",
    "14K/1480/K-1480-01.html": "14K_1480_K-1480-01.html",
    "14K/1480/K-1480-02.html": "14K_1480_K-1480-02.html",
    "14K/1480/K-1480-03.html": "14K_1480_K-1480-03.html",
    "14K/1480/K-1480-04.html": "14K_1480_K-1480-04.html",
    "00K/00.html": "00K_00.html",
    "00L/00.html": "00L_00.html",
}


def fetch(rel, fname, force=False):
    path = os.path.join(DL_DIR, fname)
    if not force and os.path.exists(path) and os.path.getsize(path) > 300:
        return "cached"
    url = f"{BASE}/{rel}"
    r = subprocess.run(["curl", "-s", "-m", str(TIMEOUT), "-w", "%{http_code}", "-o", path, url],
                       capture_output=True, text=True)
    time.sleep(PAUSE)
    code = r.stdout.strip()
    if code != "200":
        # behall inte 404-sidor
        if os.path.exists(path):
            os.remove(path)
    return code


def distrikt_codes(val):
    """Valdistriktskoder ur lanklistorna pa valkretssidorna."""
    codes = {}
    for vk in VALKRETSAR:
        fname = f"14{val}_{KOMMUN}_{vk}.html"
        with open(os.path.join(DL_DIR, fname), encoding="iso-8859-1") as f:
            t = f.read()
        for m in re.finditer(r'HREF="/val/val_02/slutresultat/14%s/%s/(\d{8})\.html">([^<]*)</A>' % (val, KOMMUN), t):
            codes[m.group(1)] = re.sub(r"\s+", " ", m.group(2)).strip()
    return codes


def main():
    force = "--force" in sys.argv
    os.makedirs(DL_DIR, exist_ok=True)
    log = []
    for rel, fname in TOP_PAGES.items():
        log.append((fname, fetch(rel, fname, force)))
    for val in VAL:
        for fname, rel in [(f"14{val}_{KOMMUN}_{KOMMUN}.html", f"14{val}/{KOMMUN}/{KOMMUN}.html"),
                           (f"14{val}_{KOMMUN}_{KOMMUN}-text.html", f"14{val}/{KOMMUN}/{KOMMUN}-text.html")]:
            log.append((fname, fetch(rel, fname, force)))
        for vk in VALKRETSAR:
            log.append((f"14{val}_{KOMMUN}_{vk}.html", fetch(f"14{val}/{KOMMUN}/{vk}.html", f"14{val}_{KOMMUN}_{vk}.html", force)))
        codes = distrikt_codes(val)
        n_ok = 0
        for code in sorted(codes):
            fname = f"14{val}_{KOMMUN}_{code}.html"
            st = fetch(f"14{val}/{KOMMUN}/{code}.html", fname, force)
            log.append((fname, st))
            if st in ("200", "cached"):
                n_ok += 1
        print(f"{val}: {len(codes)} distrikt i lanklistorna, {n_ok} sidor hamtade eller cachade", flush=True)
    bad = [(f, s) for f, s in log if s not in ("200", "cached")]
    print(f"{len(log)} sidor, {len(bad)} misslyckade")
    for f, s in bad:
        print("  MISSLYCKAD", f, s)


if __name__ == "__main__":
    main()
