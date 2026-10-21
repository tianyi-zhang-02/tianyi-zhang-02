"""Sky (ray traced) + planet -> a filmic image with bloom and a little grain.

    [GLOW=0 LX= EXP=] python3 compose.py sky.npy planet out     # writes out.png and out.jpg"""
import os
import sys

import numpy as np
from scipy.ndimage import gaussian_filter
from PIL import Image

sky, ter, out = sys.argv[1], sys.argv[2], sys.argv[3]
HOR = float(os.environ.get("HOR", .86)); LX = float(os.environ.get("LX", .5))
EXP = float(os.environ.get("EXP", 1.6))
img = np.load(sky); h, w, _ = img.shape
rgb = np.load(ter + "-rgb.npy"); a = np.load(ter + "-a.npy")[..., None]
ys = (np.arange(h) + .5)[:, None]; xs = ((np.arange(w) + .5) / w - LX)[None, :]
yh = h * HOR
# atmosphere: a thin warm limb glow just above the horizon, strongest under the hole
up = np.clip(yh - ys, 0, None) / h
glow = np.exp(-up / 0.035) * (0.25 + 0.75 * np.exp(-(xs / 0.30) ** 2))
img = img + (glow * float(os.environ.get("GLOW", .22)))[..., None] * np.array([1.0, 0.80, 0.66])
lin = img * (1 - a) + rgb
bright = np.clip(lin - 0.35, 0, None)
bloom = sum(k * gaussian_filter(bright, (w / d, w / d, 0)) for k, d in ((.5, 400), (.35, 120), (.22, 40)))
lin = lin + bloom
tm = (1 - np.exp(-EXP * lin)) ** (1 / 1.15)
# fine film grain, very light
rng = np.random.default_rng(1)
tm = tm + rng.normal(0, 0.006, tm.shape[:2])[..., None]
im = Image.fromarray((np.clip(tm, 0, 1) * 255 + .5).astype(np.uint8))
im.save(out + ".png"); im.save(out + ".jpg", quality=88, optimize=True, progressive=True)
print("ok", out, os.path.getsize(out + ".jpg"))
