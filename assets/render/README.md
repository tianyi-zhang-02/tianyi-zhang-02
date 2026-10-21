# Rendering the banner pictures

The four JPEGs here are the backgrounds that `../make_night_banner.py` embeds into the SVGs. They are rendered
once, offline, with plain NumPy and SciPy (no GPU), and committed so the SVGs can be regenerated without
rendering again.

| File | Size (2x) | Used by |
| --- | --- | --- |
| `banner.jpg` | 2400 × 1000 | `night-banner*.svg` |
| `banner-mobile.jpg` | 1200 × 1360 | `night-banner-mobile*.svg` |
| `card.jpg` | 1760 × 400 | `card-notes*.svg` |
| `card-mobile.jpg` | 1200 × 540 | `card-notes-mobile*.svg` |

- `raytrace.py` traces light around a Schwarzschild black hole (with a thin accretion disk, Doppler beaming and an
  infalling stream) against a procedural starfield. The distortion of the disk and of the stars is gravitational
  lensing, not an effect drawn on top.
- `planet.py` draws the icy planet's limb, lit from above and behind by the hole.
- `compose.py` puts the two together and adds bloom and a little grain.

`render.sh` holds the exact settings. Each picture is supersampled 3 × 3, and the full set takes about half an hour
on a laptop.

```sh
bash assets/render/render.sh
python3 assets/make_night_banner.py
```
