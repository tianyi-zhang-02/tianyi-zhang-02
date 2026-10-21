"""Profile banner and project card: a night sky with 1-bit grain, a name a light passes over, a constellation
that draws Shanghai → Atlanta → Bay Area, a planet rising, and a terminal strip that types the research topics.

    python assets/make_night_banner.py      # writes the SVGs next to this file

Every variant has a static twin for prefers-reduced-motion (the README picks it with <picture>), and the
animated ones also stop under that media query in case a viewer shows them anyway. Text uses system fonts;
textLength keeps the name the same width whatever font the viewer has."""
import random
from pathlib import Path

OUT = Path(__file__).parent
SANS = "-apple-system,BlinkMacSystemFont,'Segoe UI',Helvetica,Arial,sans-serif"
MONO = "ui-monospace,SFMono-Regular,Menlo,Consolas,monospace"
IVORY, AMBER, MUTED, LINE, DEEP = "#f2e8d5", "#e8a672", "#8a91a3", "#1c2230", "#05070d"
TOPICS = ["representation learning", "llm post-training", "model &amp; agent evaluation"]
DESC = ("Tianyi Zhang: Georgia Tech CS master's, graduating May 2027; Shanghai, Atlanta, Bay Area. "
        "Representation learning, LLM post-training, and model and agent evaluation.")

MOTION = '''<style>
.tw{animation:tw 5s ease-in-out infinite alternate}.t1{animation-duration:7s;animation-delay:-2s}.t2{animation-duration:4s;animation-delay:-1s}
.t3{animation-duration:9s;animation-delay:-4s}.t4{animation-duration:6s;animation-delay:-3s}
@keyframes tw{from{opacity:.15}to{opacity:1}}
.drift{animation:drift 90s ease-in-out infinite alternate}@keyframes drift{to{transform:translate(-24px,6px)}}
.rise{animation:rise 3.2s cubic-bezier(.2,.7,.2,1) both}@keyframes rise{from{transform:translateY(46px);opacity:.3}}
.route{stroke-dasharray:1400;stroke-dashoffset:1400;animation:route 14s ease-in-out infinite}
@keyframes route{0%{stroke-dashoffset:1400}35%,85%{stroke-dashoffset:0}100%{stroke-dashoffset:-1400}}
.city{animation:city 14s ease-in-out infinite;opacity:0}.c1{animation-delay:.2s}.c2{animation-delay:2.2s}.c3{animation-delay:4.2s}
@keyframes city{0%{opacity:0}6%,80%{opacity:1}96%,100%{opacity:0}}
.sweep{animation:sweep 9s ease-in-out infinite}@keyframes sweep{0%,55%{transform:translateX(-420px)}85%,100%{transform:translateX(1400px)}}
.meteor{opacity:0;animation:meteor 17s linear infinite 3s}
@keyframes meteor{0%{opacity:0;transform:translate(0,0)}1%{opacity:.9}6%{opacity:0;transform:translate(-260px,120px)}100%{opacity:0;transform:translate(-260px,120px)}}
.word{opacity:0;animation:word 12s steps(1) infinite}.w1{animation-delay:4s}.w2{animation-delay:8s}@keyframes word{0%{opacity:1}33.3%,100%{opacity:0}}
.caret{animation:caret 1s steps(1) infinite}@keyframes caret{50%{opacity:0}}
@media (prefers-reduced-motion:reduce){*{animation:none!important}.city{opacity:1}.route{stroke-dashoffset:0}.w1,.w2{opacity:0}.word:not(.w1):not(.w2){opacity:1}}
</style>'''


def defs(name_clip):
    return f'''<defs>
<linearGradient id="sky" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#04060b"/><stop offset=".65" stop-color="#0a0e19"/><stop offset="1" stop-color="#151321"/></linearGradient>
<radialGradient id="planet" cx=".5" cy=".02" r=".7"><stop offset="0" stop-color="{AMBER}"/><stop offset=".22" stop-color="#8a5a3c"/><stop offset=".6" stop-color="#241a22"/><stop offset="1" stop-color="#0b0b12"/></radialGradient>
<radialGradient id="limb" cx=".5" cy="1" r=".6"><stop offset="0" stop-color="{AMBER}" stop-opacity=".35"/><stop offset="1" stop-color="{AMBER}" stop-opacity="0"/></radialGradient>
<linearGradient id="light" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="{AMBER}" stop-opacity="0"/><stop offset=".5" stop-color="#ffd9a8" stop-opacity=".95"/><stop offset="1" stop-color="{AMBER}" stop-opacity="0"/></linearGradient>
<filter id="dither" x="0" y="0" width="100%" height="100%" color-interpolation-filters="sRGB">
 <feColorMatrix type="matrix" values=".3 .59 .11 0 0 .3 .59 .11 0 0 .3 .59 .11 0 0 0 0 0 1 0" result="g"/>
 <feTurbulence type="fractalNoise" baseFrequency="1.6" numOctaves="1" seed="5" result="n"/>
 <feColorMatrix in="n" type="matrix" values="1 0 0 0 0 1 0 0 0 0 1 0 0 0 0 0 0 0 0 1" result="ng"/>
 <feComposite in="g" in2="ng" operator="arithmetic" k2="1" k3="1.1" k4="-.55" result="d"/>
 <feComponentTransfer in="d"><feFuncR type="discrete" tableValues="0 1"/><feFuncG type="discrete" tableValues="0 1"/><feFuncB type="discrete" tableValues="0 1"/></feComponentTransfer>
 <feColorMatrix type="matrix" values="0 0 0 0 .95 0 0 0 0 .78 0 0 0 0 .6 1 0 0 0 0"/>
</filter>
<filter id="grain" x="0" y="0" width="100%" height="100%"><feTurbulence type="fractalNoise" baseFrequency="1.9" numOctaves="1" seed="11"/>
 <feComponentTransfer><feFuncA type="discrete" tableValues="0 0 0 .55"/></feComponentTransfer><feColorMatrix type="matrix" values="0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 0"/></filter>
<filter id="haze" x="-20%" y="-50%" width="140%" height="200%"><feGaussianBlur stdDeviation="22"/></filter>
<clipPath id="name">{name_clip}</clipPath>
<pattern id="cells" width="48" height="48" patternUnits="userSpaceOnUse"><path d="M48 0H0V48" fill="none" stroke="{LINE}" stroke-width=".6"/></pattern>
</defs>'''


def sky(o, rng, w, h, top, star_bottom, n_stars):
    o.append(f'<rect width="{w}" height="{h}" fill="url(#sky)"/>')
    o.append(f'<rect y="{top}" width="{w}" height="{h - top}" fill="url(#cells)" opacity=".55"/>')
    stars = []
    for i in range(n_stars):
        x, y = rng.uniform(0, w), rng.uniform(top + 2, star_bottom)
        r = rng.choice([.5, .6, .7, .8, 1, 1.1, 1.4]) if rng.random() < .93 else rng.uniform(1.5, 2)
        cls = f' class="tw t{i % 5}"' if rng.random() < .45 else ""
        stars.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{r}" fill="#fff" opacity="{rng.uniform(.25, .9):.2f}"{cls}/>')
    o.append('<g class="drift">' + "".join(stars) + '</g>')
    band = "".join(f'<ellipse cx="{x:.0f}" cy="{top + 36 + .2 * x + rng.uniform(-24, 24):.0f}" rx="{rng.uniform(40, 90):.0f}" ry="{rng.uniform(14, 26):.0f}" fill="#9d8cc4"/>'
                   for x in [rng.uniform(0, w) for _ in range(max(8, int(w / 66)))])
    o.append(f'<g opacity=".22" class="drift" filter="url(#haze)">{band}</g>')
    o.append(f'<g class="meteor"><line x1="{w * .84:.0f}" y1="{top + 36}" x2="{w * .84 + 70:.0f}" y2="{top + 4}" stroke="#fff" stroke-width="1.4" stroke-linecap="round" opacity=".9"/></g>')


def planet(o, w, h, horizon):
    cx, r = w / 2, max(900, w * .8)
    cy = horizon + r - 12
    o.append(f'<g class="rise"><circle cx="{cx}" cy="{cy - 20}" r="{r}" fill="url(#limb)"/>'
             f'<g filter="url(#dither)"><circle cx="{cx}" cy="{cy}" r="{r}" fill="url(#planet)"/></g>'
             f'<path d="M -300 {horizon + 26} Q {cx} {horizon - 10} {w + 300} {horizon + 26}" fill="none" stroke="{AMBER}" stroke-opacity=".5" stroke-width="1.2"/></g>')


def name_block(o, box):
    x, y, w, h = box
    o.append(f'<g clip-path="url(#name)"><rect x="{x}" y="{y}" width="{w}" height="{h}" fill="{IVORY}"/>'
             f'<rect x="{x}" y="{y}" width="{w}" height="{h}" filter="url(#grain)" opacity=".55"/>'
             f'<rect class="sweep" x="0" y="{y}" width="380" height="{h}" fill="url(#light)" opacity=".85"/></g>')


def constellation(o, pts, path, static):
    dash = ' stroke-dasharray="4 6"' if static else ""
    o.append(f'<path class="route" d="{path}" fill="none" stroke="{AMBER}" stroke-width="1.3" stroke-opacity=".85"{dash}/>')
    for x, y, label, c in pts:
        o.append(f'<g class="city {c}"><circle cx="{x}" cy="{y}" r="9" fill="{AMBER}" opacity=".18"/><circle cx="{x}" cy="{y}" r="2.6" fill="#fff"/>'
                 f'<text x="{x}" y="{y + 24}" font-family="{MONO}" font-size="12" fill="{IVORY}" fill-opacity=".8" text-anchor="middle">{label}</text></g>')


def strip(o, w, typed_x, right=None):
    o.append(f'<rect width="{w}" height="34" fill="{DEEP}"/><line x1="0" y1="34" x2="{w}" y2="34" stroke="{LINE}"/>')
    o.append(f'<text x="16" y="22" font-family="{MONO}" font-size="13" fill="{MUTED}">~/tianyi-zhang-02 $ <tspan fill="{IVORY}">now --topic</tspan></text>' if typed_x > 200
             else f'<text x="16" y="22" font-family="{MONO}" font-size="13" fill="{MUTED}">~ $ <tspan fill="{IVORY}">now</tspan></text>')
    for i, word in enumerate(TOPICS):
        o.append(f'<text class="word{f" w{i}" if i else ""}" x="{typed_x}" y="22" font-family="{MONO}" font-size="13" fill="{AMBER}">{word}<tspan class="caret">▍</tspan></text>')
    if right:
        o.append(f'<text x="{w - 16}" y="22" font-family="{MONO}" font-size="12.5" fill="{MUTED}" text-anchor="end">{right}</text>')


def info_rows(o, w, rows):
    for y, cells in rows:
        o.append(f'<rect y="{y}" width="{w}" height="50" fill="{DEEP}" fill-opacity=".55"/><line x1="0" y1="{y}" x2="{w}" y2="{y}" stroke="{LINE}"/>')
        for text, x in cells:
            if x:
                o.append(f'<line x1="{x}" y1="{y}" x2="{x}" y2="{y + 50}" stroke="{LINE}"/>')
            o.append(f'<text x="{x + 18}" y="{y + 30}" font-family="{MONO}" font-size="13" fill="{IVORY}" fill-opacity=".78">{text}</text>')


def svg(w, h, body, static, name_clip):
    head = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" role="img" aria-labelledby="t d">',
            '<title id="t">Tianyi Zhang</title>', f'<desc id="d">{DESC}</desc>']
    if not static:
        head.append(MOTION)
    return "\n".join(head + [defs(name_clip)] + body + [f'<rect x=".5" y=".5" width="{w - 1}" height="{h - 1}" fill="none" stroke="{LINE}"/>', '</svg>'])


def desktop(static=False):
    w, h, o = 1200, 480, []
    sky(o, random.Random(7), w, h, 34, 390, 260)
    planet(o, w, h, 370)
    name_block(o, (60, 80, 1090, 150))
    pts = [(170, 300, "shanghai", "c1"), (610, 268, "atlanta", "c2"), (1030, 306, "bay area", "c3")]
    constellation(o, pts, "M 170 300 Q 390 236 610 268 Q 830 248 1030 306", static)
    info_rows(o, w, [(h - 50, [("georgia-tech / cs-ms / may-2027", 0), ("research: representation · post-training · evaluation", 380), ("notes: cooking-agi ↗", 900)])])
    strip(o, w, 276, "33.78°N 84.40°W · learning in public")
    clip = f'<text x="70" y="214" font-family="{SANS}" font-size="142" font-weight="800" textLength="1060" lengthAdjust="spacingAndGlyphs">TIANYI ZHANG</text>'
    return svg(w, h, o, static, clip)


def mobile(static=False):
    w, h, o = 600, 600, []
    sky(o, random.Random(9), w, h, 34, 470, 170)
    planet(o, w, h, 470)
    name_block(o, (20, 60, 560, 270))
    pts = [(80, 392, "shanghai", "c1"), (300, 362, "atlanta", "c2"), (520, 396, "bay area", "c3")]
    constellation(o, pts, "M 80 392 Q 190 348 300 362 Q 410 350 520 396", static)
    info_rows(o, w, [(h - 100, [("georgia-tech / cs-ms / may-2027", 0)]), (h - 50, [("representation · post-training · eval", 0)])])
    strip(o, w, 104)
    clip = (f'<text x="36" y="182" font-family="{SANS}" font-size="132" font-weight="800" textLength="528" lengthAdjust="spacingAndGlyphs">TIANYI</text>'
            f'<text x="36" y="318" font-family="{SANS}" font-size="132" font-weight="800" textLength="528" lengthAdjust="spacingAndGlyphs">ZHANG</text>')
    return svg(w, h, o, static, clip)


def card(w, h, static=False):
    """The study-notes card: a smaller sky, the title, and a call to read."""
    rng = random.Random(3)
    o = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" role="img" aria-labelledby="ct cd">',
         '<title id="ct">AGI Study Notes · cooking-agi</title><desc id="cd">Bilingual notes on ML and language models, with interactive diagrams.</desc>']
    if not static:
        o.append('<style>.tw{animation:tw 5s ease-in-out infinite alternate}.t1{animation-duration:7s;animation-delay:-2s}.t2{animation-duration:4s;animation-delay:-1s}'
                 '@keyframes tw{from{opacity:.15}to{opacity:1}}@media (prefers-reduced-motion:reduce){*{animation:none!important}}</style>')
    o.append(f'<defs><linearGradient id="sky" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#04060b"/><stop offset="1" stop-color="#121226"/></linearGradient>'
             f'<pattern id="cells" width="48" height="48" patternUnits="userSpaceOnUse"><path d="M48 0H0V48" fill="none" stroke="{LINE}" stroke-width=".6"/></pattern></defs>')
    o.append(f'<rect width="{w}" height="{h}" fill="url(#sky)"/><rect width="{w}" height="{h}" fill="url(#cells)" opacity=".55"/>')
    o.append("".join(f'<circle cx="{rng.uniform(0, w):.1f}" cy="{rng.uniform(0, h):.1f}" r="{rng.choice([.5, .7, .9, 1.2])}" fill="#fff" opacity="{rng.uniform(.2, .8):.2f}"'
                     f'{f" class={chr(34)}tw t{i % 3}{chr(34)}" if rng.random() < .5 else ""}/>' for i in range(int(w * h / 1400))))
    wide = w > 700
    o.append(f'<text x="28" y="{42}" font-family="{MONO}" font-size="12.5" fill="{MUTED}">tianyi-zhang-02/cooking-agi</text>')
    o.append(f'<text x="26" y="{100 if wide else 98}" font-family="{SANS}" font-size="{46 if wide else 44}" font-weight="800" letter-spacing="-1.6" fill="{IVORY}">AGI Study Notes</text>')
    lines = (["Bilingual notes on ML and language models, with interactive diagrams."] if wide
             else ["Bilingual notes on ML and language models,", "with interactive diagrams."])
    for i, line in enumerate(lines):
        o.append(f'<text x="28" y="{134 + i * 24}" font-family="{SANS}" font-size="17" fill="{IVORY}" fill-opacity=".72">{line}</text>')
    bx, by, bw = (w - 236, h - 64, 208) if wide else (28, h - 62, 220)
    o.append(f'<rect x="{bx}" y="{by}" width="{bw}" height="40" rx="20" fill="{AMBER}"/>'
             f'<text x="{bx + 20}" y="{by + 26}" font-family="{SANS}" font-size="15" font-weight="650" fill="{DEEP}">read the notes</text>'
             f'<text x="{bx + bw - 20}" y="{by + 26}" font-family="{SANS}" font-size="16" font-weight="650" fill="{DEEP}" text-anchor="end">↗</text>')
    if wide:
        o.append(f'<text x="28" y="{h - 36}" font-family="{MONO}" font-size="12.5" fill="{AMBER}">✦ learning in public, with friends</text>')
    o.append(f'<rect x=".5" y=".5" width="{w - 1}" height="{h - 1}" fill="none" stroke="{LINE}"/></svg>')
    return "\n".join(o)


FILES = {
    "night-banner.svg": desktop(), "night-banner-static.svg": desktop(True),
    "night-banner-mobile.svg": mobile(), "night-banner-mobile-static.svg": mobile(True),
    "card-notes.svg": card(880, 200), "card-notes-static.svg": card(880, 200, True),
    "card-notes-mobile.svg": card(600, 252), "card-notes-mobile-static.svg": card(600, 252, True),
}
if __name__ == "__main__":
    for name, text in FILES.items():
        (OUT / name).write_text(text + "\n", encoding="utf-8")
    print("\n".join(f"{name}: {len(text) // 1024} KB" for name, text in FILES.items()))
