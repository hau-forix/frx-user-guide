#!/bin/bash
# bash render_check.sh <guide.docx> <out_dir> [expected_pages]
# docx -> PDF (Microsoft Word via AppleScript) -> one PNG per page + contact sheets.
# Prints the page count; exits 2 if it differs from expected_pages (a page overflowed).
set -euo pipefail
DOCX=$(cd "$(dirname "$1")" && pwd)/$(basename "$1")
OUT=$2; EXPECT=${3:-}
HERE=$(cd "$(dirname "$0")" && pwd)
mkdir -p "$OUT"; OUT=$(cd "$OUT" && pwd)
rm -f "$OUT"/p*.png "$OUT"/sheet*.png

# Word is sandboxed: it can only write inside its container.
BOX="$HOME/Library/Containers/com.microsoft.Word/Data/Documents"
mkdir -p "$BOX"
NAME=$(basename "$DOCX" .docx)
cp "$DOCX" "$BOX/$NAME.docx"
rm -f "$BOX/$NAME.pdf"
osascript <<EOF
tell application "Microsoft Word"
  open file name "$BOX/$NAME.docx"
  delay 4
  save as active document file name "$BOX/$NAME.pdf" file format format PDF
  close active document saving no
end tell
EOF
for _ in 1 2 3 4 5 6 7 8 9 10; do [ -f "$BOX/$NAME.pdf" ] && break; sleep 1; done
[ -f "$BOX/$NAME.pdf" ] || { echo "Word did not write $BOX/$NAME.pdf"; exit 1; }
cp "$BOX/$NAME.pdf" "$OUT/$NAME.pdf"

swift "$HERE/pdf2png.swift" "$OUT/$NAME.pdf" "$OUT" 1.6
python3 "$HERE/contact_sheet.py" "$OUT" "$OUT"/p*.png
PAGES=$(ls "$OUT"/p*.png | wc -l | tr -d ' ')
echo "PDF: $OUT/$NAME.pdf  pages: $PAGES"
if [ -n "$EXPECT" ] && [ "$PAGES" != "$EXPECT" ]; then
  echo "PAGE COUNT MISMATCH: expected $EXPECT. Find the page that spilled over (look at the sheets) and shorten it."
  exit 2
fi
