# frx-user-guide

Claude Code plugin that writes Forix user guides: A4 landscape .docx, one page per screen, text left and an
annotated screenshot right, Montserrat, Forix green, real heading styles, cover with table of contents.
The .docx imports into Google Docs (Drive → New → File upload → Open with Google Docs).

## Use

```
/frx-user-guide <product or URL> [new | update <path-to-existing.docx>]
```

Or just ask: "viết user guide cho VNPM Dashboard", "thêm trang Calendar vào guide".

## Install (teammates)

```bash
claude plugin marketplace add hau-forix/frx-user-guide
claude plugin install frx-user-guide@forix
```

## Requirements (macOS)

- Microsoft Word (renders the page check), Python 3 + Pillow (`pip3 install pillow`), Xcode command line tools (`swift`).
- Montserrat Regular + Bold in `~/Library/Fonts` (static TTFs from github.com/JulietaUla/Montserrat, `fonts/ttf`).
- Screenshots of hub.forixweb.com: Orca computer-use or Orca browser (see `references/capture.md`).

Guides contain screenshots with real client data: internal use only.
