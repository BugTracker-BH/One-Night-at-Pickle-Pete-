#!/usr/bin/env python3
"""Shrink opaque PNGs via palette quantization. Transparent overlays are left
untouched (their alpha must be preserved). Run after gen_images.py."""
import glob, os
from PIL import Image

def opaque(im):
    if im.mode != 'RGBA': return True
    lo, hi = im.getchannel('A').getextrema()
    return lo == 255

tot_before = tot_after = 0
for f in sorted(glob.glob(os.path.join(os.path.dirname(__file__), '..', 'assets', 'img', '*.png'))):
    before = os.path.getsize(f); tot_before += before
    im = Image.open(f)
    if opaque(im):
        rgb = im.convert('RGB')
        # adaptive palette; grain dithers nicely at 128 colors
        q = rgb.quantize(colors=128, method=Image.MEDIANCUT, dither=Image.FLOYDSTEINBERG)
        q.save(f, optimize=True)
    else:
        im.save(f, optimize=True)
    after = os.path.getsize(f); tot_after += after
    if before > 1_000_000:
        print(f'{os.path.basename(f):24} {before/1e6:6.1f} -> {after/1e6:5.2f} MB')
print(f'TOTAL img {tot_before/1e6:.1f} -> {tot_after/1e6:.1f} MB')
