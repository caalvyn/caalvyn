# Setup — caalvyn/caalvyn profile

## What's here
- `README.md` — renders on your profile; shows `dark_mode.svg` / `light_mode.svg`
- `generate.py` — pulls live GitHub stats and rebuilds both SVG cards
- `portrait.txt` — your ASCII portrait (regenerate with `img2ascii.py`)
- `img2ascii.py` — photo → ASCII converter
- `.github/workflows/update.yml` — rebuilds the cards daily

## One-time: create the repo and push
The repo **must** be named exactly `caalvyn` (same as your username).

1. On github.com → **New repository** → name it `caalvyn`, make it **Public**,
   do NOT add a README. Create it.
2. From this folder:
   ```bash
   cd ~/github-profile
   git remote add origin https://github.com/caalvyn/caalvyn.git
   git branch -M main
   git push -u origin main
   ```
   (Or with the GitHub CLI once installed: `gh repo create caalvyn/caalvyn --public --source=. --push`)

The push triggers the Action, which fills in your live stats within a minute.

## Optional: fuller stats token
The automatic Action token works for public stats. For the most complete numbers,
add a personal token:
1. github.com → Settings → Developer settings → **Personal access tokens**
   → Fine-grained token, read-only access to your account (Metadata + Contents).
2. In the `caalvyn/caalvyn` repo → Settings → Secrets and variables → Actions
   → **New repository secret** named `GH_STATS_TOKEN`, paste the token.

## Editing your info
Everything you see on the card lives in the `PROFILE` dict at the top of
`generate.py`. Edit, then either push (Action rebuilds) or run locally:
```bash
GITHUB_TOKEN=ghp_xxx python3 generate.py   # regenerates both SVGs
```

## New portrait
```bash
python3 img2ascii.py path/to/photo.png --width 50 --ramp hedvig --contrast 2.0
cp portrait.txt portrait.txt   # generate.py reads portrait.txt
```
