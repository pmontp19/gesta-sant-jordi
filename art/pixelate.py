"""Snap a generated image (art/raw/<slug>.png, flat magenta background) to a real pixel grid.

Usage: python3 art/pixelate.py <slug> [--big]
Writes sprites/<slug>.png (32x32 RGBA) and, with --big, sprites/<slug>@64.png too.
The subject is reduced to a 24-colour palette first; each output pixel takes the dominant palette colour of its cell
(dark colours weigh more, so outlines survive). A cell is opaque when most of it is subject.
A flat non-magenta background (the model sometimes paints it black) is removed by flood fill from the border; exits 2 otherwise.
"""
import sys
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parent.parent
COLORS = 24
DARK_BOOST = 0.3  # extra vote weight for dark palette colours (outlines)


def subject_mask(rgb):
    r, g, b = (rgb[..., i].astype(int) for i in range(3))
    # magenta-ish = high red and blue, low green (models drift off pure #FF00FF)
    magenta = (r > 150) & (b > 150) & (g < 110) & (abs(r - b) < 90)
    return ~magenta


def snap(img, size, mask=None):
    rgb = np.asarray(img.convert('RGB'))
    mask = subject_mask(rgb) if mask is None else mask
    ys, xs = np.nonzero(mask)
    y0, y1, x0, x1 = ys.min(), ys.max() + 1, xs.min(), xs.max() + 1
    # square crop around the subject with a small margin, bottom-aligned so figures stand on the tile
    side = int(max(y1 - y0, x1 - x0) * 1.06)
    cx = (x0 + x1) // 2
    top, left = y1 - side + int(side * 0.03), cx - side // 2
    # palette first (subject pixels only), so every output pixel is a clean palette colour
    pal_img = Image.fromarray(rgb[mask][None, :, :], 'RGB').quantize(COLORS, method=Image.Quantize.MEDIANCUT)
    pal = np.asarray(pal_img.getpalette()[:COLORS * 3], np.float64).reshape(-1, 3)
    idx = np.full(rgb.shape[:2], -1, np.int16)
    idx[mask] = np.asarray(pal_img)[0]
    # dark colours win ties more easily: keeps outlines, eyes and seams at low resolution
    lum = pal @ np.array([.299, .587, .114])
    weight = 1 + DARK_BOOST * (lum < 70)
    edges_y = np.linspace(top, top + side, size + 1).astype(int)
    edges_x = np.linspace(left, left + side, size + 1).astype(int)
    out = np.zeros((size, size, 4), np.uint8)
    H, W = idx.shape
    for j in range(size):
        for i in range(size):
            ya, yb = max(edges_y[j], 0), min(edges_y[j + 1], H)
            xa, xb = max(edges_x[i], 0), min(edges_x[i + 1], W)
            area = (edges_y[j + 1] - edges_y[j]) * (edges_x[i + 1] - edges_x[i])
            if ya >= yb or xa >= xb:
                continue
            cell = idx[ya:yb, xa:xb]
            sub = cell[cell >= 0]
            if sub.size <= area * 0.45:
                continue
            votes = np.bincount(sub, minlength=len(pal)) * weight
            out[j, i] = (*pal[int(np.argmax(votes))].astype(np.uint8), 255)
    return Image.fromarray(out, 'RGBA')


def border(rgb):
    return np.concatenate([rgb[0], rgb[-1], rgb[:, 0], rgb[:, -1]])


def background_ok(img):
    """The prompt asks for flat magenta; refuse images whose border isn't mostly magenta."""
    return (~subject_mask(border(np.asarray(img.convert('RGB')))[None])[0]).mean() > 0.9


def flat_border(img):
    """Fallback when the model ignored the magenta request but still used one flat colour (often pure black)."""
    b = border(np.asarray(img.convert('RGB'))).astype(int)
    return (np.abs(b - np.median(b, 0)).max(1) <= 12).mean() > 0.9


def flood_mask(img):
    """Background = pixels connected to the border with the border colour; dark pixels inside the figure stay."""
    work = img.convert('RGB').copy()
    w, h = work.size
    sentinel = (1, 254, 3)
    for x in range(0, w, 8):
        for y in (0, h - 1):
            if work.getpixel((x, y)) != sentinel:
                ImageDraw.floodfill(work, (x, y), sentinel, thresh=12)
    for y in range(0, h, 8):
        for x in (0, w - 1):
            if work.getpixel((x, y)) != sentinel:
                ImageDraw.floodfill(work, (x, y), sentinel, thresh=12)
    a = np.asarray(work)
    return ~((a[..., 0] == 1) & (a[..., 1] == 254) & (a[..., 2] == 3))


def main():
    slug, big = sys.argv[1], '--big' in sys.argv
    src = Image.open(ROOT / 'art' / 'raw' / f'{slug}.png')
    mask = None
    if not background_ok(src):
        if not flat_border(src):
            print(f'✗ {slug}: background is neither magenta nor flat')
            sys.exit(2)
        mask = flood_mask(src)
    snap(src, 32, mask).save(ROOT / 'sprites' / f'{slug}.png')
    if big:
        snap(src, 64, mask).save(ROOT / 'sprites' / f'{slug}@64.png')
    print(f'✓ {slug}' + (' (+64)' if big else ''))


if __name__ == '__main__':
    main()
