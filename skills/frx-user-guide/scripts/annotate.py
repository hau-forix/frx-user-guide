"""annotate.py <spec.json> [<spec.json> ...]

Crop a raw screenshot and draw Forix guide markers: red rounded box + red numbered circle.

spec:
{
  "src": "shots/directory.png",         # raw screenshot
  "out": "final/01_directory.png",      # annotated PNG that goes into the docx
  "scale": 1.0,     # multiplier from the coords below to raw pixels. 1.0 = coords are raw px
                    # (e.g. from element_rects.js x DPR). If you measured on a downscaled preview,
                    # scale = raw_width / preview_width (2000 px preview of a 3024 px shot -> 1.512).
  "crop": [x1, y1, x2, y2],   # optional, same coord space as marks
  "pad": 6,                   # grow every box by this much (coord space) so it doesn't hug the text
  "up": 1,                    # upscale the crop (use 2 for small/low-res shots)
  "maxw": 1800,               # final max width in px (keeps the docx small)
  "marks": [{"box": [x1, y1, x2, y2], "n": 1, "at": "tl|tr|bl|br|l|r", "pad": 6}]
}
Same "n" on several boxes = one feature in several places: every box is drawn, the circle only once.
"""
import json
import sys

from PIL import Image, ImageDraw, ImageFont

RED = (220, 30, 45)
WHITE = (255, 255, 255)


def annotate(spec):
    k = spec.get('scale', 1.0)
    im = Image.open(spec['src']).convert('RGB')
    if 'crop' in spec:
        cx1, cy1, cx2, cy2 = [v * k for v in spec['crop']]
    else:
        cx1, cy1, cx2, cy2 = 0, 0, im.width, im.height
    im = im.crop((int(cx1), int(cy1), int(cx2), int(cy2)))
    up = spec.get('up', 1)
    if up != 1:
        im = im.resize((int(im.width * up), int(im.height * up)), Image.LANCZOS)

    # stroke / circle sized from the output width so markers look the same on every image
    ref = min(im.width, 3000)
    W = max(4, round(ref / 300))
    R = max(18, round(ref / 60))
    try:
        fnt = ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial Bold.ttf', round(R * 1.25))
    except OSError:
        fnt = ImageFont.load_default()

    d = ImageDraw.Draw(im)
    circles = []
    seen = set()
    for m in spec['marks']:
        pad = m.get('pad', spec.get('pad', 6))
        bx = [m['box'][0] - pad, m['box'][1] - pad, m['box'][2] + pad, m['box'][3] + pad]
        x1, y1, x2, y2 = [v * k for v in bx]
        x1, x2 = (x1 - cx1) * up, (x2 - cx1) * up
        y1, y2 = (y1 - cy1) * up, (y2 - cy1) * up
        d.rounded_rectangle((x1, y1, x2, y2), radius=W * 2, outline=RED, width=W)
        if m['n'] in seen:
            continue
        seen.add(m['n'])
        at = m.get('at', 'tl')
        cx, cy = {'tl': (x1 - 8, y1 - 8), 'tr': (x2 + 8, y1 - 8), 'bl': (x1 - 8, y2 + 8), 'br': (x2 + 8, y2 + 8),
                  'l': (x1 - R - 6, (y1 + y2) / 2), 'r': (x2 + R + 6, (y1 + y2) / 2)}[at]
        cx = min(max(cx, R + 2), im.width - R - 2)
        cy = min(max(cy, R + 2), im.height - R - 2)
        circles.append((cx, cy, m['n']))
    for cx, cy, n in circles:  # circles last so a later box never cuts through a number
        d.ellipse((cx - R, cy - R, cx + R, cy + R), fill=RED, outline=WHITE, width=max(3, W // 2 + 1))
        d.text((cx, cy + 1), str(n), fill=WHITE, font=fnt, anchor='mm')

    maxw = spec.get('maxw', 1800)
    if im.width > maxw:
        im = im.resize((maxw, int(im.height * maxw / im.width)), Image.LANCZOS)
    im.save(spec['out'], optimize=True)
    print(spec['out'], im.size)


if __name__ == '__main__':
    for path in sys.argv[1:]:
        with open(path) as f:
            annotate(json.load(f))
