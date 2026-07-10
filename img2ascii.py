#!/usr/bin/env python3
"""
img2ascii.py — convert a photo into a monospace ASCII-art portrait
suitable for a GitHub profile README (neofetch style).

Usage:
    python3 img2ascii.py INPUT.jpg [--width 60] [--invert] [--ramp dense|medium|blocks]
    # writes portrait.txt next to this script and prints it

Tips:
    - Use a high-contrast, well-lit headshot with a plain background.
    - Width 50–65 looks best on a GitHub profile beside the info column.
    - Try --invert if your background is dark; try different --ramp values.
"""
import argparse
import sys
from PIL import Image, ImageEnhance, ImageOps

RAMPS = {
    # dark -> light (we map dark pixels to dense chars by default)
    "dense":  "@%#*+=-:. ",
    "medium": "@8&WM#*oahkbdpqwmZO0QLCJUYXzcvunxrjft/\\|()1{}[]?-_+~<>i!lI;:,\"^`'. ",
    "blocks": "█▓▒░ ",
    "hedvig": "MWNXK0Okxdolc:;,'. ",
}


def to_ascii(path, width=60, ramp="medium", invert=False, contrast=1.6, gamma=1.0):
    chars = RAMPS[ramp]
    src = Image.open(path)
    # Flatten transparency onto white so the background becomes spaces.
    if src.mode in ("RGBA", "LA") or (src.mode == "P" and "transparency" in src.info):
        src = src.convert("RGBA")
        bg = Image.new("RGBA", src.size, (255, 255, 255, 255))
        src = Image.alpha_composite(bg, src)
    img = src.convert("L")
    img = ImageOps.autocontrast(img)
    img = ImageEnhance.Contrast(img).enhance(contrast)

    w, h = img.size
    # characters are ~2x taller than wide -> compress rows
    aspect = h / w
    new_w = width
    new_h = max(1, int(aspect * new_w * 0.5))
    img = img.resize((new_w, new_h))

    px = list(img.getdata())
    n = len(chars) - 1
    out_lines = []
    for row in range(new_h):
        line = []
        for col in range(new_w):
            val = px[row * new_w + col] / 255.0
            if gamma != 1.0:
                val = val ** gamma
            if invert:
                val = 1.0 - val
            # val 0 (dark) -> chars[0] (dense) ; val 1 (light) -> space
            idx = int(val * n)
            line.append(chars[idx])
        out_lines.append("".join(line).rstrip())
    return "\n".join(out_lines)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("input")
    ap.add_argument("--width", type=int, default=60)
    ap.add_argument("--ramp", choices=list(RAMPS), default="medium")
    ap.add_argument("--invert", action="store_true")
    ap.add_argument("--contrast", type=float, default=1.6)
    ap.add_argument("--gamma", type=float, default=1.0)
    ap.add_argument("--out", default="portrait.txt")
    args = ap.parse_args()

    art = to_ascii(args.input, args.width, args.ramp, args.invert,
                   args.contrast, args.gamma)
    with open(args.out, "w") as f:
        f.write(art + "\n")
    print(art)
    print(f"\n[written to {args.out}  |  {args.width} cols]", file=sys.stderr)


if __name__ == "__main__":
    main()
