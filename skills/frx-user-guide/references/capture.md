# Capturing and annotating screenshots

## Pick the capture route

| Situation | Route |
|---|---|
| Prod hub (hub.forixweb.com/...), needs the user's Google sign-in | User's own Chrome via Orca computer-use: `bash scripts/chrome.sh ...`. **REQUIRED SUB-SKILL:** computer-use |
| Local dev server (localhost:...) or the page can be opened in Orca's browser | Orca embedded browser (tabs, eval, page screenshot). **REQUIRED SUB-SKILL:** orca-cli. Lets you run `element_rects.js` for exact boxes |
| User says which tool to use | Use that one |

Before capturing on the user's Chrome: ask them to stay off Chrome for ~15 minutes (a tab switch mid-run sends clicks to the wrong page). Offer "capture now" vs "write text first".

## Safety on production

- Read-only. Never click Done, Save, Add, Create, Delete, Report, Mark, Disconnect or anything that writes.
  To show a dialog, open it and close it with **Escape**.
- Screenshots contain real client names and ticket text. Say so when delivering; the guide is internal.
- To find a client with data for every section (risks, notes, mood), a read-only query is fine; never write.

## Chrome recipe (Orca computer-use)

```bash
export FRX_SHOTS=$WORK/shots
bash scripts/chrome.sh windows                      # pick the window id
export FRX_WIN=<id>
bash scripts/chrome.sh go "https://hub.forixweb.com/clients/home" directory 5
bash scripts/chrome.sh key "CmdOrCtrl+-"            # zoom out: 80% normal pages, 50% wide tables
bash scripts/chrome.sh press "link Billing" billing # AXPress by accessibility-tree regex, then shot
bash scripts/chrome.sh key "CmdOrCtrl+0"            # reset zoom at the end
```

- Element indexes go stale after every action; `press`/`go` refetch the tree each time.
- `CmdOrCtrl+-` works, `CmdOrCtrl+Minus` does not.
- `orca computer scroll` may do nothing: click a heading, then `key Page_Down` / arrow keys.
- Dropdowns: `set-value`, then click the option. Typing + Return may not apply.
- Lazy sections may be missing from the tree until loaded: wait, press again.
- Raw shots are usually Retina (2x, e.g. 3024 px wide) but can come back 1x (1280 px). Check the real size
  (`shot` prints it) before choosing `scale` / `up`: `up: 2` for 1x shots.
- macOS has no `timeout`; use bash `sleep` loops. zsh doesn't word-split `$A`, so scripts are bash.

## Annotate

1. Get boxes. Best: run `scripts/element_rects.js` in the page (DOM rects × DPR = raw px, `scale: 1`).
   Otherwise read coords off the image as the Read tool shows it. The Read tool states the display size when it
   downscales ("displayed at 2000x1500, multiply by 1.40"); use that factor as `scale`, else `scale: 1`.
   For eyeballing, overlay a 100 px grid on the preview first.
2. One spec JSON per image (format in `scripts/annotate.py` docstring), number markers in reading order,
   ≤ 7 per image. Same number on several boxes = same feature in several places.
   Circle position `at`: put it on the side with empty space. Buttons/inputs in a row → `l` or `r`;
   a box with a label above-left (titles, "Last refreshed") → `tr`; wide rows → `l` at the left edge.
3. `python3 scripts/annotate.py specs/*.json` → `final/NN_name.png` (NN = page order).
4. `python3 scripts/contact_sheet.py $WORK/sheets final/*.png` (never into `final/`, the build would pick the
   sheets up) and Read every sheet; with 1-2 images Read the PNGs directly. Is each box on its target,
   does any number cover text, is the crop tight? Fix specs, rerun.

Crop tight to the boxes: a full-window shot prints too small to read. Wide tables: capture at lower browser
zoom, then crop to the columns the captions talk about rather than the full width. When updating an existing guide,
match its marker style (sample stroke and circle size from its images in `word/media/`) instead of the defaults.
