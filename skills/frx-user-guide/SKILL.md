---
name: frx-user-guide
description: Use when the user asks for a Forix user guide or "hướng dẫn sử dụng" for a Forix dashboard or internal tool (hub.forixweb.com, VNPM, Clients Dashboard, Daily Snapshots...), wants annotated screenshots in a Word/.docx guide that imports into Google Docs, or wants to add or change pages in an existing *-User-Guide.docx.
argument-hint: "<product or URL> [new | update <path-to-existing.docx>]"
---

# Forix user guide (.docx)

Produces the house-style guide: A4 landscape, one page per screen, text left / annotated screenshot right,
Montserrat throughout, Forix green, cover with TOC, real heading styles, Word-rendered check before delivery.

**Headings are real Word styles** (Title, Subtitle, Heading 1-3, mapped in the `guide_lib` docstring), so they show in
Word's Navigation pane and the Google Docs outline. Use only the lib helpers for titles and labels: a title written
with `p('**...**')` is not a heading.
Proven on the VNPM Dashboard and Clients Dashboard guides.

`SK` below = this skill's base directory (printed as "Base directory for this skill" when it loads; the author's copy
is `~/.claude/skills/frx-user-guide/skills/frx-user-guide`, a marketplace install lives under `~/.claude/plugins/cache/`). Start every shell with
`export SK=<that path>`; the example script reads `$SK`. Work in the session scratchpad (`$WORK`).

## Inputs (ask once, in one AskUserQuestion, only what is not already given)

1. Product + URL, and **new guide** or **update** of an existing .docx.
2. Audience. Default: PM/USPM daily users; admin features get one short page at the end.
   Scope: full product guide (default) or a quick guide for one feature. A quick guide skips Basics and the
   roles page, keeps a short FAQ, uses `g.cover(..., subtitle='Quick Guide')` and is named
   `<Product>-<Feature>-Quick-Guide.docx`.
3. Capture: prod Chrome now, or text first. Read `references/capture.md` for the routes.

## New guide

1. **Facts first.** Dispatch a subagent to read the app's frontend + backend for each screen: what shows and when,
   every button and what it does, permissions per role, refresh schedules, exact UI strings. Ask it to list
   places where UI text and behaviour disagree. Write from this fact sheet, not from screenshots.
   Every number on the cover (sources, refresh times) must come from it; drop a row you can't source.
2. **Outline.** Cover + one page per screen in the order a user meets them + Reference (roles, FAQ).
   Show the outline in chat (titles only) and wait for the go-ahead.
3. **Capture + annotate** per `references/capture.md`. Read every contact sheet.
4. **Write.** Copy `SK/examples/sample_guide.py` to `$WORK/guide.py`, keep its shape
   (`plan()` → `cover()` → one `g.page()` per TOC row), replace the content. Follow `references/writing-style.md`.
5. **Build + check:**
   ```bash
   python3 $WORK/guide.py $WORK/final $WORK/out/<Product>-User-Guide.docx
   V=$(find ~/.claude -path '*docx/scripts/office/validate.py' 2>/dev/null | head -1)   # docx skill's validator, optional
   [ -n "$V" ] && (cd "$(dirname "$V")" && python3 validate.py $WORK/out/<Product>-User-Guide.docx)
   bash SK/scripts/render_check.sh $WORK/out/<Product>-User-Guide.docx $WORK/render <1 + number of pages>
   ```
   Read every `render/sheet*.png`. A page count mismatch means a page spilled: fix it (writing-style.md, length budget) and rerun.
   The render check always runs, every build. Word briefly opens a window; it is not activated, so the user's typing is safe.
   Montserrat Regular + Bold must be installed (`ls ~/Library/Fonts | grep -i montserrat`), or Word renders a fallback
   font and the page check is wrong. Missing: download the static TTFs from github.com/JulietaUla/Montserrat
   (fonts/ttf) into `~/Library/Fonts`, quit Word (check no document is open first) and rerun.
6. **Deliver** to `~/Downloads/<Product>-User-Guide.docx` (+ the PDF from render). If the file exists, `cp -n` it to
   `<name>.backup.docx` first. Tell the user: page count, that screenshots show real client data, and
   Google Docs import = Drive → New → File upload → Open with Google Docs.

## Update an existing guide

Keep the user's own edits: edit the shipped file, never regenerate it from scratch.
Guides made before 2026-10-16 (VNPM, Clients Dashboard) use Poppins/Arial and have no heading styles. New blocks from
`guide_lib` come out in Montserrat with heading styles; ask the user whether to restyle the whole file before mixing.

**Restyle a legacy guide** (Montserrat + headings, content untouched):
```python
import sys, os; sys.path.insert(0, os.path.join(os.environ['SK'], 'scripts')); import guide_lib as g
g.restyle_legacy('$WORK/in.docx', '$WORK/out.docx')   # template defaults to SK/assets/forix-guide-template.docx
```
It prints heading counts (VNPM: Title 1, Subtitle 1, Heading1 13, Heading2 29, Heading3 6) and also removes the empty
paragraph that pushed old covers onto a blank page 2. Render the **original too**: compare page counts and check that
the TOC page numbers match the rendered pages (old VNPM file rendered 15 pages for a 14-page TOC).
Validator: run with `--original <in.docx>`; old files already carry tblLayout/tcMar/zoom schema warnings that Word ignores.
Backup with a dated name (`<name>.backup-YYYY-MM-DD.docx`) when a `.backup.docx` already exists.

1. `cp -n guide.docx guide.backup.docx`, unzip to `$WORK/x`, read `word/document.xml` around the target page.
2. Build new blocks with `guide_lib` helpers (same look) and splice them in with `insert_after` / `start_of`.
   Anchors are visible strings like `'>Client directory<'`; a TOC label appears twice (TOC row first, page title
   second), so pass `occurrence=0` / `occurrence=1`. New page: find its successor's title with `start_of(...)`,
   step back one `<w:p>` to the eyebrow, insert there.
3. New images: copy into `word/media/`, add a rels entry with a fresh rId, a unique `docPr id`; match the existing marker style.
4. Added or removed a page: `bump_page_numbers(doc, '>label before the new page<')`, then
   `add_toc_row(doc, after_label, label, page)`, then grep every "page N" in body text and fix by hand.
   A 16+ row TOC fills the cover: trim cover text so it still fits.
5. Re-zip with `guide_lib.write_docx(src, dst, {...})` (or `zip -X -D`), then the same validate + `render_check.sh`.

## Common mistakes

| Mistake | Fix |
|---|---|
| Vietnamese text or technical terms in the guide | English, user language only |
| TOC numbers typed by hand drift | `g.plan()` + `g.pg()` / `g.toc_rows()`; the build asserts page order |
| "Looks fine" without rendering | `render_check.sh` with the expected page count, read the sheets |
| Clicking write buttons on prod while capturing | Read-only; open dialogs and Escape |
| `activate` in the Word AppleScript, hidden (`.name`) files | Never; the script handles this |
| Full-window screenshots, unreadable when printed | Crop tight to the marked area |
| python-docx not installed | Not needed: guide_lib writes OOXML on the bundled template (only Pillow required) |
| Hard-coding `f='Arial'` / Poppins in a run | Leave `f` out; `FONT = 'Montserrat'` is the default everywhere |
| Bold paragraph used as a section title | `heading()` / `label()` / `qa()`, so it lands in the outline |

## Files

- `scripts/guide_lib.py` — blocks (`p note label bullet numbered cap qa data_table callout subheading`), `Guide` (plan / cover / page / image / build), update helpers.
- `scripts/annotate.py`, `scripts/element_rects.js`, `scripts/contact_sheet.py`, `scripts/chrome.sh` — screenshots.
- `scripts/render_check.sh` (+ `pdf2png.swift`) — Word → PDF → page PNGs + sheets, page-count gate.
- `assets/forix-guide-template.docx` — Montserrat styles (Normal, Title, Subtitle, Heading 1-3 in Forix colours), header "<Product> · User guide · <Month Year>", "Page N" footer.
- `examples/sample_guide.py` — 8-page worked example for a made-up product (Order Desk); draws grey placeholders
  for missing screenshots, so it builds with an empty image folder. Delete `placeholders()` in a real guide.
