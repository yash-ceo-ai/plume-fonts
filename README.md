# Plume Fonts

Work in progress: **Plume Sans** and **Plume Mono**, free, open (SIL OFL 1.1) typefaces made to sit beside
[Plume Icons](https://github.com/yash-ceo-ai/plume-icons) in the Renown app and any other project.

Status: **Plume Sans alpha 0.1.0**: Inter (SIL OFL) with every outer corner softened to match Plume Icons' round joins,
round quotes and commas on by default, renamed. Weights 400, 500 and 600 in `fonts/` (TTF and WOFF2). Covers Latin,
Romanian, Vietnamese, Greek and Cyrillic. Not released yet; the letter shapes are still Inter's, only the corners differ.

Preview: open `study/plume-sans.html` (Plume Sans next to Inter, next to Plume Icons, in the Renown UI).

- `docs/font-brief.md`: what we want, the legal rule, the measured candidates and the recommended base font.
- `study/candidates.md`, `study/candidates.json`, `study/missing.txt`: our measurements of six OFL fonts and how well each
  covers the app's own text (English, Romanian, Greek).
- `study/compare.html`: the real UI in each candidate, side by side (run `npm install` first; it reads the fonts from
  `node_modules`).

## Rules

- Nothing from Söhne or any other licensed font goes into this repo or into the fonts. Only OFL sources and our own drawings.
- Modified OFL fonts keep their original copyright notices and are renamed.

## Build Plume Sans

```sh
npm install
python3 -m venv .venv && .venv/bin/pip install fonttools brotli skia-pathops
.venv/bin/python scripts/build_sans.py            # fonts/PlumeSans-{Regular,Medium,SemiBold}.{ttf,woff2}
node scripts/preview.mjs                          # study/plume-sans.html
```

`--radius 50` is the corner size in font units at weight 400 (scaled up for heavier weights). Larger radii make thin
parts of letters disappear (tried 64 and 78); the build keeps a glyph's strokes intact by retrying with a smaller radius.

## Run the study

```sh
npm install
python3 -m venv .venv && .venv/bin/pip install fonttools brotli
.venv/bin/python scripts/measure.py     # study/candidates.*, study/missing.txt
node scripts/compare.mjs                # study/compare.html
```

## Licence

SIL Open Font License 1.1. See [LICENSE](LICENSE).
