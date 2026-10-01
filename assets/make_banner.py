#!/usr/bin/env python3
"""Generate deterministic, theme-aware SVG headers for the profile README."""

import math
import random
from pathlib import Path

WIDTH = 1200
HEIGHT = 340
THEMES = {
    "dark": {
        "background": "#0d1117", "ink": "#f0eee8", "muted": "#8e969c",
        "accent": "#cba77a", "line": "#30363d", "orbit": "#58616a",
    },
    "light": {
        "background": "#ffffff", "ink": "#24292f", "muted": "#687078",
        "accent": "#9a7248", "line": "#d1d9e0", "orbit": "#abb2b9",
    },
}


def pixel_planet(ink):
    radius = 119
    centre_x, centre_y = 947, 152
    randomizer = random.Random(71)
    parts = []
    for row in range(-radius, radius + 1, 3):
        for column in range(-radius, radius + 1, 3):
            position_x = column + randomizer.uniform(-.8, .8)
            position_y = row + randomizer.uniform(-.8, .8)
            normal_x, normal_y = position_x / radius, position_y / radius
            distance = normal_x * normal_x + normal_y * normal_y
            if distance >= 1:
                continue
            normal_z = math.sqrt(1 - distance)
            brightness = max(0, -.68 * normal_x - .42 * normal_y + .6 * normal_z)
            if randomizer.random() < .04 + .87 * brightness:
                size = .55 + .52 * brightness
                parts.append(
                    f'<circle cx="{centre_x + position_x:.2f}" cy="{centre_y + position_y:.2f}" r="{size:.2f}"/>'
                )
    return f'<g fill="{ink}">' + "\n".join(parts) + "</g>"


def orbit_path(start_angle, end_angle):
    rotation = math.radians(-26)
    points = []
    for step in range(101):
        angle = math.radians(start_angle + (end_angle - start_angle) * step / 100)
        local_x = 183 * math.cos(angle)
        local_y = 49 * math.sin(angle)
        position_x = 947 + local_x * math.cos(rotation) - local_y * math.sin(rotation)
        position_y = 152 + local_x * math.sin(rotation) + local_y * math.cos(rotation)
        points.append(f'{position_x:.2f},{position_y:.2f}')
    return 'M' + ' L'.join(points)


def build(theme, compact=False):
    colors = THEMES[theme]
    width, height = (500, 265) if compact else (WIDTH, HEIGHT)
    font = '-apple-system,BlinkMacSystemFont,Segoe UI,Helvetica,Arial,sans-serif'
    if compact:
        lettering = f'''<text x="0" y="25" font-family="ui-monospace,SFMono-Regular,Consolas,monospace" font-size="16" letter-spacing="1.4" fill="{colors['muted']}">RESEARCH / BUILDING / NOTES</text>
<text x="-2" y="103" font-family="{font}" font-size="68" font-weight="700" letter-spacing="-3" fill="{colors['ink']}">Tianyi</text>
<text x="-2" y="169" font-family="{font}" font-size="68" font-weight="700" letter-spacing="-3" fill="{colors['ink']}">Zhang</text>
<text x="1" y="219" font-family="{font}" font-size="21" fill="{colors['muted']}">Shanghai · Atlanta · Bay Area</text>'''
        planet_transform = 'translate(381 112) scale(.58) translate(-947 -152)'
    else:
        lettering = f'''<text x="0" y="57" font-family="ui-monospace,SFMono-Regular,Consolas,monospace" font-size="17" letter-spacing="3" fill="{colors['muted']}">RESEARCH / BUILDING / NOTES</text>
<text x="-5" y="183" font-family="{font}" font-size="108" font-weight="700" letter-spacing="-5" fill="{colors['ink']}">Tianyi Zhang</text>
<text x="2" y="234" font-family="{font}" font-size="22" fill="{colors['muted']}">Shanghai · Atlanta · Bay Area</text>'''
        planet_transform = ''
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" aria-labelledby="title description">
<title id="title">Tianyi Zhang</title>
<desc id="description">An editorial wordmark with a finely stippled planet and a single bronze orbital marker.</desc>
<rect width="{width}" height="{height}" fill="{colors['background']}"/>
{lettering}
<g transform="{planet_transform}">
<path d="{orbit_path(180, 360)}" fill="none" stroke="{colors['orbit']}" stroke-width=".8"/>
<circle cx="947" cy="152" r="120" fill="{colors['background']}"/>
{pixel_planet(colors['ink'])}
<path d="{orbit_path(0, 180)}" fill="none" stroke="{colors['orbit']}" stroke-width="1"/>
<circle cx="1111.48" cy="71.78" r="4" fill="{colors['accent']}"/>
</g>
<path d="M0 {height - 13}H{width}" stroke="{colors['line']}"/>
<path d="M0 {height - 13}H43" stroke="{colors['accent']}" stroke-width="2"/>
</svg>
'''


if __name__ == "__main__":
    directory = Path(__file__).resolve().parent
    for theme in THEMES:
        for compact in (False, True):
            suffix = '-mobile' if compact else ''
            destination = directory / f"banner-{theme}{suffix}.svg"
            destination.write_text(build(theme, compact), encoding="utf-8")
            print(f"Generated {destination.name}")
