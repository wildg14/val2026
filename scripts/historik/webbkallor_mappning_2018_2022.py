"""Bygger data/historik/mappning_2018_2022.csv ur Valmyndighetens fil
"Jämförelser 2018 och 2022 - valdistrikt och uppsamlingsdistrikt" (v2).

Källa (nedladdad 2026-09-03 från val.se, sidan "Rådata från val 2002-2022"):
https://val.se/download/18.162047b519a91d0533119148/1666857349837/jamforelser-2018-och-2022-valdistrikt-och-uppsamlingsdistrikt-v2.xlsx

Fliken "Fysiska valdistrikt" har kolumnerna
Kod_2022;Valdistrikt;Jämförbart;Valdistriktskod2018;Kod 2 2018;Kod 3 2018;
Valdistriktsnamn 2018;Namn 2 2018;Namn 3 2018;Län.

Avvikelse i källan: för 104 rader i riket (85 i Göteborg, 18 i Piteå, 1 i
Svalöv) står 2018-koden som tal i kolumnen Jämförbart i stället för "ja",
och ytterligare några rader har koden som text där. Dessa rader tolkas som
jämförbara (kolumnen Valdistriktskod2018 är ifylld och namnet 2018 finns).
Filen saknar procentandelar, så kolumnen procent lämnas tom.
"""
import csv
import re
import sys

import openpyxl

SCRATCH = "/private/tmp/claude-501/-Users-daniel-code-Temp/f347baf2-1af3-43b3-b36d-e80b868ede0e/scratchpad"
KALLA_V2 = SCRATCH + "/dl_webb/2022/jamforelser-2018-och-2022-valdistrikt-och-uppsamlingsdistrikt-v2.xlsx"
KALLA_V1 = SCRATCH + "/dl_webb/2022/jamforelser_2018_2022_valdistrikt_uppsamlingsdistrikt.xlsx"
UT = "/Users/daniel/code/Temp/data/historik/mappning_2018_2022.csv"
KOMMUN = "1480"
KALLA_NAMN = "jamforelser-2018-och-2022-valdistrikt-och-uppsamlingsdistrikt-v2.xlsx"


def kod(v):
    """Normalisera en valdistriktskod till åtta siffror som text, annars None."""
    if v is None:
        return None
    s = str(v).strip()
    if re.fullmatch(r"\d{7,8}", s):
        return s.zfill(8)
    return None


def namn(v):
    if v is None:
        return ""
    return re.sub(r"\s+", " ", str(v)).strip()


def las(fil):
    wb = openpyxl.load_workbook(fil, read_only=True, data_only=True)
    ws = wb["Fysiska valdistrikt"]
    rader = list(ws.iter_rows(values_only=True))
    rubrik = [str(c) for c in rader[0]]
    assert rubrik[:4] == ["Kod_2022", "Valdistrikt", "Jämförbart", "Valdistriktskod2018"], rubrik
    return rader[1:]


def tolka(rad):
    """Returnerar (kod_2022, namn_2022, jamforbart, [(kod_2018, namn_2018), ...], avvikelse)."""
    k22 = kod(rad[0])
    n22 = namn(rad[1])
    jf = rad[2]
    avvikelse = ""
    koder = []
    if isinstance(jf, str) and jf.strip().lower() in ("ja", "nej"):
        jamforbart = jf.strip().lower()
    elif kod(jf):
        jamforbart = "ja"
        avvikelse = "2018-kod i kolumnen Jämförbart i källan"
    else:
        jamforbart = "okant"
        avvikelse = "oväntat värde i Jämförbart: %r" % (jf,)
    if jamforbart == "ja":
        par = [(kod(rad[3]), namn(rad[6])), (kod(rad[4]), namn(rad[7])), (kod(rad[5]), namn(rad[8]))]
        koder = [(k, n) for k, n in par if k]
        if not koder and kod(jf):
            koder = [(kod(jf), namn(rad[6]))]
        if not koder:
            avvikelse = (avvikelse + "; " if avvikelse else "") + "jämförbart ja men ingen 2018-kod"
    return k22, n22, jamforbart, koder, avvikelse


def main():
    rader = las(KALLA_V2)
    gbg = [r for r in rader if kod(r[0]) and kod(r[0]).startswith(KOMMUN)]
    ut = []
    stat = {"ja": 0, "nej": 0, "okant": 0, "avvikelse": 0, "flera_2018": 0}
    for r in gbg:
        k22, n22, jamforbart, koder, avv = tolka(r)
        stat[jamforbart] += 1
        if avv:
            stat["avvikelse"] += 1
        if len(koder) > 1:
            stat["flera_2018"] += 1
        if koder:
            for k18, n18 in koder:
                ut.append([k18, k22, "", jamforbart, n18, n22, avv, KALLA_NAMN])
        else:
            ut.append(["", k22, "", jamforbart, "", n22, avv, KALLA_NAMN])
    ut.sort(key=lambda x: (x[1], x[0]))
    with open(UT, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f, delimiter=";", lineterminator="\n")
        w.writerow(["kod_2018", "kod_2022", "procent", "jamforbart", "namn_2018", "namn_2022", "avvikelse", "kalla_fil"])
        w.writerows(ut)
    # Jämförelse mot v1 för Göteborg
    v1 = {kod(r[0]): r for r in las(KALLA_V1) if kod(r[0]) and kod(r[0]).startswith(KOMMUN)}
    skillnad = [kod(r[0]) for r in gbg if tuple(r) != tuple(v1.get(kod(r[0]), ()))]
    print("Göteborgsrader i v2:", len(gbg), "rader skrivna:", len(ut), stat)
    print("Göteborgsrader som skiljer sig mellan v1 och v2:", len(skillnad), skillnad[:10])
    print("Skrev", UT)


if __name__ == "__main__":
    sys.exit(main())
