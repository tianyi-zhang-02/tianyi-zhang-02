#!/usr/bin/env python3
"""Generate self-contained night-sky SVG banners and reduced-motion alternatives."""

import math
import random
from pathlib import Path

WIDTH = 1200
HEIGHT = 410
THEMES = {
    'dark': {'edge': '#0d1117', 'sky': '#060b15', 'ink': '#f2f1ed'},
    'light': {'edge': '#d1d9e0', 'sky': '#080e1b', 'ink': '#f5f3ef'},
}
FONT = '-apple-system,BlinkMacSystemFont,Segoe UI,Helvetica,Arial,sans-serif'
MONO = 'ui-monospace,SFMono-Regular,Consolas,monospace'


def star_field(width, height):
    randomizer = random.Random(20260921)
    layers = [[], [], [], [], [], []]
    count = 260 if width < 600 else 880
    for _ in range(count):
        position_x = randomizer.uniform(-24, width + 24)
        position_y = randomizer.uniform(-20, height)
        magnitude = randomizer.random()
        size = .48 + magnitude ** 4 * 1.85
        opacity = .25 + magnitude * .72
        tint = randomizer.choice(('#eef3ff', '#d0ddff', '#f6e9d5', '#ffffff'))
        circle = f'<circle cx="{position_x:.2f}" cy="{position_y:.2f}" r="{size:.2f}" fill="{tint}" opacity="{opacity:.2f}"/>'
        layer = randomizer.randrange(1, 6) if magnitude > .83 else 0
        layers[layer].append(circle)
        if magnitude > .98:
            layers[layer].append(
                f'<circle cx="{position_x:.2f}" cy="{position_y:.2f}" r="{size * 5:.2f}" fill="url(#star-glow)"/>'
            )
    parts = ['<g class="sky-drift">', '<g>' + ''.join(layers[0]) + '</g>']
    for index, layer in enumerate(layers[1:]):
        parts.append(f'<g class="star-pulse pulse-{index}">' + ''.join(layer) + '</g>')
    return ''.join(parts) + '</g>'


def milky_way(width, height):
    randomizer = random.Random(41)
    centre_x, centre_y = width * .78, height * .36
    rotation = math.radians(37)
    span = width * .75
    band_width = height * .12
    parts = ['<g class="galaxy-drift">']
    for index in range(25):
        fraction = index / 24 - .5
        local_x = fraction * span
        local_y = -local_x ** 2 / (span * 8)
        position_x = centre_x + local_x * math.cos(rotation) - local_y * math.sin(rotation)
        position_y = centre_y + local_x * math.sin(rotation) + local_y * math.cos(rotation)
        core = math.exp(-((fraction - .05) / .24) ** 2)
        size = band_width * (1.05 + core * .85)
        parts.append(f'<ellipse cx="{position_x:.2f}" cy="{position_y:.2f}" rx="{size * 1.2:.2f}" ry="{size:.2f}" fill="url(#galaxy-haze)" opacity="{.22 + core * .24:.2f}"/>')
    for _ in range(850 if width > 600 else 330):
        fraction = randomizer.uniform(-.65, .65)
        local_x = fraction * span
        core = math.exp(-((fraction - .05) / .24) ** 2)
        local_y = randomizer.gauss(0, band_width * (.32 + core * .17))
        if -band_width * .16 < local_y < band_width * .06 and randomizer.random() < .82:
            continue
        local_y -= local_x ** 2 / (span * 8)
        position_x = centre_x + local_x * math.cos(rotation) - local_y * math.sin(rotation)
        position_y = centre_y + local_x * math.sin(rotation) + local_y * math.cos(rotation)
        size = randomizer.uniform(.35, 1)
        opacity = randomizer.uniform(.1, .46) * (.65 + core * .65)
        parts.append(f'<circle cx="{position_x:.2f}" cy="{position_y:.2f}" r="{size:.2f}" fill="#e4e7f5" opacity="{opacity:.2f}"/>')
    return ''.join(parts) + '</g>'


def horizon(width, height):
    radius = width * 1.7
    centre_x, centre_y = width * .56, height * .86 + radius
    def limb_y(position_x):
        return centre_y - math.sqrt(radius ** 2 - (position_x - centre_x) ** 2)
    arc = f'M-30 {limb_y(-30):.2f} A{radius:.2f} {radius:.2f} 0 0 1 {width + 30} {limb_y(width + 30):.2f}'
    sunrise_x = width * .16
    sunrise_y = limb_y(sunrise_x)
    parts = [f'<ellipse cx="{sunrise_x:.2f}" cy="{sunrise_y - 4:.2f}" rx="{width * .26:.2f}" ry="{height * .2:.2f}" fill="url(#sunrise)"/>']
    for stroke_width, opacity in ((52, .025), (28, .045), (13, .075), (5, .18)):
        parts.append(f'<path d="{arc}" fill="none" stroke="url(#atmosphere)" stroke-width="{stroke_width}" opacity="{opacity}"/>')
    parts.append(f'<path d="{arc} L{width + 30} {height + 30} H-30Z" fill="url(#planet-body)"/>')
    parts.append(f'<path d="{arc}" fill="none" stroke="url(#atmosphere)" stroke-width="1.4" opacity=".82"/>')
    return ''.join(parts)


def animation_style():
    return '''<style>
.sky-drift { animation: sidereal 84s ease-in-out infinite alternate; }
.galaxy-drift { animation: galaxy 105s ease-in-out infinite alternate; }
.star-pulse { animation: twinkle 6s ease-in-out infinite alternate; }
.pulse-1 { animation-duration:8s; animation-delay:-3s; }
.pulse-2 { animation-duration:5s; animation-delay:-1s; }
.pulse-3 { animation-duration:9s; animation-delay:-5s; }
.pulse-4 { animation-duration:7s; animation-delay:-2s; }
.meteor { opacity:0; animation: passing-star 21s linear infinite; animation-delay:2s; }
.meteor-second { animation-duration:29s; animation-delay:12s; }
@keyframes sidereal { from { transform:translate(0,0); } to { transform:translate(-18px,8px); } }
@keyframes galaxy { from { transform:translate(0,0); } to { transform:translate(-10px,4px); } }
@keyframes twinkle { from { opacity:.4; } to { opacity:1; } }
@keyframes passing-star {
  0% { transform:translate(0,0); opacity:0; }
  1.5% { opacity:.75; }
  7.5% { transform:translate(-210px,112px); opacity:0; }
  100% { transform:translate(-210px,112px); opacity:0; }
}
@media (prefers-reduced-motion:reduce) {
  .sky-drift,.galaxy-drift,.star-pulse,.meteor { animation:none!important; }
  .meteor { display:none; }
}
</style>'''


def build(theme, compact=False, animated=True):
    colors = THEMES[theme]
    width, height = (500, 345) if compact else (WIDTH, HEIGHT)
    text_x = 30 if compact else 54
    if compact:
        lettering = f'''<text x="{text_x}" y="52" font-family="{MONO}" font-size="14" letter-spacing="1.7" fill="#b4becb">RESEARCH / BUILDING / NOTES</text>
<text x="{text_x - 3}" y="132" font-family="{FONT}" font-size="66" font-weight="700" letter-spacing="-3" fill="{colors['ink']}">Tianyi</text>
<text x="{text_x - 3}" y="195" font-family="{FONT}" font-size="66" font-weight="700" letter-spacing="-3" fill="{colors['ink']}">Zhang</text>
<text x="{text_x}" y="243" font-family="{FONT}" font-size="20" fill="#bec8d5">Shanghai · Atlanta · Bay Area</text>'''
    else:
        lettering = f'''<text x="{text_x}" y="88" font-family="{MONO}" font-size="17" letter-spacing="3" fill="#b4becb">RESEARCH / BUILDING / NOTES</text>
<text x="{text_x - 5}" y="216" font-family="{FONT}" font-size="106" font-weight="700" letter-spacing="-5" fill="{colors['ink']}">Tianyi Zhang</text>
<text x="{text_x}" y="271" font-family="{FONT}" font-size="23" fill="#bec8d5">Shanghai · Atlanta · Bay Area</text>'''
    meteors = ''
    if animated:
        for index, (position_x, position_y) in enumerate(((width * .9, height * .17), (width * .79, height * .29))):
            extra = ' meteor-second' if index else ''
            meteors += f'''<g transform="translate({position_x:.2f} {position_y:.2f})"><g class="meteor{extra}">
<path d="M0 0L100 -53" fill="none" stroke="url(#meteor-tail)" stroke-width="1.1"/>
<circle r="1.1" fill="#f3f5ff"/>
</g></g>'''
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" aria-labelledby="title description">
<title id="title">Tianyi Zhang</title>
<desc id="description">Shanghai · Atlanta · Bay Area. A quiet night sky with a drifting Milky Way, gently twinkling stars, and a planetary horizon. Motion respects reduced-motion preferences.</desc>
{animation_style() if animated else ''}
<defs>
<clipPath id="frame"><rect width="{width}" height="{height}" rx="14"/></clipPath>
<radialGradient id="galaxy-haze"><stop stop-color="#babacc" stop-opacity=".25"/><stop offset=".4" stop-color="#829cc6" stop-opacity=".1"/><stop offset="1" stop-color="#637bb0" stop-opacity="0"/></radialGradient>
<radialGradient id="star-glow"><stop stop-color="#c9dcff" stop-opacity=".36"/><stop offset=".2" stop-color="#c9dcff" stop-opacity=".12"/><stop offset="1" stop-color="#c9dcff" stop-opacity="0"/></radialGradient>
<radialGradient id="sunrise"><stop stop-color="#ffdbab" stop-opacity=".5"/><stop offset=".12" stop-color="#edbb85" stop-opacity=".19"/><stop offset=".4" stop-color="#b58667" stop-opacity=".04"/><stop offset="1" stop-color="#8f7160" stop-opacity="0"/></radialGradient>
<linearGradient id="atmosphere"><stop stop-color="#d5e6ff" stop-opacity=".4"/><stop offset=".16" stop-color="#ffdfaf"/><stop offset=".4" stop-color="#b6d9fb"/><stop offset="1" stop-color="#4a648c" stop-opacity=".15"/></linearGradient>
<linearGradient id="planet-body"><stop stop-color="#0b1426"/><stop offset=".45" stop-color="#060d19"/><stop offset="1" stop-color="#030811"/></linearGradient>
<linearGradient id="text-shade"><stop stop-color="#050a13" stop-opacity=".82"/><stop offset=".4" stop-color="#050a13" stop-opacity=".67"/><stop offset=".74" stop-color="#050a13" stop-opacity="0"/></linearGradient>
<linearGradient id="meteor-tail" x1="0" y1="0" x2="100" y2="-53" gradientUnits="userSpaceOnUse"><stop stop-color="#dce7ff" stop-opacity=".8"/><stop offset="1" stop-color="#dce7ff" stop-opacity="0"/></linearGradient>
</defs>
<g clip-path="url(#frame)">
<rect width="{width}" height="{height}" fill="{colors['sky']}"/>
{milky_way(width, height)}
{star_field(width, height)}
{meteors}
{horizon(width, height)}
<rect width="{width}" height="{height * .8:.2f}" fill="url(#text-shade)"/>
{lettering}
</g>
<rect x=".5" y=".5" width="{width - 1}" height="{height - 1}" rx="14" fill="none" stroke="{colors['edge']}"/>
</svg>
'''


if __name__ == '__main__':
    directory = Path(__file__).resolve().parent
    for theme in THEMES:
        for compact in (False, True):
            suffix = '-mobile' if compact else ''
            destination = directory / f'banner-{theme}{suffix}.svg'
            destination.write_text(build(theme, compact), encoding='utf-8')
            print(f'Generated {destination.name}')
    for compact in (False, True):
        suffix = '-mobile' if compact else ''
        destination = directory / f'banner-static{suffix}.svg'
        destination.write_text(build('dark', compact, animated=False), encoding='utf-8')
        print(f'Generated {destination.name}')
