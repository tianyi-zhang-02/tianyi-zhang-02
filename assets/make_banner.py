#!/usr/bin/env python3
"""Generate the profile banner: a trace that starts as noise and resolves into signal.

Deterministic (fixed seed) so re-running produces a byte-identical file and the
diff stays empty unless the design actually changed.

    python assets/make_banner.py
"""

import math
import random

W, H = 1200, 200
BASE = H / 2
X0, X1 = 30, W - 30
STEP = 2

THEMES = {
    "light": {
        "noise": "#C2C4BD",
        "signal": "#1E3EC8",
        "dot": "#1E3EC8",
        "label": "#8A8D93",
    },
    "dark": {
        "noise": "#3B3E47",
        "signal": "#9DAEFF",
        "dot": "#9DAEFF",
        "label": "#80838B",
    },
}


def trace(seed=7):
    """Noise amplitude decays left→right while a clean wave takes over."""
    rng = random.Random(seed)
    pts = []
    x = X0
    while x <= X1:
        t = (x - X0) / (X1 - X0)
        noise = rng.uniform(-1, 1) * 76 * (1 - t) ** 2.6
        wave = 38 * (t ** 1.2) * math.sin((x - X0) / 62.0)
        pts.append((x, BASE + noise + wave))
        x += STEP
    return pts


def specks(seed=11, n=110):
    """Scattered points that thin out as the signal emerges."""
    rng = random.Random(seed)
    out = []
    for _ in range(n):
        t = rng.random() ** 1.8          # bunched toward the noisy left
        x = X0 + t * (X1 - X0)
        y = BASE + rng.uniform(-1, 1) * 82 * (1 - t) ** 2.0
        out.append((x, y, 0.9 * (1 - t) ** 1.2))
    return out


def build(theme):
    c = THEMES[theme]
    pts = trace()
    d = " ".join(f"{'M' if i == 0 else 'L'}{x:.1f} {y:.1f}" for i, (x, y) in enumerate(pts))

    dots = "\n".join(
        f'  <circle cx="{x:.1f}" cy="{y:.1f}" r="1.5" fill="{c["noise"]}" opacity="{o:.2f}"/>'
        for x, y, o in specks()
        if o > 0.06
    )

    # the wave settles into a steady rhythm — mark where it stops being noise
    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" role="img" aria-label="A trace that begins as noise on the left and resolves into a clean periodic signal on the right">
  <defs>
    <linearGradient id="fade" x1="0" y1="0" x2="1" y2="0">
      <stop offset="0.00" stop-color="{c['noise']}"/>
      <stop offset="0.30" stop-color="{c['noise']}"/>
      <stop offset="0.62" stop-color="{c['signal']}"/>
      <stop offset="1.00" stop-color="{c['signal']}"/>
    </linearGradient>
  </defs>
{dots}
  <path d="{d}" fill="none" stroke="url(#fade)" stroke-width="1.7"
        stroke-linecap="round" stroke-linejoin="round"/>
  <circle cx="{X1:.0f}" cy="{BASE:.0f}" r="4" fill="{c['dot']}"/>
  <text x="{X0}" y="{H - 12}" font-family="ui-monospace, SFMono-Regular, Menlo, Consolas, monospace"
        font-size="12" letter-spacing="2.2" fill="{c['label']}">NOISE</text>
  <text x="{X1}" y="{H - 12}" text-anchor="end" font-family="ui-monospace, SFMono-Regular, Menlo, Consolas, monospace"
        font-size="12" letter-spacing="2.2" fill="{c['signal']}">SIGNAL</text>
</svg>
'''


if __name__ == "__main__":
    import pathlib

    here = pathlib.Path(__file__).parent
    for theme in THEMES:
        path = here / f"banner-{theme}.svg"
        path.write_text(build(theme))
        print(f"wrote {path.relative_to(here.parent)}")
