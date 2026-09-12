#!/bin/bash
# Valnattens slinga: hämtar Valmyndighetens filer, läser in dem och publicerar, utan handpåläggning.
#
# Ett varv är körschemats kommando (docs/valnatt-korschema.md, Söndag): uppdatera_2026.py --hamta,
# och vid ny data git add data, commit, push. Första gången läggs --valnatt till, så att konfigen
# slår över i valnattsläge. Dessutom hanterar slingan de två fällorna körschemat beskriver:
#   - "Inget nytt" fast förra körningen stannade på ett FEL efter hämtningen: då provas
#     --valnatt-mapp data/valnatt/senaste, samma väg som körschemat anger, aldrig --tvinga.
#   - En push som inte gick fram: kvarliggande commits pushas i början av nästa varv.
# Allt som kräver ett beslut (--tvinga, --utan-signatur, byte till slutlig räkning, CSV för hand)
# gör slingan inte; den loggar FEL och fortsätter försöka, och skickar en macOS-notis vid tre
# fel i rad.
#
# Körs för hand:            bash verktyg/valnatt-slinga.sh
# Körs som launchd-agent:   se docs/valnatt-korschema.md
# Stoppas:                  touch valnatt-slinga.stopp i projektroten (slingan tar bort filen och avslutar)
# Loggen:                   ~/valnatt-slinga.log (VALNATT_LOGG)
#
# Miljövariabler för provkörning: VALNATT_ROT (projektrot), VALNATT_LOKAL (mapp med zip-filer i
# stället för val.se; genrepsfilerna är testmärkta så --tvinga läggs då till), VALNATT_INTERVALL,
# VALNATT_INTERVALL_VANTAR (sekunder), VALNATT_GREN (standard main), VALNATT_STATUS och
# VALNATT_TILLFALLE (standard preliminar och p).

ROT="${VALNATT_ROT:-$(cd "$(dirname "$0")/.." && pwd)}"
PY="$ROT/.venv/bin/python"
LOGG="${VALNATT_LOGG:-$HOME/valnatt-slinga.log}"
STOPP="$ROT/valnatt-slinga.stopp"
PIDFIL="$ROT/valnatt-slinga.pid"
STATUS="${VALNATT_STATUS:-preliminar}"
TILLFALLE="${VALNATT_TILLFALLE:-p}"
LOKAL="${VALNATT_LOKAL:-}"
GREN="${VALNATT_GREN:-main}"
INTERVALL="${VALNATT_INTERVALL:-600}"           # var tionde minut under kvällen (Pages: mjuk gräns tio bygg per timme)
INTERVALL_VANTAR="${VALNATT_INTERVALL_VANTAR:-120}"   # tills val.se öppnar
INTERVALL_DAG="${VALNATT_INTERVALL_DAG:-3600}"  # måndag till onsdag: en gång i timmen räcker
VALDAG="${VALNATT_VALDAG:-20260913}"
BEHALL_HAMTNINGAR=6

export PATH="/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin"
export GIT_TERMINAL_PROMPT=0
export PYTHONIOENCODING=utf-8
export LANG="${LANG:-sv_SE.UTF-8}"

logg() { printf '%s %s\n' "$(date '+%Y-%m-%d %H:%M:%S')" "$*" >> "$LOGG"; }
logg_block() { printf '%s\n' "$1" | sed 's/^/    /' >> "$LOGG"; }
notis() { /usr/bin/osascript -e "display notification \"$1\" with title \"Valnatten\"" >/dev/null 2>&1 || true; }

# Bara en slinga i taget. Pidfilen visar vem som kör; en död pid tas över.
if [ -f "$PIDFIL" ] && kill -0 "$(cat "$PIDFIL" 2>/dev/null)" 2>/dev/null; then
  logg "En slinga kör redan (pid $(cat "$PIDFIL")). Avslutar."
  exit 1
fi
echo $$ > "$PIDFIL"
trap 'rm -f "$PIDFIL"' EXIT

for f in "$PY" "$ROT/scripts/uppdatera_2026.py" "$ROT/data/konfig.json"; do
  [ -e "$f" ] || { logg "Saknas: $f. Avslutar."; exit 2; }
done
command -v openssl >/dev/null || { logg "openssl saknas i PATH. Avslutar."; exit 2; }

valnatt_pa() {
  "$PY" -c 'import json,sys; print("ja" if json.load(open(sys.argv[1])).get("valnatt") else "nej")' "$ROT/data/konfig.json" 2>/dev/null
}

UT=""
kor_uppdatera() {   # loggar hela utskriften, lämnar returkoden och utskriften i UT
  UT=$("$PY" "$ROT/scripts/uppdatera_2026.py" "$@" 2>&1)
  local rc=$?
  logg_block "$UT"
  return $rc
}

hamta_och_las() {   # körschemats kommando; --valnatt tills konfigen är i valnattsläge
  local extra=()
  [ "$(valnatt_pa)" = nej ] && extra+=(--valnatt)
  if [ -n "$LOKAL" ]; then
    local h
    h=$("$PY" "$ROT/scripts/hamta_2026.py" --lokal "$LOKAL" --tillfalle "$TILLFALLE" --ut "$ROT/data/valnatt" --bara-om-nytt 2>&1)
    local hrc=$?
    logg_block "$h"
    if [ $hrc -ne 0 ]; then UT="$h"; return $hrc; fi
    kor_uppdatera --valnatt-mapp "$ROT/data/valnatt/senaste" --status "$STATUS" --tvinga ${extra[@]+"${extra[@]}"}
  else
    kor_uppdatera --hamta --tillfalle "$TILLFALLE" --status "$STATUS" ${extra[@]+"${extra[@]}"}
  fi
}

las_senaste() {     # vägen vidare efter ett FEL efter hämtningen, utan --tvinga
  local extra=()
  [ "$(valnatt_pa)" = nej ] && extra+=(--valnatt)
  local tv=()
  [ -n "$LOKAL" ] && tv+=(--tvinga)
  kor_uppdatera --valnatt-mapp "$ROT/data/valnatt/senaste" --status "$STATUS" ${tv[@]+"${tv[@]}"} ${extra[@]+"${extra[@]}"}
}

pusha() {
  if git -C "$ROT" push -q origin "HEAD:$GREN" 2>>"$LOGG"; then
    logg "Push ok."
    return 0
  fi
  logg "PUSH MISSLYCKADES, pushas igen i början av nästa varv."
  notis "Push misslyckades, försöker igen nästa varv."
  return 1
}

publicera() {
  git -C "$ROT" add data 2>>"$LOGG" || { logg "git add misslyckades."; return 1; }
  if git -C "$ROT" diff --cached --quiet; then
    logg "Inget att committa."
    return 0
  fi
  local msg="Valnatten: uppdaterat $(date +%H:%M)"
  [ "$1" = forsta ] && msg="Valnatten: första resultaten"
  git -C "$ROT" commit -q -m "$msg" 2>>"$LOGG" || { logg "git commit misslyckades."; return 1; }
  logg "Committat: $msg"
  pusha
}

hamtat_men_inte_inlast() {   # senaste hämtningen är nyare än det som ligger i data/
  local manifest="$ROT/data/valnatt/senaste/hamtat.json"
  [ -f "$manifest" ] || return 1
  [ -f "$ROT/data/valdata_2026.json" ] || return 0
  [ "$manifest" -nt "$ROT/data/valdata_2026.json" ]
}

stada_hamtningar() {   # behåll de senaste, senaste-länken rörs aldrig (mappnamnen är tidsstämplar utan mellanslag)
  local d="$ROT/data/valnatt"
  [ -d "$d" ] || return 0
  local alla=( $(ls -1d "$d"/2* 2>/dev/null | sort) )
  local n=${#alla[@]} i=0
  while [ $i -lt $((n - BEHALL_HAMTNINGAR)) ]; do
    local gammal="${alla[$i]}"
    [ "$(readlink "$d/senaste")" = "$(basename "$gammal")" ] || rm -rf "$gammal"
    i=$((i + 1))
  done
}

raknade() { printf '%s\n' "$UT" | grep -m1 '^Räknade distrikt'; }
felrad() { printf '%s\n' "$UT" | grep -m1 '^FEL'; }

logg "Slingan startar (pid $$, rot $ROT, gren $GREN, status $STATUS, tillfälle $TILLFALLE${LOKAL:+, LOKAL $LOKAL})."
FEL_I_RAD=0
PUBLICERAT=0

while :; do
  if [ -e "$STOPP" ]; then
    rm -f "$STOPP"
    logg "Stoppfil hittad. Slingan avslutas."
    exit 0
  fi

  # Kvarliggande commits från ett varv där pushen inte gick fram.
  git -C "$ROT" fetch -q origin 2>>"$LOGG"
  kvar=$(git -C "$ROT" rev-list --count "origin/$GREN..HEAD" 2>/dev/null || echo 0)
  if [ "${kvar:-0}" != 0 ]; then
    logg "$kvar commit(s) är inte pushade. Pushar."
    pusha
  fi

  sov=$INTERVALL
  hamta_och_las
  rc=$?
  case $rc in
    0)
      logg "Returkod 0, ny data. $(raknade)"
      if [ $PUBLICERAT -eq 0 ]; then publicera forsta; else publicera; fi
      PUBLICERAT=1
      FEL_I_RAD=0
      ;;
    3)
      if hamtat_men_inte_inlast; then
        logg "Inget nytt hos Valmyndigheten, men senaste hämtningen är inte inläst. Provar --valnatt-mapp data/valnatt/senaste."
        las_senaste
        rc2=$?
        if [ $rc2 -eq 0 ]; then
          logg "Inläsningen gick igenom. $(raknade)"
          if [ $PUBLICERAT -eq 0 ]; then publicera forsta; else publicera; fi
          PUBLICERAT=1
          FEL_I_RAD=0
        else
          logg "Inläsningen stannade igen (returkod $rc2): $(felrad)"
          FEL_I_RAD=$((FEL_I_RAD + 1))
        fi
      else
        logg "Inget nytt."
        FEL_I_RAD=0
      fi
      ;;
    *)
      if printf '%s\n' "$UT" | grep -q 'index.md5 är tom eller har fel form\|svarar 404'; then
        logg "Val.se har inte öppnat än. Väntar $INTERVALL_VANTAR s."
        sov=$INTERVALL_VANTAR
      else
        logg "FEL (returkod $rc): $(felrad)"
        FEL_I_RAD=$((FEL_I_RAD + 1))
      fi
      ;;
  esac

  if [ $FEL_I_RAD -gt 0 ] && [ $((FEL_I_RAD % 3)) -eq 0 ]; then
    notis "$FEL_I_RAD fel i rad, se ~/valnatt-slinga.log"
    logg "$FEL_I_RAD fel i rad. Notis skickad. Slingan fortsätter försöka."
  fi

  stada_hamtningar

  # Efter valnatten räcker en gång i timmen (körschemat, Måndag till onsdag).
  if [ "$(date +%Y%m%d)" -gt "$VALDAG" ] && [ "$sov" -eq "$INTERVALL" ]; then
    sov=$INTERVALL_DAG
  fi
  sleep "$sov"
done
