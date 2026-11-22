# Plume Fonts

Work in progress: **Plume Sans** and **Plume Mono**, free, open (SIL OFL 1.1) typefaces made to sit beside
[Plume Icons](https://github.com/yash-ceo-ai/plume-icons) in the Renown app and any other project.

Status: Task 1 of the plan is done (design brief and candidate study). Nothing is released yet.

- `docs/font-brief.md`: what we want, the legal rule, the measured candidates and the recommended base font.
- `study/candidates.md`, `study/candidates.json`, `study/missing.txt`: our measurements of six OFL fonts and how well each
  covers the app's own text (English, Romanian, Greek).
- `study/compare.html`: the real UI in each candidate, side by side (run `npm install` first; it reads the fonts from
  `node_modules`).

## Rules

- Nothing from Söhne or any other licensed font goes into this repo or into the fonts. Only OFL sources and our own drawings.
- Modified OFL fonts keep their original copyright notices and are renamed.

## Run the study

```sh
npm install
python3 -m venv .venv && .venv/bin/pip install fonttools brotli
.venv/bin/python scripts/measure.py     # study/candidates.*, study/missing.txt
node scripts/compare.mjs                # study/compare.html
```

## Licence

SIL Open Font License 1.1. See [LICENSE](LICENSE).
