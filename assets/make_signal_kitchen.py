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
HEIGHT = 300

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
    start_x, start_y = 42, 76
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
        x = 756 + index * (400 / max(len(sampled) - 1, 1))
        normalized = math.sqrt(count / peak)
        y = 174 - normalized * 92
        points.append((x, y))
    return smooth_path(points), points[-1]


def moving_ingredients(colors: list[str]) -> str:
    paths = [
        ("M 420 92 C 485 92, 510 126, 565 145", 0.0, 6.2, colors[4]),
        ("M 390 132 C 478 135, 515 146, 565 151", 1.4, 7.1, colors[3]),
        ("M 430 184 C 485 180, 525 168, 568 158", 2.8, 6.7, colors[2]),
        ("M 365 214 C 470 218, 526 190, 574 165", 4.1, 7.8, colors[4]),
    ]
    out = []
    for path, delay, duration, color in paths:
        out.append(
            f'''<circle r="3.4" fill="{color}" opacity="0">
      <animate attributeName="opacity" values="0;1;1;0" dur="{duration}s" begin="{delay}s" repeatCount="indefinite"/>
      <animateMotion path="{path}" dur="{duration}s" begin="{delay}s" repeatCount="indefinite"/>
    </circle>'''
        )
    return "\n    ".join(out)


def build(theme: str, username: str, weeks: list[list[dict]], total: int) -> str:
    colors = THEMES[theme]
    dots = calendar_dots(weeks, colors["grid"])
    signal, endpoint = signal_path(weeks)
    ingredients = moving_ingredients(colors["grid"])
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
      .signal {{ stroke-dasharray: 760; stroke-dashoffset: 760; animation: draw 5.8s ease-in-out infinite; }}
      .stir {{ transform-box: fill-box; transform-origin: 50% 88%; animation: stir 2.6s ease-in-out infinite alternate; }}
      .steam-a {{ animation: steam 3.8s ease-in-out infinite; }}
      .steam-b {{ animation: steam 3.8s 1.6s ease-in-out infinite; }}
      .flame {{ transform-box: fill-box; transform-origin: center bottom; animation: flame 1.1s ease-in-out infinite alternate; }}
      .pulse {{ animation: pulse 2.1s ease-in-out infinite; }}
      @keyframes draw {{ 0%, 12% {{ stroke-dashoffset: 760; opacity: .24; }} 58%, 88% {{ stroke-dashoffset: 0; opacity: 1; }} 100% {{ stroke-dashoffset: 0; opacity: .24; }} }}
      @keyframes stir {{ from {{ transform: rotate(-7deg); }} to {{ transform: rotate(8deg); }} }}
      @keyframes steam {{ 0% {{ transform: translateY(8px); opacity: 0; }} 35% {{ opacity: .65; }} 100% {{ transform: translateY(-20px); opacity: 0; }} }}
      @keyframes flame {{ from {{ transform: scale(.86, .88); opacity: .68; }} to {{ transform: scale(1.05, 1.08); opacity: 1; }} }}
      @keyframes pulse {{ 0%, 100% {{ opacity: .34; }} 50% {{ opacity: 1; }} }}
      @media (prefers-reduced-motion: reduce) {{ * {{ animation: none !important; }} .signal {{ stroke-dashoffset: 0; }} }}
    </style>
  </defs>

  <g aria-label="Contribution ingredients">
    {dots}
    {ingredients}
  </g>

  <g aria-label="AGI cooking pot">
    <ellipse class="flame" cx="620" cy="224" rx="31" ry="8" fill="{colors['heat']}" opacity=".78" filter="url(#soft-glow)"/>
    <path class="stir" d="M 612 67 L 629 165" fill="none" stroke="{colors['pot_edge']}" stroke-width="6" stroke-linecap="round"/>
    <path class="steam-a" d="M 600 119 C 586 101, 610 91, 598 70" fill="none" stroke="{colors['steam']}" stroke-width="3" stroke-linecap="round" opacity="0"/>
    <path class="steam-b" d="M 638 118 C 651 100, 630 89, 643 67" fill="none" stroke="{colors['steam']}" stroke-width="3" stroke-linecap="round" opacity="0"/>
    <path d="M 573 151 Q 620 137 667 151 L 657 207 Q 620 228 583 207 Z" fill="url(#pot-sheen)"/>
    <path d="M 570 151 Q 620 166 670 151" fill="none" stroke="{colors['blue_soft']}" stroke-width="7" stroke-linecap="round"/>
    <path d="M 579 168 L 557 176" fill="none" stroke="{colors['pot_edge']}" stroke-width="7" stroke-linecap="round"/>
    <path d="M 661 168 L 683 176" fill="none" stroke="{colors['pot_edge']}" stroke-width="7" stroke-linecap="round"/>
    <circle cx="609" cy="184" r="3" fill="{colors['blue']}"/>
    <circle cx="631" cy="184" r="3" fill="{colors['blue']}"/>
    <path d="M 613 195 Q 620 201 627 195" fill="none" stroke="{colors['blue_soft']}" stroke-width="2.4" stroke-linecap="round"/>
    <circle class="pulse" cx="581" cy="133" r="2.8" fill="{colors['blue_soft']}"/>
    <circle class="pulse" cx="661" cy="126" r="2.2" fill="{colors['blue']}"/>
  </g>

  <g aria-label="Contribution signal">
    <path d="M 704 155 C 728 155, 735 155, 756 155" fill="none" stroke="{colors['faint']}" stroke-width="1.5" stroke-dasharray="3 7"/>
    <path d="{signal}" fill="none" stroke="{colors['blue_soft']}" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" opacity=".28"/>
    <path class="signal" d="{signal}" fill="none" stroke="url(#signal-gradient)" stroke-width="3.2" stroke-linecap="round" stroke-linejoin="round"/>
    <circle class="pulse" cx="{endpoint[0]:.1f}" cy="{endpoint[1]:.1f}" r="5" fill="{colors['blue']}"/>
  </g>

  <g font-family="ui-monospace, SFMono-Regular, Menlo, Consolas, monospace" font-size="11" letter-spacing="1.8">
    <text x="42" y="264" fill="{colors['muted']}">RAW CONTRIBUTIONS</text>
    <text x="620" y="264" text-anchor="middle" fill="{colors['blue']}">AGI 大锅烩</text>
    <text x="1158" y="264" text-anchor="end" fill="{colors['blue']}">SIGNAL</text>
  </g>
  <text x="1158" y="286" text-anchor="end" font-family="ui-monospace, SFMono-Regular, Menlo, Consolas, monospace" font-size="9" fill="{colors['muted']}" opacity=".72">updated {today} · {total} contributions</text>
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
