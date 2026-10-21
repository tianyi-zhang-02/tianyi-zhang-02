"""A pale icy planet seen from orbit, only its upper limb in frame, lit from above and behind by the hole:
banded ice-cloud texture on the sphere, a soft terminator, a bright crescent at the limb and a thin
atmosphere outside it.

    [PR= TOP= LX= LBACK= TEX= KS= SS=] python3 planet.py W H out

Writes out-rgb.npy (linear light, additive outside the disc) and out-a.npy (coverage)."""
import os
import sys

import numpy as np

W, H, OUT = int(sys.argv[1]), int(sys.argv[2]), sys.argv[3]
E = lambda k, d: float(os.environ.get(k, d))
SS = int(E("SS", 3))
Wr, Hr = W * SS, H * SS
u1 = Wr / 1200.0                                   # px per 1x unit
R = E("PR", 2600) * u1                             # planet radius (1x units)
CX = E("LX", .5) * Wr
TOP = E("TOP", .835) * Hr                          # where the limb crosses the centre column
CY = TOP + R
ATM = E("ATM", 16) * u1                            # atmosphere thickness


def hashf(i, j, k, s):
    h = (i * 73856093) ^ (j * 19349663) ^ (k * 83492791) ^ (s * 2654435761)
    h = (h ^ (h >> 13)) * 1274126177
    h = h ^ (h >> 16)
    return (h & 0xFFFFFF).astype(np.float64) / 0xFFFFFF


def vnoise(p, s):
    i = np.floor(p).astype(np.int64); f = p - i
    u = f * f * (3 - 2 * f)
    acc = 0
    for dx in (0, 1):
        for dy in (0, 1):
            for dz in (0, 1):
                w = (u[..., 0] if dx else 1 - u[..., 0]) * (u[..., 1] if dy else 1 - u[..., 1]) * (u[..., 2] if dz else 1 - u[..., 2])
                acc = acc + w * hashf(i[..., 0] + dx, i[..., 1] + dy, i[..., 2] + dz, s)
    return acc


def fbm(p, s, oct=6, foot=None):
    out, tot, a, f = 0.0, 0.0, 1.0, 1.0
    for o in range(oct):
        w = 1.0 if foot is None else np.clip(1.5 - 2.5 * f * foot, 0, 1)
        out = out + a * (w * vnoise(p * f + 7.1 * o, s + o) + (1 - w) * 0.5)
        tot += a; f *= 2.03; a *= .52
    return out / tot


def rows(rng_):
    r0, r1 = rng_
    ys = np.arange(r0, r1) + .5; xs = np.arange(Wr) + .5
    Y, X = np.meshgrid(ys, xs, indexing="ij")
    dxp, dyp = X - CX, Y - CY
    d = np.sqrt(dxp ** 2 + dyp ** 2)
    inside = d < R
    u, v = dxp / R, -dyp / R                            # v up
    zz = np.sqrt(np.clip(1 - u * u - v * v, 0, 1))
    n = np.stack([u, v, zz], -1)                         # view space, z toward the viewer
    L = np.array([0.0, 1.0, -E("LBACK", .32)]); L /= np.linalg.norm(L)
    ndl = n @ L
    wrap = np.clip((ndl + 0.18) / 1.18, 0, 1) ** 1.6     # soft terminator
    cx = X / Wr - E("LX", .5)
    fwd = np.exp(-(cx / E("FWD", .34)) ** 2)

    # ice-cloud bands: noise on the sphere, stretched along latitude, warped
    tilt = np.radians(E("TILT", 8))
    rot = np.array([[1, 0, 0], [0, np.cos(tilt), -np.sin(tilt)], [0, np.sin(tilt), np.cos(tilt)]])
    p = n @ rot.T
    sc = E("TEX", 1.0) * R / (70 * u1)
    foot = np.clip(sc / (np.maximum(zz, 0.03) * R) * 1.2, 0, 4)
    q = np.stack([p[..., 0] * sc * .35, p[..., 1] * sc * 1.6, p[..., 2] * sc * .35], -1)
    warp = np.stack([fbm(q * .5, 11, 4, foot), fbm(q * .5 + 3, 22, 4, foot), fbm(q * .5 + 6, 33, 4, foot)], -1) - .5
    c = fbm(q + 2.2 * warp, 44, 7, foot)
    bands = 0.5 + 0.5 * np.sin(p[..., 1] * sc * 2.4 + 3 * (c - .5))
    alb = 0.38 + 0.52 * np.clip((c - .32) / .42, 0, 1) ** 1.3 + 0.10 * bands
    cream = np.array([1.0, 0.93, 0.84]); shadow = np.array([0.30, 0.34, 0.44])
    lit = alb * wrap
    rgb_in = (cream * (lit * (0.55 + 0.45 * fwd))[..., None] * E("KS", 1.05)
              + shadow * (alb * (1 - wrap) * 0.10)[..., None])
    # limb brightening: thin atmosphere seen edge-on over the lit crescent
    edge = np.clip((R - d) / u1, 0, None)
    rgb_in += (np.exp(-edge / E("LIMB", 3.5)) * (0.35 + 0.65 * fwd) * 0.9)[..., None] * np.array([1.0, 0.92, 0.82])
    rgb_in *= inside[..., None]
    # atmosphere outside the disc
    hgt = np.clip(d - R, 0, None)
    glow = np.exp(-hgt / ATM) * (0.25 + 0.75 * fwd) * (~inside)
    blue = np.array([0.55, 0.72, 1.0]); warmg = np.array([1.0, 0.82, 0.62])
    mixw = fwd[..., None]
    rgb_out = glow[..., None] * (warmg * mixw + blue * (1 - mixw)) * E("KG", .55)
    rgb = rgb_in + rgb_out

    return rgb.astype(np.float32), inside.astype(np.float32)


if __name__ == "__main__":
    from multiprocessing import Pool
    y0 = int(max(0, TOP - ATM * 14)) // SS * SS
    chunks = [(y, min(Hr, y + 3 * SS)) for y in range(y0, Hr, 3 * SS)]
    with Pool(os.cpu_count()) as pool:
        parts = pool.map(rows, chunks)
    full = np.zeros((Hr, Wr, 3), np.float32); cov = np.zeros((Hr, Wr), np.float32)
    full[y0:] = np.concatenate([p[0] for p in parts], 0); cov[y0:] = np.concatenate([p[1] for p in parts], 0)
    lin = full.reshape(H, SS, W, SS, 3).mean((1, 3)).astype(np.float32)
    a = cov.reshape(H, SS, W, SS).mean((1, 3)).astype(np.float32)
    np.save(OUT + "-rgb.npy", lin); np.save(OUT + "-a.npy", a)
    print("ok", lin.shape, float(lin.max()))
