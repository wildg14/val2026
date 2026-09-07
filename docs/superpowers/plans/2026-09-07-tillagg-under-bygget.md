# Tillägg under bygget: beslut som ändrade planerna för valnatten 2026 och historiksektionen

Skrivet 2026-09-05 till 2026-09-07 av kontrollern i den session som byggde `docs/superpowers/plans/2026-09-05-valnatt-2026.md` (tolv tasks, klar) och började `docs/superpowers/plans/2026-09-05-historik-sektion.md` (Task 1 till 5 klara, Task 6 byggd men bara spec-granskad). Varje task byggdes av en implementerare och granskades i två steg (spec och kvalitet); när granskningen hittade fel i planen fattade kontrollern ett beslut och skrev ner det här. Dokumenten låg under bygget i sessionens scratchpad och gällde före plantexten där de skiljer sig. Planfilerna är oförändrade och är historik; det här dokumentet och `docs/HANDOVER.md` är källan till vad som faktiskt byggdes.

Ordningen nedan följer bygget: först valnattsplanens sju dokument, sedan historikplanens.

---

## Tillägg till valnattsplanen, beslutat av kontrollern 2026-09-05 efter kvalitetsgranskningen av Task 1

Bakgrund: Valmyndighetens preliminära filer listar bara rapportpartierna i `partiRoster`; övriga partiers röster ligger i `rosterOvrigaPartier`. I genrep-filerna saknas K (Kommunistiska Partiet) i kommunvalet och FI i regionvalet, trots att båda är nyckelpartier i sidans schema. Planens kod fyllde alla nyckelpartier med 0, vilket ger påhittade nollor och falska förändringstal (K -1,0 procentenheter). Den slutliga filen listar alla partier, så felet gäller valnatten.

Regel: **ett nyckelparti som inte förekommer i filens `partiRoster` saknas i datan.** Det står varken som 0 eller markeras; det finns inte i `roster`-ordboken för det distriktet eller aggregatet, och dess röster ingår i Övriga. Sidan hanterar redan partiuppsättningar som skiljer sig per val (`partierIVal` läser nycklarna ur `aggregat.majorna`, distriktsvärden läses med `|| 0` eller genom nyckliteration), så ett parti som inte redovisas syns helt enkelt inte förrän filen listar det.

Konsekvenser per task:
- Task 1 (rättat i uppföljning): `_mappa_partiroster` fyller bara partier som förekommer i `partiRoster` (plus Övriga). Testet `set(d["roster"]) == {...alla nyckelpartier...}` blir `{"V", "S", "D", OVRIGA}` och `"K" not in d["roster"]`.
- Task 2: `_omrade` ger `andel` bara för redovisade partier. Testet `agg["riket"]["andel"]["V"] == 0.0` (V saknas i det syntetiska objektet) blir `"V" not in agg["riket"]["andel"]`. Genrep-facit `agg["goteborg"]["andel"]["D"] == 0.0` gäller bara om DEM faktiskt står i kommunfilens valomrade-partiRoster; kontrollera mot filen.
- Task 5: `schema._diff` räknar bara partier som finns i både ny och bas. Om partiuppsättningen (utom Övriga) skiljer sig mellan ny och bas för ett distrikt eller område, utelämnas Övriga också ur diffen, eftersom Övrigas sammansättning då skiljer sig. Ett test för det.
- Task 6: `fyll` kopierar `post["roster"]` som den är (ingen ändring), så distriktets ordbok saknar partiet. Aggregaten från `aggregat_2026` likaså.
- Task 9: kontrollera att `divergens()` (Majorna mot Sverige, raden med `omr.post.andel[p]`) hoppar över partier som saknas i jämförelseområdets `andel` i stället för att ge NaN.
- Task 11: i raden "Sedan 2022" ska ett parti utan tal i swingfilen hoppas över, inte skrivas som `+0,0` (planens kod har `post[val][a.p] || 0`).
- Task 12 (README, Dataschema): en mening om att partier som inte redovisas i den preliminära filen saknas i datan tills den slutliga filen listar dem.

Precisering efter omgranskningen av Task 1 (2026-09-05): premissen "den slutliga filen listar alla partier" håller inte mot genrepets slutliga kommunfil. Där listas partier med röster individuellt per distrikt (även små som SKP, MED), medan partier med noll röster i distriktet utelämnas helt (D, FI och K saknas i alla 397 distrikt i genrepets slutfil, och rosterOvrigaPartier är 0). Regeln "saknas i filen = saknas i datan" är därför rätt för båda filerna, men betydelsen skiljer sig: i den preliminära filen betyder det "inte rapportparti", i den slutliga "inga röster i distriktet". README (Task 12) ska formulera det så, inte som "tills den slutliga filen listar dem".

Status: Task 1 rättad i b0a4c21 och godkänd i omgranskning. Rest till Task 2: lägg ett regressionstest mot RF-genrepfilen (FI saknas i alla RF-poster).

---

## Tillägg till valnattsplanen, beslutat av kontrollern 2026-09-05 efter kvalitetsgranskningen av Task 2

### 1. Valdeltagande i aggregaten räknas mot röstberättigade i räknade distrikt (rättat i Task 2-uppföljning)

Planens `_omrade` tog `antalRostberattigade` (hela områdets väljarkår) som nämnare medan `totaltAntalRoster` bara är rösterna i räknade distrikt. Tidigt på valkvällen gav det t.ex. 12,5 procent i stället för 83 för riket. Valmyndighetens filer har rätt nämnare i samma objekt: `antalRostberattigadeIRaknadeValdistrikt` (finns i mandatfördelningens `valomrade` och i summeringens `kommuner[]`, formatbeskrivningarna prel-mandatfordelning.md rad 40 och prel-summering-rd-rf.md rad 36; i genrep lika med totalen eftersom allt är räknat). Regel: `rostberattigade = antalRostberattigadeIRaknadeValdistrikt`, med `antalRostberattigade` som reserv när fältet saknas. Planens inledning ("Aggregat") nämner inte fältet; det här dokumentet gäller.

### 2. Fel i jämförelseaggregaten får inte stoppa distriktsimporten (gäller Task 6)

Planens `las_valnattsmapp` i Task 6 gör `fel(...)` (sys.exit 1) när `aggregat_2026` höjer `FormatFel` eller `SummaFel`, t.ex. om summeringsfilen inte listar kommun 1480 eller en aggregatsumma inte går ihop under Valmyndighetens pågående skrivning. Aggregaten används bara som jämförelsemarkörer; distrikten ligger i en annan fil. Regel i Task 6: fånga `(valnatt.FormatFel, SummaFel)` runt `aggregat_2026` och `riksdag_verklig`, ge `varning(f"{val}: jämförelseaggregat kunde inte läsas: {ex}")` och lämna aggregatet tomt för det valet. xlsx-vägen gör redan så (utelämnar område som saknas).

### 3. Delvis räknat jämförelseområde ska synas i sidan (gäller Task 10)

Riksdagsfilens `valomrade` växer under kvällen (`antalValdistriktRaknade` mot `antalValdistriktSomSkaRaknas`), och de första distrikten är systematiskt små och lantliga. `_omrade` levererar `antal_distrikt` och `totalt_distrikt` i aggregatet. Regler för sidan (Task 10, samma JS-fil som toppsvaret):
- Toppsvarets mening "X % röstade, mot Y % i riket" tar bara med riket när jämförelseområdet är färdigräknat: `antal_distrikt` saknas (2022-data) eller `antal_distrikt >= totalt_distrikt`. Annars bara "X % röstade."
- Sektionen "Majorna mot Sverige" (`divergens`) får en dämpad mening under staplarna när jämförelseområdet är delvis räknat: "Riket: 1 342 av 6 626 distrikt räknade." (namnet ur `post.namn`, för kommunvalet "Göteborg"). Ingen mening när området är färdigräknat eller när nycklarna saknas.

### 4. Småsaker rättade i Task 2-uppföljningen
Typkontroll av rotobjekt i `las_valomrade` och `las_kommun` (FormatFel), `val` valideras i `_omrade`, `valtyp` i mandat- och summeringsfilernas rot kontrolleras mot `val` när fältet finns, `giltiga + ogiltiga == rostande` kontrolleras i `_omrade` (SummaFel, blir varning i Task 6 enligt punkt 2), `if v is not None` i `aggregat_2026`, docstring om formen, tester för giltiga 0, saknad kommun, null röstberättigade.

### 5. Efter omgranskningen av Task 2 (godkänd i 5ddcbe9)
Rest till Task 3 (samma fil): i `_omrade` ska vakten för ogiltiga vara `rem = (rf.get("rosterEjPaverkaMandat") or {})` följt av `if rem.get("antalRoster") is not None:` (så att `{}`, `null` och en lista inte ger fel SummaFel eller AttributeError); `valtyp` som är null i roten ska behandlas som saknat fält; de två valtyp-blocken i `las_valomrade` och `las_kommun` blir en hjälpfunktion `_kontrollera_valtyp(obj, val)`.
Precisering av punkt 2 för Task 6: fånga `Exception` (inte bara FormatFel och SummaFel) runt `aggregat_2026` och `riksdag_verklig`, eftersom en oväntad form i aggregatfilen kan ge AttributeError eller TypeError, och aggregaten aldrig får stoppa distriktsimporten. Varningen ska innehålla undantagets typ och text.

### 6. Efter kvalitetsgranskningen av Task 3 (f852425)
Rättas i Task 3-uppföljning: `riksdag_verklig` kontrollerar rot (dict) och valtyp "rd" via `_kontrollera_valtyp`; `partiLista` som inte är lista ger `{}`; reservkoden är `parti_2026(p) or partiforkortning or partibeteckning or partikod` så att koden aldrig blir tom; `las_rostfordelning` får samma vakt för `rosterEjPaverkaMandat` som `_omrade` (icke-dict ger FormatFel, inte AttributeError); test med icke-tom lista i `rosterEjPaverkaMandat`.

Gäller Task 6 (`las_valnattsmapp`, efter `verklig = valnatt.riksdag_verklig(mandat[0])`): `varning` när `verklig` är icke-tom och summan inte är 349; `varning` per partikod i `verklig` som inte finns i `NYCKELPARTIER["rd"]` (ett nytt parti i riksdagen kan aldrig finnas i `riksdag_majorna`, och halvcirkeln får då prickar utan namn). Aldrig `fel` för mandaten.

Gäller Task 10 (planlucka): halvcirkeln "Om Majorna bestämde" visar från Task 6 en preliminär riksdagsfördelning under etiketten "Riksdagen 2026" och ingressen "jämfört med den verkliga riksdagen" (valgrafik.js rad cirka 30, 380, 409). När `data().meta.status === "preliminar"` och `riksdag_verklig` är icke-tom: en dämpad mening under halvcirkeln, "Preliminär fördelning, riket: X av Y distrikt räknade." (ur `aggregat.riket.rd.antal_distrikt` och `totalt_distrikt`; utan talen om nycklarna saknas, då bara "Preliminär mandatfördelning."), och ingressens "den verkliga riksdagen" blir "riksdagen" när status är preliminär. Etiketten "Riksdagen 2026" behålls.

Gäller Task 12: README-punkten under Vanliga fel ("Halvcirkeln visar bara 'Majornas riksdag' 2026 - väntat. Riksdagens verkliga fördelning är inte känd på valnatten") stryks eller skrivs om: mandaten läses ur mandatfördelningsfilen och är preliminära tills den slutliga räkningen. Överlämningen ska nämna att `valtyp: null` i roten godtas som saknat fält (planbeslut) och att den preliminära riksdagsfördelningen ändras under kvällen och efter onsdagsräkningen.

### 7. Efter omgranskningen av Task 3 (ea0c462, godkänd)
Restlista, görs som egen commit av Task 4-agenten innan Task 4: i `riksdag_verklig` hoppa över (`continue`) poster där koden blir tom; `valomrade` och `mandatfordelning` som inte är dict ger FormatFel (samma som `las_valomrade`); `@finns`-regressionstest att `riksdag_verklig(MANDAT_RF)` och `riksdag_verklig(MANDAT_KF)` höjer FormatFel. Observation till överlämningen: `_kontrollera_valtyp` godtar saknat eller null `valtyp`, så vakten är bara så stark som fältets närvaro (alla genrep-filer har fältet).

---

## Tillägg till valnattsplanen, beslutat av kontrollern 2026-09-05 efter kvalitetsgranskningen av Task 4

### Ändrad semantik i `scripts/hamta_2026.py` (rättas i Task 4-uppföljning)
- `--bara-om-nytt` jämför md5-summorna för de tre valda filerna (ur `valj_filer(index, tillfalle)`) mot samma tre i föregående körnings `senaste/index.md5`, inte hela indexet (hela landets index ändras varje minut, så flaggan var verkningslös). Kod 3 när alla tre är oförändrade.
- Ett återförsök: om md5 inte stämmer för en fil, eller om `valj_filer` inte hittar exakt en träff, hämtas index på nytt och hela urvalet görs om en gång innan körningen avbryts (servern skriver om filerna löpande under kvällen).
- `senaste` byts atomärt (tillfällig länk plus `os.replace`), relativt (`mapp.name`); en riktig katalog på platsen ger ett tydligt `HamtFel`, ingen tyst radering.
- Saknad signaturfil ger `HamtFel`, inte `KeyError`. Nyckeln hämtas före tidsstämpelmappen skapas. Index läses med `utf-8-sig`. Nätfel nämner adressen; 404 på `index.md5` ger ett eget meddelande om att filerna publiceras på valkvällen. Timeout 30 s. `--lokal` hoppar över indexfiler som inte går att tolka. Storleksgräns per fil i zip.
- Hjälpfunktioner `valj_lokala_filer(lokal, tillfalle)` och `peka_senaste(ut, mapp)` bryts ut ur `main()` och testas.

### Gäller Task 6 (`--hamta`-vägen i `scripts/uppdatera_2026.py`)
Planens kod bygger `sys.argv` ofullständigt: `--ut` skickas inte (hamta skriver då alltid till `ROT/data/valnatt` medan uppdatera läser `Path(a.ut)/valnatt/senaste`), och `--bara-om-nytt` skickas aldrig (grenen `if kod == 3` är död). Regel: argv byggs fullständigt: `["--tillfalle", a.tillfalle, "--ut", str(Path(a.ut) / "valnatt"), "--bara-om-nytt"]` plus `["--genrep"]` när `a.genrep`. Kod 3 ger utskriften "Inget nytt att läsa in." och returkod 3 utan att något skrivs. Vill man tvinga en omläsning av samma filer används `--valnatt-mapp data/valnatt/senaste`. Anropet ska ske i `try/finally` som återställer `sys.argv`. Hamta-fel (returkod 1 eller 2) ger `fel("hämtningen misslyckades, inget skrivet")` som i planen.

### Gäller Task 12
Körschemat: nyckeln hämtas dagen innan (redan gjort i det här bygget, pem-filerna är gitignorerade och saknas i en färsk klon; signaturtestet hoppas då över tyst). `--utan-signatur` är reservläge och syns i utskriften som "signatur ej kontrollerad". README under Vanliga fel: "FEL: signatur saknas för <fil>". Överlämningen: halvfärdiga tidsstämpelmappar under `data/valnatt/` kan bli kvar efter avbrutna körningar och är ofarliga (`senaste` pekar bara på lyckade).

### Efter omgranskningen av Task 4 (e6fdd5e, godkänd)
Restlista, görs som egen commit av Task 6-agenten före Task 6 (bara `scripts/hamta_2026.py` och `tests/test_hamta_2026.py`):
- Återförsöket i `main` görs bara vid md5-fel eller fel antal träffar i `valj_filer` (inte vid 404 eller nätfel), med `time.sleep(3)` före andra försöket. Bryt ut orsaken, t.ex. en egen undantagsklass `AndradUnderHamtning(HamtFel)` som `kontrollera_md5` och `valj_filer` höjer, så att `main` kan skilja på dem.
- `main` fångar även `http.client.IncompleteRead`, `UnicodeDecodeError` och `zipfile.BadZipFile` (gör dem till `HamtFel` i `hamta`, `las_index`/`valj_lokala_filer` respektive `packa_upp`), och har ett sista `except Exception` som skriver `FEL: oväntat fel: <typ>: <text>` och returnerar 2, så att in-process-anrop från uppdatera_2026 alltid får en returkod.
- Katalogfelet i `peka_senaste` skriver ut den verkliga sökvägen (`ut / "senaste"`), inte "data/valnatt/senaste". Vakten mot en riktig katalog körs redan i början av `main` (före hämtning) så att felet kommer snabbt.
- Oanvänd bindning `index` från `valj_lokala_filer` i `main` tas bort.
Task 6: omge `hamta_2026.main()` med `except Exception` som ger `fel("hämtningen misslyckades: <typ>: <text>")`.

---

## Tillägg till valnattsplanen, beslutat av kontrollern 2026-09-06 efter kvalitetsgranskningen av Task 5

### Ändringar i `schema.swing` (rättas i Task 5-uppföljning)
- Nytt argument `samma_yta=None`. None (standard) betyder dagens regel: helomrade när alla distrikt i ny är räknade och antalet distrikt är lika i ny och bas. True betyder att anroparen intygar att området täcker samma yta i båda åren, så helomrade gäller när alla distrikt i ny är räknade oavsett antal (2022 mot 2018: 23 mot 22 distrikt, samma yta enligt specen). False betyder aldrig helomrade. Områdesnivån bryts ut till en hjälpfunktion `_omradesniva(ny, bas, bas_d, val, jamforbara, samma_yta)` som ger `(majorna_diff, kohortpost)`.
- `_diff` normaliserar negativ noll (`round(...) + 0.0`) så att sidan aldrig visar "-0,0". Docstringen säger att ett parti som saknas i ett års data behandlas som "inte redovisat" oavsett om filen är preliminär (inte rapportparti) eller slutlig (noll röster), och att funktionen därför aldrig visar ett fall till noll.
- Distrikt som saknas i basåret får meningen "{namn} fanns inte som valdistrikt {ar_bas}. Siffrorna går inte att jämföra med {ar_bas}." (inte "ritades om").
- `*.tmp` i `.gitignore`.

### Gäller Task 11 (kortet)
`kohort.antal` räknar distrikt som är både räknade och jämförbara, medan statusraden räknar alla räknade. Texten i `omradesRad` och `hurAndratMajorna` ska därför lyda "räknat på N jämförbara distrikt av 23" (inte "räknat på N av 23 distrikt"), så att läsaren inte tror att bara N är räknade. Specen (avsnitt 5 och 7) skriver samma tal på båda ställena; det är ett specfel.

### Gäller historikplanen (`docs/superpowers/plans/2026-09-05-historik-sektion.md`, swing_2022 mot 2018)
Anropa `schema.swing(valdata_2022, valdata_2018, jamforbara=[de nio], meningar=..., samma_yta=True)` i stället för att skriva över `s["majorna"]` och `s["kohort"]` i efterhand. Områdesnivån blir då aggregatet för de 23 distrikten mot aggregatet för 2018 års 22, vilket ska stämma med tidsserien; kontrollera det med ett test i stället för att patcha. Kontrollern läser historikplanen innan den körs och avgör då exakt hur.

### Efter omgranskningen av Task 5 (019fc03, godkänd)
Restlista (egen liten commit, görs av restcommit-agenten före Task 6): docstringen i `_omradesniva` ska beskriva `samma_yta` (None kräver lika antal distrikt, True kräver bara att alla är räknade, False aldrig helomrade); i `test_swing_negativ_noll` (eller vad testet heter, rad cirka 131) ersätts den verkningslösa `assert d["V"] == 0.0` med `assert math.copysign(1, d["V"]) == 1.0`; ett test att `samma_yta=True` fortfarande ger `helomrade False` när ett distrikt är oräknat.
Gäller Task 9 (JS): `pe()` i valgrafik.js (rad cirka 140) ger "−0,0" för värden mellan -0,05 och 0; normalisera så att avrundat noll alltid skrivs "0,0" utan tecken. Divergensen i Majorna mot Sverige räknas i JS och kan träffa det.

---

## Tillägg till valnattsplanen, beslutat av kontrollern 2026-09-06 efter kvalitetsgranskningen av Task 6

### Rättat i Task 6-uppföljning (`scripts/uppdatera_2026.py`, `scripts/valnatt.py`)
- Planfel: spärren "tom import: inget distrikt räknat i något val" var ett `fel` och stoppade kvällens första körning (20.00 till cirka 21.00 är inget Majornadistrikt räknat), så konfigen växlade aldrig till valnattsläget. Nu en varning; filerna skrivs med `meta.valnatt.raknade: 0` och konfigen sätts. Per-val-spärren mot färre räknade distrikt än befintlig fil finns kvar.
- `riksdag_verklig` skrivs så snart mandatfördelningen finns, även när inget Majornadistrikt är räknat i rd.
- Halvskriven JSON (`JSONDecodeError`), fel teckenkodning och läsfel ger `FormatFel` med filnamn (i `valnatt._las_objekt`), aldrig traceback. Trasig jämförelsefil ger `fel`.
- FEL-texten för färre räknade distrikt säger att `--tvinga` ersätter hela filen (rf och kf töms om de saknas i den nya) och att rätt kommando efter ett stopp är `--valnatt-mapp data/valnatt/senaste --tvinga` (eftersom `--hamta` med `--bara-om-nytt` ger kod 3 för samma filer).
- Flera röst-, mandat- eller summeringsfiler i samma valmapp ger varning med filnamnen.
- Alla tre valens spärrfel samlas och rapporteras innan körningen avbryts. Namnvarningen ges en gång per distrikt och körning. Okända partier varnas per parti aggregerat över distrikten. Valdata, swing och konfig byggs i minnet innan något skrivs. Utskrifter med radbuffring så att `2>&1 | tee` ger rätt ordning. `SystemExit` från `hamta_2026.main()` ger FEL-rad. Testdata (`meta.test`) till repots `data/` kräver `--tvinga`.
- Docstringen: båda jämförbarhetskällorna (JSON-filernas statusJamforelse och Valmyndighetens xlsx) läses; säger någon "ej jämförbart" gäller det, med varning vid konflikt. Det är avsiktligt konservativt.

### Gäller Task 9 (JS)
`meta.valnatt.raknade` räknar distrikt där något val är räknat, inte per val. `renderPanel` (valgrafik.js rad cirka 729, texten "Snittet för räknade distrikt i Majorna") ska räkna per visat val på samma sätt som rad cirka 740 gör, så att kartan för kommunvalet inte säger "Snittet för hela Majorna" när bara riksdagsvalet är färdigräknat.

### Gäller Task 12 (README, körschema, HANDOVER)
- README-texten "om ingen fil har något räknat distrikt" (skriptet vägrar skriva) stryks; i stället: en körning utan räknade Majornadistrikt skriver filerna med 0 av 23 räknade och slår på valnattsläget, det är det normala läget den första timmen.
- Vanliga fel: "FEL: ... färre räknade distrikt" - en trasig fil i ett val stoppar hela skrivningen, avsiktligt; efter ett stopp är kommandot för att gå vidare `--valnatt-mapp data/valnatt/senaste --tvinga`, och `--tvinga` ersätter hela filen (slår inte ihop med den gamla). "FEL: ... har inte formen av en JSON-fil" (halvskriven fil: kör igen).
- Körschemat: torrkörningen skriver till en tillfällig mapp; skriptet vägrar testdata till repots `data/` utan `--tvinga`.
- HANDOVER: refaktoreringar som väntar till efter valet: `main` i uppdatera_2026 är lång, `bygg` läser globalen `JAMFORBAR`, xlsx-vägen och JSON-vägen dubblerar distriktsslingan.

### Efter omgranskningen av Task 6 (a935f04, godkänd)
Restlista, görs som egen commit av Task 7-agenten före Task 7: `las_bas` (och `schema.las_konfig` via `main`) ger FEL-rad, inte traceback, på skadad JSON; FEL-texten vid färre räknade distrikt listar valen på en rad och ger instruktionen en gång; test för grenen "befintlig skarp, ny testdata".
Gäller Task 12 (README): `--tvinga` låser upp tre spärrar samtidigt (färre räknade, testdata över skarp, testdata till repots data/), så efter en `--genrep`-körning med standard-`--ut` skriver återstartskommandot testmärkt data utan stopp; skriv det under Vanliga fel.

### Efter kvalitetsgranskningen av Task 7 (36daa4a), rättas i Task 7-uppföljning
`las_csv`: radnummer ur `DictReader.line_num` (tomma rader i mallen gjorde numren 23 rader fel); extra kolumn, fel teckenkodning och saknad fil ger FEL-rad; `rostberattigade` måste vara ifyllt för alla räknade distrikt i ett val eller inget (annars blev Majornas valdeltagande över 100 procent i aggregatet); tal med hårt mellanslag (U+00A0) tolkas; rad med tal men utan val eller kod ger FEL; varningen för saknad `rostande` säger att valdeltagandet då visas cirka en procentenhet för lågt; spärrtexten nämner kompletteringsfallet `--valnatt-mapp data/valnatt/senaste --csv valnatt.csv`; mallen får två inledande instruktionsrader; oläsbar befintlig valdata säger "ta bort filen och kör om".

### Gäller Task 12 (README, avsnittet Reservväg)
- Kompletteringsfallet som eget stycke: fyller man i några distrikt för hand medan JSON-vägen fungerar för resten körs `--valnatt-mapp data/valnatt/senaste --csv valnatt.csv`; CSV:n vinner per distrikt och val, resten kommer från JSON-filerna och jämförelseaggregaten finns kvar. `--csv` ensam ovanpå en färdig fil stoppas av spärren, och `--tvinga` ersätter hela filen i stället för att komplettera.
- Mallen har 12 rader per distrikt (9 partier inklusive Övriga plus giltiga, rostande, rostberattigade), 276 tal för riksdagsvalet, inte "cirka 200". Mallen täcker bara riksdagsvalet; rf och kf skrivs för hand i samma format. Partiordningen i mallen är sidans (V, S, MP, SD, M, C, L, KD), inte val.se:s.
- Vanliga fel: "FEL: ... 'rostberattigade' är ifyllt för vissa distrikt men inte för ..." (fyll i för alla eller inget), "FEL: ... rad N: fler kolumner än rubriken" (extra semikolon), "FEL: ... kunde inte läsas" (spara som CSV UTF-8 i Excel).

### Efter omgranskningen av Task 7-rättelsen (2e71e59, underkänd, rättas i 2e71e59-uppföljning)
Regeln för `rostberattigade` gäller slutläget per val över alla räknade distrikt (även dem JSON-vägen fyllt), inte bara CSV:ns rader; saknas talet i CSV:n för ett distrikt som JSON-vägen redan har ett tal för behålls JSON-vägens tal. Kommentarkontrollen körs före kolumnvakten. "Spara som CSV UTF-8" bara vid teckenkodningsfel. `las_bas`-rådet "ta bort filen" bara för den nya årsfilen, inte för basåret.
README (Task 12, Reservväg): rader som börjar med # hoppas över; `rostberattigade` är allt eller inget per val; kompletteringskommandot; saknad `rostande` sätts lika med giltiga (valdeltagandet cirka en procentenhet för lågt).

### Efter tredje granskningen av Task 7 (809b3d8, godkänd)
Restlista, görs som egen commit av Task 8-agenten: kontrollen av röstberättigade (blandat läge ger FEL, saknas för alla ger varning) flyttas ut ur `las_csv` till en funktion `kontrollera_rostberattigade(distrikt)` som `main` kör på slutläget oavsett källa (JSON-vägen ensam saknade vakten: ett distrikt med `antalRostberattigade: null` gav 5 procent för högt valdeltagande utan varning); FEL-texten skiljer på "saknas i CSV-filen" och "saknas i källan"; kommentarkontrollen i `las_csv` normaliserar nycklarna först (rubriken `Val;Kod;Parti;Roster` gav "okänt val '#'"); docstringen för `las_bas` stämmer med anropen (`skriv_mall` använder `roll="bas"`); `las_rafiler` i `main` omges av samma felfångst som de andra vägarna så att en oläsbar xlsx ger FEL-rad, inte traceback.

---

## Tillägg till valnattsplanen, beslutat av kontrollern 2026-09-06 efter kvalitetsgranskningen av Task 8

### Rättas i Task 8-uppföljning (`scripts/bygg_geo.py`, `scripts/geo.py`, `scripts/bygg_data.py`, `tests/test_geo.py`)
- Okänt `--ar` utan `--zip` ger FEL-rad, inte traceback (`Path("")` existerar). `--ar` valideras som fyra siffror.
- Ytkontrollen räknar `unary_union` på oavrundade geometrier för båda åren och rapporterar symmetrisk differens och areaskillnad i kvadratmeter (tröskel 10 kvadratmeter), i stället för summan av avrundade `area_km2` (kvantiseringsfel upp till 1 150 kvadratmeter, blind för luckor och överlapp). Saknat `--jamfor` ger FEL; saknad standardjämförelse skrivs ut som en rad.
- `geo.las_distrikt` föredrar `.geojson` framför `.json` och ger begripligt fel när filen saknar `features`. `egenskaper` faller tillbaka även på null och tom sträng.
- `bygg_data.py`: docstringen säger `distrikt_2022`; sidviktsmätningen summerar de filer sidan laddar (konfig, distrikt_<år> och valdata_<år> för åren i konfigen, bakgrund) i stället för `*.js`.
- Tester: exakt de nio omritade har ändrat form (symmetrisk differens över 100 kvadratmeter) och övriga är oförändrade inom 10 kvadratmeter; unionerna är lika; inga överlapp; committad `distrikt_2026.geojson` är byte-identisk med byggarens utdata; `bygg_geo.py` går att köra som subprocess; 2026-namnen börjar inte med "Västra Centrum". `ZIP_2026` relativt `ROT`.

### Planens steg 6 för Task 8 stämde inte med verkligheten
Förväntad utskrift var "4.6554 km²" och "+146 kvadratmeter"; verkligheten är 4,6553 km² i båda åren och 0 kvadratmeters skillnad (full precision: 4 655 447,5 mot 4 655 445,8). Ingen åtgärd i koden; noteras i överlämningen.

### Gäller Task 9
`scripts/hamta_bakgrund.py` rad cirka 156 har `--geojson` med standardvärdet `data/distrikt.geojson` och går sönder när filen tas bort; ta med den i namnbytet. `bygg_data.py`:s docstring likaså om den inte redan är rättad.

### Observation till överlämningen (Task 12)
Elva distrikt skiljer sig geometriskt mellan 2022 och 2026, inte nio: Marieberg (14800542) och Karl Johan (14800544) har bytt ett kvarter på 533 kvadratmeter (vid 57,696174 N, 11,928638 E) men Valmyndigheten markerar båda som "Kan jämföras", så kortet visar förändring för dem. Det är Valmyndighetens bedömning och koden följer den.

### Efter omgranskningen av Task 8-rättelsen (4346bbd, godkänd)
Restlista, görs som egen commit av Task 12-agenten (`scripts/bygg_geo.py`, `scripts/geo.py`, `tests/test_geo.py`): `--jamfor` och `--zip` kontrolleras med `is_file()` (katalog eller tom sträng ger FEL-rad, inte traceback) och valideras före inläsningen; `jamfor_union` gör `buffer(0)` på ogiltiga geometrier eller ger ValueError med begripligt meddelande; subprocesstesterna kontrollerar felraden, inte bara returkoden; identitetstestet jämför bytes (läs geojson-filen som text mot `json.dumps` med samma parametrar som `schema.skriv`) och finns även för 2022; test för raden "Ingen ytjämförelse".

---

## Tillägg till valnattsplanen, JS-delen, antecknat av kontrollern 2026-09-06 efter Task 9

### Gäller Task 10 (samma fil, rätta i samma commit)
Befintlig bugg (finns även före Task 9, verifierat av Task 9-agenten): i bildläget `?bild=jamforelse` kastar sidan `TypeError: Cannot read properties of null (reading 'replaceChildren')` efter att bilden ritats, eftersom `state.bild` bara sätts i karta-grenen av `renderBild` och ResizeObserver då anropar `renderKarta()` när `.mp-main` ersatts och `$("#karta")` är null (valgrafik.js rad cirka 668). Bilden blir rätt ändå, men felet syns i konsolen och kan dölja riktiga fel. Rättning: sätt `state.bild` för båda bildlägena (eller vakta `renderKarta` mot saknat `#karta`), och kontrollera med `verktyg/skal-check.js` bildläget att inga JS-fel loggas för `?bild=jamforelse` och `?bild=karta`.

### Gäller Task 12 (README, HANDOVER)
Sidan laddar `swing_<år>.js` för varje år i konfigen och tål att filen saknas (404 i konsolen, ingen swing för det året). `swing_2022.js` finns inte förrän historikplanen skrivit den; `verktyg/skal-check.js` och `beehiiv-check.js` räknar en saknad `data/swing_<år>.js` som "valfri fil som saknas", inte som JS-fel. Skriv det under Fallgropar (och att en saknad `valdata_`- eller `distrikt_`-fil däremot är ett fel).
Verktygen: `verktyg/forbered_tvaar.py` och `tvaar-check.js` bygger och kontrollerar testsidan `tmp/tvaar/` (gitignorerad) med två år; valnattsdatan tas från en mapp skriven av `uppdatera_2026.py`.

### Efter spec-granskningen av Task 9 (06bdcb8, godkänd)
Gäller Task 12: `index.html`, `docs/beehiivtest.html` och `docs/inbaddningstest.html` har kvar "Majornas 23 valdistrikt" i `meta description` och `og:description`; README rad cirka 5 och 188 har talet 23 i löptext. Skalets metataggar är statiska och får stå kvar med 23 (antalet är 23 båda åren), men skriv i HANDOVER att det är hårdkodat där. README-tabellens kolumner på raderna `distrikt_2022` och `valdata_2026` är fyra tecken sneda; räta upp.

### Efter kvalitetsgranskningen av Task 9 (06bdcb8), rättas i Task 9-uppföljning
`start()`: ett år vars `distrikt_<år>` eller `valdata_<år>` inte går att ladda hoppas över med `console.warn` och tas bort ur `KONFIG.ar` (sidan felar bara när inget år går att ladda); geometri, valdata, bakgrund och swing laddas i ett svep efter konfigen (två vågor, inte sex). `laddaSkript`: minutnyckeln bara på `valdata_` och `swing_` (bakgrund, geometri och 2022-data ändras inte på valnatten). Ny hjälpfunktion `raknadeIVal(val)` som `renderPanel` använder på båda ställena. `gemensamBbox` tål år utan bbox. `geoMap()` (död kod) bort. Vakt mot geometrikod utan valdata i `renderKarta`. `forbered_tvaar.py`: valfria filer (bakgrund, swing_2022) kopieras om de finns; pytest-test för skriptet. `tvaar-check.js` skriver ut vilka kontroller som föll och lyssnar på konsolfel. `test_inbaddning`: tillåtlista för `document.*`.

### Gäller Task 10
`statusText` ska använda `raknadeIVal("rd")` (inte ett fjärde eget uttryck). `tvaar-check.js` får gärna en kontroll av markörtexten per val mot en testsida där kf är halvräknat (Task 9-granskaren byggde en sådan för hand; `forbered_tvaar.py` kan få en flagga `--kf-raknade N` som doktorerar valdata_2026 i testsidan).

### Gäller Task 11 (varning)
Planens `pe(post[val][a.p] || 0)` i `hurAndrat` skriver nu ett prydligt "0,0" för ett parti utan tal i swingfilen sedan `pe()` slutade skriva negativ noll. Regeln i tillagg-ej-redovisade (hoppa över partiet) måste implementeras i `hurAndrat` och `hurAndratMajorna`, inte lämnas åt `pe()`.

### Efter omgranskningen av Task 9-rättelsen (9c8d9f0, godkänd)
Rest till Task 10: `verktyg/forbered_tvaar.py` avvisar negativt `--kf-raknade`; `tests/test_forbered_tvaar.py` får felvägstester (saknad obligatorisk fil, `--kf-raknade 99`). `gemensamBbox`-reservraden är kosmetisk (om inget år har bbox kastar `projektion` ändå); lämnas. Minutnyckeln hamnar även på `valdata_2022.js` (13,7 kB per manuell omladdning); accepterat.
Gäller Task 12: planfilen `docs/superpowers/plans/2026-09-05-valnatt-2026.md` rad cirka 1769 beskriver `geoMap`, som är borttagen; planen är historik och ändras inte, men HANDOVER ska säga att tilläggsdokumenten (scratchpad) gällde före planen där de skiljer sig, och sammanfatta avvikelserna.

### Efter Task 10 (78f3cfd)
Gäller Task 11 (samma fil): på valnatten, när läsaren byter till Valet 2022, säger statusraden "Slutligt resultat 2022. Valet 2026 är söndag 13 september." Regel: när `KONFIG.valnatt` är på och det visade året inte är `KONFIG.standardAr` ska raden bara lyda "Slutligt resultat 2022." (utan meningen om valdagen). Test i tvaar-check: klicka Valet 2022 på valnattssidan och läs statusraden.
Gäller Task 12: README rad cirka 102, 131, 188 och 200 nämner ingressen och banderollen (borta); `verktyg/README.md`-raderna för skal-check och tvaar-check ska nämna toppsvar, statusrad, bildlägeskontrollen och kf-testsidan. `.forbehall` är 16 px (brödtextens minimum) medan `.not` är 14 px; behålls.

### Efter spec-granskningen av Task 10 (78f3cfd, godkänd)
Observationer att väga in i Task 11 eller kvalitetsgranskningen av Task 10: `.statusrad` har `min-height: 26px` (en rad) men på 390 px blir statusraden två rader, så `header.topp` växer 30 px när datan kommer (specen: sidan ska inte hoppa); överväg `min-height` som rymmer två rader på mobil (t.ex. 52 px under 600 px containerbredd) eller kortare text. Halvcirkelns ingressmening står nu på två ställen (`MARKUP` rad cirka 31 och `renderRiksdag` rad cirka 455); bör bli en konstant. Specen säger "Ladda om" i högerkanten, tasktexten lade den inline sist i statusraden; tasktexten gäller.

### Efter kvalitetsgranskningen av Task 10 (78f3cfd), rättas i Task 10-uppföljning
Reserverade höjder: `.statusrad` 52 px under 700 px containerbredd, 26 px däröver; `.toppsvar` 208 px; valnattsraden kortas till "Preliminärt, X av Y distrikt räknade. Uppdaterad HH:MM." (rubriken under säger redan riksdagsvalet); klassen `har-mening` på rot när `KONFIG.toppsvar.mening` är satt ger extra reserverad höjd. Mandatförbehållet använder `omradeDelvis(rike)`: färdigräknat riket ger "Preliminär mandatfördelning.", inte "6 626 av 6 626". Fjärde grenen i `statusText`: valnatt på och visat år skilt från standardåret ger "Slutligt resultat 2022." med "Ladda om" (vägen tillbaka till den levande vyn). Gren 3 och 4 får testsidor via flaggor i `forbered_tvaar.py` (status, valnatt av) och kontroller i `tvaar-check.js`. Negativ `--kf-raknade` avvisas före `rmtree`. Ingressmeningen till halvcirkeln blir en konstant. `statusText` byggd så att `delvis` sätts en gång. "Ladda om" blir en `<button>` med länkutseende (blanksteg fungerar, cmd-klick öppnar inget). `aria-hidden` på radens innehåll i toppsvaret så att skärmläsare inte läser talet två gånger. Förbehållet under Majorna mot Sverige säger "Sverige:" (områdets visningsnamn), inte "Riket:". `KONFIG`-standardobjektet och filhuvudet listar `valdag`, `toppsvar`, `historik`. Överflödig CSS-rad för `.ladda-om` bort. Hjälpare `arPreliminar()` för `meta.status !== "slutlig"`.
Gäller Task 12: `docs/HANDOVER.md` rad cirka 116 ("KONFIG.valnatt visar banderoll ... Halvcirkeln visar bara Majornas fördelning 2026") och 137 ("grafikens rubrik och ingress dubbla") är fel efter Task 6 och 10; README rad cirka 102 (ingressen i inbaddad-läget). Skriv om.

### Efter Task 10-rättelsen (8b79813)
Gäller Task 12 (README, konfignycklar): `toppsvar.mening` bör hållas till en rad (cirka 60 tecken); sidan reserverar höjd för en rad extra och en längre mening kan ge några pixlars hopp på små telefoner. Årväljarens rad reserveras (44 px) så fort konfigen listar två år, även innan datan kommit. Testsidorna under `tmp/` innehåller kopior av `valgrafik.js` och `.css` och måste byggas om efter varje ändring i källfilerna (fallgrop för HANDOVER).

### Efter omgranskningen av Task 10-rättelsen (8b79813, godkänd)
Rest till Task 11 (samma filer): brytpunkten för statusradens och toppsvarets reserverade höjd sänks från 700 till 600 px containerbredd (texten behöver cirka 530 px; 600 tar bort 26 till 56 px död yta mellan 560 och 699); kommentaren vid `KONFIG` i valgrafik.js säger inte längre "samma som schema.KONFIG_STANDARD" (JS-objektet bär bara `visa`-flaggorna för samarbete och hjalp).
Gäller Task 12 (HANDOVER, Fallgropar): reservationen av sidhuvudets höjd gäller från det att `konfig.js` lästs (årväljarens rad 44 px och toppsvarets höjd sätts då), inte från första målningen; i det degraderade läget där ett år inte kan laddas krymper sidhuvudet 56 px när årväljaren döljs. README (Valnatten): på valnatten visar Valet 2022 raden "Slutligt resultat 2022. Ladda om", och knappen laddar om sidan till den levande 2026-vyn. Toppsvaret i nolläget (0 av 23) visar en rad i en 208 px hög reserverad ruta; avsiktligt.

### Efter kvalitetsgranskningen av Task 11 (8bdd36c), rättas i Task 11-uppföljning
Talraden får riktiga mellanslag mellan talen (brytbar; `nowrap` bara inom "S +3,8"), så att den inte rinner ut ur kortet under 340 px. Noten "Små tal: förändring mot 2022 i procentenheter" får kohortförbehållet (", räknat på N jämförbara distrikt av 23") när `kohort[val]` finns och inte är helomrade, eftersom de små talen på Hela Majorna räknas på kohorten. tvaar-check kontrollerar att ett parti som tas bort ur swingposten försvinner ur raden utan "0,0". `toppMedTal`-parametern `tal` byts (skuggar formateraren `tal`); dubbelt `helomrade`-prov bort; `storst` bara i omritningsgrenen; rubriken "Hur har det ändrats" som `<h4>`; `#panel-live` läser med omritningsmeningen; docstring i `forbered_tvaar.py` om att kf-sidans swingfil är omräknad, inte pipelinens.
Gäller Task 12 (README, Dataschema/Valnatten): beskriv raden "Hur har det ändrats" (tre grenar: jämförbart distrikt får tal för de tre största partierna med tal, omritat får mening och områdesrad, Hela Majorna får kohorttexten "räknat på N jämförbara distrikt av 23" tills alla är räknade; partier som saknar tal i swingfilen visas inte). HANDOVER: avvikelsen från specens kohortformulering ("N av 23 distrikt" blev "N jämförbara distrikt av 23", eftersom kohorten är räknade och jämförbara medan statusraden räknar alla räknade). `docs/skarmdumpar/` visar kort utan raden.

---

## Tillägg till historikplanen, beslutade av kontrollern 2026-09-07 innan bygget

Planen skrevs 2026-09-05 före valnattsomgången. Koden har ändrats sedan dess; tilläggen nedan gäller före plantexten där de skiljer sig. Kontrollern har verifierat punkterna mot databasen och koden.

### Miljö
- Databasen `data/historik/majorna_historik.sqlite` är en symlänk i worktreet till huvudkatalogens fil (gitignorerad). Öppnas skrivskyddat. Tabeller: aggregat, crosswalk, distrikt, distrikt_summa, fortidsroster, majorna_medlem, mandat, parti_kanon, partier, rostberattigade_kategori, roster, tidsserie, val.
- `tidsserie` majorna rd V: 2006 3225/18803 (17 distrikt), 2010 3785/20452 (17), 2014 4102/20960 (17), 2018 6782/21167 (22), 2022 5793/21308 (23). Stämmer med planens fakta.
- `roster.parti_kanon` 2018 innehåller utöver sidans koder även numeriska koder ("0470", "1397"), småpartier (AFS, MED, SKP med flera) och "ÖVR"; planens `distrikt_ur_db` lägger allt som inte är nyckelparti i Övriga, vilket är rätt.
- **`mandat`-tabellen har dubbla rader** för riket rd 2006 (varje parti två gånger, samma tal, plus en rad `ÖVR` med 349). Planens Task 4 `verklig = {r["parti"]: int(r["mandat"]) ...}` skulle ge `ÖVR: 349` och en summa långt över 349. Regel: filtrera `parti` till `NYCKELPARTIER["rd"]` (V, S, MP, SD, M, C, L, KD), ta `DISTINCT` (eller `MAX(mandat)` per parti), och kontrollera summan 349 med `SystemExit` vid avvikelse. Kontrollera samma sak för 2010, 2014, 2018 innan filerna skrivs.
- `val`-tabellen har `valdag` per (ar, val); 2006 ger "2006-09-17".

### Task 2: `swing_2022` med `samma_yta=True`, ingen efterhandsskrivning
`schema.swing` har sedan valnattsomgången argumentet `samma_yta` (None = dagens antalsregel, True = anroparen intygar samma yta så helomrade gäller när alla distrikt i ny är räknade oavsett antal). Planens kod skriver över `s["majorna"]` och `s["kohort"]` efter anropet; det ska i stället göras så här:
- Bygg `bas` med `distrikt` = de nio 2018-distrikten under 2022 års koder (som planen) OCH `aggregat.majorna[val]` = områdesnivån ur `tidsserie` 2018 (nivå majorna): `{"roster": {...}, "giltiga", "rostande", "rostberattigade"}` där `roster` har exakt samma nycklar som `ny["aggregat"]["majorna"][val]["roster"]` (NYCKELPARTIER[val] plus Övriga); partier i tidsserien som inte är nyckelpartier för valet (t.ex. K i rf) läggs i Övriga. Det behövs eftersom `schema._diff` bara räknar partier som finns i båda åren och utelämnar Övriga när partiuppsättningen skiljer sig.
- Anropa `schema.swing(ny, bas, jamforbara=list(kedja), meningar=meningar, samma_yta=True)`. Då blir `majorna[val]` diffen av aggregaten (samma tal som planens tidsserieformel, avrundat till en decimal) och `kohort[val]` = `{antal: 23, totalt: 23, helomrade: True, koder: [...]}`.
- Lägg därefter till `s["kohort"][val]["metod"] = "omradesserien"` som ren anteckning (kortet läser inte nyckeln). Planens test behålls; testet på `s["majorna"]["rd"]["V"]` mot tidsserien ska passera utan efterhandsskrivning. Lägg ett test att `s["majorna"]["rd"]` inte har negativ noll och att Övriga finns med i diffen (partiuppsättningarna är lika).

### Task 6 till 9: sidan har ändrats sedan planen skrevs
- `start()` i `valgrafik.js` laddar konfig först och sedan geometri, valdata, bakgrund och swing för alla år i ett `Promise.all`; ett år utan geometri eller valdata hoppas över. `historik` och `distrikt_2006` läggs i samma svep (med `.catch(() => null)`), inte som sekventiella `await` efter swing. `KONFIG.historik.visa === false` stänger av laddningen.
- Sidhuvudet har statusrad och toppsvar (ingen banderoll, ingen ingress); `raknadeIVal(val)`, `arPreliminar()`, `omradeDelvis(post)`, `raknadeText(post)`, `kohortSlut(k)` finns som hjälpare. Använd `raknadeIVal(val)` i `aretsPunkt` i stället för planens `alla.filter(...)`. Kortets rad "Hur har det ändrats" finns (Task 11); kohorttexten lyder "räknat på N jämförbara distrikt av 23". Planens Task 9 väntar sig "räknat på 9 av 23 distrikt" i kortet; det ska vara "räknat på N jämförbara distrikt av 23" där N är antalet jämförbara bland de nio första distrikten (14800526 till 14800534: jämförbara är 526, 527, 528, alltså N = 3).
- `verktyg/forbered_tvaar.py` har flaggorna `--valnatt`, `--status`, `--kf-raknade N` (bara kommunvalet), `--utan-parti`. Planens `--partiell N` (alla tre valen) läggs till som ny flagga och räknar om swingfilen som `--kf-raknade` gör. `verktyg/tvaar-check.js` tar namngivna argument (`--sida= --kf= --kf6= --slutlig= --prel= --utanparti=`); `historik-check.js` ska följa samma mönster.
- `renderFakta` och sidfoten (`#fot`) har ändrats sedan planen (Task 10 till 12 i valnattsplanen rörde inte dem, men kontrollera mot filen innan `renderFakta` kortas i Task 8). Tillåtlistan för `document.*` i `tests/test_inbaddning.py` gäller; `s()`-hjälparen för SVG finns (kartan använder den).
- Reserverad höjd: sektionens ytor ska ha `min-height` innan datan finns (planen har det). Beehiivs regler och Majpostens skrivregler som förut.
- `data/distrikt.js` finns som övergångskopia för cachad kod (tas bort efter valet); sidan laddar den inte.
- Sidvikten i Task 10 mäts med den lista README anger plus `data/historik.js`, `data/swing_2022.js`, `data/distrikt_2006.js`.

### Task 10
HANDOVER och README uppdateras i samma anda som valnattsplanens Task 12 (statusavsnitt daterat, beslut, fallgropar, startpunkt). Planfilerna ändras inte.

### Task 1: partiuppsättning per val (beslut 2026-09-07 efter första körningen)
Databasens `tidsserie` har FI som egen rad i riksdagsvalet alla år (Majorna: 471 år 2006, 430 år 2010, 3 458 år 2014, 386 år 2018, 23 år 2022) och `SUMMA_ÖVRIGA` är residualen mot elva namngivna partier oavsett val. Sidans schema (`NYCKELPARTIER` i `scripts/valmyndigheten.py`) har åtta partier i riksdagsvalet och lägger FI i Övriga där; `valdata_2022.json` har därför Övriga 318 i rd medan tidsserien ger 295 plus FI 23. Regel: `historik.json` följer sidans partiuppsättning per val (`NYCKELPARTIER[val]` plus Övriga); partier i tidsserien utanför valets uppsättning (FI i rd, K i rf) läggs i Övriga. Då är 2022-raden identisk med `valdata_2022.json` som specen kräver, och `kontrollera.py --historik` (Task 5) kan jämföra rakt av. `meta.partier` behåller de tolv koderna som "partier som kan förekomma" och `meta.noter` får en mening om regeln. Testet `set(p["roster"]) == set(PARTIER)` blir `set(NYCKELPARTIER[val]) | {"Övriga"}` och andelsloopen går över `p["roster"]`. Till HANDOVER och Daniel: FI:s 16,5 procent i Majornas riksdagsval 2014 syns bara i Övriga; vill Daniel se FI som egen linje i riksdagsvalet krävs att FI blir nyckelparti i rd i hela schemat (även 2022 och 2026), ett beslut efter valet.

### Efter kvalitetsgranskningen av Task 1 (fb46d3d)
Rättas i Task 1-uppföljning: `meta.noter` om Övriga ("giltiga minus de elva partierna") stämmer bara för kommunvalet; skrivs om. `meta.partier_per_val` = `{val: NYCKELPARTIER[val] + [Övriga]}` läggs till. `metod` väljs deterministiskt (mängden icke-residualsträngar, fel vid fler än en). `ALLA_KODER` utan positionsberoende. `valdeltagande`-vakten `is not None`. Kontroll att giltiga, rostande och röstberättigade är lika på alla rader i en grupp. Saknad tabell ger FEL-rad. Ny hjälpare `omradespost(con, ar, val, niva)` som gör frågan och anropar `_post` (Task 2 använder den för basaggregatet 2018). Tester: `meta.metod` fem nycklar, `valdeltagande` på alla nivåer, `antal_distrikt` null för goteborg och riket i alla val, felfall med saknad databas.

Gäller Task 2: loopa aldrig över `PARTIER` för andelar (KeyError på FI i rd); bygg `bas["aggregat"]["majorna"][val]` ur `omradespost(con, 2018, val, "majorna")` med nycklarna roster, giltiga, rostande, rostberattigade; Övriga kommer med i diffen eftersom partiuppsättningarna nu är lika.
Gäller Task 6: nottexten under bild A ska nämna att partier utanför valets uppsättning ligger i Övriga (FI:s 3 458 röster i riksdagsvalet 2014, 17,9 procent av Övriga det året, syns inte som egen linje). Till HANDOVER och Daniel: vill han se FI i riksdagsvalet krävs att FI blir nyckelparti i rd i hela schemat.

### Efter kvalitetsgranskningen av Task 2 (9e87f88)
Rättas i Task 2-uppföljning: `bas["distrikt"]` får alla 23 2018-motsvarigheter under 2022 års koder (kedjefilens `kod_2018` för varje rad; två 2022-koder kan peka på samma 2018-distrikt, t.ex. 14800530 och 14800535 på 14801011, vilket är tillåtet för de omritade) så att `orsak` blir "ej jämförbart enligt källan" för de fjorton, inte "saknas i basåret"; `las_kedja` returnerar de nio jämförbara med vakt mot dubbla `kod_2018` bland dem (`SystemExit`); `utf-8-sig`, `exists`-vakt och kolumnkontroll i `las_kedja`; NULL i `distrikt_summa` blir `None`, inte 0; `post[val]` sätts bara när summan finns; namnuppslag via dict; `BAS_AR = 2018`; docstring om varför `distrikt_ur_db` lägger okända koder i Övriga (rösttabellen har ingen residualrad) medan `_post` hoppar över dem; `main` sist i filen; utskriften med "9 av 23" och "14 av 23"; tester: `las_kedja()` ger exakt nio, distriktsnivåns Övriga för Godhem rd mot handräknat tal ur databasen, `giltiga`-vakten fyrar på doktorerad `distrikt_summa`.

Gäller Task 3: `distrikt_<år>_majornaomradet.geojson` (2006/2010/2014 = 17, 2018 = 22) är rena Polygon med `kod` och `namn`, inget crs-block; `scripts/geo.py` har redan polylabel, avrundning, `etikett`, `area_km2` och `bbox`; återanvänd (bryt ut en funktion i geo.py som tar en lista features) och lägg bara till `simplify`-steget för 2006.

Gäller Task 4: `mandat`-tabellen har dubbelrader 2006, 2010, 2014 och 2018 (två källor: `mandat_<år>_riksdag.csv` och `mandat_riksdag_riket.csv`), en falsk 349-rad (`ÖVR` 2006, `FI` 2014), NULL-mandat för småpartier 2010, och `niva` innehåller valkretsnamn 2006 och 2014, så `niva='riket'` är obligatoriskt; regeln `SELECT DISTINCT parti, mandat WHERE niva='riket' AND val='rd' AND parti IN NYCKELPARTIER["rd"] AND mandat IS NOT NULL` ger 349 alla fem åren; 2006 saknar SD-rad (noll mandat) så vakta summan 349, inte antalet partier. Plankodens `_jamforelse` anropar `_post(rader)` med ett argument; signaturen är `_post(rader, val)`. **Partier som inte fanns ett år**: `distrikt_ur_db` skriver i dag `"D": 0` för 2006 till 2014 och `"FI": 0` för rf 2006 och 2010; sidan skulle visa "Demokraterna 0,0 %" för ett parti som bildades 2018. Regel (samma anda som "saknas = inte redovisat"): per (år, val) ingår ett nyckelparti i distriktens `roster` bara om partiet har minst en rad i `roster` för något Majornadistrikt det året och valet; annars utelämnas nyckeln. Gäller `distrikt_ur_db` (påverkar inte swing_2022, där D, FI och K alla finns 2018 i sina val) och aggregaten i Task 4 (`_jamforelse` och `_vgregion` bygger andel bara för partier med rad). Lägg en kontroll (varning i utskriften) när ett nyckelparti helt saknar rader ett år, så att en kodavvikelse i `parti_kanon` (t.ex. FP i stället för L) inte tyst blir noll.

Gäller Task 10 (HANDOVER): fem av de nio jämförbara distrikten är geometriskt inte helt 1:1 mot 2018 (Gråberget Västra 83,5 procent innanför, Slottsskogsgat. m fl 92,0, Kommendörsgatan 95,2, Godhem 95,3, Svalebo 97,0 enligt `docs/historik/noter/kedja.md`); kortet visar rena tal eftersom Göteborgs stads jämförbarhetsbedömning används, som specen föreskriver. `swing_2022.js` är 6,6 kB och laddas före valdagen (sidvikten). `kohort.metod` finns bara i swing_2022.

### Efter omgranskningen av Task 2 (f66d60f, godkänd)
Rest till Task 3-agenten (egen liten commit före Task 3): `_las_kedja_rader` ger `SystemExit` vid dubbel `kod_2022`; `bygg_swing_2022` kontrollerar att `set(las_kedja_alla()) == {d["kod"] for d in ny["distrikt"]}`; `giltiga` i `distrikt_ur_db` hanteras som de andra summorna (`None` om NULL, då utelämnas valet); `@finns` tas bort från de två CSV-testerna som inte rör databasen.
Task 4: välj distrikt via `majorna_medlem` (aldrig uppsamlingsdistrikt, där NULL finns); `schema._summa` kraschar på None, så `distrikt_ur_db`:s None-hantering är bara robusthet. `raknat = False` när inget val har summeringsrad får inte tyst sänka `meta.valnatt.raknade` i en slutlig historikfil (lägg en vakt: alla medlemmar ska ha data i alla tre valen, annars FEL).

### Efter kvalitetsgranskningen av Task 3 (fbce812)
Rättas i Task 3-uppföljning: `las_distrikt` kontrollerar `saknas` innan `features_till_schema` (annars "min() iterable argument is empty" i stället för listan på saknade koder, valnattens troligaste fel); tolerans 0,0002 grader (symmetrisk differens 0,55 procent, största konturavvikelse 14 m, `.js` 9,5 kB); testerna mäter symmetrisk differens (under 1,2 procent) med nettot som lös gräns, storleken på `.js` (under 12 kB) i stället för `.geojson`, byte-identitet för den committade `distrikt_2006.*`, grad-3-noder bevarade, ytterkonturen 2006 mot 2022 (symmetrisk differens under 1,2 procent); en ensam feature och ogiltig indata hanteras i den topologiska vägen (`buffer(0)` först, `linemerge` bara på MultiLineString); skilda felmeddelanden för dubbel kod, överlappande källpolygoner och fel antal polygoner; kommentaren räknar 16,8 m per pixel (cos(lat)); `decimaler`-parametern tas bort ur `las_distrikt`; docstring om att `area_km2` i den förenklade filen inte beskriver det verkliga distriktet; `returncode` kontrolleras i testerna och bygget görs en gång per modul.

Gäller Task 4: `bygg_geo(2010/2014/2018, False)` är verifierat (giltiga, noll överlapp, etiketter inne, union 0,041 procent från 2022, bbox skiljer 18 m i öst); `.js`-filerna blir cirka 28 kB var (laddas inte).
Gäller Task 8: varje feature har exakt en ring (`coordinates[0]` är säkert); gemensam bbox 2006 och 2022 skiljer cirka 1 px; `stroke-width: 3` i viewBox 1000 blir 0,5 CSS-px vid 170 px bredd, för tunt; använd 4 till 5 och titta på skärmdumpen i 1x och 2x. Ytterkonturerna 2006 och 2022 sammanfaller på riktigt (0,047 procent).

### Efter kvalitetsgranskningen av Task 4 (a3fbe57)
Rättas i Task 4-uppföljning: `HISTORIK_AR = [2006, 2010, 2014, 2018]` som tillåtlista i `main` (`ar 2022` skrev annars över sidans kanoniska `valdata_2022` innan den dog på saknad geometri); `kalla` "Valmyndigheten, slutlig rösträkning per valdistrikt {år}." och `avgransning` "{n} valdistrikt som täcker samma yta som dagens 23" (inga repo-sökvägar i publicerad text; filerna byggs om); tester: `riksdag_majorna` räknas om oberoende i testet ur distriktens summerade rd-röster med `jamkade_uddatal` (importen fanns oanvänd), vakten "alla tre valen" och 349-dubblettvakten på doktorerad databas; `_vgregion` med `ORDER BY parti`, dubblettvakt per parti och enighetskontroll av summorna, None-hantering som `_post`; `rd_summa` via `schema._summa`; `main`: `in (...)`, icke-numeriskt år ger FEL-rad, `aren` avvisas för underkommandon som inte tar år; 2006-regeln ("bara förenklad geometri") i `bygg_geo` eller dokumenterad; indentering.

Gäller Task 10 (HANDOVER och README): sidan klarar 2018 i `KONFIG.ar` helt (22 distrikt, kort, tabell, Majorna mot Sverige med Västra Götaland, halvcirkeln 349, Röstdelningen, inga JS-fel; 404 för `swing_2018.js` är valfri); **2006 får inte läggas i `KONFIG.ar`** förrän en oförenklad `distrikt_2006` finns (den förenklade konturfilen har 309 hörn mot 1 146 för samma distrikt 2010; sidan ritar den utan varning). Ett historikår kostar cirka 40 kB. 2014: FI fick 16,5 procent i Majornas riksdagsval (tredje största) och ligger helt i Övriga (18,0 procent); halvcirkeln delar ut alla 349 mandat på åtta partier och kortet visar Övriga som tredje stapel; kräver redaktionell not om 2014 någonsin visas, eller att FI blir nyckelparti i rd (Daniels beslut). SD 2006 (noll verkliga mandat, 2,0 procent i Majorna) syns inte i mandatlegenden (befintlig sidlogik). `aggregat.goteborg` bär `namn` och summor i historikfilerna (supermängd mot 2022). `riksdag_verklig` i alfabetisk ordning (sidan sorterar själv).

### Gäller Task 6 (beslut 2026-09-07 innan bygget)
- X-axeln: planens `histAxelAr` lägger bara till det visade året, så före valdagen (index.html visar 2022) skulle axeln sluta på 22 utan ring, medan specen (avsnitt 7, "Före valdagen") och planens Task 9 (`xEtiketter === '06 10 14 18 22 26'` på index.html) kräver en tom ring på 2026 med talraden "2026: räknas på valnatten." Regel: axeln är seriens år, plus det visade året om det inte är med, plus nästa valår ur `KONFIG.valdag` (första fyra tecknen) om det är större än sista året på axeln. `histTalrad` för ett år utan punkt skriver "{år}: räknas på valnatten."
- `aretsPunkt` använder `raknadeIVal(val)` och `arPreliminar()`; punkten finns bara när alla distrikt är räknade (som planen).
- Laddningen: `historik` och `distrikt_2006` i samma `Promise.all`-svep som övriga datafiler (efter konfigen), båda med `.catch(() => null)`; `KONFIG.historik.visa === false` stänger av. Sektionen döljs (`hidden`) när `state.historik` saknas.
- Nottexten under bild A (planens text) får ett tillägg: "Partier utanför valets uppsättning ligger i Övriga; i riksdagsvalet 2014 gäller det Feministiskt initiativ med 16,5 procent." Skriv talet ur datan (`serie.rd.majorna` 2014: Övriga minus det som Övriga var 2010 och 2018 säger inget; ta i stället det fasta talet ur historikdatabasen, 3 458 av 20 960 = 16,5 procent, som en redaktionell konstant i `KONFIG.historik`-fri form: en konstant `HIST_NOT_FI_2014` i JS med kommentaren att talet är ur `tidsserie` 2014 rd majorna FI). Om det känns fel att hårdkoda: skriv noten utan talet ("ligger i Övriga, störst i riksdagsvalet 2014") och rapportera.
- `renderHistorik` anropas sist i `renderAllt`, i flikarnas `onclick` i `renderKontroller`, och i ResizeObserver när bredden ändras (läs hur observern är skriven i dag, variabelnamnen i planen kan skilja sig).
- Testsidor: `verktyg/forbered_tvaar.py` kopierar `historik.js` och `distrikt_2006.js` som valfria filer (lägg till dem i VALFRIA om de saknas där) så att tvåårssidorna visar sektionen; `tvaar-check.js` behöver ingen historikkontroll än (Task 9 skriver `historik-check.js`), men kör den för att se att inget bröts.

### Efter kvalitetsgranskningen av Task 6 (16bf902), beslutat av kontrollern 2026-09-07 (andra sessionen)

Granskningen gjordes med två Opus-granskare (en visuell med 29 skärmdumpar i 320 till 1280 px, alla tre valen, inbäddningstestet och fyra valnattssidor; en kodgranskare på diffen 119c2ae..16bf902) och en motgranskare per lista som reproducerade varje fynd. Alla tal stämde mot facit och mot databasen, de fyra 2026-lägena stämde med specens avsnitt 7, inga JS-fel. Sex fynd bekräftades som Important. Rättas i en Task 6-uppföljning (egen commit: `valgrafik.js`, `valgrafik.css`, `tests/`) innan Task 7:

1. **Den tomma ringen för året som inte får ritas** låg på y(max/2), alltså exakt på 20-procentslinjen, utan text, och läslinjen ritades över den. Regel: ringen ritas på axelns nollnivå y(0) (där ritas ingen hjälplinje), med texten "räknas på valnatten" i 12 px sten högerställd strax till vänster om ringen, och läslinjen ritas före ringen så att ringen ligger överst.
2. **Talraden** byggs som noder på samma sätt som kortets rad "Hur har det ändrats" (`talrad` i valgrafik.js): ett span per parti med `white-space: nowrap` och ett vanligt mellanslag emellan, årsprefixet som eget span, mellanrum mellan grupperna med `margin-right` på spannen. `.hist-talrad` utan `nowrap` och `overflow: hidden`, så att raden bryts i stället för att klippas (den klipptes tyst vid 320 px på valnattssidan: "SD 20,6" försvann, och de tre mellanslagen i strängen kollapsade till ett). Ett parti utan tal i årets punkt hoppas över, aldrig "0,0", och linjen får ett hål i stället för att gå till noll.
3. **Sista punkten kommer från det senaste laddade året, inte från kartans årsknapp.** `aretsPunkt` läser det största året i `KONFIG.ar` (det årets `state.data`) oavsett `state.ar`; sektionen följer kartans val men inte kartans år. Därmed säger sidan inte "räknas på valnatten" om 2026 när läsaren tittar på Valet 2022 efter slutlig räkning (bekräftat fel på en slutlig testsida). `raknadeIVal` och `arPreliminar` får ett valfritt dataargument med `data()` som standard, så att `aretsPunkt` kan räkna på ett annat år. `antal_distrikt` för den punkten sätts i `aretsPunkt` ur det årets distriktlista. `histAxelAr` lägger till det året och valdagsåret ur `KONFIG.valdag` sorterat; åren utan punkt räknas fram med filter mot punkterna, inte med slice.
4. **Läslinjens år** faller tillbaka till sista punkten när det valda året saknar punkt i det visade valet, inte bara när det saknas på axeln (talraden stod annars utan ett enda tal efter klick på Valet 2022 eller på Kommun med tre räknade distrikt). Ringens år går fortfarande att välja med klick och pil och ger då "{år}: räknas på valnatten."
5. **Piltangenter och klick bygger inte om bilden.** `histLinjer` skapar läslinjen en gång; `sattHistorikAr` flyttar bara x1 och x2 (eller döljer linjen) och skriver om talraden, utan `replaceChildren` och utan `focus()`. Fokus ligger då kvar av sig självt och skärmläsaren läser bara talraden (`aria-live`), inte hela bildbeskrivningen på nytt. `aria-label` på bilden är enligt specen rubrikmeningen plus "Andel av giltiga röster per valår i procent. Talraden under bilden visar ett års tal; vänster och höger pil byter år." och "{år} räknas på valnatten." när det gäller, utan seriens alla tal (den var 467 tecken; talraden är textalternativet).
6. **Partibokstäverna i högerkanten** ritas i en mörkad partifärg: partifärgen blandas mot bläck tills kontrasten mot papper är minst 4,5:1 (SD-gult gav 1,6:1, MP-grönt 3,0:1, S-rött 4,1:1; V och M klarar gränsen oförändrade). Hjälpare i JS byggd på `relLuminans` som redan finns. Linjer, punkter och ledarlinjer behåller den rena partifärgen. Ren bläcktext var alternativet; Daniel kan ändra efter valet.
7. **Omritning vid breddändring.** ResizeObservern uppdaterade referensbredden vid varje utslag, så stegvisa ändringar under 10 procent ritade aldrig om; historikbilden (viewBox i pixlar) sträcktes då av CSS till 18 px axeltext och 429 px höjd, och kartans etiketter växte från 9 till 13 px vid samma drag. Regel: referensbredden uppdateras bara när något ritades om (eller när den är null), så att ändringarna ackumuleras. Historiken får därtill en egen kontroll i observern: rita om när svg:ens viewBox-bredd i `#hist-bild-a` skiljer sig mer än 4 px från ytans `clientWidth`.
8. **Bredd och marginaler.** Golvet `Math.max(300, ...)` sänks till 200 (bara mot degenererade containrar) så att 320 px-telefoner får 1:1 mellan viewBox och pixlar; `M.v` höjs från 34 till 40 så att "40 %" får luft mot vänsterkanten (stod 0,6 px från kanten).
9. **Reserverad höjd.** `.hist-bild { min-height: 320px }` flyttas till `@container (min-width: 600px)`, samma tröskel som `arDesktop`; i bandet 600 till 899 px var bilden 320 px hög i en yta reserverad till 280.
10. **Noten under bild A** börjar med "Tryck på ett år i bilden för att se det årets tal." och namnger partierna utanför valets uppsättning (ur `meta.partier` mot `meta.partier_per_val`, med namnen i `PARTIER`): i riksdagsvalet "Partier utanför valets uppsättning ligger i Övriga: Demokraterna, Feministiskt initiativ och Kommunistiska Partiet; i riksdagsvalet 2014 fick Feministiskt initiativ 16,5 procent.", i regionvalet "... ligger i Övriga: Kommunistiska Partiet.", ingen mening i kommunvalet.
11. **Vakter och tester.** Hjälparen `histAr()` (tom lista när `meta.ar` saknas) används i `aretsPunkt` och `histAxelAr`; `renderHistorik` döljer sektionen när listan är tom. `tests/test_inbaddning.py`: regex på de tre anropsställena för `renderHistorik` (sist i `renderAllt`, flikarnas `onclick`, ResizeObservern), att sektionens markup saknar `<button`, vitrymdstolerant CSS-kontroll. `tests/test_bygg_historik.py`: `HIST_NOT_FI_2014` i valgrafik.js stämmer med `tidsserie` 2014 rd majorna FI (3 458 av 20 960), hoppas över utan databas.
12. **Accepterat utan ändring:** talradens fasta partiordning (V, S, MP, SD, M) i stället för fallande per år, eftersom positionerna då är stabila när läsaren byter år; `.hist-figur`-reglerna och den tomma `#hist-mening-b` väntar på Task 7 och 8.

Gäller Task 7 (bild B): samma mönster som bild A efter uppföljningen (omritning styrd av viewBox mot `clientWidth`, sista punkten ur senaste laddade året, etiketter med kontrast minst 4,5:1, inga "0,0" för saknade tal, `aria-label` = rubrikmeningen plus en kort beskrivning).
Gäller Task 9: `historik-check.js` kontrollerar ringens läge (cy lika med y(0)) och texten "räknas på valnatten" i bilden, att svg-noden är samma efter ett piltryck, talradens spans och att raden inte klipps vid 320 px, och kontrastkravet på etiketterna.

### Efter granskningen av Task 6-uppföljningen (3c67057, godkänd av spec- och kvalitetsgranskare)

Restlista, görs som egen liten commit av Task 7-agenten före Task 7 (bara `valgrafik.js`): läslinjen kortas så att den slutar 8 px ovanför nollnivån (den tog i bokstäverna i "räknas på valnatten" på 320 till 700 px); en delsträcka med en enda fast punkt skriver ingen `path` (villkor `fasta.length > 1`); etiketterna i högerkanten ankras vid varje partis egen sista punkt (`px` per parti, ledarlinje från `px + 4` till `px + 11`, texten vid `px + 13`), inte i en gemensam kolumn, så att ett parti vars linje slutar tidigare får bokstaven där linjen slutar; hex-parsningen bryts ut till en hjälpare (`hexTal`) som `mix`, `relLuminans` och `textFarg` delar, och `textFarg` ger versaler.

Accepterat utan ändring: kartans skaldrift stannar under tio procent vid stegvisa breddändringar (tröskeln i ResizeObservern behålls, kartkoden rörs inte i valveckan; kandidat för refaktoreringslistan efter valet); läsarens val av ringåret nollställs när bilden ritas om vid breddändring (följer beslut 4); talradens avslutande blanksteg (samma mönster som kortets rad).

Gäller Task 7 (bild B): Göteborgs- och riketlinjerna kan sluta tidigare än Majornas (aggregat saknas för det visade året via CSV-vägen), så etiketten ska sitta vid varje series egen sista punkt, med samma förskjutningsregel som bild A. Bild B använder samma hjälpare som bild A efter uppföljningen: `histPunkter` (sista punkten ur senaste laddade året), `histAxelAr`, `histHarTal`-mönstret för saknade tal, `textFarg` för etiketter i färg, ingen egen omritningslogik (ResizeObserverns `histBildSlak` prövar bara bild A; bild B ritas om i samma `renderHistorik`).
