#!/usr/bin/env python3
"""
generate.py — render neofetch-style profile cards (dark + light SVG) with
live GitHub stats. Designed to run in a GitHub Action but also works locally.

Env:
    GITHUB_TOKEN   a PAT or the Action's GITHUB_TOKEN (read:user, repo scope)
    GH_USER        github username (default: caalvyn)

Without a token it renders with placeholder stats so you can preview the look.

Outputs:  dark_mode.svg, light_mode.svg
"""
import html
import json
import os
import urllib.request

USER = os.environ.get("GH_USER", "caalvyn")
TOKEN = os.environ.get("GITHUB_TOKEN", "")

# ---- static profile fields (edit these) -----------------------------------
PROFILE = {
    "title": f"{USER}@dev",
    "rows_top": [
        ("OS", "Linux, Windows"),
        ("Uptime", "25 years"),
        ("Host", "calvyn.dev"),
        ("IDE", "VS Code, IDEA, WebStorm"),
        ("Shell", "bash / zsh"),
    ],
    "rows_lang": [
        ("Languages.Programming", "Python, JavaScript, TypeScript"),
        ("Languages.Frameworks", "Next.js, Django, Wagtail, React"),
        ("Languages.Real", "English"),
    ],
    "rows_hobby": [
        ("Hobbies.Software", "Autonomous Builds, AI tooling, Web Developer"),
        ("Hobbies.Hardware", "Home Lab"),
    ],
    "rows_contact": [
        ("Email", "calvyn.dev@icloud.com"),
        ("Website", "https://calvyn.dev"),
        ("GitHub", f"@{USER}"),
    ],
}

# ---- themes ----------------------------------------------------------------
THEMES = {
    "dark": {
        "bg": "#1a1b27", "border": "#2f3352", "art": "#70a5fd",
        "title": "#70a5fd", "sep": "#41485e", "label": "#e4b854",
        "value": "#d5d8e2", "add": "#57ab5a", "del": "#e5534b",
    },
    "light": {
        "bg": "#fffefe", "border": "#e4e2e2", "art": "#4577c9",
        "title": "#2b6cb0", "sep": "#c8ccd4", "label": "#b3801d",
        "value": "#2f3440", "add": "#2a7d3a", "del": "#c23b34",
    },
}

CHAR_W = 8.4          # px per monospace char at font-size 14
LINE_H = 17           # px per line
FONT = ("ui-monospace, 'SF Mono', 'Cascadia Code', 'Fira Code', "
        "Consolas, 'Courier New', monospace")
INNER_COLS = 48       # dotted-leader column width for the info side


def gh_graphql(query, variables):
    if not TOKEN:
        return None
    req = urllib.request.Request(
        "https://api.github.com/graphql",
        data=json.dumps({"query": query, "variables": variables}).encode(),
        headers={"Authorization": f"bearer {TOKEN}",
                 "Content-Type": "application/json",
                 "User-Agent": "profile-generator"},
    )
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)


def fetch_stats():
    """Return dict of live stats, or sensible placeholders without a token."""
    q = """
    query($login:String!){
      user(login:$login){
        followers{totalCount}
        following{totalCount}
        repositories(first:100, ownerAffiliations:OWNER, isFork:false){
          totalCount
          nodes{ stargazerCount }
        }
        contributionsCollection{
          totalCommitContributions
          restrictedContributionsCount
        }
      }
    }"""
    try:
        data = gh_graphql(q, {"login": USER})
        u = data["data"]["user"]
        stars = sum(n["stargazerCount"] for n in u["repositories"]["nodes"])
        commits = (u["contributionsCollection"]["totalCommitContributions"]
                   + u["contributionsCollection"]["restrictedContributionsCount"])
        return {
            "repos": u["repositories"]["totalCount"],
            "stars": stars,
            "commits": commits,
            "followers": u["followers"]["totalCount"],
            "following": u["following"]["totalCount"],
        }
    except Exception as e:  # no token or API error -> placeholders
        print(f"[generate] using placeholder stats ({e})")
        return {"repos": "??", "stars": "??", "commits": "??",
                "followers": "??", "following": "??"}


def esc(s):
    return html.escape(str(s), quote=True)


def leader_row(label, value, cols=INNER_COLS):
    """Build (label, dots, value) with dotted leader filling to `cols`."""
    label, value = str(label), str(value)
    fill = max(1, cols - len(label) - len(value) - 2)
    return label, " " + "." * fill + " ", value


def build_svg(theme_name, stats, art_lines):
    t = THEMES[theme_name]
    art_w = max(len(l) for l in art_lines)
    info_x = 20 + int(art_w * CHAR_W) + 28
    y = 34
    parts = []

    # --- flatten the info side into an ordered list of items ---
    # ("gap",) | ("header", text) | ("row", label, value)
    items = [("header", PROFILE["title"])]
    items += [("row", k, v) for k, v in PROFILE["rows_top"]]
    items += [("gap",)]
    items += [("row", k, v) for k, v in PROFILE["rows_lang"]]
    items += [("gap",)]
    items += [("row", k, v) for k, v in PROFILE["rows_hobby"]]
    items += [("gap",), ("header", "Contact")]
    items += [("row", k, v) for k, v in PROFILE["rows_contact"]]
    items += [("gap",), ("header", "GitHub Stats")]
    items += [
        ("row", "Repos", stats["repos"]),
        ("row", "Stars", stats["stars"]),
        ("row", "Commits (this year)", stats["commits"]),
        ("row", "Followers", stats["followers"]),
        ("row", "Following", stats["following"]),
    ]

    # inner column width (chars) = widest "label + 2 + value", also >= headers
    cols = 2
    for it in items:
        if it[0] == "row":
            cols = max(cols, len(str(it[1])) + len(str(it[2])) + 2)
        elif it[0] == "header":
            cols = max(cols, len(str(it[1])) + 3)

    def span(text, color, bold=False):
        w = ' font-weight="600"' if bold else ""
        return f'<tspan fill="{color}"{w}>{esc(text)}</tspan>'

    def line(x, spans, ypos):
        parts.append(
            f'<text x="{x}" y="{ypos}" xml:space="preserve" '
            f'font-family="{FONT}" font-size="14">{"".join(spans)}</text>')

    # --- portrait (left) ---
    for i, l in enumerate(art_lines):
        parts.append(
            f'<text x="20" y="{y + i*LINE_H}" xml:space="preserve" '
            f'font-family="{FONT}" font-size="14" fill="{t["art"]}">'
            f'{esc(l)}</text>')

    # --- info (right) ---
    iy = y
    for it in items:
        if it[0] == "gap":
            iy += LINE_H // 2 + 3
        elif it[0] == "header":
            text = it[1]
            dashes = "-" * max(2, cols - len(text) - 1)
            line(info_x, [span(text + " ", t["title"], True),
                          span(dashes, t["sep"])], iy)
            iy += LINE_H
        else:  # row
            label, value = str(it[1]), str(it[2])
            fill = max(1, cols - len(label) - len(value) - 2)
            line(info_x, [span(label, t["label"], True),
                          span(" " + "." * fill + " ", t["sep"]),
                          span(value, t["value"])], iy)
            iy += LINE_H

    height = max(y + len(art_lines) * LINE_H, iy) + 20
    width = info_x + int(cols * CHAR_W) + 24

    svg = (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" '
        f'height="{height}" viewBox="0 0 {width} {height}" '
        f'font-family="{FONT}">'
        f'<rect x="1" y="1" width="{width-2}" height="{height-2}" rx="10" '
        f'fill="{t["bg"]}" stroke="{t["border"]}" stroke-width="1.5"/>'
        + "".join(parts) + "</svg>"
    )
    return svg


def main():
    with open(os.path.join(os.path.dirname(__file__), "portrait.txt")) as f:
        art_lines = [l.rstrip("\n") for l in f if l.strip("\n")]
    stats = fetch_stats()
    for name in ("dark", "light"):
        svg = build_svg(name, stats, art_lines)
        out = os.path.join(os.path.dirname(__file__), f"{name}_mode.svg")
        with open(out, "w") as f:
            f.write(svg)
        print(f"[generate] wrote {out}")


if __name__ == "__main__":
    main()
