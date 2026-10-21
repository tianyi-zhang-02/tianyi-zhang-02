"""A Schwarzschild black hole with a thin accretion disk and an infalling stream, ray traced with the
plane-of-orbit trick (x'' = -1.5 h^2 x / r^5, lengths in Schwarzschild radii), over a procedural starfield.

    [HX= HY= SHADOW= ROLL= STREAM= ROUT= SS=] python3 raytrace.py W H out.npy inclination_deg distance

Writes a linear-light float image (H/SS x W/SS x 3). See render.sh for the settings behind each picture."""
import os
import sys
from multiprocessing import Pool

import numpy as np

W, H = int(sys.argv[1]), int(sys.argv[2])
OUT = sys.argv[3]
S = W / 2400.0                       # scale relative to the 2x banner
D = float(sys.argv[5]) if len(sys.argv) > 5 else 40.0     # camera distance
INCL = np.radians(float(sys.argv[4]) if len(sys.argv) > 4 else 4.0)
HOLE = (W * float(os.environ.get("HX", .5)), H * float(os.environ.get("HY", .74)))
F = float(os.environ.get("SHADOW", 80)) / np.arctan(2.598 / D) * S
ROLL = np.radians(float(os.environ.get("ROLL", 0)))
STREAM = float(os.environ.get("STREAM", 0))
R_IN, R_OUT = 3.0, float(os.environ.get("ROUT", 19.0))

cam = np.array([0.0, D * np.sin(INCL), -D * np.cos(INCL)])
fw = -cam / np.linalg.norm(cam)
right = np.cross(np.array([0.0, 1.0, 0.0]), fw); right /= np.linalg.norm(right)
up = np.cross(fw, right)
right, up = np.cos(ROLL) * right + np.sin(ROLL) * up, -np.sin(ROLL) * right + np.cos(ROLL) * up


def hash3(i, j, k):
    h = (i.astype(np.int64) * 73856093) ^ (j.astype(np.int64) * 19349663) ^ (k * 83492791)
    h = (h ^ (h >> 13)) * 1274126177
    h = h ^ (h >> 16)
    return (h & 0xFFFFFF).astype(np.float64) / 0xFFFFFF


def fbm(d, seed, scale=3.0, octaves=5):
    """Cheap smooth noise on the sphere from summed sines of rotated coordinates."""
    rng = np.random.default_rng(seed)
    acc = np.zeros(d.shape[0]); amp = 1.0; tot = 0.0; s = scale
    for _ in range(octaves):
        for _ in range(3):
            k = rng.normal(size=3); k /= np.linalg.norm(k)
            acc += amp * np.sin(s * (d @ k) * 6.0 + rng.uniform(0, 6.28))
            tot += amp
        amp *= 0.55; s *= 2.1
    return 0.5 + 0.5 * acc / tot


def _hashf(i, j, k, s):
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
                w = (u[:, 0] if dx else 1 - u[:, 0]) * (u[:, 1] if dy else 1 - u[:, 1]) * (u[:, 2] if dz else 1 - u[:, 2])
                acc = acc + w * _hashf(i[:, 0] + dx, i[:, 1] + dy, i[:, 2] + dz, s)
    return acc


def vfbm(p, s, oct=5, lac=2.07, gain=.55):
    a, tot, out = 1.0, 0.0, 0.0
    for o in range(oct):
        out = out + a * vnoise(p, s + o); tot += a
        p = p * lac + 11.3; a *= gain
    return out / tot


MW_N = np.array([-0.45, 0.75, -0.5]); MW_N /= np.linalg.norm(MW_N)


def background(d):
    d = d / np.linalg.norm(d, axis=1, keepdims=True)
    lat = np.arcsin(np.clip(d @ MW_N, -1, 1))
    band = np.exp(-(lat / 0.20) ** 2)
    n1 = fbm(d, 1, 2.0); n2 = fbm(d, 2, 5.0, 4)
    dust = 1 - 0.75 * np.exp(-((lat + 0.025) / 0.05) ** 2) * (n2 > 0.48) * np.clip((n2 - 0.48) * 6, 0, 1)
    glow = band * (0.35 + 0.65 * n1 ** 2) * dust
    col = np.stack([0.62 * glow, 0.70 * glow, 0.86 * glow], 1) * 0.055
    # warm core toward one side of the band
    core = np.exp(-(lat / 0.09) ** 2) * np.exp(-(((d @ np.array([0.9, -0.2, 0.38])) - 1) / 0.25) ** 2)
    col += np.stack([core, 0.8 * core, 0.6 * core], 1) * 0.05 * dust[:, None]
    # procedural stars on an equirectangular grid, 3x3 neighbourhood splats
    N = int(5200)
    th = np.arccos(np.clip(d[:, 1], -1, 1)); ph = np.arctan2(d[:, 2], d[:, 0]) + np.pi
    u = ph / (2 * np.pi) * N; v = th / np.pi * (N / 2)
    iu, iv = np.floor(u).astype(np.int64), np.floor(v).astype(np.int64)
    dens = 0.006 * (1 + 1.5 * band)
    stars = np.zeros_like(col)
    for di in (-1, 0, 1):
        for dj in (-1, 0, 1):
            ci, cj = (iu + di) % N, iv + dj
            p = hash3(ci, cj, 1)
            sx = ci + hash3(ci, cj, 2); sy = cj + hash3(ci, cj, 3)
            du = (u - sx + N / 2) % N - N / 2; dv = v - sy
            mag = hash3(ci, cj, 4) ** 9
            sig = 0.20 + 0.22 * mag
            g = np.exp(-(du * du + dv * dv) / (2 * sig * sig)) * (p < dens)
            b = (0.012 + 1.4 * mag) * g
            t = hash3(ci, cj, 5)
            c = np.stack([0.80 + 0.25 * t, 0.86 + 0.06 * t, 1.08 - 0.40 * t], 1)
            stars += b[:, None] * c
    return col + stars


def disk_colour(p, vray):
    r = np.hypot(p[:, 0], p[:, 2])
    x = (r - R_IN) / (R_OUT - R_IN)
    inten = (R_IN / r) ** 1.7 * np.clip(1 - np.sqrt(R_IN / r), 0, 1) ** 0.45 * 4.2
    inten *= np.clip(x / 0.02, 0, 1) * np.clip((1 - x) / 0.35, 0, 1) ** 1.5
    phi = np.arctan2(p[:, 2], p[:, 0])
    # gas sheared along the orbit: fine in radius, long in azimuth, with a slight trailing spiral
    lr = np.log(r)
    sw = phi + 1.4 * lr
    q = np.stack([lr * 16.0, np.cos(sw) * 2.4, np.sin(sw) * 2.4], 1)
    n1 = vfbm(q, 101, 5)
    q2 = np.stack([lr * 46.0, np.cos(sw) * 5.0, np.sin(sw) * 5.0], 1)
    n2 = vfbm(q2, 202, 4)
    tex = 0.42 + 0.95 * np.clip(n1 - 0.5, -0.5, 0.5) + 0.35 * (n2 - 0.5) + 0.58
    tex = np.clip(tex, 0.25, 1.6) ** 1.2
    # doppler beaming, softened
    beta = np.sqrt(0.5 / np.maximum(r - 1.0, 0.5)); beta = np.minimum(beta, 0.6)
    t = np.stack([-p[:, 2], np.zeros_like(r), p[:, 0]], 1) / r[:, None]
    n = -vray / np.linalg.norm(vray, axis=1, keepdims=True)
    gam = 1 / np.sqrt(1 - beta ** 2)
    dop = 1 / (gam * (1 - beta * np.sum(t * n, 1)))
    beam = dop ** 1.1
    grav = np.sqrt(np.clip(1 - 1 / r, 0, 1))
    I = inten * tex * beam * grav
    if STREAM > 0:
        arm = np.angle(np.exp(1j * (phi - (2.4 - 1.9 * np.log(r / R_IN)))))
        st = np.exp(-(arm / 0.20) ** 2) * np.clip((r - 6) / 5, 0, 1) * np.clip((R_OUT + 9 - r) / 7, 0, 1)
        I = I + STREAM * st * (R_IN / r) ** 0.5 * (0.7 + 0.3 * tex) * grav
    w = np.clip(x, 0, 1) ** 0.45
    hot = np.array([1.0, 0.92, 0.80]); warm = np.array([1.0, 0.56, 0.24])
    c = hot[None] * (1 - w[:, None]) + warm[None] * w[:, None]
    c[:, 2] *= np.clip(dop, 0.6, 1.4) ** 0.6           # approaching side a little whiter
    alpha = np.clip(0.95 * np.clip(x / 0.03, 0, 1) * np.clip((1 - x) / 0.5, 0, 1), 0, 0.95)
    if STREAM > 0:
        red = np.array([1.0, 0.30, 0.16])
        mixr = (st / (st + 0.15 + inten * tex))[:, None]
        c = c * (1 - mixr) + red[None] * mixr
        alpha = np.maximum(alpha, 0.8 * st)
    return I[:, None] * c, alpha


def trace(rows):
    y0, y1 = rows
    ys, xs = np.mgrid[y0:y1, 0:W]
    dx = (xs.ravel() + 0.5 - HOLE[0]); dy = (HOLE[1] - ys.ravel() - 0.5)
    v = dx[:, None] * right + dy[:, None] * up + F * fw
    v /= np.linalg.norm(v, axis=1, keepdims=True)
    n = v.shape[0]
    p = np.tile(cam, (n, 1))
    h2 = np.sum(np.cross(p, v) ** 2, 1)
    col = np.zeros((n, 3)); acc = np.zeros(n)
    idx = np.arange(n)
    for step in range(6000):
        if idx.size == 0:
            break
        P, V, Hh = p[idx], v[idx], h2[idx]
        r = np.linalg.norm(P, axis=1)
        dt = np.clip(0.06 * (r - 0.6), 0.004, 2.5)
        a = -1.5 * Hh[:, None] * P / r[:, None] ** 5
        Vh = V + 0.5 * dt[:, None] * a
        Pn = P + dt[:, None] * Vh
        rn = np.linalg.norm(Pn, axis=1)
        an = -1.5 * Hh[:, None] * Pn / rn[:, None] ** 5
        Vn = Vh + 0.5 * dt[:, None] * an
        cross = (P[:, 1] * Pn[:, 1]) < 0
        if cross.any():
            ci = np.nonzero(cross)[0]
            t = P[ci, 1] / (P[ci, 1] - Pn[ci, 1])
            pc = P[ci] + t[:, None] * (Pn[ci] - P[ci])
            rc = np.hypot(pc[:, 0], pc[:, 2])
            hit = (rc > R_IN) & (rc < R_OUT + (9 if STREAM > 0 else 0))
            if hit.any():
                hi = ci[hit]; g = idx[hi]
                c, al = disk_colour(pc[hit], Vn[hi])
                col[g] += (1 - acc[g])[:, None] * al[:, None] * c
                acc[g] += (1 - acc[g]) * al
        p[idx], v[idx] = Pn, Vn
        done_in = rn < 1.0
        done_out = (rn > D * 1.6) & (np.sum(Pn * Vn, 1) > 0)
        opaque = acc[idx] > 0.995
        if done_out.any():
            g = idx[done_out]
            col[g] += (1 - acc[g])[:, None] * background(Vn[done_out])
        keep = ~(done_in | done_out | opaque)
        idx = idx[keep]
    return col.reshape(y1 - y0, W, 3)


if __name__ == "__main__":
    chunks = [(y, min(H, y + 12)) for y in range(0, H, 12)]
    with Pool(os.cpu_count()) as pool:
        parts = pool.map(trace, chunks)
    img = np.concatenate(parts, 0).astype(np.float32)
    ss = int(os.environ.get("SS", 1))
    if ss > 1:
        img = img.reshape(H // ss, ss, W // ss, ss, 3).mean((1, 3))
    np.save(OUT, img)
    print("ok", img.shape, float(img.max()))
