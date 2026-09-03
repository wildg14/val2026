"""Jämkade uddatalsmetoden (modified Sainte-Laguë) med procentspärr.

Används för räkneexemplet "Om Majorna bestämde": Majornas riksdagsröster
fördelade på 349 mandat som om Majorna vore hela landet.
"""


def jamkade_uddatal(roster, mandat, sparr=0.04, forsta_delningstal=1.2, exkludera=("Övriga",)):
    """Fördela `mandat` platser på partierna i `roster` (parti -> antal röster).

    Spärren räknas på samtliga giltiga röster, inklusive partier i `exkludera`,
    som aldrig själva får mandat. Returnerar bara partier som fått minst ett mandat.
    """
    totalt = sum(roster.values())
    kandidater = {p: r for p, r in roster.items()
                  if p not in exkludera and totalt and r / totalt >= sparr}
    fordelning = {p: 0 for p in kandidater}

    def kvot(p):
        n = fordelning[p]
        return kandidater[p] / (forsta_delningstal if n == 0 else 2 * n + 1)

    for _ in range(mandat):
        if not kandidater:
            break
        fordelning[max(kandidater, key=kvot)] += 1
    return {p: n for p, n in fordelning.items() if n > 0}
