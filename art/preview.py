"""Contact sheet: raw image (left) next to its pixelated sprite(s) scaled up with nearest neighbour.
Usage: python3 art/preview.py out.png slug [slug ...]"""
import sys
from pathlib import Path
from PIL import Image
ROOT = Path(__file__).resolve().parent.parent
out, slugs = sys.argv[1], sys.argv[2:]
H = 256
rows = []
for s in slugs:
    raw = Image.open(ROOT / 'art/raw' / f'{s}.png').convert('RGB').resize((H, H))
    tiles = [raw]
    for f in (f'{s}.png', f'{s}@64.png'):
        p = ROOT / 'sprites' / f
        if p.exists():
            sp = Image.open(p)
            bg = Image.new('RGBA', (H, H), (169, 147, 91, 255))
            bg.alpha_composite(sp.resize((H, H), Image.NEAREST))
            tiles.append(bg.convert('RGB'))
    row = Image.new('RGB', (H * 3 + 16, H), (18, 23, 53))
    for i, t in enumerate(tiles):
        row.paste(t, (i * (H + 8), 0))
    rows.append(row)
sheet = Image.new('RGB', (rows[0].width, len(rows) * (H + 8)), (18, 23, 53))
for i, r in enumerate(rows):
    sheet.paste(r, (0, i * (H + 8)))
sheet.save(out)
