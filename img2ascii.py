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


def to_ascii(path, width=60, ramp="medium", invert=False, contrast=1.6,
             gamma=1.0, crop=None, autocrop=False, row_scale=0.5):
    chars = RAMPS[ramp]
    src = Image.open(path)
    # Flatten transparency onto white so the background becomes spaces.
    if src.mode in ("RGBA", "LA") or (src.mode == "P" and "transparency" in src.info):
        src = src.convert("RGBA")
        if autocrop:
            box = src.getchannel("A").getbbox()   # tight bounds of the subject
            if box:
                src = src.crop(box)
        bg = Image.new("RGBA", src.size, (255, 255, 255, 255))
        src = Image.alpha_composite(bg, src)
    if crop:
        src = src.crop(crop)                        # explicit L,T,R,B pixel box
    img = src.convert("L")
    img = ImageOps.autocontrast(img)
    img = ImageEnhance.Contrast(img).enhance(contrast)

    w, h = img.size
    # characters are ~2x taller than wide -> compress rows by row_scale
    aspect = h / w
    new_w = width
    new_h = max(1, int(aspect * new_w * row_scale))
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
    ap.add_argument("--crop", default=None,
                    help="pixel box L,T,R,B to crop before converting")
    ap.add_argument("--autocrop", action="store_true",
                    help="crop to the subject's non-transparent bounds")
    ap.add_argument("--row-scale", type=float, default=0.5,
                    help="row compression (0.5 for 2:1 cells)")
    ap.add_argument("--out", default="portrait.txt")
    args = ap.parse_args()

    crop = tuple(int(x) for x in args.crop.split(",")) if args.crop else None
    art = to_ascii(args.input, args.width, args.ramp, args.invert,
                   args.contrast, args.gamma, crop=crop,
                   autocrop=args.autocrop, row_scale=args.row_scale)
    with open(args.out, "w") as f:
        f.write(art + "\n")
    print(art)
    print(f"\n[written to {args.out}  |  {args.width} cols]", file=sys.stderr)


if __name__ == "__main__":
    main()
