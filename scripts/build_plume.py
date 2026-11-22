"""Builds Plume, our own typeface, from stroke skeletons. No outlines from any other font.

Every letter is a few centre-lines (lines and arcs) on a 1000-unit grid. They are stroked with round caps and round joins,
the same way Plume Icons are drawn (1.8 line on a 24 grid = 75 units), then merged into one outline per glyph.

    .venv/bin/python scripts/build_plume.py [--out fonts] [--weights 400,500,600] [--only abc]

Weights: stroke width 76 (Regular), 92 (Medium), 110 (SemiBold) units.
"""
import argparse, math, os, sys
import pathops
from pathops import LineCap, LineJoin, PathOp
from fontTools.fontBuilder import FontBuilder
from fontTools.pens.cu2quPen import Cu2QuPen
from fontTools.pens.transformPen import TransformPen
from fontTools.pens.ttGlyphPen import TTGlyphPen

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
VERSION = "0.3.0"
UPM = 1000
XH, CAP, ASC, DESC, OVER = 545, 720, 770, -215, 10  # outer x-height, cap height, ascender, descender, round overshoot
WEIGHTS = {400: ("Regular", 76), 500: ("Medium", 92), 600: ("SemiBold", 110)}
KY = 1.09  # strokes are drawn with the height stretched by KY, then squeezed back: horizontals come out 1/KY thinner than verticals
TAB = 570  # advance of every digit: figures line up in tables by default


class Shape:
    """One glyph under construction. Skeleton strokes go in with m/l/c/arc; solid dots with dot/ring."""

    def __init__(self, h, ox=0.0):
        self.h, self.ox, self.T = h, ox, None
        self.strokes, self.fills = pathops.Path(), pathops.Path()
        self.sp, self.fp = self.strokes.getPen(), self.fills.getPen()
        self.cur, self.is_open = None, False
        # skeleton heights: centre-line of a flat edge that sits at the given outer height
        self.yb, self.yx, self.yc, self.ya, self.yd = h, XH - h, CAP - h, ASC - h, DESC + h

    def pt(self, x, y):
        if self.T:
            x, y = self.T(x, y)
        return (x + self.ox, y * KY)

    def m(self, x, y):
        self._end()
        self.sp.moveTo(self.pt(x, y)); self.cur, self.is_open = (x, y), True

    def l(self, x, y):
        self.sp.lineTo(self.pt(x, y)); self.cur = (x, y)

    def c(self, x1, y1, x2, y2, x, y):
        self.sp.curveTo(self.pt(x1, y1), self.pt(x2, y2), self.pt(x, y)); self.cur = (x, y)

    def z(self):
        self.sp.closePath(); self.is_open = False

    def _end(self):
        if self.is_open:
            self.sp.endPath(); self.is_open = False

    def poly(self, *pts, close=False):
        self.m(*pts[0])
        for p in pts[1:]:
            self.l(*p)
        if close:
            self.z()

    def arc(self, cx, cy, rx, ry, a0, a1, move=False):
        """Elliptical arc from angle a0 to a1 in degrees (counter-clockwise is positive)."""
        n = max(1, int(math.ceil(abs(a1 - a0) / 90.0)))
        step = (a1 - a0) / n
        start = (cx + rx * math.cos(math.radians(a0)), cy + ry * math.sin(math.radians(a0)))
        if move:
            self.m(*start)
        elif self.cur is None or abs(self.cur[0] - start[0]) > 0.01 or abs(self.cur[1] - start[1]) > 0.01:
            self.l(*start)
        k = 4 / 3 * math.tan(math.radians(step) / 4)
        for i in range(n):
            ps, pe = math.radians(a0 + i * step), math.radians(a0 + (i + 1) * step)
            x0, y0 = cx + rx * math.cos(ps), cy + ry * math.sin(ps)
            x3, y3 = cx + rx * math.cos(pe), cy + ry * math.sin(pe)
            self.c(x0 - k * rx * math.sin(ps), y0 + k * ry * math.cos(ps), x3 + k * rx * math.sin(pe), y3 - k * ry * math.cos(pe), x3, y3)

    def ell(self, cx, cy, rx, ry):
        self.arc(cx, cy, rx, ry, 0, 360, move=True)
        self.z()

    # solid shapes (not stroked)
    def _fill_circle(self, cx, cy, r, sign=1):
        n = 4
        pen = self.fp
        pts = [(cx + r * math.cos(math.radians(sign * 90 * i)), cy + r * math.sin(math.radians(sign * 90 * i))) for i in range(n + 1)]
        k = 4 / 3 * math.tan(math.radians(90) / 4)
        pen.moveTo(self.pt(*pts[0]))
        for i in range(n):
            a = math.radians(sign * 90 * i)
            b = math.radians(sign * 90 * (i + 1))
            x0, y0 = cx + r * math.cos(a), cy + r * math.sin(a)
            x3, y3 = cx + r * math.cos(b), cy + r * math.sin(b)
            kk = k * sign
            pen.curveTo(self.pt(x0 - kk * r * math.sin(a), y0 + kk * r * math.cos(a)), self.pt(x3 + kk * r * math.sin(b), y3 - kk * r * math.cos(b)), self.pt(x3, y3))
        pen.closePath()

    def dot(self, cx, cy, r=None):
        self._fill_circle(cx, cy, r or self.h * 1.12)

    def ring(self, cx, cy, r_out, r_in):
        self._fill_circle(cx, cy, r_out, 1)
        self._fill_circle(cx, cy, r_in, -1)

    def outline(self):
        """Outline every skeleton stroke on its own, then merge them (strokes that overlap must add, never cancel)."""
        self._end()
        out = pathops.Path()
        for c in self.strokes.contours:
            piece = pathops.Path()
            c.draw(piece.getPen())
            piece.stroke(2 * self.h, LineCap.ROUND_CAP, LineJoin.ROUND_JOIN, 4)
            piece.convertConicsToQuads(0.05)
            piece.simplify(fix_winding=True, keep_starting_points=False)
            out = pathops.op(out, piece, PathOp.UNION) if len(list(out.contours)) else piece
        if len(list(self.fills.contours)):
            f = pathops.Path(self.fills)
            f.simplify(fix_winding=True, keep_starting_points=False)
            out = pathops.op(out, f, PathOp.UNION) if len(list(out.contours)) else f
        out.simplify(fix_winding=True, keep_starting_points=False)
        return out


# ---------------------------------------------------------------------------------------------------------------
# Letters. Each function draws one glyph at x = 0 (its left outer edge) and returns its outer width.
# Heights: yb baseline centre-line, yx x-height, yc cap height, ya ascender, yd descender (all centre-lines).
# ---------------------------------------------------------------------------------------------------------------
G = {}


def glyph(*chars):
    def deco(fn):
        for ch in chars:
            G[ch] = fn
        return fn
    return deco


def bowl_rx(s, W): return W / 2 - s.h
def bowl_ry(s): return XH / 2 + OVER - s.h


@glyph("o")
def _o(s):
    W = 490; s.ell(W / 2, XH / 2, bowl_rx(s, W), bowl_ry(s)); return W


@glyph("c")
def _c(s):
    W = 430; h = s.h
    s.arc(W / 2 + 4, XH / 2, (W + 8) / 2 - h, bowl_ry(s), 42, 318, move=True); return W


@glyph("e")
def _e(s):
    W = 470; rx = bowl_rx(s, W)
    s.m(s.h, XH / 2); s.l(W - s.h, XH / 2)
    s.arc(W / 2, XH / 2, rx, bowl_ry(s), 0, 322); return W


@glyph("a")
def _a(s):
    W = 470; s.ell(W / 2, XH / 2, bowl_rx(s, W), bowl_ry(s)); s.m(W - s.h, s.yx); s.l(W - s.h, s.yb); return W


@glyph("d")
def _d(s):
    W = 480; s.ell(W / 2, XH / 2, bowl_rx(s, W), bowl_ry(s)); s.m(W - s.h, s.ya); s.l(W - s.h, s.yb); return W


@glyph("b")
def _b(s):
    W = 480; s.ell(W / 2, XH / 2, bowl_rx(s, W), bowl_ry(s)); s.m(s.h, s.ya); s.l(s.h, s.yb); return W


@glyph("q")
def _q(s):
    W = 480; s.ell(W / 2, XH / 2, bowl_rx(s, W), bowl_ry(s)); s.m(W - s.h, s.yx); s.l(W - s.h, s.yd); return W


@glyph("p")
def _p(s):
    W = 480; s.ell(W / 2, XH / 2, bowl_rx(s, W), bowl_ry(s)); s.m(s.h, s.yx); s.l(s.h, s.yd); return W


@glyph("g")
def _g(s):
    W = 480; h = s.h
    s.ell(W / 2, XH / 2, bowl_rx(s, W), bowl_ry(s))
    r = 118; cy = DESC + h + r
    s.m(W - h, s.yx); s.l(W - h, cy); s.arc(W / 2, cy, W / 2 - h, r, 0, -158); return W


def arch(s, x0, x1, top, yarch):
    """Arch from the stem at x0 (height yarch) up over to x1, ending at yarch on the right; returns nothing."""
    s.arc((x0 + x1) / 2, yarch, (x1 - x0) / 2, top - yarch, 180, 0, move=True)


@glyph("n")
def _n(s):
    W = 440; h = s.h; ya = XH * 0.50
    s.m(h, s.yb); s.l(h, s.yx)
    arch(s, h, W - h, s.yx + OVER, ya); s.l(W - h, s.yb); return W


@glyph("h")
def _h(s):
    W = 440; h = s.h; ya = XH * 0.50
    s.m(h, s.yb); s.l(h, s.ya)
    arch(s, h, W - h, s.yx + OVER, ya); s.l(W - h, s.yb); return W


@glyph("m")
def _m(s):
    W = 700; h = s.h; ya = XH * 0.50; mid = W / 2
    s.m(h, s.yb); s.l(h, s.yx)
    arch(s, h, mid, s.yx + OVER, ya); s.l(mid, s.yb)
    arch(s, mid, W - h, s.yx + OVER, ya); s.l(W - h, s.yb); return W


@glyph("u")
def _u(s):
    W = 440; h = s.h; yb = XH * 0.50 - 0
    s.m(h, s.yx); s.l(h, yb); s.arc(W / 2, yb, W / 2 - h, yb - (h - OVER), 180, 360)
    s.m(W - h, s.yx); s.l(W - h, s.yb); return W


@glyph("r")
def _r(s):
    W = 330; h = s.h; ya = XH * 0.50; R = 190
    s.m(h, s.yb); s.l(h, s.yx)
    s.arc(h + R, ya, R, s.yx + OVER - ya, 180, 68, move=True); return W


@glyph("i", "ı")
def _i(s):
    W = 2 * s.h; s.m(s.h, s.yb); s.l(s.h, s.yx); return W


@glyph("i")
def _i_dot(s):
    W = 2 * s.h; s.m(s.h, s.yb); s.l(s.h, s.yx); s.dot(s.h, XH + 128); return W


@glyph("j")
def _j(s):
    h = s.h; r = 118; xs = 175; W = xs + h; cy = DESC + h + r
    s.m(xs, s.yx); s.l(xs, cy); s.arc(xs - r, cy, r, r, 0, -112); s.dot(xs, XH + 128); return W


@glyph("l")
def _l(s):
    h = s.h; r = 105; W = h + r + h
    s.m(h, s.ya); s.l(h, h + r); s.arc(h + r, h + r, r, r, 180, 270); return W


@glyph("t")
def _t(s):
    h = s.h; r = 108; xs = 128; W = 296
    s.m(xs, 690 - h); s.l(xs, h + r); s.arc(xs + r, h + r, r, r, 180, 270)
    s.m(h, s.yx); s.l(W - h, s.yx); return W


@glyph("f")
def _f(s):
    h = s.h; r = 112; xs = 128; W = 320
    s.m(xs, s.yb); s.l(xs, s.ya - r); s.arc(xs + r, s.ya - r, r, r, 180, 90); s.l(W - h, s.ya)
    s.m(h, s.yx); s.l(W - h - 20, s.yx); return W


@glyph("k")
def _k(s):
    W = 430; h = s.h
    s.m(h, s.ya); s.l(h, s.yb)
    ay = 0.33 * XH
    s.m(W - h, s.yx); s.l(h, ay)
    x = 0.46 * W; t = (x - h) / (W - 2 * h); y = ay + t * (s.yx - ay)
    s.m(x, y); s.l(W - h, s.yb); return W


@glyph("v")
def _v(s):
    W = 450; s.poly((s.h, s.yx), (W / 2, s.yb), (W - s.h, s.yx)); return W


@glyph("w")
def _w(s):
    W = 670; h = s.h
    s.poly((h, s.yx), (W * 0.25, s.yb), (W * 0.5, s.yx), (W * 0.75, s.yb), (W - h, s.yx)); return W


@glyph("x")
def _x(s):
    W = 440; h = s.h
    s.m(h, s.yx); s.l(W - h, s.yb); s.m(W - h, s.yx); s.l(h, s.yb); return W


@glyph("y")
def _y(s):
    W = 450; h = s.h
    s.m(W - h, s.yx); xd, yd = 0.16 * W + h, s.yd
    s.l(xd, yd)
    yc = 0.26 * XH; t = (yc - s.yx) / (yd - s.yx); x = W - h + t * (xd - (W - h))
    s.m(h, s.yx); s.l(x, yc); return W


@glyph("z")
def _z(s):
    W = 410; h = s.h; s.poly((h, s.yx), (W - h, s.yx), (h, s.yb), (W - h, s.yb)); return W


@glyph("s")
def _s(s):
    W = 400; h = s.h; top, bot = s.yx + OVER, s.yb - OVER
    mid = bot + 0.47 * (top - bot)
    rx = W / 2 - h; cx = W / 2
    cu, ru = (top + mid) / 2, (top - mid) / 2
    cl, rl = (bot + mid) / 2, (mid - bot) / 2
    s.arc(cx, cu, rx * 0.94, ru, 24, 270, move=True)
    s.arc(cx, cl, rx, rl, 90, -156); return W


# --- capitals ---
@glyph("A")
def _A(s):
    W = 640; h = s.h; yb, yc = s.yb, s.yc
    s.poly((h, yb), (W / 2, yc), (W - h, yb))
    y = yb + 0.30 * (yc - yb); x = h + (W / 2 - h) * (y - yb) / (yc - yb)
    s.m(x, y); s.l(W - x, y); return W


def bowl_cap(s, x0, top, bot, right, move_to=True):
    """A bowl for B, D, P, R: from the stem at x0 along top, around the right side, back along bot."""
    ry = (top - bot) / 2; cx = right - ry; cy = (top + bot) / 2
    s.m(x0, top); s.l(cx, top); s.arc(cx, cy, ry, ry, 90, -90); s.l(x0, bot)


@glyph("B")
def _B(s):
    W = 520; h = s.h; ym = CAP * 0.54
    s.m(h, s.yb); s.l(h, s.yc)
    bowl_cap(s, h, s.yc, ym, W - h - 14); bowl_cap(s, h, ym, s.yb, W - h); return W


@glyph("P")
def _P(s):
    W = 500; h = s.h
    s.m(h, s.yb); s.l(h, s.yc); bowl_cap(s, h, s.yc, CAP * 0.40, W - h); return W


@glyph("R")
def _R(s):
    W = 520; h = s.h; ym = CAP * 0.40
    s.m(h, s.yb); s.l(h, s.yc); bowl_cap(s, h, s.yc, ym, W - h - 10)
    s.m(W * 0.44, ym); s.l(W - h, s.yb); return W


@glyph("D")
def _D(s):
    W = 580; h = s.h; ry = (s.yc - s.yb) / 2; cx = W - h - ry
    s.m(h, s.yb); s.l(h, s.yc); s.l(cx, s.yc); s.arc(cx, CAP / 2, ry * 0.95, ry, 90, -90); s.l(h, s.yb); return W


@glyph("E")
def _E(s):
    W = 450; h = s.h
    s.poly((W - h, s.yc), (h, s.yc), (h, s.yb), (W - h, s.yb)); s.m(h, CAP / 2); s.l(W - h - 36, CAP / 2); return W


@glyph("F")
def _F(s):
    W = 430; h = s.h
    s.poly((W - h, s.yc), (h, s.yc), (h, s.yb)); s.m(h, CAP / 2); s.l(W - h - 36, CAP / 2); return W


@glyph("G")
def _G(s):
    W = 610; h = s.h; rx = W / 2 - h; ry = CAP / 2 + OVER - h
    s.arc(W / 2, CAP / 2, rx, ry, 38, 360, move=True); s.l(W * 0.52, CAP / 2); return W


@glyph("H")
def _H(s):
    W = 570; h = s.h
    s.m(h, s.yb); s.l(h, s.yc); s.m(W - h, s.yb); s.l(W - h, s.yc); s.m(h, CAP / 2); s.l(W - h, CAP / 2); return W


@glyph("I")
def _I(s):
    W = 2 * s.h; s.m(s.h, s.yb); s.l(s.h, s.yc); return W


@glyph("J")
def _J(s):
    W = 380; h = s.h; r = W / 2 - h; cy = h - OVER + r
    s.m(W - h, s.yc); s.l(W - h, cy); s.arc(W / 2, cy, r, r, 0, -180); return W


@glyph("K")
def _K(s):
    W = 540; h = s.h
    s.m(h, s.yc); s.l(h, s.yb)
    s.m(W - h, s.yc); s.l(h, CAP * 0.36)
    x = 0.42 * W; t = (x - h) / (W - 2 * h); y = CAP * 0.36 + t * (s.yc - CAP * 0.36)
    s.m(x, y); s.l(W - h, s.yb); return W


@glyph("L")
def _L(s):
    W = 420; s.poly((s.h, s.yc), (s.h, s.yb), (W - s.h, s.yb)); return W


@glyph("M")
def _M(s):
    W = 740; h = s.h
    s.poly((h, s.yb), (h, s.yc), (W / 2, CAP * 0.24), (W - h, s.yc), (W - h, s.yb)); return W


@glyph("N")
def _N(s):
    W = 590; h = s.h; s.poly((h, s.yb), (h, s.yc), (W - h, s.yb), (W - h, s.yc)); return W


@glyph("O")
def _O(s):
    W = 660; s.ell(W / 2, CAP / 2, W / 2 - s.h, CAP / 2 + OVER - s.h); return W


@glyph("Q")
def _Q(s):
    W = 660; h = s.h
    s.ell(W / 2, CAP / 2, W / 2 - h, CAP / 2 + OVER - h); s.m(W * 0.58, CAP * 0.24); s.l(W * 0.84, -26 + h); return W


@glyph("C")
def _C(s):
    W = 590; h = s.h; s.arc(W / 2 + 6, CAP / 2, (W + 12) / 2 - h, CAP / 2 + OVER - h, 40, 320, move=True); return W


@glyph("S")
def _S(s):
    W = 520; h = s.h; top, bot = s.yc + OVER, s.yb - OVER
    mid = bot + 0.47 * (top - bot); rx = W / 2 - h; cx = W / 2
    cu, ru = (top + mid) / 2, (top - mid) / 2
    cl, rl = (bot + mid) / 2, (mid - bot) / 2
    s.arc(cx, cu, rx * 0.94, ru, 24, 270, move=True); s.arc(cx, cl, rx, rl, 90, -156); return W


@glyph("T")
def _T(s):
    W = 520; s.m(s.h, s.yc); s.l(W - s.h, s.yc); s.m(W / 2, s.yc); s.l(W / 2, s.yb); return W


@glyph("U")
def _U(s):
    W = 580; h = s.h; r = W / 2 - h; cy = h - OVER + r
    s.m(h, s.yc); s.l(h, cy); s.arc(W / 2, cy, r, r, 180, 360); s.l(W - h, s.yc); return W


@glyph("V")
def _V(s):
    W = 630; s.poly((s.h, s.yc), (W / 2, s.yb), (W - s.h, s.yc)); return W


@glyph("W")
def _W(s):
    W = 920; h = s.h
    s.poly((h, s.yc), (W * 0.23, s.yb), (W * 0.5, s.yc * 0.86), (W * 0.77, s.yb), (W - h, s.yc)); return W


@glyph("X")
def _X(s):
    W = 580; h = s.h; s.m(h, s.yc); s.l(W - h, s.yb); s.m(W - h, s.yc); s.l(h, s.yb); return W


@glyph("Y")
def _Y(s):
    W = 600; h = s.h; ym = CAP * 0.46
    s.m(h, s.yc); s.l(W / 2, ym); s.m(W - h, s.yc); s.l(W / 2, ym); s.m(W / 2, ym); s.l(W / 2, s.yb); return W


@glyph("Z")
def _Z(s):
    W = 520; s.poly((s.h, s.yc), (W - s.h, s.yc), (s.h, s.yb), (W - s.h, s.yb)); return W


# --- figures (every one has the same advance, so columns line up) ---
@glyph("0")
def _0(s):
    W = 470; s.ell(W / 2, CAP / 2, W / 2 - s.h, CAP / 2 + OVER - s.h); return W


@glyph("1")
def _1(s):
    W = 300; h = s.h; xs = 0.64 * W
    s.poly((h, s.yc - 120), (xs, s.yc), (xs, s.yb)); return W


def stacked(s, W, top, bot, frac=0.47):
    mid = bot + frac * (top - bot); rx = W / 2 - s.h
    return (W / 2, (top + mid) / 2, rx * 0.92, (top - mid) / 2, (bot + mid) / 2, rx, (mid - bot) / 2, mid)


@glyph("2")
def _2(s):
    W = 470; h = s.h; r = W / 2 - h
    s.arc(W / 2, s.yc - r, r, r, 165, -38, move=True); s.l(h, s.yb); s.l(W - h, s.yb); return W


@glyph("3")
def _3(s):
    W = 470; h = s.h; cx, cu, rxu, ru, cl, rxl, rl, mid = stacked(s, W, s.yc + OVER, s.yb - OVER, 0.49)
    s.arc(cx, cu, rxu, ru, 152, -90, move=True); s.arc(cx, cl, rxl, rl, 90, -152); return W


@glyph("4")
def _4(s):
    W = 490; h = s.h; xs = 0.70 * W
    s.poly((xs, s.yb), (xs, s.yc), (h, CAP * 0.30), (W - h, CAP * 0.30)); return W


@glyph("5")
def _5(s):
    W = 470; h = s.h; rx = W / 2 - h; top, bot = CAP * 0.66, s.yb - OVER
    cl, rl = (top + bot) / 2, (top - bot) / 2
    x0, y0 = W / 2 + rx * math.cos(math.radians(140)), cl + rl * math.sin(math.radians(140))
    s.poly((W - h, s.yc), (h + 14, s.yc), (h + 6, y0 + 10), (x0, y0)); s.arc(W / 2, cl, rx, rl, 140, -152); return W


@glyph("6")
def _6(s):
    W = 470; h = s.h; r = W / 2 - h; cy = h - OVER + r
    s.ell(W / 2, cy, r, r); s.m(h, cy); s.c(h, CAP * 0.78, W * 0.30, s.yc, W * 0.84, s.yc - 6); return W


@glyph("9")
def _9(s):
    W = 470; s.T = lambda x, y: (W - x, CAP - y); _6(s); s.T = None; return W


@glyph("7")
def _7(s):
    W = 450; s.poly((s.h, s.yc), (W - s.h, s.yc), (W * 0.30, s.yb)); return W


@glyph("8")
def _8(s):
    W = 470; cx, cu, rxu, ru, cl, rxl, rl, mid = stacked(s, W, s.yc + OVER, s.yb - OVER, 0.48)
    s.ell(cx, cu, rxu, ru); s.ell(cx, cl, rxl, rl); return W


# --- punctuation and symbols ---
@glyph(".")
def _period(s):
    r = s.h * 1.12; s.dot(r, r); return 2 * r


@glyph(",")
def _comma(s):
    r = s.h * 1.12; s.dot(r, r); s.m(r + 4, r - 2); s.l(r - 26, -90 + s.h); return 2 * r + 6


@glyph(":")
def _colon(s):
    r = s.h * 1.12; s.dot(r, r); s.dot(r, XH - r); return 2 * r


@glyph(";")
def _semi(s):
    r = s.h * 1.12; s.dot(r, XH - r); s.dot(r, r); s.m(r + 4, r - 2); s.l(r - 26, -90 + s.h); return 2 * r + 6


@glyph("!")
def _excl(s):
    r = s.h * 1.12; s.m(r, s.yc); s.l(r, 230); s.dot(r, r); return 2 * r


@glyph("?")
def _q_(s):
    W = 400; h = s.h; r = W / 2 - h; cy = s.yc - r
    s.arc(W / 2, cy, r, r, 172, -62, move=True); s.l(W / 2, 225); s.dot(W / 2, s.h * 1.12); return W


@glyph('"')
def _dq(s):
    h = s.h; s.m(h, s.yc); s.l(h, CAP - 190); s.m(h + 150, s.yc); s.l(h + 150, CAP - 190); return 150 + 2 * h


@glyph("'")
def _sq(s):
    h = s.h; s.m(h, s.yc); s.l(h, CAP - 190); return 2 * h


@glyph("-")
def _hy(s):
    W = 290; s.m(s.h, 255); s.l(W - s.h, 255); return W


@glyph("\u2013")
def _en(s):
    W = 470; s.m(s.h, 255); s.l(W - s.h, 255); return W


@glyph("\u2014")
def _em(s):
    W = 860; s.m(s.h, 255); s.l(W - s.h, 255); return W


@glyph("\u2212", "\u2012")
def _minus(s):
    W = 440; s.m(s.h, 290); s.l(W - s.h, 290); return W


@glyph("_")
def _us(s):
    W = 520; s.m(s.h, -70); s.l(W - s.h, -70); return W


@glyph("/")
def _sl(s):
    W = 330; s.m(s.h, s.yb - 40); s.l(W - s.h, s.yc + 20); return W


@glyph("\\")
def _bs(s):
    W = 330; s.m(s.h, s.yc + 20); s.l(W - s.h, s.yb - 40); return W


@glyph("|")
def _pipe(s):
    s.m(s.h, s.ya); s.l(s.h, s.yd); return 2 * s.h


@glyph("(")
def _lp(s):
    W = 250; h = s.h; s.m(W - h, s.ya); s.c(h - 40, 600, h - 40, -40, W - h, s.yd); return W


@glyph(")")
def _rp(s):
    W = 250; h = s.h; s.m(h, s.ya); s.c(W - h + 40, 600, W - h + 40, -40, h, s.yd); return W


@glyph("[")
def _lb(s):
    W = 260; h = s.h; s.poly((W - h, s.ya), (h, s.ya), (h, s.yd), (W - h, s.yd)); return W


@glyph("]")
def _rb(s):
    W = 260; h = s.h; s.poly((h, s.ya), (W - h, s.ya), (W - h, s.yd), (h, s.yd)); return W


@glyph("{")
def _lc(s):
    W = 290; h = s.h; r = 66; mx = W / 2 - 24
    s.m(W - h, s.ya); s.l(mx + r, s.ya); s.arc(mx + r, s.ya - r, r, r, 90, 180); s.l(mx, 300 + r)
    s.arc(mx - r, 300 + r, r, r, 0, -90); s.l(h, 300)
    s.m(h, 300); s.arc(mx - r, 300 - r, r, r, 90, 0); s.l(mx, s.yd + r); s.arc(mx + r, s.yd + r, r, r, 180, 270); s.l(W - h, s.yd); return W


@glyph("}")
def _rc(s):
    W = 290; h = s.h; r = 66; mx = W / 2 + 24
    s.m(h, s.ya); s.l(mx - r, s.ya); s.arc(mx - r, s.ya - r, r, r, 90, 0); s.l(mx, 300 + r)
    s.arc(mx + r, 300 + r, r, r, 180, 270); s.l(W - h, 300)
    s.m(W - h, 300); s.arc(mx + r, 300 - r, r, r, 90, 180); s.l(mx, s.yd + r); s.arc(mx - r, s.yd + r, r, r, 0, -90); s.l(h, s.yd); return W


@glyph("<")
def _lt(s):
    W = 440; s.poly((W - s.h, 470), (s.h, 280), (W - s.h, 90)); return W


@glyph(">")
def _gt(s):
    W = 440; s.poly((s.h, 470), (W - s.h, 280), (s.h, 90)); return W


@glyph("=")
def _eq(s):
    W = 440; s.m(s.h, 380); s.l(W - s.h, 380); s.m(s.h, 200); s.l(W - s.h, 200); return W


@glyph("+")
def _plus(s):
    W = 440; s.m(s.h, 290); s.l(W - s.h, 290); s.m(W / 2, 290 + (W / 2 - s.h)); s.l(W / 2, 290 - (W / 2 - s.h)); return W


@glyph("\u00d7")
def _times(s):
    W = 400; h = s.h; s.m(h, 470); s.l(W - h, 110); s.m(W - h, 470); s.l(h, 110); return W


@glyph("\u00f7")
def _div(s):
    W = 440; s.m(s.h, 290); s.l(W - s.h, 290); s.dot(W / 2, 470); s.dot(W / 2, 110); return W


@glyph("*")
def _star(s):
    W = 340; h = s.h; cx, cy, r = W / 2, CAP - 150, W / 2 - h
    for a in (90, 18, -54, -126, 162):
        s.m(cx, cy); s.l(cx + r * math.cos(math.radians(a)), cy + r * math.sin(math.radians(a)))
    return W


@glyph("#")
def _hash(s):
    W = 560; h = s.h
    s.m(0.30 * W, s.yc); s.l(0.18 * W, 40); s.m(0.80 * W, s.yc); s.l(0.68 * W, 40)
    s.m(h, 470); s.l(W - h, 470); s.m(h, 230); s.l(W - h, 230); return W


@glyph("%")
def _pct(s):
    W = 700; h = s.h; r = 128
    s.ell(r + h * 0.4, s.yc - r + h * 0.4, r - h * 0.4, r - h * 0.4); s.ell(W - r - h * 0.4, r + h * 0.6, r - h * 0.4, r - h * 0.4)
    s.m(W - h - 20, s.yc + 10); s.l(h + 20, s.yb - 10); return W


@glyph("&")
def _amp(s):
    W = 620; h = s.h; C_ = CAP
    cx1, cy1, rx1, ry1 = 0.34 * W, 0.775 * C_, 0.155 * W, 0.17 * C_      # upper loop
    cx2, cy2, rx2, ry2 = 0.37 * W, 0.235 * C_, 0.255 * W, 0.235 * C_ - 4  # lower bowl
    a_b = math.radians(236)
    bx, by = cx1 + rx1 * math.cos(a_b), cy1 + ry1 * math.sin(a_b)
    s.m(W - h - 6, s.yb); s.l(bx, by)
    s.arc(cx1, cy1, rx1, ry1, 236, -48)
    ex, ey = cx1 + rx1 * math.cos(math.radians(-48)), cy1 + ry1 * math.sin(math.radians(-48))
    dx, dy = cx2 + rx2 * math.cos(math.radians(172)), cy2 + ry2 * math.sin(math.radians(172))
    s.l(dx, dy)
    s.arc(cx2, cy2, rx2, ry2, 172, 352)
    s.l(W - h - 14, 0.43 * C_); return W


@glyph("@")
def _at(s):
    W = 780; h = s.h; cx, cy = W / 2, 262
    s.arc(cx, cy, W / 2 - h, 322 - h, 22, 338, move=True)             # outer ring, open at the right
    ir = 104; ix = cx - 22
    s.ell(ix, cy, ir, ir + 6)                                          # the 'a'
    sx = ix + ir
    s.m(sx, cy + 78); s.l(sx, cy - 52); s.c(sx, cy - 126, sx + 112, cy - 122, sx + 150, cy - 12)   # stem curling to the ring
    return W


@glyph("$")
def _dollar(s):
    _S2(s); return 520


def _S2(s):
    W = 520; h = s.h; top, bot = s.yc - 30, s.yb + 30
    mid = bot + 0.47 * (top - bot); rx = W / 2 - h; cx = W / 2
    cu, ru = (top + mid) / 2, (top - mid) / 2
    cl, rl = (bot + mid) / 2, (mid - bot) / 2
    s.arc(cx, cu, rx * 0.94, ru, 24, 270, move=True); s.arc(cx, cl, rx, rl, 90, -156)
    s.m(cx, s.yc + 60); s.l(cx, s.yb - 60)


@glyph("~")
def _tilde(s):
    W = 440; s.m(s.h, 250); s.c(70, 360, 160, 360, W / 2, 270); s.c(W / 2 + 60, 190, W - 70, 190, W - s.h, 300); return W


@glyph("^")
def _caret(s):
    W = 420; s.poly((s.h, 440), (W / 2, s.yc), (W - s.h, 440)); return W


@glyph("`")
def _grave(s):
    W = 240; s.m(s.h, s.yc); s.l(W - s.h, s.yc - 110); return W


def quote_mark(s, cx, closing):
    """One curly-quote comma: a round dot with a short tail. Closing marks (’ ”) hang the tail down-left, opening marks
    (‘ “) lift it up-right. The top of the mark is at cap height."""
    h = s.h; r = h * 1.2; top = CAP - 6
    if closing:
        dy = top - r; s.dot(cx, dy); s.m(cx + 2, dy - 4); s.c(cx - 4, dy - 44, cx - 16, dy - 78, cx - 34, dy - 108)
    else:
        ty = top - h
        dy = ty - 108; s.dot(cx, dy); s.m(cx - 2, dy + 4); s.c(cx + 4, dy + 44, cx + 16, dy + 78, cx + 34, ty)


@glyph("\u2018")
def _lsq(s):
    r = s.h * 1.2; cx = r + 6; quote_mark(s, cx, False); return 2 * r + 46


@glyph("\u2019")
def _rsq(s):
    r = s.h * 1.2; cx = r + 40; quote_mark(s, cx, True); return 2 * r + 46


@glyph("\u201c")
def _ldq(s):
    r = s.h * 1.2; g = 2 * r + 40
    for dx in (0, g):
        quote_mark(s, r + 6 + dx, False)
    return g + 2 * r + 46


@glyph("\u201d")
def _rdq(s):
    r = s.h * 1.2; g = 2 * r + 40
    for dx in (0, g):
        quote_mark(s, r + 40 + dx, True)
    return g + 2 * r + 46


@glyph("\u2026")
def _ell(s):
    r = s.h * 1.12; g = 2 * r + 70
    for i in range(3):
        s.dot(r + i * g, r)
    return 2 * g + 2 * r


@glyph("\u00b7", "\u2022")
def _mid(s):
    r = s.h * 1.2; s.dot(r, 280); return 2 * r


@glyph("\u00b0")
def _deg(s):
    r = 62; s.ring(r + 6, s.yc - r + 6, r + s.h * 0.5, r - s.h * 0.5 if r - s.h * 0.5 > 8 else 8); return 2 * r + 12


@glyph("\u20ac")
def _euro(s):
    W = 560; h = s.h
    s.arc(W / 2 + 18, CAP / 2, W / 2 - h - 2, CAP / 2 + OVER - h, 40, 320, move=True)
    s.m(h, 0.60 * CAP); s.l(W - 90, 0.60 * CAP); s.m(h, 0.40 * CAP); s.l(W - 90, 0.40 * CAP); return W


@glyph("\u00a3")
def _pound(s):
    W = 480; h = s.h; r = 130
    s.arc(h + r + 70, s.yc - r, r, r, 0, 180, move=True); s.l(h + 70, 130); s.c(h + 70, 60, 20 + h, 40, h, s.yb)
    s.l(W - h, s.yb); s.m(h, 340); s.l(W - 90, 340); return W


@glyph("\u00a5")
def _yen(s):
    W = 600; h = s.h; ym = CAP * 0.46
    s.m(h, s.yc); s.l(W / 2, ym); s.m(W - h, s.yc); s.l(W / 2, ym); s.m(W / 2, ym); s.l(W / 2, s.yb)
    s.m(W * 0.2, 0.36 * CAP); s.l(W * 0.8, 0.36 * CAP); s.m(W * 0.2, 0.20 * CAP); s.l(W * 0.8, 0.20 * CAP); return W


@glyph("\u2192")
def _ar(s):
    W = 700; s.m(s.h, 280); s.l(W - s.h, 280); s.poly((W - 190, 470), (W - s.h, 280), (W - 190, 90)); return W


@glyph("\u2190")
def _al(s):
    W = 700; s.m(s.h, 280); s.l(W - s.h, 280); s.poly((190, 470), (s.h, 280), (190, 90)); return W


@glyph("\u2191")
def _au(s):
    W = 400; s.m(W / 2, s.yd + 60); s.l(W / 2, s.yc); s.poly((W / 2 - 150, s.yc - 150), (W / 2, s.yc), (W / 2 + 150, s.yc - 150)); return W


@glyph("\u2193")
def _ad(s):
    W = 400; s.m(W / 2, s.yc); s.l(W / 2, s.yd + 60); s.poly((W / 2 - 150, s.yd + 210), (W / 2, s.yd + 60), (W / 2 + 150, s.yd + 210)); return W


@glyph("\u2713")
def _check(s):
    W = 560; s.poly((s.h, 250), (W * 0.38, s.yb + 30), (W - s.h, s.yc - 60)); return W


@glyph("\u2248")
def _approx(s):
    W = 440
    for y in (350, 190):
        s.m(s.h, y); s.c(W * 0.20, y + 100, W * 0.38, y + 100, W / 2, y); s.c(W * 0.62, y - 100, W * 0.8, y - 100, W - s.h, y)
    return W


@glyph("\u22ef")
def _mdots(s):
    r = s.h * 1.12; g = 2 * r + 70
    for i in range(3):
        s.dot(r + i * g, 280)
    return 2 * g + 2 * r


@glyph("\u00a1")
def _iexcl(s):
    r = s.h * 1.12; s.dot(r, XH - r + 0); s.m(r, 330); s.l(r, s.yd + 20); return 2 * r


@glyph("\u00bf")
def _iques(s):
    W = 400; h = s.h; r = W / 2 - h; cy = h + r
    s.T = lambda x, y: (W - x, CAP - y); _q_(s); s.T = None; return W




# --- more symbols ---
@glyph("\u2039")
def _lsa(s):
    W = 300; h = s.h; s.poly((W - h - 20, 470), (h + 20, 280), (W - h - 20, 90)); return W


@glyph("\u203a")
def _rsa(s):
    W = 300; h = s.h; s.poly((h + 20, 470), (W - h - 20, 280), (h + 20, 90)); return W


@glyph("\u00ab")
def _ldaq(s):
    W = 500; h = s.h
    for dx in (0, 190):
        s.poly((W - h - 20 - 190 + dx, 470), (h + 20 + dx, 280), (W - h - 20 - 190 + dx, 90))
    return W - 0


@glyph("\u00bb")
def _rdaq(s):
    W = 500; h = s.h
    for dx in (0, 190):
        s.poly((h + 20 + dx, 470), (W - h - 20 - 190 + dx, 280), (h + 20 + dx, 90))
    return W


@glyph("\u201e")
def _lowdq(s):
    r = s.h * 1.2; g = 2 * r + 40
    for dx in (0, g):
        cx = r + 40 + dx; dy = -r + 40
        s.dot(cx, dy); s.m(cx + 2, dy - 4); s.c(cx - 4, dy - 44, cx - 16, dy - 78, cx - 34, dy - 108)
    return g + 2 * r + 46


@glyph("\u201a")
def _lowsq(s):
    r = s.h * 1.2; cx = r + 40; dy = -r + 40
    s.dot(cx, dy); s.m(cx + 2, dy - 4); s.c(cx - 4, dy - 44, cx - 16, dy - 78, cx - 34, dy - 108); return 2 * r + 46


def _solid_tri(s, pts):
    pen = s.fp
    pen.moveTo(s.pt(*pts[0]))
    for p_ in pts[1:]:
        pen.lineTo(s.pt(*p_))
    pen.closePath()


@glyph("\u25b2")
def _triup(s):
    W = 420; h = s.h; _solid_tri(s, [(h, 120), (W - h, 120), (W / 2, 120 + 330)]); s.poly((h, 120), (W - h, 120), (W / 2, 450), close=True); return W


@glyph("\u25bc")
def _tridown(s):
    W = 420; h = s.h; _solid_tri(s, [(h, 450), (W / 2, 120), (W - h, 450)]); s.poly((h, 450), (W - h, 450), (W / 2, 120), close=True); return W


@glyph("\u21b5")
def _enter(s):
    W = 560; h = s.h; r = 110
    s.m(W - h, s.yx + 60); s.l(W - h, 190 + r - 0); s.arc(W - h - r, 190 + r - 0, r, r, 0, -90); s.l(h + 150, 190)
    s.poly((h + 150 + 70, 190 + 80), (h + 150, 190), (h + 150 + 70, 190 - 80)); return W


# ---------------------------------------------------------------------------------------------------------------
# Accents (drawn centred at cx, cy) and composition of accented letters
# ---------------------------------------------------------------------------------------------------------------
def acc_acute(s, cx, cy): s.m(cx - 38, cy - 40); s.l(cx + 30, cy + 40)
def acc_grave(s, cx, cy): s.m(cx + 38, cy - 40); s.l(cx - 30, cy + 40)
def acc_circ(s, cx, cy): s.poly((cx - 64, cy - 32), (cx, cy + 38), (cx + 64, cy - 32))
def acc_caron(s, cx, cy): s.poly((cx - 64, cy + 32), (cx, cy - 38), (cx + 64, cy + 32))
def acc_diae(s, cx, cy): s.dot(cx - 62, cy); s.dot(cx + 62, cy)
def acc_dot(s, cx, cy): s.dot(cx, cy)
def acc_macron(s, cx, cy): s.m(cx - 56, cy); s.l(cx + 56, cy)
def acc_breve(s, cx, cy): s.m(cx - 62, cy + 30); s.c(cx - 58, cy - 38, cx + 58, cy - 38, cx + 62, cy + 30)
def acc_tilde(s, cx, cy): s.m(cx - 72, cy - 6); s.c(cx - 60, cy + 46, cx - 20, cy + 46, cx, cy + 8); s.c(cx + 20, cy - 30, cx + 60, cy - 30, cx + 72, cy + 24)
def acc_ring(s, cx, cy): r = 52; s.ring(cx, cy, r + 0.2 * s.h, max(10, r - 0.62 * s.h))
def acc_commabelow(s, cx, cy): s.m(cx + 4, -22); s.l(cx - 22, -118)
def acc_cedilla(s, cx, cy): s.m(cx, -4); s.c(cx + 44, -20, cx + 62, -80, cx + 6, -120)


ACCENTS = {"acute": acc_acute, "grave": acc_grave, "circ": acc_circ, "caron": acc_caron, "diae": acc_diae, "dot": acc_dot,
           "macron": acc_macron, "breve": acc_breve, "tilde": acc_tilde, "ring": acc_ring, "comma": acc_commabelow, "cedilla": acc_cedilla}
COMPOSE = {}


def _compose(chars, base, acc):
    for ch, b in zip(chars, base):
        COMPOSE[ch] = (b, acc)


_compose("àèìòù", "aeıou", "grave"); _compose("áéíóúý", "aeıouy", "acute"); _compose("âêîôû", "aeıou", "circ")
_compose("ãñõ", "ano", "tilde"); _compose("äëïöüÿ", "aeıouy", "diae"); _compose("å", "a", "ring"); _compose("ç", "c", "cedilla")
_compose("ăĂ", "aA", "breve"); _compose("ȘȚ", "ST", "comma"); _compose("șț", "st", "comma"); _compose("ÂÎ", "AI", "circ")
_compose("ÀÈÌÒÙ", "AEIOU", "grave"); _compose("ÁÉÍÓÚÝ", "AEIOUY", "acute"); _compose("ÂÊÔÛ", "AEOU", "circ")
_compose("ÃÑÕ", "ANO", "tilde"); _compose("ÄËÏÖÜ", "AEIOU", "diae"); _compose("Å", "A", "ring"); _compose("Ç", "C", "cedilla")
_compose("āēīōū", "aeıou", "macron")
_compose("ćńśź", "cnsz", "acute")
_compose("ŝĉ", "sc", "circ"); _compose("čšžřěň", "cszren", "caron"); _compose("ČŠŽ", "CSZ", "caron"); _compose("ě", "e", "caron")



# ---------------------------------------------------------------------------------------------------------------
# Greek and Cyrillic. Letters that look the same as a Latin letter reuse our Latin drawing; the rest are drawn here.
# ---------------------------------------------------------------------------------------------------------------
def small(fn, fx=0.86):
    """Draw a capital shape at x-height (for Cyrillic lower case that mirrors the capital)."""
    def g(s):
        h = s.h; W = fn(Shape(h)); Wn = 2 * h + (W - 2 * h) * fx
        k = (XH - 2 * h) / (CAP - 2 * h)
        s.T = lambda x, y: (h + (x - h) * fx, h + (y - h) * k)
        fn(s); s.T = None
        return Wn
    return g


def mirror(fn):
    def g(s):
        W = fn(Shape(s.h)); s.T = lambda x, y: (W - x, y); fn(s); s.T = None
        return W
    return g


def put(ch, fn):
    G[ch] = fn


# --- Greek capitals ---
@glyph("\u0393")
def _Gamma(s):
    W = 440; h = s.h; s.poly((h, s.yb), (h, s.yc), (W - h, s.yc)); return W


@glyph("\u0394")
def _Delta(s):
    W = 650; h = s.h; s.poly((h + 6, s.yb), (W / 2, s.yc), (W - h - 6, s.yb), close=True); return W


@glyph("\u0398")
def _Theta(s):
    W = 660; h = s.h; s.ell(W / 2, CAP / 2, W / 2 - h, CAP / 2 + OVER - h); s.m(W * 0.30, CAP / 2); s.l(W * 0.70, CAP / 2); return W


@glyph("\u039b")
def _Lambda(s):
    W = 650; h = s.h; s.poly((h, s.yb), (W / 2, s.yc), (W - h, s.yb)); return W


@glyph("\u039e")
def _Xi(s):
    W = 520; h = s.h; s.m(h, s.yc); s.l(W - h, s.yc); s.m(W * 0.2, CAP / 2); s.l(W * 0.8, CAP / 2); s.m(h, s.yb); s.l(W - h, s.yb); return W


@glyph("\u03a0")
def _Pi(s):
    W = 580; h = s.h; s.poly((h, s.yb), (h, s.yc), (W - h, s.yc), (W - h, s.yb)); return W


@glyph("\u03a3")
def _Sigma(s):
    W = 500; h = s.h; s.poly((W - h, s.yc), (h, s.yc), (W * 0.58, CAP / 2), (h, s.yb), (W - h, s.yb)); return W


@glyph("\u03a6")
def _Phi(s):
    W = 700; h = s.h; s.m(W / 2, s.yb); s.l(W / 2, s.yc); s.ell(W / 2, CAP / 2, W * 0.36, CAP * 0.34); return W


@glyph("\u03a8")
def _Psi(s):
    W = 680; h = s.h; s.m(W / 2, s.yb); s.l(W / 2, s.yc)
    s.m(h, s.yc); s.l(h, CAP * 0.48); s.arc(W / 2, CAP * 0.48, W / 2 - h, CAP * 0.32, 180, 360); s.l(W - h, s.yc); return W


@glyph("\u03a9")
def _Omega(s):
    W = 680; h = s.h; cx, cy = W / 2, CAP * 0.56; rx, ry = W / 2 - h - 18, CAP * 0.44 - h + 4
    x0 = cx + rx * math.cos(math.radians(236))
    s.m(h, s.yb); s.l(x0 - 4, s.yb); s.arc(cx, cy, rx, ry, 236, -56); s.l(W - x0 + 4, s.yb); s.l(W - h, s.yb); return W


for _g, _l in zip("ΑΒΕΖΗΙΚΜΝΟΡΤΥΧ", "ABEZHIKMNOPTYX"):
    G[_g] = G[_l]

# --- Greek lower case ---
@glyph("\u03b1")
def _alpha(s):
    return _a(s)


@glyph("\u03b2")
def _beta(s):
    W = 500; h = s.h; ym = ASC * 0.56
    s.m(h, s.yd); s.l(h, s.ya)
    bowl_cap(s, h, s.ya, ym, W - h - 16); bowl_cap(s, h, ym, s.yb, W - h); return W


@glyph("\u03b3")
def _gamma(s):
    W = 460; h = s.h; yy = 0.34 * XH
    s.m(h, s.yx); s.l(W / 2, yy); s.m(W - h, s.yx); s.l(W / 2, yy); s.m(W / 2, yy); s.l(W / 2, s.yd); return W


@glyph("\u03b4")
def _delta(s):
    W = 470; h = s.h
    s.ell(W / 2, XH / 2, W / 2 - h, XH / 2 + OVER - h)
    s.m(W * 0.40, s.yx + OVER); s.c(W * 0.52, s.yx + 60, W * 0.72, s.ya - 6, W - h - 30, s.ya); return W


@glyph("\u03b5")
def _eps(s):
    W = 390; h = s.h; top, bot = s.yx + OVER, s.yb - OVER; mid = bot + 0.5 * (top - bot)
    rx = W / 2 - h; cx = W / 2; cu, ru = (top + mid) / 2, (top - mid) / 2; cl, rl = (bot + mid) / 2, (mid - bot) / 2
    s.T = lambda x, y: (W - x, y)
    s.arc(cx, cu, rx * 0.9, ru, 152, -90, move=True); s.arc(cx, cl, rx, rl, 90, -152)
    s.T = None; return W


@glyph("\u03b6")
def _zeta(s):
    W = 400; h = s.h; r = 120
    s.m(W - h - 10, s.yx); s.l(h + r, s.yx); s.arc(h + r, s.yx - r, r, r, 90, 180)
    s.l(h, 0.40 * XH); s.arc(W / 2, 0.40 * XH, W / 2 - h, 0.40 * XH - h + 8, 180, 360)
    s.l(W - h, 0.08 * XH) if False else None
    s.m(h + 10, 0.40 * XH); s.c(h + 10, 0.05 * XH, W * 0.42, -20, W * 0.42, s.yd + 40); s.c(W * 0.42, s.yd, W * 0.62, s.yd, W * 0.7, s.yd + 50); return W


@glyph("\u03b7")
def _eta(s):
    W = 440; h = s.h; ya = XH * 0.50
    s.m(h, s.yb); s.l(h, s.yx); arch(s, h, W - h, s.yx + OVER, ya); s.l(W - h, s.yd); return W


@glyph("\u03b8")
def _theta(s):
    W = 440; h = s.h; s.ell(W / 2, CAP / 2, W / 2 - h, CAP / 2 + OVER - h); s.m(W * 0.26, CAP / 2); s.l(W * 0.74, CAP / 2); return W


@glyph("\u03b9")
def _iota(s):
    h = s.h; r = 90; W = h + r + h; s.m(h, s.yx); s.l(h, h + r); s.arc(h + r, h + r, r, r, 180, 270); return W


@glyph("\u03ba")
def _kappa(s):
    return small(_K, 0.78)(s)


@glyph("\u03bb")
def _lambda(s):
    W = 470; h = s.h
    s.m(h + 4, s.ya); s.l(W - h, s.yb)
    y = 0.46 * ASC; x = h + 4 + (W - h - h - 4) * (s.ya - y) / (s.ya - s.yb); s.m(x, y); s.l(h, s.yb); return W


@glyph("\u03bc")
def _mu(s):
    W = 440; h = s.h; yb_ = XH * 0.50
    s.m(h, s.yx); s.l(h, s.yd); s.m(h, 0.30 * XH); s.l(h, yb_); s.arc(W / 2, yb_, W / 2 - h, yb_ - (h - OVER), 180, 360)
    s.m(W - h, s.yx); s.l(W - h, s.yb); return W


@glyph("\u03bd")
def _nu(s):
    return _v(s)


@glyph("\u03be")
def _xi(s):
    W = 400; h = s.h; r = 100
    s.m(W - h - 10, s.yx); s.l(h + r, s.yx); s.arc(h + r, s.yx - r, r, r, 90, 180)
    s.l(h, 0.60 * XH); s.arc(W / 2, 0.58 * XH, W / 2 - h, 0.15 * XH, 180, 360) if False else None
    s.arc(W / 2, 0.58 * XH - 0, W / 2 - h, 0.2 * XH, 180, 270); s.m(W * 0.5, 0.38 * XH); s.l(W * 0.5, 0.38 * XH)
    s.m(h + 8, 0.40 * XH); s.c(h + 8, 0.02 * XH, W * 0.42, -20, W * 0.44, s.yd + 40); s.c(W * 0.44, s.yd, W * 0.62, s.yd, W * 0.7, s.yd + 50); return W


@glyph("\u03bf")
def _omicron(s):
    return _o(s)


@glyph("\u03c0")
def _pi(s):
    W = 500; h = s.h
    s.m(h, s.yx); s.l(W - h, s.yx); s.m(W * 0.27, s.yx); s.l(W * 0.27, s.yb); s.m(W * 0.73, s.yx); s.l(W * 0.73, s.yb); return W


@glyph("\u03c1")
def _rho(s):
    return _p(s)


@glyph("\u03c2")
def _sigma_final(s):
    W = 400; h = s.h; rx = W / 2 - h
    s.arc(W / 2 + 6, XH / 2, rx, bowl_ry(s), 50, 270, move=True)
    s.c(W / 2 + 60, s.yb - OVER, W - h - 6, 20, W - h - 6, -60); s.c(W - h - 6, s.yd + 6, W * 0.7, s.yd, W * 0.6, s.yd + 20); return W


@glyph("\u03c3")
def _sigma(s):
    W = 560; h = s.h; ew = 450
    s.ell(ew / 2, XH / 2, ew / 2 - h, bowl_ry(s)); s.m(ew / 2, s.yx + OVER - 1); s.l(W - h, s.yx + OVER - 1); return W


@glyph("\u03c4")
def _tau(s):
    W = 400; h = s.h; r = 80
    s.m(h, s.yx); s.l(W - h, s.yx); s.m(W / 2 - 18, s.yx); s.l(W / 2 - 18, h + r); s.arc(W / 2 - 18 + r, h + r, r, r, 180, 270); return W


@glyph("\u03c5")
def _upsilon(s):
    W = 440; h = s.h; yb_ = XH * 0.50
    s.m(h, s.yx); s.l(h, yb_); s.arc(W / 2, yb_, W / 2 - h, yb_ - (h - OVER), 180, 360); s.l(W - h, s.yx); return W


@glyph("\u03c6")
def _phi(s):
    W = 520; h = s.h; s.ell(W / 2, XH / 2, W / 2 - h, bowl_ry(s)); s.m(W / 2, s.ya); s.l(W / 2, s.yd); return W


@glyph("\u03c7")
def _chi(s):
    W = 440; h = s.h; s.m(h, s.yx); s.l(W - h, s.yd); s.m(W - h, s.yx); s.l(h, s.yd); return W


@glyph("\u03c8")
def _psi(s):
    W = 540; h = s.h; yb_ = XH * 0.46
    s.m(W / 2, s.ya); s.l(W / 2, s.yd)
    s.m(h, s.yx); s.l(h, yb_); s.arc(W / 2, yb_, W / 2 - h, yb_ - (h - OVER), 180, 360); s.l(W - h, s.yx); return W


@glyph("\u03c9")
def _omega(s):
    W = 640; h = s.h; r = W * 0.27 - h; cy = XH * 0.40
    s.m(h, s.yx); s.l(h, cy); s.arc(W * 0.27, cy, r, cy - (h - OVER), 180, 360)
    s.l(W * 0.73 - r, cy); s.arc(W * 0.73, cy, r, cy - (h - OVER), 180, 360); s.l(W - h, s.yx); return W


# --- Cyrillic capitals ---
G["\u0413"] = G["\u0393"]; G["\u041b"] = G["\u039b"]; G["\u041f"] = G["\u03a0"]; G["\u0424"] = G["\u03a6"]
for _c, _l in zip("АВЕКМНОРСТХ", "ABEKMHOPCTX"):
    G[_c] = G[_l]
G["\u0406"] = G["I"]; G["\u0407"] = G["I"]; G["\u0401"] = G["E"]


@glyph("\u0411")
def _Be(s):
    W = 520; h = s.h; ym = CAP * 0.56
    s.poly((W - h - 6, s.yc), (h, s.yc), (h, s.yb)); bowl_cap(s, h, ym, s.yb, W - h); return W


@glyph("\u0414")
def _De(s):
    W = 650; h = s.h
    s.m(0.27 * W, s.yc); s.l(W - 0.14 * W, s.yc); s.m(0.34 * W, s.yc); s.l(0.22 * W, s.yb); s.m(0.80 * W, s.yc); s.l(0.80 * W, s.yb)
    s.poly((h, s.yb + 64), (h, s.yb), (W - h, s.yb), (W - h, s.yb + 64)); return W


@glyph("\u0416")
def _Zhe(s):
    W = 780; h = s.h
    s.m(W / 2, s.yc); s.l(W / 2, s.yb)
    s.poly((h, s.yc), (W / 2, CAP / 2), (h, s.yb)); s.poly((W - h, s.yc), (W / 2, CAP / 2), (W - h, s.yb)); return W


@glyph("\u0417")
def _Ze(s):
    return _3(s)


@glyph("\u0418")
def _I_(s):
    W = 590; h = s.h; s.m(h, s.yb); s.l(h, s.yc); s.m(W - h, s.yb); s.l(W - h, s.yc); s.m(W - h, s.yc); s.l(h, s.yb); return W


@glyph("\u0419")
def _Ik(s):
    return _I_(s)


@glyph("\u0423")
def _U_(s):
    W = 560; h = s.h
    s.m(h, s.yc); s.l(W * 0.52, CAP * 0.30); s.m(W - h, s.yc); s.l(W * 0.20, s.yb - 6); return W


@glyph("\u0426")
def _Tse(s):
    W = 640; h = s.h; xr = W - 0.18 * W
    s.m(h, s.yc); s.l(h, s.yb); s.l(W - h, s.yb); s.m(xr, s.yc); s.l(xr, s.yb); s.m(W - h, s.yb); s.l(W - h, s.yb - 100); return W


@glyph("\u0427")
def _Che(s):
    W = 560; h = s.h
    s.m(h, s.yc); s.l(h, CAP * 0.62); s.c(h, CAP * 0.40, W * 0.5, CAP * 0.34, W - h, CAP * 0.46); s.m(W - h, s.yc); s.l(W - h, s.yb); return W


@glyph("\u0428")
def _Sha(s):
    W = 840; h = s.h; s.poly((h, s.yc), (h, s.yb), (W - h, s.yb), (W - h, s.yc)); s.m(W / 2, s.yc); s.l(W / 2, s.yb); return W


@glyph("\u0429")
def _Shcha(s):
    W = 900; h = s.h; xr = W - 0.10 * W
    s.poly((h, s.yc), (h, s.yb), (W - h, s.yb)); s.m(xr - 0.0, s.yc); s.l(xr, s.yb); s.m(W * 0.44, s.yc); s.l(W * 0.44, s.yb); s.m(W - h, s.yb); s.l(W - h, s.yb - 100); return W


@glyph("\u042c")
def _Soft(s):
    W = 520; h = s.h; s.m(h, s.yc); s.l(h, s.yb); bowl_cap(s, h, CAP * 0.55, s.yb, W - h); return W


@glyph("\u042a")
def _Hard(s):
    W = 600; h = s.h; xs = 0.26 * W
    s.m(h, s.yc); s.l(xs, s.yc); s.m(xs, s.yc); s.l(xs, s.yb); bowl_cap(s, xs, CAP * 0.55, s.yb, W - h); return W


@glyph("\u042b")
def _Yeru(s):
    W = 740; h = s.h; s.m(h, s.yc); s.l(h, s.yb); bowl_cap(s, h, CAP * 0.55, s.yb, W - 0.28 * W); s.m(W - h, s.yc); s.l(W - h, s.yb); return W


@glyph("\u042d")
def _E_rev(s):
    return mirror(_C)(s)


@glyph("\u042e")
def _Yu(s):
    W = 860; h = s.h; rx = 0.32 * W
    s.m(h, s.yc); s.l(h, s.yb); s.m(h, CAP / 2); s.l(0.30 * W, CAP / 2); s.ell(W - rx - h, CAP / 2, rx - 0, CAP / 2 + OVER - h); return W


@glyph("\u042f")
def _Ya(s):
    return mirror(_R)(s)


@glyph("\u0404")
def _Ye(s):
    W = 580; h = s.h
    s.arc(W / 2 + 6, CAP / 2, (W + 12) / 2 - h, CAP / 2 + OVER - h, 40, 320, move=True)
    return W


# --- Cyrillic lower case: shapes shared with Latin, or the capital drawn at x-height ---
for _c, _l in zip("аеорсху", "aeopcxy"):
    G[_c] = G[_l]
G["\u0456"] = G["i"]; G["\u0457"] = G["\u0131"]; G["\u0451"] = G["e"]
for _c, _fn in {
    "в": _B, "г": G["\u0393"], "з": _3, "и": G["\u0418"], "к": _K, "л": G["\u039b"], "м": _M, "н": _H, "п": G["\u03a0"], "т": _T,
    "ч": G["\u0427"], "ш": G["\u0428"], "ь": G["\u042c"], "ъ": G["\u042a"], "ы": G["\u042b"], "э": G["\u042d"], "ю": G["\u042e"],
    "я": G["\u042f"], "ж": G["\u0416"], "ц": G["\u0426"], "щ": G["\u0429"], "д": G["\u0414"], "є": G["\u0404"],
}.items():
    G[_c] = small(_fn, 0.84)


@glyph("\u0439")
def _ik(s):
    return small(G["\u0418"], 0.84)(s)


@glyph("\u0431")
def _be(s):
    W = 460; h = s.h
    s.ell(W / 2, XH / 2, W / 2 - h, bowl_ry(s)); s.m(h, XH / 2); s.l(h, s.ya - 70); s.c(h, s.ya, W * 0.5, s.ya, W - h - 20, s.ya - 24); return W


@glyph("\u0444")
def _ef(s):
    W = 560; h = s.h; s.ell(W / 2, XH / 2, W / 2 - h, bowl_ry(s)); s.m(W / 2, s.ya); s.l(W / 2, s.yd); return W



_compose("ΆΈΉΊΌΎΏ", "ΑΕΗΙΟΥΩ", "acute"); _compose("άέήίόύώ", "αεηιουω", "acute"); _compose("ϊϋ", "ιυ", "diae")
_compose("ЁёЇїЙй", "ЕеIıИи", "diae"); COMPOSE["Й"] = ("И", "breve"); COMPOSE["й"] = ("и", "breve")


def draw(char, s):
    """Draw `char` into Shape s; returns its outer width."""
    if char in COMPOSE:
        base, acc = COMPOSE[char]
        bs = base if base == "ı" else base
        W = G[bs](s)
        cap = base.isupper()
        cx = W / 2
        if acc in ("comma", "cedilla"):
            ACCENTS[acc](s, cx, 0)
        else:
            top = CAP if cap else XH
            ACCENTS[acc](s, cx, top + (92 if acc not in ("diae", "dot", "ring", "macron") else (96 if acc != "ring" else 112)))
        return W
    return G[char](s)


# ---------------------------------------------------------------------------------------------------------------
# Spacing: left and right side bearings (outer edge to the neighbour), by glyph kind
# ---------------------------------------------------------------------------------------------------------------
STEM_L = set("bhkmnpruijlBDEFHIKLMNPRUdq")   # a vertical stem on the left edge
STEM_R = set("dqaghmnuijlHIJMNUBDhm")        # a vertical stem on the right edge
ROUND = set("ocesCGOQS0369$")
DIAG = set("AVWXYvwxyTjkzZ7Z")


def bearings(ch, h):
    base = COMPOSE[ch][0] if ch in COMPOSE else ch
    base = "i" if base == "ı" else base
    if ch in ".,:;!?'\"" or ch in "\u201a\u201e\u2018\u2019\u201c\u201d\u2026\u00b7\u2022\u22ef":
        return 64, 64
    if ch in "()[]{}|":
        return 60, 60
    if ch in "-\u2013\u2014\u2212+=<>\u00d7\u00f7\u2192\u2190\u2191\u2193\u2248~^`\u00b0":
        return 56, 56
    L = 60
    R = 60
    if base in STEM_L: L = 74
    if base in STEM_R: R = 74
    if base in ROUND: L, R = 48, 48
    if base in "ABC".replace("B", "") or base in "AVWXYvwxy": L, R = 26, 26
    if base in "TFPLZz7": L, R = (28, 28) if base == "T" else (L, R)
    return L, R


def build_glyph(ch, h):
    probe = Shape(h)
    W = draw(ch, probe)
    L, R = bearings(ch, h)
    if ch in "0123456789":
        L = R = (TAB - W) / 2
    s = Shape(h, ox=L)
    draw(ch, s)
    return s.outline(), W, L, L + W + R


def kerning_pairs():
    """A few optical corrections, in units (negative = closer)."""
    pairs = {}
    caps_diag = "AVWXYTLP"
    def add(a, b, v):
        for x in a:
            for y in b:
                pairs[(x, y)] = v
    add("AV", "VWYTAvwy", -50); add("T", "oaecsuvwyzrAO", -70); add("V", "oaecsAO", -45); add("W", "oaecsA", -35)
    add("Y", "oaecsAO", -60); add("P", "A", -50); add("L", "VWYT", -60); add("F", "oaeAr", -40); add("rvwy", ".,", -50)
    add("AVWYTP", ".,", -60); add("LTVWY", "\u2019\u201d'", -40)
    return pairs


def to_ttglyph(path):
    pen = TTGlyphPen(None)
    path.draw(TransformPen(Cu2QuPen(pen, max_err=0.6, reverse_direction=True), (1, 0, 0, 1 / KY, 0, 0)))
    return pen.glyph()


def build(weight, out_dir, only=None):
    style, sw = WEIGHTS[weight]
    h = sw / 2
    chars = [c for c in list(G.keys()) + list(COMPOSE.keys()) if (not only or c in only)]
    chars = sorted(set(chars), key=ord)
    glyphs, metrics, cmap, order = {}, {}, {}, [".notdef", "space"]
    # .notdef: a plain box
    box = Shape(h)
    box.poly((90, 0 + h), (90, CAP - h), (430, CAP - h), (430, h), close=True)
    glyphs[".notdef"] = to_ttglyph(box.outline()); metrics[".notdef"] = (520, 90)
    sp = pathops.Path()
    glyphs["space"] = to_ttglyph(sp); metrics["space"] = (250, 0)
    cmap[0x20] = "space"; cmap[0xA0] = "space"
    names = {}
    for ch in chars:
        if ch == " ":
            continue
        path, W, L, adv = build_glyph(ch, h)
        name = f"uni{ord(ch):04X}"
        g = to_ttglyph(path)
        bounds = path.bounds if len(list(path.contours)) else (0, 0, 0, 0)
        glyphs[name] = g; metrics[name] = (int(round(adv)), int(round(bounds[0])))
        cmap[ord(ch)] = name; names[ch] = name; order.append(name)
    fb = FontBuilder(UPM, isTTF=True)
    fb.setupGlyphOrder(order)
    fb.setupCharacterMap(cmap)
    fb.setupGlyf(glyphs)
    fb.setupHorizontalMetrics(metrics)
    fb.setupHorizontalHeader(ascent=960, descent=-240, lineGap=0)
    fam = "Plume"
    reg = style == "Regular"
    fb.setupNameTable({
        "copyright": "Copyright 2026 The Plume Fonts Authors (https://github.com/yash-ceo-ai/plume-fonts)",
        "familyName": fam if reg else f"{fam} {style}",
        "styleName": "Regular",
        "uniqueFontIdentifier": f"{VERSION};PLUME;Plume-{style}",
        "fullName": f"{fam} {style}" if not reg else fam,
        "version": f"Version {VERSION}",
        "psName": f"Plume-{style}",
        "licenseDescription": "This Font Software is licensed under the SIL Open Font License, Version 1.1. This license is available with a FAQ at: https://openfontlicense.org",
        "licenseInfoURL": "https://openfontlicense.org",
        "typographicFamily": fam,
        "typographicSubfamily": style,
    })
    fb.setupOS2(sTypoAscender=960, sTypoDescender=-240, sTypoLineGap=0, usWinAscent=1120, usWinDescent=320, sxHeight=XH, sCapHeight=CAP,
                usWeightClass=weight, fsType=0, achVendID="PLUM", fsSelection=0b1000000, usFirstCharIndex=0x20, usLastCharIndex=0xFFFF)
    fb.setupPost(keepGlyphNames=False)
    # kerning (GPOS) from the pair table
    from fontTools.feaLib.builder import addOpenTypeFeaturesFromString
    pairs = kerning_pairs()
    lines = [f"pos uni{ord(a):04X} uni{ord(b):04X} {v};" for (a, b), v in sorted(pairs.items()) if a in names and b in names]
    fea = "languagesystem DFLT dflt;\nlanguagesystem latn dflt;\nfeature kern {\n" + "\n".join(lines) + "\n} kern;\n"
    addOpenTypeFeaturesFromString(fb.font, fea)
    os.makedirs(out_dir, exist_ok=True)
    base = os.path.join(out_dir, f"Plume-{style}")
    fb.font.save(base + ".ttf")
    f2 = fb.font
    f2.flavor = "woff2"
    f2.save(base + ".woff2")
    return {"weight": weight, "glyphs": len(order), "ttf_kb": round(os.path.getsize(base + ".ttf") / 1024), "woff2_kb": round(os.path.getsize(base + ".woff2") / 1024)}


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=os.path.join(ROOT, "fonts"))
    ap.add_argument("--weights", default="400,500,600")
    ap.add_argument("--only", default=None, help="build only these characters (for quick tests)")
    a = ap.parse_args()
    for w in [int(x) for x in a.weights.split(",")]:
        print(build(w, a.out, a.only), flush=True)
