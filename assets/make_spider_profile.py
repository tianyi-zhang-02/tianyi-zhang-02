#!/usr/bin/env python3
"""Generate a pixel-art Spider-Man contribution swing for a GitHub profile."""

from __future__ import annotations

import argparse
import json
import math
import os
import pathlib
import random
import urllib.request


WIDTH = 1200
HEIGHT = 320

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

THEMES = {
    "light": {
        "background": "#FFFFFF",
        "grid": ["#EEF1F7", "#DCE3FB", "#B5C2F1", "#7188DD", "#2447C6"],
        "red": "#E0343E",
        "red_dark": "#8F1725",
        "blue": "#2148B8",
        "blue_dark": "#142B68",
        "outline": "#111827",
        "eye": "#FFFFFF",
        "web": "#9DA7BC",
        "signal": "#2447C6",
        "muted": "#8A909C",
    },
    "dark": {
        "background": "#0D1117",
        "grid": ["#202638", "#2F3B64", "#485A94", "#7589CC", "#A3B3FF"],
        "red": "#FF5964",
        "red_dark": "#B82A39",
        "blue": "#6F8EFF",
        "blue_dark": "#394E9E",
        "outline": "#080B12",
        "eye": "#FFFFFF",
        "web": "#6F778A",
        "signal": "#9FB0FF",
        "muted": "#858DA0",
    },
}


def fetch_calendar(username: str, token: str) -> tuple[list[list[dict]], int]:
    request = urllib.request.Request(
        "https://api.github.com/graphql",
        data=json.dumps({"query": GRAPHQL_QUERY, "variables": {"login": username}}).encode(),
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "User-Agent": "spider-contribution-profile",
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


def contribution_grid(weeks: list[list[dict]], colors: list[str]) -> str:
    dots = []
    start_x, start_y = 56, 112
    step_x, step_y = 20.4, 22
    for week_index, week in enumerate(weeks[-53:]):
        for day in week:
            level = day["level"]
            size = 6 if level == 0 else 7 + level
            x = start_x + week_index * step_x
            y = start_y + day["weekday"] * step_y
            dots.append(
                f'<rect x="{x - size / 2:.1f}" y="{y - size / 2:.1f}" width="{size}" height="{size}" '
                f'rx="1.2" fill="{colors[level]}" opacity="{0.42 if level == 0 else 0.86}"/>'
            )
    return "\n    ".join(dots)


def swing_path(weeks: list[list[dict]]) -> str:
    totals = [sum(day["count"] for day in week) for week in weeks[-53:]]
    peak = max(max(totals), 1)
    points = []
    for index, count in enumerate(totals):
        x = 54 + index * (1092 / max(len(totals) - 1, 1))
        level = math.sqrt(count / peak)
        wave = math.sin(index * 0.72) * 24
        y = 205 - level * 92 + wave
        points.append((x, max(58, min(244, y))))

    commands = [f"M {points[0][0]:.1f} {points[0][1]:.1f}"]
    for index in range(1, len(points)):
        previous = points[index - 1]
        current = points[index]
        midpoint = ((previous[0] + current[0]) / 2, (previous[1] + current[1]) / 2)
        commands.append(f"Q {previous[0]:.1f} {previous[1]:.1f} {midpoint[0]:.1f} {midpoint[1]:.1f}")
    commands.append(f"T {points[-1][0]:.1f} {points[-1][1]:.1f}")
    return " ".join(commands)


def core(colors: dict) -> str:
    return f'''
      <path d="M -11 -42 H 10 L 16 -34 V -15 L 10 -7 H -10 L -16 -15 V -34 Z" fill="{colors['red']}" stroke="{colors['outline']}" stroke-width="4"/>
      <path d="M -10 -30 L -2 -26 L -8 -16 L -13 -18 Z" fill="{colors['eye']}" stroke="{colors['outline']}" stroke-width="2"/>
      <path d="M 10 -30 L 2 -26 L 8 -16 L 13 -18 Z" fill="{colors['eye']}" stroke="{colors['outline']}" stroke-width="2"/>
      <path d="M 0 -40 V -8 M -13 -33 L 13 -15 M 13 -33 L -13 -15" stroke="{colors['red_dark']}" stroke-width="1.4" opacity=".9"/>
      <path d="M -12 -7 H 12 L 18 13 L 12 34 H -12 L -18 13 Z" fill="{colors['red']}" stroke="{colors['outline']}" stroke-width="4"/>
      <path d="M -12 18 H 12 L 15 36 H -15 Z" fill="{colors['blue']}" stroke="{colors['outline']}" stroke-width="3"/>
      <path d="M 0 -3 V 21 M -12 4 H 12 M -15 12 H 15" stroke="{colors['red_dark']}" stroke-width="1.5" opacity=".9"/>
      <path d="M 0 3 L 5 11 L 0 18 L -5 11 Z" fill="{colors['outline']}"/>
'''


def pose_frames(colors: dict) -> str:
    body = core(colors)
    outline = colors["outline"]
    red = colors["red"]
    blue = colors["blue"]
    web = colors["web"]

    return f'''
    <g class="frame frame-a">
      <path d="M 30 -18 L 110 -125" stroke="{web}" stroke-width="3" stroke-linecap="square"/>
      <g transform="rotate(-18)">{body}
        <path d="M 13 -2 L 24 -4 L 38 -28 L 31 -35 L 13 -12 Z" fill="{red}" stroke="{outline}" stroke-width="4"/>
        <path d="M -14 0 L -28 4 L -45 22 L -38 29 L -10 13 Z" fill="{red}" stroke="{outline}" stroke-width="4"/>
        <path d="M -9 33 L -25 42 L -42 61 L -34 68 L -8 51 Z" fill="{blue}" stroke="{outline}" stroke-width="4"/>
        <path d="M 9 33 L 25 38 L 45 51 L 40 61 L 12 53 Z" fill="{blue}" stroke="{outline}" stroke-width="4"/>
        <path d="M -42 61 L -52 65 L -49 75 L -34 68 Z M 45 51 L 56 51 L 57 61 L 40 61 Z" fill="{red}" stroke="{outline}" stroke-width="3"/>
      </g>
    </g>

    <g class="frame frame-b">
      <path d="M 22 -25 L 82 -138" stroke="{web}" stroke-width="3" stroke-linecap="square"/>
      <g transform="rotate(12)">{body}
        <path d="M 12 -4 L 24 -8 L 31 -37 L 22 -40 L 9 -15 Z" fill="{red}" stroke="{outline}" stroke-width="4"/>
        <path d="M -12 -3 L -27 -10 L -37 -35 L -28 -40 L -8 -14 Z" fill="{red}" stroke="{outline}" stroke-width="4"/>
        <path d="M -10 34 L -31 43 L -39 68 L -29 72 L -8 52 Z" fill="{blue}" stroke="{outline}" stroke-width="4"/>
        <path d="M 10 34 L 30 43 L 39 67 L 29 72 L 8 52 Z" fill="{blue}" stroke="{outline}" stroke-width="4"/>
        <path d="M -39 68 L -47 77 L -37 83 L -29 72 Z M 39 67 L 48 76 L 38 83 L 29 72 Z" fill="{red}" stroke="{outline}" stroke-width="3"/>
      </g>
    </g>

    <g class="frame frame-c">
      <path d="M -26 -18 L -104 -126" stroke="{web}" stroke-width="3" stroke-linecap="square"/>
      <g transform="rotate(178)">{body}
        <path d="M 12 -3 L 28 -8 L 44 -27 L 37 -35 L 9 -14 Z" fill="{red}" stroke="{outline}" stroke-width="4"/>
        <path d="M -12 -3 L -28 -8 L -44 -27 L -37 -35 L -9 -14 Z" fill="{red}" stroke="{outline}" stroke-width="4"/>
        <path d="M -10 34 L -34 42 L -51 59 L -44 68 L -9 52 Z" fill="{blue}" stroke="{outline}" stroke-width="4"/>
        <path d="M 10 34 L 34 42 L 51 59 L 44 68 L 9 52 Z" fill="{blue}" stroke="{outline}" stroke-width="4"/>
        <path d="M -51 59 L -60 66 L -53 75 L -44 68 Z M 51 59 L 60 66 L 53 75 L 44 68 Z" fill="{red}" stroke="{outline}" stroke-width="3"/>
      </g>
    </g>

    <g class="frame frame-d">
      <g transform="rotate(-5)">{body}
        <path d="M 12 -3 L 30 -8 L 53 -18 L 57 -8 L 16 10 Z" fill="{red}" stroke="{outline}" stroke-width="4"/>
        <path d="M -12 -3 L -30 -8 L -53 -18 L -57 -8 L -16 10 Z" fill="{red}" stroke="{outline}" stroke-width="4"/>
        <path d="M -10 34 L -33 38 L -53 54 L -47 64 L -8 53 Z" fill="{blue}" stroke="{outline}" stroke-width="4"/>
        <path d="M 10 34 L 29 49 L 46 69 L 36 76 L 7 54 Z" fill="{blue}" stroke="{outline}" stroke-width="4"/>
        <path d="M -53 54 L -64 58 L -61 68 L -47 64 Z M 46 69 L 51 81 L 40 84 L 36 76 Z" fill="{red}" stroke="{outline}" stroke-width="3"/>
      </g>
    </g>

    <g class="frame frame-e">
      <g transform="translate(0 17)">{body}
        <path d="M 12 -3 L 24 -2 L 40 16 L 33 23 L 11 11 Z" fill="{red}" stroke="{outline}" stroke-width="4"/>
        <path d="M -12 -3 L -24 -2 L -40 16 L -33 23 L -11 11 Z" fill="{red}" stroke="{outline}" stroke-width="4"/>
        <path d="M -10 34 L -34 44 L -51 41 L -52 53 L -22 60 L -4 51 Z" fill="{blue}" stroke="{outline}" stroke-width="4"/>
        <path d="M 10 34 L 34 44 L 51 41 L 52 53 L 22 60 L 4 51 Z" fill="{blue}" stroke="{outline}" stroke-width="4"/>
        <path d="M -51 41 L -63 39 L -65 50 L -52 53 Z M 51 41 L 63 39 L 65 50 L 52 53 Z" fill="{red}" stroke="{outline}" stroke-width="3"/>
      </g>
    </g>
'''


def build(theme: str, username: str, weeks: list[list[dict]], total: int) -> str:
    colors = THEMES[theme]
    grid = contribution_grid(weeks, colors["grid"])
    path = swing_path(weeks)
    frames = pose_frames(colors)

    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {WIDTH} {HEIGHT}" width="{WIDTH}" height="{HEIGHT}" role="img" aria-labelledby="title desc" shape-rendering="crispEdges">
  <title id="title">Spider-Man swings through {username}'s contribution graph</title>
  <desc id="desc">A high-detail pixel Spider-Man follows a path generated from {total} GitHub contributions.</desc>
  <defs>
    <filter id="glow" x="-40%" y="-40%" width="180%" height="180%">
      <feGaussianBlur stdDeviation="3" result="blur"/>
      <feMerge><feMergeNode in="blur"/><feMergeNode in="SourceGraphic"/></feMerge>
    </filter>
    <linearGradient id="trail" x1="0" y1="0" x2="1" y2="0">
      <stop offset="0" stop-color="{colors['signal']}" stop-opacity=".08"/>
      <stop offset=".55" stop-color="{colors['signal']}" stop-opacity=".48"/>
      <stop offset="1" stop-color="{colors['signal']}"/>
    </linearGradient>
    <style>
      .grid {{ animation: grid 3.4s ease-in-out infinite; }}
      .trail {{ stroke-dasharray: 1700; stroke-dashoffset: 1700; animation: trail 8s ease-in-out infinite; }}
      .runner {{ animation: runner 8s ease-in-out infinite; }}
      .frame {{ opacity: 0; }}
      .frame-a {{ animation: frame-a 8s steps(1, end) infinite; }}
      .frame-b {{ animation: frame-b 8s steps(1, end) infinite; }}
      .frame-c {{ animation: frame-c 8s steps(1, end) infinite; }}
      .frame-d {{ animation: frame-d 8s steps(1, end) infinite; }}
      .frame-e {{ animation: frame-e 8s steps(1, end) infinite; }}
      .spark {{ transform-box: fill-box; transform-origin: center; animation: spark 8s steps(2, end) infinite; }}
      @keyframes grid {{ 0%, 100% {{ opacity: .48; }} 50% {{ opacity: .78; }} }}
      @keyframes trail {{ 0%, 8% {{ stroke-dashoffset: 1700; opacity: .1; }} 79%, 92% {{ stroke-dashoffset: 0; opacity: 1; }} 100% {{ stroke-dashoffset: 0; opacity: .1; }} }}
      @keyframes runner {{ 0%, 4% {{ opacity: 0; }} 8%, 91% {{ opacity: 1; }} 96%, 100% {{ opacity: 0; }} }}
      @keyframes frame-a {{ 0%, 19.9% {{ opacity: 1; }} 20%, 100% {{ opacity: 0; }} }}
      @keyframes frame-b {{ 0%, 19.9% {{ opacity: 0; }} 20%, 39.9% {{ opacity: 1; }} 40%, 100% {{ opacity: 0; }} }}
      @keyframes frame-c {{ 0%, 39.9% {{ opacity: 0; }} 40%, 59.9% {{ opacity: 1; }} 60%, 100% {{ opacity: 0; }} }}
      @keyframes frame-d {{ 0%, 59.9% {{ opacity: 0; }} 60%, 79.9% {{ opacity: 1; }} 80%, 100% {{ opacity: 0; }} }}
      @keyframes frame-e {{ 0%, 79.9% {{ opacity: 0; }} 80%, 96% {{ opacity: 1; }} 96.1%, 100% {{ opacity: 0; }} }}
      @keyframes spark {{ 0%, 88%, 97%, 100% {{ transform: scale(.2); opacity: 0; }} 93% {{ transform: scale(1.4); opacity: 1; }} }}
      @media (prefers-reduced-motion: reduce) {{ * {{ animation: none !important; }} .trail {{ stroke-dashoffset: 0; }} .runner, .frame-a {{ opacity: 1; }} }}
    </style>
  </defs>

  <g class="grid">{grid}</g>
  <path d="{path}" fill="none" stroke="{colors['web']}" stroke-width="1.4" opacity=".22"/>
  <path class="trail" d="{path}" fill="none" stroke="url(#trail)" stroke-width="4" stroke-linecap="square" stroke-linejoin="miter"/>

  <g class="runner" opacity="0">
    <g transform="scale(1.05)">{frames}</g>
    <animateMotion path="{path}" dur="8s" repeatCount="indefinite" rotate="0" keyTimes="0;.08;.92;1" keyPoints="0;0;1;1" calcMode="spline" keySplines="0 0 1 1;.22 .61 .36 1;0 0 1 1"/>
  </g>

  <g class="spark" transform="translate(1146 163)" opacity="0" stroke="{colors['signal']}" stroke-width="4">
    <path d="M 0 -8 V -24 M 0 8 V 24 M -8 0 H -24 M 8 0 H 24"/>
    <path d="M -6 -6 L -17 -17 M 6 6 L 17 17 M 6 -6 L 17 -17 M -6 6 L -17 17"/>
  </g>

  <text x="48" y="298" font-family="ui-monospace, SFMono-Regular, Menlo, Consolas, monospace" font-size="10" letter-spacing="2.4" fill="{colors['muted']}">YOUR FRIENDLY NEIGHBORHOOD CONTRIBUTOR</text>
</svg>
'''


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--username", default="tianyi-zhang-02")
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
        path = args.out_dir / f"spider-contributions{suffix}.svg"
        path.write_text(build(theme, args.username, weeks, total), encoding="utf-8")
        print(f"wrote {path}")


if __name__ == "__main__":
    main()
