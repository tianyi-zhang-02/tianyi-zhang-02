#!/usr/bin/env python3
"""Generate a contribution-powered, self-contained animated profile SVG."""

from __future__ import annotations

import argparse
import datetime as dt
import json
import math
import os
import pathlib
import random
import urllib.request


WIDTH = 1200
HEIGHT = 330

THEMES = {
    "light": {
        "muted": "#8B9099",
        "faint": "#E9ECF4",
        "grid": ["#EEF1F7", "#DDE4FF", "#B8C5FA", "#7D91E8", "#3455D1"],
        "ink": "#1F2328",
        "blue": "#2447C6",
        "blue_soft": "#8EA2F0",
        "pot": "#20283A",
        "pot_edge": "#40506D",
        "steam": "#AAB2C2",
        "heat": "#FF8A5B",
    },
    "dark": {
        "muted": "#8B93A7",
        "faint": "#252B3B",
        "grid": ["#252B3B", "#303B62", "#46598F", "#7185C4", "#A0B1FF"],
        "ink": "#F0F3FA",
        "blue": "#A0B1FF",
        "blue_soft": "#7185C4",
        "pot": "#D7DEEE",
        "pot_edge": "#A5B0C7",
        "steam": "#7E879B",
        "heat": "#FFAA7E",
    },
}

GRAPHQL_QUERY = """
query($login: String!) {
  user(login: $login) {
    contributionsCollection {
      contributionCalendar {
        totalContributions
        weeks {
          contributionDays {
            contributionCount
            contributionLevel
            date
            weekday
          }
        }
      }
    }
  }
}
"""

LEVELS = {
    "NONE": 0,
    "FIRST_QUARTILE": 1,
    "SECOND_QUARTILE": 2,
    "THIRD_QUARTILE": 3,
    "FOURTH_QUARTILE": 4,
}


def fetch_calendar(username: str, token: str) -> tuple[list[list[dict]], int]:
    request = urllib.request.Request(
        "https://api.github.com/graphql",
        data=json.dumps({"query": GRAPHQL_QUERY, "variables": {"login": username}}).encode(),
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "User-Agent": "signal-kitchen-profile",
        },
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        payload = json.load(response)

    if payload.get("errors"):
        raise RuntimeError(payload["errors"][0]["message"])

    calendar = payload["data"]["user"]["contributionsCollection"]["contributionCalendar"]
    weeks = []
    for week in calendar["weeks"]:
        days = []
        for day in week["contributionDays"]:
            days.append(
                {
                    "count": day["contributionCount"],
                    "level": LEVELS[day["contributionLevel"]],
                    "weekday": day["weekday"],
                }
            )
        weeks.append(days)
    return weeks[-53:], calendar["totalContributions"]


def demo_calendar() -> tuple[list[list[dict]], int]:
    rng = random.Random(2002)
    weeks = []
    total = 0
    for week_index in range(53):
        energy = 0.35 + 0.38 * math.sin(week_index / 4.2) ** 2
        days = []
        for weekday in range(7):
            count = max(0, int(rng.gauss(energy * 5, 2.5)))
            if rng.random() < 0.34:
                count = 0
            level = 0 if count == 0 else min(4, 1 + count // 3)
            days.append({"count": count, "level": level, "weekday": weekday})
            total += count
        weeks.append(days)
    return weeks, total


def esc(text: str) -> str:
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def calendar_dots(weeks: list[list[dict]], colors: list[str]) -> str:
    start_x, start_y = 42, 94
    step_x, step_y = 8.1, 20
    dots = []
    for week_index, week in enumerate(weeks):
        for day in week:
            x = start_x + week_index * step_x
            y = start_y + day["weekday"] * step_y
            level = day["level"]
            radius = 2.1 if level == 0 else 2.5 + level * 0.25
            opacity = 0.72 if level == 0 else 0.94
            dots.append(
                f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{radius:.1f}" '
                f'fill="{colors[level]}" opacity="{opacity:.2f}"/>'
            )
    return "\n    ".join(dots)


def smooth_path(points: list[tuple[float, float]]) -> str:
    if not points:
        return ""
    commands = [f"M {points[0][0]:.1f} {points[0][1]:.1f}"]
    for index in range(1, len(points)):
        previous = points[index - 1]
        current = points[index]
        midpoint = ((previous[0] + current[0]) / 2, (previous[1] + current[1]) / 2)
        commands.append(f"Q {previous[0]:.1f} {previous[1]:.1f} {midpoint[0]:.1f} {midpoint[1]:.1f}")
    commands.append(f"T {points[-1][0]:.1f} {points[-1][1]:.1f}")
    return " ".join(commands)


def signal_path(weeks: list[list[dict]]) -> tuple[str, tuple[float, float]]:
    totals = [sum(day["count"] for day in week) for week in weeks]
    if not totals:
        totals = [0]
    peak = max(max(totals), 1)
    sampled = totals[-28:]
    points = []
    for index, count in enumerate(sampled):
        x = 770 + index * (386 / max(len(sampled) - 1, 1))
        normalized = math.sqrt(count / peak)
        y = 205 - normalized * 102
        points.append((x, y))
    return smooth_path(points), points[-1]


def moving_ingredients(colors: dict) -> str:
    tokens = [
        ("DATA", "M 395 100 C 480 86, 520 125, 574 164", 0.0, colors["grid"][4]),
        ("CODE", "M 365 145 C 462 130, 530 148, 578 174", 1.7, colors["grid"][3]),
        ("EVAL", "M 405 202 C 485 205, 530 194, 582 183", 3.4, colors["grid"][4]),
        ("IDEA", "M 350 244 C 470 257, 535 224, 586 192", 5.1, colors["grid"][2]),
    ]
    out = []
    for label, path, delay, color in tokens:
        out.append(
            f'''<g opacity="0">
      <rect x="-22" y="-10" width="44" height="20" rx="10" fill="{colors['faint']}" stroke="{color}" stroke-width="1.4"/>
      <text x="0" y="3.5" text-anchor="middle" font-family="ui-monospace, SFMono-Regular, Menlo, Consolas, monospace" font-size="8" font-weight="700" letter-spacing="1" fill="{colors['ink']}">{label}</text>
      <animate attributeName="opacity" values="0;1;1;0" keyTimes="0;.12;.82;1" dur="8s" begin="{delay}s" repeatCount="indefinite"/>
      <animateMotion path="{path}" dur="8s" begin="{delay}s" repeatCount="indefinite" keyTimes="0;.78;1" keyPoints="0;1;1" calcMode="spline" keySplines=".3 .7 .3 1;0 0 1 1"/>
    </g>'''
        )

    particle_paths = [
        ("M 420 86 C 492 88, 538 135, 584 171", 0.6, colors["grid"][4], 5.0),
        ("M 390 122 C 480 118, 536 150, 586 177", 2.1, colors["grid"][2], 4.4),
        ("M 420 176 C 495 177, 548 179, 590 183", 3.7, colors["grid"][3], 5.8),
        ("M 382 228 C 480 241, 548 207, 590 190", 5.3, colors["grid"][4], 4.8),
    ]
    for path, delay, color, radius in particle_paths:
        out.append(
            f'''<circle r="{radius}" fill="{color}" opacity="0" filter="url(#soft-glow)">
      <animate attributeName="opacity" values="0;1;1;0" keyTimes="0;.12;.84;1" dur="6.4s" begin="{delay}s" repeatCount="indefinite"/>
      <animateMotion path="{path}" dur="6.4s" begin="{delay}s" repeatCount="indefinite"/>
    </circle>'''
        )
    return "\n    ".join(out)


def build(theme: str, username: str, weeks: list[list[dict]], total: int) -> str:
    colors = THEMES[theme]
    dots = calendar_dots(weeks, colors["grid"])
    signal, endpoint = signal_path(weeks)
    ingredients = moving_ingredients(colors)
    today = dt.date.today().isoformat()

    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {WIDTH} {HEIGHT}" width="{WIDTH}" height="{HEIGHT}" role="img" aria-labelledby="title desc">
  <title id="title">AGI signal kitchen powered by {esc(username)}'s GitHub contributions</title>
  <desc id="desc">Contribution points travel into a small cooking pot and emerge as a clean signal.</desc>
  <defs>
    <linearGradient id="pot-sheen" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0" stop-color="{colors['pot_edge']}"/>
      <stop offset="1" stop-color="{colors['pot']}"/>
    </linearGradient>
    <linearGradient id="signal-gradient" x1="0" y1="0" x2="1" y2="0">
      <stop offset="0" stop-color="{colors['blue_soft']}"/>
      <stop offset="1" stop-color="{colors['blue']}"/>
    </linearGradient>
    <filter id="soft-glow" x="-40%" y="-40%" width="180%" height="180%">
      <feGaussianBlur stdDeviation="3" result="blur"/>
      <feMerge><feMergeNode in="blur"/><feMergeNode in="SourceGraphic"/></feMerge>
    </filter>
    <style>
      .ingredients-grid {{ animation: breathe 3.2s ease-in-out infinite; }}
      .signal {{ stroke-dasharray: 760; stroke-dashoffset: 760; animation: draw 9s ease-in-out infinite; }}
      .pot-character {{ transform-box: fill-box; transform-origin: center bottom; animation: cook 9s ease-in-out infinite; }}
      .stir {{ transform-box: fill-box; transform-origin: 52% 88%; animation: stir .72s ease-in-out infinite alternate; }}
      .steam-a {{ animation: steam 2.5s ease-in-out infinite; }}
      .steam-b {{ animation: steam 2.5s 1.15s ease-in-out infinite; }}
      .flame {{ transform-box: fill-box; transform-origin: center bottom; animation: flame .48s ease-in-out infinite alternate; }}
      .eye {{ transform-box: fill-box; transform-origin: center; animation: blink 4.2s ease-in-out infinite; }}
      .bubble-a {{ animation: bubble 2.1s ease-in infinite; }}
      .bubble-b {{ animation: bubble 2.1s .7s ease-in infinite; }}
      .bubble-c {{ animation: bubble 2.1s 1.35s ease-in infinite; }}
      .speech {{ transform-box: fill-box; transform-origin: left bottom; animation: speech 9s ease-in-out infinite; }}
      .burst {{ transform-box: fill-box; transform-origin: center; animation: burst 9s ease-out infinite; }}
      .pulse {{ animation: pulse 2.1s ease-in-out infinite; }}
      @keyframes breathe {{ 0%, 100% {{ opacity: .58; }} 50% {{ opacity: 1; }} }}
      @keyframes draw {{ 0%, 43% {{ stroke-dashoffset: 760; opacity: .15; }} 77%, 94% {{ stroke-dashoffset: 0; opacity: 1; }} 100% {{ stroke-dashoffset: 0; opacity: .15; }} }}
      @keyframes cook {{ 0%, 31%, 58%, 100% {{ transform: translateY(0) rotate(0); }} 36% {{ transform: translateY(-8px) rotate(-3deg); }} 40% {{ transform: translateY(1px) rotate(4deg); }} 44% {{ transform: translateY(-6px) rotate(-4deg); }} 48% {{ transform: translateY(0) rotate(3deg); }} 53% {{ transform: translateY(-3px) rotate(-1deg); }} }}
      @keyframes stir {{ from {{ transform: rotate(-13deg); }} to {{ transform: rotate(14deg); }} }}
      @keyframes steam {{ 0% {{ transform: translateY(10px) scale(.75); opacity: 0; }} 35% {{ opacity: .8; }} 100% {{ transform: translateY(-30px) scale(1.12); opacity: 0; }} }}
      @keyframes flame {{ from {{ transform: scale(.78, .78); opacity: .55; }} to {{ transform: scale(1.14, 1.18); opacity: 1; }} }}
      @keyframes blink {{ 0%, 43%, 47%, 100% {{ transform: scaleY(1); }} 45% {{ transform: scaleY(.08); }} }}
      @keyframes bubble {{ 0% {{ transform: translateY(12px) scale(.35); opacity: 0; }} 30% {{ opacity: 1; }} 100% {{ transform: translateY(-42px) scale(1.18); opacity: 0; }} }}
      @keyframes speech {{ 0%, 30%, 64%, 100% {{ transform: scale(.7) translateY(8px); opacity: 0; }} 37%, 57% {{ transform: scale(1) translateY(0); opacity: 1; }} }}
      @keyframes burst {{ 0%, 76%, 88%, 100% {{ transform: scale(.25); opacity: 0; }} 81% {{ transform: scale(1.35); opacity: 1; }} }}
      @keyframes pulse {{ 0%, 100% {{ opacity: .34; }} 50% {{ opacity: 1; }} }}
      @media (prefers-reduced-motion: reduce) {{ * {{ animation: none !important; }} .signal {{ stroke-dashoffset: 0; }} }}
    </style>
  </defs>

  <g aria-label="Contribution ingredients">
    <g class="ingredients-grid">{dots}</g>
    {ingredients}
  </g>

  <g aria-label="AGI cooking pot">
    <g class="speech" opacity="0">
      <rect x="676" y="54" width="112" height="38" rx="17" fill="{colors['faint']}" stroke="{colors['blue_soft']}" stroke-width="1.5"/>
      <path d="M 685 88 L 671 103 L 704 91" fill="{colors['faint']}" stroke="{colors['blue_soft']}" stroke-width="1.5" stroke-linejoin="round"/>
      <text x="732" y="78" text-anchor="middle" font-family="ui-monospace, SFMono-Regular, Menlo, Consolas, monospace" font-size="10" font-weight="700" letter-spacing="1.4" fill="{colors['blue']}">LET HIM COOK</text>
    </g>
    <path class="steam-a" d="M 592 132 C 571 107, 605 92, 590 65" fill="none" stroke="{colors['steam']}" stroke-width="4" stroke-linecap="round" opacity="0"/>
    <path class="steam-b" d="M 651 130 C 670 105, 637 91, 655 62" fill="none" stroke="{colors['steam']}" stroke-width="4" stroke-linecap="round" opacity="0"/>
    <ellipse class="flame" cx="620" cy="272" rx="48" ry="11" fill="{colors['heat']}" opacity=".82" filter="url(#soft-glow)"/>
    <g class="pot-character">
      <path class="stir" d="M 603 58 L 635 190" fill="none" stroke="{colors['pot_edge']}" stroke-width="8" stroke-linecap="round"/>
      <path d="M 550 171 Q 620 143 690 171 L 673 246 Q 620 279 567 246 Z" fill="url(#pot-sheen)"/>
      <path d="M 548 170 Q 620 194 692 170" fill="none" stroke="{colors['blue_soft']}" stroke-width="10" stroke-linecap="round"/>
      <path d="M 562 194 L 532 204" fill="none" stroke="{colors['pot_edge']}" stroke-width="10" stroke-linecap="round"/>
      <path d="M 678 194 L 708 204" fill="none" stroke="{colors['pot_edge']}" stroke-width="10" stroke-linecap="round"/>
      <g class="eye"><circle cx="600" cy="215" r="5" fill="{colors['blue']}"/><circle cx="640" cy="215" r="5" fill="{colors['blue']}"/></g>
      <path d="M 606 231 Q 620 244 634 231" fill="none" stroke="{colors['blue_soft']}" stroke-width="4" stroke-linecap="round"/>
      <circle class="bubble-a" cx="592" cy="171" r="5" fill="{colors['grid'][3]}"/>
      <circle class="bubble-b" cx="621" cy="174" r="7" fill="{colors['grid'][4]}"/>
      <circle class="bubble-c" cx="652" cy="171" r="4" fill="{colors['grid'][2]}"/>
    </g>
  </g>

  <g aria-label="Contribution signal">
    <path d="M 714 186 C 735 186, 748 186, 770 186" fill="none" stroke="{colors['faint']}" stroke-width="2" stroke-dasharray="3 8"/>
    <path d="{signal}" fill="none" stroke="{colors['blue_soft']}" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" opacity=".28"/>
    <path class="signal" d="{signal}" fill="none" stroke="url(#signal-gradient)" stroke-width="4" stroke-linecap="round" stroke-linejoin="round"/>
    <circle r="7" fill="{colors['blue']}" opacity="0" filter="url(#soft-glow)">
      <animate attributeName="opacity" values="0;0;1;1;0" keyTimes="0;.43;.48;.82;.9" dur="9s" repeatCount="indefinite"/>
      <animateMotion path="{signal}" dur="9s" repeatCount="indefinite" keyTimes="0;.43;.82;1" keyPoints="0;0;1;1"/>
    </circle>
    <g transform="translate({endpoint[0]:.1f} {endpoint[1]:.1f})">
      <g class="burst" opacity="0" stroke="{colors['blue']}" stroke-width="3" stroke-linecap="round">
        <path d="M 0 -9 L 0 -22"/><path d="M 0 9 L 0 22"/><path d="M -9 0 L -22 0"/><path d="M 9 0 L 22 0"/>
        <path d="M -7 -7 L -16 -16"/><path d="M 7 7 L 16 16"/><path d="M 7 -7 L 16 -16"/><path d="M -7 7 L -16 16"/>
      </g>
    </g>
    <circle class="pulse" cx="{endpoint[0]:.1f}" cy="{endpoint[1]:.1f}" r="5" fill="{colors['blue']}"/>
  </g>

  <g font-family="ui-monospace, SFMono-Regular, Menlo, Consolas, monospace" font-size="11" letter-spacing="1.8">
    <text x="42" y="302" fill="{colors['muted']}">CONTRIBUTIONS / NOISE</text>
    <text x="620" y="302" text-anchor="middle" fill="{colors['blue']}">AGI 大锅烩</text>
    <text x="1158" y="302" text-anchor="end" fill="{colors['blue']}">SIGNAL / SHIP</text>
  </g>
  <text x="1158" y="322" text-anchor="end" font-family="ui-monospace, SFMono-Regular, Menlo, Consolas, monospace" font-size="9" fill="{colors['muted']}" opacity=".72">updated {today} · {total} contributions</text>
</svg>
'''


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--username", default=os.environ.get("GITHUB_REPOSITORY_OWNER", "tianyi-zhang-02"))
    parser.add_argument("--out-dir", type=pathlib.Path, default=pathlib.Path("dist"))
    parser.add_argument("--demo", action="store_true")
    args = parser.parse_args()

    if args.demo:
        weeks, total = demo_calendar()
    else:
        token = os.environ.get("GITHUB_TOKEN")
        if not token:
            raise SystemExit("GITHUB_TOKEN is required unless --demo is used")
        weeks, total = fetch_calendar(args.username, token)

    args.out_dir.mkdir(parents=True, exist_ok=True)
    for theme in THEMES:
        suffix = "-dark" if theme == "dark" else ""
        path = args.out_dir / f"signal-kitchen{suffix}.svg"
        path.write_text(build(theme, args.username, weeks, total), encoding="utf-8")
        print(f"wrote {path}")


if __name__ == "__main__":
    main()
