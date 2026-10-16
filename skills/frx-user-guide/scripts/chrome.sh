#!/bin/bash
# Drive the user's signed-in Chrome window through Orca computer-use and save screenshots.
#   export FRX_WIN=<chrome window id>  FRX_SHOTS=<dir for raw png>
#   bash chrome.sh windows                 # list Chrome windows -> pick FRX_WIN
#   bash chrome.sh shot <name> [treeLines] # screenshot -> $FRX_SHOTS/<name>.png, prints a11y tree head
#   bash chrome.sh go <url> [name] [wait]  # type url in the address bar, Return, wait, optional shot
#   bash chrome.sh press "<tree regex>" [name] [wait]  # AXPress first element whose tree line matches
#   bash chrome.sh key "<combo>"           # e.g. "CmdOrCtrl+-" (zoom out), "CmdOrCtrl+0", "Escape", "Page_Down"
#   bash chrome.sh tree [lines]            # fresh accessibility tree (indexes go stale after every action)
# Full flag reference: the computer-use skill / `orca computer --help`.
set -uo pipefail
A="--app com.google.Chrome --window-id ${FRX_WIN:-}"
SHOTS=${FRX_SHOTS:-./shots}
TMP=$(mktemp -t frxguide); trap 'rm -f "$TMP"' EXIT
mkdir -p "$SHOTS"

tree() { orca computer get-app-state $A --no-screenshot --json > "$TMP"; python3 -c "
import json,sys; print(json.load(open('$TMP'))['result']['snapshot']['treeText'])"; }

find_idx() { tree | python3 -c "
import re,sys
pat=sys.argv[1]
for l in sys.stdin:
    m=re.match(r'\s*(\d+) (.*)',l)
    if m and re.search(pat,m.group(2)): print(m.group(1)); break" "$1"; }

ok() { python3 -c "import json,sys;d=json.load(sys.stdin);print('$1',d.get('ok'),d.get('error') or '')"; }

shot() {
  orca computer get-app-state $A --restore-window --json > "$TMP" 2>&1
  python3 - "$TMP" "$SHOTS/$1.png" "${2:-40}" <<'PY'
import json,sys,shutil
d=json.load(open(sys.argv[1]))
if not d.get('ok'): print(d.get('error')); sys.exit(1)
r=d['result']; shutil.copy(r['screenshot']['path'], sys.argv[2])
print(sys.argv[2], r['screenshot']['width'], 'x', r['screenshot']['height'], 'scale', r['screenshot'].get('scale'))
print('\n'.join(r['snapshot']['treeText'].splitlines()[:int(sys.argv[3])]))
PY
}

case ${1:-} in
  windows) orca computer list-windows --app com.google.Chrome --json ;;
  tree) tree | head -n "${2:-80}" ;;
  shot) shot "$2" "${3:-40}" ;;
  go)
    i=$(find_idx 'text field.*Address and search bar'); orca computer click $A --element-index "$i" --restore-window --no-screenshot --json | ok click
    sleep 0.5
    i=$(find_idx 'text field.*Address and search bar'); orca computer set-value $A --element-index "$i" --value "$2" --no-screenshot --json | ok set
    orca computer press-key $A --key Return --restore-window --no-screenshot --json | ok enter
    sleep "${4:-4}"; [ -n "${3:-}" ] && shot "$3" 1 ;;
  press)
    i=$(find_idx "$2"); [ -z "$i" ] && { echo "not found: $2"; exit 1; }
    orca computer click $A --element-index "$i" --no-screenshot --json | ok press
    sleep "${4:-1.5}"; [ -n "${3:-}" ] && shot "$3" 1 ;;
  key)
    case $2 in
      *+*) orca computer hotkey $A --key "$2" --restore-window --no-screenshot --json | ok hotkey ;;
      *) orca computer press-key $A --key "$2" --restore-window --no-screenshot --json | ok key ;;
    esac ;;
  *) sed -n '2,10p' "$0"; exit 1 ;;
esac
