"""Builds Plume Sans (alpha) from Inter (SIL OFL 1.1): static 400/500/600, subset to the scripts the app uses, every outer
corner softened to match Plume Icons' round joins, round quotes and commas on by default, renamed.

    .venv/bin/python scripts/build_sans.py [--radius 30] [--out dist/fonts] [--weights 400,500,600]

Corner softening is a morphological opening: erode the outline by r, then grow it back by r with round joins. Stems keep
their width, outer corners become round (radius r), inner corners stay as they are. See docs/font-brief.md."""
import argparse, copy, os, sys
import pathops
from fontTools import subset
from fontTools.pens.cu2quPen import Cu2QuPen
from fontTools.pens.ttGlyphPen import TTGlyphPen
from fontTools.ttLib import TTFont, newTable
from fontTools.ttLib.tables._g_l_y_f import Glyph
from fontTools.varLib import instancer

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "node_modules/inter-ui/variable/InterVariable.woff2")
VERSION = "0.1.0"
STYLE = {400: "Regular", 500: "Medium", 600: "SemiBold"}
# Heavier weights have thicker strokes, so they can take a bigger radius without thin parts disappearing.
RADIUS_SCALE = {400: 1.0, 500: 1.12, 600: 1.3}

# Latin, Latin Extended A/B, Latin Extended Additional (Vietnamese), Greek, Cyrillic, punctuation, currency, arrows,
# maths and the few symbols the app text uses.
UNICODES = (
    list(range(0x20, 0x7F)) + list(range(0xA0, 0x250)) + list(range(0x2B0, 0x300)) + list(range(0x300, 0x370))
    + list(range(0x370, 0x400)) + list(range(0x400, 0x530)) + list(range(0x1E00, 0x1F00))
    + list(range(0x2000, 0x2070)) + list(range(0x2070, 0x20D0)) + list(range(0x2100, 0x2200))
    + list(range(0x2200, 0x2300)) + list(range(0x2300, 0x2400)) + list(range(0x25A0, 0x2600)) + [0x2713, 0x2714, 0x2717]
)
DEFAULT_ON = ["ss03"]  # round quotes and commas: they sit with Plume's round terminals


def _op(a, b, kind):
    try:
        return pathops.op(a, b, kind)
    except pathops.PathOpsError:
        a2, b2 = pathops.Path(a), pathops.Path(b)
        a2.simplify(fix_winding=True, keep_starting_points=False)
        b2.simplify(fix_winding=True, keep_starting_points=False)
        return pathops.op(a2, b2, kind)


def _soften_once(path: pathops.Path, r: float, why: list = None):
    """Round the outer corners of a filled outline with radius r (font units). Returns None if that would damage it."""
    if r <= 0:
        return path
    try:
        base = pathops.Path(path)
        base.simplify(fix_winding=True, keep_starting_points=False)
        band = pathops.Path(base)
        band.stroke(2 * r, pathops.LineCap.BUTT_CAP, pathops.LineJoin.ROUND_JOIN, 4)
        band.convertConicsToQuads(0.1)
        eroded = _op(base, band, pathops.PathOp.DIFFERENCE)
        if not len(list(eroded.contours)):
            return path  # too thin to round: keep it as it is
        grow = pathops.Path(eroded)
        grow.stroke(2 * r, pathops.LineCap.BUTT_CAP, pathops.LineJoin.ROUND_JOIN, 4)
        grow.convertConicsToQuads(0.1)
        out = _op(eroded, grow, pathops.PathOp.UNION)
        # Rounding can leave tiny specks; drop them.
        clean = pathops.Path()
        for c in out.contours:
            if abs(c.area) >= SPECK:
                c.draw(clean.getPen())
        out = clean
        # Safety: rounding must not lose a stroke or merge or split shapes. Keep the original outline if it did.
        if len(list(out.contours)) != len(list(base.contours)) or out.area < 0.92 * abs(base.area):
            UNSAFE.append(1)
            if why is not None:
                why.append((len(list(base.contours)), len(list(out.contours)), round(out.area / max(abs(base.area), 1), 3)))
            return None
        return out
    except pathops.PathOpsError:
        FAILED.append(1)
        return None


SPECK = 4000  # font units squared: smaller islands are rounding debris
KEPT: dict = {}
FAILED: list = []
STEPS = (1.0, 0.8, 0.64, 0.5, 0.36)  # try the full radius first, then smaller ones for glyphs with thin necks


def soften(path: pathops.Path, r: float, why: list = None):
    """Soften with the biggest radius in STEPS that keeps every stroke. Returns (path, factor used or 0)."""
    for f in STEPS:
        out = _soften_once(path, r * f, why if f == STEPS[0] else None)
        if out is not None:
            return out, f
    return path, 0
UNSAFE: list = []


def apply_default_features(font: TTFont, tags: list[str]) -> list[str]:
    """Make single-substitution features default by remapping the cmap (so no CSS is needed)."""
    if "GSUB" not in font:
        return []
    gsub = font["GSUB"].table
    cmap = font.getBestCmap()
    done = []
    subs = {}
    for rec in gsub.FeatureList.FeatureRecord:
        if rec.FeatureTag in tags:
            for li in rec.Feature.LookupListIndex:
                lk = gsub.LookupList.Lookup[li]
                for st in lk.SubTable:
                    st = getattr(st, "ExtSubTable", st)
                    if hasattr(st, "mapping"):
                        subs.update(st.mapping)
            done.append(rec.FeatureTag)
    for table in font["cmap"].tables:
        for code, g in list(table.cmap.items()):
            if g in subs:
                table.cmap[code] = subs[g]
    return sorted(set(done))


def rename(font: TTFont, weight: int):
    style = STYLE[weight]
    fam = "Plume Sans"
    full = f"{fam} {style}" if style != "Regular" else fam
    ps = f"PlumeSans-{style}"
    legacy_fam = fam if style == "Regular" else f"{fam} {style}"
    name = font["name"]
    name.names = []
    notice = (
        "Copyright 2016 The Inter Project Authors (https://github.com/rsms/inter). "
        "Copyright 2026 The Plume Fonts Authors (https://github.com/yash-ceo-ai/plume-fonts)."
    )
    rec = {
        0: notice,
        1: legacy_fam,
        2: "Regular",
        3: f"{VERSION};PLUME;{ps}",
        4: full if style != "Regular" else f"{fam} Regular",
        5: f"Version {VERSION}",
        6: ps,
        13: "This Font Software is licensed under the SIL Open Font License, Version 1.1. This license is available with a FAQ at: https://openfontlicense.org",
        14: "https://openfontlicense.org",
        16: fam,
        17: style,
    }
    for nid, text in rec.items():
        name.setName(text, nid, 3, 1, 0x409)
        name.setName(text, nid, 1, 0, 0)
    font["OS/2"].usWeightClass = weight
    font["OS/2"].fsSelection = (font["OS/2"].fsSelection & ~0b100001) | 0b1000000  # REGULAR bit, not bold or italic
    font["head"].macStyle = 0
    font["OS/2"].achVendID = "PLUM"


def build(weight: int, radius: float, out_dir: str) -> dict:
    font = TTFont(SRC)
    font = instancer.instantiateVariableFont(font, {"wght": weight, "opsz": 14}, inplace=False)
    opts = subset.Options()
    opts.layout_features = ["*"]
    opts.glyph_names = False
    opts.notdef_outline = True
    opts.name_IDs = ["*"]
    opts.hinting = False
    opts.drop_tables += ["STAT", "MVAR", "HVAR", "avar", "fvar", "gvar", "cvar", "DSIG"]
    sub = subset.Subsetter(opts)
    sub.populate(unicodes=UNICODES)
    sub.subset(font)

    glyf, hmtx = font["glyf"], font["hmtx"]
    gs = font.getGlyphSet()
    n = rounded = 0
    for gname in font.getGlyphOrder():
        g = glyf[gname]
        if g.numberOfContours == 0 and not g.isComposite():
            continue
        path = pathops.Path()
        gs[gname].draw(path.getPen(glyphSet=gs))
        n += 1
        why = []
        soft, used = soften(path, radius * RADIUS_SCALE[weight], why)
        if used != 1.0:
            KEPT[gname] = used
        pen = TTGlyphPen(None)
        soft.draw(Cu2QuPen(pen, max_err=0.5, reverse_direction=True))
        new = pen.glyph()
        glyf[gname] = new
        rounded += 1
        new.recalcBounds(glyf)
        hmtx[gname] = (hmtx[gname][0], new.xMin if new.numberOfContours else 0)
    apply_default_features_done = apply_default_features(font, DEFAULT_ON)
    rename(font, weight)
    font["maxp"].recalc(font) if hasattr(font["maxp"], "recalc") else None
    os.makedirs(out_dir, exist_ok=True)
    base = os.path.join(out_dir, f"PlumeSans-{STYLE[weight]}")
    font.flavor = None
    font.save(base + ".ttf")
    font.flavor = "woff2"
    font.save(base + ".woff2")
    return {"weight": weight, "smaller_radius": sum(1 for v in KEPT.values() if v), "kept_sharp": sum(1 for v in KEPT.values() if not v), "glyphs": len(font.getGlyphOrder()), "outlines": n, "default_features": apply_default_features_done,
            "ttf_kb": round(os.path.getsize(base + ".ttf") / 1024), "woff2_kb": round(os.path.getsize(base + ".woff2") / 1024)}


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--radius", type=float, default=50)
    ap.add_argument("--out", default=os.path.join(ROOT, "fonts"))
    ap.add_argument("--weights", default="400,500,600")
    a = ap.parse_args()
    for w in [int(x) for x in a.weights.split(",")]:
        print(build(w, a.radius, a.out), flush=True)
