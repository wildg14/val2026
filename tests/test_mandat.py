from scripts.mandat import jamkade_uddatal

MAJORNA_RD_2022 = {"V": 5793, "S": 5515, "MP": 3349, "SD": 2152, "M": 1894,
                   "C": 910, "L": 886, "KD": 491, "Övriga": 318}


def test_majornas_riksdag_2022():
    m = jamkade_uddatal(MAJORNA_RD_2022, 349)
    assert m == {"V": 99, "S": 94, "MP": 57, "SD": 37, "M": 32, "C": 15, "L": 15}
    assert sum(m.values()) == 349


def test_sparr_raknas_pa_alla_giltiga_roster():
    # KD har 491/21308 = 2,3 % och hamnar utanför. Övriga räknas i nämnaren men får aldrig mandat.
    m = jamkade_uddatal(MAJORNA_RD_2022, 349)
    assert "KD" not in m and "Övriga" not in m


def test_forsta_delningstal():
    # B:s första kvot är 6 (delningstal 1,0) eller 5 (1,2). A:s nionde och tionde kvot är 5,88 och 5,26.
    r = {"A": 100, "B": 6}
    assert jamkade_uddatal(r, 10, sparr=0, forsta_delningstal=1.0) == {"A": 9, "B": 1}
    assert jamkade_uddatal(r, 10, sparr=0, forsta_delningstal=1.2) == {"A": 10}
