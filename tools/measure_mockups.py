#!/usr/bin/env python3
"""Print the transparent screen hole (x, y, w, h) in each mockup PNG.
Run after replacing a mockup file, then update MOCKUPS in render.py."""
from pathlib import Path
import numpy as np
from PIL import Image
from scipy import ndimage  # pip3 install scipy

for f in sorted((Path(__file__).resolve().parent.parent / "brand").glob("mockup-*.png")):
    a = np.array(Image.open(f).convert("RGBA"))[..., 3] < 20
    lab, n = ndimage.label(a)
    H, W = a.shape
    for i, sl in enumerate(ndimage.find_objects(lab), 1):
        y, x = sl
        if x.start > 0 and y.start > 0 and x.stop < W and y.stop < H and (lab[sl] == i).sum() > 5000:
            print(f.name, (x.start, y.start, x.stop - x.start, y.stop - y.start))
