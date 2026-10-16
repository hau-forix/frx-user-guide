"""contact_sheet.py <out_dir> <img> [<img> ...]  -> out_dir/sheet0.png, sheet1.png ... (2x2 grids, labelled)

Use it twice: on final/*.png to check every annotated screenshot, and (via render_check.sh) on
rendered pages to check layout. Read the sheets with the Read tool instead of each image one by one.
"""
import os
import sys

from PIL import Image, ImageDraw, ImageFont

out_dir, files = sys.argv[1], sys.argv[2:]
os.makedirs(out_dir, exist_ok=True)
CELL_W, CELL_H, COLS, ROWS = 1400, 1000, 2, 2
try:
    fnt = ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial Bold.ttf', 34)
except OSError:
    fnt = ImageFont.load_default()
per = COLS * ROWS
for s in range(0, len(files), per):
    sheet = Image.new('RGB', (CELL_W * COLS, (CELL_H + 50) * ROWS), 'white')
    d = ImageDraw.Draw(sheet)
    for i, f in enumerate(files[s:s + per]):
        im = Image.open(f).convert('RGB')
        im.thumbnail((CELL_W - 20, CELL_H - 20))
        x, y = (i % COLS) * CELL_W, (i // COLS) * (CELL_H + 50)
        sheet.paste(im, (x + 10, y + 50))
        d.rectangle((x + 10, y + 50, x + 10 + im.width, y + 50 + im.height), outline=(180, 180, 180), width=2)
        d.text((x + 12, y + 8), os.path.basename(f), fill=(0, 0, 0), font=fnt)
    p = os.path.join(out_dir, f'sheet{s // per}.png')
    sheet.save(p)
    print(p)
