"""Task 1: measure the OFL candidate fonts with our own tools (fontTools) and check how much of the app's text each
covers. Output: study/candidates.json and study/candidates.md. Run: .venv/bin/python scripts/measure.py"""
import glob, json, os, re, statistics, sys
from fontTools.ttLib import TTFont

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FS = os.path.join(ROOT, "node_modules/@fontsource-variable")
MESSAGES = os.environ.get("MESSAGES_DIR", "/Users/yash/Projects/seofast/messages")
CANDIDATES = ["geist", "inter", "hanken-grotesk", "instrument-sans", "figtree", "schibsted-grotesk"]
LANGS = ["en", "ro", "el", "ar"]


def load(c):
    files = sorted(glob.glob(f"{FS}/{c}/files/{c}-*-wght-normal.woff2"))
    return {os.path.basename(f).split(f"{c}-")[1].replace("-wght-normal.woff2", ""): TTFont(f) for f in files}


def text_of(lang):
    chars = set()
    paths = glob.glob(f"{MESSAGES}/{lang}.json") + glob.glob(f"{MESSAGES}/*/{lang}.json")
    for p in paths:
        try:
            data = json.load(open(p, encoding="utf-8"))
        except Exception:
            continue
        stack = [data]
        while stack:
            v = stack.pop()
            if isinstance(v, dict):
                stack.extend(v.values())
            elif isinstance(v, str):
                chars.update(re.sub(r"\{[^}]*\}", "", v))
    return {ch for ch in chars if ch.strip() and ord(ch) > 31}


def metrics(font):
    upm = font["head"].unitsPerEm
    os2 = font["OS/2"]
    cmap = font.getBestCmap()
    hmtx = font["hmtx"]
    adv = lambda ch: hmtx[cmap[ord(ch)]][0] / upm
    lower = [adv(c) for c in "abcdefghijklmnopqrstuvwxyz" if ord(c) in cmap]
    digits = [adv(c) for c in "0123456789" if ord(c) in cmap]
    axes = {a.axisTag: (a.minValue, a.defaultValue, a.maxValue) for a in font["fvar"].axes} if "fvar" in font else {}
    return {
        "upm": upm,
        "x_height": round(os2.sxHeight / upm, 3),
        "cap_height": round(os2.sCapHeight / upm, 3),
        "x_to_cap": round(os2.sxHeight / os2.sCapHeight, 3),
        "ascender": round(font["hhea"].ascent / upm, 3),
        "descender": round(font["hhea"].descent / upm, 3),
        "avg_lower_width": round(statistics.mean(lower), 3),
        "avg_digit_width": round(statistics.mean(digits), 3),
        "tabular_figures_default": len({round(d, 3) for d in digits}) == 1,
        "o_width": round(adv("o"), 3),
        "weight_axis": axes.get("wght"),
    }


def main():
    out = {}
    need = {l: text_of(l) for l in LANGS}
    for c in CANDIDATES:
        subsets = load(c)
        if not subsets:
            print("missing", c, file=sys.stderr)
            continue
        m = metrics(subsets["latin"])
        have = set()
        for f in subsets.values():
            have.update(chr(k) for k in f.getBestCmap())
        scripts = sorted(s for s in subsets if not s.endswith("-ext"))
        cover = {}
        for l, chars in need.items():
            if chars:
                cover[l] = round(100 * len(chars & have) / len(chars), 1)
        m["subsets"] = sorted(subsets)
        m["scripts"] = scripts
        m["language_coverage_pct"] = cover
        out[c] = m
    os.makedirs(f"{ROOT}/study", exist_ok=True)
    json.dump(out, open(f"{ROOT}/study/candidates.json", "w"), indent=2)

    rows = ["| Font | x-height | cap | x/cap | avg a-z width | tabular digits | weights | scripts | el | ro | ru | vi |", "|---|---|---|---|---|---|---|---|---|---|---|---|"]
    for c, m in out.items():
        w = m["weight_axis"]
        cv = m["language_coverage_pct"]
        rows.append(
            f"| {c} | {m['x_height']} | {m['cap_height']} | {m['x_to_cap']} | {m['avg_lower_width']} | {'yes' if m['tabular_figures_default'] else 'no'} | "
            f"{int(w[0])}-{int(w[2])} | {', '.join(m['scripts'])} | {cv.get('el','-')} | {cv.get('ro','-')} | {cv.get('ru','-')} | {cv.get('vi','-')} |"
        )
    open(f"{ROOT}/study/candidates.md", "w").write("\n".join(rows) + "\n")
    print("\n".join(rows))
    print("\nlanguages measured:", {l: len(c) for l, c in need.items()})


def missing_report():
    """Which characters of the app's own text each candidate lacks (written to study/missing.txt)."""
    lines = []
    need = {l: text_of(l) for l in ["en", "ro", "el"]}
    for c in CANDIDATES:
        have = set()
        for f in load(c).values():
            have.update(chr(k) for k in f.getBestCmap())
        for l, chars in need.items():
            miss = sorted(chars - have)
            lines.append(f"{c} {l}: {len(miss)} missing  {''.join(miss)[:80]}")
    open(f"{ROOT}/study/missing.txt", "w").write("\n".join(lines) + "\n")
    print("\n".join(lines))


main()
missing_report()
