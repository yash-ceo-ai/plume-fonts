# Plume Fonts

**Plume**: a free, open (SIL OFL 1.1) typeface drawn from scratch to match
[Plume Icons](https://github.com/yash-ceo-ai/plume-icons). No outline, spacing or kerning from Inter, Söhne or any other
font went into it.

Status: **alpha 0.1.0**. Previews (run `npm run preview` and `npm run slider` first if they are missing):

- `study/plume.html`: Plume in the Renown UI, with weights, sizes and every character.
- `study/compare-slider.html`: a before and after slider, today's font (Geist) against Plume, on the same screen.

## How it is made

Every letter is a few centre-lines (lines and arcs) on a 1000-unit grid, stroked with round caps and round joins, exactly how
Plume Icons are drawn (a 1.8 line on a 24 grid is 75 units; Regular is 76). The strokes are merged into one outline per
glyph and written to a TrueType font with `fontTools`. The letters live in `scripts/build_plume.py`; change a number and
rebuild.

- Weights: Regular 400 (stroke 76), Medium 500 (92), SemiBold 600 (110). Files in `fonts/` (TTF and WOFF2).
- Figures are tabular by default (every digit has the same width), so columns line up.
- Covers: Basic Latin, Latin-1 accents, Romanian (ă â î ș ț), common symbols, currency (€ £ ¥), arrows (← → ↑ ↓) and ✓.
- Not yet: Greek, Cyrillic (the app's Greek text falls back to another font until they are drawn), Arabic (uses a fallback
  font), a variable font file, Plume Mono, hinting, and a full kerning pass.

## Build

```sh
npm install
python3 -m venv .venv && .venv/bin/pip install fonttools brotli skia-pathops
.venv/bin/python scripts/build_plume.py     # fonts/Plume-{Regular,Medium,SemiBold}.{ttf,woff2}
node scripts/preview.mjs                    # study/plume.html
node scripts/slider.mjs                     # study/compare-slider.html
```

## Use

```css
@font-face { font-family: 'Plume'; src: url('/fonts/Plume-Regular.woff2') format('woff2'); font-weight: 400; font-display: swap; }
@font-face { font-family: 'Plume'; src: url('/fonts/Plume-Medium.woff2') format('woff2'); font-weight: 500; font-display: swap; }
@font-face { font-family: 'Plume'; src: url('/fonts/Plume-SemiBold.woff2') format('woff2'); font-weight: 600; font-display: swap; }
body { font-family: 'Plume', system-ui, sans-serif; }
```

## Rules

- Nothing from a licensed font goes into this repo. Letters are our own drawings.
- `docs/font-brief.md` and `study/` hold the early look study of free fonts (history only; none of them is used).

## Licence

SIL Open Font License 1.1. See [LICENSE](LICENSE).
