# Plume Sans: design brief and candidate study (Task 1)

Status: Task 1 done, waiting on the owner's choice of base font (Task 2).

## Goal

A free, open (SIL OFL 1.1) typeface family, **Plume Sans** (and later **Plume Mono**), that matches the Plume Icons
style and reads as a premium UI font in the Renown app, with no licence fees for us or anyone else.

## Legal rule for this project

- No outline, spacing or kerning data from Söhne or any other licensed font goes into Plume. That includes Klim's
  "Test Söhne" trial files: their licence allows trying them in design work only, not modifying or building on them.
- Söhne is used here only as a reference for qualities, from Klim's public description (a refined grotesque in the
  Akzidenz-Grotesk and Helvetica tradition, with a New York signage influence) and from looking at it on screen.
- Plume Sans is derived only from OFL fonts (modification and redistribution are allowed if the result is renamed and
  the original copyright notices are kept) and from our own drawings.

## Traits we want

| Trait | Target | Why |
|---|---|---|
| Tone | Calm, neutral, a little warm | The app is a monochrome dashboard; the type must not shout |
| Terminals | Horizontal cuts on most letters, slightly softened corners | Grotesque clarity, softened to sit beside Plume's round joins |
| x-height | 0.52 to 0.55 em (x/cap about 0.74) | Legible at 13 to 14px in tables |
| Width | Average a-z advance about 0.53 em | Same density as the current layout (Geist) so no screen reflows |
| Figures | Tabular by default in tables (`tnum`), proportional in prose | KPI and table columns line up |
| Weights | 400, 500, 600 first, variable axis 300 to 700 | The design system only uses 400, 500 and 600 |
| Scripts | Latin, Latin Extended (Romanian), Greek, Cyrillic | The app ships en, ro, el and ar; Arabic uses a fallback |
| Details | Distinct 1, l, I; open 6 and 9; a clear single-storey or double-storey g chosen on purpose | Reads well for IDs, domains and numbers |

## Candidates measured (our own script, `scripts/measure.py`)

All six are OFL and available as variable fonts. Numbers are in em units.

| Font | x-height | cap | x/cap | avg a-z width | tabular digits by default | weights | scripts |
|---|---|---|---|---|---|---|---|
| Geist | 0.530 | 0.710 | 0.746 | 0.534 | no (use `tnum`) | 100-900 | Latin, Cyrillic, Vietnamese |
| **Inter** | 0.546 | 0.728 | 0.750 | 0.536 | no (use `tnum`) | 100-900 | Latin, **Greek**, Cyrillic, Vietnamese |
| Hanken Grotesk | 0.493 | 0.697 | 0.707 | 0.504 | yes | 100-900 | Latin, Vietnamese |
| Instrument Sans | 0.510 | 0.720 | 0.708 | 0.525 | no | 400-700 | Latin |
| Figtree | 0.500 | 0.700 | 0.714 | 0.499 | no | 300-900 | Latin |
| Schibsted Grotesk | 0.527 | 0.703 | 0.750 | 0.526 | no | 400-900 | Latin |

Coverage of the app's own text (`study/missing.txt`):

- English and Romanian: every candidate covers all letters. The only gaps are the symbols `← → ↵ ≈ ⋯ ⌘ ▲ ▼ ✓`,
  which the app draws with icons or a fallback anyway.
- Greek: **only Inter covers it** (95%; the rest is the same symbols). Geist covers 61%, so Greek users today see a
  system font mixed into Geist text. Hanken Grotesk, Instrument Sans, Figtree and Schibsted have no Greek.

Side-by-side render in the real UI (sidebar, KPI, table, body, Greek and Romanian lines): `study/compare.html`.

## What the comparison shows

- **Geist and Inter** have the closest density and rhythm to what the app uses now. Inter has horizontal terminals
  and an open, even texture, the closest of the free fonts to the Helvetica and Akzidenz lineage that Söhne comes from.
  Geist is cleaner and more geometric.
- **Hanken Grotesk, Figtree and Instrument Sans** are smaller on the em (lower x-height), so text looks about 5 to 8%
  smaller at the same size and would need re-tuning of the layout.
- **Schibsted Grotesk** has the same proportions as Geist but is Latin only and more editorial.

## Recommendation (owner decides)

Use **Inter** as the starting point for Plume Sans:

1. It is the only free candidate with Greek, Cyrillic and Vietnamese, so we don't have to draw about 70 Greek glyphs per
   weight to cover the app's Greek screens.
2. Its proportions match what the layout already uses (x-height, width), so nothing reflows.
3. It has a full OpenType feature set (tabular figures, stylistic alternates) and a maintained variable build.
4. It doesn't reserve its name, so we may modify it as long as we rename it and keep Inter's copyright notice.

Risk: Inter is very common. The answer is in Task 3: reshape the terminals, the figures (1, 4, 7), the G, R, a, g, y and
the spacing, so the result is recognisably Plume, not "Inter again". Geist stays as a visual reference for rounding.

Alternative: start from Geist, which looks more distinctive today, and draw Greek ourselves (extra work in Task 5).
