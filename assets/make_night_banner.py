"""Profile banner and project card: a ray-traced black hole over the limb of a pale, icy planet, the name in
wide-spaced capitals between two hairlines, and the website's line "I build systems that learn."

    python assets/make_night_banner.py      # writes the SVGs next to this file

The pictures are rendered once by the scripts in assets/render/ (see the README there) and embedded as JPEG,
because GitHub shows a README's SVG as an image and an image may not load anything else. Motion is slow and
sparse (the hole and the limb breathe, a few stars twinkle, a light passes over "learn") and stops under
prefers-reduced-motion; each file also has a static twin that the README picks with <picture>. Fonts are
system stacks, so nothing needs to be downloaded."""
import base64
import random
from pathlib import Path

OUT = Path(__file__).parent
RENDER = OUT / "render"
SERIF = "'Iowan Old Style','Palatino Linotype','Book Antiqua',Palatino,Georgia,serif"
SANS = "-apple-system,BlinkMacSystemFont,'Segoe UI',Helvetica,Arial,sans-serif"
MONO = "SFMono-Regular,ui-monospace,Menlo,Consolas,'Liberation Mono',monospace"
INK, SOFT, MUTED, WARM = "#f4f1ec", "#d9d4cc", "#8f8a84", "#d9c6a5"
DESC = ("Tianyi Zhang (张天毅): Georgia Tech CS master's, graduating 2027; Shanghai, Atlanta, Bay Area. "
        "I build systems that learn, and the tests that tell real magic from a good trick. "
        "Representation learning, LLM post-training, and evaluation.")

MOTION = '''<style>
.rise{animation:rise 2.4s cubic-bezier(.2,.7,.2,1) both}.rise2{animation-delay:.3s}.rise3{animation-delay:.6s}
@keyframes rise{from{opacity:0;transform:translateY(8px)}}
.breath{animation:breath 8s ease-in-out infinite alternate}@keyframes breath{from{opacity:.25}to{opacity:1}}
.dawn{animation:dawn 11s ease-in-out infinite alternate}@keyframes dawn{from{opacity:.3}to{opacity:.95}}
.tw{animation:tw 5s ease-in-out infinite alternate}.t1{animation-duration:7s;animation-delay:-2s}.t2{animation-duration:4s;animation-delay:-1s}.t3{animation-duration:9s;animation-delay:-4s}
@keyframes tw{from{opacity:.1}to{opacity:1}}
.glint{animation:glint 6s ease-in-out infinite}@keyframes glint{0%,100%{opacity:.35}50%{opacity:1}}
.shine{animation:shine 10s ease-in-out infinite}@keyframes shine{0%,60%{transform:translateX(-220px)}86%,100%{transform:translateX(220px)}}
@media (prefers-reduced-motion:reduce){*{animation:none!important}}
</style>'''


def picture(name):
    return "data:image/jpeg;base64," + base64.b64encode((RENDER / name).read_bytes()).decode()


def svg(w, h, body, static, title="Tianyi Zhang", desc=DESC, ids=("t", "d"), defs=""):
    head = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" role="img" aria-labelledby="{ids[0]} {ids[1]}">',
            f'<title id="{ids[0]}">{title}</title>', f'<desc id="{ids[1]}">{desc}</desc>']
    if not static:
        head.append(MOTION)
    return "\n".join(head + [f"<defs>{defs}</defs>"] + body + ['</svg>'])


def common_defs(hx, hy, hr, pcx, pcy, pr):
    return (f'<radialGradient id="hole" cx="{hx}" cy="{hy}" r="{hr}" gradientUnits="userSpaceOnUse">'
            '<stop offset="0" stop-color="#ffe6c4" stop-opacity=".22"/><stop offset=".45" stop-color="#ffcf9a" stop-opacity=".07"/>'
            '<stop offset="1" stop-color="#ffcf9a" stop-opacity="0"/></radialGradient>'
            f'<radialGradient id="limb" cx="{pcx}" cy="{pcy}" r="{pr + 26}" gradientUnits="userSpaceOnUse">'
            f'<stop offset="{(pr - 4) / (pr + 26):.5f}" stop-color="#fff1dc" stop-opacity="0"/>'
            f'<stop offset="{pr / (pr + 26):.5f}" stop-color="#fff1dc" stop-opacity=".55"/>'
            '<stop offset="1" stop-color="#ffd9b0" stop-opacity="0"/></radialGradient>'
            f'<radialGradient id="limbfade" cx="{hx}" cy="{pcy - pr}" r="{pr * .26}" gradientUnits="userSpaceOnUse">'
            '<stop offset="0" stop-color="#fff"/><stop offset="1" stop-color="#fff" stop-opacity="0"/></radialGradient>'
            f'<mask id="limbmask"><rect x="0" y="0" width="100%" height="100%" fill="url(#limbfade)"/></mask>'
            '<linearGradient id="hairT" x2="0" y2="1"><stop offset="0" stop-color="#fff" stop-opacity="0"/><stop offset="1" stop-color="#fff" stop-opacity=".7"/></linearGradient>'
            '<linearGradient id="hairB" x2="0" y2="1"><stop offset="0" stop-color="#fff" stop-opacity=".7"/><stop offset="1" stop-color="#fff" stop-opacity="0"/></linearGradient>'
            '<linearGradient id="flare"><stop offset="0" stop-color="#fff" stop-opacity="0"/><stop offset=".5" stop-color="#fff" stop-opacity=".75"/><stop offset="1" stop-color="#fff" stop-opacity="0"/></linearGradient>'
            '<linearGradient id="flarev" x2="0" y2="1"><stop offset="0" stop-color="#fff" stop-opacity="0"/><stop offset=".5" stop-color="#fff" stop-opacity=".75"/><stop offset="1" stop-color="#fff" stop-opacity="0"/></linearGradient>'
            '<linearGradient id="shine" x1="0" x2="1"><stop offset="0" stop-color="#fff" stop-opacity="0"/><stop offset=".5" stop-color="#fff" stop-opacity=".9"/><stop offset="1" stop-color="#fff" stop-opacity="0"/></linearGradient>')


def glow_layers(hx, hy, hr, pcx, pcy, pr):
    """The hole's light and the lit limb, breathing; drawn over the picture with screen blending."""
    return [f'<circle class="breath" cx="{hx}" cy="{hy}" r="{hr}" fill="url(#hole)" style="mix-blend-mode:screen"/>',
            f'<g mask="url(#limbmask)"><circle class="dawn" cx="{pcx}" cy="{pcy}" r="{pr + 26}" fill="url(#limb)" style="mix-blend-mode:screen"/></g>']


def twinkles(rng, n, box, avoid=()):
    out = []
    while len(out) < n:
        x, y = rng.uniform(box[0], box[2]), rng.uniform(box[1], box[3])
        if any(a[0] < x < a[2] and a[1] < y < a[3] for a in avoid):
            continue
        r = rng.choice([.55, .65, .8, 1.0])
        out.append(f'<circle class="tw t{len(out) % 4}" cx="{x:.1f}" cy="{y:.1f}" r="{r}" fill="#eef1ff"/>')
    return out


def glint(x, y, size=7):
    return (f'<g class="glint"><rect x="{x - size}" y="{y - .5}" width="{2 * size}" height="1" fill="url(#flare)"/>'
            f'<rect x="{x - .5}" y="{y - size}" width="1" height="{2 * size}" fill="url(#flarev)"/></g>')


def title_block(cx, top, size, gap, words_w, tag_y, tag_size, static, hair=30):
    """TIANYI | ZHANG in wide capitals with a hairline above and below, then the line from the website."""
    y = top + hair + size * .78
    o = [f'<rect x="{cx - .5}" y="{top}" width="1" height="{hair}" fill="url(#hairT)"/>', glint(cx, top),
         f'<g class="rise"><text x="{cx - gap}" y="{y:.1f}" font-family="{SANS}" font-size="{size}" font-weight="300" fill="{INK}" '
         f'text-anchor="end" textLength="{words_w[0]}" lengthAdjust="spacing">TIANYI</text>'
         f'<text x="{cx + gap}" y="{y:.1f}" font-family="{SANS}" font-size="{size}" font-weight="300" fill="{INK}" '
         f'textLength="{words_w[1]}" lengthAdjust="spacing">ZHANG</text></g>',
         f'<rect x="{cx - .5}" y="{y + 14:.1f}" width="1" height="{hair - 4}" fill="url(#hairB)"/>',
         f'<rect x="{cx - 40}" y="{y + 14 + hair - 4:.1f}" width="80" height="1" fill="url(#flare)" opacity=".7"/>',
         f'<g class="rise rise2"><text x="{cx}" y="{tag_y}" font-family="{SERIF}" font-size="{tag_size}" fill="{SOFT}" text-anchor="middle">'
         f'I build systems that <tspan font-style="italic" fill="{WARM}">learn.</tspan></text></g>']
    if not static:  # a light passes over "learn."
        o.append(f'<clipPath id="learn"><text x="{cx}" y="{tag_y}" font-family="{SERIF}" font-size="{tag_size}" text-anchor="middle">'
                 f'<tspan fill-opacity="0">I build systems that </tspan><tspan font-style="italic">learn.</tspan></text></clipPath>'
                 f'<g clip-path="url(#learn)"><rect class="shine" x="{cx}" y="{tag_y - tag_size}" width="120" height="{tag_size * 1.5}" fill="url(#shine)" opacity=".8"/></g>')
    return o


def desktop(static=False):
    w, h = 1200, 500
    hx, hy, pcx, pr = 600, 140, 600, 2600
    pcy = h * .835 + pr
    rng = random.Random(21)
    o = [f'<image href="{picture("banner.jpg")}" width="{w}" height="{h}" preserveAspectRatio="none"/>']
    if not static:
        o += glow_layers(hx, hy, 190, pcx, pcy, pr)
        o += twinkles(rng, 22, (30, 60, 1170, 380), avoid=[(330, 40, 880, 260), (250, 230, 950, 400)])
    o += title_block(600, 244, 38, 28, (262, 234), 382, 22, static)
    o += [f'<text x="40" y="44" font-family="{MONO}" font-size="10.5" letter-spacing="2.4" fill="{MUTED}">张天毅 · GEORGIA TECH · M.S. CS · 2027</text>',
          f'<text x="{w - 40}" y="44" font-family="{MONO}" font-size="10.5" letter-spacing="2.4" fill="{MUTED}" text-anchor="end">SHANGHAI · ATLANTA · BAY AREA</text>']
    return svg(w, h, o, static, defs=common_defs(hx, hy, 190, pcx, pcy, pr))


def mobile(static=False):
    w, h = 600, 680
    hx, hy, pcx, pr = 300, 184, 300, 1300
    pcy = h * .855 + pr
    rng = random.Random(23)
    o = [f'<image href="{picture("banner-mobile.jpg")}" width="{w}" height="{h}" preserveAspectRatio="none"/>']
    if not static:
        o += glow_layers(hx, hy, 190, pcx, pcy, pr)
        o += twinkles(rng, 16, (20, 70, 580, 540), avoid=[(60, 70, 540, 330), (40, 330, 560, 520)])
    o += title_block(300, 352, 30, 20, (204, 182), 476, 21, static, hair=26)
    o += [f'<text x="300" y="44" font-family="{MONO}" font-size="10.5" letter-spacing="2.2" fill="{MUTED}" text-anchor="middle">张天毅 · GEORGIA TECH · M.S. CS · 2027</text>',
          f'<text x="300" y="64" font-family="{MONO}" font-size="10.5" letter-spacing="2.2" fill="{MUTED}" text-anchor="middle" fill-opacity=".8">SHANGHAI · ATLANTA · BAY AREA</text>']
    return svg(w, h, o, static, defs=common_defs(hx, hy, 190, pcx, pcy, pr))


def card(w, h, static=False):
    """The study-notes card: the same sky, a small black hole to the right, the planet's limb along its foot."""
    wide = w > 700
    rng = random.Random(5)
    if wide:
        hx, hy, pcx, pr, top = w * .84, h * .36, w * .66, 1700 * w / 1200 * 2 / 2, h * .80
    else:
        hx, hy, pcx, pr, top = w * .80, h * .25, w * .62, 1100 * w / 1200 * 2 / 2, h * .86
    pcy = top + pr
    o = [f'<image href="{picture("card.jpg" if wide else "card-mobile.jpg")}" width="{w}" height="{h}" preserveAspectRatio="none"/>']
    if not static:
        o += [f'<circle class="breath" cx="{hx:.1f}" cy="{hy:.1f}" r="{70 if wide else 64}" fill="url(#hole)" style="mix-blend-mode:screen"/>']
        o += twinkles(rng, 10, (20, 20, w - 20, h * .7), avoid=[(0, 20, 560 if wide else 380, h * .75), (hx - 120, hy - 50, hx + 120, hy + 50)])
    o += [f'<text x="32" y="{40 if wide else 46}" font-family="{MONO}" font-size="11" letter-spacing="2.2" fill="{MUTED}">OPEN NOTES · 中文 / ENGLISH</text>',
          f'<text x="30" y="{92 if wide else 104}" font-family="{SERIF}" font-size="{46}" letter-spacing="-1.2" fill="{INK}">Cooking <tspan font-style="italic" fill="{WARM}">AGI</tspan></text>']
    lines = (["Modern AI in my own words: notes, interactive figures, and a history of the technology."] if wide
             else ["Modern AI in my own words: notes,", "interactive figures, and a history", "of the technology."])
    for i, line in enumerate(lines):
        o.append(f'<text x="32" y="{(124 if wide else 142) + i * 24}" font-family="{SANS}" font-size="{15 if wide else 16}" fill="{SOFT}" fill-opacity=".85">{line}</text>')
    bx, by = (32, 144) if wide else (32, h - 64)
    o.append(f'<rect x="{bx}" y="{by}" width="170" height="36" rx="18" fill="#000" fill-opacity=".35" stroke="#5a5650"/>'
             f'<text x="{bx + 20}" y="{by + 23}" font-family="{SANS}" font-size="14" font-weight="600" fill="{INK}">Open the notes</text>'
             f'<text x="{bx + 150}" y="{by + 23}" font-family="{SANS}" font-size="15" fill="{INK}" text-anchor="end">→</text>')
    return svg(w, h, o, static, title="Cooking AGI · cooking-agi",
               desc="Modern AI in my own words: bilingual notes, interactive figures, and a history of the technology.", ids=("ct", "cd"),
               defs=common_defs(hx, hy, 70, pcx, pcy, pr))


FILES = {
    "night-banner.svg": desktop(), "night-banner-static.svg": desktop(True),
    "night-banner-mobile.svg": mobile(), "night-banner-mobile-static.svg": mobile(True),
    "card-notes.svg": card(880, 200), "card-notes-static.svg": card(880, 200, True),
    "card-notes-mobile.svg": card(600, 270), "card-notes-mobile-static.svg": card(600, 270, True),
}
if __name__ == "__main__":
    for name, text in FILES.items():
        (OUT / name).write_text(text + "\n", encoding="utf-8")
    print("\n".join(f"{name}: {len(text) // 1024} KB" for name, text in FILES.items()))
