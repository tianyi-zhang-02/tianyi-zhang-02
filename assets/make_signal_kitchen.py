#!/usr/bin/env python3
"""Generate a contribution-powered, self-contained animated profile SVG."""

from __future__ import annotations

import argparse
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
    start_x, start_y = 42, 88
    step_x, step_y = 8.1, 19
    dots = []
    for week_index, week in enumerate(weeks):
        for day in week:
            x = start_x + week_index * step_x
            y = start_y + day["weekday"] * step_y
            level = day["level"]
            size = 4.2 if level == 0 else 4.2 + level * 0.65
            opacity = 0.72 if level == 0 else 0.94
            dots.append(
                f'<rect x="{x - size / 2:.1f}" y="{y - size / 2:.1f}" width="{size:.1f}" height="{size:.1f}" rx="0.8" '
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
    sampled = totals[-25:]
    points = [(770, 205), (792, 205)]
    for index, count in enumerate(sampled):
        x = 808 + index * (348 / max(len(sampled) - 1, 1))
        normalized = math.sqrt(count / peak)
        y = 205 - normalized * 102
        points.append((x, y))
    return smooth_path(points), points[-1]


def build(theme: str, username: str, weeks: list[list[dict]], total: int) -> str:
    colors = THEMES[theme]
    dots = calendar_dots(weeks, colors["grid"])
    signal, endpoint = signal_path(weeks)

    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {WIDTH} {HEIGHT}" width="{WIDTH}" height="{HEIGHT}" role="img" aria-labelledby="title desc">
  <title id="title">{esc(username)}'s pixel signal kitchen</title>
  <desc id="desc">A pixel chef collects one of {total} GitHub contributions, cooks it, and turns it into a signal.</desc>
  <defs>
    <linearGradient id="signal-gradient" x1="0" y1="0" x2="1" y2="0">
      <stop offset="0" stop-color="{colors['blue_soft']}"/>
      <stop offset="1" stop-color="{colors['blue']}"/>
    </linearGradient>
    <filter id="soft-glow" x="-40%" y="-40%" width="180%" height="180%">
      <feGaussianBlur stdDeviation="3" result="blur"/>
      <feMerge><feMergeNode in="blur"/><feMergeNode in="SourceGraphic"/></feMerge>
    </filter>
    <style>
      .grid {{ animation: grid-glow 3.6s ease-in-out infinite; }}
      .scanner {{ animation: scan 10s ease-in-out infinite; }}
      .chosen {{ transform-box: fill-box; transform-origin: center; animation: chosen 10s ease-in-out infinite; }}
      .chef {{ animation: chef-route 10s cubic-bezier(.45,.05,.3,1) infinite; }}
      .chef-bob {{ animation: chef-bob .48s steps(2, end) infinite; }}
      .leg-left {{ transform-box: fill-box; transform-origin: top center; animation: leg-left .48s steps(2, end) infinite; }}
      .leg-right {{ transform-box: fill-box; transform-origin: top center; animation: leg-right .48s steps(2, end) infinite; }}
      .carry {{ animation: carry 10s steps(1, end) infinite; }}
      .pot {{ transform-box: fill-box; transform-origin: center bottom; animation: pot-react 10s steps(1, end) infinite; }}
      .liquid {{ animation: liquid 10s steps(2, end) infinite; }}
      .smoke-a {{ animation: smoke 2s steps(4, end) infinite; }}
      .smoke-b {{ animation: smoke 2s .8s steps(4, end) infinite; }}
      .signal {{ stroke-dasharray: 760; stroke-dashoffset: 760; animation: draw 10s ease-in-out infinite; }}
      .burst {{ transform-box: fill-box; transform-origin: center; animation: burst 10s steps(2, end) infinite; }}
      .status {{ animation: status 10s steps(1, end) infinite; }}
      @keyframes grid-glow {{ 0%, 100% {{ opacity: .62; }} 50% {{ opacity: .96; }} }}
      @keyframes scan {{ 0%, 4% {{ transform: translateX(0); opacity: 0; }} 7% {{ opacity: .8; }} 27% {{ transform: translateX(390px); opacity: .8; }} 30%, 100% {{ transform: translateX(390px); opacity: 0; }} }}
      @keyframes chosen {{ 0%, 20%, 100% {{ transform: scale(1); opacity: .3; }} 25%, 34% {{ transform: scale(1.65); opacity: 1; }} 38% {{ transform: scale(.2); opacity: 0; }} }}
      @keyframes chef-route {{ 0%, 7% {{ transform: translateX(0); opacity: 0; }} 10% {{ opacity: 1; }} 32%, 72% {{ transform: translateX(105px); opacity: 1; }} 83% {{ transform: translateX(0); opacity: 1; }} 87%, 100% {{ transform: translateX(0); opacity: 0; }} }}
      @keyframes chef-bob {{ 0% {{ transform: translateY(0); }} 100% {{ transform: translateY(-4px); }} }}
      @keyframes leg-left {{ 0% {{ transform: rotate(16deg); }} 100% {{ transform: rotate(-16deg); }} }}
      @keyframes leg-right {{ 0% {{ transform: rotate(-16deg); }} 100% {{ transform: rotate(16deg); }} }}
      @keyframes carry {{ 0%, 34% {{ opacity: 1; }} 35%, 100% {{ opacity: 0; }} }}
      @keyframes pot-react {{ 0%, 41%, 61%, 100% {{ transform: translateY(0); }} 44%, 50%, 56% {{ transform: translateY(-5px); }} 47%, 53%, 59% {{ transform: translateY(2px); }} }}
      @keyframes liquid {{ 0%, 40%, 62%, 100% {{ opacity: .45; }} 45%, 59% {{ opacity: 1; }} }}
      @keyframes smoke {{ 0% {{ transform: translateY(12px); opacity: 0; }} 25% {{ opacity: .72; }} 100% {{ transform: translateY(-34px); opacity: 0; }} }}
      @keyframes draw {{ 0%, 52% {{ stroke-dashoffset: 760; opacity: .12; }} 84%, 94% {{ stroke-dashoffset: 0; opacity: 1; }} 100% {{ stroke-dashoffset: 0; opacity: .12; }} }}
      @keyframes burst {{ 0%, 83%, 91%, 100% {{ transform: scale(.2); opacity: 0; }} 87% {{ transform: scale(1.4); opacity: 1; }} }}
      @keyframes status {{ 0%, 39% {{ opacity: .25; }} 43%, 64% {{ opacity: 1; }} 68%, 100% {{ opacity: .25; }} }}
      @media (prefers-reduced-motion: reduce) {{ * {{ animation: none !important; }} .signal {{ stroke-dashoffset: 0; }} }}
    </style>
  </defs>

  <g aria-label="Contribution field">
    <g class="grid">{dots}</g>
    <rect class="scanner" x="36" y="72" width="10" height="140" rx="2" fill="{colors['blue_soft']}" opacity="0"/>
    <rect class="chosen" x="439" y="128" width="9" height="9" rx="1" fill="{colors['blue']}" opacity=".3" filter="url(#soft-glow)"/>
  </g>

  <g class="chef" aria-label="Pixel chef robot" opacity="0">
    <g class="chef-bob">
      <rect x="390" y="77" width="54" height="10" rx="2" fill="{colors['faint']}" stroke="{colors['blue_soft']}" stroke-width="2"/>
      <rect x="399" y="67" width="36" height="12" rx="2" fill="{colors['faint']}" stroke="{colors['blue_soft']}" stroke-width="2"/>
      <rect x="404" y="91" width="28" height="8" fill="{colors['pot_edge']}"/>
      <rect x="394" y="98" width="48" height="42" rx="5" fill="{colors['pot']}" stroke="{colors['pot_edge']}" stroke-width="3"/>
      <rect x="404" y="112" width="6" height="6" fill="{colors['blue']}"/><rect x="426" y="112" width="6" height="6" fill="{colors['blue']}"/>
      <rect x="411" y="128" width="14" height="4" fill="{colors['blue_soft']}"/>
      <rect x="398" y="144" width="40" height="47" rx="3" fill="{colors['pot_edge']}"/>
      <rect x="407" y="151" width="22" height="32" fill="{colors['faint']}"/>
      <rect x="414" y="159" width="8" height="8" fill="{colors['blue']}"/>
      <rect x="383" y="150" width="15" height="9" fill="{colors['pot_edge']}"/><rect x="438" y="150" width="22" height="9" fill="{colors['pot_edge']}"/>
      <rect class="carry" x="458" y="140" width="15" height="15" rx="2" fill="{colors['blue']}" filter="url(#soft-glow)"/>
      <rect class="leg-left" x="401" y="190" width="12" height="25" fill="{colors['pot']}"/>
      <rect class="leg-right" x="423" y="190" width="12" height="25" fill="{colors['pot']}"/>
    </g>
  </g>

  <g aria-label="Flying contribution" opacity="0">
    <rect x="-8" y="-8" width="16" height="16" rx="2" fill="{colors['blue']}" filter="url(#soft-glow)"/>
    <animate attributeName="opacity" values="0;0;1;1;0;0" keyTimes="0;.34;.36;.49;.52;1" dur="10s" repeatCount="indefinite"/>
    <animateMotion path="M 578 145 Q 620 74 640 174" dur="10s" repeatCount="indefinite" keyTimes="0;.34;.51;1" keyPoints="0;0;1;1"/>
  </g>

  <g aria-label="Pixel cooker">
    <g class="smoke-a" opacity="0" fill="{colors['steam']}"><rect x="612" y="121" width="9" height="9"/><rect x="621" y="106" width="9" height="9"/><rect x="612" y="91" width="9" height="9"/></g>
    <g class="smoke-b" opacity="0" fill="{colors['steam']}"><rect x="660" y="127" width="8" height="8"/><rect x="652" y="112" width="8" height="8"/><rect x="660" y="97" width="8" height="8"/></g>
    <g class="pot">
      <rect x="579" y="170" width="122" height="13" fill="{colors['pot_edge']}"/>
      <rect x="566" y="176" width="18" height="12" fill="{colors['pot_edge']}"/><rect x="696" y="176" width="18" height="12" fill="{colors['pot_edge']}"/>
      <path d="M 586 183 H 694 L 681 244 H 599 Z" fill="{colors['pot']}" stroke="{colors['pot_edge']}" stroke-width="4" stroke-linejoin="round"/>
      <g class="liquid" fill="{colors['blue_soft']}"><rect x="588" y="173" width="20" height="7"/><rect x="612" y="173" width="20" height="7"/><rect x="636" y="173" width="20" height="7"/><rect x="660" y="173" width="20" height="7"/></g>
      <rect class="status" x="628" y="211" width="24" height="8" rx="1" fill="{colors['blue']}" opacity=".25"/>
      <rect x="605" y="245" width="22" height="7" fill="{colors['pot_edge']}"/><rect x="653" y="245" width="22" height="7" fill="{colors['pot_edge']}"/>
    </g>
  </g>

  <g aria-label="Contribution signal">
    <path d="M 714 206 H 770" fill="none" stroke="{colors['faint']}" stroke-width="2" stroke-dasharray="4 7"/>
    <path d="{signal}" fill="none" stroke="{colors['blue_soft']}" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" opacity=".28"/>
    <path class="signal" d="{signal}" fill="none" stroke="url(#signal-gradient)" stroke-width="3.6" stroke-linecap="round" stroke-linejoin="round"/>
    <circle r="7" fill="{colors['blue']}" opacity="0" filter="url(#soft-glow)">
      <animate attributeName="opacity" values="0;0;1;1;0" keyTimes="0;.53;.58;.86;.92" dur="10s" repeatCount="indefinite"/>
      <animateMotion path="{signal}" dur="10s" repeatCount="indefinite" keyTimes="0;.53;.86;1" keyPoints="0;0;1;1"/>
    </circle>
    <g transform="translate({endpoint[0]:.1f} {endpoint[1]:.1f})">
      <g class="burst" opacity="0" stroke="{colors['blue']}" stroke-width="3" stroke-linecap="round">
        <path d="M 0 -9 L 0 -22"/><path d="M 0 9 L 0 22"/><path d="M -9 0 L -22 0"/><path d="M 9 0 L 22 0"/>
        <path d="M -7 -7 L -16 -16"/><path d="M 7 7 L 16 16"/><path d="M 7 -7 L 16 -16"/><path d="M -7 7 L -16 16"/>
      </g>
    </g>
    <rect x="{endpoint[0] - 4:.1f}" y="{endpoint[1] - 4:.1f}" width="8" height="8" rx="1" fill="{colors['blue']}"/>
  </g>

  <g font-family="ui-monospace, SFMono-Regular, Menlo, Consolas, monospace" font-size="11" letter-spacing="1.8">
    <text x="42" y="296" fill="{colors['muted']}">01 / COLLECT</text>
    <text x="640" y="296" text-anchor="middle" fill="{colors['blue']}">02 / COOK</text>
    <text x="1158" y="296" text-anchor="end" fill="{colors['blue']}">03 / SHIP</text>
  </g>
  <text x="640" y="318" text-anchor="middle" font-family="ui-monospace, SFMono-Regular, Menlo, Consolas, monospace" font-size="9" letter-spacing="2" fill="{colors['muted']}" opacity=".8">AGI 大锅烩</text>
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
